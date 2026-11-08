#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 30: ביטוח לאומי: מענק "אוטומטי" (season 7 "הכסף בדרך", VOICED, built 8.11 under §P, target 30 s;
experiment story_cta_onscreen). Voices = voice bank 3000–3010 (Benji = cat, Delia = Sharit; 3003 = 3000's text, so the cold-open
line is replayed in context) + 2703 "שרית?! גם פה?", prepared by voice/ep30_prep.py.
Want: make sure the "automatic" winter grant really comes to HIM (he does not believe in "automatic").
Plant: the ביטוח לאומי envelope in his paw from frame 0, small grey print "לכבוד: סבתא · אילת" (his registered address is
grandma's since ep8–9); slapped on the glass mid-climb; he even says it himself ("הכתובת הרשומה. אילת."). Never pointed at.
Climb: Sharit "אין טופס, מותק. זה אוטומטי." → he insists → she finds a form ✓ (טופס) → he signs three times ✓ (חתימה) →
"רגע, מותק... איזה כתובת?" → "הכתובת הרשומה. אילת." → STAMP "המענק... אושר!" ✓ gold (אושר), the queue cheers.
Peak: the approval letter in both paws, "סוף סוף... משהו אוטומטי שעובד.", hush + heartbeat.
Break (mixup): Sharit, munching: "מזל טוב לסבתא, מותק." — snap onto the letter's small print, chips drain, frozen face, whip
into the cold open (loop). Experiment: Sharit's in-world counter sign "ספרו לי בתגובות מה קרה לכם · הסיפור הכי טוב יהפוך לפרק"
in every Sharit shot, including the break line (no card after the break, §P).
No music (voiced rule): SFX + lobby murmur only. Serial pills "פרק 30" + live ticket (hud.stage_of, §O4).

  python3 ep30.py times
  python3 ep30.py test 0 0.6 1.5 2.4 3 4.5 ...
  python3 ep30.py render                                  -> out/ep30_grant.mp4
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
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep30', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); PINKSUB = (255, 182, 210); GOLD = (255, 196, 40); GREEN = (40, 170, 80)
QUEUE = int(os.environ.get('QUEUE', '462'))
EP_LABEL = 'פרק 30'
OUTNAME = os.environ.get('OUTNAME', 'ep30_grant')
LIMIT = float(os.environ.get('LIMIT', '0'))    # render only the first LIMIT seconds (predictor cuts)
NOCTA = os.environ.get('NOCTA', '0') == '1'    # control: no counter sign
L2TWO = os.environ.get('L2TWO', '0') == '1'    # 6א probe: L02 as a two-shot (his face reacting) instead of Sharit alone
WALKZ = float(os.environ.get('WALKZ', '0'))    # 6א probe: storm-in shot tighter on his face
RANTZ = float(os.environ.get('RANTZ', '0'))    # 6א probe: cold open tighter
WINZ = float(os.environ.get('WINZ', '0'))      # 6א probe: clerk-POV window shots tighter on his face
SPEAKER = {0: 'cat', 1: 'cat', 27: 'cat', 2: 'sh', 4: 'sh', 5: 'cat', 8: 'sh', 9: 'cat', 6: 'sh', 7: 'cat', 10: 'sh'}

# ------------------------------------------------------------------ timeline (from the real line lengths)
SEQ = [1, 27, 2, 0, 4, 5, 8, 9, 6, 7, 10]
COLD_END = round(D[0] + 0.15, 2)          # cold open = L00 "אוטומטי?! אין דבר כזה אוטומטי!" (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.35)          # ◀◀ רגע קודם
T0 = RW[1]
GAPS = {1: 0.10, 27: 0.10, 2: 0.10, 0: 0.12, 4: 0.12, 5: 0.15, 8: 0.10, 9: 0.15, 6: 0.25, 7: 0.50}
L = {}
t_ = T0 + 0.05
for i in SEQ:
    L[i] = t_
    t_ += D[i] + GAPS.get(i, 0.0)
HOLD = (L[7] + D[7], L[10])               # peak hold: hush + heartbeat
FREEZE = L[10] + D[10]
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
    0: [['אוטומטי?!'], ['אין דבר כזה אוטומטי!']],
    1: [['באתי לוודא'], ['שהמענק מגיע אליי.']],
    27: [['שרית?!'], ['גם פה?']],
    2: [['אין טופס, מותק.'], ['זה אוטומטי.']],
    4: [['טוב...'], ['יש לי פה טופס אחד, חמוד.']],
    5: [['חתמתי!'], ['גם פה, גם פה,'], ['וגם פה.']],
    8: [['רגע, מותק...'], ['איזה כתובת?']],
    9: [['הכתובת הרשומה.'], ['אילת.']],
    6: [['המענק...'], ['אושר!']],
    7: [['סוף סוף...'], ['משהו אוטומטי שעובד.']],
    10: [['מזל טוב לסבתא, מותק.']],
}

def chunk_starts(i):
    """start (s, relative) of each subtitle chunk: proportional by text length, snapped to the nearest speech segment"""
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

SLAP = L[0] + 0.18                        # the envelope slapped to the glass on "אוטומטי?!"
CHK1 = at(4, 1) + 0.35                    # "...יש לי פה טופס אחד" → the form lands ✓ טופס
SIGNS = [L[5] + 0.1, at(5, 1) + 0.15, at(5, 2) + 0.05]   # three paw-signatures: "חתמתי!" / "גם פה, גם פה," / "וגם פה."
CHK2 = SIGNS[2] + 0.12                    # ✓ חתימה
CHK3 = at(6, 1)                           # "אושר!" STAMP ✓ gold
REVEAL = L[10] + 0.72                     # "מזל טוב לסבתא," → snap onto the letter's small print

