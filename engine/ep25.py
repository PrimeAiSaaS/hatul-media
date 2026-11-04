#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 25: הבנק שלי: סגירת חשבון (season 5 "החשבון" finale, VOICED, built 4.11 under §P; experiment
voiced_length arm control_30). Voices = voice bank 2500–2510 (Benji = cat, Delia = Sharit), prepared by voice/ep25_prep.py
(L07, the coin counting, trimmed to 3.5 s: "ארבעים ושמונה... חמישים. יפה, מותק!").
Want: close his account at הבנק שלי, for good. Plant: Sharit's SECOND rubber stamp, its label "חשבון חדש", standing on the
counter beside her closing stamp: in the cold open (0–2.4 s), at L01, beside her hand at L08. Never pointed at.
Climb: closing form signed ✓ (טופס) → the closing fee paid in coins from his jar (his card is frozen, ep21) ✓ (עמלה) →
STAMP "החשבון נסגר" ✓✓✓ gold (נסגר), confetti, the queue applauds. Peak: at the glass door, sunlight, paw on the handle,
"חופשי. סוף סוף... חופשי." eyes closed, hush + heartbeat. Break (full_circle): a second THUNK behind him; he freezes;
Sharit: "מזל טוב, מותק." (the "חשבון חדש" stamp in her hand) → "חשבון חדש." — the red imprint "חשבון חדש נפתח אוטומטית"
slaps onto the closing form in his paw. Frozen face, whip into the cold open (loop).
No music (voiced rule): SFX + branch murmur only. Serial pills "פרק 25" + live ticket (hud.stage_of, §O4).

  python3 ep25.py times
  python3 ep25.py test 0 0.3 1.2 2.6 3.2 4.5 ...
  python3 ep25.py render                                  -> out/ep25_close.mp4
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
VDIR = os.path.join(HERE, 'voice', 'ep25', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
NL = 11
D = [META[i]['dur'] for i in range(NL)]
YELLOW = (255, 221, 51); PINKSUB = (255, 182, 210); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 30, 44)
QUEUE = int(os.environ.get('QUEUE', '468'))
EP_LABEL = 'פרק 25'
OUTNAME = os.environ.get('OUTNAME', 'ep25_close')
LIMIT = float(os.environ.get('LIMIT', '0'))    # render only the first LIMIT seconds (predictor cuts)
NOSUB = os.environ.get('NOSUB', '0') == '1'     # cover frames: no subtitles
CROWDJ = os.environ.get('CROWDJ', '0') == '1'   # predictor probe: waiting customers' faces behind him in the jar two-shot
BIGO = os.environ.get('BIGO', '0') == '1'       # predictor probe: cold open tight on his shouting face, pull back to the two-shot after the slam
RECAPZ = os.environ.get('RECAPZ', '0') == '1'   # predictor probe: L02 recap framed tight on his face (icons around it)
TWO1 = os.environ.get('TWO1', '0') == '1'       # predictor probe: L01 (Sharit's 'למה?') as a two-shot with his big face instead of Sharit alone
SPEAKER = {0: 'cat', 1: 'sh', 2: 'cat', 3: 'sh', 4: 'cat', 5: 'sh', 6: 'cat', 7: 'sh', 8: 'sh', 9: 'cat', 10: 'sh'}

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
    0: [['באתי לסגור את החשבון.'], ['סופית.']],
    1: [['אוי, חמוד... למה?'], ['טוב לך אצלנו.']],
    2: [['הקפאתם לי את החשבון,'], ['הקוד הלך לסבתא,'], ['והסוללה נגמרה לי', 'באמצע.'], ['סוגרים.']],
    3: [['טוב, מותק.'], ['טופס סגירה.']],
    4: [['חתמתי!']],
    5: [['עמלת סגירה:'], ['חמישים שקל, מותק.']],
    6: [['החשבון קפוא?'], ['אז הבאתי במטבעות!']],
    7: [['ארבעים ושמונה...'], ['חמישים.'], ['יפה, מותק!']],
    8: [['החשבון...'], ['נסגר!']],
    9: [['חופשי.'], ['סוף סוף... חופשי.']],
    10: [['מזל טוב, מותק.'], ['חשבון חדש.']],
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

CS = {i: chunk_starts(i) for i in range(NL)}

# ------------------------------------------------------------------ timeline (from the real line lengths)
COLD_END = round(D[6] + 0.15, 2)          # cold open = L06 "החשבון קפוא? אז הבאתי במטבעות!" (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.35)          # ◀◀ רגע קודם
T0 = RW[1]
OFF6 = max(0.0, CS[6][1] - 0.04)          # in context L06 plays from "אז הבאתי במטבעות!" (the full line already opened the episode)
L = [0.0] * NL
GAPS = {0: 0.10, 1: 0.10, 2: 0.12, 3: 0.08, 4: 0.12, 5: 0.10, 6: 0.30, 7: 0.10, 8: 0.20}
t_ = T0 + 0.05
for i in range(NL - 1):
    L[i] = t_
    t_ += (D[i] - (OFF6 if i == 6 else 0.0)) + GAPS.get(i, 0.0)
HOLD = (L[9] + D[9], L[9] + D[9] + 0.5)   # peak hold: hush + heartbeat
THUNK = HOLD[1]                           # the second THUNK behind him
L[10] = THUNK + 0.22
FREEZE = L[10] + D[10]
DUR = round(FREEZE + 0.45, 2)
NF = int(round(DUR * FPS))
OCC = [(6, 0.0, 0.0)] + [(i, L[i], OFF6 if i == 6 else 0.0) for i in range(NL)]   # (line, start, source offset)

def at(i, k): return L[i] + CS[i][k] - (OFF6 if i == 6 else 0.0)

SLAM_COLD = 0.10                          # the jar hits the counter (frame 0 = it is coming down)
SLAM2 = L[6] + 0.10
ICONS = [at(2, 0) + 0.15, at(2, 1), at(2, 2)]   # frozen card / grandma's phone / battery 1%
SLIDE = at(3, 1) - 0.05                   # "טופס סגירה." → the form slides over
CHK1 = at(4, 0) + 0.35                    # "חתמתי!" ✓ טופס
FEE = at(5, 1)                            # "חמישים שקל" → the 50 ₪ card pops
FF = (L[7], at(7, 1))                     # x16 coin counting
CHK2 = at(7, 2)                           # "יפה, מותק!" ✓ עמלה
CHK3 = at(8, 1) - 0.05                    # "נסגר!" THUNK ✓ נסגר, gold
REVEAL = at(10, 1) - 0.05                 # "חשבון חדש." → the imprint slaps onto his form

SUB_TIMES = []
for i0, s0, off in OCC:
    starts = [c - off for c in CS[i0]]
    for k, c in enumerate(SUBS[i0]):
        if starts[k] < -0.1: continue
        a = s0 + max(0.0, starts[k] - 0.05)
        b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(SUBS[i0]) else D[i0] - off + 0.2)
        if s0 == 0.0 and i0 == 6 and off == 0.0: b = min(b, COLD_END)
        elif i0 + 1 < NL and s0 > 0: b = min(b, L[i0 + 1] - 0.03)
        SUB_TIMES.append((a, b, c, i0))

