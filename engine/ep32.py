#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 32: הדואר: מספר אחת (season 7 "הכסף בדרך", VOICED, built 9.11 under §P, short arm ~19–21 s;
experiment voiced_length arm short_21 as written in the bible). Voices = voice bank 3200–3205 (Benji = cat, Delia = Sharit)
+ 2703 "שרית?! גם פה?", prepared by voice/ep32_prep.py (3206 not used: after the break only the frozen face, §P).
Want: the ביטוח לאומי letter waiting at the post office; the online queue opens at 10:30 and he wants number 1.
Plant: the red LED seconds clock over the post-office door (in frame 0, in every street shot, behind Sharit) and the small
grey rule "מגיעים לחלון תוך 60 שנ׳ מהקריאה" (the facade sign, the ticket on his phone, the paper by the board). Never pointed at.
Climb: 10:29:57 … 10:30:00 the button lights up ✓ (נפתח) → "עכשיו!" he taps first in the whole street → ticket "1" ✓ (מספר 1),
the crowd's phones say 2, 3, 214 → he runs in, "שרית?! גם פה?" ✓ gold (בסניף) → Sharit: "מספר אחת? כל הכבוד, מותק."
Peak: ticket raised by his cheek, eyes closed, savouring it: hush + heartbeat, the clock ticks 10:30:58, :59.
Break (one_second_late): 10:31:00 — the board flips 1 → 2, Sharit looks past him: "מספר שתיים, בבקשה."; snap onto the board +
clock, chips drain, his frozen face, whip into the cold open (loop).
No music (voiced rule): voices + SFX + street/branch room tone. Serial pills "פרק 32" + live ticket number (hud.stage_of, §O4).

  python3 ep32.py times
  python3 ep32.py test 0 0.6 1.5 2.4 ...
  python3 ep32.py render                                  -> out/ep32_post.mp4
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
VDIR = os.path.join(HERE, 'voice', 'ep32', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); PINKSUB = (255, 182, 210); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52)
BLUE = (28, 104, 226); POSTRED = (206, 38, 44)
QUEUE = int(os.environ.get('QUEUE', '458'))
EP_LABEL = 'פרק 32'
OUTNAME = os.environ.get('OUTNAME', 'ep32_post')
LIMIT = float(os.environ.get('LIMIT', '0'))     # render only the first LIMIT seconds (predictor cuts)
PHZ = float(os.environ.get('PHZ', '0'))         # 6א probe: phone shot tighter on his face
COLDZ = float(os.environ.get('COLDZ', '0'))     # 6א probe: cold open tighter
SPEAKER = {0: 'cat', 1: 'cat', 2: 'cat', 3: 'cat', 27: 'cat', 4: 'sh', 5: 'sh'}

# ------------------------------------------------------------------ timeline (from the real line lengths)
SEQ = [1, 2, 3, 0, 27, 4, 5]
COLD_END = round(D[0] + 0.06, 2)          # cold open = L00 "מספר אחת! אני ראשון!" (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.25)          # ◀◀ רגע קודם
T0 = RW[1]
RUN = 0.45                                # the dash across the street (no line)
HOLDLEN = 0.55
GAPS = {1: 0.08, 2: 0.06, 3: 0.06, 0: 0.10 + RUN, 27: 0.08, 4: HOLDLEN}
L = {}
t_ = T0 + 0.05
for i in SEQ:
    L[i] = t_
    t_ += D[i] + GAPS.get(i, 0.0)
RUNW = (L[0] + D[0] + 0.05, L[27] - 0.02)
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
    0: [['מספר אחת!'], ['אני ראשון!']],
    1: [['מכתב מביטוח לאומי'], ['מחכה לי בדואר.']],
    2: [['התורים נפתחים ב-10:30.'], ['עוד...'], ['רגע...']],
    3: [['עכשיו!'], ['ראשון בכל הרחוב!']],
    27: [['שרית?!'], ['גם פה?']],
    4: [['מספר אחת?'], ['כל הכבוד, מותק.']],
    5: [['מספר שתיים, בבקשה.']],
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

CHK1 = at(2, 2) + 0.05                    # "רגע..." → 10:30:00, the button lights up ✓ נפתח
TAP = L[3] + 0.12                         # "עכשיו!" → the paw taps
CHK2 = at(3, 1) + 0.10                    # "ראשון בכל הרחוב!" → ticket "1" ✓ מספר 1
CHK3 = L[27] + 0.05                       # inside the branch ✓ בסניף (gold)
BREAK = L[5]                              # 10:31:00: the board flips 1 → 2
REVEAL = L[5] + 0.06                      # snap onto the board + the clock

