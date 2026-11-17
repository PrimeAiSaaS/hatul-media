#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 38: החזרה (season 8 "בלאק פריידיי" finale, VOICED, built 17.11 under §P, ~21 s).
Voices = voice bank 2026-11-13 lines 3800–3804 (Benji = cat, Delia = Sharit, Vera = the app) + 2703 "שרית?! גם פה?"
+ 2509 "חופשי. סוף סוף... חופשי." (the peak, reuse) + stock 9000 "שנייה, מותק." + 9103 "יש!!!", prepared by voice/ep38_prep.py.
Set: a post-office counter (window 3), parcel shelf, LED board, the wall sign "החזרות · חלון 3" with its grey small print.
Want: return the wrong item — the "mega box" was one tiny 30 g bag ("שקית אחת. שלושים גרם. מחזיר.").
Plant: the grey small print "* החזרה תטופל כהזמנה חדשה" — on the wall sign behind him from the want line, and at the
bottom of the return form on the counter (cold open, the form slide-in, the signing). Never pointed at.
Climb (3 chips): טופס ✓ (he signs) → מדבקה ✓ (the label slapped on the bag) → הוחזר ✓ STAMP gold, the queue cheers, "יש!!!".
Peak: "חופשי. סוף סוף... חופשי." — leaning back, eyes closed, hush + heartbeat.
Break (full_circle): the phone slams in by his face: "ההזמנה שלך יצאה לדרך · מארז ענק · $89" (the app voice reads it):
the return was processed as a new order. Chips drain; frozen face; whip into the cold open (loop).
No music (voiced rule): voices + SFX + post-office room tone. Serial pills "פרק 38" + live ticket number (hud.stage_of, §O4).

  python3 voice/ep38_prep.py
  python3 ep38.py times | test t1 t2 ... | render   -> out/ep38_hachzara.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep8 as E8
import ep12 as E12
import ep13 as E13
import ep18 as E18
import ep21_v1 as V1
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep38', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 104, 226)
ORANGE = (255, 120, 30); SHARIT_SUB = (255, 182, 210); IVRSUB = (160, 214, 255)
QUEUE = int(os.environ.get('QUEUE', '446'))
EP_LABEL = 'פרק 38'
OUTNAME = os.environ.get('OUTNAME', 'ep38_hachzara')
LIMIT = float(os.environ.get('LIMIT', '0'))
SMALL = '* החזרה תטופל כהזמנה חדשה'

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
COLD_END = round(D[3] + 0.50, 2)            # cold open = 3803 "הוחזר!" + the STAMP (the loudest beat of the climb)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[0] = T0 + 0.05                            # want: "שקית אחת. שלושים גרם. מחזיר." — the tiny bag held up in the queue
FF = (L[0] + D[0] + 0.10, L[0] + D[0] + 1.85)   # x64: the board races to his number
DING = FF[1]
ARRIVE = DING + 0.05                        # Sharit slides into window 3
L[27] = ARRIVE + 0.30                       # "שרית?! גם פה?"
L[1] = L[27] + D[27] + 0.18                 # Sharit: "טופס החזרה, מותק."
FORMIN = L[1] + 0.10
L[2] = L[1] + D[1] + 0.15                   # "חתמתי. וגם מדבקה."
SIGN = (L[2] - 0.05, L[2] + ss(2, 1) - 0.05)
CHK1 = L[2] + ss(2, 1) - 0.10               # signed
LABEL = L[2] + ss(2, 1) + 0.35              # the label slapped on the bag
CHK2 = LABEL + 0.05
L[90] = L[2] + D[2] + 0.20                  # Sharit, chill: "שנייה, מותק." — the stamp rises sloooowly
RAISE = L[90]
L['3b'] = L[90] + D[90] + 0.15              # "הוחזר!" in context
STAMP = L['3b'] + 0.06
CHK3 = STAMP; GOLDT = STAMP + 0.05
L[103] = L['3b'] + D[3] + 0.30              # "יש!!!"
L[25] = L[103] + D[103] + 0.40              # "חופשי. סוף סוף... חופשי." (peak)
EYES = L[25] + ss(25, 1) - 0.1
HOLD = (L[25] + D[25] + 0.03, L[25] + D[25] + 0.50)
BREAK = HOLD[1]                             # the phone slams in
L[4] = BREAK + 0.10                         # the app: "ההזמנה שלך יצאה לדרך."
FREEZE = L[4] + D[4]
DUR = round(FREEZE + 0.42, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(3, 0.0), (0, L[0]), (27, L[27]), (1, L[1]), (2, L[2]), (90, L[90]), (3, L['3b']), (103, L[103]), (25, L[25]), (4, L[4])]
SPEAKER = {0: 'cat', 27: 'cat', 2: 'cat', 25: 'cat', 103: 'cat', 1: 'sh', 3: 'sh', 90: 'sh', 4: 'ivr'}

