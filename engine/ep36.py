#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 36: המשלוח בדרך (season 8 "בלאק פריידיי" ep3, VOICED, built 16.11 under §P, ~21 s).
Voices = voice bank 2026-11-13 lines 3600–3605 (Benji = cat, Vera = grandma) + 2703 "שרית?! גם פה?" (Sharit is the courier
dispatcher on the call screen) + stock 9000 "שנייה, מותק.", 9102 "יאללה!", 9103 "יש!!!", prepared by voice/ep36_prep.py.
Set: his own front door (an everyday place, new set: hallway wall, wooden door with peephole, doormat), the phone's
tracking page with a live ETA ("השליח בעוד 3 דק׳ → 2 → 1") = the counter in front of the viewer.
Want: catch the courier at home and get the Black Friday snack box (ep34/35's cart).
Plant: the tracking page's small grey line "כתובת למשלוח: הכתובת הרשומה" (cold open, the want close-up, again after
the call). Never pointed at. (The registered address = grandma in Eilat, ep35.)
Climb (meter = 3 chips + the ETA): "יצא מהמחסן. יפה." ✓ → "נחת בישראל!" ✓ → Sharit on the dispatcher call → "בדרך אליך
היום! היום!" ✓ → the ETA runs down → "יאללה!" → the bell → "יש!!!" gold.
Peak: "סוף סוף... הוא פה." — paw on the door handle, eyes closed, hush + heartbeat.
Break (mixup): the door opens on an empty landing; the screen splits: grandma in Eilat at HER door, hugging the box,
signing the courier's pad: "חמוד! הגיע לך משהו!" — frozen face, whip into the cold open (loop).
No music (voiced rule): voices + SFX + hallway room tone. Serial pills "פרק 36" + live ticket number (hud.stage_of, §O4).

  python3 voice/ep36_prep.py
  python3 ep36.py times | test t1 t2 ... | render   -> out/ep36_mishloach.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep7 as E7
import ep10 as E10
import ep12 as E12
import ep18 as E18
import ep21_v1 as E21
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep36', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 104, 226)
ORANGE = (255, 120, 30); BF = (18, 18, 22); GRAN_SUB = (255, 196, 232); SHARIT_SUB = (186, 214, 255)
QUEUE = int(os.environ.get('QUEUE', '446'))
EP_LABEL = 'פרק 36'
OUTNAME = os.environ.get('OUTNAME', 'ep36_mishloach')
LIMIT = float(os.environ.get('LIMIT', '0'))
BIGF = os.environ.get('BIGF', '0') == '1'      # 6א probe: bigger face in the close-ups

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

# ------------------------------------------------------------------ timeline (from the real line lengths)
COLD_END = round(D[0] + 0.12, 2)            # cold open = 3600 "בדרך אליך היום! היום!" (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "המארז של בלאק פריידי. מחכה ליד הדלת."
L[2] = L[1] + D[1] + 0.15                   # "יצא מהמחסן. יפה."
CHK1 = L[2] + 0.25
L[3] = L[2] + D[2] + 0.12                   # "נחת בישראל!"
CHK2 = L[3] + 0.15
RING = (L[3] + D[3] + 0.06, L[3] + D[3] + 0.46)   # the dispatcher calls: Sharit on the call screen
L[27] = RING[1] + 0.05                      # "שרית?! גם פה?"
L[900] = L[27] + D[27] + 0.08               # Sharit: "שנייה, מותק."
UPD = L[900] + D[900] + 0.04                # the call ends, the page updates: "בדרך אליך היום"
L['0b'] = UPD + 0.10                        # the cold-open line again, in context
CHK3 = L['0b'] + 0.10
WAIT = (L['0b'] + D[0] + 0.06, L['0b'] + D[0] + 1.76)    # ETA 3 → 2 → 1 → "השליח ליד הבית!"
ETA_T = [WAIT[0], WAIT[0] + 0.50, WAIT[0] + 1.00, WAIT[0] + 1.50]
L[102] = WAIT[1]                            # "יאללה!"
BELL = L[102] + D[102] + 0.08               # ding-dong
L[103] = BELL + 0.62                        # "יש!!!"
GOLDT = L[103] + 0.02
L[4] = L[103] + D[103] + 0.14               # "סוף סוף... הוא פה." (peak line)
HOLD = (L[4] + D[4] + 0.03, L[4] + D[4] + 0.55)
BREAK = HOLD[1]                             # the handle goes down, the door opens: nobody
L[5] = BREAK + 0.12                         # grandma (split): "חמוד! הגיע לך משהו!"
FREEZE = L[5] + D[5]
DUR = round(FREEZE + 0.38, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (3, L[3]), (27, L[27]), (900, L[900]), (0, L['0b']), (102, L[102]),
       (103, L[103]), (4, L[4]), (5, L[5])]
SPEAKER = {0: 'cat', 1: 'cat', 2: 'cat', 3: 'cat', 27: 'cat', 900: 'sharit', 102: 'cat', 103: 'cat', 4: 'cat', 5: 'grandma'}