SUB_TIMES = []
for i0, s0 in OCC:
    for k, c in enumerate(SUBS[i0]):
        a = s0 + max(0.0, CS[i0][k] - 0.05)
        b = s0 + (CS[i0][k + 1] - 0.05 if k + 1 < len(SUBS[i0]) else D[i0] + 0.2)
        if s0 == 0.0: b = min(b, COLD_END)
        else: b = min(b, NEXT[i0] - 0.03)
        SUB_TIMES.append((a, b, c, i0))

C = lambda i: L[i] - 0.08
SHOTS = [('street', 0.0, COLD_END), ('rewind', COLD_END, T0), ('street', T0, C(2)), ('phone', C(2), C(0)),
         ('street', C(0), RUNW[0]), ('run', RUNW[0], RUNW[1]), ('two', RUNW[1], BREAK), ('reveal', BREAK, FREEZE - 0.02),
         ('frozen', FREEZE - 0.02, DUR + 1)]

TOPCAPS = [(0.0, C(2), ['איך תופסים', 'תור בדואר?'], 96, 250, WHITE)]   # hook F16 (ep30 was F10), keyword דואר, from frame 1

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

# ------------------------------------------------------------------ the clock (the plant): story time in seconds since midnight
OPEN = 10 * 3600 + 30 * 60
def clock_secs(t):
    if t < COLD_END:                       # the cold open = the replay moment of L00
        return clock_secs(L[0] + t)
    if t < T0:                             # rewind: spins back
        u = (t - COLD_END) / (T0 - COLD_END)
        return int(lerp(OPEN + 5, OPEN - 8, u))
    if t < CHK1:                           # counting down to 10:30:00 (1.6 s of story per second)
        return OPEN - math.ceil((CHK1 - t) * 1.6)
    if t < RUNW[0]:
        return OPEN + int(t - CHK1)
    if t < RUNW[1]:                        # the dash: time flies
        u = (t - RUNW[0]) / (RUNW[1] - RUNW[0])
        return int(lerp(clock_secs(RUNW[0] - 1e-3), OPEN + 41, u))
    if t < HOLD[0]:                        # inside: 10:30:41 → 10:30:57
        u = (t - RUNW[1]) / (HOLD[0] - RUNW[1])
        return OPEN + 41 + int(16 * u)
    if t < BREAK:                          # the hold: :58, :59 in real time
        return OPEN + 58 + int((t - HOLD[0]) / (BREAK - HOLD[0]) * 2)
    return OPEN + 60

def clock_text(t):
    s = clock_secs(t)
    return f'{s // 3600:02d}:{(s // 60) % 60:02d}:{s % 60:02d}'

def led_clock(img, c, t, s=1.0):
    """red LED seconds clock (world units)"""
    d = ImageDraw.Draw(img)
    w_, h_ = 330 * s, 104 * s
    d.rounded_rectangle([S(c[0] - w_ / 2 + 6), S(c[1] - h_ / 2 + 8), S(c[0] + w_ / 2 + 6), S(c[1] + h_ / 2 + 8)], radius=S(14 * s), fill=(0, 0, 0, 70))
    d.rounded_rectangle([S(c[0] - w_ / 2), S(c[1] - h_ / 2), S(c[0] + w_ / 2), S(c[1] + h_ / 2)], radius=S(14 * s),
                        fill=(26, 10, 12), outline=(70, 70, 76), width=iw(6))
    hot = t >= BREAK
    col = (255, 60, 50) if not hot or int(t * 6) % 2 == 0 else (255, 170, 140)
    d.text((S(c[0]), S(c[1] + 4 * s)), clock_text(t), font=font(S(70 * s), 900), fill=col, anchor='mm')