SUBS = {
    0: [['שקית אחת.'], ['שלושים גרם.'], ['מחזיר.']],
    27: [['שרית?! גם פה?']],
    1: [['טופס החזרה, מותק.']],
    2: [['חתמתי.'], ['וגם מדבקה.']],
    90: [['שנייה, מותק.']],
    3: [['הוחזר!']],
    103: [['יש!!!']],
    25: [['חופשי.'], ['סוף סוף...'], ['חופשי.']],
    4: [['ההזמנה שלך יצאה לדרך.']],
}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]
    starts = [0.0] + [ss(li, k) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 4 and k == len(ch) - 1: b = DUR - 0.25
        if li == 25 and k == len(ch) - 1: b = min(b, HOLD[0] + 0.02)
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('two', 0.0, COLD_END), ('rewind', COLD_END, T0), ('two', T0, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['מחזירים חבילה', 'בבלאק פריידיי?']       # keyword: החזרה / חבילה (F16 pain question)
TOPCAPS = [(0.0, COLD_END, HOOK), (T0, L[0] + D[0] - 0.1, HOOK)]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def story_t(t):
    return L['3b'] + t if t < COLD_END else t

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

# ------------------------------------------------------------------ props
def bag_layer(label=False):
    """the 'mega box' content: one tiny 30 g snack bag"""
    w_, h_ = 200, 230
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    SH.snack_bag(d, (w_ / 2, h_ / 2 + 10), 0, 0.95)
    d.rounded_rectangle([S(w_ / 2 - 54), S(h_ / 2 + 18), S(w_ / 2 + 54), S(h_ / 2 + 58)], radius=S(10), fill=WHITE, outline=(120, 64, 10), width=iw(3))
    d.text((S(w_ / 2), S(h_ / 2 + 38)), '30 גרם', font=font(S(26), 900), fill=INK, anchor='mm')
    if label:
        d.rounded_rectangle([S(16), S(36), S(w_ - 16), S(100)], radius=S(6), fill=(250, 250, 246), outline=(60, 60, 70), width=iw(3))
        for k in range(14): d.rectangle([S(30 + k * 8), S(46), S(30 + k * 8 + (3 if k % 3 else 5)), S(74)], fill=INK)
        d.text((S(w_ - 30), S(86)), 'החזרה', font=font(S(20), 900), fill=RED, anchor='rm')
    return lay

def form_layer(signed=0.0, stamped=False):
    """the return form; the plant = the grey small print at the bottom"""
    w_, h_ = 420, 300
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(w_) - 1, S(h_) - 1], fill=(252, 252, 248), outline=(150, 150, 160), width=iw(3))
    d.rectangle([0, 0, S(w_), S(54)], fill=RED)
    d.text((S(w_ / 2), S(28)), 'טופס החזרה', font=font(S(34), 900), fill=WHITE, anchor='mm')
    for k in range(3):
        d.rounded_rectangle([S(150), S(78 + k * 38), S(w_ - 26), S(98 + k * 38)], radius=S(5), fill=(208, 212, 222))
        d.rectangle([S(28), S(78 + k * 38), S(130), S(98 + k * 38)], outline=(170, 174, 184), width=iw(2))
    d.line([(S(30), S(218)), (S(w_ - 30), S(218))], fill=(150, 150, 160), width=iw(2))
    d.text((S(w_ - 30), S(204)), 'חתימה:', font=font(S(22), 800), fill=(110, 110, 120), anchor='rm')
    if signed > 0:
        pts = [(lerp(250, 50, u), 200 - 18 * math.sin(u * 19) * (1 - 0.3 * u)) for u in np.linspace(0, clamp(signed), 30)]
        if len(pts) > 1: line(d, pts, (30, 60, 160), 4)
    d.text((S(w_ - 30), S(266)), SMALL, font=font(S(22), 700), fill=(150, 150, 158), anchor='rm')
    if stamped:
        st = Image.new('RGBA', (S(240), S(100)), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([S(4), S(4), S(236), S(96)], radius=S(14), outline=RED + (230,), width=iw(7))
        sd.text((S(120), S(50)), 'הוחזר', font=font(S(54), 900), fill=RED + (230,), anchor='mm')
        st = st.rotate(12, resample=Image.BICUBIC, expand=True)
        lay.alpha_composite(st, dest=(S(90), S(70)))
    return lay

def phone_layer():
    """the break: the app's push"""
    pw, ph = 400, 720
    lay = Image.new('RGBA', (S(pw), S(ph)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(pw) - 1, S(ph) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(pw - 14), S(ph - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(pw / 2 - 56), S(28), S(pw / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.rounded_rectangle([S(30), S(110), S(pw - 30), S(560)], radius=S(26), fill=WHITE, outline=(200, 204, 214), width=iw(3))
    pd.text((S(pw - 56), S(156)), 'החנות', font=font(S(32), 900), fill=(90, 96, 110), anchor='rm')
    pd.text((S(pw / 2), S(240)), 'ההזמנה שלך', font=font(S(44), 900), fill=INK, anchor='mm')
    pd.text((S(pw / 2), S(298)), 'יצאה לדרך!', font=font(S(44), 900), fill=GREEN, anchor='mm')
    pd.rounded_rectangle([S(60), S(346), S(pw - 60), S(446)], radius=S(18), fill=(255, 232, 232), outline=RED, width=iw(4))
    pd.text((S(pw / 2), S(396)), '$89', font=font(S(62), 900), fill=RED, anchor='mm')
    pd.text((S(pw / 2), S(500)), 'מארז ענק · הזמנה חדשה', font=font(S(28), 800), fill=(110, 112, 124), anchor='mm')
    return lay

def stamp_layer():
    w_, h_ = 170, 230
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    E(d, w_ / 2, 50, 46, 46, fill=(60, 40, 30), outline=(20, 12, 8), width=4)
    d.rectangle([S(w_ / 2 - 16), S(80), S(w_ / 2 + 16), S(160)], fill=(90, 60, 40), outline=(20, 12, 8), width=iw(4))
    d.rounded_rectangle([S(10), S(160), S(w_ - 10), S(214)], radius=S(8), fill=(40, 40, 46), outline=(10, 10, 12), width=iw(4))
    d.rectangle([S(16), S(208), S(w_ - 16), S(222)], fill=RED)
    return lay

def paste_rot(img, lay, c, ang=0.0, sc=1.0, a=100):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    V1.shadow_paste(img, lay, c, a, (14, 18), 10)

burst = E18.burst

# ------------------------------------------------------------------ the set: the post-office counter
BOARD_C = (300, 620)
def build_post_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        v = y / H; d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(214, 186, v)), int(lerp(222, 196, v)), int(lerp(236, 214, v))))
    d.rectangle([0, S(1080), W * K, S(1120)], fill=(200, 40, 46))                 # red post stripe
    # parcel shelf on the left (behind Sharit)
    d.rectangle([S(0), S(770), S(470), S(1180)], fill=(120, 84, 54))
    rng = random.Random(38)
    for y in (930, 1100):
        d.rectangle([S(0), S(y), S(470), S(y + 18)], fill=(80, 54, 30))
        x = 20
        while x < 440:
            w_ = rng.uniform(80, 150); h_ = rng.uniform(60, 140)
            d.rectangle([S(x), S(y - h_), S(x + w_), S(y)], fill=(206, 160, 106), outline=(110, 72, 36), width=iw(3))
            d.rectangle([S(x + w_ / 2 - 8), S(y - h_), S(x + w_ / 2 + 8), S(y)], fill=(230, 200, 150))
            x += w_ + 8
    # the LED board frame (numbers drawn per frame)
    d.rounded_rectangle([S(BOARD_C[0] - 230), S(BOARD_C[1] - 110), S(BOARD_C[0] + 230), S(BOARD_C[1] + 110)], radius=S(16), fill=(24, 24, 28), outline=(70, 70, 80), width=iw(6))
    d.text((S(BOARD_C[0]), S(BOARD_C[1] - 72)), 'חלון 3', font=font(S(34), 900), fill=(200, 200, 210), anchor='mm')
    # the returns sign on the right (the plant, behind him)
    x0, y0, x1, y1 = 640, 250, 1040, 560
    d.rounded_rectangle([S(x0 + 8), S(y0 + 10), S(x1 + 8), S(y1 + 10)], radius=S(14), fill=(150, 156, 170))
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(14), fill=(252, 252, 248), outline=(120, 120, 130), width=iw(5))
    d.rectangle([S(x0), S(y0), S(x1), S(y0 + 90)], fill=RED)
    d.text((S((x0 + x1) / 2), S(y0 + 46)), 'החזרות', font=font(S(56), 900), fill=WHITE, anchor='mm')
    d.text((S((x0 + x1) / 2), S(y0 + 150)), 'סניף דואר · חלון 3', font=font(S(40), 900), fill=INK, anchor='mm')
    d.text((S((x0 + x1) / 2), S(y0 + 222)), 'מחזירים · מקבלים כסף', font=font(S(30), 800), fill=(90, 90, 100), anchor='mm')
    d.text((S(x1 - 24), S(y1 - 34)), SMALL, font=font(S(24), 700), fill=(150, 150, 158), anchor='rm')
    img = img.filter(ImageFilter.GaussianBlur(S(1.6)))
    img.alpha_composite(Image.new('RGBA', img.size, (255, 252, 240, 40)))
    return img

def board_num(t):
    s_t = story_t(t)
    if s_t < FF[0]: return QUEUE - 66
    if s_t < FF[1]: return int(lerp(QUEUE - 66, QUEUE, ease_in(clamp((s_t - FF[0]) / (FF[1] - FF[0] - 0.1)))))
    return QUEUE

T_HEAD = (215, 920); TS = 1.32
HX2, HY2, F2 = 815, 950, 1.48
QUEUE_TWO = [('c2', 600, 700, 0.44, 0.4), ('h0', 760, 640, 0.40, 1.6), ('c3', 1010, 700, 0.42, 2.4)]
FORM_C = (470, 1500); BAG_C = (690, 1470)

def sh_dx(t):
    s_t = story_t(t)
    if s_t < ARRIVE: return -900
    return -900 * (1 - ease_out(clamp((s_t - ARRIVE) / 0.3)))

def cat_state(t):
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    s_t = story_t(t)
    if L['3b'] <= s_t < L[103]:             # "הוחזר!" — the stamp: eyes huge, joy rising
        u = s_t - STAMP
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-30, blush=1.0, look=(-26, 14))
        rot = 5 * math.sin(max(0, u) * 14) * math.exp(-max(0, u) * 2); dy = -26 * math.exp(-max(0, u) * 4) if u >= 0 else 0
    elif t < FF[0]:                         # the want: outraged at the tiny bag
        st.update(lid=0.0, pupil='tiny', brow='annoyed', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-18, look=(-18, -4), sweat=0.6, blush=0.0)
        rot = 4 * math.sin(t * 5); dy = -12 * v
    elif t < ARRIVE:                        # x64: waiting, tapping, glancing at the board
        u = (t - FF[0]) / (FF[1] - FF[0])
        st.update(lid=0.5 - 0.4 * u, pupil='normal', brow='none', mouth='flat', look=(-30, -20), ear_droop=0.4 * (1 - u))
        dy = -6 * abs(math.sin(t * 14))
    elif t < L[1]:                          # "שרית?! גם פה?" double take
        u = t - L[27]
        st.update(lid=0.0, pupil='tiny', brow='up', ear_dy=-24 * math.exp(-max(0, u) * 2), mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0, look=(-20, 4))
        if u >= 0: rot = 8 * math.sin(u * 20) * math.exp(-u * 3); dy = -30 * math.exp(-u * 5)
    elif t < L[2]:                          # the form comes
        st.update(lid=0.2, pupil='big', brow='none', mouth='smile', look=(-28, 16), blush=0.5)
    elif t < L[90]:                         # "חתמתי. וגם מדבקה." — proud, busy
        st.update(lid=0.1, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), look=(-24, 18), blush=0.7, ear_dy=-12)
        dy = -10 * v + (-16 * math.exp(-(t - LABEL) * 7) if t >= LABEL else 0)
    elif t < L['3b']:                       # "שנייה, מותק." — the slow stamp: he leans in, eyes on it
        u = t - L[90]
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', look=(-30, -10), ear_dy=-20, blush=0.6)
        rot = -3 * u; dy = -6 * u
    elif t < L[25]:                         # "יש!!!" — joy
        u = t - L[103]
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28 * math.exp(-u * 2), blush=1.0, look=(-8, 0))
        dy = -26 * abs(math.sin(u * 9)) * math.exp(-u * 1.0)
    elif t < BREAK:                         # THE PEAK: leaning back, eyes closed
        if t < EYES: st.update(lid=0.3, mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-14, blush=1.0, look=(-6, -10)); rot = -3
        else: st.update(eye_mode='closed', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-28, blush=1.0, look=(0, -8)); dy = -14; rot = -7
    else:                                   # the push — frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-24 * math.exp(-u * 4), look=(-30, 14),
                  twitch=(u >= 0.5 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.4), blush=0.0)
        dy = -8 - 14 * math.exp(-u * 8)
    return st, rot, dy