SUBS = {
    0: [['בדרך אליך היום!'], ['היום!']],
    1: [['המארז של בלאק פריידי.'], ['מחכה ליד הדלת.']],
    2: [['יצא מהמחסן.'], ['יפה.']],
    3: [['נחת בישראל!']],
    27: [['שרית?! גם פה?']],
    900: [['שנייה, מותק.']],
    102: [['יאללה!']],
    103: [['יש!!!']],
    4: [['סוף סוף...'], ['הוא פה.']],
    5: [['חמוד!'], ['הגיע לך משהו!']],
}
SPLIT = {0: [0, 1], 1: [0, 1], 2: [0, 1], 4: [0, 1], 5: [0, 1]}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]; ks = SPLIT.get(li, [0])
    starts = [0.0] + [ss(li, ks[k]) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 5 and k == len(ch) - 1: b = DUR - 0.25
        if li == 4 and k == len(ch) - 1: b = min(b, HOLD[0] + 0.02)
        SUB_TIMES.append((a, b, c, li))

C = lambda t: t - 0.08
SHOTS = [('close', 0.0, COLD_END), ('rewind', COLD_END, T0), ('close', T0, C(WAIT[0])), ('door', C(WAIT[0]), BREAK),
         ('split', BREAK, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['מחכים לשליח', 'ליד הדלת?']          # keyword: שליח / משלוח (F16 pain question, everyone has waited)
TOPCAPS = [(0.0, COLD_END, HOOK), (T0, L[2] - 0.1, HOOK)]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def story_t(t):
    """the cold open is the in-context replay of 3600: map its time onto the story clock"""
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

# ------------------------------------------------------------------ the phone (tracking page / dispatcher call)
def n_steps(t):
    st = story_t(t)
    return sum(1 for c_ in (CHK1, CHK2, CHK3) if st >= c_)

def eta_k(t):
    """0 = no ETA yet; 1..3 = 'בעוד 3/2/1 דק׳'; 4 = 'השליח ליד הבית!'"""
    st = story_t(t)
    if st < CHK3: return 0
    return 1 + sum(1 for e in ETA_T[1:] if st >= e)

def phone_state(t):
    st = story_t(t)
    if RING[0] <= st < UPD: return 'call'
    return 'track'

PW, PH = 400, 720
SH_CALL = None
def phone_layer(state, ns, ek, talk=0):
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    if state == 'call':
        pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(36, 52, 92))
        pd.text((S(PW / 2), S(96)), 'מוקד המשלוחים', font=font(S(34), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(140)), 'שיחה נכנסת...', font=font(S(26), 800), fill=(180, 196, 230), anchor='mm')
        lay.alpha_composite(SH_CALL[talk], (int(S(PW / 2)) - SH_CALL[talk].width // 2, int(S(170))))
        pd = ImageDraw.Draw(lay)
        E(pd, PW / 2 - 90, 640, 40, 40, fill=RED); E(pd, PW / 2 + 90, 640, 40, 40, fill=GREEN)
        return lay
    pd.rectangle([S(14), S(66), S(PW - 14), S(132)], fill=BF)
    pd.text((S(PW / 2), S(99)), 'מעקב משלוח', font=font(S(38), 900), fill=ORANGE, anchor='mm')
    # the box (ep34's cart)
    pd.rounded_rectangle([S(110), S(150), S(PW - 110), S(240)], radius=S(10), fill=(214, 168, 112), outline=(120, 80, 40), width=iw(4))
    pd.rectangle([S(PW / 2 - 14), S(150), S(PW / 2 + 14), S(240)], fill=(236, 206, 150))
    pd.text((S(PW / 2), S(268)), 'מארז חטיפים ענק', font=font(S(26), 800), fill=(70, 70, 80), anchor='mm')
    rows = ['יצא מהמחסן', 'נחת בישראל', 'בדרך אליך היום']
    for k, lab in enumerate(rows):
        y = 312 + k * 60; done = k < ns
        pd.text((S(PW - 50), S(y)), lab, font=font(S(32), 900 if done else 700), fill=INK if done else (170, 172, 184), anchor='rm')
        if done:
            E(pd, 64, y, 19, 19, fill=GREEN); line(pd, [(55, y), (62, y + 8), (75, y - 8)], WHITE, 5)
        else:
            pd.ellipse([S(46), S(y - 18), S(82), S(y + 18)], outline=(180, 184, 196), width=iw(4))
        if k < 2: line(pd, [(64, y + 22), (64, y + 38)], GREEN if k + 1 < ns else (200, 204, 214), 5)
    # the route bar: warehouse → plane → truck → house pin
    y = 514; x0, x1 = 54, PW - 54
    pd.rounded_rectangle([S(x0), S(y - 7), S(x1), S(y + 7)], radius=S(7), fill=(220, 224, 232))
    prog = [0.0, 0.33, 0.62, 0.80][min(ns, 3)]
    if ek >= 1: prog = [0.80, 0.80, 0.87, 0.94, 1.0][ek]
    xp = x1 - (x1 - x0) * prog     # RTL: from the right (warehouse) to the left (home)
    pd.rounded_rectangle([S(xp), S(y - 7), S(x1), S(y + 7)], radius=S(7), fill=GREEN)
    E(pd, x0 + 4, y - 18, 16, 16, fill=RED); poly(pd, [(x0 - 8, y - 12), (x0 + 16, y - 12), (x0 + 4, y + 6)], fill=RED)
    pd.rounded_rectangle([S(xp - 22), S(y - 20), S(xp + 22), S(y + 10)], radius=S(6), fill=ORANGE, outline=(110, 50, 10), width=iw(3))
    if ek == 0:
        pd.text((S(PW / 2), S(574)), 'עדכון הבא בקרוב', font=font(S(28), 800), fill=(120, 124, 136), anchor='mm')
    elif ek < 4:
        pd.rounded_rectangle([S(40), S(546), S(PW - 40), S(604)], radius=S(29), fill=BLUE)
        pd.text((S(PW / 2), S(575)), f'השליח בעוד {4 - ek} דק׳', font=font(S(34), 900), fill=WHITE, anchor='mm')
    else:
        pd.rounded_rectangle([S(40), S(546), S(PW - 40), S(604)], radius=S(29), fill=GREEN)
        pd.text((S(PW / 2), S(575)), 'השליח ליד הבית!', font=font(S(34), 900), fill=WHITE, anchor='mm')
    pd.text((S(PW / 2), S(646)), 'כתובת למשלוח: הכתובת הרשומה', font=font(S(22), 800), fill=(150, 152, 162), anchor='mm')   # the plant
    return lay

_PHC = {}
def phone_at(t):
    st = phone_state(t)
    talk = 0
    if st == 'call':
        sv = voice_v(t, 'sharit'); talk = 2 if sv > 0.3 else (1 if sv > 0.1 else 0)
    key = (st, n_steps(t), eta_k(t), talk)
    if key not in _PHC:
        if len(_PHC) > 40: _PHC.clear()
        _PHC[key] = phone_layer(*key)
    return _PHC[key]

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    E21.shadow_paste(img, lay, c, 100, (16, 20), 12)

burst = E18.burst

# ------------------------------------------------------------------ the set: his own front door (new)
DOOR_X0, DOOR_X1, DOOR_Y0, DOOR_Y1 = 40, 430, 250, 1720
HANDLE = (395, 1130)
def build_home_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):                                   # warm hallway wall
        v = y / H; d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(246, 222, v)), int(lerp(232, 200, v)), int(lerp(206, 168, v))))
    d.rectangle([0, S(1720), W * K, H * K], fill=(196, 170, 140))   # floor tiles
    for x in range(-40, W, 180): line(d, [(x, 1720), (x - 120, 1920)], (176, 150, 122), 4)
    line(d, [(0, 1820), (W, 1820)], (176, 150, 122), 4)
    d.rectangle([0, S(1700), W * K, S(1724)], fill=(150, 120, 92))                       # baseboard
    # coat hooks + a framed photo of grandma's palm tree (Eilat, the registered address)
    d.rounded_rectangle([S(760), S(380), S(1000), S(560)], radius=S(8), fill=(150, 104, 66), outline=(96, 64, 38), width=iw(5))
    for y in range(398, 544, 6):
        d.rectangle([S(778), S(y), S(982), S(y + 6)], fill=m.lerpc((120, 190, 240), (255, 214, 160), (y - 398) / 146))
    E(d, 940, 440, 22, 22, fill=(255, 210, 80))
    capsule(d, (840, 544), (850, 460), 10, (130, 90, 60))
    for a in (-150, -110, -60, -20, 20):
        r_ = math.radians(a); line(d, [(850, 460), (850 + 46 * math.cos(r_), 460 + 26 * math.sin(r_) + 14)], (60, 150, 70), 8)
    d.rectangle([S(560), S(330), S(720), S(346)], fill=(120, 84, 54))
    for x in (590, 640, 690): capsule(d, (x, 346), (x, 380), 10, (90, 90, 96))
    # the door frame + door
    d.rectangle([S(DOOR_X0 - 26), S(DOOR_Y0 - 26), S(DOOR_X1 + 26), S(DOOR_Y1)], fill=(236, 230, 220), outline=(150, 140, 126), width=iw(5))
    door_panel(d, closed=True)
    # doormat
    poly(d, [(60, 1760), (420, 1760), (450, 1860), (30, 1860)], fill=(150, 96, 60), outline=(96, 60, 36), width=4)
    d.text((S(240), S(1812)), 'ברוכים הבאים', font=font(S(38), 900), fill=(236, 210, 170), anchor='mm')
    return img

