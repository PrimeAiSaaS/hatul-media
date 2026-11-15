#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 35: חצות של בלאק פריידיי (season 8 "בלאק פריידיי" ep2, VOICED, built 15.11 under §P, ~23 s).
Voices = voice bank 2026-11-13 lines 3500–3505 (Benji = cat, Vera = grandma) + stock 9104 "רגע... מה?!" (the break
reaction), prepared by voice/ep35_prep.py. No Sharit in this one (bible).
Set: the kiosk at night (ep21/ep23 world) — an everyday place — with the red LED wall clock that counts REAL seconds to
00:00 through the whole episode (experiment realtime_countdown, replay of the ep23 keep).
Want: pay for the Black Friday snack box ($74.99, ep34's cart) before the sale ends at 00:00.
Plant: the red LED clock + the grey bank-app line "אימות עסקה חריגה: עד 60 שנ׳" (in the cold open on the phone, in the
want close-up under the button, and again in the split screen). Never pointed at.
Climb (meter = 3 chips + 4 code boxes): card ✓ → SMS "עסקה חריגה" → "סבתא, מהר! הקוד!" → grandma in Eilat reads the code
4… 8… 2… 1 (callback ep23), he types each ✓ → "אושר! אושר!" gold.
Peak: "סוף סוף... בזמן." — paw over "לתשלום", eyes closed, the clock 23:59:58 → 59, hush + heartbeat.
Break (one_second_late): tap → the clock flips 00:00:00, the site flips "המבצע הסתיים · $89", chips drain, "רגע... מה?!",
frozen face, whip into the cold open (loop).
No music (voiced rule): voices + SFX + kiosk room tone. Serial pills "פרק 35" + live ticket number (hud.stage_of, §O4).

  python3 voice/ep35_prep.py
  python3 ep35.py times | test t1 t2 ... | render   -> out/ep35_hatzot.mp4
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
import ep13 as E13
import ep18 as E18
import ep21_v1 as E21
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep35', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 104, 226)
ORANGE = (255, 120, 30); BF = (18, 18, 22); GRAN_SUB = (255, 196, 232)
QUEUE = int(os.environ.get('QUEUE', '448'))
EP_LABEL = 'פרק 35'
OUTNAME = os.environ.get('OUTNAME', 'ep35_hatzot')
LIMIT = float(os.environ.get('LIMIT', '0'))
CODE = '4821'
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
COLD_END = round(D[0] + 0.12, 2)            # cold open = 3500 "סבתא, מהר! הקוד!" (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "שבעים וארבע תשעים ותשע. עד חצות. משלם."
CARD = L[1] + ss(1, 2) + 0.15               # card ✓ on "משלם."
SMS = L[1] + D[1] + 0.12                    # the bank screen slams in: "אימות עסקה חריגה"
L[2] = SMS + 0.35                           # "עסקה חריגה?! זה מארז חטיפים!"
L['0b'] = L[2] + D[2] + 0.08                # the cold-open line again, in context
RING = (L['0b'] + D[0] + 0.02, L['0b'] + D[0] + 0.40)
L[3] = RING[1]                              # grandma: "חמוד! ארבע... שמונה... שתיים... אחת."
DIG = [L[3] + ss(3, k + 1) + 0.22 for k in range(4)]
L[4] = L[3] + D[3] + 0.10                   # "אושר! אושר!"
GOLDT = L[4] + 0.05
L[5] = L[4] + D[4] + 0.20                   # "סוף סוף... בזמן." (peak line)
HOLD = (L[5] + D[5] + 0.03, L[5] + D[5] + 0.58)
TAP = HOLD[1]                               # the paw comes down on "לתשלום"
BREAK = TAP + 0.15                          # 00:00:00 — the site flips
DRAIN = BREAK + 0.45
L[104] = BREAK + 0.55                       # "רגע... מה?!"
FREEZE = L[104] + D[104]
DUR = round(FREEZE + 0.45, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (0, L['0b']), (3, L[3]), (4, L[4]), (5, L[5]), (104, L[104])]
SPEAKER = {0: 'cat', 1: 'cat', 2: 'cat', 3: 'grandma', 4: 'cat', 5: 'cat', 104: 'cat'}
MIDNIGHT = 24 * 3600

SUBS = {
    0: [['סבתא, מהר!'], ['הקוד!']],
    1: [['שבעים וארבע תשעים ותשע.'], ['עד חצות.'], ['משלם.']],
    2: [['עסקה חריגה?!'], ['זה מארז חטיפים!']],
    3: [['חמוד!'], ['ארבע...'], ['שמונה...'], ['שתיים...'], ['אחת.']],
    4: [['אושר! אושר!']],
    5: [['סוף סוף...'], ['בזמן.']],
    104: [['רגע... מה?!']],
}
SPLIT = {0: [0, 1], 1: [0, 1, 2], 2: [0, 1], 3: [0, 1, 2, 3, 4], 4: [0], 5: [0, 1], 104: [0]}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]; ks = SPLIT.get(li, [0])
    starts = [0.0] + [ss(li, ks[k]) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 104 and k == len(ch) - 1: b = DUR - 0.25
        if li == 3 and k == len(ch) - 1: b = min(b, L[4] - 0.03)
        SUB_TIMES.append((a, b, c, li))

C = lambda t: t - 0.08
SHOTS = [('close', 0.0, COLD_END), ('rewind', COLD_END, T0), ('close', T0, RING[0]), ('split', RING[0], C(L[4])),
         ('close', C(L[4]), FREEZE - 0.02), ('frozen', FREEZE - 0.02, DUR + 1)]
HOOK = ['קוד מהבנק', 'דקה לפני חצות?']        # keyword: קוד / הבנק / חצות (F16 pain question)
TOPCAPS = [(0.0, COLD_END, HOOK), (T0, CARD - 0.1, HOOK)]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def story_t(t):
    """the cold open is the in-context replay of 3500: map its time onto the story clock"""
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

# ------------------------------------------------------------------ the clock (real seconds to midnight)
def clock_secs(t):
    st = story_t(t)
    return MIDNIGHT + math.floor(st - BREAK)
def clock_text(t):
    s = clock_secs(t) % 86400
    return f'{s // 3600:02d}:{(s // 60) % 60:02d}:{s % 60:02d}'

def led_clock(img, c, t, s=1.0, scramble=False):
    d = ImageDraw.Draw(img)
    w_, h_ = 380 * s, 116 * s
    d.rounded_rectangle([S(c[0] - w_ / 2), S(c[1] - h_ / 2), S(c[0] + w_ / 2), S(c[1] + h_ / 2)], radius=S(14 * s),
                        fill=(26, 10, 12), outline=(70, 70, 76), width=iw(6))
    txt = clock_text(t)
    if scramble:
        r = random.Random(int(t * 60)); txt = f'23:{r.randint(10, 59):02d}:{r.randint(0, 59):02d}'
    secs = clock_secs(t) % 86400
    hot = secs >= 23 * 3600 + 59 * 60 + 50 or secs < 60
    col = (255, 60, 50) if not hot or int(t * 4) % 2 == 0 else (255, 160, 130)
    if secs < 60 and not scramble: col = (255, 60, 50)
    d.text((S(c[0]), S(c[1] + 4 * s)), txt, font=font(S(78 * s), 900), fill=col, anchor='mm')

# ------------------------------------------------------------------ the phone (store → bank → store → ended)
def n_digits(t):
    st = story_t(t)
    return sum(1 for d_ in DIG if st >= d_)

def phone_state(t):
    st = story_t(t)
    if st >= BREAK: return 'ended'
    if st >= GOLDT: return 'approved'
    if st >= SMS: return 'verify'
    return 'cart'

PW, PH = 400, 720
def phone_layer(state, nd, card):
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    if state == 'verify':
        pd.rectangle([S(14), S(66), S(PW - 14), S(146)], fill=BLUE)
        pd.text((S(PW / 2), S(106)), 'הבנק שלי', font=font(S(42), 900), fill=WHITE, anchor='mm')
        pd.rounded_rectangle([S(34), S(170), S(PW - 34), S(250)], radius=S(16), fill=(255, 236, 236), outline=RED, width=iw(4))
        pd.text((S(PW / 2), S(210)), 'עסקה חריגה!', font=font(S(44), 900), fill=RED, anchor='mm')
        pd.text((S(PW / 2), S(286)), 'קוד נשלח למספר הרשום', font=font(S(26), 800), fill=(90, 96, 110), anchor='mm')
        for k in range(4):
            x0 = 64 + k * 72; done = k < nd
            pd.rounded_rectangle([S(x0), S(320), S(x0 + 60), S(400)], radius=S(12), fill=(226, 246, 232) if done else WHITE,
                                 outline=GREEN if done else (170, 176, 190), width=iw(4))
            if done: pd.text((S(x0 + 30), S(362)), CODE[k], font=font(S(50), 900), fill=INK, anchor='mm')
        pd.rounded_rectangle([S(40), S(440), S(PW - 40), S(520)], radius=S(40), fill=(170, 186, 214))
        pd.text((S(PW / 2), S(480)), 'אישור', font=font(S(42), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(580)), 'אימות עסקה חריגה: עד 60 שנ׳', font=font(S(25), 800), fill=(140, 144, 156), anchor='mm')   # the plant
        return lay
    pd.rectangle([S(14), S(66), S(PW - 14), S(132)], fill=BF)
    pd.text((S(PW / 2), S(99)), 'בלאק פריידיי', font=font(S(40), 900), fill=ORANGE, anchor='mm')
    if state == 'ended':
        pd.rectangle([S(14), S(132), S(PW - 14), S(PH - 60)], fill=(34, 34, 40))
        pd.text((S(PW / 2), S(230)), 'המבצע', font=font(S(62), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(300)), 'הסתיים', font=font(S(62), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(400)), '$74.99', font=font(S(40), 800), fill=(150, 150, 160), anchor='mm')
        line(pd, [(PW / 2 - 80, 400), (PW / 2 + 80, 400)], (150, 150, 160), 4)
        pd.text((S(PW / 2), S(490)), '$89.00', font=font(S(92), 900), fill=(255, 80, 80), anchor='mm')
        pd.text((S(PW / 2), S(590)), '00:00', font=font(S(36), 900), fill=(160, 160, 170), anchor='mm')
        return lay
    # the box (ep34's cart, 11 bags)
    cols = [(244, 160, 36), (226, 60, 60), (60, 150, 220), (90, 190, 90), (240, 210, 60), (170, 90, 200)]
    pd.rounded_rectangle([S(40), S(150), S(PW - 40), S(290)], radius=S(18), fill=(255, 240, 220), outline=(200, 160, 120), width=iw(3))
    for k in range(11):
        x = 70 + (k % 6) * 46; y = 186 + (k // 6) * 56
        pts = [(x - 18, y - 24), (x + 18, y - 24), (x + 16, y + 24), (x - 16, y + 24)]
        poly(pd, pts, fill=cols[k % 6], outline=tuple(max(0, c - 90) for c in cols[k % 6]), width=2)
    pd.text((S(PW / 2), S(330)), '$74.99', font=font(S(80), 900), fill=GREEN, anchor='mm')
    if state == 'approved':
        pd.rounded_rectangle([S(54), S(380), S(PW - 54), S(432)], radius=S(26), fill=GOLD, outline=(120, 80, 0), width=iw(3))
        pd.text((S(PW / 2), S(406)), 'העסקה אושרה', font=font(S(32), 900), fill=INK, anchor='mm')
    else:
        pd.rounded_rectangle([S(54), S(380), S(PW - 54), S(432)], radius=S(26), fill=RED)
        pd.text((S(PW / 2), S(406)), 'המבצע נגמר ב-00:00', font=font(S(30), 900), fill=WHITE, anchor='mm')
    # card row
    pd.rounded_rectangle([S(54), S(452), S(PW - 54), S(500)], radius=S(12), fill=WHITE, outline=GREEN if card else (190, 194, 206), width=iw(3))
    pd.text((S(PW - 76), S(476)), '•••• 4821' if False else '•••• 7316', font=font(S(28), 800), fill=INK, anchor='rm')
    if card:
        E(pd, 92, 476, 16, 16, fill=GREEN); line(pd, [(84, 476), (90, 483), (101, 469)], WHITE, 5)
    pd.rounded_rectangle([S(50), S(526), S(PW - 50), S(600)], radius=S(37), fill=BLUE, outline=(20, 40, 90), width=iw(4))
    pd.text((S(PW / 2), S(563)), 'לתשלום', font=font(S(40), 900), fill=WHITE, anchor='mm')
    if state == 'cart':
        pd.text((S(PW / 2), S(640)), '* אימות עסקה חריגה: עד 60 שנ׳', font=font(S(22), 800), fill=(150, 152, 162), anchor='mm')   # the plant
    return lay

_PHC = {}
def phone_at(t):
    key = (phone_state(t), n_digits(t), story_t(t) >= CARD)
    if key not in _PHC:
        if len(_PHC) > 32: _PHC.clear()
        _PHC[key] = phone_layer(*key)
    return _PHC[key]

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    E21.shadow_paste(img, lay, c, 100, (16, 20), 12)

burst = E18.burst

# ------------------------------------------------------------------ the cat close-up (kiosk at night, the clock over his shoulder)
HXP, HYP, FP = (780, 940, 2.0) if BIGF else (760, 960, 1.78)
CLOCK_C, CLOCK_S = (300, 515), 1.05
QUEUE_BEHIND = [('c0', 110, 900, 0.48, 0.0), ('h1', 1010, 660, 0.40, 1.1), ('c3', 1015, 1170, 0.52, 2.0)]

def base_cat():
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.3); return st

def cat_close_state(t):
    st = base_cat(); rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    if t < COLD_END:                 # cold open: "סבתא, מהר! הקוד!" — shouting into the phone, sweat, tiny pupils
        st.update(lid=0.0, pupil='tiny' if t < 0.6 else 'big', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0,
                  ear_dy=-26, look=(-22, 6), blush=0.0)
        rot = 7 * math.sin(t * 13) * math.exp(-t * 1.2); dy = -18 * v
    elif t < SMS:                    # the want: dreamy-determined, "עד חצות." glance at the clock
        glance = L[1] + ss(1, 1) - 0.05 <= t < L[1] + ss(1, 2)
        st.update(lid=0.15, pupil='big', brow='none' if not glance else 'up', mouth=cat_mouth(t, rest='smile', loud='w'),
                  ear_dy=-14, look=(-24, 8) if not glance else (-30, -18), blush=0.6)
        if t >= CARD: st.update(lid=0.0, blush=0.9, mouth='smile'); dy = -14 * math.exp(-(t - CARD) * 5)
        rot = 3 * math.sin(t * 4); dy += -8 * v
    elif t < L['0b']:                # "עסקה חריגה?! זה מארז חטיפים!" — outrage
        u = t - SMS
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0,
                  ear_dy=-26 * math.exp(-u * 3), look=(-20, 8))
        if t >= L[2] + ss(2, 1) - 0.05: st.update(brow='annoyed', pupil='big', look=(0, -4))
        rot = 6 * math.sin(u * 30) * math.exp(-u * 4) + 2 * math.sin(t * 9) * (v > 0.1); dy = -16 * v
    elif t < RING[0] + 0.5:          # "סבתא, מהר! הקוד!" in context
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0, ear_dy=-26, look=(-22, 6))
        rot = 5 * math.sin(t * 13); dy = -18 * v
    elif t < GOLDT + 0.05:
        st.update(lid=0.1, pupil='big', brow='up', mouth='w', ear_dy=-14, look=(-22, 10))
    elif t < L[5]:                   # "אושר! אושר!" — beaming, bouncing
        u = t - GOLDT
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28 * math.exp(-u * 2), blush=1.0, look=(-6, -6))
        dy = -26 * abs(math.sin(u * 9)) * math.exp(-u * 1.0); rot = 6 * math.sin(u * 11) * math.exp(-u * 1.2)
    elif t < HOLD[0]:                # "סוף סוף... בזמן." — paw rising over the button
        st.update(lid=0.25, pupil='normal', brow='none', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-10, blush=0.9, look=(-22, 10))
        rot = -3 + 2 * math.sin(t * 3)
    elif t < BREAK:                  # THE PEAK: eyes closed, paw hovering, hush
        st.update(eye_mode='closed', mouth='smile', ear_dy=-24, blush=1.0, look=(0, -6)); rot = -6; dy = -8
    else:                            # 00:00:00 — eyes snap open, frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat' if speaking(t) is None else cat_mouth(t, rest='flat', loud='w'),
                  ear_dy=-20 * math.exp(-u * 4), look=(-30, -14) if u < 0.5 else (-24, 10),
                  twitch=(0.5 < u < 1.4 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.4), ear_droop=0.6 * clamp(u / 0.3))
        dy = -6
    return st, rot, dy