C = lambda i: L[i] - 0.08
SHOTS = [('jar', 0.0, COLD_END), ('rewind', COLD_END, T0), ('march', T0, C(1)), ('sh', C(1), C(2)), ('recap', C(2), C(3)),
         ('two', C(3), C(5)), ('sh', C(5), C(6)), ('jar', C(6), C(7)), ('count', C(7), C(8)), ('sh', C(8), C(9)),
         ('door', C(9), THUNK + 0.30), ('sh', THUNK + 0.30, REVEAL), ('reveal', REVEAL, DUR + 1)]

HOOK = ['לסגור חשבון', 'בבנק שלי?']
TOPCAPS = [(0.0, C(1), HOOK, 96, 210, WHITE)]   # hook (F16), keyword from frame 1

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def talk(t, i):
    for li, s0, off in OCC:
        if li == i and s0 <= t < s0 + D[i] - off:
            env = META[i]['env']; k = int((t - s0 + off) * FPS)
            return env[k] if k < len(env) else 0.0
    return 0.0

def speaking(t):
    for li, s0, off in OCC:
        if s0 <= t < s0 + D[li] - off: return li
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

def slam_t(t): return SLAM_COLD if t < COLD_END else SLAM2

# ------------------------------------------------------------------ props
def rubber_stamp(label, col=(40, 44, 52)):
    """a standing rubber stamp: wooden knob, handle, rubber base, a label plate on the handle"""
    lay = Image.new('RGBA', (S(190), S(250)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    E(d, 95, 46, 40, 34, fill=(150, 96, 52), outline=(70, 40, 20), width=5)
    d.rounded_rectangle([S(78), S(70), S(112), S(130)], radius=S(6), fill=(150, 96, 52), outline=(70, 40, 20), width=iw(4))
    d.rounded_rectangle([S(14), S(126), S(176), S(208)], radius=S(10), fill=col, outline=(14, 14, 18), width=iw(4))
    d.rectangle([S(20), S(206), S(170), S(234)], fill=(196, 40, 52), outline=(14, 14, 18), width=iw(3))
    d.rounded_rectangle([S(24), S(140), S(166), S(194)], radius=S(6), fill=(252, 250, 240), outline=(120, 120, 110), width=iw(2))
    s = 30
    while d.textlength(label, font=font(S(s), 900)) > S(132) and s > 14: s -= 1
    d.text((S(95), S(168)), label, font=font(S(s), 900), fill=(30, 30, 40), anchor='mm')
    return lay

def stamp_imprint(text, col=RED, size=84, w_extra=80):
    f = font(S(size), 900)
    tw = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(text, font=f)
    w, h = int(tw + S(w_extra)), S(int(size * 1.66))
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(6), S(6), w - S(6), h - S(6)], radius=S(18), outline=col + (235,), width=iw(9))
    d.text((w / 2, h / 2), text, font=f, fill=col + (235,), anchor='mm')
    return lay

def form_layer(signed=0.0, closed=False, reopened=False):
    """the closing form: title, lines, signature line (signed 0..1 = the flourish drawn so far)"""
    FW, FH = 360, 470
    lay = Image.new('RGBA', (S(FW), S(FH)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(FW) - 1, S(FH) - 1], fill=(252, 252, 246), outline=(140, 140, 140), width=iw(3))
    d.rectangle([0, 0, S(FW), S(64)], fill=(28, 104, 226))
    d.text((S(FW / 2), S(34)), 'הבנק שלי', font=font(S(34), 900), fill=WHITE, anchor='mm')
    d.text((S(FW - 22), S(100)), 'טופס סגירת חשבון', font=font(S(32), 900), fill=INK, anchor='rm')
    for k in range(5): line(d, [(30, 150 + k * 40), (FW - 30 - 50 * (k % 2), 150 + k * 40)], (176, 182, 196), 5)
    line(d, [(40, 410), (220, 410)], (90, 90, 100), 3)
    d.text((S(FW - 26), S(406)), 'חתימה:', font=font(S(26), 800), fill=(90, 90, 100), anchor='rm')
    if signed > 0:
        pts = [(50 + 160 * u, 395 - 26 * math.sin(u * 13) - 10 * math.sin(u * 5)) for u in [k / 40 * signed for k in range(41)]]
        line(d, pts, (20, 40, 140), 5)
    return lay

def jar_layer(fill=1.0):
    lay = Image.new('RGBA', (S(260), S(330)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(20), S(60), S(240), S(320)], radius=S(40), fill=(214, 236, 246, 150), outline=(90, 120, 140), width=iw(6))
    top = 320 - 230 * fill
    rng = random.Random(3)
    for k in range(int(70 * fill)):
        x = rng.uniform(46, 214); y = rng.uniform(max(top, 90), 300)
        c = [(232, 184, 60), (200, 200, 206), (214, 150, 70)][k % 3]
        poly(d, epoly(x, y, 22, 9, rng.uniform(-30, 30)), fill=c, outline=(110, 80, 20), width=2)
    d.rounded_rectangle([S(40), S(20), S(220), S(66)], radius=S(10), fill=(200, 60, 50), outline=(110, 30, 20), width=iw(5))
    d.rounded_rectangle([S(70), S(150), S(190), S(214)], radius=S(8), fill=(252, 250, 240), outline=(140, 130, 110), width=iw(3))
    d.text((S(130), S(182)), 'קופה', font=font(S(36), 900), fill=(40, 40, 50), anchor='mm')
    return lay