def door_panel(d, closed=True, k=0.0):
    """closed door, or swung open by k (0..1): the panel shrinks toward the hinge on the left"""
    x0, x1, y0, y1 = DOOR_X0, DOOR_X1, DOOR_Y0, DOOR_Y1
    if not closed:
        d.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=(96, 98, 110))             # the landing behind: empty
        d.rectangle([S(x0), S(y0 + 980), S(x1), S(y1)], fill=(130, 130, 138))
        for yy in range(y0 + 300, y0 + 980, 130): line(d, [(x0 + 40, yy), (x1 - 10, yy - 40)], (120, 122, 134), 6)   # stair rail
        d.rectangle([S(x0 + 120), S(y0 + 360), S(x1 - 40), S(y0 + 980)], fill=(110, 80, 56))                   # the neighbour's shut door
        E(d, x1 - 80, y0 + 690, 14, 14, fill=(220, 190, 80))
        xr = lerp(x1, x0 + 70, ease_out(k))
        poly(d, [(x0, y0), (xr, y0 + 60 * k), (xr, y1 - 60 * k), (x0, y1)], fill=(150, 92, 52), outline=(90, 52, 26), width=6)
        return
    d.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=(160, 100, 56), outline=(90, 52, 26), width=iw(6))
    for (a, b) in ((300, 900), (1000, 1640)):
        d.rounded_rectangle([S(x0 + 50), S(a), S(x1 - 50), S(b)], radius=S(10), outline=(120, 72, 36), width=iw(7))
    E(d, (x0 + x1) / 2, 560, 22, 22, fill=(40, 40, 46), outline=(200, 170, 80), width=5)   # peephole
    d.rounded_rectangle([S(HANDLE[0] - 64), S(HANDLE[1] - 14), S(HANDLE[0] + 8), S(HANDLE[1] + 14)], radius=S(10), fill=(220, 190, 80), outline=(120, 96, 30), width=iw(3))
    E(d, HANDLE[0], HANDLE[1], 22, 22, fill=(220, 190, 80), outline=(120, 96, 30), width=4)
    d.rounded_rectangle([S(HANDLE[0] - 12), S(HANDLE[1] + 50), S(HANDLE[0] + 12), S(HANDLE[1] + 100)], radius=S(6), fill=(120, 96, 30))   # lock