SUB_TIMES = []
for i0, s0 in OCC:
    for k, c in enumerate(SUBS[i0]):
        a = s0 + max(0.0, CS[i0][k] - 0.05)
        b = s0 + (CS[i0][k + 1] - 0.05 if k + 1 < len(SUBS[i0]) else D[i0] + 0.2)
        if s0 == 0.0: b = min(b, COLD_END)
        else: b = min(b, NEXT[i0] - 0.03)
        SUB_TIMES.append((a, b, c, i0))

C = lambda i: L[i] - 0.08
SHOTS = [('rant', 0.0, COLD_END), ('rewind', COLD_END, T0), ('walk', T0, C(27)), ('two', C(27), C(2)), ('two' if L2TWO else 'sh', C(2), C(0)),
         ('win', C(0), C(4)), ('sh', C(4), C(5)), ('two', C(5), C(8)), ('sh', C(8), C(9)), ('win', C(9), C(6)),
         ('two', C(6), C(7)), ('peak', C(7), L[10] - 0.05), ('sh', L[10] - 0.05, REVEAL), ('reveal', REVEAL, DUR + 1)]

TOPCAPS = [(0.0, C(27), ['מענק ״אוטומטי״', 'מביטוח לאומי?'], 92, 250, WHITE)]   # hook (F10), keyword from frame 1

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
ENV_W, ENV_H = 360, 230
def envelope_layer():
    """the ביטוח לאומי envelope: big "מענק חורף" + red "אוטומטי", and the small grey address nobody reads"""
    lay = Image.new('RGBA', (S(ENV_W + 16), S(ENV_H + 16)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    o = 8; x1 = o + ENV_W; y1 = o + ENV_H
    d.rectangle([S(o), S(o), S(x1), S(y1)], fill=(250, 248, 240), outline=(120, 120, 130), width=iw(4))
    poly(d, [(o, o), (o + ENV_W / 2, o + 92), (x1, o)], outline=(170, 170, 176), width=3)
    d.rectangle([S(o), S(o), S(x1), S(o + 40)], fill=(24, 92, 170))
    d.text((S(x1 - 16), S(o + 21)), 'ביטוח לאומי', font=font(S(26), 900), fill=WHITE, anchor='rm')
    d.text((S(x1 - 18), S(o + 92)), 'מענק חורף', font=font(S(48), 900), fill=(20, 30, 60), anchor='rm')
    d.rounded_rectangle([S(o + 18), S(o + 130), S(o + 160), S(o + 174)], radius=S(10), fill=(214, 36, 44))
    d.text((S(o + 89), S(o + 152)), 'אוטומטי', font=font(S(30), 900), fill=WHITE, anchor='mm')
    d.text((S(x1 - 18), S(o + 204)), 'לכבוד: סבתא · אילת', font=font(S(22), 800), fill=(138, 140, 150), anchor='rm')
    return lay

LET_W, LET_H = 330, 430
def letter_layer():
    """the approval letter: green "המענק אושר", seal, and the same small grey address line"""
    lay = Image.new('RGBA', (S(LET_W + 16), S(LET_H + 16)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    o = 8; x1 = o + LET_W; y1 = o + LET_H
    d.rectangle([S(o), S(o), S(x1), S(y1)], fill=(252, 252, 248), outline=(130, 130, 140), width=iw(4))
    d.rectangle([S(o), S(o), S(x1), S(o + 46)], fill=(24, 92, 170))
    d.text((S(x1 - 16), S(o + 24)), 'ביטוח לאומי', font=font(S(28), 900), fill=WHITE, anchor='rm')
    d.text((S(o + LET_W / 2), S(o + 104)), 'המענק אושר', font=font(S(48), 900), fill=(30, 140, 60), anchor='mm')
    for k in range(4): line(d, [(o + 40, o + 160 + k * 34), (x1 - 40 - 50 * (k % 2), o + 160 + k * 34)], (180, 184, 196), 5)
    E(d, o + 90, o + 340, 46, 46, fill=(240, 196, 60), outline=(170, 120, 20), width=4)
    poly(d, m.star(o + 90, o + 340, 30, 6, 0.55, -90), fill=(250, 226, 120))
    d.text((S(x1 - 18), S(o + 398)), 'לכבוד: סבתא · אילת', font=font(S(22), 800), fill=(138, 140, 150), anchor='rm')
    return lay

def form_layer(signs=0):
    lay = Image.new('RGBA', (S(420), S(300)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([S(4), S(4), S(416), S(296)], fill=(252, 252, 246), outline=(150, 150, 150), width=iw(3))
    d.text((S(396), S(34)), 'בקשה · מענק חורף', font=font(S(30), 900), fill=(20, 30, 60), anchor='rm')
    for k in range(3):
        y = 92 + k * 66
        line(d, [(40, y + 26), (250, y + 26)], (150, 156, 170), 4)
        d.text((S(396), S(y + 14)), 'חתימה', font=font(S(24), 800), fill=(90, 96, 110), anchor='rm')
        if k < signs:   # the paw-print signature
            cx, cy = 150, y + 10
            E(d, cx, cy + 6, 22, 17, fill=(40, 60, 140))
            for dx, dy in ((-22, -16), (-7, -24), (9, -24), (24, -16)): E(d, cx + dx, cy + dy, 7, 8, fill=(40, 60, 140))
    return lay

def cta_sign():
    """Sharit's in-world counter sign (experiment story_cta_onscreen)"""
    w, h = 360, 196
    lay = Image.new('RGBA', (S(w + 12), S(h + 12)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(6), S(6), S(w + 6), S(h + 6)], radius=S(16), fill=(255, 236, 120), outline=(120, 90, 10), width=iw(5))
    d.text((S(6 + w / 2), S(46)), 'ספרו לי בתגובות', font=font(S(36), 900), fill=INK, anchor='mm')
    d.text((S(6 + w / 2), S(92)), 'מה קרה לכם', font=font(S(36), 900), fill=INK, anchor='mm')
    d.text((S(6 + w / 2), S(140)), 'הסיפור הכי טוב יהפוך לפרק', font=font(S(25), 800), fill=(110, 40, 20), anchor='mm')
    d.text((S(6 + w / 2), S(178)), '· שרית ·', font=font(S(22), 800), fill=(110, 40, 20), anchor='mm')
    return lay

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    m.paste_center(img, lay, S(c[0]), S(c[1]))

def stamp_layer(text, col=(214, 30, 44)):
    f = font(S(84), 900)
    tw = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(text, font=f)
    w, h = int(tw + S(80)), S(140)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(6), S(6), w - S(6), h - S(6)], radius=S(18), outline=col + (235,), width=iw(9))
    d.text((w / 2, h / 2), text, font=f, fill=col + (235,), anchor='mm')
    return lay

def stamp_tool(d, c, s=1.0):
    """rubber stamp seen from the side: wooden handle + base"""
    x, y = c
    d.rounded_rectangle([S(x - 26 * s), S(y - 150 * s), S(x + 26 * s), S(y - 40 * s)], radius=S(20 * s), fill=(150, 90, 40), outline=(70, 40, 16), width=iw(4))
    E(d, x, y - 160 * s, 40 * s, 30 * s, fill=(170, 104, 50), outline=(70, 40, 16), width=4)
    d.rectangle([S(x - 80 * s), S(y - 44 * s), S(x + 80 * s), S(y)], fill=(60, 60, 66), outline=(20, 20, 24), width=iw(4))
    d.rectangle([S(x - 76 * s), S(y - 8 * s), S(x + 76 * s), S(y + 6 * s)], fill=(200, 30, 40))

def burst(img, c, u, col=(255, 236, 120), r0=150, n=10, dur=0.4):
    if not (0 <= u < dur): return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(n):
        a_ = math.radians(k * 360 / n + 10); ra, rb = r0 + 60 * u, r0 + 80 + 200 * u
        line(od, [(c[0] + ra * math.cos(a_), c[1] + ra * math.sin(a_)), (c[0] + rb * math.cos(a_), c[1] + rb * math.sin(a_))], col + (int(230 * (1 - u / dur)),), 10)
    img.alpha_composite(ov)

CONF = [(random.Random(k).uniform(40, 1040), random.Random(k + 50).uniform(-300, 200), random.Random(k + 9).uniform(0, 6.28),
         [(255, 214, 64), (255, 92, 120), (64, 186, 186), (120, 200, 90), (255, 255, 255)][k % 5]) for k in range(46)]
def confetti(img, u):
    if not (0 <= u < 2.2): return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for x, y0, ph, col in CONF:
        y = y0 + 900 * u + 40 * math.sin(u * 5 + ph); xx = x + 30 * math.sin(u * 3 + ph)
        a = math.degrees(u * 8 + ph)
        poly(od, xform([(-12, -7), (12, -7), (12, 7), (-12, 7)], xx, y, a), fill=col + (230,))
    img.alpha_composite(ov)

# ------------------------------------------------------------------ the lobby (ביטוח לאומי branch), camera on the cat
def build_lobby_bg():
    img = E3.wall_gradient(); d = ImageDraw.Draw(img)
    d.rectangle([0, S(1200), W * K, H * K], fill=E3.WAIN)
    d.rounded_rectangle([S(50), S(410), S(440), S(530)], radius=S(14), fill=(24, 92, 170), outline=(12, 46, 90), width=iw(5))
    d.text((S(245), S(470)), 'ביטוח לאומי', font=font(S(54), 900), fill=WHITE, anchor='mm')
    # the ironic notice (the want's world, not the plant)
    d.rounded_rectangle([S(70), S(560), S(420), S(650)], radius=S(10), fill=(255, 246, 200), outline=(200, 160, 40), width=iw(4))
    d.text((S(245), S(590)), 'מענק חורף: אוטומטי!', font=font(S(32), 900), fill=(200, 40, 40), anchor='mm')
    d.text((S(245), S(628)), 'אין צורך להגיע לסניף', font=font(S(24), 800), fill=(110, 70, 20), anchor='mm')
    x0, y0, x1, y1 = 600, 400, 1020, 640
    d.rounded_rectangle([S(x0 + 8), S(y0 + 10), S(x1 + 8), S(y1 + 10)], radius=S(20), fill=(160, 168, 184))
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(20), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(6))
    d.line([(S(x1 - 130), S(y0 + 20)), (S(x1 - 130), S(y1 - 20))], fill=(60, 60, 70), width=iw(3))
    d.text((S(x1 - 65), S(y0 + 70)), 'חלון', font=font(S(36), 800), fill=E3.AMBER, anchor='mm')
    d.text((S(x1 - 65), S(y0 + 150)), '3', font=font(S(76), 900), fill=E3.AMBER, anchor='mm')
    E3.clock_face(d, 960, 740, 62)
    return img

# the called number jumps around for no reason (running gag #1 lives on the board, §O4)
JUMPS = [(0.0, '17'), (0.9, '904'), (2.0, '12'), (4.4, '3'), (10.0, '388'), (19.0, '1'), (24.0, '76'), (27.5, '17')]
def board_text(t):
    txt = '17'
    for tj, v in JUMPS:
        if t >= tj: txt = v
    for tj, _ in JUMPS:
        if 0 < tj and 0 <= t - tj < 0.3: return txt, int((t - tj) / 0.07) % 2 == 0
    return txt, True

BACK = E13.BACK; MID = E13.MID
HX, HY, F = 540, 1010, 1.38

def crowd_mood_lobby(t, mode):
    if mode == 'rant': return 0
    if mode == 'peak': return 1 if t < HOLD[0] else 2
    if mode == 'reveal': return 1
    return 2

def cat_lobby(t, i, mode):
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy, dx = 0.0, 0.0, 0.0
    v = cat_v(t)
    if mode == 'rant':   # outraged from frame 0 (R5): tiny pupils, sweat, shouting
        st.update(lid=0.0, pupil='tiny', brow='annoyed', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-22, sweat=1.0, blush=0.0, look=(0, 0))
        dy = -14 * v - 10 * abs(math.sin(t * 7)); rot = 5 * math.sin(t * 8.5)
        if t >= CS[0][1]: st['look'] = (-6, -2); rot = -6 * math.sin(t * 9)
    elif mode == 'walk':
        u = t - T0
        st.update(lid=0.0, pupil='big', brow='annoyed', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-10, look=(-8, -2), blush=0.2, sweat=0.4)
        dx = 420 * (1 - ease_out(clamp(u / 0.32))); rot = -10 * (1 - ease_out(clamp(u / 0.45)))
        dy = -14 * abs(math.sin(u * 14)) * math.exp(-u * 2.5) - 8 * v
    elif mode == 'peak':
        u = t - (L[7] - 0.08)
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-24, blush=1.0, look=(0, -10))
        dy = -24 * ease_out(clamp(u / 0.25)); rot = 3 * math.sin(t * 4)
        if t >= HOLD[0]: st.update(mouth='smile', eye_mode='closed'); rot = 0.0   # eyes closed, beaming: the held "this is it"
    else:   # reveal: frozen
        u = t - REVEAL
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-18 * math.exp(-max(0, u) * 4), look=(-14, -6),
                  twitch=(0.2 < u < 0.7 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.3), blush=0.0)
        dy = -24
    return st, rot, dy, dx

def scene_lobby(t, i, mode=None):
    mode = mode or shot(t)[0]
    img = LOBBY.copy()
    txt, on = board_text(t)
    E3.led_text(img, txt, 735, 520, 140 if len(txt) < 3 else 112, on)
    E3.clock_hands(ImageDraw.Draw(img), 960, 740, 62, 11 * 3600 + 40 * 60 + t * 20)
    mood = crowd_mood_lobby(t, mode)
    jit = 1.0 if mood == 1 else 0.4
    hush = mode == 'peak' and t >= HOLD[0]
    for name, x, y, sc, ph in BACK:
        hop = -24 * abs(math.sin(t * 7 + ph)) if (mood == 1 and not hush and mode != 'reveal') else 0
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph) * jit, y + hop + 10 * math.sin(t * 4.4 + ph) * jit * (0 if hush else 1), sc, flip=x > 540)
    for name, x, y, sc, ph in MID:
        hop = -30 * abs(math.sin(t * 6 + ph)) if (mood == 1 and not hush and mode != 'reveal') else 0
        E13.paste_sprite(img, name, mood, x + 8 * math.sin(t * 3.4 + ph), y + hop + 12 * math.sin(t * 5 + ph) * jit * (0 if hush else 1), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy, dx = cat_lobby(t, i, mode)
    hx = HX + dx
    E(d, hx, 1660 + 0.5 * dy, 430, 460, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1720 + 0.5 * dy, 200, 310, fill=CREAM)
    if mode in ('peak', 'reveal'):
        # the approval letter raised in both paws, over his chest (the small print right under his chin)
        lc = (hx, 1330 + 0.4 * dy + (6 * math.sin(t * 6) if t < HOLD[0] else 0))
        for side in (-1, 1): capsule(d, (hx + side * 240, 1480 + 0.5 * dy), (lc[0] + side * 175, lc[1] + 30), 110, FUR, OUT, 4)
        E12.paste_head(img, st, i, hx, HY + dy, F, rot)
        paste_rot(img, LETTER, lc, 2 * math.sin(t * 5) if t < HOLD[0] else 0, 1.05)
        d = ImageDraw.Draw(img)
        for side in (-1, 1): E12.big_paw(d, (lc[0] + side * 178, lc[1] + 30), 90 * side, 0.85)
    else:
        # left paw (viewer's right): the ticket with the live number
        lp = (hx + 175, 1360 + 8 * math.sin(t * 2.0) + 0.5 * dy)
        capsule(d, (hx + 230, 1440 + 0.5 * dy), lp, 110, FUR, OUT, 4)
        tk = xform([(-48, -78), (48, -78), (48, 78), (-48, 78)], lp[0] + 10, lp[1] - 120, 8)
        poly(d, tk, fill=(252, 250, 242), outline=(150, 150, 140), width=3)
        c_ = xform([(0, -20)], lp[0] + 10, lp[1] - 120, 8)[0]
        d.text((S(c_[0]), S(c_[1])), str(QUEUE), font=font(S(40), 900), fill=INK, anchor='mm')
        E12.big_paw(d, lp, -10, 0.9)
        # right paw (viewer's left): the envelope, shaken at the camera on "אוטומטי?!"
        shake_e = 16 * math.sin(t * 15) if mode == 'rant' else 6 * math.sin(t * 9)
        pc = (300, 1150 + 0.5 * dy + shake_e)
        rp = (pc[0] - 120, pc[1] + 112)   # grip the left corner: the small print stays clear
        capsule(d, (hx - 230, 1440 + 0.5 * dy), rp, 110, FUR, OUT, 4)
        E12.paste_head(img, st, i, hx, HY + dy, F, rot)
        paste_rot(img, ENVL, pc, -10 + 4 * math.sin(t * 8), 1.0)
        d = ImageDraw.Draw(img)
        E12.big_paw(d, rp, 10, 0.9)
    if mode == 'walk':   # speed lines while he storms in
        u = t - T0
        if u < 0.45:
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            a = int(220 * (1 - u / 0.45))
            for k in range(7):
                y = 700 + k * 120; x0 = hx + 420 + 60 * (k % 2)
                line(od, [(x0, y), (x0 + 260, y)], (255, 255, 255, a), 10)
            img.alpha_composite(ov)
    if mode == 'rant':   # anger puffs from the ears
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for side in (-1, 1):
            for k in range(3):
                pu = (t * 1.6 + k / 3) % 1.0
                x = hx + side * (250 + 60 * pu); y = 640 - 220 * pu
                r = 26 + 40 * pu
                E(od, x, y, r, r * 0.8, fill=(255, 255, 255, int(170 * (1 - pu))))
        img.alpha_composite(ov)
    if mode == 'peak' and t < HOLD[0]:
        burst(img, (HX, 1250), t - (L[7] + 0.05), (255, 236, 120), 260, 12, 0.5)
    return img

# ------------------------------------------------------------------ window 3, clerk POV
def scene_win(t, i):
    img = E3.WIN_BG.copy(); d = ImageDraw.Draw(img)
    E3.clock_hands(d, 880, 470, 86, 11 * 3600 + 42 * 60 + t * 20)
    cx = 540
    v = cat_v(t)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    replay = t < L[9] - 0.2
    if replay:   # "אוטומטי?! אין דבר כזה אוטומטי!" — insists, the envelope slapped flat on the glass
        st.update(lid=0.0, pupil='tiny', brow='annoyed', ear_dy=-20, mouth=cat_mouth(t, rest='w', loud='w'), look=(0, 0), sweat=1.0)
        e = ease_in(clamp((t - (SLAP - 0.2)) / 0.2))
    else:        # "הכתובת הרשומה. אילת." — proud, the envelope held up by his cheek
        st.update(lid=0.0, pupil='big', brow='up', ear_dy=-10, mouth=cat_mouth(t, rest='smile', loud='smile'), look=(4, -4), blush=0.7)
        e = 1.0
    E3.draw_body(d, cx, 1.0, feet=False)
    capsule(d, (cx + 122, 1180), (cx + 170, 1330), 62, FUR, OUT, 3)
    lp = lerp2((cx - 200, 860), (cx - 150, 1040), e) if replay else (cx - 230, 1000)
    capsule(d, (cx - 122, 1180), lp, 62, FUR, OUT, 3)
    shake = 10 * math.sin(t * 70) * math.exp(-(t - SLAP) * 7) if (replay and t >= SLAP) else 0
    E3.composite_head(img, st, i, cx + shake, 960 - 10 * v)
    d = ImageDraw.Draw(img)
    if replay:
        pc = (lerp(330, 330, e), lerp(900, 1180, e))
        paste_rot(img, ENVL, pc, lerp(-20, -4, e), lerp(1.0, 1.25, e))
        d = ImageDraw.Draw(img); m.draw_paw(d, (pc[0] - 150, pc[1] + 40), ang=-8)
    else:
        pc = (300, 1060 + 6 * math.sin(t * 5))
        paste_rot(img, ENVL, pc, -8, 1.05)
        d = ImageDraw.Draw(img); m.draw_paw(d, (pc[0] - 150, pc[1] + 80), ang=-8)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = E3.WIN
    od.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=(210, 230, 245, 38))
    for k, (a_, b_) in enumerate(((x0 + 60, x0 + 140), (x0 + 190, x0 + 220))):
        poly(od, [(a_, y1), (b_, y1), (b_ + 300, y0), (a_ + 300, y0)], fill=(255, 255, 255, 34 if k == 0 else 26))
    img.alpha_composite(ov)
    img.alpha_composite(E3.WIN_FG)
    SH.snack_bag(ImageDraw.Draw(img), (180, 1560), 12, 1.1)
    if replay and t >= SLAP: burst(img, (pc[0], pc[1]), t - SLAP, (255, 255, 255), 170, 10, 0.3)
    return img