def card_frozen():
    lay = Image.new('RGBA', (S(220), S(150)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(6), S(6), S(214), S(144)], radius=S(16), fill=(28, 104, 226), outline=(10, 30, 80), width=iw(4))
    d.rectangle([S(26), S(40), S(70), S(74)], fill=(232, 190, 80))
    d.text((S(196), S(118)), 'הבנק שלי', font=font(S(26), 900), fill=WHITE, anchor='rm')
    ov = Image.new('RGBA', lay.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle([S(6), S(6), S(214), S(144)], radius=S(16), fill=(220, 240, 255, 120))
    for k in range(6):   # snowflake
        a = math.radians(k * 60); line(od, [(150, 60), (150 + 34 * math.cos(a), 60 + 34 * math.sin(a))], (255, 255, 255, 255), 6)
    lay.alpha_composite(ov)
    return lay

def phone_gran():
    lay = Image.new('RGBA', (S(150), S(250)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(6), S(6), S(144), S(244)], radius=S(22), fill=(44, 44, 52), outline=(14, 14, 18), width=iw(4))
    d.rounded_rectangle([S(16), S(26), S(134), S(224)], radius=S(12), fill=(240, 246, 250))
    E(d, 75, 92, 32, 32, fill=(236, 184, 146), outline=(120, 70, 46), width=3)
    E(d, 75, 66, 34, 18, fill=(214, 214, 220))
    d.text((S(75), S(152)), 'סבתא', font=font(S(30), 900), fill=INK, anchor='mm')
    d.text((S(75), S(194)), '4821', font=font(S(30), 900), fill=(28, 104, 226), anchor='mm')
    return lay

def battery1():
    lay = Image.new('RGBA', (S(220), S(120)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(8), S(14), S(186), S(106)], radius=S(14), fill=(30, 30, 36), outline=(250, 250, 250), width=iw(6))
    d.rectangle([S(188), S(42), S(210), S(78)], fill=(250, 250, 250))
    d.rectangle([S(22), S(28), S(34), S(92)], fill=(232, 40, 40))
    d.text((S(112), S(60)), '1%', font=font(S(46), 900), fill=(255, 80, 80), anchor='mm')
    return lay

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

COINS = [(random.Random(k + 300).uniform(-1, 1), random.Random(k + 400).uniform(0.6, 1.0), random.Random(k + 500).uniform(0, 6.28),
          [(232, 184, 60), (200, 200, 206), (214, 150, 70)][k % 3]) for k in range(26)]
def coin_burst(img, c, u):
    """coins jumping out of the jar on the slam; they land and stay on the counter"""
    if u < 0: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k, (vx, vy, ph, col) in enumerate(COINS):
        uu = min(u, 0.75)
        x = c[0] + vx * 520 * uu
        y = c[1] - 120 - 1500 * vy * uu + 2600 * uu * uu
        y = min(y, 1660 + 14 * (k % 3))
        a = math.degrees(ph + u * 14) if u < 0.75 else math.degrees(ph)
        sq = abs(math.cos(ph + u * 9)) if u < 0.75 else 0.45
        poly(od, epoly(x, y, 24, max(5, 22 * sq), a), fill=col + (255,), outline=(110, 80, 20, 255), width=3)
    img.alpha_composite(ov)

# ------------------------------------------------------------------ sets
BACK = E13.BACK; MID = E13.MID
def build_lobby_bg(door=False):
    img = E3.wall_gradient(); d = ImageDraw.Draw(img)
    d.rectangle([0, S(1200), W * K, H * K], fill=E3.WAIN)
    d.rounded_rectangle([S(50), S(410), S(440), S(530)], radius=S(14), fill=(28, 104, 226), outline=(14, 50, 120), width=iw(5))
    d.text((S(245), S(470)), 'הבנק שלי', font=font(S(56), 900), fill=WHITE, anchor='mm')
    d.rounded_rectangle([S(70), S(560), S(420), S(640)], radius=S(10), fill=(255, 246, 200), outline=(200, 160, 40), width=iw(4))
    d.text((S(245), S(600)), 'סגירת חשבון: חלון 3', font=font(S(34), 900), fill=(200, 40, 40), anchor='mm')
    x0, y0, x1, y1 = 600, 400, 1020, 640
    d.rounded_rectangle([S(x0 + 8), S(y0 + 10), S(x1 + 8), S(y1 + 10)], radius=S(20), fill=(160, 168, 184))
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(20), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(6))
    d.line([(S(x1 - 130), S(y0 + 20)), (S(x1 - 130), S(y1 - 20))], fill=(60, 60, 70), width=iw(3))
    d.text((S(x1 - 65), S(y0 + 70)), 'חלון', font=font(S(36), 800), fill=E3.AMBER, anchor='mm')
    d.text((S(x1 - 65), S(y0 + 150)), '3', font=font(S(76), 900), fill=E3.AMBER, anchor='mm')
    return img

def build_door_bg():
    """the branch exit: a tall glass door on the left, bright street sunlight behind it"""
    img = E3.wall_gradient(); d = ImageDraw.Draw(img)
    d.rectangle([0, S(1200), W * K, H * K], fill=E3.WAIN)
    x0, y0, x1, y1 = 20, 300, 470, 1260
    d.rectangle([S(x0 - 20), S(y0 - 20), S(x1 + 20), S(y1)], fill=(150, 156, 170))
    # street outside: sky + sun
    for y in range(y0, y1, 6):
        u = (y - y0) / (y1 - y0)
        d.rectangle([S(x0), S(y), S(x1), S(y + 6)], fill=m.lerpc((255, 244, 196), (255, 214, 120), u))
    E(d, 240, 520, 120, 120, fill=(255, 252, 230))
    d.rectangle([S(x0), S(1050), S(x1), S(y1)], fill=(236, 200, 140))
    d.rectangle([S(x0), S(y0), S(x1), S(y1)], outline=(110, 116, 128), width=iw(10))
    d.line([(S(245), S(y0)), (S(245), S(y1))], fill=(110, 116, 128), width=iw(8))
    d.rounded_rectangle([S(150), S(430), S(340), S(490)], radius=S(10), fill=(30, 150, 70))
    d.text((S(245), S(460)), 'יציאה', font=font(S(38), 900), fill=WHITE, anchor='mm')
    return img

def sun_rays(img, t, k=1.0):
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for j in range(7):
        a = math.radians(-12 + j * 9 + 2 * math.sin(t * 1.5 + j))
        x0, y0 = 240, 520
        pts = [(x0, y0), (x0 + 1500 * math.cos(a - 0.03), y0 + 1500 * math.sin(a - 0.03)), (x0 + 1500 * math.cos(a + 0.03), y0 + 1500 * math.sin(a + 0.03))]
        poly(od, pts, fill=(255, 240, 180, int(46 * k)))
    img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(S(6))))

JUMPS = [(0.0, '17'), (3.0, '904'), (5.6, '12'), (9.0, '3'), (13.0, '388'), (19.0, '1'), (25.0, '76'), (29.0, '17')]
def board_text(t):
    txt = '17'
    for tj, v in JUMPS:
        if t >= tj: txt = v
    for tj, _ in JUMPS:
        if 0 < tj and 0 <= t - tj < 0.3: return txt, int((t - tj) / 0.07) % 2 == 0
    return txt, True

HX, HY, F = 560, 1010, 1.38

def scene_march(t, i):
    """L00: he marches in from the right, the jar under his arm, his ticket (live number) in the other paw"""
    img = LOBBY.copy()
    txt, on = board_text(t)
    E3.led_text(img, txt, 735, 520, 140 if len(txt) < 3 else 112, on)
    for name, x, y, sc, ph in BACK:
        E13.paste_sprite(img, name, 0, x + 6 * math.sin(t * 3 + ph) * 0.4, y + 10 * math.sin(t * 4.4 + ph) * 0.4, sc, flip=x > 540)
    for name, x, y, sc, ph in MID:
        E13.paste_sprite(img, name, 0, x + 8 * math.sin(t * 3.4 + ph), y + 12 * math.sin(t * 5 + ph) * 0.4, sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    u = t - T0
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.2, lid=0.0, pupil='normal', brow='angry' if False else 'none',
                                     mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-8, look=(-8, 0))
    if t >= at(0, 1): st.update(mouth=cat_mouth(t, rest='flat', loud='w'), lid=0.25, ear_dy=-14)   # "סופית." — narrowed eyes
    dx = 420 * (1 - ease_out(clamp(u / 0.32)))
    step = abs(math.sin(u * 7.5))
    dy = -18 * step - 8 * cat_v(t)
    rot = -8 * (1 - ease_out(clamp(u / 0.45))) + 2.5 * math.sin(u * 7.5)
    hx = HX + dx
    E(d, hx, 1660 + 0.5 * dy, 430, 460, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1720 + 0.5 * dy, 200, 310, fill=CREAM)
    # viewer's right: the jar clamped under his arm
    jp = (hx + 300, 1330 + 0.5 * dy)
    paste_rot(img, JAR, jp, -8, 1.0); d = ImageDraw.Draw(img)
    capsule(d, (hx + 230, 1440 + 0.5 * dy), (hx + 250, 1440 + 0.5 * dy), 110, FUR, OUT, 4)
    E12.big_paw(d, (jp[0] - 20, jp[1] + 120), -20, 0.9)
    # viewer's left: the ticket with the live number
    lp = (hx - 200, 1360 + 8 * math.sin(t * 2.0) + 0.5 * dy)
    capsule(d, (hx - 230, 1440 + 0.5 * dy), lp, 110, FUR, OUT, 4)
    tk = xform([(-48, -78), (48, -78), (48, 78), (-48, 78)], lp[0] - 10, lp[1] - 120, -8)
    poly(d, tk, fill=(252, 250, 242), outline=(150, 150, 140), width=3)
    c_ = xform([(0, -20)], lp[0] - 10, lp[1] - 120, -8)[0]
    d.text((S(c_[0]), S(c_[1])), str(QUEUE), font=font(S(40), 900), fill=INK, anchor='mm')
    E12.big_paw(d, lp, 10, 0.9)
    E12.paste_head(img, st, i, hx, HY + dy, F, rot)
    if u < 0.45:   # speed lines while he strides in
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        a = int(220 * (1 - u / 0.45))
        for k in range(7):
            y = 700 + k * 120; x0 = hx + 420 + 60 * (k % 2)
            line(od, [(x0, y), (x0 + 260, y)], (255, 255, 255, a), 10)
        img.alpha_composite(ov)
    return img