def base_cat():
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.3); return st

# ------------------------------------------------------------------ close-up: cat + phone (the tracking page), door at left
HXP, HYP, FP = (780, 940, 2.0) if BIGF else (760, 960, 1.78)

def cat_close_state(t):
    st = base_cat(); rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    if t < COLD_END:                 # cold open: "בדרך אליך היום! היום!" — bouncing, ecstatic
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28, look=(-22, 6), blush=1.0)
        rot = 7 * math.sin(t * 11); dy = -30 * abs(math.sin(t * 8)) - 10 * v
    elif t < L[2]:                   # the want: dreamy, glances at the door on "מחכה ליד הדלת."
        glance = t >= L[1] + ss(1, 1) - 0.05
        st.update(lid=0.15, pupil='big', brow='none', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-14,
                  look=(-24, 8) if not glance else (-34, -4), blush=0.8)
        rot = 3 * math.sin(t * 4); dy = -8 * v
    elif t < RING[0]:                # the first two steps: nodding, pleased, then "נחת בישראל!" excited
        st.update(lid=0.1, pupil='big', brow='up' if t >= L[3] else 'none', mouth=cat_mouth(t, rest='smile', loud='w'),
                  ear_dy=-16 if t < L[3] else -28, look=(-24, 10), blush=0.7 + 0.3 * (t >= L[3]))
        for c_ in (CHK1, CHK2):
            if c_ <= t < c_ + 0.5: dy -= 16 * math.exp(-(t - c_) * 6)
        rot = 2 * math.sin(t * 5) + (5 * math.sin((t - L[3]) * 20) * math.exp(-(t - L[3]) * 3) if t >= L[3] else 0); dy += -10 * v
    elif t < L[900]:                 # the call: "שרית?! גם פה?" — shocked
        u = t - RING[0]
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), sweat=0.6, ear_dy=-26 * math.exp(-u * 2), look=(-30, 4))
        rot = 6 * math.sin(u * 28) * math.exp(-u * 3); dy = -14 * v
    elif t < UPD:                    # "שנייה, מותק." — deadpan wait
        st.update(lid=0.55, pupil='normal', brow='annoyed', mouth='flat', look=(-26, 8), ear_droop=0.3)
    else:                            # "בדרך אליך היום! היום!" in context
        u = t - UPD
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28, look=(-22, 6), blush=1.0)
        rot = 6 * math.sin(u * 11); dy = -26 * abs(math.sin(u * 8)) - 10 * v
    return st, rot, dy

def scene_close(t, i, scramble=False):
    img = HOME.copy()
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_close_state(t)
    E(d, HXP, 1700, 430, 450, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1760, 200, 300, fill=CREAM)
    pc = (270, 1110 + 5 * math.sin(t * 8)); sc = 0.98
    if t < COLD_END: pc = (270 + 10 * math.sin(t * 30), 1110 - 12 * abs(math.sin(t * 8)))
    if RING[0] <= t < RING[0] + 0.4: sc += 0.18 * math.exp(-(t - RING[0]) * 9); pc = (270 + 8 * math.sin(t * 90), 1110)
    grip = (pc[0] - 190, pc[1] + 150)
    capsule(d, (HXP - 240, 1520), grip, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP, HYP + dy, FP, rot)
    paste_rot(img, phone_at(t), pc, -6, sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, grip, 70, 0.9)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= t < c_ + 0.5: burst(img, (pc[0], pc[1] - 60), t - c_, (120, 255, 160), 160, 10, 0.4)
    if RING[0] <= t < RING[0] + 0.45: burst(img, pc, t - RING[0], (150, 190, 255), 220, 12, 0.45)
    return img

