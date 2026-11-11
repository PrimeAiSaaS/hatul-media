#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 33: ביטוח לאומי: הקצבה נכנסה (season 7 "הכסף בדרך" finale, VOICED, built 11.11 under §P, ~18 s;
the data agent's default voiced length of 10.11, "~21 s"). Voices = voice bank 3300–3305 (Benji = cat, Delia = Sharit)
+ 2703 "שרית?! גם פה?", prepared by voice/ep33_prep.py (3304 = Gabi's 9.11 pick, take C; 3306 not used: after the break
only the frozen face, §P).
Want: the November קצבה came in early (Thursday 26.11), so: every snack in the kiosk.
Plant: the SMS on his phone — big "הקצבה הופקדה ✓", and under it one small grey line "* הקדמת תשלום לפי בקשתך" (his own
paw-signed request from ep29). In the cold open, in the want close-up, and once more mid-climb as the grey fine print on the
app's payment screen ("* עמלת הקדמת תשלום תחויב בנפרד"). Never pointed at.
Climb: SMS ✓ (קצבה) → he sweeps the shelf into his basket, 12 bags ✓ (חטיפים) → at the counter "שרית?! גם פה?" →
TWIST (experiment mid_climb_twist): he slaps cash down, Sharit "רק אפליקציה, מותק. בלי מזומן." (chip 3 flashes a red X,
the queue groans) → "אין בעיה. אפליקציה." phone over the terminal → "אושר, מותק." ✓ gold (תשלום), the queue cheers.
Peak: he hugs the basket, eyes closed: hush + heartbeat.
Break (win_is_loss): the phone dings, Sharit glances at her screen: "רגע... עמלת הקדמת תשלום, חמוד." — snap onto his phone:
red "עמלת הקדמת תשלום −49.90 ₪ · יתרה: 0.00 ₪", the terminal flips "בוטל", chips drain, frozen face, whip into the cold open.
No music (voiced rule): voices + SFX + kiosk room tone. Serial pills "פרק 33" + live ticket number (hud.stage_of, §O4).

  python3 ep33.py times
  python3 ep33.py test 0 0.6 1.5 2.4 ...
  python3 ep33.py render                                  -> out/ep33_kitsba.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep12 as E12
import ep13 as E13
import ep18 as E18
import ep21_v1 as V1
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep33', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); PINKSUB = (255, 182, 210); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52)
BLUE = (28, 104, 226); BLGREEN = (18, 120, 110)
QUEUE = int(os.environ.get('QUEUE', '456'))
EP_LABEL = 'פרק 33'
OUTNAME = os.environ.get('OUTNAME', 'ep33_kitsba')
LIMIT = float(os.environ.get('LIMIT', '0'))     # render only the first LIMIT seconds (predictor cuts)
TWOZ = float(os.environ.get('TWOZ', '0'))       # 6א probe: two-shot tighter
COLDPH = os.environ.get('COLDPH', '1') == '1'
COLDZ = float(os.environ.get('COLDZ', '0'))     # 6א probe: cold open tighter on his face
PHSM = os.environ.get('PHSM', '1') == '1'       # 6א probe: want close-up with a smaller phone, bigger face   # 6א probe: cold-open phone lower, his whole face clear
SPEAKER = {0: 'cat', 1: 'cat', 3: 'cat', 27: 'cat', 2: 'sh', 4: 'sh', 5: 'sh'}

# ------------------------------------------------------------------ timeline (from the real line lengths)
SEQ = [1, 0, 27, 2, 3, 4, 5]
COLD_END = round(D[0] + 0.06, 2)          # cold open = L00 "כל החטיפים! הכול שלי!" (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.25)          # ◀◀ רגע קודם
T0 = RW[1]
SLAP = 0.35                               # the cash slap before her "רק אפליקציה" (no line)
HOLDLEN = 0.55
GAPS = {1: 0.10, 0: 0.12, 27: 0.08 + SLAP, 2: 0.10, 3: 0.12, 4: HOLDLEN}
L = {}
t_ = T0 + 0.05
for i in SEQ:
    L[i] = t_
    t_ += D[i] + GAPS.get(i, 0.0)
HOLD = (L[4] + D[4], L[5])                # peak hold: hush + heartbeat
FREEZE = L[5] + D[5]
DUR = round(FREEZE + 0.45, 2)
NF = int(round(DUR * FPS))
OCC = [(0, 0.0)] + [(i, L[i]) for i in SEQ]
NEXT = {i: (L[SEQ[k + 1]] if k + 1 < len(SEQ) else DUR) for k, i in enumerate(SEQ)}

def segments(i, gap_frames=4, thr=0.08):
    env = META[i]['env']; segs = []; start = None; quiet = 0
    for k, v in enumerate(env):
        if v >= thr:
            if start is None: start = k
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet >= gap_frames:
                segs.append((start / FPS, (k - quiet + 1) / FPS)); start = None; quiet = 0
    if start is not None: segs.append((start / FPS, len(env) / FPS))
    return [s_ for s_ in segs if s_[1] - s_[0] >= 0.10]

SUBS = {
    0: [['כל החטיפים!'], ['הכול שלי!']],
    1: [['הקצבה נכנסה.'], ['מוקדם!']],
    27: [['שרית?!'], ['גם פה?']],
    2: [['רק אפליקציה, מותק.'], ['בלי מזומן.']],
    3: [['אין בעיה.'], ['אפליקציה.']],
    4: [['אושר, מותק.']],
    5: [['רגע...'], ['עמלת הקדמת תשלום,'], ['חמוד.']],
}

def chunk_starts(i):
    chunks = SUBS[i]; segs = segments(i)
    tot = sum(len(' '.join(c)) for c in chunks); acc = 0; out = []
    for k, c in enumerate(chunks):
        guess = D[i] * acc / tot; acc += len(' '.join(c))
        if k == 0 or not segs: out.append(0.0 if k == 0 else guess); continue
        best = min((s for s, _ in segs if s > out[-1] + 0.2), key=lambda s: abs(s - guess), default=guess)
        out.append(best)
    return out