# ------------------------------------------------------------------ two-shot at window 3: Sharit left, the cat big on the right, the counter in front
T_HEAD = (225, 900); TS = 1.45
HX2, HY2, F2 = 790, 960, 1.45
STAMP_POS = [(130, 1660), (330, 1660)]     # her closing stamp, the "חשבון חדש" stamp (the plant)

def counter(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    d.rectangle([S(-20), S(1700), S(1100), S(1960)], fill=(150, 156, 170))

def stamps_on_counter(img, t, lift=None):
    """both stamps standing on the counter. lift = index of the stamp that is in her hand (not drawn here)"""
    for k, (lay, p) in enumerate(((STAMP_CLOSE, STAMP_POS[0]), (STAMP_NEW, STAMP_POS[1]))):
        if lift == k: continue
        paste_rot(img, lay, p, 0, 1.1)

def sharit_two(img, i, st_s):
    Ls = SH.draw(st_s, i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))

def scene_jar(t, i):
    """cold open + L06 in context: he slams the coin jar on the counter, coins burst; both stamps in shot"""
    img = SH_BG.copy()
    s0 = slam_t(t); u = t - s0
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.55, red=0.8, look=(18, 10), snack=True, mouth='munch')
    if u >= 0: st_s.update(lid=0.1 if u < 0.6 else 0.35, mouth='grin' if u > 0.6 else 'talk', snack=True, look=(22, 14), rot=-4 * math.exp(-u * 3))
    if CROWDJ:
        for name, x, y, sc, ph in E13.WIN_CROWD:
            hop = -26 * abs(math.sin(t * 7 + ph)) if u > 0.1 else 0
            E13.paste_sprite(img, name, 1 if u > 0 else 0, x + 300, y - 120 + hop, sc * 0.8, flip=x > 540)
    sharit_two(img, i, st_s)
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.5)
    v = cat_v(t)
    if u < 0: st.update(lid=0.1, pupil='big', brow='up', ear_dy=-20, mouth=cat_mouth(t, rest='w', loud='w'), look=(-18, 6))
    else: st.update(lid=0.0, pupil='big', brow='up', ear_dy=-26 * math.exp(-u * 2) - 6, mouth=cat_mouth(t, rest='smile', loud='smile'), look=(-20, 8), blush=0.9)
    dy = -40 * (1 - ease_in(clamp((u + 0.25) / 0.25))) if u < 0 else 22 * math.exp(-u * 8) * math.cos(u * 30)
    rot = -6 if u < 0 else 5 * math.sin(u * 16) * math.exp(-u * 2.5)
    E(d, HX2, 1720 + 0.3 * dy, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770 + 0.3 * dy, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy - 10 * v, F2, rot)
    counter(img)
    stamps_on_counter(img, t)
    d = ImageDraw.Draw(img)
    # the jar: coming down hard (frame 0 = in motion), then on the counter
    jc = (600, 1580) if u >= 0 else (600, 1580 - 620 * (1 - ease_in(clamp((u + 0.28) / 0.28))))
    sq = 1.0 + (0.12 * math.exp(-u * 12) if u >= 0 else 0)
    if u >= 0.0: coin_burst(img, (jc[0], jc[1]), u)
    lay = JAR if sq < 1.01 else JAR.resize((int(JAR.width * sq), int(JAR.height / sq)), Image.BICUBIC)
    paste_rot(img, lay, (jc[0], jc[1] + (10 if sq > 1.01 else 0)), 0 if u >= 0 else 6, 1.0)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (jc[0] + 90, jc[1] - 120), -60, 0.9)
    if u >= 0: burst(img, (jc[0], jc[1] - 40), u, (255, 236, 120), 170, 12, 0.35)
    return img

def scene_recap(t, i):
    """L02 (the send beat): his big face, three callback icons pop beside him"""
    img = SH_BG.copy()
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.65, red=0.9, look=(16, 6), snack=True, mouth='munch')
    if sh_v(t) > 0.1: st_s['mouth'] = 'talk'
    sharit_two(img, i, st_s)
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.2)
    k = sum(1 for x in ICONS if t >= x)
    st.update(lid=0.2 + 0.1 * k, pupil='normal', brow='sad' if k < 3 else 'none', ear_dy=-4, ear_droop=0.2 * k,
              mouth=cat_mouth(t, rest='flat', loud='w'), look=(-14, -6 + 4 * k))
    if t >= at(2, 3): st.update(lid=0.35, brow='none', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-16, look=(-20, 4))   # "סוגרים."
    v = cat_v(t)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 - 10 * v, F2, 3 * math.sin(t * 3.5))
    counter(img)
    stamps_on_counter(img, t)
    # the three callbacks pop in a row above his head (ep21 frozen card, ep23 grandma got the code, ep24 battery 1%)
    for j, (lay, c) in enumerate(((ICON_CARD, (840, 640)), (ICON_GRAN, (560, 600)), (ICON_BATT, (300, 650)))):
        uu = t - ICONS[j]
        if uu < 0: continue
        sc = 1 + 0.35 * math.exp(-uu * 9) * math.cos(uu * 20) if uu < 0.6 else 1.0
        paste_rot(img, lay, c, [-8, 4, -6][j] + 3 * math.sin(t * 3 + j), sc)
        if uu < 0.3: burst(img, c, uu, (255, 255, 255), 120, 8, 0.3)
    if t >= at(2, 3):   # "סוגרים." — a red X stamp over all three
        uu = t - at(2, 3)
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        s = 1.4 - 0.4 * ease_out(clamp(uu / 0.12))
        for c in ((840, 640), (560, 600), (300, 650)):
            r = 70 * s
            line(od, [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)], (230, 30, 40, 235), 16)
            line(od, [(c[0] - r, c[1] + r), (c[0] + r, c[1] - r)], (230, 30, 40, 235), 16)
        img.alpha_composite(ov)
    return img