def rule_sign(sc=1.0):
    """the small grey rule (the plant): post-office paper"""
    w, h = 300, 92
    lay = Image.new('RGBA', (S(w + 8), S(h + 8)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([S(4), S(4), S(w + 4), S(h + 4)], fill=(250, 250, 244), outline=(150, 150, 150), width=iw(3))
    d.text((S(4 + w / 2), S(34)), 'מגיעים לחלון תוך', font=font(S(26), 800), fill=(110, 112, 122), anchor='mm')
    d.text((S(4 + w / 2), S(70)), '60 שנ׳ מהקריאה', font=font(S(26), 800), fill=(110, 112, 122), anchor='mm')
    return lay

# ------------------------------------------------------------------ props
def slip_layer():
    """the post-office pickup slip: "דבר דואר ממתין לך · ביטוח לאומי" """
    w, h = 340, 210
    lay = Image.new('RGBA', (S(w + 16), S(h + 16)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    o = 8; x1 = o + w; y1 = o + h
    d.rectangle([S(o), S(o), S(x1), S(y1)], fill=(255, 238, 150), outline=(150, 120, 30), width=iw(4))
    d.rectangle([S(o), S(o), S(x1), S(o + 40)], fill=POSTRED)
    d.text((S(x1 - 16), S(o + 21)), 'הודעה מהדואר', font=font(S(26), 900), fill=WHITE, anchor='rm')
    d.text((S(x1 - 18), S(o + 82)), 'דבר דואר', font=font(S(42), 900), fill=(40, 30, 20), anchor='rm')
    d.text((S(x1 - 18), S(o + 128)), 'ממתין לך', font=font(S(34), 900), fill=(40, 30, 20), anchor='rm')
    d.rounded_rectangle([S(o + 16), S(o + 158), S(o + 196), S(o + 196)], radius=S(10), fill=(24, 92, 170))
    d.text((S(o + 106), S(o + 177)), 'ביטוח לאומי', font=font(S(24), 900), fill=WHITE, anchor='mm')
    return lay

PW, PH = 400, 700
_PH = {}
def phone_layer(state):
    """queue app. state: 'wait' (grey, opens 10:30) | 'open' (green) | 'ticket' (number 1) | 'skip' (number 1, red X)"""
    if state in _PH: return _PH[state]
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(242, 244, 248))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.rectangle([S(14), S(70), S(PW - 14), S(150)], fill=POSTRED)
    pd.text((S(PW / 2), S(111)), 'זימון תור · דואר', font=font(S(38), 900), fill=WHITE, anchor='mm')
    if state in ('wait', 'open'):
        pd.text((S(PW / 2), S(220)), 'סניף הדואר', font=font(S(40), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(274)), 'חלון 3', font=font(S(34), 800), fill=(90, 96, 110), anchor='mm')
        col = GREEN if state == 'open' else (190, 194, 204)
        pd.rounded_rectangle([S(40), S(380), S(PW - 40), S(490)], radius=S(55), fill=col, outline=(30, 90, 40) if state == 'open' else (150, 154, 164), width=iw(5))
        pd.text((S(PW / 2), S(435)), 'קבע תור' if state == 'open' else 'נפתח ב-10:30', font=font(S(40), 900), fill=WHITE, anchor='mm')
    else:
        pd.text((S(PW / 2), S(206)), 'המספר שלך', font=font(S(38), 900), fill=(90, 96, 110), anchor='mm')
        pd.text((S(PW / 2), S(370)), '1', font=font(S(230), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(520)), 'חלון 3', font=font(S(34), 800), fill=(90, 96, 110), anchor='mm')
        pd.text((S(PW / 2), S(604)), 'מגיעים תוך 60 שנ׳ מהקריאה', font=font(S(22), 700), fill=(150, 154, 164), anchor='mm')   # the plant
        if state == 'skip':
            line(pd, [(110, 250), (290, 480)], RED, 22); line(pd, [(290, 250), (110, 480)], RED, 22)
    _PH[state] = lay
    return lay

def phone_state(t):
    if t >= BREAK + 0.15: return 'skip'
    if t >= CHK2: return 'ticket'
    if t >= CHK1: return 'open'
    return 'wait'

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    m.paste_center(img, lay, S(c[0]), S(c[1]))

def burst(img, c, u, col=(255, 236, 120), r0=150, n=10, dur=0.4):
    if not (0 <= u < dur): return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(n):
        a_ = math.radians(k * 360 / n + 10); ra, rb = r0 + 60 * u, r0 + 80 + 200 * u
        line(od, [(c[0] + ra * math.cos(a_), c[1] + ra * math.sin(a_)), (c[0] + rb * math.cos(a_), c[1] + rb * math.sin(a_))], col + (int(230 * (1 - u / dur)),), 10)
    img.alpha_composite(ov)

def num_chip(img, c, txt, u, sc=1.0):
    """a crowd cat's own (worse) number popping over its head"""
    if u < 0: return
    k = 1.5 - 0.5 * ease_out(clamp(u / 0.14))
    d = ImageDraw.Draw(img)
    w_, h_ = (60 + 30 * len(txt)) * sc * k, 64 * sc * k
    d.rounded_rectangle([S(c[0] - w_ / 2), S(c[1] - h_ / 2), S(c[0] + w_ / 2), S(c[1] + h_ / 2)], radius=S(h_ / 2), fill=(250, 250, 250), outline=(20, 20, 24), width=iw(4))
    d.text((S(c[0]), S(c[1] + 2)), txt, font=font(S(40 * sc * k), 900), fill=INK, anchor='mm')

# ------------------------------------------------------------------ the street in front of the post office
def build_street_bg():
    w, h = W * K, H * K
    yy = np.linspace(0, 1, h)[:, None, None]
    sky = np.array((150, 206, 246), float)[None, None, :] * (1 - yy) + np.array((214, 238, 252), float)[None, None, :] * yy
    img = Image.fromarray(np.clip(np.repeat(sky, w, axis=1), 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    d = ImageDraw.Draw(img)
    d.rectangle([S(0), S(420), S(1080), S(1290)], fill=(238, 226, 200))                 # stone facade
    for y in range(470, 1290, 64): line(d, [(0, y), (1080, y)], (222, 208, 178), 3)
    d.rounded_rectangle([S(50), S(540), S(300), S(610)], radius=S(14), fill=POSTRED, outline=(120, 16, 20), width=iw(5))
    d.text((S(175), S(575)), 'סניף דואר', font=font(S(40), 900), fill=WHITE, anchor='mm')
    # the glass door, the branch board visible inside
    d.rectangle([S(390), S(700), S(690), S(1290)], fill=(120, 150, 172), outline=(70, 74, 84), width=iw(8))
    d.line([(S(540), S(700)), (S(540), S(1290))], fill=(70, 74, 84), width=iw(6))
    d.rounded_rectangle([S(420), S(730), S(660), S(850)], radius=S(10), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(4))
    d.text((S(610), S(774)), 'חלון', font=font(S(26), 800), fill=E3.AMBER, anchor='mm')
    d.text((S(610), S(814)), '3', font=font(S(30), 900), fill=E3.AMBER, anchor='mm')
    # two windows
    for x0 in (60, 790):
        d.rectangle([S(x0), S(640), S(x0 + 230), S(1000)], fill=(176, 204, 224), outline=(120, 110, 96), width=iw(7))
        poly(d, [(x0 + 30, 1000), (x0 + 90, 1000), (x0 + 190, 640), (x0 + 130, 640)], fill=(206, 226, 240))
    # sidewalk
    d.rectangle([S(0), S(1290), S(1080), S(1920)], fill=(196, 196, 200))
    for x in range(-200, 1200, 180): line(d, [(x, 1290), (x - 120, 1920)], (176, 176, 182), 4)
    return img

# the crowd outside: everybody waiting for 10:30 with a phone
STREET_CROWD = [('c0', 110, 800, 0.50, 0.0, '214'), ('h0', 290, 840, 0.40, 1.1, '3'), ('c2', 800, 790, 0.44, 2.0, '57'),
                ('c3', 980, 820, 0.50, 0.6, '2'), ('h1', 190, 1000, 0.55, 1.7, '96'), ('c4', 900, 1010, 0.60, 2.6, '12')]
HX, HY, F = 540, 1060, 1.38

def street_mood(t):
    if C(0) <= t < RUNW[0] or t < COLD_END: return 1 if t - (C(0) if t >= C(0) else 0) < 0.5 else 0   # shocked, then annoyed
    return 2                                                                                          # bored, staring at phones

def cat_street(t, i, mode):
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    rot, dy, dx = 0.0, 0.0, 0.0
    v = cat_v(t)
    li = speaking(t)
    if li == 0 or t < COLD_END:   # "מספר אחת! אני ראשון!" — wide-eyed disbelief, sweat, shouting (R5: never calm)
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-24, sweat=1.0, blush=0.6, look=(0, -4))
        dy = -16 * v - 12 * abs(math.sin(t * 8)); rot = 5 * math.sin(t * 9)
    elif mode == 'run':
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-20, sweat=0.6, look=(-14, 0))
        u = (t - RUNW[0]) / (RUNW[1] - RUNW[0])
        dx = -900 * ease_in(u); rot = 14; dy = -20 * abs(math.sin(t * 20))
    else:                          # "מכתב מביטוח לאומי מחכה לי בדואר." — the slip waved at us, the door still closed
        st.update(lid=0.0, pupil='big', brow='annoyed', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-12, sweat=0.8, look=(-6, 0))
        dy = -10 * v; rot = 3 * math.sin(t * 6)
    return st, rot, dy, dx

def scene_street(t, i, mode=None):
    mode = mode or shot(t)[0]
    img = STREET.copy()
    led_clock(img, (540, 632), t, 1.05)
    paste_rot(img, RULE, (850, 632), 3, 0.9)
    mood = street_mood(t)
    for name, x, y, sc, ph, num in STREET_CROWD:
        hop = -14 * abs(math.sin(t * 6 + ph)) if mood == 1 else 0
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + hop + 6 * math.sin(t * 4 + ph), sc, flip=x > 540)
        d = ImageDraw.Draw(img)   # each one holds a phone up
        px = x + (60 if x < 540 else -60) * sc * 1.6; py = y + 150 * sc * 1.4
        d.rounded_rectangle([S(px - 26 * sc * 1.6), S(py - 44 * sc * 1.6), S(px + 26 * sc * 1.6), S(py + 44 * sc * 1.6)], radius=S(8), fill=(20, 20, 24))
        d.rounded_rectangle([S(px - 20 * sc * 1.6), S(py - 36 * sc * 1.6), S(px + 20 * sc * 1.6), S(py + 36 * sc * 1.6)], radius=S(6), fill=(200, 230, 255))
        if t >= CHK2 or t < COLD_END:   # their numbers (the stakes: 2, 3, 214 …)
            u = (t - CHK2) if t >= CHK2 else (t + 0.3 - 0.08 * STREET_CROWD.index((name, x, y, sc, ph, num)))
            num_chip(img, (x, y - 140 * sc * 1.5), num, u, 0.9)
    d = ImageDraw.Draw(img)
    st, rot, dy, dx = cat_street(t, i, mode)
    hx = HX + dx
    E(d, hx, 1710 + 0.5 * dy, 430, 460, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1770 + 0.5 * dy, 200, 310, fill=CREAM)
    replay = (li_ := speaking(t)) == 0 or t < COLD_END or (C(0) <= t < RUNW[0])
    if replay or mode == 'run':
        # right paw (viewer's left): the phone with ticket "1" thrust up
        pc = (290, 1060 + 0.4 * dy + 10 * math.sin(t * 14))
        capsule(d, (hx - 230, 1490 + 0.5 * dy), (pc[0] + 20, pc[1] + 250), 110, FUR, OUT, 4)
        E12.paste_head(img, st, i, hx, HY + dy, F, rot)
        paste_rot(img, phone_layer('ticket'), pc, -8 + 3 * math.sin(t * 10), 0.78)
        d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 20, pc[1] + 250), 10, 0.9)
    else:
        # the slip waved at the camera
        pc = (300, 1160 + 0.5 * dy + 8 * math.sin(t * 11))
        rp = (pc[0] - 110, pc[1] + 100)
        capsule(d, (hx - 230, 1490 + 0.5 * dy), rp, 110, FUR, OUT, 4)
        E12.paste_head(img, st, i, hx, HY + dy, F, rot)
        paste_rot(img, SLIP, pc, -10 + 5 * math.sin(t * 9), 1.0)
        d = ImageDraw.Draw(img); E12.big_paw(d, rp, 10, 0.9)
    # left paw (viewer's right): the live queue ticket (§O4)
    lp = (hx + 185, 1400 + 8 * math.sin(t * 2.0) + 0.5 * dy)
    capsule(d, (hx + 230, 1490 + 0.5 * dy), lp, 110, FUR, OUT, 4)
    tk = xform([(-48, -78), (48, -78), (48, 78), (-48, 78)], lp[0] + 10, lp[1] - 120, 8)
    poly(d, tk, fill=(252, 250, 242), outline=(150, 150, 140), width=3)
    c_ = xform([(0, -20)], lp[0] + 10, lp[1] - 120, 8)[0]
    d.text((S(c_[0]), S(c_[1])), str(QUEUE), font=font(S(40), 900), fill=INK, anchor='mm')
    E12.big_paw(d, lp, -10, 0.9)
    if mode == 'run' or replay:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        a = 200 if mode == 'run' else 0
        if mode == 'run':
            for k in range(8):
                y = 650 + k * 130; x0 = hx + 380 + 60 * (k % 2)
                line(od, [(x0, y), (x0 + 380, y)], (255, 255, 255, a), 12)
        img.alpha_composite(ov)
    if t < COLD_END or (L[0] <= t < L[0] + 0.5):
        burst(img, (300, 1000), t if t < COLD_END else t - L[0], (255, 236, 120), 230, 12, 0.45)
    return img