def scene_close(t, i, scramble=False):
    img = KIOSK.copy()
    led_clock(img, CLOCK_C, t, CLOCK_S, scramble)
    cheer = GOLDT <= t < L[5]
    for name, x, y, sc, ph in QUEUE_BEHIND:
        jump = (-24 * abs(math.sin(t * 9 + ph))) if cheer else 0
        mood = 1 if (cheer or t >= BREAK) else (2 if t < COLD_END or SMS <= t < L['0b'] else 0)
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_close_state(t)
    E(d, HXP, 1700, 430, 450, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1760, 200, 300, fill=CREAM)
    pc = (270, 1110 + 5 * math.sin(t * 8)); sc = 0.98
    if t < COLD_END: pc = (270 + 6 * math.sin(t * 40) * math.exp(-t * 3), 1110)
    if SMS <= t < SMS + 0.4: sc += 0.18 * math.exp(-(t - SMS) * 9)
    if t >= BREAK: sc = 1.06 + 0.12 * math.exp(-(t - BREAK) * 9); pc = (270 + 6 * math.sin(t * 50) * math.exp(-(t - BREAK) * 6), 1110)
    grip = (pc[0] - 190, pc[1] + 150)
    capsule(d, (HXP - 240, 1520), grip, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP, HYP + dy, FP, rot)
    paste_rot(img, phone_at(t), pc, -6, sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, grip, 70, 0.9)
    # the other paw: card tap / hovering over "לתשלום" (peak) / down on it (tap)
    btn = (pc[0] + 10, pc[1] + (563 - PH / 2) * sc)
    rp = None
    if CARD - 0.3 <= t < CARD + 0.25:
        rp = lerp2((btn[0] + 160, btn[1] - 40), (btn[0] + 40, btn[1] - 110), math.sin(math.pi * clamp((t - CARD + 0.3) / 0.55)))
    elif L[5] <= t < TAP:
        hov = 190 - 70 * ease_io(clamp((t - L[5]) / (HOLD[0] - L[5])))
        rp = (btn[0] + 30, btn[1] - hov + 3 * math.sin(t * 40) * (t >= HOLD[0]))
    elif TAP <= t < BREAK + 0.6:
        rp = (btn[0] + 30, lerp(btn[1] - 120, btn[1] - 20, ease_in(clamp((t - TAP) / 0.1))))
    if rp is not None:
        capsule(d, (HXP + 170, 1520), (rp[0] + 60, rp[1] + 60), 100, FUR, OUT, 4)
        E12.big_paw(d, rp, -20, 0.8)
    if t < 0.4: burst(img, (300, 1000), t, (255, 120, 120), 200, 12, 0.4)
    if CARD <= t < CARD + 0.5: burst(img, btn, t - CARD, (120, 255, 160), 160, 10, 0.4)
    if SMS <= t < SMS + 0.45: burst(img, (300, 1000), t - SMS, (255, 120, 120), 220, 12, 0.45)
    if GOLDT <= t < L[5]: E18.confetti(img, t - GOLDT + 0.3)
    if t >= BREAK: burst(img, (300, 1000), t - BREAK, (255, 120, 120), 240, 12, 0.4)
    if t >= BREAK:      # the wall clock itself pops on 00:00:00
        burst(img, CLOCK_C, t - BREAK, (255, 90, 90), 170, 12, 0.4)
    return img