def scene_two1(t, i):
    """probe TWO1: L01 as a two-shot — Sharit's puppy eyes on the left, his big determined face on the right"""
    img = SH_BG.copy()
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.62, red=0.8, blush=0.9, look=(18, 6), snack=True,
                                  rot=-5 * math.sin(t * 2))
    st_s['mouth'] = 'talk' if sh_v(t) > 0.12 else 'munch'
    sharit_two(img, i, st_s)
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.2)
    u = t - at(1, 1)
    if u < 0: st.update(lid=0.3, pupil='normal', brow='none', mouth='flat', ear_dy=-6, look=(-18, 4))
    else: st.update(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-18 * math.exp(-u * 3) - 4, look=(-20, 2), sweat=0.6)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2, F2, (-4 if u < 0 else 6 * math.exp(-u * 4) * math.sin(u * 20)))
    counter(img)
    stamps_on_counter(img, t)
    paste_rot(img, JAR, (900, 1560), 0, 0.9)
    return img

def scene_two(t, i):
    """L03–L04: she slides the closing form over, he signs it with a flourish ✓1"""
    img = SH_BG.copy()
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.5, red=0.8, blush=0.6, look=(18, 8))
    st_s['mouth'] = 'talk' if sh_v(t) > 0.12 else 'grin'
    sharit_two(img, i, st_s)
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    sig = clamp((t - (L[4] - 0.05)) / 0.45)
    u1 = t - CHK1
    if t < L[4]: st.update(lid=0.1, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile_small', loud='w'), ear_dy=-10, look=(-16, 12))
    else:
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-20, look=(-12, 14), blush=0.8)
    dy = -26 * abs(math.sin(u1 * 7)) * math.exp(-u1 * 1.6) if u1 >= 0 else 0
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy - 8 * cat_v(t), F2, 2 * math.sin(t * 4))
    counter(img)
    stamps_on_counter(img, t)
    e = ease_out(clamp((t - SLIDE) / 0.35))
    fc = lerp2((260, 1800), (560, 1690), e)
    paste_rot(img, form_layer(signed=sig), fc, lerp(-14, -4, e), 0.92)
    d = ImageDraw.Draw(img)
    if t < SLIDE + 0.35: SH.hand(d, (fc[0] - 200, fc[1] + 120))
    if t >= L[4] - 0.1:   # his paw with a pen, flourishing
        pp = (fc[0] - 90 + 160 * sig + 10 * math.sin(t * 40) * (1 - sig), fc[1] + 150 - 26 * math.sin(sig * 13))
        line(d, [(pp[0], pp[1]), (pp[0] + 60, pp[1] - 120)], (20, 40, 140), 12)
        E12.big_paw(d, (pp[0] + 70, pp[1] - 110), -150, 0.8)
    if u1 >= 0:
        s2 = 1.6 - 0.6 * ease_out(clamp(u1 / 0.12)); r = 60 * s2
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        c = (700, 1250)
        E(od, c[0], c[1], r, r, fill=GREEN + (235,), outline=WHITE + (255,), width=6)
        line(od, [(c[0] - 0.45 * r, c[1]), (c[0] - 0.1 * r, c[1] + 0.35 * r), (c[0] + 0.5 * r, c[1] - 0.35 * r)], WHITE + (255,), int(14 * s2))
        img.alpha_composite(ov)
        burst(img, (HX2, 900), u1, (255, 236, 120), 300, 12, 0.45)
    return img

# ------------------------------------------------------------------ Sharit at window 3 (customer POV), both stamps on the ledge
SLEDGE = [(760, 1400), (905, 1400)]
def sh_state(t, i):
    st = SH.base(); st.update(lid=0.55, red=0.8, hand_l=(190, 700))
    v = sh_v(t)
    st['mouth'] = 'talk' if v > 0.12 else 'grin'
    if L[1] - 0.1 <= t < L[2]:            # "אוי, חמוד... למה? טוב לך אצלנו." — sad puppy eyes, munching
        st.update(snack=True, look=(-6, 4), rot=-5 * math.sin(t * 2), blush=0.8, lid=0.62)
        if v <= 0.12: st['mouth'] = 'munch'
    elif L[5] - 0.1 <= t < L[6]:          # the fee: flat
        st.update(snack=True, lid=0.7, red=1.0, look=(4, 8))
        if v <= 0.12: st['mouth'] = 'munch'
    elif L[8] - 0.1 <= t < L[9]:          # "החשבון... נסגר!" — big moment, she stamps
        st.update(blush=1.0, lid=0.4, look=(10, 14), rot=4 * math.sin((t - L[8]) * 3))
    else:                                  # the break: "מזל טוב, מותק." the second stamp raised, a sweet grin
        st.update(blush=0.9, lid=0.5, look=(0, 0), rot=3 * math.sin(t * 3))
        if v <= 0.12: st['mouth'] = 'grin'
    return st

def scene_sh(t, i):
    img = E3.OFFICE.copy()
    img.alpha_composite(SH.draw(sh_state(t, i), i), dest=(int(S(E3.SH_POS[0])), int(S(E3.SH_POS[1]))))
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); E3.glass_tint(ImageDraw.Draw(ov)); img.alpha_composite(ov)
    img.alpha_composite(E3.GLASS_FG)
    E3.clock_hands(ImageDraw.Draw(img), 900, 420, 66, 11 * 3600 + 6 * 60 + t * 20)
    d = ImageDraw.Draw(img)
    brk = t >= THUNK
    stamping = L[8] - 0.1 <= t < L[9]
    for k, p in enumerate(SLEDGE):
        lay = STAMP_CLOSE if k == 0 else STAMP_NEW
        if stamping and k == 0:
            u = t - CHK3
            # the closing stamp rises, then THUNKs onto the form at "נסגר!"
            d.rectangle([S(330), S(1190), S(690), S(1290)], fill=(252, 252, 246), outline=(150, 150, 150), width=iw(3))
            y = 1000 if u < -0.12 else (lerp(1000, 1180, ease_in(clamp((u + 0.12) / 0.12))) if u < 0 else 1180 - 80 * ease_out(clamp((u - 0.15) / 0.3)))
            x = lerp(p[0], 510, ease_io(clamp((t - L[8]) / 0.4)))
            if u >= 0: paste_rot(img, IMP_CLOSED, (510, 1240), 4, 0.62 if u > 0.1 else 0.9)
            paste_rot(img, lay, (x, y), 0, 0.85); d = ImageDraw.Draw(img)
            SH.hand(d, (x, y - 110))
        elif brk and k == 1:
            # "מזל טוב, מותק." — she holds up the second stamp, label to camera
            u = t - THUNK
            pc = (lerp(p[0], 720, ease_out(clamp(u / 0.2))), lerp(p[1], 1080, ease_out(clamp(u / 0.2))))
            paste_rot(img, lay, pc, -6 + 4 * math.sin(t * 5), 1.15); d = ImageDraw.Draw(img)
            SH.hand(d, (pc[0], pc[1] - 120))
        else:
            paste_rot(img, lay, p, 0, 0.85)
    if L[5] - 0.1 <= t < L[6] and t >= FEE:   # the fee card
        u = t - FEE
        sc = 1 + 0.3 * math.exp(-u * 9) * math.cos(u * 20)
        paste_rot(img, FEE_CARD, (360, 1230), -6, sc)
    if stamping and t >= CHK3:
        u = t - CHK3
        confetti(img, u); burst(img, (510, 1240), u, (255, 236, 120), 200, 12, 0.45)
    return img