# ------------------------------------------------------------------ the door shot: wait, the bell, the peak
DHX, DHY, DFP = 720, 900, 1.62
def door_state(t):
    st = base_cat(); rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    if t < L[102]:                   # waiting: ETA runs down, eyes flick door ↔ phone, foot taps
        k = eta_k(t)
        st.update(lid=0.2, pupil='big', brow='up', mouth='smile_small' if k >= 3 else 'flat', ear_dy=-16 - 4 * k,
                  look=(-36, -6) if int(t * 3) % 2 == 0 else (-10, 26), blush=0.4 + 0.15 * k)
        dy = -6 * abs(math.sin(t * 12)); rot = 2 * math.sin(t * 6)
    elif t < BELL:                   # "יאללה!"
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28, look=(-30, 0), blush=1.0)
        dy = -18 * v
    elif t < L[4]:                   # the bell → "יש!!!" gold, jumping
        u = t - BELL
        st.update(lid=0.0, pupil='big' if u > 0.15 else 'tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-30, blush=1.0, look=(-34, -4))
        dy = -34 * abs(math.sin(u * 9)) * math.exp(-u * 0.8); rot = 5 * math.sin(u * 11)
    elif t < HOLD[0]:                # "סוף סוף... הוא פה." — paw going to the handle
        st.update(lid=0.3, pupil='normal', brow='none', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-12, blush=1.0, look=(-30, 8))
        rot = -4 + 2 * math.sin(t * 3)
    elif t < BREAK:                  # THE PEAK: eyes closed, paw on the handle, hush
        st.update(eye_mode='closed', mouth='smile', ear_dy=-24, blush=1.0, look=(0, -6)); rot = -7; dy = -8
    else:                            # the door is open: nobody. frozen.
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-20 * math.exp(-u * 4), look=(-36, -4) if u < 0.8 else (-24, -40),
                  twitch=(0.8 < u < 1.8 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.5), ear_droop=0.6 * clamp(u / 0.3))
        dy = -6
    return st, rot, dy

def handle_paw(t):
    """screen-left paw: reaches the handle during the peak line, rests on it through the hold, presses at the break"""
    if t < L[4] - 0.1: return None, 0.0
    k = ease_io(clamp((t - (L[4] - 0.1)) / 0.7))
    p = lerp2((DHX - 330, 1420), (HANDLE[0] - 10, HANDLE[1] - 8), k)
    press = 0.0
    if t >= BREAK - 0.08: press = clamp((t - (BREAK - 0.08)) / 0.08)
    return (p[0], p[1] + 20 * press), press

def scene_door(t, i, opened=None):
    img = HOME.copy()
    d = ImageDraw.Draw(img)
    if opened is None: opened = t >= BREAK
    if opened:
        door_panel(d, closed=False, k=clamp((t - BREAK) / 0.22))
        d = ImageDraw.Draw(img)
    st, rot, dy = door_state(t)
    E(d, DHX, 1640, 400, 430, fill=FUR, outline=OUT, width=7)
    E(d, DHX, 1700, 190, 290, fill=CREAM)
    # the phone (small, by his cheek) while waiting
    if t < BELL + 0.3:
        pc = (DHX + 230, 1200 + 4 * math.sin(t * 9))
        capsule(d, (DHX + 230, 1460), (pc[0] + 20, pc[1] + 170), 100, FUR, OUT, 4)
        paste_rot(img, phone_at(t), pc, 8, 0.72)
        d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 20, pc[1] + 170), -10, 0.8)
    hp, press = handle_paw(t)
    if hp is not None and not opened:
        capsule(d, (DHX - 230, 1450), hp, 104, FUR, OUT, 4)
    E12.paste_head(img, st, i, DHX, DHY + dy, DFP, rot)
    d = ImageDraw.Draw(img)
    if hp is not None and not opened: E12.big_paw(d, hp, 20, 0.8)
    if opened:   # the arm, still out, in the air where the handle was
        u = clamp((t - BREAK) / 0.2); p = lerp2(HANDLE, (HANDLE[0] + 80, HANDLE[1] + 40), u)
        capsule(d, (DHX - 230, 1450), p, 104, FUR, OUT, 4); E12.big_paw(d, p, 20, 0.8)
    if BELL <= t < BELL + 0.6:   # the bell rings: rings over the door
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        k = int((t - BELL) * 10) % 2; cc = (DOOR_X1 - 40, DOOR_Y0 + 120)
        for r in (90, 150):
            od.arc([S(cc[0] - r), S(cc[1] - r), S(cc[0] + r), S(cc[1] + r)], 180, 360, fill=(255, 236, 120, 230 if k else 120), width=iw(10))
        img.alpha_composite(ov)
        d = ImageDraw.Draw(img); d.text((S(cc[0] + 10), S(cc[1] - 190)), 'דינג דונג!', font=font(S(64), 900), fill=WHITE, anchor='mm', stroke_width=iw(7), stroke_fill=INK)
    if GOLDT <= t < L[4]: E18.confetti(img, t - GOLDT + 0.3)
    if BREAK <= t < BREAK + 0.4: burst(img, (240, 900), t - BREAK, (200, 200, 210), 180, 12, 0.4)
    return img