def sh_state(t):
    s_t = story_t(t)
    st = SH.base(); st.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.5, red=0.8, blush=0.6, look=(18, 6))
    talk = voice_v(t, 'sh') > 0.12
    st['mouth'] = 'talk' if talk else ('munch' if (int(t * 7)) % 2 and s_t < L[1] else 'grin')
    if s_t < L[1]: st.update(snack=True, lid=0.6)
    elif s_t < L[2]: st.update(look=(24, 20), lid=0.45, hand_r=(560, 720))               # slides the form
    elif s_t < L[90]: st.update(look=(24, 22), lid=0.4)
    elif s_t < L['3b']: st.update(look=(10, -6), lid=0.7, blush=0.8)                     # chill, the stamp rising
    elif s_t < BREAK: st.update(look=(20, 6), lid=0.45, blush=1.0, mouth='grin' if not talk else 'talk')
    else: st.update(look=(20, 10), lid=0.6, blush=0.6, snack=True)
    return st

def stamp_pos(t):
    """Sharit's stamp: rises slowly through 9000, slams at STAMP, lifts"""
    s_t = story_t(t)
    rest, top, hit = (330, 1380), (360, 1080), (FORM_C[0] - 10, FORM_C[1] - 70)
    if s_t < L[90]: return None
    if s_t < STAMP - 0.08: return lerp2(rest, top, ease_io(clamp((s_t - L[90]) / (STAMP - 0.08 - L[90]))))
    if s_t < STAMP: return lerp2(top, hit, ease_in(clamp((s_t - (STAMP - 0.08)) / 0.08)))
    if s_t < STAMP + 0.35: return hit
    if s_t < STAMP + 0.8: return lerp2(hit, rest, ease_io(clamp((s_t - STAMP - 0.35) / 0.45)))
    return None