CS = {i: chunk_starts(i) for i in SUBS}
def at(i, k): return L[i] + CS[i][k]

CHK1 = at(1, 1) + 0.05                    # "מוקדם!" → ✓ קצבה
CHK2 = at(0, 1) + 0.10                    # "הכול שלי!" → basket full ✓ חטיפים
SLAPT = L[27] + D[27] + 0.12              # the cash hits the counter
DENY = at(2, 0) + 0.25                    # "רק אפליקציה" → chip 3 red X (the twist)
PHONE_UP = L[3] + 0.15                    # "אין בעיה. אפליקציה." → the phone comes out
CHK3 = L[4] + 0.12                        # "אושר, מותק." → terminal green ✓ gold
BREAK = L[5]                              # the phone dings: the fee
REVEAL = at(5, 1) - 0.05                  # "עמלת הקדמת תשלום" → snap onto the phone

SUB_TIMES = []
for i0, s0 in OCC:
    for k, c in enumerate(SUBS[i0]):
        a = s0 + max(0.0, CS[i0][k] - 0.05)
        b = s0 + (CS[i0][k + 1] - 0.05 if k + 1 < len(SUBS[i0]) else D[i0] + 0.2)
        if s0 == 0.0: b = min(b, COLD_END)
        else: b = min(b, NEXT[i0] - 0.03)
        SUB_TIMES.append((a, b, c, i0))

C = lambda i: L[i] - 0.08
SHOTS = [('kiosk', 0.0, COLD_END), ('rewind', COLD_END, T0), ('phone', T0, C(0)), ('kiosk', C(0), C(27)),
         ('two', C(27), C(3)), ('pay', C(3), CHK3 - 0.12), ('two', CHK3 - 0.12, REVEAL), ('reveal', REVEAL, FREEZE - 0.02),
         ('frozen', FREEZE - 0.02, DUR + 1)]

TOPCAPS = [(0.0, C(0), ['קצבה מוקדמת', 'מביטוח לאומי?'], 96, 250, WHITE)]   # hook F10 (ep32 was F16), keyword ביטוח לאומי + קצבה

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def talk(t, i):
    for li, s0 in OCC:
        if li == i and s0 <= t < s0 + D[i]:
            env = META[i]['env']; k = int((t - s0) * FPS)
            return env[k] if k < len(env) else 0.0
    return 0.0

def speaking(t):
    for li, s0 in OCC:
        if s0 <= t < s0 + D[li]: return li
    return None

def cat_v(t):
    li = speaking(t)
    return talk(t, li) if li is not None and SPEAKER[li] == 'cat' else 0.0

def sh_v(t):
    li = speaking(t)
    return talk(t, li) if li is not None and SPEAKER[li] == 'sh' else 0.0

def cat_mouth(t, rest='w', loud='smile'):
    v = cat_v(t)
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

# ------------------------------------------------------------------ props
PW, PH = 400, 700
_PH = {}
def phone_layer(state):
    """state: 'sms' (the plant) | 'pay' (payment screen + grey fine print) | 'ok' (green אושר) | 'fee' (red: the break)"""
    if state in _PH: return _PH[state]
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(242, 244, 248))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    if state == 'sms':
        pd.rectangle([S(14), S(70), S(PW - 14), S(150)], fill=BLGREEN)
        pd.text((S(PW / 2), S(111)), 'ביטוח לאומי', font=font(S(40), 900), fill=WHITE, anchor='mm')
        pd.rounded_rectangle([S(34), S(172), S(PW - 34), S(520)], radius=S(26), fill=WHITE, outline=(200, 204, 214), width=iw(3))
        E(pd, PW / 2, 240, 44, 44, fill=GREEN)
        line(pd, [(PW / 2 - 20, 240), (PW / 2 - 5, 256), (PW / 2 + 22, 222)], WHITE, 12)
        pd.text((S(PW / 2), S(330)), 'הקצבה', font=font(S(54), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(392)), 'הופקדה', font=font(S(54), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(460)), 'יום ה׳ · 26.11', font=font(S(30), 800), fill=(90, 96, 110), anchor='mm')
        pd.text((S(PW / 2), S(552)), '* הקדמת תשלום לפי בקשתך', font=font(S(25), 800), fill=(140, 144, 156), anchor='mm')   # the plant
    else:
        pd.rectangle([S(14), S(70), S(PW - 14), S(150)], fill=BLUE)
        pd.text((S(PW / 2), S(111)), 'תשלום באפליקציה', font=font(S(34), 900), fill=WHITE, anchor='mm')
        if state in ('pay', 'ok'):
            pd.text((S(PW / 2), S(200)), 'קיוסק', font=font(S(38), 900), fill=(90, 96, 110), anchor='mm')
            pd.text((S(PW / 2), S(290)), '49.90 ₪', font=font(S(84), 900), fill=INK, anchor='mm')
            col = GREEN if state == 'ok' else (60, 120, 230)
            pd.rounded_rectangle([S(40), S(360), S(PW - 40), S(450)], radius=S(45), fill=col, outline=(20, 40, 90), width=iw(5))
            pd.text((S(PW / 2), S(405)), 'אושר' if state == 'ok' else 'לתשלום', font=font(S(44), 900), fill=WHITE, anchor='mm')
            pd.text((S(PW / 2), S(505)), '* עמלת הקדמת תשלום', font=font(S(25), 800), fill=(140, 144, 156), anchor='mm')   # the plant, mid-climb
            pd.text((S(PW / 2), S(540)), 'תחויב בנפרד', font=font(S(25), 800), fill=(140, 144, 156), anchor='mm')
        else:   # 'fee'
            pd.rounded_rectangle([S(30), S(180), S(PW - 30), S(640)], radius=S(28), fill=RED, outline=(90, 10, 14), width=iw(5))
            pd.text((S(PW / 2), S(250)), 'עמלת', font=font(S(50), 900), fill=WHITE, anchor='mm')
            pd.text((S(PW / 2), S(310)), 'הקדמת תשלום', font=font(S(46), 900), fill=WHITE, anchor='mm')
            pd.text((S(PW / 2), S(410)), '−49.90 ₪', font=font(S(76), 900), fill=(255, 236, 120), anchor='mm')
            pd.line([S(60), S(480), S(PW - 60), S(480)], fill=(255, 170, 170), width=iw(3))
            pd.text((S(PW / 2), S(540)), 'יתרה: 0.00 ₪', font=font(S(44), 900), fill=WHITE, anchor='mm')
    _PH[state] = lay
    return lay