# ------------------------------------------------------------------ grandma (top half of the split, ep23's Eilat living room)
def gran_state(t):
    st = E10.gran_base()
    st.update(hand_r=(520, 470), hand_l=(170, 760))
    g = voice_v(t, 'grandma')
    if t < L[3]:
        st.update(lid=0.5, mouth='lazy', look=(-10, 10), blush=0.5)
    elif t < L[3] + ss(3, 1) - 0.1:                      # "חמוד!"
        u = t - L[3]
        st.update(lid=0.1, mouth='grin' if g < 0.15 else 'talk', look=(8, 0), blush=0.9, rot=-6 * math.exp(-u * 4))
    else:                                                 # reading slowly, squinting at her phone
        st.update(lid=0.62, mouth='talk' if g > 0.12 else 'lazy', look=(16, 4), rot=3 * math.sin(t * 2.5), blush=0.5)
    return st

def gran_phone():
    pw, ph = 300, 520
    lay = Image.new('RGBA', (S(pw), S(ph)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(pw) - 1, S(ph) - 1], radius=S(44), fill=(20, 20, 24))
    pd.rounded_rectangle([S(12), S(12), S(pw - 12), S(ph - 12)], radius=S(36), fill=(92, 52, 86))
    pd.text((S(pw / 2), S(80)), 'סבתא', font=font(S(30), 800), fill=(236, 220, 236), anchor='mm')
    pd.rounded_rectangle([S(20), S(140), S(pw - 20), S(280)], radius=S(18), fill=(246, 246, 250))
    pd.text((S(pw - 34), S(176)), 'הבנק שלי', font=font(S(26), 800), fill=(90, 90, 100), anchor='rm')
    pd.text((S(pw / 2), S(232)), CODE, font=font(S(60), 900), fill=(200, 40, 60), anchor='mm')
    return lay

