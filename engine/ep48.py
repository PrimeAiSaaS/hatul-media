#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 48: על הנורה — Series 2 "שוקו והג׳ינג׳י", season 1 "על הכביש", ep5 = season finale (VOICED, built
27.11 under §P, ~24 s). Music: "as the data says by then; if no data, none" — no 72 h data on ep44/46 yet → NO music.
Voices = voice bank 2026-11-23 lines 4800–4808 (Benji = the ginger, Knox = Shoko, Delia = Sharit), voice/ep48_prep.py.
Set: night. Shoko DRIVES (image right, his car, his confidence), the ginger rides (image left). The dashboard's centre
cluster: the orange fuel light, the needle on E and the small grey "טווח: 0 ק״מ" (THE PLANT: frame 0 + mid-climb; Shoko
drops his sunglasses over it once). Cut-outs: station 1 (side, closed), station 2 (top-down: a queue of forty cars),
station 3 (side, lit, the pump, Sharit's kiosk).
Want: reach fuel before the car dies. Stakes: pushing the car.
Clock: the nav "לתחנה בעוד 00:SS", real seconds, hits 00:00 on the break (the engine dies).
Climb: "נורת דלק. כבר עשרים קילומטר." → Shoko: "יש עוד חמישים על הנורה. רגוע." → station 1 ✓ "תחנה! ...סגורה." →
station 2 ✓ "תחנה! ...תור של ארבעים רכבים." → Shoko: "עוד אחת. אני מרגיש אותה." → station 3, rolling in on fumes:
"עוד מטר! עוד מטר!" ✓ gold.
Peak: "הגענו... הגענו!" both cheer, heartbeat.
Break (one_second_late): 00:00 — the engine dies one meter before the pump; the kiosk speaker (Sharit): "שירות עצמי, מותק."
Tag: Shoko, sunglasses down: "מישהו דוחף?" — the ginger pushes the car alone, Shoko steering.

  python3 voice/ep48_prep.py
  python3 ep48.py times | test t1 t2 ... | render   -> out/ep48_nura.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep13 as E13
import ep18 as E18
import ep44 as B
import ep47 as P
import hud as HUD
import clock_overlay as C
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, clamp, epoly, xform,
                        ease_io, ease_out, ease_in, font, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep48', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); AMBER = (255, 160, 30)
SHARIT_SUB = (255, 182, 210); SHOKO_SUB = (190, 230, 120)
QUEUE = int(os.environ.get('QUEUE', '434'))
EP_LABEL = 'פרק 48'
SERIES_LABEL = 'שוקו והג׳ינג׳י'
OUTNAME = os.environ.get('OUTNAME', 'ep48_nura')
LIMIT = float(os.environ.get('LIMIT', '0'))
GINGER, SHOKO = B.GINGER, B.SHOKO
paw, car_side = B.paw, B.car_side
NIGHT = (8, 14, 40)

def head(img, st, i, hx, hy, f, rot=0.0, pal=GINGER, shades='up', pick=True, wob=0.0):
    B.palette(pal)
    Lh, _ = m.draw_head(st, i)
    dl = ImageDraw.Draw(Lh)
    if shades == 'up': B.shades(dl)
    elif shades == 'down':                           # over the eyes, deadpan
        for cx in m.EYE_L[0], m.EYE_R[0]:
            poly(dl, [(cx - 58, 186), (cx + 58, 186), (cx + 48, 238), (cx - 48, 238)], fill=(16, 16, 20), outline=(0, 0, 0), width=5)
            line(dl, [(cx - 38, 198), (cx - 12, 198)], (120, 160, 200), 5)
        line(dl, [(m.EYE_L[0] + 58, 200), (m.EYE_R[0] - 58, 200)], (0, 0, 0), 8)
    if pick: B.toothpick(dl, wob)
    B.palette(GINGER)
    if abs(rot) > 1e-3: Lh = Lh.rotate(rot, resample=Image.BICUBIC, center=(260 * K, 245 * K))
    sz = int(520 * K * f)
    Lh = Lh.resize((sz, sz), Image.BICUBIC)
    img.alpha_composite(Lh, dest=(int(S(hx) - 260 * K * f), int(S(hy) - 245 * K * f)))

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
COLD_END = round(D[0] + 0.30, 2)            # cold open = 4800 "עוד מטר! עוד מטר!" (night, low angle, both leaning forward)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # the ginger: "נורת דלק. כבר עשרים קילומטר."
L[2] = L[1] + D[1] + 0.08                   # Shoko: "יש עוד חמישים על הנורה. רגוע." — drops his shades over the range
ROAD1 = L[2] + D[2] + 0.05                  # station 1 (side): closed
L[3] = ROAD1 + 0.25                         # "תחנה! ...סגורה."
CHK1 = L[3] + 0.15                          # תחנה 1 ✓ (passed — closed)
TOP = L[3] + D[3] + 0.08                    # station 2 (top-down): forty cars
L[4] = TOP + 0.20                           # "תחנה! ...תור של ארבעים רכבים."
CHK2 = L[4] + 0.15
INT2 = L[4] + D[4] + 0.08                   # interior: the dash again (plant), Shoko: "עוד אחת. אני מרגיש אותה."
L[5] = INT2 + 0.10
ROAD3 = L[5] + D[5] + 0.06                  # station 3 (side, lit): rolling in on fumes
L['0b'] = ROAD3 + 0.35                      # "עוד מטר! עוד מטר!" in context
CHK3 = L['0b'] + D[0] - 0.05; GOLDT = CHK3 + 0.04   # under the canopy ✓ gold
PEAK = CHK3 + 0.25                          # interior: "הגענו... הגענו!" both cheer
L[6] = PEAK + 0.05
HOLD = (L[6] + D[6] + 0.02, L[6] + D[6] + 0.44)
BREAK = HOLD[1]                             # 00:00 — the engine dies one metre before the pump
ZERO = BREAK
L[7] = BREAK + 0.75                         # the kiosk speaker: "שירות עצמי, מותק."
TAG = L[7] + D[7] + 0.06                    # interior: Shoko, shades down: "מישהו דוחף?"
L[8] = TAG + 0.10
PUSH = L[8] + D[8] - 0.35                   # side: the ginger pushes alone, Shoko steering
FREEZE = PUSH + 1.0
DUR = round(FREEZE + 0.33, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (3, L[3]), (4, L[4]), (5, L[5]), (0, L['0b']), (6, L[6]), (7, L[7]), (8, L[8])]
SPEAKER = {0: 'cat', 1: 'cat', 3: 'cat', 4: 'cat', 6: 'cat', 2: 'shoko', 5: 'shoko', 8: 'shoko', 7: 'sh'}

SUBS = {
    0: [['עוד מטר!'], ['עוד מטר!']],
    1: [['נורת דלק.'], ['כבר עשרים קילומטר.']],
    2: [['יש עוד חמישים על הנורה.'], ['רגוע.']],
    3: [['תחנה!'], ['...סגורה.']],
    4: [['תחנה!'], ['...תור של ארבעים רכבים.']],
    5: [['עוד אחת.'], ['אני מרגיש אותה.']],
    6: [['הגענו...'], ['הגענו!']],
    7: [['שירות עצמי, מותק.']],
    8: [['מישהו דוחף?']],
}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]
    if len(ch) > 1 and len(SEG[li]) < len(ch): ch = [[' '.join(sum(ch, []))]]
    segs = SEG[li]; n = len(ch)
    idx = [round(k * len(segs) / n) for k in range(n)]
    starts = [0.0] + [ss(li, idx[k]) for k in range(1, n)]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < n else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 6: b = min(b, HOLD[0] + 0.05)
        if li == 8: b = DUR - 0.25
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('car', 0.0, COLD_END), ('rewind', COLD_END, T0), ('car', T0, ROAD1), ('road1', ROAD1, TOP), ('top', TOP, INT2),
         ('car', INT2, ROAD3), ('road3', ROAD3, PEAK), ('car', PEAK, BREAK), ('road3', BREAK, TAG), ('car', TAG, PUSH),
         ('push', PUSH, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['נורת דלק?', 'יש עוד 50 קילומטר']          # keyword: נורת דלק (the pain in the viewer's words)
TOPCAPS = [(0.0, COLD_END, HOOK), (T0, L[1] + D[1] - 0.1, HOOK)]
HOOK_END = max(t1 for _, t1, _ in TOPCAPS)

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

def mouth_of(t, who, rest='flat', loud='w'):
    v = voice_v(t, who)
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

# ------------------------------------------------------------------ states
def ginger_state(t):
    st = E3.base_state(); st.update(red=0.0, blush=0.0, mouth='flat')
    rot, dy, lean = 0.0, 0.0, 0.0
    s_t = story_t(t)
    if t < COLD_END or (L['0b'] <= t < PEAK):                 # leaning forward: "עוד מטר!"
        st.update(lid=0.0, pupil='big', brow='up', mouth=mouth_of(s_t, 'cat', 'flat', 'smile'), ear_dy=-20, sweat=1.0, look=(10, -20))
        dy = -10 * voice_v(s_t, 'cat'); lean = 1.0; rot = 4 * math.sin(s_t * 11)
    elif t < L[2]:                                            # the want: the fuel light
        st.update(lid=0.0, pupil='big', brow='up', mouth=mouth_of(t, 'cat', 'flat', 'w'), ear_dy=-14, sweat=0.8, look=(30, 30))
        dy = -8 * voice_v(t, 'cat')
    elif t < ROAD1:                                           # Shoko's "רגוע."
        st.update(lid=0.3, pupil='normal', brow='annoyed', mouth='flat', ear_dy=-10, sweat=0.8, look=(34, 0))
    elif t < PEAK:                                            # INT2: dread
        st.update(lid=0.0, pupil='tiny', brow='up', mouth='flat', ear_dy=-16, sweat=1.0, look=(30, 20))
    elif t < BREAK:                                           # THE PEAK: cheering
        st.update(lid=0.0 if voice_v(t, 'cat') > 0.12 else 0.97, pupil='big', brow='up', mouth=mouth_of(t, 'cat', 'smile', 'smile'), ear_dy=-28, sweat=0.3, look=(0, -10), blush=0.7)
        dy = -22 * abs(math.sin((t - PEAK) * 7)); rot = 6 * math.sin((t - PEAK) * 7)
    else:                                                     # dead engine: frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none' if u < 0.9 else 'sad', mouth='flat', ear_droop=clamp((u - 0.4) / 0.8) * 0.7,
                  look=(20, 10), twitch=(u > 0.9 and int(t * 12) % 2 == 0), sweat=1.0)
    return st, rot, dy, lean