def phone_state(t):
    if t >= BREAK + 0.1: return 'fee'
    if t >= CHK3: return 'ok'
    if t >= PHONE_UP - 0.2: return 'pay'
    return 'sms'

def basket_layer(n):
    """red plastic shopping basket with n snack bags sticking out (world units 420x300)"""
    w, h = 460, 420
    lay = Image.new('RGBA', (S(w), S(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rng = random.Random(33)
    cols = [(244, 160, 36), (226, 60, 60), (60, 150, 220), (90, 190, 90), (240, 210, 60), (170, 90, 200)]
    slots = [(120, 150, -14), (330, 150, 12), (225, 120, 2), (170, 170, -6), (290, 175, 8), (80, 190, -20), (370, 190, 18),
             (225, 160, -3), (130, 110, -10), (320, 105, 9), (200, 85, -5), (260, 80, 6)]
    for k in range(min(n, len(slots))):
        x, y, a = slots[k]; col = cols[k % len(cols)]; s_ = 0.62
        pts = xform([(-52 * s_ * 1.3, -110 * s_), (52 * s_ * 1.3, -110 * s_), (48 * s_ * 1.3, 90 * s_), (-48 * s_ * 1.3, 90 * s_)], x, y, a)
        poly(d, pts, fill=col, outline=tuple(max(0, c - 90) for c in col), width=3)
        c_ = xform([(0, -10 * s_)], x, y, a)[0]
        E(d, c_[0], c_[1], 18, 18, fill=(255, 255, 255))
    # the basket body (in front of the bags)
    poly(d, [(20, 210), (440, 210), (400, 410), (60, 410)], fill=(214, 44, 52), outline=(110, 16, 20), width=6)
    for k in range(6):
        x0 = 70 + k * 62
        d.rounded_rectangle([S(x0), S(240), S(x0 + 36), S(380)], radius=S(10), fill=(150, 24, 30))
    d.rectangle([S(20), S(205), S(440), S(228)], fill=(236, 70, 76), outline=(110, 16, 20), width=iw(4))
    return lay

def cash_layer():
    """a ₪200 note (generic, no real design)"""
    lay = Image.new('RGBA', (S(380), S(190)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(379), S(189)], radius=S(12), fill=(214, 150, 120), outline=(120, 60, 40), width=iw(5))
    d.rounded_rectangle([S(16), S(16), S(364), S(174)], radius=S(8), outline=(150, 80, 60), width=iw(3))
    E(d, 110, 95, 58, 58, fill=(196, 128, 100), outline=(150, 80, 60), width=3)
    d.text((S(260), S(96)), '200 ₪', font=font(S(70), 900), fill=(90, 34, 20), anchor='mm')
    return lay

def app_sign():
    """stand-up counter sign: 'רק אפליקציה · לא מקבלים מזומן'"""
    w, h = 250, 150
    lay = Image.new('RGBA', (S(w + 8), S(h + 8)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(4), S(4), S(w + 4), S(h + 4)], radius=S(12), fill=(252, 250, 242), outline=(60, 60, 70), width=iw(4))
    d.rectangle([S(4), S(4), S(w + 4), S(42)], fill=BLUE)
    d.text((S(4 + w / 2), S(24)), 'רק אפליקציה', font=font(S(28), 900), fill=WHITE, anchor='mm')
    d.text((S(4 + w / 2), S(78)), 'לא מקבלים', font=font(S(30), 900), fill=INK, anchor='mm')
    d.text((S(4 + w / 2), S(118)), 'מזומן', font=font(S(30), 900), fill=INK, anchor='mm')
    return lay

def term_layer(state):
    """kiosk terminal: 0 waiting, 'ok' green אושר, 'void' red בוטל"""
    lay = V1.terminal_layer(0); d = ImageDraw.Draw(lay)
    if state == 'ok':
        d.rounded_rectangle([S(24), S(26), S(V1.TMW - 24), S(150)], radius=S(14), fill=(60, 190, 100), outline=(16, 16, 20), width=iw(4))
        d.text((S(V1.TMW / 2), S(88)), 'אושר', font=font(S(64), 900), fill=WHITE, anchor='mm')
    elif state == 'void':
        d.rounded_rectangle([S(24), S(26), S(V1.TMW - 24), S(150)], radius=S(14), fill=RED, outline=(16, 16, 20), width=iw(4))
        d.text((S(V1.TMW / 2), S(88)), 'בוטל', font=font(S(64), 900), fill=WHITE, anchor='mm')
    return lay

def wall_clock(d, c, r, t):
    E(d, c[0] + 5, c[1] + 7, r + 2, r + 2, fill=(0, 0, 0, 60))
    E(d, c[0], c[1], r, r, fill=(58, 58, 64)); E(d, c[0], c[1], r - 10, r - 10, fill=(250, 248, 238))
    for k in range(12):
        a = math.radians(k * 30)
        line(d, [(c[0] + (r - 16) * math.sin(a), c[1] - (r - 16) * math.cos(a)), (c[0] + (r - 26) * math.sin(a), c[1] - (r - 26) * math.cos(a))], (40, 40, 44), 4)
    mins = 9 * 60 + 2 + t * 0.6
    for ang, ln, wd in (((mins / 60) % 12 / 12 * 360, r * 0.48, 9), ((mins % 60) / 60 * 360, r * 0.72, 6)):
        a = math.radians(ang); line(d, [c, (c[0] + ln * math.sin(a), c[1] - ln * math.cos(a))], (30, 30, 34), wd)
    E(d, c[0], c[1], 7, 7, fill=(30, 30, 34))

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    m.paste_center(img, lay, S(c[0]), S(c[1]))

def shadow_rot(img, lay, c, ang=0.0, sc=1.0, a=100):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    V1.shadow_paste(img, lay, c, a, (10, 14), 8)

def burst(img, c, u, col=(255, 236, 120), r0=150, n=10, dur=0.4):
    if not (0 <= u < dur): return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(n):
        a_ = math.radians(k * 360 / n + 10); ra, rb = r0 + 60 * u, r0 + 80 + 200 * u
        line(od, [(c[0] + ra * math.cos(a_), c[1] + ra * math.sin(a_)), (c[0] + rb * math.cos(a_), c[1] + rb * math.sin(a_))], col + (int(230 * (1 - u / dur)),), 10)
    img.alpha_composite(ov)

# ------------------------------------------------------------------ the kiosk, wide: the cold open + the sweep (L00 replayed)
KX, KY, KF = 600, 880, 1.62
QUEUE_K = [('h0', 150, 820, 0.50, 0.3), ('c2', 330, 760, 0.46, 1.4), ('c3', 900, 790, 0.50, 2.2), ('h2', 1030, 900, 0.48, 0.9)]

def bags_at(t):
    """bags in the basket: the sweep happens during L00 (cold open = its replay)"""
    tc = t if t < COLD_END else (t - L[0] if L[0] <= t else -1)
    if t >= L[0] + D[0] or (t >= CHK2): return 12
    if tc < 0: return 3
    return int(3 + 9 * clamp(tc / max(0.3, CS[0][1] + 0.1)))

def scene_kiosk(t, i):
    img = KIOSK0.copy(); d = ImageDraw.Draw(img)
    wall_clock(d, (830, 520), 74, t)
    replay = t < COLD_END
    tc = t if replay else t - L[0]
    mood = 1 if int(tc / 0.6) % 2 == 0 else 0        # the queue: shocked / annoyed at the man emptying the shelf
    for name, x, y, sc, ph in QUEUE_K:
        hop = -12 * abs(math.sin(t * 6 + ph)) if mood == 1 else 0
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + hop + 8 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    v = cat_v(t)
    # "כל החטיפים! הכול שלי!" — wide-eyed disbelief (the money came EARLY), sweat, shouting → a huge grin on "הכול שלי!"
    st.update(lid=0.0, pupil='tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-24, sweat=1.0, blush=0.6, look=(0, -4))
    dy = -16 * v - 12 * abs(math.sin(t * 8)); rot = 5 * math.sin(t * 9)
    if tc >= CS[0][1] - 0.1:
        st.update(pupil='big', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-30, blush=1.0, look=(0, -12))
        rot = -8 + 4 * math.sin(t * 12); dy -= 18
    E(d, KX, 1650 + 0.5 * dy, 430, 450, fill=FUR, outline=OUT, width=7)
    E(d, KX, 1710 + 0.5 * dy, 200, 300, fill=CREAM)
    # right paw (viewer's left): the phone with the SMS thrust up (the plant line under it)
    pc = ((230, 1310) if COLDPH else (250, 1150)); pc = (pc[0], pc[1] + 0.4 * dy + 10 * math.sin(t * 14))
    capsule(d, (KX - 230, 1460 + 0.5 * dy), (pc[0] + 20, pc[1] + 250), 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, KX, KY + dy, KF, rot)
    paste_rot(img, phone_layer('sms'), pc, -8 + 3 * math.sin(t * 10), 0.80)
    d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 20, pc[1] + 250), 10, 0.9)
    # left paw (viewer's right): sweeping bags off the shelf into the basket; bags fly
    n = bags_at(t)
    bc = (700, 1500 + 0.3 * dy)
    paste_rot(img, BASKET[n], bc, -4 + 2 * math.sin(t * 7), 0.95)
    d = ImageDraw.Draw(img)
    sw = (t * 7.0) % 1.0
    lp = (lerp(980, 760, ease_io(sw)), lerp(1180, 1320, ease_io(sw)))
    capsule(d, (KX + 230, 1460 + 0.5 * dy), lp, 110, FUR, OUT, 4)
    E12.big_paw(d, lp, -30, 0.9)
    if n < 12:
        rng = random.Random(int(t * 7))
        for k in range(2):     # bags in the air
            u = (sw + 0.5 * k) % 1.0
            bp = (lerp(960, 720, u), lerp(1150, 1360, u) - 160 * math.sin(math.pi * u))
            SH.snack_bag(d, bp, 40 * u - 20 + 30 * k, 0.55)
    # the live queue ticket (§O4) on the counter edge, under the phone arm
    tk = xform([(-48, -78), (48, -78), (48, 78), (-48, 78)], 380, 1570, -8)
    poly(d, tk, fill=(252, 250, 242), outline=(150, 150, 140), width=3)
    c_ = xform([(0, -20)], 380, 1570, -8)[0]
    d.text((S(c_[0]), S(c_[1])), str(QUEUE), font=font(S(40), 900), fill=INK, anchor='mm')
    if t < 0.45 or (L[0] <= t < L[0] + 0.45):
        burst(img, (700, 1250), t if t < COLD_END else t - L[0], (255, 236, 120), 230, 12, 0.45)
    if t >= CHK2: burst(img, (700, 1380), t - CHK2, (255, 220, 90), 220, 12, 0.5)
    return img

# ------------------------------------------------------------------ the want: his face + the phone (SMS) beside it
HXP, HYP, FP = 700, 980, 1.62
def scene_phone(t, i):
    img = KIOSK_BLUR.copy()
    d = ImageDraw.Draw(img)
    v = cat_v(t)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    u = t - L[1]
    if t < CHK1 - 0.05:    # "הקצבה נכנסה." — he can't believe it: eyes huge, sweating
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-18, sweat=1.0, look=(-22, 6))
        rot = 4 * math.sin(t * 7); dy = -10 * v
    else:                  # "מוקדם!" — it sinks in: he lights up
        w_ = t - CHK1
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-28, blush=1.0, look=(-10, -6))
        rot = -3; dy = -36 * abs(math.sin(w_ * 8)) * math.exp(-w_ * 1.6)
    E(d, HXP, 1760, 400, 430, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1810, 180, 290, fill=CREAM)
    pc = (300, 960 + 6 * math.sin(t * 9))
    capsule(d, (HXP - 240, 1560), (pc[0] + 40, pc[1] + 290), 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP - (20 if PHSM else 0), HYP + dy - 8 * v - (30 if PHSM else 0), FP * (1.22 if PHSM else 1.0), rot)
    sc = 1.04 + (0.1 * math.exp(-(t - CHK1) * 8) if t >= CHK1 else 0.18 * math.exp(-u * 9))
    if PHSM: sc *= 0.78; pc = (250, pc[1] + 60)
    paste_rot(img, phone_layer('sms'), pc, -6, sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (pc[0] + 40, pc[1] + 290), 8, 0.95)
    if u < 0.4: burst(img, (300, 1050), u, (255, 255, 255), 120, 8, 0.3)
    if t >= CHK1: burst(img, (300, 1080), t - CHK1, (120, 230, 140), 220, 12, 0.5)
    return img