# ------------------------------------------------------------------ Sharit at window 3 (customer POV)
def sh_state(t, i):
    st = SH.base(); st.update(lid=0.55, red=0.8, hand_l=(190, 700))
    v = sh_v(t)
    st['mouth'] = 'talk' if v > 0.12 else 'grin'
    if L[2] - 0.1 <= t < L[0]:          # "אין טופס, מותק. זה אוטומטי." — munching, unbothered
        st.update(snack=True, look=(6, 6), rot=3 * math.sin(t * 2))
        if v <= 0.12: st['mouth'] = 'munch'
    elif L[4] - 0.1 <= t < L[5]:        # "טוב... יש לי פה טופס אחד, חמוד." — digs in the drawer, pulls out ONE form
        st.update(blush=0.6, look=(-10, 14), lid=0.5, rot=-6 * math.sin((t - L[4]) * 2.2))
        if t >= at(4, 1) - 0.1: st.update(look=(0, 2), rot=0.0, hand_r=(560, 600))
    elif L[8] - 0.1 <= t < L[9]:        # "רגע, מותק... איזה כתובת?" — the stamp in the air, stops
        st.update(lid=0.5, look=(0, 0), blush=0.3, hand_r=(560, 560), rot=-4)
    else:                                 # the break: flat, munching, heavy lids
        st.update(snack=True, lid=0.72, red=1.0, look=(4, 10), rot=0.0, blush=0.3)
        if v <= 0.12: st['mouth'] = 'munch'
    return st