# ------------------------------------------------------------------ grandma in Eilat (top of the split): at HER door, the box, signing
def gran_state(t):
    st = E10.gran_base()
    st.update(hand_r=(520, 600), hand_l=(170, 760))
    g = voice_v(t, 'grandma')
    if t < L[5] + ss(5, 1) - 0.1:                      # "חמוד!"
        u = t - L[5]
        st.update(lid=0.1, mouth='grin' if g < 0.15 else 'talk', look=(8, 0), blush=1.0, rot=-6 * math.exp(-u * 4))
    else:                                               # "הגיע לך משהו!" — beaming, signing
        st.update(lid=0.3, mouth='talk' if g > 0.12 else 'grin', look=(14, 16), rot=3 * math.sin(t * 2.5), blush=0.9)
    return st

G_GF = 1.55
G_ORIGIN = (470 - 350 * G_GF, 760 - 300 * G_GF)
def scene_gran(t, i):
    img = GRAN_BG.copy()
    d = ImageDraw.Draw(img)
    # her open front door at the right edge, the stairwell light
    d.rectangle([S(860), S(300), S(1080), S(1500)], fill=(250, 240, 210))
    poly(d, [(860, 300), (960, 340), (960, 1460), (860, 1500)], fill=(120, 160, 190), outline=(60, 90, 110), width=6)
    lay = E10.gran_draw(gran_state(t), i)
    lay = lay.resize((int(lay.width * G_GF), int(lay.height * G_GF)), Image.BICUBIC)
    img.alpha_composite(lay, dest=(int(S(G_ORIGIN[0])), int(S(G_ORIGIN[1]))))
    d = ImageDraw.Draw(img)
    # the box in her arms (the cat's Black Friday box)
    bx, by = 330, 1250
    d.rounded_rectangle([S(bx - 250), S(by - 170), S(bx + 250), S(by + 190)], radius=S(12), fill=(214, 168, 112), outline=(110, 72, 36), width=iw(7))
    d.rectangle([S(bx - 30), S(by - 170), S(bx + 30), S(by + 190)], fill=(236, 206, 150))
    d.rounded_rectangle([S(bx + 50), S(by - 120), S(bx + 230), S(by - 20)], radius=S(8), fill=WHITE, outline=(120, 120, 130), width=iw(3))
    d.text((S(bx + 140), S(by - 70)), 'בלאק פריידיי', font=font(S(28), 900), fill=INK, anchor='mm')
    E(d, bx - 200, by - 120, 46, 36, fill=SH.SKIN if False else (240, 196, 166), outline=(120, 76, 54), width=5)
    # the courier's arm from the right, holding the signature pad; grandma's pen hand on it
    u = t - L[5]
    pad = (810 - 30 * ease_out(clamp(u / 0.3)), 1150)
    capsule(d, (1120, 1120), (pad[0] + 120, pad[1] + 60), 90, (60, 110, 200), (30, 60, 120), 4)
    d.rounded_rectangle([S(pad[0] - 150), S(pad[1] - 110), S(pad[0] + 130), S(pad[1] + 110)], radius=S(16), fill=(40, 40, 46))
    d.rounded_rectangle([S(pad[0] - 132), S(pad[1] - 92), S(pad[0] + 112), S(pad[1] + 92)], radius=S(10), fill=(240, 244, 248))
    d.text((S(pad[0] + 96), S(pad[1] - 62)), 'חתימה:', font=font(S(28), 900), fill=(90, 90, 100), anchor='rm')
    sig = clamp((u - 0.4) / 1.4)
    pts = [(pad[0] + 80 - 200 * k / 30, pad[1] + 10 + 24 * math.sin(k * 0.9) * (1 - k / 40)) for k in range(int(30 * sig) + 1)]
    if len(pts) > 1: line(d, pts, (30, 60, 170), 6)
    pen = pts[-1]
    E(d, pen[0] + 30, pen[1] - 40, 48, 40, fill=(240, 196, 166), outline=(120, 76, 54), width=5)
    capsule(d, (pen[0] + 30, pen[1] - 40), pen, 12, (230, 60, 80), (120, 20, 40), 2)
    d.rounded_rectangle([S(pad[0] - 120), S(pad[1] + 46), S(pad[0] + 100), S(pad[1] + 84)], radius=S(8), fill=GREEN)
    d.text((S(pad[0] - 10), S(pad[1] + 65)), 'נמסר ✓' if False else 'נמסר', font=font(S(26), 900), fill=WHITE, anchor='mm')
    if 0 <= u < 0.4: burst(img, (bx, by - 200), u, (255, 236, 120), 200, 12, 0.4)
    return img

def split_frame(t, i):
    g = scene_gran(t, i)
    c = scene_door(t, i, opened=True)
    top = g.crop((0, S(470), W * K, S(1430))).resize((W, 960), Image.LANCZOS)
    bot = c.crop((0, S(900 - 560), W * K, S(900 + 400))).resize((W, 960), Image.LANCZOS)
    fr = Image.new('RGBA', (W, H)); fr.paste(top, (0, 0)); fr.paste(bot, (0, 960))
    d = ImageDraw.Draw(fr); d.rectangle([0, 954, W, 966], fill=(20, 20, 26))
    # place tags: "אילת" (top) / "אצלו" (bottom)
    for y, lab in ((880, 'אילת'), (1010, 'הבית שלו')):
        tw = d.textlength(lab, font=font(40, 900)) + 50
        d.rounded_rectangle([W - 40 - tw, y - 32, W - 40, y + 32], radius=32, fill=(20, 20, 26))
        d.text((W - 40 - tw / 2, y), lab, font=font(40, 900), fill=WHITE, anchor='mm')
    return fr