# ------------------------------------------------------------------ "אין בעיה. אפליקציה.": his face + the payment screen (the plant, mid-climb)
def scene_pay(t, i):
    img = KSH_BG.copy(); d = ImageDraw.Draw(img)
    v = cat_v(t); u = t - L[3]
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.5)
    st.update(lid=0.25, pupil='normal', brow='none', mouth=cat_mouth(t, rest='smile', loud='smile'), look=(-22, 8), blush=0.5, ear_dy=-8)
    if u < 0.35: st.update(lid=0.0, pupil='big', brow='up')
    rot = -4 + 2 * math.sin(t * 4); dy = -8 * v
    E(d, HXP, 1760, 400, 430, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1810, 180, 290, fill=CREAM)
    pc = (300, 960 + 5 * math.sin(t * 8))
    capsule(d, (HXP - 240, 1560), (pc[0] + 40, pc[1] + 290), 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP, HYP + dy, FP, rot)
    sc = 1.04 + 0.16 * math.exp(-u * 9)
    paste_rot(img, phone_layer('pay'), pc, -6 + 4 * math.exp(-u * 6), sc)
    d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 40, pc[1] + 290), 8, 0.95)
    # the cool flip: he spins the phone out like a card
    burst(img, (300, 1060), u, (255, 255, 255), 140, 8, 0.3)
    return img