def shoko_state(t):
    st = E3.base_state(); st.update(lid=0.55, brow='annoyed', mouth='smile_small', look=(-14, 4), red=0.0, blush=0.0)
    v = voice_v(t, 'shoko')
    if v > 0.12: st['mouth'] = 'w' if v > 0.32 else 'smile_small'
    rot, dy, lean = 0.0, 0.0, 0.0
    if t < COLD_END or (L['0b'] <= t < PEAK): st.update(lid=0.2, look=(0, -20), mouth='goofy'); lean = 0.8
    if PEAK <= t < BREAK: st.update(lid=0.5, mouth='goofy', look=(-20, -10)); dy = -14 * abs(math.sin((t - PEAK) * 7 + 1))
    return st, rot, dy, lean

def shades_mode(t):
    """Shoko's sunglasses: on his forehead; on the dash over the range readout (4802 → ROAD1); on his eyes in the tag"""
    if L[2] + 0.5 <= t < ROAD1: return 'dash'
    if t >= TAG: return 'down'
    return 'up'

# ------------------------------------------------------------------ the dash cluster (THE PLANT)
CL = (560, 1345)
def cluster(img, t, shades_on=False, sc=1.0, c=CL):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = c[0] - 170 * sc, c[1] - 70 * sc, c[0] + 170 * sc, c[1] + 70 * sc
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(26 * sc), fill=(12, 14, 20), outline=(70, 74, 86), width=iw(5 * sc))
    # the fuel gauge (left half): an arc E…F, the needle on E
    gc = (c[0] - 80 * sc, c[1] + 26 * sc); r = 62 * sc
    d.arc([S(gc[0] - r), S(gc[1] - r), S(gc[0] + r), S(gc[1] + r)], 200, 340, fill=(200, 204, 214), width=iw(5 * sc))
    d.text((S(gc[0] - r + 2 * sc), S(gc[1] - 6 * sc)), 'E', font=font(S(26 * sc), 900), fill=(255, 80, 60), anchor='mm')
    d.text((S(gc[0] + r - 2 * sc), S(gc[1] - 6 * sc)), 'F', font=font(S(26 * sc), 900), fill=(200, 204, 214), anchor='mm')
    na = math.radians(204 + 2 * math.sin(t * 9))
    line(d, [gc, (gc[0] + r * 0.95 * math.cos(na), gc[1] + r * 0.95 * math.sin(na))], (255, 70, 50), 6 * sc)
    E(d, gc[0], gc[1], 9 * sc, 9 * sc, fill=(200, 204, 214))
    # the fuel light (blinking amber pump icon)
    on = int(t * 3) % 2 == 0 and t < BREAK + 0.2
    pc = (c[0] + 20 * sc, c[1] - 30 * sc); col = AMBER if on else (70, 44, 10)
    d.rounded_rectangle([S(pc[0] - 16 * sc), S(pc[1] - 22 * sc), S(pc[0] + 12 * sc), S(pc[1] + 22 * sc)], radius=S(4 * sc), fill=col)
    line(d, [(pc[0] + 12 * sc, pc[1] - 10 * sc), (pc[0] + 24 * sc, pc[1] + 4 * sc), (pc[0] + 24 * sc, pc[1] + 16 * sc)], col, 5 * sc)
    if on:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        E(od, pc[0], pc[1], 60 * sc, 60 * sc, fill=AMBER + (60,)); img.alpha_composite(ov); d = ImageDraw.Draw(img)
    # the range readout (small grey — the plant)
    d.text((S(c[0] + 100 * sc), S(c[1] + 34 * sc)), 'טווח: 0 ק״מ', font=font(S(34 * sc), 800), fill=(176, 180, 192), anchor='mm')
    if shades_on:                                     # Shoko's sunglasses dropped over the readout
        for k, cx in enumerate((c[0] + 60 * sc, c[0] + 160 * sc)):
            poly(d, [(cx - 52 * sc, c[1] + 6 * sc), (cx + 52 * sc, c[1] + 6 * sc), (cx + 44 * sc, c[1] + 62 * sc), (cx - 44 * sc, c[1] + 62 * sc)], fill=(16, 16, 20), outline=(0, 0, 0), width=5 * sc)
            line(d, [(cx - 34 * sc, c[1] + 18 * sc), (cx - 10 * sc, c[1] + 18 * sc)], (120, 160, 200), 4 * sc)
        line(d, [(c[0] + 112 * sc, c[1] + 16 * sc), (c[0] + 108 * sc, c[1] + 16 * sc)], (0, 0, 0), 8 * sc)