# ------------------------------------------------------------------ phone close: his face + the phone beside it
HXP, HYP, FP = 700, 980, 1.62
def scene_phone(t, i):
    img = STREET_BLUR.copy()
    led_clock(img, (300, 560), t, 1.15)
    d = ImageDraw.Draw(img)
    v = cat_v(t)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    rot, dy = 0.0, 0.0
    if t < TAP - 0.12:   # "התורים נפתחים ב-10:30. עוד... רגע..." — tense, sweating, eyes on the phone
        st.update(lid=0.0, pupil='big' if t < at(2, 1) else 'tiny', brow='annoyed', mouth=cat_mouth(t, rest='flat', loud='w'),
                  ear_dy=-8 - 10 * clamp((t - L[2]) / 3), sweat=1.0, look=(-22, 10), blush=0.0)
        rot = -4 + (3 * math.sin(t * 40) if t >= at(2, 2) else 0)
        if t >= CHK1: st.update(pupil='big', brow='up', ear_dy=-26, look=(-22, 4))
    elif t < CHK2:       # "עכשיו!" — tap
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-24, sweat=0.8, look=(-22, 8))
        dy = -14 * v
    else:                # "ראשון בכל הרחוב!" — ticket "1": he lights up
        u = t - CHK2
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-28, blush=1.0, look=(-10, -6))
        dy = -36 * abs(math.sin(u * 8)) * math.exp(-u * 1.6)
    # body + the arm holding the phone
    E(d, HXP, 1760, 400, 430, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1810, 180, 290, fill=CREAM)
    pc = (300, 1110 + (0 if t < TAP else 6 * math.sin(t * 12)))
    capsule(d, (HXP - 240, 1560), (pc[0] + 40, pc[1] + 290), 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP, HYP + dy - 8 * v, FP, rot)
    sc = 1.04 if t < CHK2 else 1.04 + 0.1 * math.exp(-(t - CHK2) * 8)
    paste_rot(img, phone_layer(phone_state(t)), pc, -6, sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (pc[0] + 40, pc[1] + 290), 8, 0.95)
    # the tapping paw (the other one) comes in on "עכשיו!"
    if TAP - 0.15 <= t < CHK2 + 0.25:
        u = t - (TAP - 0.15)
        k = clamp(u / 0.15)
        bob = 50 * max(0.0, 1 - abs(u - 0.15) / 0.08)
        pp = (lerp(520, 330, ease_out(k)), lerp(1500, 1190, ease_out(k)) + bob)
        capsule(d, (HXP + 160, 1600), pp, 100, FUR, OUT, 4)
        E12.big_paw(d, pp, -160, 0.75)
        if u >= 0.15: burst(img, (300, 1150), u - 0.15, (255, 255, 255), 90, 8, 0.25)
    if t >= CHK1: burst(img, (300, 1150), t - CHK1, (120, 230, 140), 170, 10, 0.35)
    if t >= CHK2: burst(img, (300, 1080), t - CHK2, (255, 220, 90), 220, 12, 0.5)
    return img