# ------------------------------------------------------------------ x16: Sharit counts the coins, his face in the foreground
def scene_count(t, i):
    img = E3.OFFICE.copy()
    st = SH.base(); st.update(lid=0.5, red=0.8, finger=True, look=(0, 16))
    v = sh_v(t); st['mouth'] = 'talk' if v > 0.12 else 'lazy'
    ff = FF[0] <= t < FF[1]
    if ff:   # her finger flicks coin after coin
        st['hand_r'] = (545 + 30 * math.sin(t * 40), 760 + 12 * math.cos(t * 40)); st['rot'] = 2 * math.sin(t * 20)
    img.alpha_composite(SH.draw(st, i), dest=(int(S(E3.SH_POS[0])), int(S(E3.SH_POS[1]))))
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); E3.glass_tint(ImageDraw.Draw(ov)); img.alpha_composite(ov)
    img.alpha_composite(E3.GLASS_FG)
    E3.clock_hands(ImageDraw.Draw(img), 900, 420, 66, 11 * 3600 + 6 * 60 + (t - FF[0]) * (16 * 60 if ff else 20) + 300)
    d = ImageDraw.Draw(img)
    # coin stacks growing on the ledge
    u = clamp((t - FF[0]) / max(0.1, CHK2 - FF[0]))
    n = int(lerp(3, 10, u))
    for k in range(n):
        sx = 300 + (k % 5) * 70; base = 1440 - (k // 5) * 0
        hh = 8 + (k * 7) % 5
        for j in range(hh):
            E(d, sx, base - j * 9, 30, 10, fill=[(232, 184, 60), (200, 200, 206), (214, 150, 70)][(k + j) % 3], outline=(110, 80, 20), width=2)
    for k, p in enumerate(SLEDGE): paste_rot(img, STAMP_CLOSE if k == 0 else STAMP_NEW, p, 0, 0.85)
    # tally display
    tally = 48 if t < at(7, 1) else 50
    if t < L[7] + 0.15: tally = int(lerp(1, 48, clamp((t - (L[7] - 0.1)) / 0.25)))
    d.rounded_rectangle([S(140), S(1180), S(400), S(1300)], radius=S(16), fill=(20, 22, 26), outline=(90, 90, 100), width=iw(5))
    E3.led_text(img, f'{tally} ₪', 270, 1240, 70, True)
    # his face in the foreground, eyes on the coins
    st2 = E3.base_state(); st2.update(red=0.9, cobweb=1.0, blush=0.5, lid=0.0, pupil='big', brow='up', look=(-18, -4),
                                       mouth='w' if t < at(7, 1) else 'smile', ear_dy=-10)
    if t >= CHK2: st2.update(mouth='smile', ear_dy=-22, blush=1.0)
    bob = -16 * abs(math.sin(t * 9)) if ff else 0
    d = ImageDraw.Draw(img)
    E(d, 870, 1940, 400, 330, fill=FUR, outline=OUT, width=7)
    E12.paste_head(img, st2, i, 850, 1560 + bob, 1.25, -6 + 3 * math.sin(t * 6))
    if t >= CHK2:
        uu = t - CHK2; s2 = 1.6 - 0.6 * ease_out(clamp(uu / 0.12)); r = 60 * s2
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        c = (540, 1200)
        E(od, c[0], c[1], r, r, fill=GREEN + (235,), outline=WHITE + (255,), width=6)
        line(od, [(c[0] - 0.45 * r, c[1]), (c[0] - 0.1 * r, c[1] + 0.35 * r), (c[0] + 0.5 * r, c[1] - 0.35 * r)], WHITE + (255,), int(14 * s2))
        img.alpha_composite(ov)
    return img

def ff_overlay(frame):
    frame.alpha_composite(m.SCAN)
    fd = ImageDraw.Draw(frame)
    for x0 in (858, 902):
        fd.polygon([(x0, 640), (x0 + 44, 670), (x0, 700)], fill=WHITE, outline=(10, 10, 12), width=4)
    fd.text((1005, 670), 'x16', font=font(46, 900), fill=WHITE, anchor='mm', stroke_width=6, stroke_fill=(10, 10, 12))

# ------------------------------------------------------------------ the door: peak + break
DX, DY, DF = 740, 1000, 1.36
def scene_door(t, i, reveal=False):
    img = DOOR.copy()
    peak = t < THUNK
    sun_rays(img, t, 1.0 if peak else 0.4)
    for name, x, y, sc, ph in BACK[3:]:
        mood = 1 if t < HOLD[0] else (2 if peak else 1)
        hop = -20 * abs(math.sin(t * 7 + ph)) if t < HOLD[0] else 0
        E13.paste_sprite(img, name, mood, x + 30, y + 40 + hop, sc, flip=True)
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0)
    u = t - L[9]
    if peak:
        st.update(lid=0.1, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-18, blush=0.9, look=(-16, -8))
        if t >= HOLD[0] - 0.1: st.update(eye_mode='closed', mouth='smile', blush=1.0, look=(0, 0))
        dy = -10 * ease_out(clamp(u / 0.3)); rot = -4 + 2 * math.sin(t * 3) if t < HOLD[0] else -4
    else:
        uu = t - THUNK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-22 * math.exp(-uu * 3), look=(14, -4),
                  twitch=(t >= REVEAL + 0.15 and int(t * 12) % 2 == 0), sweat=clamp((t - REVEAL) / 0.3) if t >= REVEAL else 0.4, blush=0.0)
        dy = -20 * math.exp(-uu * 6) - 10; rot = 0.0
    E(d, DX, 1660 + 0.5 * dy, 430, 460, fill=FUR, outline=OUT, width=7)
    E(d, DX, 1720 + 0.5 * dy, 200, 310, fill=CREAM)
    # viewer's left paw on the door handle
    hp = (380, 1190)
    d.rounded_rectangle([S(hp[0] - 22), S(hp[1] - 110), S(hp[0] + 22), S(hp[1] + 110)], radius=S(20), fill=(200, 204, 214), outline=(90, 96, 110), width=iw(5))
    capsule(d, (DX - 230, 1440 + 0.5 * dy), (hp[0] + 30, hp[1] + 30), 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, DX, DY + dy, DF, rot)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (hp[0] + 20, hp[1] + 20), 100, 0.9)
    # viewer's right paw: the closing form with the green "החשבון נסגר" (and, at the break, the red imprint)
    fc = (880, 1290 + 0.4 * dy)
    capsule(d, (DX + 230, 1440 + 0.5 * dy), (fc[0] - 10, fc[1] + 150), 110, FUR, OUT, 4)
    paste_rot(img, FORM_DONE, fc, 6, 0.78)
    if t >= REVEAL:
        uu = t - REVEAL
        sc = 1.8 - 1.0 * ease_out(clamp(uu / 0.1))
        paste_rot(img, IMP_NEW, (fc[0] - 4, fc[1] - 40), 9, 0.46 * sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (fc[0] - 10, fc[1] + 160), -20, 0.9)
    if peak and t < HOLD[0]: burst(img, (240, 520), t - (L[9] + 0.05), (255, 250, 220), 170, 10, 0.5)
    if t >= REVEAL: burst(img, (fc[0], fc[1] - 40), t - REVEAL, (255, 255, 255), 160, 10, 0.3)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('טופס', 770), ('עמלה', 545), ('נסגר', 320)]