G_GF = 2.0
G_ORIGIN = (560 - 350 * G_GF, 830 - 300 * G_GF)
def scene_gran(t, i):
    img = GRAN_BG.copy()
    lay = E10.gran_draw(gran_state(t), i)
    lay = lay.resize((int(lay.width * G_GF), int(lay.height * G_GF)), Image.BICUBIC)
    shake = 8 * math.sin(t * 90) if RING[0] <= t < RING[1] else 0
    img.alpha_composite(lay, dest=(int(S(G_ORIGIN[0])), int(S(G_ORIGIN[1]))))
    hand = (G_ORIGIN[0] + 520 * G_GF + shake, G_ORIGIN[1] + 470 * G_GF)
    ph = GRAN_PHONE.rotate(-10 + 2 * math.sin(t * 3), resample=Image.BICUBIC, expand=True)
    m.paste_center(img, ph, S(hand[0] - 10), S(hand[1] - 210))
    d = ImageDraw.Draw(img)
    E(d, hand[0], hand[1] - 20, 64, 52, fill=SH.SKIN, outline=SH.SKIN_O, width=5)
    if RING[0] <= t < RING[1] + 0.1:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        k = int((t - RING[0]) * 14) % 2; cc = (hand[0] - 10, hand[1] - 210)
        for r in (180, 230):
            od.arc([S(cc[0] - r), S(cc[1] - r), S(cc[0] + r), S(cc[1] + r)], -40, 40, fill=(255, 236, 120, 230 if k else 120), width=iw(10))
        img.alpha_composite(ov)
    burst(img, (hand[0] - 10, hand[1] - 210), t - L[3], (255, 236, 120), 160, 10, 0.35)
    return img