# ------------------------------------------------------------------ the counter: Sharit at the till (left), the cat (right)
T_HEAD = (225, 900); TS = 1.45
HX2, HY2, F2 = 800, 960, 1.45
QUEUE_TWO = [('c2', 560, 700, 0.44, 0.4), ('h0', 700, 640, 0.40, 1.6), ('c3', 1000, 700, 0.42, 2.4)]
TERM_C = (300, 1470); SIGN_C = (110, 1480); BASK_C = (560, 1440); CASH_C = (430, 1540)

def kiosk_sharit(st, i):
    keep = (SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O)
    SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O = (240, 128, 40), (206, 96, 24), (110, 50, 10)
    try: return SH.draw(st, i)
    finally: SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O = keep

def phone_pos(t):
    """his phone: comes out on "אפליקציה", hovers over the terminal, then (break) he pulls it up to his face"""
    if t < PHONE_UP - 0.2: return None
    e = ease_out(clamp((t - (PHONE_UP - 0.2)) / 0.3))
    p = lerp2((780, 1650), (TERM_C[0] + 40, TERM_C[1] - 250), e)
    if t < CHK3: p = (p[0], p[1] + 5 * math.sin(t * 14))
    if t >= BREAK: p = lerp2(p, (560, 1150), ease_out(clamp((t - BREAK - 0.1) / 0.3)))
    return p

