#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 42: הפסקת חשמל (season 9 "הקו פנוי" ep4, VOICED, built 19.11 under §P, ~21 s).
Voices = voice bank 2026-11-19 lines 4200–4204 (Benji = cat, Delia = Sharit) + 2703 "שרית?! גם פה?" + stock 9000
"שנייה, מותק.", 9103 "יש!!!", 9104 "רגע... מה?!", prepared by voice/ep42_prep.py.
Set (new): his kitchen in a blackout — lit only by the phone torch and the screen glow; the freezer, the snack-box ice cream
(callback ep27) melting on the counter, the fuse box on the wall behind him.
Want: get the power back before the ice cream melts ("אין חשמל. והגלידה נמסה.").
Plant: the fuse box behind him — one switch "ראשי" is DOWN — the torch passes over it in frame 0 and again mid-climb (x64).
Never pointed at.
Climb (3 chips): בקו ✓ (the electricity hotline, "מקום 47") → מקום 12 ✓ ("שתים עשרה! אני מתקרב!") → נציגה ✓ gold
(Sharit answers, "יש!!!"). Peak: "שנייה, מותק." — she checks; he holds the phone to his cheek, eyes closed; hush + heartbeat.
Break (never_needed): "רק אצלך, מותק. בדקת את הלוח בבית?" — he turns, flips "ראשי": the lights snap on, the freezer hums,
the ice cream is already a puddle. "רגע... מה?!" Frozen face; whip into the cold open.
Experiment (follows): part_label — "חלק 4 מתוך 5" pill in frame 0 (and the first caption line).
No music (voiced rule): voices + SFX (hold beeps, not music) + fridge-silence room tone. Serial pills + live ticket number (§O4).

  python3 voice/ep42_prep.py
  python3 ep42.py times | test t1 t2 ... | render   -> out/ep42_hashmal.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep7 as E7
import ep12 as E12
import ep18 as E18
import ep21_v1 as E21
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep42', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 104, 226)
NAVY = (30, 50, 110); SHARIT_SUB = (255, 182, 210)
QUEUE = int(os.environ.get('QUEUE', '441'))
EP_LABEL = 'פרק 42'
PART_LABEL = 'חלק 4 מתוך 5'
OUTNAME = os.environ.get('OUTNAME', 'ep42_hashmal_v3')
LIMIT = float(os.environ.get('LIMIT', '0'))

def segments(i, gap_frames=4, thr=0.08):
    env = META[i]['env']; segs = []; start = None; quiet = 0
    for k, v in enumerate(env):
        if v >= thr:
            if start is None: start = k
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet >= gap_frames: segs.append((start / FPS, (k - quiet + 1) / FPS)); start = None; quiet = 0
    if start is not None: segs.append((start / FPS, len(env) / FPS))
    return [s_ for s_ in segs if s_[1] - s_[0] >= 0.10]
SEG = {i: segments(i) for i in META}
def ss(i, k):
    s = SEG[i]
    return s[k][0] if k < len(s) else D[i] * (k / max(1, len(s)))

# ------------------------------------------------------------------ timeline
COLD_END = round(D[0] + 0.40, 2)            # cold open = 4200 "שתים עשרה! אני מתקרב!" (the loudest climb line)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "אין חשמל. והגלידה נמסה."
L[2] = L[1] + D[1] + 0.12                   # "מקום ארבעים ושבע..." — on hold
CHK1 = L[2] + 0.25
FF = (L[2] + D[2] + 0.10, L[2] + D[2] + 2.50)   # x64: 47 → 12 on the hold screen, the torch swings over the fuse box, the ice cream melts
L['0b'] = FF[1] + 0.05                      # "שתים עשרה! אני מתקרב!" in context (= the cold open)
CHK2 = L['0b'] + 0.05
RING = (L['0b'] + D[0] + 0.06, L['0b'] + D[0] + 0.40)   # the line connects
L[3] = RING[1] + 0.05                       # Sharit: "שלום, מדברת שרית, מותק."
CHK3 = L[3] + 0.10; GOLDT = CHK3 + 0.05
L[103] = L[3] + D[3] + 0.08                 # "יש!!!"
L[27] = L[103] + D[103] + 0.10              # "שרית?! גם פה?"
L[90] = L[27] + D[27] + 0.15                # Sharit: "שנייה, מותק." — she checks (the peak)
HOLD = (L[90] + D[90] + 0.03, L[90] + D[90] + 0.55)
BREAK = HOLD[1]
L[4] = BREAK                                # Sharit: "רק אצלך, מותק. בדקת את הלוח בבית?"
TURN = L[4] + ss(4, 1) - 0.10               # on "בדקת את הלוח" he turns to the fuse box
FLIP = L[4] + D[4] + 0.12                   # paw flips "ראשי": lights on
L[104] = FLIP + 0.38                        # "רגע... מה?!"
FREEZE = L[104] + D[104]
DUR = round(FREEZE + 0.40, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (0, L['0b']), (3, L[3]), (103, L[103]), (27, L[27]), (90, L[90]), (4, L[4]), (104, L[104])]
SPEAKER = {0: 'cat', 1: 'cat', 2: 'cat', 103: 'cat', 27: 'cat', 104: 'cat', 3: 'sh', 90: 'sh', 4: 'sh'}