# ------------------------------------------------------------------ the car interior at night (Shoko drives, image right)
DRX, PAX, HY, F = 800, 290, 950, 0.90
def scene_car(t, i):
    img = CAR_NIGHT.copy()
    d = ImageDraw.Draw(img)
    # the road ahead through the windshield: dark, the station's glow when close
    s_t = story_t(t)
    glow = 0.0
    if t < COLD_END or t >= L['0b']: glow = 1.0
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    if glow:
        E(od, 540, 420, 520, 200, fill=(255, 236, 170, 70)); E(od, 540, 430, 300, 110, fill=(255, 246, 210, 90))
    img.alpha_composite(ov); d = ImageDraw.Draw(img)
    for hx in (DRX, PAX):
        d.rounded_rectangle([S(hx - 120), S(700), S(hx + 120), S(860)], radius=S(40), fill=(30, 32, 40), outline=(20, 20, 26), width=iw(5))
    gst, grot, gdy, glean = ginger_state(t); sst, srot, sdy, slean = shoko_state(t)
    for hx, pal in ((DRX, SHOKO), (PAX, GINGER)):
        E(d, hx, 1560, 250, 320, fill=pal['FUR'], outline=pal['OUT'], width=7)
        E(d, hx, 1600, 120, 230, fill=pal['CREAM'])
    line(d, [(PAX - 170, 1250), (PAX + 150, 1600)], (24, 24, 28), 26)
    line(d, [(DRX + 170, 1250), (DRX - 150, 1600)], (24, 24, 28), 26)
    sm = shades_mode(t)
    head(img, gst, i, PAX + 30 * glean, HY + gdy + 60 * glean, F + 0.12 * glean, grot, GINGER, shades='none', pick=False)
    head(img, sst, i, DRX - 20 * slean, HY - 10 + sdy + 40 * slean, F + 0.08 * slean, srot, SHOKO, shades='none' if sm == 'dash' else sm, wob=6 * math.sin(t * 3))
    d = ImageDraw.Draw(img)
    # dash
    poly(d, [(0, 1430), (W, 1430), (W, 1600), (0, 1600)], fill=(22, 24, 30))
    d.rectangle([0, S(1420), W * K, S(1446)], fill=(40, 42, 50))
    wc = (DRX, 1560); r = 175
    d.arc([S(wc[0] - r), S(wc[1] - r), S(wc[0] + r), S(wc[1] + r)], 180, 360, fill=(14, 14, 18), width=iw(36))
    BODY = (120, 124, 140); BODY_D = (90, 94, 108)
    d.rectangle([0, 0, W * K, S(250)], fill=BODY); d.rectangle([0, S(228), W * K, S(256)], fill=BODY_D)
    poly(d, [(0, 250), (120, 250), (30, 1450), (0, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(W, 250), (W - 120, 250), (W - 30, 1450), (W, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(-40, 1600), (W + 40, 1600), (W + 40, 1960), (-40, 1960)], fill=BODY)
    poly(d, [(-40, 1590), (W + 40, 1590), (W + 40, 1630), (-40, 1630)], fill=BODY_D)
    d.rectangle([S(532), S(250), S(548), S(300)], fill=(20, 20, 24))
    d.rounded_rectangle([S(420), S(296), S(660), S(366)], radius=S(22), fill=(16, 16, 20), outline=(6, 6, 8), width=iw(4))
    d.rounded_rectangle([S(432), S(306), S(648), S(356)], radius=S(16), fill=(30, 36, 60))
    # paws: Shoko one paw on the wheel; the ginger's paws on the dash (leaning) or up (cheering)
    p_ = (DRX + 150, 1410)
    capsule(d, (DRX + 80, 1520), p_, 78, SHOKO['FUR'], SHOKO['OUT'], 4); paw(d, p_, SHOKO, 0, 0.85)
    if sm == 'dash' and t < L[2] + 0.9:                       # Shoko's paw laying the shades on the dash
        k = clamp((t - (L[2] + 0.3)) / 0.4); pp = (lerp(DRX - 120, 720, k), lerp(1300, 1400, k))
        capsule(d, (DRX - 60, 1520), pp, 78, SHOKO['FUR'], SHOKO['OUT'], 4); paw(d, pp, SHOKO, 30, 0.85)
    if PEAK <= t < BREAK:
        for px in (PAX - 170, PAX + 170):
            pp = (px, 1050 - 40 * abs(math.sin((t - PEAK) * 7)))
            capsule(d, (PAX + (px - PAX) * 0.4, 1480), pp, 78, GINGER['FUR'], GINGER['OUT'], 4); paw(d, pp, GINGER, 0, 0.85)
    else:
        for px in (PAX - 150, PAX + 150):
            pp = (px, 1420)
            capsule(d, (PAX + (px - PAX) * 0.5, 1520), pp, 78, GINGER['FUR'], GINGER['OUT'], 4); paw(d, pp, GINGER, 0, 0.85)
    # night grade + dash glow on the faces
    img.alpha_composite(NIGHT_OV)
    cluster(img, t if t >= COLD_END else s_t, shades_on=(sm == 'dash'), sc=1.25)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    E(od, 540, 1300, 520, 300, fill=(255, 150, 40, 26 if int(story_t(t) * 3) % 2 == 0 else 10))
    if glow: E(od, 540, 900, 700, 500, fill=(255, 236, 170, 34))
    img.alpha_composite(ov)
    if BREAK <= t:                                            # the engine dies: the dash goes dark
        img.alpha_composite(Image.new('RGBA', img.size, (0, 0, 0, 40)))
    return img

# ------------------------------------------------------------------ night road kit
def night_bg():
    img = B.build_road_bg(); d = ImageDraw.Draw(img)
    for y in range(0, 1060, 8):
        v = y / 1060
        d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(6, 30, v)), int(lerp(10, 36, v)), int(lerp(34, 70, v))))
    for k in range(40):
        r = random.Random(k); E(d, r.uniform(0, W), r.uniform(20, 600), 3, 3, fill=(230, 230, 250))
    E(d, 880, 220, 60, 60, fill=(244, 240, 220))
    d.rectangle([0, S(1060), W * K, H * K], fill=(40, 42, 50)); d.rectangle([0, S(1600), W * K, H * K], fill=(70, 70, 76))
    return img