def scene_two(t, i):
    img = BG.copy()
    s_t = story_t(t)
    E3.led_text(img, str(board_num(t)), BOARD_C[0], BOARD_C[1] + 20, 110)
    cheer = GOLDT <= s_t < BREAK - 0.05
    for name, x, y, sc, ph in QUEUE_TWO:
        jump = (-20 * abs(math.sin(t * 9 + ph))) if cheer else 0
        mood = 1 if cheer else (0 if s_t >= BREAK + 0.2 else 2)
        E13.paste_sprite(img, name, mood, x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    dx = sh_dx(t)
    if dx > -880:
        Ls = SH.draw(sh_state(t), i)
        Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
        img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] + dx - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state(t)
    lean = -30 * ease_io(clamp((s_t - L[25]) / 0.6)) if L[25] <= s_t < BREAK else 0
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2 - lean * 0.3, HY2 + dy + lean, F2, rot)
    d = ImageDraw.Draw(img)
    # counter
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1720)], radius=S(16), fill=(150, 96, 58), outline=(80, 50, 28), width=iw(6))
    d.rectangle([S(-20), S(1580), S(1100), S(1606)], fill=(190, 130, 80))
    # the form (on the counter from FORMIN; in the cold open already stamped)
    if s_t >= FORMIN:
        u = s_t - FORMIN
        c = lerp2((150, 1500), FORM_C, ease_out(clamp(u / 0.3)))
        signed = clamp((s_t - SIGN[0]) / (SIGN[1] - SIGN[0]))
        paste_rot(img, FORM_SIGNED_ST if s_t >= STAMP else (FORM_SIGNED if signed >= 1 else form_layer(signed) if signed > 0 else FORM0), c, 3, 0.85, 80)
        if 0 <= s_t - STAMP < 0.3: burst(img, (FORM_C[0], FORM_C[1] - 20), s_t - STAMP, (255, 120, 120), 200, 12, 0.3)
    d = ImageDraw.Draw(img)
    # the bag
    labeled = s_t >= LABEL
    if s_t < L[27]:                                            # held up in his paw during the want
        bc = (640 + 10 * math.sin(t * 6), 1230 + 12 * math.sin(t * 9))
        capsule(d, (HX2 - 160, 1540), (bc[0] + 30, bc[1] + 90), 100, FUR, OUT, 4)
        paste_rot(img, BAG_L if labeled else BAG, bc, -8 + 6 * math.sin(t * 5), 0.9, 90)
        d = ImageDraw.Draw(img); E12.big_paw(d, (bc[0] + 30, bc[1] + 90), -10, 0.7)
    else:
        paste_rot(img, BAG_L if labeled else BAG, BAG_C, 6, 0.8, 80)
        d = ImageDraw.Draw(img)
        if SIGN[0] <= s_t < SIGN[1]:                           # signing: paw + pen over the form
            u = clamp((s_t - SIGN[0]) / (SIGN[1] - SIGN[0]))
            pp = (FORM_C[0] + 80 - 170 * u, FORM_C[1] + 40 - 16 * math.sin(u * 19))
            capsule(d, (HX2 - 160, 1540), pp, 100, FUR, OUT, 4)
            line(d, [(pp[0] - 10, pp[1] - 10), (pp[0] - 60, pp[1] - 70)], (30, 60, 160), 12)
            E12.big_paw(d, pp, -20, 0.7)
        elif LABEL - 0.15 <= s_t < LABEL + 0.25:              # the label slap
            u = s_t - LABEL
            pp = lerp2((BAG_C[0] + 60, BAG_C[1] - 160), BAG_C, ease_in(clamp((u + 0.15) / 0.15))) if u < 0 else BAG_C
            capsule(d, (HX2 - 160, 1540), pp, 100, FUR, OUT, 4); E12.big_paw(d, pp, 0, 0.75)
            if u >= 0: burst(img, BAG_C, u, (255, 255, 255), 120, 8, 0.25)
        elif s_t >= BREAK:                                     # the phone by his face
            u = s_t - BREAK
            pc = lerp2((760, 2100), (520, 1110), ease_out(clamp(u / 0.18)))
            capsule(d, (HX2 - 160, 1540), (pc[0] + 30, pc[1] + 170), 100, FUR, OUT, 4)
            paste_rot(img, PHONE, pc, 5 + 3 * math.sin(u * 30) * math.exp(-u * 5), 0.62)
            d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 30, pc[1] + 170), -10, 0.7)
        else:
            rp = (HX2 - 140, 1480 + 8 * math.sin(t * 2.0))
            capsule(d, (HX2 - 160, 1540), rp, 100, FUR, OUT, 4); E12.big_paw(d, rp, 10, 0.85)
    sp = stamp_pos(t)
    if sp is not None:
        paste_rot(img, STAMPL, sp, -6, 0.9, 90)
        d = ImageDraw.Draw(img)
        capsule(d, (60, 1300), (sp[0] - 40, sp[1] - 70), 70, SH.BLOUSE, SH.BLOUSE_O, 4)
        SH.hand(d, (sp[0] - 30, sp[1] - 90))
    if cheer: E18.confetti(img, s_t - GOLDT + 0.3)
    burst(img, FORM_C, s_t - CHK1, (120, 255, 160), 160, 10, 0.4)
    burst(img, BAG_C, s_t - CHK2, (120, 255, 160), 140, 10, 0.4)
    if s_t >= BREAK: burst(img, (520, 1110), s_t - BREAK, (255, 120, 120), 220, 12, 0.4)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('טופס', 820, CHK1), ('מדבקה', 540, CHK2), ('הוחזר', 260, CHK3)]