SUBS = {
    0: [['שתים עשרה! אני מתקרב!']],
    1: [['אין חשמל.'], ['והגלידה נמסה.']],
    2: [['מקום ארבעים ושבע...']],
    3: [['שלום, מדברת שרית, מותק.']],
    103: [['יש!!!']],
    27: [['שרית?! גם פה?']],
    90: [['שנייה, מותק.']],
    4: [['רק אצלך, מותק.'], ['בדקת את הלוח בבית?']],
    104: [['רגע... מה?!']],
}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]
    if len(ch) > 1 and len(SEG[li]) < len(ch): ch = [[' '.join(sum(ch, []))]]
    starts = [0.0] + [ss(li, k) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 104: b = DUR - 0.25
        if li == 90: b = min(b, HOLD[0] + 0.02)
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('room', 0.0, COLD_END), ('rewind', COLD_END, T0), ('room', T0, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['מקום 47 בתור', 'למוקד החשמל']          # keyword: מוקד החשמל / הפסקת חשמל (F5)
TOPCAPS = [(0.0, COLD_END, HOOK), (T0, L[1] + D[1] - 0.1, HOOK)]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def story_t(t):
    return L['0b'] + t if t < COLD_END else t

def speaking(t):
    for li, s0 in OCC:
        if s0 <= t < s0 + D[li]: return li, s0
    return None

def voice_v(t, who='cat'):
    sp = speaking(t)
    if not sp or SPEAKER[sp[0]] != who: return 0.0
    li, s0 = sp; env = META[li]['env']; k = int((t - s0) * FPS)
    return env[k] if k < len(env) else 0.0

def cat_mouth(t, rest='w', loud='smile'):
    v = voice_v(t, 'cat')
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

def lights_on(t):
    return t >= COLD_END and story_t(t) >= FLIP

def melt(t):
    """0 = solid, 1 = puddle"""
    s_t = story_t(t)
    if t >= COLD_END and s_t >= FLIP: return 1.0
    s0 = FLIP - 0.05 - 17.0                     # the clock reads 00:17 at the start of the story, 00:00 at FLIP - 0.05
    return 0.08 + 0.87 * clamp((s_t - s0) / 17.0)

# ------------------------------------------------------------------ the phone (hold screen / call)
PW, PH = 400, 720
SH_CALL = None
def hold_pos(t):
    s_t = story_t(t)
    if s_t < L[2]: return None
    if s_t < FF[0]: return 47
    if s_t < FF[1]: return int(round(lerp(47, 12, ease_in(clamp((s_t - FF[0]) / (FF[1] - FF[0] - 0.15))))))
    return 12

def phone_state(t):
    s_t = story_t(t)
    if t < COLD_END: return 'hold'               # the cold open stays on the hold screen ("12")
    if s_t >= RING[0]: return 'call'
    return 'hold'

def phone_layer(state, pos, talk=0, lit=False):
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    E(pd, PW - 60, 40, 12, 12, fill=(255, 250, 200) if not lit else (60, 60, 66))   # the torch LED
    if state == 'call':
        pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=NAVY)
        pd.text((S(PW / 2), S(96)), 'מוקד החשמל', font=font(S(36), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(140)), 'נציגה מחוברת', font=font(S(26), 800), fill=(190, 206, 240), anchor='mm')
        lay.alpha_composite(SH_CALL[talk], (int(S(PW / 2)) - SH_CALL[talk].width // 2, int(S(170))))
        pd = ImageDraw.Draw(lay)
        E(pd, PW / 2, 640, 40, 40, fill=RED)
        return lay
    pd.rectangle([S(14), S(66), S(PW - 14), S(132)], fill=NAVY)
    pd.text((S(PW / 2), S(99)), 'מוקד החשמל', font=font(S(36), 900), fill=WHITE, anchor='mm')
    pd.text((S(PW / 2), S(190)), 'השיחה בהמתנה...', font=font(S(30), 800), fill=(90, 92, 104), anchor='mm')
    if pos is not None:
        pd.text((S(PW / 2), S(260)), 'אתה במקום', font=font(S(34), 800), fill=INK, anchor='mm')
        pd.rounded_rectangle([S(90), S(296), S(PW - 90), S(436)], radius=S(26), fill=(255, 236, 236) if pos > 20 else (232, 250, 238),
                             outline=RED if pos > 20 else GREEN, width=iw(6))
        pd.text((S(PW / 2), S(368)), str(pos), font=font(S(104), 900), fill=RED if pos > 20 else GREEN, anchor='mm')
    for k in range(5):
        pd.rounded_rectangle([S(110 + k * 40), S(500 - 20 * (k % 3)), S(130 + k * 40), S(540)], radius=S(6), fill=(170, 176, 196))
    pd.text((S(PW / 2), S(600)), 'השיחה מוקלטת', font=font(S(22), 700), fill=(150, 152, 162), anchor='mm')
    return lay

_PHC = {}
def phone_at(t):
    st = phone_state(t); talk = 0
    if st == 'call':
        sv = voice_v(t, 'sh'); talk = 2 if sv > 0.3 else (1 if sv > 0.1 else 0)
    key = (st, hold_pos(t), talk, lights_on(t))
    if key not in _PHC:
        if len(_PHC) > 80: _PHC.clear()
        _PHC[key] = phone_layer(*key)
    return _PHC[key]

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    E21.shadow_paste(img, lay, c, 100, (16, 20), 12)

burst = E18.burst

# ------------------------------------------------------------------ the set: his kitchen (new)
FUSE = (880, 520)          # the fuse box centre (on the wall behind him, right)
TUB = (790, 1470)          # polish 23.11: the ice cream cup on a foreground counter, bigger, in frame in every shot
def build_kitchen_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        v = y / H; d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(236, 214, v)), int(lerp(226, 206, v)), int(lerp(196, 170, v))))
    for x in range(0, W, 90):                                   # tiles backsplash
        line(d, [(x, 900), (x, 1300)], (210, 200, 176), 3)
    for y in range(900, 1300, 90): line(d, [(0, y), (W, y)], (210, 200, 176), 3)
    # the freezer / fridge on the left
    d.rounded_rectangle([S(20), S(240), S(420), S(1380)], radius=S(26), fill=(240, 242, 246), outline=(150, 154, 166), width=iw(7))
    line(d, [(20, 640), (420, 640)], (150, 154, 166), 6)
    d.rounded_rectangle([S(370), S(320), S(392), S(560)], radius=S(8), fill=(170, 174, 186))
    d.rounded_rectangle([S(370), S(720), S(392), S(1000)], radius=S(8), fill=(170, 174, 186))
    d.text((S(220), S(440)), 'מקפיא', font=font(S(40), 900), fill=(150, 156, 170), anchor='mm')
    # window with the dark street (night)
    d.rounded_rectangle([S(500), S(200), S(760), S(560)], radius=S(8), fill=(40, 52, 90), outline=(240, 240, 236), width=iw(12))
    for (x, y) in ((560, 300), (700, 260), (620, 420)): E(d, x, y, 4, 4, fill=(220, 220, 240))
    # the fuse box (the plant): grey box, 6 switches, "ראשי" DOWN
    x0, y0 = FUSE[0] - 140, FUSE[1] - 170
    d.rounded_rectangle([S(x0), S(y0), S(x0 + 280), S(y0 + 340)], radius=S(12), fill=(196, 198, 206), outline=(110, 112, 124), width=iw(6))
    d.text((S(FUSE[0]), S(y0 + 34)), 'לוח חשמל', font=font(S(30), 900), fill=(70, 72, 84), anchor='mm')
    for k in range(6):
        cx = x0 + 40 + k * 40
        d.rounded_rectangle([S(cx - 14), S(y0 + 80), S(cx + 14), S(y0 + 170)], radius=S(5), fill=(250, 250, 250), outline=(90, 92, 104), width=iw(3))
        d.rounded_rectangle([S(cx - 9), S(y0 + 86), S(cx + 9), S(y0 + 116)], radius=S(4), fill=(60, 62, 72))
    d.rounded_rectangle([S(x0 + 70), S(y0 + 196), S(x0 + 210), S(y0 + 316)], radius=S(8), fill=(250, 250, 250), outline=(90, 92, 104), width=iw(4))
    d.text((S(FUSE[0]), S(y0 + 222)), 'ראשי', font=font(S(26), 900), fill=RED, anchor='mm')
    # counter
    d.rectangle([0, S(1560), W * K, H * K], fill=(150, 116, 84))
    d.rounded_rectangle([S(-20), S(1540), S(1100), S(1600)], radius=S(10), fill=(206, 196, 180), outline=(140, 130, 116), width=iw(5))
    img = img.filter(ImageFilter.GaussianBlur(S(1.2)))
    return img