# ------------------------------------------------------------------ inside: Sharit at window 3 (left), his face (right)
T_HEAD = (225, 930); TS = 1.40
HX2, HY2, F2 = 790, 990, 1.45
BOARD2 = (230, 470)
def board_num(t): return '2' if t >= BREAK else '1'

def scene_two(t, i, mode='two'):
    img = SH_BG.copy(); d = ImageDraw.Draw(img)
    # the branch board above window 3 + the clock + the rule, sharp over the blurred office
    bx, by = BOARD2
    d.rounded_rectangle([S(bx - 190 + 8), S(by - 92 + 10), S(bx + 190 + 8), S(by + 92 + 10)], radius=S(18), fill=(0, 0, 0, 70))
    d.rounded_rectangle([S(bx - 190), S(by - 92), S(bx + 190), S(by + 92)], radius=S(18), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(6))
    d.line([(S(bx + 70), S(by - 72)), (S(bx + 70), S(by + 72))], fill=(60, 60, 70), width=iw(3))
    d.text((S(bx + 130), S(by - 26)), 'חלון', font=font(S(34), 800), fill=E3.AMBER, anchor='mm')
    d.text((S(bx + 130), S(by + 36)), '3', font=font(S(64), 900), fill=E3.AMBER, anchor='mm')
    flip = 0 <= t - BREAK < 0.3
    on = (int((t - BREAK) / 0.07) % 2 == 0) if flip else (int(t * 3) % 3 != 0 if t < BREAK else True)   # "1" blinks: called
    E3.led_text(img, board_num(t), bx - 60, by + 4, 132, on)
    led_clock(img, (620, 470), t, 1.0)
    paste_rot(img, RULE, (900, 470), 3, 0.74)
    # Sharit
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.55, red=0.8, look=(18, 6))
    st_s['mouth'] = 'talk' if sh_v(t) > 0.12 else 'grin'
    if t < L[4] - 0.05:                    # "שרית?! גם פה?" — munching
        st_s.update(snack=True, lid=0.6, look=(18, 2))
        if sh_v(t) <= 0.12: st_s['mouth'] = 'munch'
    elif t < BREAK:                        # "מספר אחת? כל הכבוד, מותק." — warm, impressed
        st_s.update(blush=0.8, lid=0.42, look=(20, 0), hand_r=(560, 600))
    else:                                  # 10:31:00 — she looks past him, flat
        st_s.update(lid=0.66, red=1.0, look=(-22, 6), blush=0.2, rot=-4)
    Ls = SH.draw(st_s, i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    # the cat
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    rot, dy = 0.0, 0.0
    v = cat_v(t)
    if t < L[4] - 0.05:                    # double take
        u = t - L[27]
        st.update(lid=0.0, pupil='tiny', brow='up', ear_dy=-24, mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0, look=(-16, 0))
        rot = 6 * math.sin(u * 10) * math.exp(-u * 2)
        dy = -30 * math.exp(-u * 5)
    elif t < HOLD[0]:                      # she congratulates him: he glows
        u = t - L[4]
        st.update(lid=0.0, pupil='big', brow='up', ear_dy=-20 - 6 * clamp(u / 1.5), mouth='smile', look=(-16, -2), blush=0.6 + 0.4 * clamp(u / 1.5))
        dy = -8 * abs(math.sin(t * 5))
    elif t < BREAK:                        # THE PEAK: eyes closed, savouring it
        st.update(eye_mode='closed', mouth='smile', ear_dy=-28, blush=1.0, look=(0, -8))
        dy = -14
    else:                                  # frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-20 * math.exp(-u * 4), look=(-20, -10),
                  twitch=(0.3 < u < 0.9 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.3), blush=0.0)
        dy = -14
    E(d, HX2, 1750, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1800, 170, 280, fill=CREAM)
    # his phone with ticket "1" held up by his cheek (from her line on)
    show_ph = t >= L[4] - 0.05
    if show_ph:
        pc = (lerp(600, 570, clamp((t - L[4]) / 0.3)), lerp(1500, 1235, ease_out(clamp((t - L[4]) / 0.3))) + (4 * math.sin(t * 6) if t < HOLD[0] else 0) - 110 * ease_out(clamp((t - BREAK - 0.1) / 0.2)))
        capsule(d, (HX2 - 200, 1640), (pc[0] + 30, pc[1] + 170), 100, FUR, OUT, 4)
    E12.paste_head(img, st, i, HX2, HY2 + dy - 10 * v, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1600), S(1100), S(1720)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    if show_ph:
        paste_rot(img, phone_layer(phone_state(t)), pc, 4, 0.52)
        d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 30, pc[1] + 170), -10, 0.7)
    # number 2 slips in front of the window
    if t >= BREAK:
        u = t - BREAK
        x2 = lerp(-260, 150, ease_out(clamp(u / 0.35)))
        E13.paste_sprite(img, 'c1', 2, x2, 1330, 0.72)
        num_chip(img, (x2 + 10, 1110), '2', u - 0.1, 1.0)
    if t >= CHK3 and t < L[4]:
        burst(img, (HX2, 900), t - CHK3, (255, 236, 120), 280, 12, 0.4)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('נפתח', 790, CHK1), ('מספר 1', 540, CHK2), ('בסניף', 290, CHK3)]