def buildings_night(d, off):
    span = 1360
    for x, h, c in B.BUILD:
        xx = (x - off * 0.35) % span - 160
        d.rectangle([S(xx), S(1060 - h), S(xx + 220), S(1060)], fill=(28, 30, 44), outline=(16, 16, 24), width=iw(3))
        for r_ in range(int(h / 110)):
            for c_ in range(2):
                lit = (int(x + r_ * 7 + c_ * 3) % 3 == 0)
                d.rectangle([S(xx + 34 + c_ * 92), S(1060 - h + 40 + r_ * 110), S(xx + 94 + c_ * 92), S(1060 - h + 100 + r_ * 110)], fill=(250, 214, 120) if lit else (40, 46, 64))

def station(img, x, lit=True, closed=False, kiosk=True, t=0.0, speak=False):
    """a side-view fuel station (no chain name): canopy on two pillars, a pump, a kiosk with Sharit"""
    d = ImageDraw.Draw(img)
    if lit:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        poly(od, [(x - 380, 760), (x + 380, 760), (x + 560, 1600), (x - 560, 1600)], fill=(255, 244, 200, 60))
        img.alpha_composite(ov); d = ImageDraw.Draw(img)
    d.rectangle([S(x - 420), S(700), S(x + 420), S(770)], fill=(230, 230, 236) if lit else (70, 72, 80), outline=(20, 20, 24), width=iw(4))
    d.rectangle([S(x - 420), S(750), S(x + 420), S(770)], fill=(200, 50, 50) if lit else (60, 30, 30))
    for px in (x - 360, x + 360): d.rectangle([S(px - 16), S(770), S(px + 16), S(1500)], fill=(200, 200, 206) if lit else (60, 62, 70))
    # the pump
    pc = x + 40
    d.rounded_rectangle([S(pc - 60), S(1200), S(pc + 60), S(1500)], radius=S(14), fill=(220, 60, 60) if lit else (70, 40, 40), outline=(20, 20, 24), width=iw(4))
    d.rounded_rectangle([S(pc - 40), S(1230), S(pc + 40), S(1290)], radius=S(6), fill=(30, 60, 40) if lit else (20, 22, 26))
    line(d, [(pc + 60, 1300), (pc + 100, 1380), (pc + 80, 1460)], (20, 20, 24), 10)
    if closed:                                                 # a 'סגור' board on a chain
        line(d, [(pc - 80, 1300), (pc, 1250), (pc + 80, 1300)], (180, 180, 190), 5)
        d.rounded_rectangle([S(pc - 100), S(1300), S(pc + 100), S(1380)], radius=S(10), fill=(250, 250, 248), outline=(20, 20, 24), width=iw(4))
        d.text((S(pc), S(1342)), 'סגור', font=font(S(52), 900), fill=RED, anchor='mm')
    if kiosk:
        kx = x - 250
        d.rectangle([S(kx - 130), S(1080), S(kx + 130), S(1500)], fill=(210, 206, 196) if lit else (60, 60, 66), outline=(20, 20, 24), width=iw(4))
        d.rectangle([S(kx - 100), S(1120), S(kx + 100), S(1300)], fill=(250, 236, 190) if lit else (24, 26, 34))
        if lit:
            av = SH_AV[1 if speak and int(t * 8) % 2 else 0]
            img.alpha_composite(av, (int(S(kx) - av.width / 2), int(S(1215) - av.height / 2))); d = ImageDraw.Draw(img)
            E(d, kx + 70, 1340, 22, 22, fill=(60, 60, 66), outline=(20, 20, 24), width=3)   # the speaker grille
            for j in range(3): line(d, [(kx + 56, 1332 + j * 8), (kx + 84, 1332 + j * 8)], (20, 20, 24), 2)
            if speak:
                for j in range(3):
                    r_ = 34 + 18 * j + 10 * ((t * 4) % 1)
                    d.arc([S(kx + 70 - r_), S(1340 - r_), S(kx + 70 + r_), S(1340 + r_)], 300, 60, fill=(255, 230, 120), width=iw(5))
    return pc