def scene_sh(t, i):
    img = E3.OFFICE.copy()
    img.alpha_composite(SH.draw(sh_state(t, i), i), dest=(int(S(E3.SH_POS[0])), int(S(E3.SH_POS[1]))))
    d = ImageDraw.Draw(img)
    if L[4] - 0.1 <= t < L[5] and t >= CHK1 - 0.35:   # the one form, slapped on the counter
        u = t - (CHK1 - 0.35)
        paste_rot(img, FORMS[0], lerp2((780, 780), (540, 1250), ease_out(clamp(u / 0.3))), lerp(30, 4, ease_out(clamp(u / 0.3))), 1.0)
        d = ImageDraw.Draw(img)
    if L[8] - 0.1 <= t < L[9]:   # the stamp raised over the signed form
        paste_rot(img, FORMS[3], (540, 1250), 4, 1.0); d = ImageDraw.Draw(img)
        stamp_tool(d, (740, 760 + 8 * math.sin(t * 3)), 1.0)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); E3.glass_tint(ImageDraw.Draw(ov)); img.alpha_composite(ov)
    img.alpha_composite(E3.GLASS_FG)
    E3.clock_hands(ImageDraw.Draw(img), 900, 420, 66, 11 * 3600 + 41 * 60 + t * 20)
    if not NOCTA:   # experiment: Sharit's counter sign, taped to the glass (in every Sharit shot, also on the break line)
        paste_rot(img, CTA, (215, 735), -4, 0.82)
    return img