def main_switch(d, up):
    x0, y0 = FUSE[0] - 140, FUSE[1] - 170
    cx, top = FUSE[0], y0 + 236
    d.rounded_rectangle([S(cx - 18), S(top), S(cx + 18), S(top + 70)], radius=S(6), fill=(230, 232, 236), outline=(90, 92, 104), width=iw(3))
    if up: d.rounded_rectangle([S(cx - 13), S(top + 4), S(cx + 13), S(top + 34)], radius=S(5), fill=GREEN)
    else: d.rounded_rectangle([S(cx - 13), S(top + 36), S(cx + 13), S(top + 66)], radius=S(5), fill=RED)

def counter_front(d):
    """polish 23.11: a foreground counter so the ice cream (and the puddle) sit on something"""
    d.rectangle([S(-20), S(1470), S(1100), S(1520)], fill=(214, 204, 188), outline=(140, 130, 116), width=iw(5))
    d.rectangle([S(-20), S(1520), S(1100), S(2000)], fill=(150, 116, 84), outline=(96, 70, 46), width=iw(5))
    for x in (260, 620, 980): line(d, [(x, 1540), (x, 1960)], (120, 90, 62), 4)

SCOOPS = [((-46, -8), (250, 170, 196)), ((46, -8), (252, 240, 214)), ((0, -78), (150, 96, 70))]   # strawberry, vanilla, chocolate
def tub(d, mk):
    """the ice cream: a cup with 3 scoops and a spoon, melting with the clock (mk 0..1); 1 = a big puddle, the empty cup"""
    x, y = TUB                                    # y = the counter top
    pw = 70 + 300 * mk ** 1.3                     # puddle half-width
    if mk > 0.05:
        E(d, x - 10, y + 10, pw, 16 + 56 * mk, fill=(240, 150, 182), outline=(176, 84, 120), width=5)
        E(d, x - 70, y - 2, pw * 0.35, 4 + 10 * mk, fill=(255, 226, 236))   # gloss
        E(d, x - 40, y + 4, pw * 0.55, 8 + 16 * mk, fill=(250, 214, 226))                       # vanilla swirl in it
        E(d, x + 60, y + 10, pw * 0.3, 6 + 10 * mk, fill=(160, 104, 78))                         # chocolate swirl
    if mk >= 0.999:                               # the break: the empty cup on its side in the puddle, the spoon in it
        d.polygon([(S(x + 40), S(y - 70)), (S(x + 180), S(y - 40)), (S(x + 170), S(y + 4)), (S(x + 30), S(y - 4))],
                  fill=(255, 255, 255), outline=(150, 150, 160))
        d.text((S(x + 105), S(y - 30)), 'גלידה', font=font(S(30), 900), fill=(200, 80, 110), anchor='mm')
        capsule(d, (x - 220, y + 6), (x - 60, y - 6), 14, (200, 204, 214), (110, 114, 126), 3)   # the spoon
        E(d, x - 240, y + 8, 30, 16, fill=(200, 204, 214), outline=(110, 114, 126), width=3)
        return
    # the cup (trapezoid), label
    top, bot = y - 150, y
    d.polygon([(S(x - 95), S(top)), (S(x + 95), S(top)), (S(x + 72), S(bot)), (S(x - 72), S(bot))], fill=(255, 255, 255), outline=(150, 150, 160))
    d.rectangle([S(x - 88), S(top + 40), S(x + 88), S(top + 70)], fill=(244, 120, 160))
    d.text((S(x), S(top + 108)), 'גלידה', font=font(S(34), 900), fill=(200, 80, 110), anchor='mm')
    # scoops: shrink and sag with mk; drips down the cup
    k = 1 - 0.75 * mk
    for (dx, dy), col in SCOOPS:
        r = 58 * k; cy = top + 6 + dy * k + 30 * mk
        E(d, x + dx * (0.6 + 0.4 * k), cy, r, r * (1 - 0.25 * mk), fill=col, outline=tuple(max(0, c - 60) for c in col), width=4)
    for j, (dx, col) in enumerate(((-60, (250, 170, 196)), (-10, (252, 240, 214)), (50, (150, 96, 70)))):
        ln = 20 + 120 * mk * (0.7 + 0.3 * j)
        capsule(d, (x + dx, top + 4), (x + dx - 4 * j, min(bot - 6, top + 4 + ln)), 9, col)
    # the spoon stuck in, tilting as the scoops sink
    a = math.radians(-30 - 25 * mk)
    sx, sy = x + 20, top - 10 - 30 * k
    ex, ey = sx + 150 * math.sin(-a), sy - 150 * math.cos(a)
    capsule(d, (sx, sy), (ex, ey), 12, (200, 204, 214), (110, 114, 126), 3)