def scene_road(t, i, kind):
    img = NIGHT_BG.copy(); d = ImageDraw.Draw(img)
    sc = 0.95; y = 1540
    gst = dict(lid=0.0, pupil='big', brow='up', mouth='flat', ear_dy=-14, sweat=1.0, look=(30, -6))
    sst = dict(lid=0.55, brow='annoyed', mouth='smile_small', look=(20, 0))
    if kind == 'road1':                                       # station 1: closed, they roll past
        u = clamp((t - ROAD1) / (TOP - ROAD1)); off = u * 700
        buildings_night(d, off); B.lanes(d, off)
        station(img, 640 - off * 0.6, lit=False, closed=True, kiosk=True, t=t)
        x = lerp(260, 520, ease_out(u))
        gst.update(mouth='w' if voice_v(t, 'cat') > 0.2 else 'flat', look=(40, 0))
        car_side(img, x, y, sc, (70, 72, 84), [('ginger', gst, -60, 0.40), ('shoko', sst, 70, 0.40)], 1, None, t)
        headlights(img, x, y, sc)
    else:                                                     # station 3: rolling in on fumes; the break; Sharit
        buildings_night(d, 0); B.lanes(d, 0)
        pc = station(img, 780, lit=True, closed=False, kiosk=True, t=t, speak=voice_v(t, 'sh') > 0.12)
        stop_x = pc - 60 - 110 - 240 * sc                 # the nose stops ~1 m (≈110 px) short of the pump
        if t < BREAK:
            u = clamp((t - ROAD3) / (PEAK - ROAD3))
            x = lerp(-200, stop_x - 30, ease_out(u)) + 14 * math.sin(t * 20) * (1 - u)
            gst.update(mouth='w' if voice_v(story_t(t), 'cat') > 0.2 else 'smile_small', look=(40, -10))
            sst.update(lid=0.3, mouth='goofy')
        else:
            u = t - BREAK
            x = stop_x - 30 + 30 * (1 - math.exp(-u * 8))
            gst.update(pupil='tiny', brow='none', mouth='flat', look=(40, 0)); sst.update(lid=0.5, mouth='flat')
        car_side(img, x, y, sc, (70, 72, 84), [('ginger', gst, -60, 0.40), ('shoko', sst, 70, 0.40)], 1, None, t)
        d = ImageDraw.Draw(img)
        if t < BREAK + 0.4: headlights(img, x, y, sc, 1.0 if t < BREAK else max(0, 1 - (t - BREAK) / 0.3))
        if t >= BREAK:                                        # one metre short: the gap marker + a cough of smoke
            u = t - BREAK
            nose = x + 240 * sc
            k = clamp((u - 0.15) / 0.2)
            if k > 0:
                yy = 1310
                line(d, [(nose + 8, yy), (pc - 68, yy)], (255, 70, 60), 10)
                for xx_, s_ in ((nose + 8, 1), (pc - 68, -1)):
                    poly(d, [(xx_, yy), (xx_ + s_ * 26, yy - 16), (xx_ + s_ * 26, yy + 16)], fill=(255, 70, 60))
                d.text((S((nose + pc - 60) / 2), S(yy - 70)), '1 מ׳', font=font(S(84), 900), fill=(255, 90, 80), anchor='mm', stroke_width=iw(6), stroke_fill=(10, 10, 12))
            if u < 1.2:
                ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
                for j in range(4): E(od, x - 260 * sc - 30 * j, y - 40 - 80 * u - 20 * j, 50 + 50 * u, 34 + 30 * u, fill=(150, 150, 160, int(170 * (1 - u / 1.2))))
                img.alpha_composite(ov)
    img.alpha_composite(NIGHT_OV2)
    return img