def chips(frame, t, y=330):
    if t < T0 + 0.2 or t >= BREAK + 0.6: return
    gold = t >= GOLDT
    drained = t >= BREAK
    d = ImageDraw.Draw(frame)
    for lab, cx, tk in CHIPS:
        ok = t >= tk and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if drained: sc = 1.0 + 0.15 * math.exp(-(t - BREAK) * 10)
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
    f = font(size, 900); lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

BG = BAG = BAG_L = FORM0 = FORM_SIGNED = FORM_SIGNED_ST = PHONE = STAMPL = PILL_EP = PILL_Q = None
def init_all():
    global BG, BAG, BAG_L, FORM0, FORM_SIGNED, FORM_SIGNED_ST, PHONE, STAMPL, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    E13.build_crowd()
    BG = build_post_bg()
    BAG = bag_layer(); BAG_L = bag_layer(True)
    FORM0 = form_layer(0); FORM_SIGNED = form_layer(1.0); FORM_SIGNED_ST = form_layer(1.0, True)
    PHONE = phone_layer(); STAMPL = stamp_layer()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'two':
        z, cx, cy = 1.05 + 0.01 * pu, 540, 1000
        if a == 0.0:                                   # cold open: tight on his face + the stamp slam
            z, cx, cy = 1.38 + 0.03 * t, 680, 1100
            if t < 0.3: z = 1.55 - 0.17 * ease_out(t / 0.3)
        elif t < FF[0]: z, cx, cy = 1.22, 720, 1000   # the want: close on him and the tiny bag
        elif t < ARRIVE: z, cx, cy = 1.0, 540, 960     # x64 wide: the board races
        elif L[27] <= t < L[27] + 0.8: z, cx, cy = 1.12, 520, 980
        elif L[1] <= t < L[2]: z, cx, cy = 1.15, 400, 1060
        elif L[90] <= t < STAMP: z, cx, cy = 1.10 + 0.08 * clamp((t - L[90]) / (STAMP - L[90])), 520, 1100
        if HOLD[0] <= t < BREAK:
            k = ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0]))); z, cx, cy = 1.05 + 0.15 * k, lerp(540, 700, k), lerp(1000, 1060, k)
        if t >= BREAK: z, cx, cy = 1.18, 640, 1060
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1000
    elif name == 'frozen':
        z, cx, cy = 1.32 + 0.03 * pu, 720, 1040
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_two(lerp(L['3b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    else: img = scene_two(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (LABEL, STAMP, BREAK):
        if 0 <= t - s_ < 0.3: shake = 14 * math.exp(-(t - s_) * 8)
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
    if FF[0] <= t < FF[1]: ff_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK):
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
            col = {'sh': SHARIT_SUB, 'ivr': IVRSUB}.get(SPEAKER[li], WHITE)
            m.paste_center(frame, sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < FF[0]) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + post-office room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(38)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'ivr': y = m.phone_line(y) * 1.6
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
    def slap(t0, g=0.5): add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), t0, g)
    def cheer(t0, ln=1.0, g=0.10):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    def ding(t0, g=0.16):
        add(sfx, m.tone(1046.5, 0.6, harm=((1, 1), (2.76, 0.2)), decay=5), t0, g); add(sfx, m.tone(784.0, 0.8, harm=((1, 1), (2.76, 0.2)), decay=4), t0 + 0.16, g)
    def buzz(t0):
        for k in range(2):
            tt = tt_(0.12); add(sfx, m.lowpass(np.sign(np.sin(2 * np.pi * 150 * tt)), 400) * np.sin(np.pi * tt / 0.12), t0 + k * 0.15, 0.22)
    # cold open: the stamp on its in-context time
    st0 = STAMP - L['3b']; slap(st0, 0.6); add(sfx, thud(0.9), st0)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(HOLD[0]), 150, 900) * 0.6, 0.0, 0.012)                       # post-office room tone
    add(sfx, m.bandpass(nz(DUR - BREAK + 0.3), 150, 900) * 0.6, BREAK, 0.012)
    # x64: fast blips + the board
    add(sfx, m.bandpass(nz(0.4), 600, 5000) * np.linspace(0, 1, int(0.4 * SR)), FF[0] - 0.3, 0.06)
    tc = FF[0]
    while tc < FF[1]:
        add(sfx, m.tone(1200 + 200 * math.sin(tc * 9), 0.03, harm=((1, 1),), decay=40), tc, 0.025); tc += 0.07
    ding(DING); whoosh(ARRIVE, 0.08, 0.3)
    add(sfx, m.bandpass(nz(0.3), 300, 3000) * np.sin(np.pi * tt_(0.3) / 0.3), FORMIN, 0.08)     # the form slides
    for k in range(int((SIGN[1] - SIGN[0]) / 0.09)):                                          # pen scratch
        add(sfx, m.bandpass(nz(0.05), 2500, 7000) * np.exp(-tt_(0.05) * 30), SIGN[0] + k * 0.09, 0.05)
    check(CHK1, 0.15)
    slap(LABEL, 0.5); add(sfx, thud(0.4), LABEL); check(CHK2, 0.15)
    add(sfx, m.bandpass(nz(STAMP - RAISE), 200, 900) * np.linspace(0, 1, int((STAMP - RAISE) * SR)) ** 2, RAISE, 0.05)  # tension rises with the stamp
    slap(STAMP, 0.6); add(sfx, thud(1.0), STAMP); check(CHK3, 0.2, True); cheer(GOLDT + 0.1, L[25] + 0.6 - GOLDT, 0.09)
    heartbeat(HOLD[0] + 0.04); heartbeat(HOLD[0] + 0.30, 0.5)
    buzz(BREAK); ding(BREAK + 0.02, 0.2); add(sfx, thud(0.7), BREAK)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), BREAK + 0.25, 0.18)
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
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', T0, 'FF', [round(x, 2) for x in FF])
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'SIGN', [round(x, 2) for x in SIGN], 'STAMP', round(STAMP, 2),
              'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep38_contact.png')); print('ok'); return
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