# ------------------------------------------------------------------ overlays
CHIPS = [('מחסן', 820, CHK1), ('ישראל', 540, CHK2), ('היום', 260, CHK3)]
def chips(frame, t, y=330):
    if t < COLD_END or t < CHK1 - 0.6 or t >= BREAK: return
    gold = t >= GOLDT
    d = ImageDraw.Draw(frame)
    for k_, (lab, cx, tk) in enumerate(CHIPS):
        ok = t >= tk
        fill = GOLD if gold else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or gold) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if gold and t - GOLDT < 0.5: sc = 1 + 0.25 * math.exp(-(t - GOLDT) * 8) * math.cos((t - GOLDT) * 20)
        w, h = 220 * sc, 70 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 22 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], outline=ink, width=4)

def eta_badge(frame, t, y=450):
    """the live ETA in screen space during the wait (the counter in front of the viewer)"""
    k = eta_k(t)
    if k == 0 or t >= BELL + 0.6 or t < COLD_END: return
    d = ImageDraw.Draw(frame)
    lab = f'השליח בעוד {4 - k} דק׳' if k < 4 else 'השליח ליד הבית!'
    u = t - ETA_T[k - 1]
    sc = 1 + 0.3 * math.exp(-u * 10) * math.cos(u * 20) if 0 <= u < 0.5 else 1.0
    f = font(int(52 * sc), 900); tw = d.textlength(lab, font=f) + 70; h = 92 * sc
    d.rounded_rectangle([W / 2 - tw / 2, y - h / 2, W / 2 + tw / 2, y + h / 2], radius=h / 2, fill=GREEN if k == 4 else BLUE, outline=(10, 10, 12), width=5)
    d.text((W / 2, y + 2), lab, font=f, fill=WHITE, anchor='mm')

def rewind_overlay(frame, t):
    frame.alpha_composite(m.SCAN)
    d = ImageDraw.Draw(frame)
    rng = random.Random(int(t * 120))
    for _ in range(5):
        y = rng.uniform(300, 1700); h = rng.uniform(4, 14)
        d.rectangle([0, y, W, y + h], fill=(255, 255, 255, 70))
    for x0 in (300, 344):
        d.polygon([(x0 + 44, 900), (x0, 930), (x0 + 44, 960)], fill=WHITE, outline=(10, 10, 12), width=5)
    d.text((610, 930), 'שלושה ימים קודם', font=font(66, 900), fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(10, 10, 12))

def sub_layer(lines, fill, size=64):
    f = font(size, 900); lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