def headlights(img, x, y, sc, a=1.0):
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    hx = x + 240 * sc
    poly(od, [(hx, y - 100 * sc), (hx + 520, y - 200 * sc), (hx + 520, y + 40 * sc), (hx, y - 70 * sc)], fill=(255, 246, 200, int(70 * a)))
    img.alpha_composite(ov)

# ------------------------------------------------------------------ top-down: station 2, forty cars
def scene_top(t, i):
    img = TOP_BG.copy()
    u = clamp((t - TOP) / (INT2 - TOP))
    # our car rolls past along the road (bottom lane, going up)
    lay = OUR_TOP.rotate(0, expand=True)
    x, y = 860, lerp(1750, 900, ease_io(u))
    img.alpha_composite(lay, (int(S(x) - lay.width / 2), int(S(y) - lay.height / 2)))
    d = ImageDraw.Draw(img)
    # the counter: "40"
    k = clamp((t - (L[4] + ss(4, 1))) / 0.3)
    if k > 0:
        sc = 1 + 0.4 * math.exp(-(t - (L[4] + ss(4, 1))) * 8)
        d.rounded_rectangle([S(150), S(500 - 60 * sc), S(470), S(500 + 60 * sc)], radius=S(30), fill=(250, 250, 248), outline=(10, 10, 12), width=iw(6))
        d.text((S(310), S(502)), '40 רכבים', font=font(S(int(58 * sc)), 900), fill=RED, anchor='mm')
    img.alpha_composite(NIGHT_OV2)
    # the duo in a corner bubble (second character in the shot)
    for k_, (pal, hx) in enumerate(((GINGER, 160), (SHOKO, 330))):
        E(d, 0, 0, 0, 0)
    st = E3.base_state(); st.update(lid=0.0, pupil='tiny', brow='up', mouth='w' if voice_v(t, 'cat') > 0.2 else 'flat', look=(0, 0), sweat=1.0, red=0.0, blush=0.0)
    head(img, st, i, 200, 1520, 0.62, 0, GINGER, shades='none', pick=False)
    st2 = E3.base_state(); st2.update(lid=0.55, brow='annoyed', mouth='smile_small', look=(-20, 0), red=0.0, blush=0.0)
    head(img, st2, i, 420, 1560, 0.55, 0, SHOKO, wob=5 * math.sin(t * 5))
    return img