def base_cat():
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.3); return st

HXP, HYP, FP = 640, 1000, 1.66

def cat_state(t):
    st = base_cat(); rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    s_t = story_t(t)
    if L['0b'] <= s_t < RING[0]:                 # "שתים עשרה! אני מתקרב!" — fierce hope, bouncing
        u = s_t - L['0b']
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(s_t, rest='smile', loud='w'), ear_dy=-28, look=(-24, 2), blush=0.9)
        rot = 6 * math.sin(u * 11); dy = -26 * abs(math.sin(u * 8)) - 10 * voice_v(s_t, 'cat')
    elif t < L[2]:                               # the want: panicked at the melting tub
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-20, look=(-34, 14), sweat=1.0, blush=0.0)
        rot = 4 * math.sin(t * 7); dy = -10 * v
    elif t < FF[1]:                              # on hold: deflated, then the wait
        u = clamp((t - FF[0]) / (FF[1] - FF[0]))
        st.update(lid=0.4 + 0.3 * u, pupil='normal', brow='annoyed', mouth=cat_mouth(t, rest='flat', loud='w'), ear_droop=0.6 * u, look=(-24, 6), sweat=0.4)
        dy = 10 * u
    elif t < L[103]:                             # the line connects: Sharit
        u = t - RING[0]
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-24 * math.exp(-max(0, u) * 2), look=(-30, 6), blush=0.5)
        rot = 5 * math.sin(max(0, u) * 24) * math.exp(-max(0, u) * 3)
    elif t < L[27]:                              # "יש!!!"
        u = t - L[103]
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28, blush=1.0, look=(-10, 0))
        dy = -24 * abs(math.sin(u * 9)) * math.exp(-u * 1.0)
    elif t < L[90]:                              # "שרית?! גם פה?"
        u = t - L[27]
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-24 * math.exp(-u * 2), sweat=0.8, look=(-22, 4))
        rot = 7 * math.sin(u * 20) * math.exp(-u * 3)
    elif t < BREAK:                              # THE PEAK: the phone at his cheek, eyes closed, hoping
        st.update(eye_mode='closed', mouth='smile', ear_dy=-14, blush=1.0, look=(0, 0)); rot = -6; dy = 6
    elif t < FLIP:                               # "רק אצלך... בדקת את הלוח?" — eyes open, slowly turning
        u = t - BREAK; turned = t >= TURN
        st.update(lid=0.1, pupil='tiny', brow='none', mouth='flat', look=(40, -30) if turned else (-20, 6), sweat=clamp(u / 0.8), ear_dy=-10)
        rot = 6 * ease_io(clamp((t - TURN) / 0.4)) if turned else 0
    else:                                        # lights on, the puddle — frozen
        u = t - FLIP
        st.update(lid=0.0, pupil='tiny', brow='up' if t >= L[104] else 'none', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-26 * math.exp(-u * 4),
                  look=(-34, 24), twitch=(u >= 0.5 and int(t * 12) % 2 == 0), sweat=1.0, blush=0.0)
        dy = -10
    return st, rot, dy