def chips(frame, t):
    if t < C(2): return                     # the hook owns the top band until the phone shot
    gold = t >= CHK3
    drained = t >= BREAK + 0.2
    if t >= BREAK + 0.7: return
    d = ImageDraw.Draw(frame)
    y = 330
    for lab, cx, tk in CHIPS:
        ok = t >= tk and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if drained and t - BREAK < 0.5: sc = 1.0 + 0.15 * math.exp(-(t - BREAK - 0.2) * 10)
        w, h = 220 * sc, 70 * sc
        jx = random.Random(int(t * FPS) + cx).uniform(-8, 8) if (drained and t - BREAK < 0.5) else 0
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
STREET = STREET_BLUR = SH_BG = SLIP = RULE = PILL_EP = PILL_Q = None
def init_all():
    global STREET, STREET_BLUR, SH_BG, SLIP, RULE, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    E13.build_crowd()
    STREET = build_street_bg()
    STREET_BLUR = STREET.filter(ImageFilter.GaussianBlur(S(4)))
    SH_BG = E3.build_office_bg().filter(ImageFilter.GaussianBlur(S(3)))
    SLIP = slip_layer(); RULE = rule_sign()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'street':
        if t < COLD_END or C(0) <= t:
            z = (COLDZ or 1.06) + 0.04 * pu; cy = 980 if not COLDZ else 940
            if t < 0.3: z = (COLDZ or 1.06) + 0.22 - 0.22 * ease_out(t / 0.3)     # frame 0: snap pull-back, already moving
            if C(0) <= t and pu < 0.3: z = max(z, 1.10 + 0.12 * (1 - ease_out(pu / 0.3)))
        else:
            z = 1.04 + 0.03 * pu; cy = 960
    elif name == 'rewind':
        z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'phone':
        z = (PHZ or 1.05) + 0.03 * pu; cy = 1000; cx = 520
        if t >= CHK2: z = z + 0.05 * math.exp(-(t - CHK2) * 6)
    elif name == 'run':
        u = pu / (b - a); z, cx = 1.04, 540 - 120 * u
    elif name == 'two':
        z = 1.0 + 0.02 * pu
        if t >= HOLD[0]: z = 1.02 + 0.10 * ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0]))); cx, cy = lerp(540, 600, ease_io(clamp((t - HOLD[0]) / 0.5))), 980
    elif name == 'reveal':
        e = ease_out(clamp((t - REVEAL) / 0.14))
        z, cx, cy = lerp(1.12, 1.30, e), lerp(600, 430, e), lerp(980, 860, e)                        # snap onto board "2" + the clock
    elif name == 'frozen':
        z, cx, cy = 1.28 + 0.03 * pu, 760, 920                                                         # his frozen face
    if name not in ('rewind', 'reveal', 'frozen', 'run') and not (name == 'street' and t < 0.3) and pu < 0.2:
        z = z + 0.07 * (1 - ease_out(pu / 0.2))   # snap-zoom on every cut
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name in ('street', 'run'): img = scene_street(t, i, name)
    elif name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_street(lerp(C(2) - 0.2, T0 + 0.3, ease_in(u)), i, 'street')
    elif name == 'phone': img = scene_phone(t, i)
    else: img = scene_two(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 18 * math.exp(-t * 5)
    if name == 'phone' and t >= CHK2 and t - CHK2 < 0.4: shake = 10 * math.exp(-(t - CHK2) * 6)
    if name == 'reveal' and t - REVEAL < 0.3: shake = 10 * math.exp(-(t - REVEAL) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if name == 'two' and t >= HOLD[0]:     # the hush: dims a touch, heartbeat pulse
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.24 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(60 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CHK2, BREAK):
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
    if name in ('street', 'run', 'frozen'):   # serial markers (§O3); the ticket flickers in the last second
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(32)
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
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def tick(t0, g=0.10): add(sfx, m.highpass(nz(0.025), 2500) * np.exp(-tt_(0.025) * 160), t0, g)
    def groan(t0, ln=0.9, g=0.12):
        tt = tt_(ln); fr = 220 - 70 * tt / ln
        sig = m.lowpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr) / SR)) * 0.5 + 0.5 * nz(ln), 900) * np.sin(np.pi * tt / ln)
        add(sfx, sig, t0, g)
    def ding(t0, g=0.22):
        add(sfx, m.tone(880.0, 0.9, harm=((1, 1), (2, 0.25), (3, 0.1)), decay=3), t0, g)
        add(sfx, m.tone(698.5, 1.1, harm=((1, 1), (2, 0.25)), decay=2.6), t0 + 0.22, g)
    # cold open: impact + crowd gasp
    add(sfx, thud(1.0), 0.0); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), 0.0, 0.4)
    groan(0.35, 0.9, 0.10)
    # rewind tape
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    # street traffic + murmur (room tone) everywhere except the hush
    st_len = HOLD[0]; street = m.lowpass(nz(st_len), 500) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * tt_(st_len)))
    add(sfx, street, 0.0, 0.03)
    mur2 = m.bandpass(nz(DUR - BREAK + 0.3), 200, 1400); add(sfx, mur2, BREAK, 0.02)
    # the clock ticks: every second change on screen
    prev = None
    for k in range(int(DUR * FPS)):
        tk_ = k / FPS
        if RW[0] <= tk_ < RW[1]: prev = None; continue
        s = clock_secs(tk_)
        if prev is not None and s != prev and not (RUNW[0] <= tk_ < RUNW[1]):
            tick(tk_, 0.12 if tk_ >= HOLD[0] - 0.1 else (0.09 if L[2] <= tk_ < CHK1 + 0.1 else 0.05))
        prev = s
    # cuts
    for name, a, b in SHOTS[2:]:
        if name not in ('reveal', 'frozen'): whoosh(a)
    # ✓1 the button lights up (10:30:00)
    add(sfx, m.tone(1318.5, 0.4, harm=((1, 1), (2, 0.2)), decay=7), CHK1, 0.12); check(CHK1 + 0.04, 0.15)
    # the tap + ✓2 ticket "1"
    add(sfx, m.highpass(nz(0.03), 2000) * np.exp(-tt_(0.03) * 100), TAP, 0.35)
    add(sfx, thud(0.6), CHK2); check(CHK2 + 0.04, 0.18)
    groan(L[0] + 0.3, 1.0, 0.14)          # the street groans at their own numbers
    # the dash: skid + whoosh + door bell
    add(sfx, m.bandpass(nz(0.4), 1500, 7000) * np.exp(-tt_(0.4) * 6), RUNW[0], 0.14)
    ding(RUNW[1] - 0.05, 0.10)
    # ✓3 gold, inside
    check(CHK3 + 0.05, 0.18, True)
    # peak: short "aww", then hush + heartbeat
    for k, f in enumerate((523.3, 659.3, 784.0)): add(sfx, m.tone(f, 0.9, harm=((1, 1), (2, 0.2)), decay=3), L[4] + at(4, 1) - L[4] + 0.2 + k * 0.03, 0.04)
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.05 + 0.28, 0.5)
    # break: 10:31:00 — the board's call ding, the flip clack, one low "dun"
    ding(BREAK, 0.24)
    add(sfx, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 70), BREAK + 0.02, 0.5)
    add(sfx, thud(0.8), REVEAL)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), REVEAL + 0.02, 0.30)
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
        print('CHK', round(CHK1, 2), round(TAP, 2), round(CHK2, 2), round(CHK3, 2), 'RUNW', [round(x, 2) for x in RUNW], 'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK, 2), 'FREEZE', round(FREEZE, 2))
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        for tm in (0, 1, 2.5, 4, 5, 6, 6.8, 7.2, 8, 9, 10, 12.5, 13, 15, 16.5, 17, 17.5, 18): print(tm, clock_text(tm))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames):
            sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep32_contact.png')); print('ok'); return
    if mode == 'frame':
        init_all(); tm = float(sys.argv[2])
        draw_frame(min(NF - 1, int(round(tm * FPS)))).save(os.path.join(OUTDIR, sys.argv[3] if len(sys.argv) > 3 else 'ep32_frame.png')); return
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