def build_top_bg():
    img = Image.new('RGBA', (W * K, H * K), (44, 46, 54, 255)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S(660), H * K], fill=(64, 66, 74))                         # the station forecourt (image left)
    d.rectangle([S(660), 0, S(680), H * K], fill=(200, 200, 196))                   # curb
    for y in range(-40, H, 200): d.rectangle([S(856), S(y), S(866), S(y + 110)], fill=(220, 220, 220))
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle([S(60), S(80), S(600), S(440)], radius=S(20), fill=(236, 236, 240, 255), outline=(20, 20, 24, 255), width=iw(5))
    od.rectangle([S(60), S(410), S(600), S(440)], fill=(200, 50, 50, 255))
    img.alpha_composite(ov); d = ImageDraw.Draw(img)
    for px in (200, 460): d.rounded_rectangle([S(px - 40), S(200), S(px + 40), S(320)], radius=S(10), fill=(220, 60, 60), outline=(20, 20, 24), width=iw(4))
    cols = B.CAR_COLS
    tiny = [P.car_top(1.0, cols[k % 7]).resize((S(66), S(114)), Image.LANCZOS) for k in range(7)]
    # a snake of forty cars: up from the pumps, three columns, then out along the road
    pos = []
    for col_, xx in enumerate((130, 330, 530)):
        ys = range(560, 1900, 136) if col_ % 2 == 0 else range(1880, 560, -136)
        for yy in ys: pos.append((xx, yy))
    for k, (xx, yy) in enumerate(pos[:40]):
        c = tiny[k % 7]; img.alpha_composite(c, (S(xx) - c.width // 2, S(yy) - c.height // 2))
    return img

# ------------------------------------------------------------------ the push (the tag's last beat)
def scene_push(t, i):
    img = NIGHT_BG.copy(); d = ImageDraw.Draw(img)
    u = t - PUSH
    buildings_night(d, 0); B.lanes(d, 0)
    pc = station(img, 860, lit=True, closed=False, kiosk=True, t=t)
    sc = 0.95; y = 1540
    x = (pc - 170 - 240 * sc - 260) + 26 * ease_io(clamp(u / 1.0))                     # the car creeps forward
    sst = dict(lid=0.55, brow='annoyed', mouth='goofy', look=(30, 0))
    car_side(img, x + 260, y, sc, (70, 72, 84), [('shoko', sst, 70, 0.40)], 1, None, t)
    # the ginger behind the car, pushing with both paws, strained
    gx = x + 260 - 240 * sc - 120
    st = E3.base_state(); st.update(lid=0.0, pupil='tiny', brow='sad', mouth='squish', ear_droop=0.6, sweat=1.0, look=(30, 0), red=0.0, blush=0.0)
    E(d, gx - 30, 1420, 120, 150, fill=GINGER['FUR'], outline=GINGER['OUT'], width=6)
    for py in (1360, 1450): capsule(d, (gx + 20, py), (gx + 120, py - 10), 50, GINGER['FUR'], GINGER['OUT'], 4); paw(d, (gx + 124, py - 10), GINGER, 90, 0.6)
    head(img, st, i, gx - 20, 1240 + 6 * math.sin(t * 20), 0.62, -14, GINGER, shades='none', pick=False)
    d = ImageDraw.Draw(img)
    for j in range(3): line(d, [(gx - 200 - j * 30, 1300 + j * 60), (gx - 260 - j * 30, 1300 + j * 60)], (200, 200, 210), 5)
    img.alpha_composite(NIGHT_OV2)
    return img

def scene(t, i):
    name = shot(t)[0]
    if name.startswith('road'): img = scene_road(t, i, name)
    elif name == 'top': img = scene_top(t, i)
    elif name == 'push': img = scene_push(t, i)
    else: img = scene_car(t, i)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= t < c_ + 0.5: E18.burst(img, (540, 1150), t - c_, (120, 255, 160) if c_ != CHK3 else (255, 220, 120), 170, 10, 0.4)
    if GOLDT <= t < BREAK: E18.confetti(img, t - GOLDT + 0.3)
    return img

# ------------------------------------------------------------------ overlays
CHIP_Y = 200
CHIPS = [('תחנה 1', 820, CHK1), ('תחנה 2', 540, CHK2), ('תחנה 3', 260, CHK3)]
def chips(frame, t, y=CHIP_Y):
    if t < max(T0 + 0.2, HOOK_END) or t >= BREAK: return
    gold = t >= GOLDT
    d = ImageDraw.Draw(frame)
    for lab, cx, tk in CHIPS:
        ok = t >= tk
        fill = GOLD if gold else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or gold) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        w, h = 230 * sc, 62 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 22 * sc, y), lab, font=font(int(34 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 30 * sc
        if ok:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 9 * sc, y), (bx - 3 * sc, y + 8 * sc), (bx + 10 * sc, y - 8 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 16 * sc, y - 16 * sc, bx + 16 * sc, y + 16 * sc], outline=ink, width=4)

CLOCK_LABEL = ['לתחנה', 'בעוד']
def clock_state(t):
    name = shot(t)[0]
    st = story_t(t)
    if name == 'rewind': return C.secs_left(st, ZERO), 'run', True
    s = C.secs_left(st, ZERO)
    return s, ('hot' if s <= 5 else 'run'), False