def torch_target(t):
    """where the phone torch points (world coords)"""
    s_t = story_t(t)
    if L['0b'] <= s_t < RING[0]:                 # frame 0 / in context: the beam sweeps right → left across the fuse box
        u = clamp((s_t - L['0b']) / (RING[0] - L['0b']))
        return (lerp(1060, 620, u), lerp(470, 560, u))
    if s_t < L[2]: return (TUB[0] + 10, TUB[1] - 20)
    if s_t < FF[0]: return (420, 900)
    if s_t < FF[1]:                              # bored swing: tub → fuse box → back
        u = (s_t - FF[0]) / (FF[1] - FF[0])
        return (lerp(260, 1000, math.sin(math.pi * u)), lerp(1300, 470, math.sin(math.pi * u)))
    if s_t < TURN: return (300, 1600)
    return FUSE

def scene_room(t, i):
    img = KITCHEN.copy()
    d = ImageDraw.Draw(img)
    s_t = story_t(t)
    on = lights_on(t)
    main_switch(d, on)
    st, rot, dy = cat_state(t)
    E(d, HXP, 1700, 420, 440, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1760, 190, 290, fill=CREAM)
    counter_front(d)
    peak = L[90] <= s_t < BREAK and t >= COLD_END
    flipping = TURN <= s_t and t >= COLD_END and not on
    if peak:
        pc = (420, 1000); ang = -14; sc = 0.86
    else:
        pc = (330, 1130 + 5 * math.sin(t * 8)); ang = -6; sc = 0.98
        if L['0b'] <= s_t < RING[0]: pc = (330 + 10 * math.sin(t * 30), 1120 - 14 * abs(math.sin(t * 8)))
        if RING[0] <= s_t < RING[0] + 0.4: sc += 0.16 * math.exp(-(s_t - RING[0]) * 9); pc = (330 + 8 * math.sin(t * 90), 1130)
    grip = (pc[0] - 170, pc[1] + 160) if not peak else (pc[0] + 30, pc[1] + 170)
    capsule(d, (HXP - 230, 1520), grip, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP, HYP + dy, FP, rot)
    paste_rot(img, phone_at(t), pc, ang, sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, grip, 70, 0.9)
    tub(d, melt(t))
    if flipping or (on and s_t < FLIP + 0.5):    # the other paw reaches up to the switch
        tgt = (FUSE[0], FUSE[1] + 100)
        pp = lerp2((HXP + 200, 1450), tgt, ease_out(clamp((s_t - TURN) / 0.5)))
        if on: pp = (tgt[0], tgt[1] - 30 * math.exp(-(s_t - FLIP) * 8))
        sh_ = (HXP + 250, 1230); el = (lerp(HXP + 330, pp[0] + 110, 0.5), lerp(1230, pp[1], 0.55))
        capsule(d, sh_, el, 96, FUR, OUT, 4); capsule(d, el, pp, 88, FUR, OUT, 4); E12.big_paw(d, pp, -30, 0.8)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= s_t < c_ + 0.5: burst(img, (pc[0], pc[1] - 60), s_t - c_, (120, 255, 160), 160, 10, 0.4)
    if GOLDT <= s_t < L[90]: E18.confetti(img, s_t - GOLDT + 0.3)
    if on and 0 <= s_t - FLIP < 0.45: burst(img, FUSE, s_t - FLIP, (255, 240, 160), 260, 14, 0.45)
    # darkness: the world is dark except the torch cone, the screen glow on his face, and (after the flip) everything
    if not on:
        sm = 4
        mask = Image.new('L', (W // sm, H // sm), 0); md = ImageDraw.Draw(mask)
        tx, ty = torch_target(t); px, py = pc[0], pc[1] - 200 * sc
        ang_ = math.atan2(ty - py, tx - px); dist = math.hypot(tx - px, ty - py) + 160; spread = 0.22
        pts = [(px, py), (px + dist * math.cos(ang_ - spread), py + dist * math.sin(ang_ - spread)),
               (px + dist * math.cos(ang_ + spread), py + dist * math.sin(ang_ + spread))]
        md.polygon([(x / sm, y / sm) for x, y in pts], fill=200)
        md.ellipse([(tx - 190) / sm, (ty - 190) / sm, (tx + 190) / sm, (ty + 190) / sm], fill=235)
        md.ellipse([(HXP - 330) / sm, (HYP - 330) / sm, (HXP + 330) / sm, (HYP + 330) / sm], fill=150)   # screen glow on his face
        md.ellipse([(pc[0] - 260) / sm, (pc[1] - 400) / sm, (pc[0] + 260) / sm, (pc[1] + 400) / sm], fill=255)
        md.ellipse([(TUB[0] - 240) / sm, (TUB[1] - 300) / sm, (TUB[0] + 240) / sm, (TUB[1] + 90) / sm], fill=190)   # the ice cream stays readable
        mask = mask.filter(ImageFilter.GaussianBlur(70 / sm)).resize((W * K, H * K), Image.BILINEAR)
        dark = Image.new('RGBA', img.size, (8, 12, 30, 255))
        dark = Image.blend(img, dark, 0.80)
        img = Image.composite(img, dark, mask)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('בקו', 820, CHK1), ('מקום 12', 540, CHK2), ('נציגה', 260, CHK3)]
def chips(frame, t, y=330):
    s_t = story_t(t)
    if t < L[1] + D[1] - 0.1 or t >= FLIP + 0.6: return
    gold = t >= GOLDT
    drained = t >= FLIP
    d = ImageDraw.Draw(frame)
    for lab, cx, tk in CHIPS:
        ok = t >= tk and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if drained: sc = 1.0 + 0.15 * math.exp(-(t - FLIP) * 10)
        w, h = 220 * sc, 70 * sc
        jx = random.Random(int(t * FPS) + cx).uniform(-8, 8) if drained else 0
        d.rounded_rectangle([cx + jx - w / 2, y - h / 2, cx + jx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + jx + 22 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx + jx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], outline=ink, width=4)

def rewind_overlay(frame, t):
    frame.alpha_composite(m.SCAN)
    d = ImageDraw.Draw(frame)
    rng = random.Random(int(t * 120))
    for _ in range(5):
        y = rng.uniform(300, 1700); h = rng.uniform(4, 14)
        d.rectangle([0, y, W, y + h], fill=(255, 255, 255, 70))
    for x0 in (300, 344):
        d.polygon([(x0 + 44, 900), (x0, 930), (x0 + 44, 960)], fill=WHITE, outline=(10, 10, 12), width=5)
    d.text((610, 930), 'רגע קודם', font=font(76, 900), fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(10, 10, 12))

def ff_overlay(frame, t):
    frame.alpha_composite(m.SCAN)
    d = ImageDraw.Draw(frame)
    for x0 in (850, 906):
        d.polygon([(x0, 600), (x0 + 50, 634), (x0, 668)], fill=WHITE, outline=(10, 10, 12), width=5)
    d.text((780, 634), 'x64', font=font(70, 900), fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(10, 10, 12))

def sub_layer(lines, fill, size=64):
    lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

KITCHEN = PILL_EP = PILL_Q = PILL_PART = None
def init_all():
    global KITCHEN, PILL_EP, PILL_Q, PILL_PART, SH_CALL
    m.init_static()
    KITCHEN = build_kitchen_bg()
    SH_CALL = []
    for mo in ('lazy', 'talk', 'grin'):     # Sharit on the scheduling line, 3 mouth states (headset-free crop, like ep36)
        st = SH.base(); st.update(mouth=mo, lid=0.6, look=(0, 6), snack=False)
        lay = SH.draw(st, 3 if mo == 'talk' else 0).crop((S(60), S(60), S(640), S(700)))
        SH_CALL.append(lay.resize((S(330), int(S(330) * lay.height / lay.width)), Image.LANCZOS))
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_PART = HUD._pill(PART_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'room':
        z, cx, cy = 1.04 + 0.01 * pu, 540, 1000
        if a == 0.0:                                   # cold open: wide-ish, tilted, the beam sweeping the dark kitchen
            z, cx, cy = 1.18 + 0.03 * t, 620, 980
            if t < 0.3: z = 1.38 - 0.20 * ease_out(t / 0.3)
        elif t < L[2]: z, cx, cy = 1.16, 640, 1180
        elif FF[0] <= t < FF[1]: z, cx, cy = 1.0, 540, 960
        elif L['0b'] <= t < RING[0]: z, cx, cy = 1.18, 620, 980
        elif RING[0] <= t < L[90]: z, cx, cy = 1.14, 520, 1080
        if L[90] <= t < BREAK:
            k = ease_io(clamp((t - L[90]) / (BREAK - L[90]))); z, cx, cy = 1.14 + 0.16 * k, lerp(520, 560, k), lerp(1080, 1040, k)
        if BREAK <= t < FLIP: z, cx, cy = 1.06 + 0.04 * ease_io(clamp((t - TURN) / 0.4)), lerp(560, 700, ease_io(clamp((t - TURN) / 0.4))), lerp(1040, 900, ease_io(clamp((t - TURN) / 0.4)))
        if t >= FLIP: z, cx, cy = 1.0, 540, 960
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1000
    elif name == 'frozen':
        z, cx, cy = 1.30 + 0.03 * pu, 560, 1060
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_room(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    else: img = scene_room(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (RING[0], FLIP):
        if 0 <= t - s_ < 0.3: shake = 14 * math.exp(-(t - s_) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if t < COLD_END: frame = frame.rotate(-4, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(8, 12, 30, 255))   # Dutch tilt (different from ep40's frame 0)
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if FF[0] <= t < FF[1]: ff_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, FLIP):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    if name != 'frozen': chips(frame, t)
    for t0, t1, lines in TOPCAPS:
        if t0 <= t < t1: m.paste_center(frame, m.caption_layer(lines, 96, WHITE), W / 2, 270)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            col = SHARIT_SUB if SPEAKER[li] == 'sh' else WHITE
            m.paste_center(frame, sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < L[2]) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_PART, (40 + PILL_EP.width + 10, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + blackout hush; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(42)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'sh': y = m.phone_line(y) * 1.5
        add(voice, y, s0, 0.95)
    def whoosh(t0, g=0.06, wl=0.16): add(sfx, m.bandpass(nz(wl), 600, 5000) * np.sin(np.pi * tt_(wl) / wl) ** 2, t0 - 0.08, g)
    def thud(g=0.9):
        tt = tt_(0.45); freq = 150 * np.exp(-tt * 6) + 42
        return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) + m.lowpass(nz(0.45), 420) * np.exp(-tt * 30) * 0.8) * g
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def beep(t0, g=0.05): add(sfx, m.tone(440.0, 0.12, harm=((1, 1),), decay=8), t0, g)
    def cheer(t0, ln=1.0, g=0.08):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    add(sfx, thud(0.7), 0.0)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(FLIP), 100, 500) * 0.6, 0.0, 0.007)                       # blackout hush
    tb = L[2]                                                                          # hold beeps (not music)
    while tb < RING[0] - 0.2:
        beep(tb); tb += 0.9
    check(CHK1, 0.13)
    add(sfx, m.bandpass(nz(0.4), 600, 5000) * np.linspace(0, 1, int(0.4 * SR)), FF[0] - 0.3, 0.06)
    tc = FF[0]
    while tc < FF[1]:
        add(sfx, m.tone(1200 + 200 * math.sin(tc * 9), 0.03, harm=((1, 1),), decay=40), tc, 0.025); tc += 0.07
    check(CHK2, 0.15)
    add(sfx, m.tone(880.0, 0.25, harm=((1, 1), (2, 0.3)), decay=6), RING[0], 0.14); whoosh(RING[0], 0.08, 0.25)
    check(CHK3, 0.2, True); cheer(GOLDT + 0.05, L[90] - GOLDT, 0.07)
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.31, 0.5)
    add(sfx, m.highpass(nz(0.03), 2000) * np.exp(-tt_(0.03) * 120), FLIP, 0.6); add(sfx, thud(0.6), FLIP)   # the switch clack
    hum = np.sin(2 * np.pi * 50 * tt_(DUR - FLIP)) * 0.6 + np.sin(2 * np.pi * 100 * tt_(DUR - FLIP)) * 0.3
    add(sfx, hum * np.minimum(1, tt_(DUR - FLIP) / 0.1), FLIP + 0.02, 0.04)                              # the freezer hums back
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), FLIP + 0.3, 0.14)
    out = voice + sfx
    out = out[:int(DUR * SR)]
    wl_ = 0.3; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.28)
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())

def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if mode == 'times':
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', T0, 'FF', [round(x, 2) for x in FF], 'RING', [round(x, 2) for x in RING])
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'HOLD', [round(x, 2) for x in HOLD], 'TURN', round(TURN, 2), 'FLIP', round(FLIP, 2),
              'BREAK', round(BREAK, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep42_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'{OUTNAME}_audio.wav'); build_audio(wav); print('audio ok')
    if mode == 'audio': return
    mp4 = os.path.join(OUTDIR, f'{OUTNAME}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nfr = int(LIMIT * FPS) if LIMIT else NF
    with Pool(os.cpu_count() or 2, initializer=_init_worker) as pool:
        for k, b in enumerate(pool.imap(_render, range(nfr), chunksize=4)):
            proc.stdin.write(b)
            if k % 150 == 0: print('frame', k, '/', nfr, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