# ------------------------------------------------------------------ frame
HOME = GRAN_BG = PILL_EP = PILL_Q = None
def init_all():
    global HOME, GRAN_BG, PILL_EP, PILL_Q, SH_CALL
    m.init_static()
    HOME = build_home_bg()
    E12.SHARP = True
    GRAN_BG = E12.build_gran_bg()
    SH_CALL = []
    for mo in ('lazy', 'talk', 'grin'):     # Sharit on the dispatcher call screen, 3 mouth states
        st = SH.base(); st.update(mouth=mo, lid=0.6, look=(0, 6), snack=False)
        lay = SH.draw(st, 3 if mo == 'talk' else 0).crop((S(60), S(60), S(640), S(700)))
        SH_CALL.append(lay.resize((S(330), int(S(330) * lay.height / lay.width)), Image.LANCZOS))
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'close':
        z = 1.04 + 0.02 * pu; cy = 980; cx = 540
        if a == 0.0:
            z = 1.10 + 0.04 * t; cx, cy = 470, 900
            if t < 0.3: z = 1.30 - 0.20 * ease_out(t / 0.3)
        if RING[0] <= t < UPD: z, cx, cy = 1.12, 430, 1000          # onto the call screen + his face
    elif name == 'door':
        z, cx, cy = 1.06 + 0.015 * pu, 560, 960
        if HOLD[0] <= t < BREAK:
            k = ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0]))); z += 0.08 * k; cx -= 60 * k
    elif name == 'rewind':
        z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'frozen':
        z, cx, cy = 1.30 + 0.03 * pu, 680, 900
    if name in ('close', 'door') and a > 0 and pu < 0.2:
        z = z + 0.07 * (1 - ease_out(pu / 0.2))
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'split':
        frame = split_frame(t, i)
        if t - a < 0.25:
            z = lerp(1.12, 1.0, ease_out((t - a) / 0.25)); cw, ch = W / z, H / z
            frame = frame.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.LANCZOS)
    else:
        if name == 'rewind':
            u = (t - a) / (b - a)
            img = scene_close(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i, scramble=True)
        elif name in ('door', 'frozen'): img = scene_door(t, i)
        else: img = scene_close(t, i)
        z, ccx, ccy = camera(t)
        shake = 0.0
        if t < 0.5: shake = 18 * math.exp(-t * 5)
        if 0 <= t - RING[0] < 0.3: shake = 12 * math.exp(-(t - RING[0]) * 8)
        if 0 <= t - BELL < 0.3: shake = 14 * math.exp(-(t - BELL) * 8)
        if shake:
            rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
        if z > 1.0005:
            cw, ch = W * K / z, H * K / z
            left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
            img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
        frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(60 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BELL, GOLDT, BREAK):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    if name not in ('split', 'frozen'):
        chips(frame, t)
        if name == 'door': eta_badge(frame, t)
    for t0, t1, lines in TOPCAPS:
        if t0 <= t < t1: m.paste_center(frame, m.caption_layer(lines, 96, WHITE), W / 2, 270)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            who = SPEAKER[li]
            col = GRAN_SUB if who == 'grandma' else (SHARIT_SUB if who == 'sharit' else WHITE)
            m.paste_center(frame, sub_layer(lines, col), W / 2, 170 if (who == 'grandma' and name in ('split', 'frozen')) else 1560)
    if t < COLD_END or (T0 <= t < L[2] - 0.1) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + hallway room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(36)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'sharit':             # through the phone
            y = m.bandpass(y, 300, 3400) * 1.4
        add(voice, y, s0, 0.95)
    def whoosh(t0, g=0.06, wl=0.16): add(sfx, m.bandpass(nz(wl), 600, 5000) * np.sin(np.pi * tt_(wl) / wl) ** 2, t0 - 0.08, g)
    def thud(g=0.9):
        tt = tt_(0.45); freq = 150 * np.exp(-tt * 6) + 42
        return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) + m.lowpass(nz(0.45), 420) * np.exp(-tt * 30) * 0.8) * g
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def buzz(t0, g=0.16, ln=0.32):
        tt = tt_(ln); add(sfx, m.lowpass(np.sign(np.sin(2 * np.pi * 110 * tt)), 1200) * np.exp(-tt * 4), t0, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def tick(t0, g=0.05): add(sfx, m.tone(1500, 0.03, harm=((1, 1),), decay=60), t0, g)
    def cheer(t0, ln=1.0, g=0.10):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    add(sfx, thud(0.9), 0.0); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), 0.0, 0.4)
    for k in range(6): add(sfx, m.lowpass(nz(0.05), 300) * np.exp(-tt_(0.05) * 50), 0.12 + k * 0.28, 0.25)   # bouncing feet in the cold open
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(HOLD[0]), 150, 900) * 0.6, 0.0, 0.010)                       # hallway room tone
    add(sfx, m.bandpass(nz(DUR - BREAK + 0.3), 150, 900) * 0.6, BREAK, 0.012)
    for name, a, b in SHOTS[2:]:
        if name not in ('frozen',): whoosh(a)
    for c_ in (CHK1, CHK2, CHK3): buzz(c_ - 0.05, 0.08, 0.2); check(c_, 0.15)
    tc = RING[0]
    while tc < RING[1]:                                                                  # the dispatcher call rings
        add(sfx, m.tone(1046.5, 0.05, harm=((1, 1), (2, 0.2)), decay=30), tc, 0.07); tc += 0.07
    add(sfx, m.tone(523.3, 0.12, harm=((1, 1),), decay=20), UPD - 0.05, 0.10)          # call ends
    for k, e in enumerate(ETA_T):                                                         # ETA updates: ticks, foot taps
        tick(e, 0.08); check(e, 0.06 if k < 3 else 0.12, k == 3)
    for k in range(5): add(sfx, m.lowpass(nz(0.04), 260) * np.exp(-tt_(0.04) * 60), WAIT[0] + 0.15 + k * 0.3, 0.22)
    for k, f in enumerate((659.3, 523.3)):                                                # ding-dong
        add(sfx, m.tone(f, 0.9, harm=((1, 1), (2.0, 0.3), (3.0, 0.1)), decay=3), BELL + k * 0.32, 0.32)
    check(GOLDT, 0.2, True); cheer(GOLDT + 0.1, L[4] - GOLDT, 0.06)
    heartbeat(HOLD[0] + 0.04); heartbeat(HOLD[0] + 0.30, 0.5)
    tt = tt_(0.18); add(sfx, m.highpass(nz(0.18), 900) * np.exp(-tt * 18), BREAK - 0.08, 0.35)        # the handle clacks
    tt = tt_(0.6); add(sfx, np.sin(2 * np.pi * np.cumsum(420 + 260 * np.sin(2 * np.pi * 3 * tt)) / SR) * np.sin(np.pi * tt / 0.6) * 0.5, BREAK, 0.10)   # door creak
    add(sfx, m.bandpass(nz(0.9), 300, 1500) * np.exp(-tt_(0.9) * 4), BREAK + 0.1, 0.05)                  # empty landing air
    add(sfx, thud(0.6), BREAK + 0.06)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), L[5] + ss(5, 1), 0.20)
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
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', T0)
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'RING', [round(x, 2) for x in RING], 'UPD', round(UPD, 2),
              'WAIT', [round(x, 2) for x in WAIT], 'BELL', round(BELL, 2), 'GOLDT', round(GOLDT, 2),
              'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep36_contact.png')); print('ok'); return
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