CAR_NIGHT = NIGHT_BG = TOP_BG = OUR_TOP = NIGHT_OV = NIGHT_OV2 = PILL_EP = PILL_Q = PILL_SER = None
SH_AV = []
def init_all():
    global CAR_NIGHT, NIGHT_BG, TOP_BG, OUR_TOP, NIGHT_OV, NIGHT_OV2, SH_AV, PILL_EP, PILL_Q, PILL_SER
    B.init_all()
    CAR_NIGHT = B.build_car_bg()
    d = ImageDraw.Draw(CAR_NIGHT)
    x0, y0, x1, y1 = 130, 540, 950, 820                          # the rear window at night
    d.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=(14, 18, 40))
    for k in range(9): E(d, 200 + k * 85, 700 + 20 * math.sin(k), 6, 6, fill=(250, 214, 120))
    d.rounded_rectangle([S(x0 - 20), S(y0 - 20), S(x1 + 20), S(y1 + 20)], radius=S(40), outline=(36, 38, 46), width=iw(30))
    NIGHT_BG = night_bg(); TOP_BG = build_top_bg(); OUR_TOP = P.car_top(1.0, (70, 72, 84)).resize((S(150), S(260)), Image.LANCZOS)
    NIGHT_OV = Image.new('RGBA', (W * K, H * K), NIGHT + (45,))
    NIGHT_OV2 = Image.new('RGBA', (W * K, H * K), NIGHT + (60,))
    SH_AV = []
    for mo in ('lazy', 'talk'):
        st = SH.base(); st.update(mouth=mo, lid=0.55, look=(-10, 6), snack=False)
        lay = SH.draw(st, 3).crop((S(110), S(90), S(590), S(520)))
        SH_AV.append(lay.resize((S(170), int(S(170) * lay.height / lay.width)), Image.LANCZOS))
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_SER = HUD._pill(SERIES_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'car':
        z, cx, cy = 1.08 + 0.01 * pu, 540, 1080
        if a == 0.0:                                   # cold open: low angle from the dash, both leaning in, the cluster big
            z, cx, cy = 1.30 + 0.04 * t, 540, 1180
            if t < 0.3: z = 1.50 - 0.20 * ease_out(t / 0.3)
        elif a == T0:
            if t < L[2]: z, cx, cy = 1.18, 420, 1160    # the ginger + the fuel light
            else: z, cx, cy = 1.16, 650, 1150          # Shoko + the shades on the dash
        elif a == INT2: z, cx, cy = 1.22, 560, 1200     # the dash again (plant), both faces
        elif a == PEAK: z, cx, cy = 1.10, 540, 1060
        elif a == TAG: z, cx, cy = 1.22, 700, 1040      # Shoko, shades down
    elif name == 'rewind': z, cx, cy = 1.10, 560 + 30 * math.sin(t * 90), 1100
    elif name in ('frozen',): z, cx, cy = 1.0, 540, 960
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene(lerp(L['0b'] - 0.3, T0 + 0.3, ease_in(u)), i)
    elif name == 'frozen': img = scene_push(FREEZE - 0.01, i)
    else: img = scene(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 12 * math.exp(-t * 5)
    for s_ in (CHK3, BREAK):
        if 0 <= t - s_ < 0.35: shake = 18 * math.exp(-(t - s_) * 7)
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
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.24 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(50 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: B.rewind_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK, ROAD1, TOP, INT2, ROAD3, PEAK, TAG, PUSH):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(90 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    for t0, t1, lines in TOPCAPS:
        if t0 <= t < t1:
            band = frame.crop((0, 0, W, 470)).filter(ImageFilter.GaussianBlur(14))
            mask = Image.new('L', (W, 470), 0); md = ImageDraw.Draw(mask)
            for yy in range(470): md.line([(0, yy), (W, yy)], fill=int(255 * min(1, (470 - yy) / 90)))
            frame.paste(band, (0, 0), mask)
            dk = Image.new('RGBA', (W, 470), (0, 0, 0, 0)); dd = ImageDraw.Draw(dk)
            for yy in range(470): dd.line([(0, yy), (W, yy)], fill=(8, 10, 18, int(150 * min(1, (470 - yy) / 120))))
            frame.alpha_composite(dk, (0, 0))
            m.paste_center(frame, m.caption_layer(lines, 92, WHITE), W / 2, 290)
    if name not in ('frozen',): chips(frame, t)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            col = {'sh': SHARIT_SUB, 'shoko': SHOKO_SUB}.get(SPEAKER[li], WHITE)
            yy = 1560 if name != 'top' else 1330
            if name in ('road1', 'road3', 'push'): yy = 1780
            m.paste_center(frame, B.sub_layer(lines, col), W / 2, yy)
    if t < COLD_END or (T0 <= t < ROAD1) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_SER, (40, 70 + PILL_EP.height + 6))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    if t < DUR - 0.25 and t < BREAK + 1.2:
        s, state, scr = clock_state(t)
        if t >= BREAK: s, state = 0, 'zero'
        C.draw(frame, CLOCK_LABEL, s, state, t, scr)
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio: voices + SFX (no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(48)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
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
    add(sfx, thud(0.45), 0.0)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    # the engine: sputtering more and more towards the end; dead at the break
    tt = tt_(BREAK); sput = 1 + 0.6 * np.sign(np.sin(2 * np.pi * (2 + 4 * tt / BREAK) * tt)) * (tt / BREAK)
    add(sfx, m.lowpass(nz(BREAK), 120) * (1 + 0.3 * np.sin(2 * np.pi * 16 * tt)) * np.clip(sput, 0.2, 2), 0.0, 0.05)
    for t_ in (ROAD1, TOP, INT2, ROAD3, PUSH): whoosh(t_ + 0.05, 0.08, 0.25)
    for t_ in np.arange(0.0, BREAK, 1 / 3): add(sfx, m.tone(880, 0.05, harm=((1, 1),), decay=40), t_, 0.025)   # the fuel-light ding, soft
    check(CHK1, 0.15); check(CHK2, 0.16); add(sfx, thud(0.3), CHK3 - 0.05); check(CHK3, 0.2, True)
    heartbeat(HOLD[0] + 0.02); heartbeat(HOLD[0] + 0.26, 0.5)
    tt = tt_(0.9); add(sfx, m.lowpass(nz(0.9), 260) * np.exp(-tt * 3) * (1 + np.sign(np.sin(2 * np.pi * 7 * tt))), BREAK, 0.35)   # the cough + die
    add(sfx, thud(0.4), BREAK + 0.05)
    tt = tt_(0.25); add(sfx, np.sin(2 * np.pi * 1200 * tt) * np.exp(-tt * 20), L[7] - 0.2, 0.06)   # the kiosk speaker click-beep
    for k in range(4): add(sfx, m.lowpass(nz(0.25), 300) * np.sin(np.pi * tt_(0.25) / 0.25), PUSH + 0.1 + k * 0.28, 0.10)   # straining steps
    add(sfx, m.tone(82.4, 1.0, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), FREEZE - 0.2, 0.10)
    out = voice + sfx
    out = out[:int(DUR * SR)]
    wl_ = 0.3; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.28)
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
    ticks, prev = [], None
    for i in range(int(DUR * FPS)):
        tq = i / FPS; s, state, scr = clock_state(tq)
        if scr or tq >= BREAK: prev = None; continue
        if prev is not None and s != prev and s > 0: ticks.append(tq)
        prev = s
    C.add_ticks(path, ticks, loud_from=ZERO - 5.0, final=ZERO)

def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if mode == 'times':
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', round(T0, 2))
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('ROAD1', round(ROAD1, 2), 'TOP', round(TOP, 2), 'INT2', round(INT2, 2), 'ROAD3', round(ROAD3, 2))
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'PEAK', round(PEAK, 2), 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'TAG', round(TAG, 2), 'PUSH', round(PUSH, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        print('clock frame0', C.secs_left(story_t(0), ZERO), 'after rewind', C.secs_left(story_t(T0 + 0.01), ZERO), 'peak', C.secs_left(PEAK, ZERO))
        print('SEG4', SEG[4])
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, os.environ.get('SHEET', 'ep48_contact.png'))); print('ok'); return
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