# ------------------------------------------------------------------ two-shot: Sharit left, his big face right, counter in front
T_HEAD = (225, 900); TS = 1.45
HX2, HY2, F2 = 790, 960, 1.45
def scene_two(t, i):
    img = SH_BG.copy()
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.55, red=0.8, look=(18, 6))
    st_s['mouth'] = 'talk' if sh_v(t) > 0.12 else 'grin'
    phase = 'gam' if t < L[0] - 0.1 else ('sign' if t < L[6] - 0.1 else 'stamp')
    if phase == 'gam':
        st_s.update(snack=True, lid=0.6, look=(18, 2))
        if sh_v(t) <= 0.12: st_s['mouth'] = 'munch'
    if phase == 'stamp': st_s.update(blush=0.8, lid=0.45)
    Ls = SH.draw(st_s, i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    rot, dy = 0.0, 0.0
    if phase == 'gam':     # "שרית?! גם פה?" — double take
        u = t - L[27]
        st.update(lid=0.0, pupil='tiny', brow='up', ear_dy=-24, mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0, look=(-16, 0))
        rot = 6 * math.sin(u * 10) * math.exp(-u * 2)
        if t >= L[2] - 0.05:   # "אין טופס, מותק. זה אוטומטי." — the outrage builds
            u2 = t - L[2]
            st.update(pupil='tiny', brow='annoyed', mouth='w' if u2 > CS[2][1] else 'flat', ear_dy=-10 - 14 * clamp(u2 / 1.5), look=(-18, 2))
            rot = -3 * clamp(u2 / 0.5) + (4 * math.sin(u2 * 30) if u2 > CS[2][1] + 0.2 else 0)
    elif phase == 'sign':  # signing with the paw, faster each time
        k = sum(1 for s in SIGNS if t >= s)
        st.update(lid=0.0, pupil='big', brow='up', ear_dy=-12 - 4 * k, mouth=cat_mouth(t, rest='smile', loud='smile'), look=(-18, 8), blush=0.4 + 0.2 * k)
        dy = -10 * abs(math.sin(t * 8))
    else:                  # "המענק... אושר!" — STAMP, he lights up
        u = t - CHK3
        st.update(lid=0.0, pupil='big', brow='up', ear_dy=-14, mouth='smile_small', look=(-18, 6), blush=0.6)
        if u >= 0: st.update(ear_dy=-26, mouth='smile', blush=1.0, look=(-10, -4)); dy = -40 * abs(math.sin(u * 7)) * math.exp(-u * 1.4)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy - 10 * cat_v(t), F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    if phase == 'gam': pass
    elif phase == 'sign':
        k = sum(1 for s in SIGNS if t >= s)
        fc = (500, 1210)
        paste_rot(img, FORMS[k], fc, 4, 1.15); d = ImageDraw.Draw(img)
        # the signing paw: thumps down on each signature line
        nxt = min(k, 2); ty = fc[1] - 37 + nxt * 76
        bob = 0.0
        for s in SIGNS:
            u = t - s
            if -0.12 <= u < 0.1: bob = 70 * (1 - abs(u + 0.01) / 0.12)
        pp = (fc[0] - 40, ty + 70 - (bob if k < 3 else 0) + (0 if k < 3 else 90))
        capsule(d, (HX2 - 200, 1640), pp, 100, FUR, OUT, 4)
        E12.big_paw(d, pp, -150, 0.8)
        if k >= 1:
            u = t - SIGNS[k - 1]
            burst(img, (fc[0] - 69, fc[1] - 47 + (k - 1) * 76), u, (120, 140, 255), 60, 8, 0.25)
        if t >= CHK2:
            uu = t - CHK2; s2 = 1.6 - 0.6 * ease_out(clamp(uu / 0.12)); r = 56 * s2
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            c = (720, 1060)
            E(od, c[0], c[1], r, r, fill=GREEN + (235,), outline=WHITE + (255,), width=6)
            line(od, [(c[0] - 0.45 * r, c[1]), (c[0] - 0.1 * r, c[1] + 0.35 * r), (c[0] + 0.5 * r, c[1] - 0.35 * r)], WHITE + (255,), int(14 * s2))
            img.alpha_composite(ov)
    else:
        fc = (480, 1210)
        paste_rot(img, FORMS[3], fc, 4, 1.15); d = ImageDraw.Draw(img)
        u = t - CHK3
        if u < 0:   # the stamp comes down in Sharit's hand
            e = ease_in(clamp((u + 0.45) / 0.45))
            stamp_tool(d, (480, lerp(830, 1190, e)), 1.1)
        else:
            sc = 1.7 - 0.7 * ease_out(clamp(u / 0.1))
            paste_rot(img, STAMP_OK, (480, 1210), 10, sc)
            d = ImageDraw.Draw(img)
            stamp_tool(d, (430, lerp(1190, 900, ease_out(clamp(u / 0.3)))), 1.1)
            burst(img, (480, 1210), u, (255, 236, 120), 200, 12, 0.5)
            confetti(img, u)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('טופס', 770), ('חתימה', 545), ('אושר', 320)]