def scene_two(t, i):
    img = KSH_BG.copy()
    cheer = CHK3 <= t < BREAK - 0.05
    groan = DENY <= t < PHONE_UP + 0.2
    for name, x, y, sc, ph in QUEUE_TWO:
        jump = (-20 * abs(math.sin(t * 9 + ph))) if cheer else 0
        mood = 1 if (cheer or t >= BREAK + 0.3) else (0 if groan else 2)
        E13.paste_sprite(img, name, mood, x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    # Sharit
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.5, red=0.8, blush=0.6, look=(18, 6))
    st_s['mouth'] = 'talk' if sh_v(t) > 0.12 else ('munch' if (i // 4) % 2 and t < SLAPT else 'grin')
    if t < SLAPT: st_s.update(snack=True, lid=0.6)                                              # munching at the till
    elif t < PHONE_UP:                                                                           # "רק אפליקציה, מותק." — pushes the cash back
        st_s.update(hand_r=(600, 760) if t < DENY + 0.3 else (560, 700), look=(22, 16), lid=0.45, rot=-4)
    elif t < BREAK:
        st_s.update(look=(22, 18), lid=0.4, blush=0.8)
        if t >= CHK3: st_s.update(hand_r=(560, 600), look=(20, 0), blush=1.0)                    # "אושר, מותק." — thumbs at him
    else:                                                                                        # glances down at her screen: "רגע..."
        st_s.update(look=(6, 26), lid=0.6, red=1.0, blush=0.3, rot=-3, hand_r=(560, 720))
    Ls = kiosk_sharit(st_s, i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    # the cat
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy = 0.0, 0.0
    v = cat_v(t)
    if t < SLAPT - 0.1:                     # "שרית?! גם פה?" — double take
        u = t - L[27]
        st.update(lid=0.0, pupil='tiny', brow='up', ear_dy=-24 * math.exp(-u * 2), mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0,
                  look=(-20, 4) if int(u * 6) % 2 == 0 and u < 0.5 else (-16, 0))
        rot = 8 * math.sin(u * 20) * math.exp(-u * 3); dy = -30 * math.exp(-u * 5)
    elif t < L[3]:                          # the cash slap, then her "no": shock
        u = t - SLAPT
        if t < DENY: st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-18, 14), blush=0.6); dy = 10 * math.exp(-max(0, u) * 8)
        else: st.update(lid=0.0, pupil='tiny', brow='annoyed', mouth='w', sweat=1.0, ear_dy=-10, look=(-20, 6)); rot = 3 * math.sin(t * 30) * math.exp(-(t - DENY) * 3)
    elif t < CHK3:                          # "אין בעיה. אפליקציה." — cool, confident
        st.update(lid=0.25, pupil='normal', brow='none', mouth=cat_mouth(t, rest='smile', loud='smile'), look=(-20, 10), blush=0.5)
        rot = -4 + 2 * math.sin(t * 4)
    elif t < HOLD[0]:                       # "אושר, מותק." — joy
        u = t - CHK3
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24 * math.exp(-u * 3), look=(-10, 0), blush=1.0)
        dy = -20 * abs(math.sin(u * 9)) * math.exp(-u * 1.5)
    elif t < BREAK:                         # THE PEAK: hugging the basket, eyes closed
        st.update(eye_mode='closed', mouth='smile', ear_dy=-28, blush=1.0, look=(0, -8)); dy = -12; rot = -6
    else:                                   # the ding: eyes snap open, frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-20 * math.exp(-u * 4), look=(-14, 14),
                  twitch=(0.4 < u < 1.2 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.4), blush=0.0)
        dy = -8
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    # counter
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1720)], radius=S(16), fill=(150, 96, 58), outline=(80, 50, 28), width=iw(6))
    d.rectangle([S(-20), S(1580), S(1100), S(1606)], fill=(190, 130, 80))
    shadow_rot(img, SIGN, SIGN_C, 4, 0.9, 90)
    tl = TERM_VOID if t >= BREAK + 0.35 else (TERM_OK if t >= CHK3 else TERM_WAIT)
    shadow_rot(img, tl, TERM_C, 4, 0.75, 90)
    # the basket on the counter (hugged at the peak)
    hug = HOLD[0] - 0.15 <= t
    bc = (BASK_C[0] + (110 if hug else 0), BASK_C[1] - (40 if hug else 0))
    if t >= BREAK + 0.4: bc = lerp2(bc, (BASK_C[0] - 260, BASK_C[1]), ease_in(clamp((t - BREAK - 0.4) / 0.4)))   # slides back to her side
    paste_rot(img, BASKET[12], bc, -3, 0.85)
    d = ImageDraw.Draw(img)
    # the cash: slapped, then pushed back toward him
    if SLAPT - 0.12 <= t < PHONE_UP + 0.3:
        u = t - SLAPT
        cc = lerp2((780, 1150), CASH_C, ease_in(clamp((u + 0.12) / 0.12))) if u < 0 else CASH_C
        if t >= DENY: cc = lerp2(CASH_C, (900, 1560), ease_out(clamp((t - DENY) / 0.3)))
        shadow_rot(img, CASH, cc, -8, 0.7, 90)
        d = ImageDraw.Draw(img)
        if 0 <= u < 0.3: burst(img, CASH_C, u, (255, 255, 255), 120, 8, 0.25)
    # his paws
    pp = phone_pos(t)
    if hug and t < BREAK:
        for side in (-1, 1):
            rp = (bc[0] + side * 200, bc[1] + 30)
            capsule(d, (HX2 + side * 200, 1520), rp, 100, FUR, OUT, 4); E12.big_paw(d, rp, side * 30, 0.85)
    elif pp is not None:
        capsule(d, (HX2 - 160, 1540), (pp[0] + 30, pp[1] + 170), 100, FUR, OUT, 4)
    else:
        rp = (HX2 - 120, 1480 + 8 * math.sin(t * 2.0))
        if SLAPT - 0.12 <= t < SLAPT + 0.25: rp = (CASH_C[0] + 80, CASH_C[1] - 30)
        capsule(d, (HX2 - 160, 1540), rp, 100, FUR, OUT, 4); E12.big_paw(d, rp, 10, 0.85)
    if pp is not None and not (hug and t < BREAK):
        paste_rot(img, phone_layer(phone_state(t)), pp, 4, 0.5)
        d = ImageDraw.Draw(img); E12.big_paw(d, (pp[0] + 30, pp[1] + 170), -10, 0.7)
    if cheer: E18.confetti(img, t - CHK3 + 0.5)
    burst(img, (TERM_C[0], TERM_C[1] - 100), t - CHK3, (120, 255, 160), 170, 12, 0.4)
    if t >= BREAK: burst(img, (pp[0], pp[1] - 100) if pp else (560, 1100), t - BREAK, (255, 120, 120), 170, 10, 0.35)
    return img