def scene_split_cat(t, i):
    img = KIOSK.copy()
    led_clock(img, (265, 505), t, 1.1)
    d = ImageDraw.Draw(img)
    st = base_cat(); rot, dy = 0.0, 0.0
    k = n_digits(t)
    last = max([dg for dg in DIG if t >= dg], default=None)
    st.update(lid=0.2, pupil='big', brow='annoyed', mouth='flat', look=(-22, 10), ear_dy=-10, sweat=0.6)
    if t < L[3] + 0.6: st.update(lid=0.0, brow='up', mouth='w', look=(-14, -6), ear_dy=-18)
    if last is not None and t - last < 0.35:
        u = t - last; st.update(mouth='smile', lid=0.0, pupil='big', brow='up'); dy = -12 * math.exp(-u * 8)
    elif k < 4 and (int(t * 2) % 2 == 0) and t > L[3] + 1.0:
        st.update(look=(-34, -20))                        # glances at the clock between the digits
    hx, hy = 745, 930
    E(d, hx, 1640, 450, 470, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1700, 210, 320, fill=CREAM)
    c = (300, 1110)
    lay = phone_at(t)
    capsule(d, (hx - 260, 1420), (c[0] + 10, c[1] + PH * 0.43), 120, FUR, OUT, 4)
    paste_rot(img, lay, c, -6, 1.0)
    d = ImageDraw.Draw(img); E12.big_paw(d, (c[0] + 20, c[1] + PH * 0.47), 8)
    rp = (c[0] + 170, c[1] - 60)
    for dt in DIG:
        u = t - dt + 0.12
        if 0 <= u < 0.24: rp = lerp2((c[0] + 170, c[1] - 60), (c[0] + 40, c[1] - 10), math.sin(math.pi * u / 0.24))
    capsule(d, (hx + 250, 1420), rp, 120, FUR, OUT, 4)
    E12.big_paw(d, rp, -30)
    E12.paste_head(img, st, i, hx, hy + dy, 1.8, rot)
    for dt in DIG: burst(img, (c[0], c[1] - 10), t - dt, (120, 255, 160), 110, 8, 0.3)
    return img