def chips(frame, t):
    if t < L[27] - 0.1: return              # the hook owns the top band until the first window shot
    done = [t >= CHK1, t >= CHK2, t >= CHK3]; gold = done[2]
    drained = t >= REVEAL + 0.25
    if t >= REVEAL + 0.6: return            # drained, then gone: his frozen eyes own the top of the frame
    d = ImageDraw.Draw(frame)
    y = 330
    for k, (lab, cx) in enumerate(CHIPS):
        ok = done[k] and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - [CHK1, CHK2, CHK3][k]
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        w, h = 200 * sc, 70 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 22 * sc, y), lab, font=font(int(38 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 34 * sc
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
LOBBY = SH_BG = ENVL = LETTER = FORMS = CTA = STAMP_OK = PILL_EP = PILL_Q = None
def init_all():
    global LOBBY, SH_BG, ENVL, LETTER, FORMS, CTA, STAMP_OK, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    LOBBY = build_lobby_bg()
    E13.build_crowd()
    SH_BG = E3.build_office_bg().filter(ImageFilter.GaussianBlur(S(3)))
    ENVL = envelope_layer(); LETTER = letter_layer(); FORMS = [form_layer(k) for k in range(4)]
    CTA = cta_sign(); STAMP_OK = stamp_layer('אושר', (30, 140, 60))
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'rant':
        cy = 960; z = (RANTZ or 1.06) + 0.04 * pu
        if RANTZ: cy = 920
        if t < 0.3: z = (RANTZ or 1.06) + 0.20 - 0.20 * ease_out(t / 0.3)                      # frame 0: snap pull-back, already moving
        if t >= CS[0][1]: z = max(z, 1.10 + 0.06 * math.exp(-(t - CS[0][1]) * 8))
    elif name == 'rewind':
        z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'walk':
        cy = 940; z = 1.05 + 0.03 * pu
        if WALKZ: z, cy = WALKZ + 0.03 * pu, 900
    elif name == 'sh':
        z = 1.16 + 0.03 * pu; cy = 880
        if L[4] <= t < L[5] and t >= CHK1 - 0.35: z, cy = 1.06, 1000                    # show the form landing
        if L[8] - 0.1 <= t < L[9]: z, cy = 1.10 + 0.05 * pu, 940                        # the stamp in the air
        if L[10] - 0.1 <= t: z, cy = 1.24 + 0.04 * pu, 880                              # the flat break line, tighter
    elif name == 'win':
        z = 1.12 + 0.04 * pu; cy = 960
        if WINZ: z, cy = WINZ + 0.04 * pu, 900
    elif name == 'two':
        z = 1.0 + 0.03 * pu
    elif name == 'peak':
        cy = 1000; z = 1.04 + 0.02 * pu
        if t >= HOLD[0]: z = 1.06 + 0.10 * ease_io(clamp((t - HOLD[0]) / (HOLD[1] - HOLD[0])))   # the slow push of the hold
    elif name == 'reveal':
        e = ease_out(clamp((t - REVEAL) / 0.14))
        z, cx, cy = lerp(1.16, 1.45, e), lerp(540, 545, e), lerp(1000, 1286, e)                    # snap onto the small print, chin in frame
        if t >= FREEZE - 0.05:
            k_ = ease_in(clamp((t - FREEZE + 0.05) / 0.4))
            z, cx, cy = lerp(1.45, 1.24, k_), lerp(545, 540, k_), lerp(1286, 1000, k_)
    if name not in ('rewind', 'rant', 'reveal') and pu < 0.2: z = z + 0.07 * (1 - ease_out(pu / 0.2))   # snap-zoom on every cut
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name in ('rant', 'walk', 'peak', 'reveal'): img = scene_lobby(t, i)
    elif name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_lobby(lerp(C(27) - 0.2, T0 + 0.3, ease_in(u)), i, 'walk')
    elif name == 'sh': img = scene_sh(t, i)
    elif name == 'win': img = scene_win(t, i)
    else: img = scene_two(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 18 * math.exp(-t * 5)
    if name == 'two' and t >= CHK3 and t - CHK3 < 0.4: shake = 12 * math.exp(-(t - CHK3) * 6)
    if name == 'reveal' and t - REVEAL < 0.3: shake = 10 * math.exp(-(t - REVEAL) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if name == 'peak' and t >= HOLD[0]:     # the hush: everything dims a touch, heartbeat pulse
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.24 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(60 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CHK3, REVEAL):
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
            m.paste_center(frame, cap, W / 2, 1450 if len(lines) == 1 else 1420)
    if name in ('rant', 'walk', 'peak', 'reveal'):   # serial markers (§O3); the ticket flickers in the last second
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + lobby murmur; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(30)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:02d}.npy')).astype(np.float64)
        add(voice, y, s0, 0.95 if SPEAKER[i0] == 'cat' else 0.9)
    def whoosh(t0, g=0.06, wl=0.16): add(sfx, m.bandpass(nz(wl), 600, 5000) * np.sin(np.pi * tt_(wl) / wl) ** 2, t0 - 0.08, g)
    def thud(g=0.9):
        tt = tt_(0.45); freq = 150 * np.exp(-tt * 6) + 42
        return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) + m.lowpass(nz(0.45), 420) * np.exp(-tt * 30) * 0.8) * g
    def cheer(t0, ln=1.6, g=0.22):
        tt = tt_(ln); env = np.minimum(1, tt / 0.06) * np.exp(-tt * 1.6)
        sig = m.bandpass(nz(ln), 300, 3200) * env * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt))
        add(sfx, sig, t0, g)
        for k, f in enumerate((520, 610, 700)):
            tw = tt_(0.5); fr = f + 220 * tw / 0.5
            add(sfx, m.lowpass(np.sin(2 * np.pi * np.cumsum(fr) / SR), 2000) * np.sin(np.pi * tw / 0.5), t0 + 0.08 + k * 0.11, 0.035)
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def rustle(t0, ln=0.3, g=0.14): add(sfx, m.bandpass(nz(ln), 1500, 7000) * np.exp(-tt_(ln) * 9), t0, g)
    # cold open: impact + paper shake
    add(sfx, thud(1.0), 0.0); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), 0.0, 0.4)
    for k in range(5): rustle(0.25 + k * 0.32, 0.12, 0.06)
    # rewind tape
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    # storm-in skid
    add(sfx, m.bandpass(nz(0.35), 1500, 7000) * np.exp(-tt_(0.35) * 7), T0, 0.12)
    # lobby murmur (room tone) everywhere except the hush
    mur_len = HOLD[0]; mur = m.bandpass(nz(mur_len), 200, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * tt_(mur_len)))
    add(sfx, mur, 0.0, 0.025)
    mur2 = m.bandpass(nz(DUR - HOLD[1] + 0.3), 200, 1400); add(sfx, mur2, HOLD[1], 0.02)
    # cuts
    for name, a, b in SHOTS[2:]:
        if name != 'reveal': whoosh(a)
    # envelope slapped to the glass
    add(sfx, m.highpass(nz(0.08), 1200) * np.exp(-tt_(0.08) * 60), SLAP, 0.55); add(sfx, thud(0.5), SLAP)
    # drawer + the one form lands ✓1
    rustle(L[4] + 0.2, 0.5, 0.10); add(sfx, thud(0.45), CHK1 - 0.05); rustle(CHK1 - 0.08, 0.2, 0.18); check(CHK1, 0.17)
    # three paw-signature thumps ✓2
    for s in SIGNS: add(sfx, thud(0.5), s); rustle(s, 0.1, 0.10)
    check(CHK2, 0.17)
    # the stamp in the air: a held creak
    cl = 0.5; tc = tt_(cl); add(sfx, np.sin(2 * np.pi * np.cumsum(180 + 40 * np.sin(2 * np.pi * 6 * tc)) / SR) * np.sin(np.pi * tc / cl) * 0.5, L[8] + 0.2, 0.04)
    # STAMP ✓3 gold + cheer
    add(sfx, thud(1.0), CHK3); check(CHK3 + 0.08, 0.18, True); cheer(CHK3 - 0.02, 1.8, 0.24)
    # peak: short "aww", then hush + heartbeat
    for k, f in enumerate((523.3, 659.3, 784.0)): add(sfx, m.tone(f, 0.9, harm=((1, 1), (2, 0.2)), decay=3), L[7] + 0.1 + k * 0.03, 0.05)
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.05 + 0.28, 0.5)
    # break: a crunch of her snack, then one low "dun" + the snap zoom hit
    rustle(L[10] + 0.05, 0.12, 0.10)
    add(sfx, thud(0.9), REVEAL)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), REVEAL + 0.02, 0.32)
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
        print('CHK', round(CHK1, 2), round(CHK2, 2), round(CHK3, 2), 'SIGNS', [round(s, 2) for s in SIGNS], 'HOLD', [round(x, 2) for x in HOLD], 'REVEAL', round(REVEAL, 2), 'FREEZE', round(FREEZE, 2))
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
        sheet.save(os.path.join(OUTDIR, 'ep30_contact.png')); print('ok'); return
    if mode == 'frame':
        init_all(); tm = float(sys.argv[2])
        draw_frame(min(NF - 1, int(round(tm * FPS)))).save(os.path.join(OUTDIR, sys.argv[3] if len(sys.argv) > 3 else 'ep30_frame.png')); return
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