# ------------------------------------------------------------------ the reveal: the fee on his phone, his face behind it
def scene_reveal(t, i):
    img = KIOSK_BLUR.copy(); d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.0)
    u = t - REVEAL
    st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-20 * math.exp(-u * 4), look=(-22, 8),
              twitch=(0.3 < u < 0.9 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.3))
    E(d, HXP, 1760, 400, 430, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1810, 180, 290, fill=CREAM)
    pc = (310, 1100)
    capsule(d, (HXP - 240, 1560), (pc[0] + 40, pc[1] + 290), 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP, HYP, FP, 0)
    paste_rot(img, phone_layer('fee'), pc, -5 + 2 * math.sin(t * 40) * math.exp(-u * 6), 1.14 + 0.12 * math.exp(-u * 9))
    d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 40, pc[1] + 290), 8, 0.95)
    burst(img, (310, 1060), u, (255, 120, 120), 240, 12, 0.4)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('קצבה', 790, CHK1), ('חטיפים', 540, CHK2), ('תשלום', 290, CHK3)]
def chips(frame, t):
    if t < C(0): return                     # the hook owns the top band until the sweep
    gold = t >= CHK3
    drained = t >= REVEAL + 0.1
    if t >= REVEAL + 0.7: return
    d = ImageDraw.Draw(frame)
    y = 330
    for k_, (lab, cx, tk) in enumerate(CHIPS):
        ok = t >= tk and not drained
        denied = k_ == 2 and DENY <= t < PHONE_UP                # the twist: the third chip flashes a red X
        fill = GOLD if (gold and not drained) else (RED if denied else ((255, 255, 255) if ok else (40, 42, 52)))
        ink = INK if (ok or (gold and not drained)) else (WHITE if denied else (190, 194, 206))
        u = t - (DENY if denied else tk)
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and (ok or denied)) else 1.0
        if drained and t - REVEAL < 0.6: sc = 1.0 + 0.15 * math.exp(-(t - REVEAL - 0.1) * 10)
        w, h = 220 * sc, 70 * sc
        jx = random.Random(int(t * FPS) + cx).uniform(-8, 8) if ((drained and t - REVEAL < 0.6) or (denied and u < 0.4)) else 0
        d.rounded_rectangle([cx + jx - w / 2, y - h / 2, cx + jx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + jx + 22 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx + jx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        elif denied:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=(120, 10, 16))
            for s1, s2 in (((-9, -9), (9, 9)), ((9, -9), (-9, 9))):
                d.line([(bx + s1[0] * sc, y + s1[1] * sc), (bx + s2[0] * sc, y + s2[1] * sc)], fill=WHITE, width=int(6 * sc))
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
KIOSK0 = KIOSK_BLUR = KSH_BG = BASKET = CASH = SIGN = TERM_WAIT = TERM_OK = TERM_VOID = PILL_EP = PILL_Q = None
def init_all():
    global KIOSK0, KIOSK_BLUR, KSH_BG, BASKET, CASH, SIGN, TERM_WAIT, TERM_OK, TERM_VOID, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    E13.build_crowd()
    kb = V1.build_kiosk_bg()
    k0 = kb.filter(ImageFilter.GaussianBlur(S(1.2)))                      # R6: bright daylight
    k0.alpha_composite(Image.new('RGBA', k0.size, (255, 252, 240, 70))); KIOSK0 = k0
    KIOSK_BLUR = k0.filter(ImageFilter.GaussianBlur(S(3)))
    KSH_BG = k0.filter(ImageFilter.GaussianBlur(S(2.5)))
    BASKET = [basket_layer(n) for n in range(13)]
    CASH = cash_layer(); SIGN = app_sign()
    TERM_WAIT = term_layer(0); TERM_OK = term_layer('ok'); TERM_VOID = term_layer('void')
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'kiosk':
        z = (COLDZ or 1.06) + 0.04 * pu; cy = 980 if not COLDZ else 900
        if t < 0.3: z = (COLDZ or 1.06) + 0.22 - 0.22 * ease_out(t / 0.3)          # frame 0: snap pull-back, already moving
    elif name == 'rewind':
        z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'phone':
        z = 1.05 + 0.03 * pu; cy = 1000; cx = 520
        if t >= CHK1: z = z + 0.05 * math.exp(-(t - CHK1) * 6)
    elif name == 'pay':
        z = 1.05 + 0.03 * pu; cy = 1000; cx = 520
    elif name == 'two':
        z = (TWOZ or 1.0) + 0.02 * pu
        if t >= HOLD[0]:
            k = ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0])))
            z = z + 0.10 * k; cx, cy = lerp(540, 640, k), 1000
        if t >= BREAK: z, cx, cy = z + 0.10 + 0.04 * (t - BREAK), 640, 1000
    elif name == 'reveal':
        z, cx, cy = 1.06 + 0.03 * pu, 520, 1000
    elif name == 'frozen':
        z, cx, cy = 1.30 + 0.03 * pu, 700, 960                                                         # his frozen face
    if name not in ('rewind', 'frozen') and not (name == 'kiosk' and t < 0.3) and pu < 0.2:
        z = z + 0.07 * (1 - ease_out(pu / 0.2))   # snap-zoom on every cut
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'kiosk': img = scene_kiosk(t, i)
    elif name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_phone(lerp(C(0) - 0.2, T0 + 0.3, ease_in(u)), i)
    elif name == 'phone': img = scene_phone(t, i)
    elif name == 'pay': img = scene_pay(t, i)
    elif name == 'two': img = scene_two(t, i)
    else: img = scene_reveal(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 18 * math.exp(-t * 5)
    if name == 'two' and 0 <= t - SLAPT < 0.3: shake = 12 * math.exp(-(t - SLAPT) * 8)
    if name == 'reveal' and t - REVEAL < 0.3: shake = 10 * math.exp(-(t - REVEAL) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if name == 'two' and HOLD[0] <= t < BREAK:     # the hush: dims a touch, heartbeat pulse
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.24 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(60 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CHK2, CHK3, REVEAL):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:   # whip out -> loops into the cold open
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    chips(frame, t)
    for t0, t1, lines, size, yc, fill in TOPCAPS:
        if t0 <= t < t1:
            cap = m.caption_layer(lines, size, fill)
            m.paste_center(frame, cap, W / 2, yc)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            cap = sub_layer(lines, PINKSUB if SPEAKER[li] == 'sh' else WHITE)
            low = name in ('two', 'reveal', 'frozen')
            m.paste_center(frame, cap, W / 2, (1500 if low else 1450) if len(lines) == 1 else (1470 if low else 1420))
    if name in ('kiosk', 'frozen'):   # serial markers (§O3); the ticket flickers in the last second
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(33)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:02d}.npy')).astype(np.float64)
        add(voice, y, s0, 0.95 if SPEAKER[i0] == 'cat' else 0.9)
    def whoosh(t0, g=0.06, wl=0.16): add(sfx, m.bandpass(nz(wl), 600, 5000) * np.sin(np.pi * tt_(wl) / wl) ** 2, t0 - 0.08, g)
    def thud(g=0.9):
        tt = tt_(0.45); freq = 150 * np.exp(-tt * 6) + 42
        return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) + m.lowpass(nz(0.45), 420) * np.exp(-tt * 30) * 0.8) * g
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def buzz(t0, g=0.16):
        tt = tt_(0.32); add(sfx, m.lowpass(np.sign(np.sin(2 * np.pi * 110 * tt)), 1200) * np.exp(-tt * 4), t0, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def rustle(t0, ln=0.25, g=0.08): add(sfx, m.bandpass(nz(ln), 2000, 9000) * np.sin(np.pi * tt_(ln) / ln) ** 1.5, t0, g)
    def groan(t0, ln=0.9, g=0.12):
        tt = tt_(ln); fr = 220 - 70 * tt / ln
        sig = m.lowpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr) / SR)) * 0.5 + 0.5 * nz(ln), 900) * np.sin(np.pi * tt / ln)
        add(sfx, sig, t0, g)
    def ding(t0, g=0.22):
        add(sfx, m.tone(1318.5, 0.5, harm=((1, 1), (2, 0.25)), decay=5), t0, g)
        add(sfx, m.tone(987.8, 0.7, harm=((1, 1), (2, 0.25)), decay=4), t0 + 0.12, g)
    def cheer(t0, ln=1.0, g=0.10):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    # cold open: impact + bag rustles + crowd gasp
    add(sfx, thud(1.0), 0.0); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), 0.0, 0.4)
    for k in range(int(COLD_END / 0.143)): rustle(0.05 + k * 0.143, 0.12, 0.07)
    groan(0.35, 0.9, 0.08)
    # rewind tape
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    # kiosk murmur (room tone) everywhere except the hush
    m1 = HOLD[0]; add(sfx, m.bandpass(nz(m1), 200, 1400) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * tt_(m1))), 0.0, 0.025)
    add(sfx, m.bandpass(nz(DUR - BREAK + 0.3), 200, 1400), BREAK, 0.02)
    # the SMS arrives (want line) + ✓1
    ding(L[1] - 0.02, 0.10); check(CHK1, 0.15)
    # the sweep (L00 in context): rustles + ✓2
    for k in range(int(D[0] / 0.143)): rustle(L[0] + k * 0.143, 0.12, 0.07)
    add(sfx, thud(0.5), CHK2); check(CHK2 + 0.04, 0.18)
    # cuts
    for name, a, b in SHOTS[2:]:
        if name not in ('frozen',): whoosh(a)
    # the cash slap, her "no": buzz + groan (the twist)
    add(sfx, thud(0.7), SLAPT); add(sfx, m.highpass(nz(0.04), 2500) * np.exp(-tt_(0.04) * 90), SLAPT, 0.3)
    buzz(DENY, 0.12); groan(DENY + 0.05, 0.8, 0.12)
    # the phone out, the tap, ✓3 gold + cheer
    rustle(PHONE_UP - 0.2, 0.2, 0.08)
    add(sfx, m.tone(2093.0, 0.15, harm=((1, 1),), decay=20), CHK3 - 0.1, 0.12)
    check(CHK3 + 0.02, 0.2, True); cheer(CHK3 + 0.1, max(0.4, HOLD[0] - CHK3), 0.10)
    # peak: hush + heartbeat
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.05 + 0.28, 0.5)
    # break: the phone's ding, then (on "עמלת") one low "dun" + the terminal's error beep
    ding(BREAK, 0.20)
    add(sfx, thud(0.8), REVEAL)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), REVEAL + 0.02, 0.30)
    for k in range(2): add(sfx, m.tone(440.0, 0.12, harm=((1, 1), (3, 0.3)), decay=10), REVEAL + 0.25 + k * 0.16, 0.08)
    out = voice + sfx
    out = out[:int(DUR * SR)]
    wl_ = 0.3; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.28)
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())

# ------------------------------------------------------------------ main
def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if mode == 'times':
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END); print('L', {k: round(v, 2) for k, v in L.items()}); print('D', D)
        print('CS', {k: [round(x, 2) for x in v] for k, v in CS.items()})
        print('CHK', round(CHK1, 2), round(CHK2, 2), 'SLAP', round(SLAPT, 2), 'DENY', round(DENY, 2), 'PHONE_UP', round(PHONE_UP, 2),
              'CHK3', round(CHK3, 2), 'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK, 2), 'REVEAL', round(REVEAL, 2), 'FREEZE', round(FREEZE, 2))
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames):
            sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep33_contact.png')); print('ok'); return
    if mode == 'frame':
        init_all(); tm = float(sys.argv[2])
        draw_frame(min(NF - 1, int(round(tm * FPS)))).save(os.path.join(OUTDIR, sys.argv[3] if len(sys.argv) > 3 else 'ep33_frame.png')); return
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