def chips(frame, t):
    if RW[0] <= t < T0 + 0.25: return
    if t < COLD_END: done = [True, False, False]; gold = False      # cold open: signed, the coins are the fee
    else: done = [t >= CHK1, t >= CHK2, t >= CHK3]; gold = done[2]
    drained = t >= REVEAL + 0.2
    d = ImageDraw.Draw(frame)
    y = 345
    for k, (lab, cx) in enumerate(CHIPS):
        ok = done[k] and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        tkey = [CHK1, CHK2, CHK3][k]
        u = t - tkey
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok and t >= COLD_END) else 1.0
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
LOBBY = DOOR = SH_BG = JAR = STAMP_CLOSE = STAMP_NEW = IMP_CLOSED = IMP_NEW = FORM_DONE = FEE_CARD = None
ICON_CARD = ICON_GRAN = ICON_BATT = PILL_EP = PILL_Q = None
def init_all():
    global LOBBY, DOOR, SH_BG, JAR, STAMP_CLOSE, STAMP_NEW, IMP_CLOSED, IMP_NEW, FORM_DONE, FEE_CARD
    global ICON_CARD, ICON_GRAN, ICON_BATT, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    LOBBY = build_lobby_bg(); DOOR = build_door_bg()
    E13.build_crowd()
    SH_BG = E3.build_office_bg().filter(ImageFilter.GaussianBlur(S(3)))
    JAR = jar_layer()
    STAMP_CLOSE = rubber_stamp('סגירה'); STAMP_NEW = rubber_stamp('חשבון חדש', col=(28, 104, 226))
    IMP_CLOSED = stamp_imprint('החשבון נסגר', col=(30, 150, 70))
    IMP_NEW = stamp_imprint('חשבון חדש נפתח אוטומטית', col=RED, size=70)
    f = form_layer(signed=1.0)
    paste_rot(f, IMP_CLOSED, (180, 290), -8, 0.42)
    FORM_DONE = f
    FEE_CARD = Image.new('RGBA', (S(300), S(150)), (0, 0, 0, 0)); fd = ImageDraw.Draw(FEE_CARD)
    fd.rounded_rectangle([S(6), S(6), S(294), S(144)], radius=S(16), fill=(255, 246, 200), outline=(200, 40, 40), width=iw(6))
    fd.text((S(150), S(52)), 'עמלת סגירה', font=font(S(34), 900), fill=(200, 40, 40), anchor='mm')
    fd.text((S(150), S(108)), '50 ₪', font=font(S(54), 900), fill=INK, anchor='mm')
    ICON_CARD = card_frozen(); ICON_GRAN = phone_gran(); ICON_BATT = battery1()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'jar':
        u = t - slam_t(t)
        z = 1.04 + 0.02 * pu; cy = 1000
        if t < 0.3: z = 1.22 - 0.18 * ease_out(t / 0.3)                      # frame 0: snap pull-back, already moving
        if 0 <= u < 0.35: z = max(z, 1.04 + 0.10 * math.exp(-u * 9))
        if BIGO and t < COLD_END:
            k_ = ease_io(clamp((t - 0.55) / 0.35))
            z, cx, cy = lerp(1.55, 1.04, k_), lerp(800, 540, k_), lerp(1080, 1000, k_)
    elif name == 'rewind':
        z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'march':
        cy = 900; z = 1.05 + 0.03 * pu
    elif name == 'recap':
        z = 1.0 + 0.04 * pu; cy = 960
        if t >= at(2, 3): z, cy = 1.12, 900
        if RECAPZ: z, cx, cy = 1.28 + 0.04 * pu, 600, 880
    elif name == 'two':
        z = 1.0 + 0.03 * pu; cy = 1000
    elif name == 'sh':
        z = 1.14 + 0.03 * pu; cy = 900
        if L[8] - 0.1 <= t < L[9]: z, cy = 1.06, 1000
        if t >= THUNK: z, cy = 1.2 + 0.05 * pu, 900
    elif name == 'count':
        z = 1.04; cy = 1000
    elif name == 'door':
        cy = 960; z = 1.04 + 0.02 * pu
        if t >= HOLD[0]: z = 1.06 + 0.10 * ease_io(clamp((t - HOLD[0]) / (HOLD[1] - HOLD[0])))   # the slow push of the hold
        if t >= THUNK: z = 1.16 + 0.10 * math.exp(-(t - THUNK) * 12)
    elif name == 'reveal':
        e = ease_out(clamp((t - REVEAL) / 0.14))
        z, cx, cy = lerp(1.16, 1.6, e), lerp(540, 720, e), lerp(960, 1190, e)                     # snap onto the form, his face in frame
        if t >= FREEZE - 0.05:
            k_ = ease_in(clamp((t - FREEZE + 0.05) / 0.4))
            z, cx, cy = lerp(1.6, 1.2, k_), lerp(720, 540, k_), lerp(1190, 1000, k_)
    if name not in ('rewind', 'jar', 'reveal') and pu < 0.2: z = z + 0.07 * (1 - ease_out(pu / 0.2))   # snap-zoom on every cut
    if name == 'jar' and a > 0 and pu < 0.2: z = z + 0.07 * (1 - ease_out(pu / 0.2))
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'jar': img = scene_jar(t, i)
    elif name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_march(lerp(C(1) - 0.2, T0 + 0.3, ease_in(u)), i)
    elif name == 'march': img = scene_march(t, i)
    elif name == 'sh' and TWO1 and L[1] - 0.1 <= t < L[2]: img = scene_two1(t, i)
    elif name == 'sh': img = scene_sh(t, i)
    elif name == 'recap': img = scene_recap(t, i)
    elif name == 'two': img = scene_two(t, i)
    elif name == 'count': img = scene_count(t, i)
    else: img = scene_door(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if name == 'jar':
        u = t - slam_t(t)
        if 0 <= u < 0.5: shake = 20 * math.exp(-u * 6)
    if name == 'sh' and 0 <= t - CHK3 < 0.35: shake = 14 * math.exp(-(t - CHK3) * 8)
    if name in ('door', 'sh') and 0 <= t - THUNK < 0.3: shake = max(shake, 14 * math.exp(-(t - THUNK) * 8))
    if name == 'reveal' and t - REVEAL < 0.3: shake = 10 * math.exp(-(t - REVEAL) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if name == 'door' and HOLD[0] <= t < THUNK:     # the hush: everything dims a touch, heartbeat pulse
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.24 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(50 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if FF[0] <= t < FF[1]: ff_overlay(frame)
    for s_ in (CHK3, THUNK, REVEAL):
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
    if not NOSUB:
        for t0, t1, lines, li in SUB_TIMES:
            if t0 <= t < t1:
                cap = sub_layer(lines, PINKSUB if SPEAKER[li] == 'sh' else WHITE)
                m.paste_center(frame, cap, W / 2, 1450 if len(lines) == 1 else 1420)
    if name in ('jar', 'march', 'door', 'reveal'):   # serial markers (§O3); the ticket flickers in the last second
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + branch murmur; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(25)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0, off in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:02d}.npy')).astype(np.float64)
        y = y[int(off * SR):]
        if off > 0: f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f)
        add(voice, y, s0, 0.95 if SPEAKER[i0] == 'cat' else 0.9)
    def whoosh(t0, g=0.06, wl=0.16): add(sfx, m.bandpass(nz(wl), 600, 5000) * np.sin(np.pi * tt_(wl) / wl) ** 2, t0 - 0.08, g)
    def thud(g=0.9):
        tt = tt_(0.45); freq = 150 * np.exp(-tt * 6) + 42
        return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) + m.lowpass(nz(0.45), 420) * np.exp(-tt * 30) * 0.8) * g
    def coins(t0, n_=24, spread=0.6, g=0.10):
        r = np.random.default_rng(int(t0 * 100))
        for k in range(n_):
            f = r.uniform(2600, 6200); tc = t0 + spread * r.random() ** 1.6
            add(sfx, m.tone(f, 0.12, harm=((1, 1), (2.7, 0.4)), decay=40), tc, g * r.uniform(0.5, 1.0))
    def cheer(t0, ln=1.6, g=0.22, laugh=False):
        tt = tt_(ln); env = np.minimum(1, tt / 0.06) * np.exp(-tt * 1.6)
        sig = m.bandpass(nz(ln), 300, 3200) * env * (0.7 + 0.3 * np.sin(2 * np.pi * (5 if laugh else 7) * tt))
        add(sfx, sig, t0, g)
        for k, f in enumerate((520, 610, 700)):
            tw = tt_(0.5); fr = f + (60 if laugh else 220) * tw / 0.5
            mod = (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 9 * tw))) if laugh else 1.0
            add(sfx, m.lowpass(np.sin(2 * np.pi * np.cumsum(fr) / SR), 2000) * np.sin(np.pi * tw / 0.5) * mod, t0 + 0.08 + k * 0.11, 0.035)
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    # cold open: jar slam + coins
    add(sfx, thud(1.0), SLAM_COLD); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), SLAM_COLD, 0.45); coins(SLAM_COLD, 30, 0.7, 0.11)
    add(sfx, m.bandpass(nz(0.12), 500, 4000) * np.sin(np.pi * tt_(0.12) / 0.12) ** 2, 0.0, 0.08)
    # rewind tape
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    # march steps + jar rattle
    for k in range(5):
        ts = T0 + 0.05 + k * (math.pi / 7.5)
        add(sfx, m.lowpass(nz(0.08), 500) * np.exp(-tt_(0.08) * 40), ts, 0.25); coins(ts + 0.02, 3, 0.05, 0.04)
    # branch murmur everywhere except the hush
    mur_len = HOLD[0]; mur = m.bandpass(nz(mur_len), 200, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * tt_(mur_len)))
    add(sfx, mur, 0.0, 0.025)
    mur2 = m.bandpass(nz(DUR - THUNK + 0.3), 200, 1400); add(sfx, mur2, THUNK, 0.018)
    for name, a, b in SHOTS[2:]:
        if name not in ('reveal',) and a not in (THUNK + 0.30,): whoosh(a)
    # callback icon pops + the red X on "סוגרים."
    for x in ICONS: add(sfx, m.tone(880, 0.15, harm=((1, 1), (2, 0.4)), decay=18), x, 0.10)
    add(sfx, thud(0.6), at(2, 3))
    # the form slides, the pen flourish, ✓1
    add(sfx, m.bandpass(nz(0.3), 800, 5000) * np.sin(np.pi * tt_(0.3) / 0.3) ** 2, SLIDE, 0.08)
    add(sfx, m.bandpass(nz(0.45), 2000, 7000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 9 * tt_(0.45)))), L[4] - 0.05, 0.05)
    check(CHK1, 0.17)
    # fee card: cha-ching
    for k, f in enumerate((1568, 2093)): add(sfx, m.tone(f, 0.4, decay=8), FEE + k * 0.07, 0.08)
    # in-context slam: thud + coins + the queue laughs
    add(sfx, thud(1.0), SLAM2); coins(SLAM2, 30, 0.7, 0.11); cheer(SLAM2 + 0.15, 1.3, 0.18, laugh=True)
    # x16 counting: rapid coin clicks
    tc = FF[0]
    while tc < FF[1]:
        add(sfx, m.tone(4200 + 600 * math.sin(tc * 13), 0.04, decay=80), tc, 0.06); tc += 0.055
    check(CHK2, 0.17)
    # THUNK ✓3 gold + applause
    add(sfx, thud(1.1), CHK3); check(CHK3 + 0.1, 0.18, True); cheer(CHK3 + 0.05, 1.8, 0.24)
    # the door: a little street air, then the hush + heartbeat
    add(sfx, m.lowpass(nz(HOLD[0] - L[9] + 0.1), 900) * 0.6, L[9] - 0.05, 0.03)
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.05 + 0.28, 0.5)
    # the break: the second THUNK behind him, then the imprint slap + low dun
    add(sfx, thud(1.1), THUNK); add(sfx, m.highpass(nz(0.05), 1500) * np.exp(-tt_(0.05) * 70), THUNK, 0.35)
    add(sfx, thud(0.8), REVEAL); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), REVEAL, 0.4)
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
        print('DUR', DUR, 'NF', NF, 'OFF6', round(OFF6, 2)); print('L', [round(x, 2) for x in L]); print('D', D)
        print('CS', {k: [round(x, 2) for x in v] for k, v in CS.items()})
        print('ICONS', [round(x, 2) for x in ICONS], 'CHK', round(CHK1, 2), round(CHK2, 2), round(CHK3, 2), 'HOLD', [round(x, 2) for x in HOLD], 'THUNK', round(THUNK, 2), 'REVEAL', round(REVEAL, 2), 'FF', [round(x, 2) for x in FF])
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        for s in SUB_TIMES: print('sub', round(s[0], 2), round(s[1], 2), s[2])
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames):
            sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep25_contact.png')); print('ok'); return
    if mode == 'frame':
        init_all(); tm = float(sys.argv[2]); out = sys.argv[3]
        draw_frame(min(NF - 1, int(round(tm * FPS)))).save(out); print(out); return
    wav = os.path.join(OUTDIR, f'{OUTNAME}_audio.wav'); build_audio(wav); print('audio ok')
    if mode == 'audio': return
    mp4 = os.path.join(OUTDIR, f'{OUTNAME}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count() or 2, initializer=_init_worker) as pool:
        for k, b in enumerate(pool.imap(_render, range(int(LIMIT * FPS) if LIMIT else NF), chunksize=4)):
            proc.stdin.write(b)
            if k % 150 == 0: print('frame', k, '/', NF, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