def split_frame(t, i):
    g = scene_gran(t, i)
    c = scene_split_cat(t, i)
    top = g.crop((0, S(830 - 560), W * K, S(830 + 400))).resize((W, 960), Image.LANCZOS)
    bot = c.crop((0, S(860 - 520), W * K, S(860 + 440))).resize((W, 960), Image.LANCZOS)
    fr = Image.new('RGBA', (W, H)); fr.paste(top, (0, 0)); fr.paste(bot, (0, 960))
    ImageDraw.Draw(fr).rectangle([0, 954, W, 966], fill=(20, 20, 26))
    return fr

# ------------------------------------------------------------------ overlays
CHIPS = [('כרטיס', 820, CARD), ('קוד', 540, DIG[3]), ('אושר', 260, GOLDT)]
def chips(frame, t, y=330):
    if t < CARD - 0.1 or t < COLD_END: return
    gold = t >= GOLDT
    drained = t >= DRAIN
    if t >= DRAIN + 0.7: return
    d = ImageDraw.Draw(frame)
    for k_, (lab, cx, tk) in enumerate(CHIPS):
        ok = t >= tk and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if drained: sc = 1.0 + 0.15 * math.exp(-(t - DRAIN) * 10)
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

def code_meter(frame, t, y=960):
    """4 code boxes on the split seam: grandma's digits as he types them"""
    d = ImageDraw.Draw(frame)
    nd = n_digits(t); full = nd == 4
    bw, gap = 130, 22
    x0 = W / 2 - (4 * bw + 3 * gap) / 2
    for k in range(4):
        done = k < nd; u = t - DIG[k]
        sc = 1.0 + (0.35 * math.exp(-u * 10) * math.cos(u * 20) if 0 <= u < 0.5 else 0.0)
        cx = x0 + k * (bw + gap) + bw / 2
        w_, h_ = bw * sc, 130 * sc
        fill = (GOLD if full else GREEN) if done else (250, 250, 250)
        d.rounded_rectangle([cx - w_ / 2 + 5, y - h_ / 2 + 8, cx + w_ / 2 + 5, y + h_ / 2 + 8], radius=18, fill=(0, 0, 0, 90))
        d.rounded_rectangle([cx - w_ / 2, y - h_ / 2, cx + w_ / 2, y + h_ / 2], radius=18, fill=fill, outline=INK, width=5)
        if done: d.text((cx, y + 3), CODE[k], font=font(int(90 * sc), 900), fill=WHITE, anchor='mm', stroke_width=4, stroke_fill=INK)
        else: d.text((cx, y + 3), '_', font=font(int(70 * sc), 900), fill=(190, 194, 204), anchor='mm')

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
KIOSK = GRAN_BG = GRAN_PHONE = PILL_EP = PILL_Q = None
def init_all():
    global KIOSK, GRAN_BG, GRAN_PHONE, PILL_EP, PILL_Q
    m.init_static()
    kraw = E21.build_kiosk_bg()
    kb = kraw.filter(ImageFilter.GaussianBlur(S(2)))
    kb.alpha_composite(Image.new('RGBA', kb.size, (30, 30, 70, 40)))       # 23:59 — the kiosk at night, still bright enough (R6)
    KIOSK = kb
    E12.SHARP = True
    GRAN_BG = E12.build_gran_bg()
    GRAN_BG.alpha_composite(Image.new('RGBA', GRAN_BG.size, (20, 24, 60, 50)))
    GRAN_PHONE = gran_phone()
    E13.build_crowd()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'close':
        z = 1.04 + 0.02 * pu; cy = 980; cx = 540
        if a == 0.0:
            z = 1.10 + 0.04 * t; cx, cy = 470, 880
            if t < 0.3: z = 1.30 - 0.20 * ease_out(t / 0.3)
        if HOLD[0] <= t < BREAK:
            k = ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0]))); z += 0.08 * k
        if t >= BREAK: z, cx, cy = 1.14 + 0.03 * (t - BREAK), 420, 900          # onto the clock + the phone
        if t >= L[104]: z, cx, cy = lerp(1.14, 1.22, ease_out(clamp((t - L[104]) / 0.2))), lerp(420, 640, ease_out(clamp((t - L[104]) / 0.2))), 960
    elif name == 'rewind':
        z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'frozen':
        z, cx, cy = 1.30 + 0.03 * pu, 700, 940
    if name == 'close' and a > 0 and pu < 0.2:
        z = z + 0.07 * (1 - ease_out(pu / 0.2))
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'split':
        frame = split_frame(t, i)
        if t - a < 0.25:
            z = lerp(1.1, 1.0, ease_out((t - a) / 0.25)); cw, ch = W / z, H / z
            frame = frame.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.LANCZOS)
    else:
        if name == 'rewind':
            u = (t - a) / (b - a)
            img = scene_close(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i, scramble=True)
        else: img = scene_close(t, i)
        z, ccx, ccy = camera(t)
        shake = 0.0
        if t < 0.5: shake = 18 * math.exp(-t * 5)
        if 0 <= t - SMS < 0.3: shake = 12 * math.exp(-(t - SMS) * 8)
        if 0 <= t - BREAK < 0.35: shake = 16 * math.exp(-(t - BREAK) * 8)
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
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.28 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(60 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CARD, SMS, DIG[3], GOLDT, BREAK):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    if name == 'split': code_meter(frame, t, 960)
    else: chips(frame, t)
    for t0, t1, lines in TOPCAPS:
        if t0 <= t < t1: m.paste_center(frame, m.caption_layer(lines, 96, WHITE), W / 2, 270)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            gran = SPEAKER[li] == 'grandma'
            m.paste_center(frame, sub_layer(lines, GRAN_SUB if gran else WHITE), W / 2, 170 if (gran and name == 'split') else 1560)
    if t < COLD_END or (T0 <= t < CARD - 0.1) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + kiosk room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(35)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'grandma':            # through the phone
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
    def tap(t0, g=0.12): add(sfx, m.tone(2093.0, 0.08, harm=((1, 1),), decay=30), t0, g)
    def tick(t0, g=0.05): add(sfx, m.tone(1500, 0.03, harm=((1, 1),), decay=60), t0, g)
    def cheer(t0, ln=1.0, g=0.10):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    # the clock: a soft tick on every real second (louder in the last 10)
    for s in range(-40, 1):
        tc = BREAK + s
        if tc < 0: continue
        if tc < COLD_END: continue
        tick(tc, 0.035 if s < -10 else 0.07)
    for k in range(int(COLD_END)):              # the cold open ticks on its own clock
        tick((BREAK - L['0b']) % 1.0 + k, 0.05)
    add(sfx, thud(1.0), 0.0); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), 0.0, 0.4)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(HOLD[0]), 150, 900) * 0.6, 0.0, 0.012)                       # kiosk room tone
    add(sfx, m.bandpass(nz(DUR - BREAK + 0.3), 150, 900) * 0.6, BREAK, 0.012)
    for name, a, b in SHOTS[2:]:
        if name != 'frozen': whoosh(a)
    tap(CARD - 0.05, 0.14); check(CARD, 0.15)
    buzz(SMS, 0.15); buzz(SMS + 0.4, 0.12); add(sfx, thud(0.5), SMS)                     # the SMS vibration + "עסקה חריגה"
    tc = RING[0]
    while tc < RING[1]:                                                                  # grandma's phone rings
        add(sfx, m.tone(1318.5, 0.05, harm=((1, 1), (2, 0.2)), decay=30), tc, 0.06); tc += 0.06
    for dt in DIG: tap(dt - 0.02, 0.12); check(dt, 0.08)
    check(DIG[3] + 0.05, 0.12, True)
    check(GOLDT, 0.2, True); cheer(GOLDT + 0.1, L[5] - GOLDT, 0.10)
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.33, 0.5)
    tap(TAP, 0.18)
    add(sfx, thud(0.9), BREAK); add(sfx, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), BREAK, 0.5)
    for k, f in enumerate((440.0, 349.2, 261.6)): add(sfx, m.tone(f, 0.35, harm=((1, 1), (2, 0.4)), decay=5), BREAK + 0.05 + k * 0.12, 0.10)   # the "sale over" tri-tone down
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), DRAIN, 0.24)
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
        print('CARD', round(CARD, 2), 'SMS', round(SMS, 2), 'RING', [round(x, 2) for x in RING], 'DIG', [round(x, 2) for x in DIG],
              'GOLDT', round(GOLDT, 2), 'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK, 2), 'FREEZE', round(FREEZE, 2))
        print('clock at 0:', clock_text(0.0), 'at T0:', clock_text(T0), 'at HOLD:', clock_text(HOLD[0]), clock_text(TAP - 0.01), 'at BREAK:', clock_text(BREAK))
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep35_contact.png')); print('ok'); return
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
