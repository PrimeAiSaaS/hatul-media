#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 46: ירוק — Series 2 "שוקו והג׳ינג׳י", season 1 "על הכביש", ep3 (VOICED, built 26.11 under §P,
~25 s). MUSIC arm: an original comic underscore made in code (ep44.underscore), ◀◀ → the peak only, ducked ≥12 dB
under the voices, cut to silence at the peak.
Voices = voice bank 2026-11-23 lines 4600–4606 (Benji = the ginger, Knox = Shoko, Delia = Sharit), voice/ep46_prep.py.
Set: first in line at a red light. The car interior through the windshield (this time the ginger DRIVES, image
right, both paws on the wheel; Shoko rides, image left, a 50 ₪ note in his paw); the rear window behind them is
filled by the truck right behind (the plant: Sharit at its wheel eating a burekas, her paw hovering over the horn);
a close insert of the rear-view mirror mid-climb (plant again, never pointed at); cut-outs to the road (side view):
the line of cars behind grows longer at every step.
Want: win Shoko's bet: "חמישים שקל שצופרים לך לפני הירוק." Stakes: 50 ₪ and his pride.
Clock: "ירוק בעוד 00:SS", real seconds, visible frame 0 → the break.
Climb: the bet → "לא בתור שלי. אני מוכן." → "מראות. בדקתי. חגורה. חגור." mirrors ✓ belt ✓ → gear in first,
"יד על ההילוך. רגל על המצמד. עיניים על הרמזור." ✓ gold הילוך.
Peak: 00:02, silence, "שלוש... שתיים..." heartbeat.
Break (his_own_hand): at 00:01 — before the green — a huge horn from the truck; he jumps, his paw slips off the
clutch, the car stalls; the light turns green; horns from everywhere; Sharit out of the truck window: "יאללה, מותק!"
Tag: Shoko holds out his paw: "חמישים."

  python3 voice/ep46_prep.py
  python3 ep46.py times | test t1 t2 ... | render   -> out/ep46_yarok.mp4
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
import hud as HUD
import clock_overlay as C
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, clamp, epoly, xform,
                        ease_io, ease_out, ease_in, font, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep46', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); ORANGE = (240, 140, 30)
SHARIT_SUB = (255, 182, 210); SHOKO_SUB = (190, 230, 120)
QUEUE = int(os.environ.get('QUEUE', '434'))
EP_LABEL = 'פרק 46'
SERIES_LABEL = 'שוקו והג׳ינג׳י'
OUTNAME = os.environ.get('OUTNAME', 'ep46_yarok')
LIMIT = float(os.environ.get('LIMIT', '0'))
GINGER, SHOKO = B.GINGER, B.SHOKO
head, paw, shadow_paste, car_side = B.head, B.paw, B.shadow_paste, B.car_side

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
COLD_END = round(D[0] + 0.25, 2)            # cold open = 4600 "יד על ההילוך. רגל על המצמד. עיניים על הרמזור."
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # Shoko, the note up: "חמישים שקל שצופרים לך לפני הירוק."
ROAD1 = L[1] + D[1] + 0.05                  # cut out: first at the red light, the truck behind, a short line
INT2 = ROAD1 + 0.85
L[2] = INT2 + 0.05                          # "לא בתור שלי. אני מוכן."
MIRROR = L[2] + D[2] + 0.04                 # insert: the rear-view mirror — Sharit, the burekas, her paw over the horn
INT3 = MIRROR + 0.80
L[3] = INT3 + 0.05                          # "מראות. בדקתי. חגורה. חגור."
CHK1 = L[3] + ss(3, 1) - 0.03               # מראות ✓ on "בדקתי"
CHK2 = L[3] + D[3] - 0.15                   # חגורה ✓ (click)
ROAD2 = L[3] + D[3] + 0.05                  # the line behind is now absurdly long
INT4 = ROAD2 + 0.80
L['0b'] = INT4 + 0.05                       # "יד על ההילוך. רגל על המצמד. עיניים על הרמזור." in context (= the cold open)
CHK3 = L['0b'] + ss(0, 1) - 0.03; GOLDT = CHK3 + 0.05   # הילוך ✓ gold
PEAK = L['0b'] + D[0] + 0.08                # silence, 00:02
L[4] = PEAK + 0.05                          # "שלוש... שתיים..."
HOLD = (L[4] + D[4] + 0.02, L[4] + D[4] + 0.42)
BREAK = HOLD[1]                             # the truck's horn at 00:01 — he jumps, stalls; green
ZERO = BREAK + 0.25                         # the light turns green while they stall
L[5] = BREAK + 0.20                         # Sharit out of the truck window: "יאללה, מותק!"
TAG = L[5] + D[5] - 0.08
L[6] = TAG + 0.02                           # Shoko's paw out: "חמישים."
FREEZE = L[6] + D[6] + 0.02
DUR = round(FREEZE + 0.33, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (3, L[3]), (0, L['0b']), (4, L[4]), (5, L[5]), (6, L[6])]
SPEAKER = {0: 'cat', 2: 'cat', 3: 'cat', 4: 'cat', 1: 'shoko', 6: 'shoko', 5: 'sh'}

SUBS = {
    0: [['יד על ההילוך.'], ['רגל על המצמד.'], ['עיניים על הרמזור.']],
    1: [['חמישים שקל'], ['שצופרים לך לפני הירוק.']],
    2: [['לא בתור שלי.'], ['אני מוכן.']],
    3: [['מראות. בדקתי.'], ['חגורה. חגור.']],
    4: [['שלוש...'], ['שתיים...']],
    5: [['יאללה, מותק!']],
    6: [['חמישים.']],
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
        if li == 4: b = min(b, HOLD[0])
        if li == 6: b = DUR - 0.25
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('car', 0.0, COLD_END), ('rewind', COLD_END, T0), ('car', T0, ROAD1), ('road1', ROAD1, INT2), ('car', INT2, MIRROR),
         ('mirror', MIRROR, INT3), ('car', INT3, ROAD2), ('road2', ROAD2, INT4), ('car', INT4, BREAK), ('road3', BREAK, TAG),
         ('car', TAG, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['צופרים לכם', 'לפני הירוק?']             # keyword: צופרים / ירוק (the pain in the viewer's words)
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
    rot, dy = 0.0, 0.0
    s_t = story_t(t)
    if s_t >= L['0b'] and t < PEAK or t < COLD_END:           # the ritual, rigid, eyes on the light
        st.update(lid=0.0, pupil='tiny', brow='annoyed', mouth=mouth_of(s_t, 'cat', 'flat', 'w'), ear_dy=-18, sweat=1.0, look=(0, -26))
        dy = -6 * voice_v(s_t, 'cat')
    elif t < ROAD1:                                           # the bet: offended
        st.update(lid=0.2, pupil='big', brow='annoyed', mouth='flat', ear_dy=-10, sweat=0.4, look=(-30, 0))
    elif t < MIRROR:                                          # "לא בתור שלי. אני מוכן."
        st.update(lid=0.25, pupil='normal', brow='annoyed', mouth=mouth_of(t, 'cat', 'flat', 'w'), ear_dy=-8, sweat=0.5, look=(-26, -4))
        dy = -10 * voice_v(t, 'cat')
    elif t < L['0b']:                                         # mirrors, belt
        u = t - L[3]
        st.update(lid=0.0, pupil='big', brow='up', mouth=mouth_of(t, 'cat', 'flat', 'w'), ear_dy=-12, sweat=0.8, look=(-30 if u < ss(3, 1) else 20, -30 if u < ss(3, 1) else 20))
        rot = 4 * math.sin(t * 7)
    elif t < BREAK:                                           # THE PEAK: whispering the count
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=mouth_of(t, 'cat', 'flat', 'smile_small'), ear_dy=-24, sweat=1.0, look=(0, -30))
        rot = 1.5 * math.sin(t * 30)
    else:                                                     # stalled, frozen, then the paw out
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none' if u < 0.9 else 'sad', mouth='w' if u < 0.5 else 'flat', ear_dy=-36 * math.exp(-u * 4),
                  ear_droop=clamp((u - 1.0) / 0.8) * 0.6, look=(-20, 6), twitch=(u > 0.9 and int(t * 12) % 2 == 0), sweat=1.0)
        dy = -60 * math.exp(-u * 6)
    return st, rot, dy

def shoko_state(t):
    st = E3.base_state(); st.update(lid=0.55, brow='annoyed', mouth='smile_small', look=(20, 4), red=0.0, blush=0.0)
    rot, dy = 0.0, 0.0
    v = voice_v(t, 'shoko')
    if v > 0.12: st['mouth'] = 'w' if v > 0.32 else 'smile_small'
    if PEAK <= t < BREAK: st.update(lid=0.6, mouth='goofy', look=(30, 0))
    elif t >= BREAK: st.update(lid=0.5, mouth='goofy' if v < 0.12 else st['mouth'], look=(30, 4)); rot = 3 * math.sin(t * 3)
    return st, rot, dy

# ------------------------------------------------------------------ props
def note50(d, c, ang=0.0, sc=1.0):
    pts = xform([(-110 * sc, -56 * sc), (110 * sc, -56 * sc), (110 * sc, 56 * sc), (-110 * sc, 56 * sc)], c[0], c[1], ang)
    poly(d, pts, fill=(140, 200, 150), outline=(40, 90, 50), width=4)
    tc = xform([(0, 0)], c[0], c[1], ang)[0]
    d.text((S(tc[0]), S(tc[1])), '50', font=font(S(64 * sc), 900), fill=(30, 80, 40), anchor='mm')

def burekas(d, c, sc=1.0):
    poly(d, [(c[0] - 40 * sc, c[1] + 20 * sc), (c[0] + 40 * sc, c[1] + 20 * sc), (c[0], c[1] - 34 * sc)], fill=(232, 176, 90), outline=(140, 90, 30), width=3)
    for k_ in range(3): E(d, c[0] - 14 * sc + k_ * 14 * sc, c[1] + 2 * sc, 3 * sc, 2 * sc, fill=(60, 40, 20))

def truck_face(img, cx, cy, sc, t, horn=0.0):
    """the truck seen from the front (in the rear window / the mirror): grille, windshield, Sharit at the wheel"""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(cx - 330 * sc), S(cy - 300 * sc), S(cx + 330 * sc), S(cy + 300 * sc)], radius=S(40 * sc), fill=ORANGE, outline=(60, 30, 10), width=iw(6))
    d.rounded_rectangle([S(cx - 280 * sc), S(cy - 260 * sc), S(cx + 280 * sc), S(cy + 20 * sc)], radius=S(24 * sc), fill=(170, 200, 224))
    av = SH_AV_BIG; sz = (int(av.width * sc * 1.6), int(av.height * sc * 1.6))
    img.alpha_composite(av.resize(sz, Image.BICUBIC), (int(S(cx - 60 * sc) - sz[0] / 2), int(S(cy - 110 * sc) - sz[1] / 2)))
    d = ImageDraw.Draw(img)
    burekas(d, (cx - 160 * sc, cy - 60 * sc + 6 * sc * math.sin(t * 8)), sc * 1.2)
    d.arc([S(cx - 10 * sc), S(cy - 40 * sc), S(cx + 230 * sc), S(cy + 120 * sc)], 180, 360, fill=(30, 30, 34), width=iw(16 * sc + 2))   # her wheel
    hp = (cx + 110 * sc, lerp(cy - 70 * sc, cy - 10 * sc, horn) + 8 * sc * math.sin(t * 5) * (1 - horn))   # her paw hovering over the horn
    E(d, cx + 110 * sc, cy + 30 * sc, 30 * sc, 30 * sc, fill=(60, 60, 66))
    E(d, hp[0], hp[1], 34 * sc, 26 * sc, fill=SH.SKIN, outline=SH.SKIN_O, width=3)
    for k_ in range(6): d.rectangle([S(cx - 260 * sc), S(cy + 60 * sc + k_ * 30 * sc), S(cx + 260 * sc), S(cy + 72 * sc + k_ * 30 * sc)], fill=(60, 30, 10))
    for sx in (-1, 1): E(d, cx + sx * 260 * sc, cy + 230 * sc, 40 * sc, 30 * sc, fill=(255, 246, 200), outline=(60, 30, 10), width=3)

# ------------------------------------------------------------------ the car interior (the ginger drives, image right)
GHX, SHX, HY, F = 800, 290, 950, 0.90
def scene_car(t, i):
    img = CAR_BG.copy()
    # the truck fills the rear window (plant)
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    horn = clamp((t - (BREAK - 0.15)) / 0.15) if t >= BREAK - 0.15 else 0.0
    truck_face(lay, 540, 700, 0.62, t, horn)
    mask = Image.new('L', img.size, 0); ImageDraw.Draw(mask).rectangle([S(130), S(540), S(950), S(820)], fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(mask))))
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(110), S(520), S(970), S(840)], radius=S(40), outline=(50, 52, 60), width=iw(30))
    for hx in (GHX, SHX):
        d.rounded_rectangle([S(hx - 120), S(700), S(hx + 120), S(860)], radius=S(40), fill=(44, 46, 54), outline=(30, 30, 36), width=iw(5))
    for hx, pal in ((GHX, GINGER), (SHX, SHOKO)):
        E(d, hx, 1560, 250, 320, fill=pal['FUR'], outline=pal['OUT'], width=7)
        E(d, hx, 1600, 120, 230, fill=pal['CREAM'])
    belt = t >= CHK2 or t < COLD_END or t >= L['0b']
    line(d, [(SHX - 170, 1250), (SHX + 150, 1600)], (30, 30, 34), 26)
    if belt: line(d, [(GHX - 170, 1250), (GHX + 150, 1600)], (30, 30, 34), 26)
    elif t >= CHK2 - 0.6:                                   # the belt being pulled across
        k = clamp((t - (CHK2 - 0.6)) / 0.6); line(d, [(GHX - 170, 1250), (lerp(GHX - 170, GHX + 150, k), lerp(1250, 1600, k))], (30, 30, 34), 26)
    gst, grot, gdy = ginger_state(t); sst, srot, sdy = shoko_state(t)
    head(img, gst, i, GHX, HY + gdy, F, grot, GINGER)
    head(img, sst, i, SHX, HY - 10 + sdy, F, srot, SHOKO, props=True, wob=6 * math.sin(t * 3))
    d = ImageDraw.Draw(img)
    # dash, gear stick
    poly(d, [(0, 1430), (W, 1430), (W, 1600), (0, 1600)], fill=(34, 36, 42))
    d.rectangle([0, S(1420), W * K, S(1446)], fill=(58, 60, 68))
    d.rectangle([S(500), S(1450), S(580), S(1600)], fill=(24, 24, 28))
    gear_k = clamp((t - (CHK3 - 0.3)) / 0.3) if (t >= L['0b'] or t < COLD_END) else 0.0
    if t < COLD_END: gear_k = clamp((story_t(t) - (CHK3 - 0.3)) / 0.3)
    knob = (540, lerp(1470, 1440, gear_k))
    line(d, [(540, 1600), knob], (40, 40, 46), 16); E(d, knob[0], knob[1], 30, 30, fill=(30, 30, 34), outline=(10, 10, 12), width=4)
    # the wheel in front of the ginger
    wc = (GHX, 1560); r = 175
    d.arc([S(wc[0] - r), S(wc[1] - r), S(wc[0] + r), S(wc[1] + r)], 180, 360, fill=(18, 18, 22), width=iw(36))
    BODY = (236, 238, 242); BODY_D = (190, 194, 204)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k_, xa in enumerate((180, 300, 760)):
        poly(od, [(xa, 260), (xa + 70 + 30 * k_, 260), (xa - 200 + 30 * k_, 1420), (xa - 270, 1420)], fill=(255, 255, 255, 20))
    img.alpha_composite(ov); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W * K, S(250)], fill=BODY); d.rectangle([0, S(228), W * K, S(256)], fill=BODY_D)
    poly(d, [(0, 250), (120, 250), (30, 1450), (0, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(W, 250), (W - 120, 250), (W - 30, 1450), (W, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(-40, 1600), (W + 40, 1600), (W + 40, 1960), (-40, 1960)], fill=BODY)
    poly(d, [(-40, 1590), (W + 40, 1590), (W + 40, 1630), (-40, 1630)], fill=BODY_D)
    # the rear-view mirror (small: the truck in it)
    d.rectangle([S(532), S(250), S(548), S(300)], fill=(30, 30, 34))
    d.rounded_rectangle([S(420), S(296), S(660), S(366)], radius=S(22), fill=(24, 24, 28), outline=(10, 10, 12), width=iw(4))
    d.rounded_rectangle([S(432), S(306), S(648), S(356)], radius=S(16), fill=ORANGE)
    # paws: the ginger both on the wheel (10 and 2) — one goes to the gear in the ritual; slips at the break
    stalled = t >= BREAK
    if stalled and t < TAG:
        u = t - BREAK
        for px, py in ((GHX - 200, 1300 - 60 * math.exp(-u * 3)), (GHX + 190, 1280 - 80 * math.exp(-u * 3))):
            capsule(d, (GHX + (px - GHX) * 0.4, 1480), (px, py), 78, GINGER['FUR'], GINGER['OUT'], 4); paw(d, (px, py), GINGER, 0, 0.85)
    else:
        lp = (GHX - 160, 1410)
        if gear_k > 0: lp = (lerp(GHX - 160, 540, gear_k), lerp(1410, knob[1] - 10, gear_k))
        for p_ in (lp, (GHX + 160, 1410)):
            capsule(d, (GHX + (p_[0] - GHX) * 0.5, 1520), p_, 78, GINGER['FUR'], GINGER['OUT'], 4); paw(d, p_, GINGER, 0, 0.85)
    # Shoko: the 50 note (the bet), then the paw out (the tag)
    if T0 <= t < MIRROR:
        nc = (SHX + 130 + 8 * math.sin(t * 4), 1250 + 6 * math.sin(t * 6))
        capsule(d, (SHX + 60, 1500), (nc[0] - 40, nc[1] + 60), 80, SHOKO['FUR'], SHOKO['OUT'], 4)
        note50(d, nc, -8, 1.0); paw(d, (nc[0] - 40, nc[1] + 60), SHOKO, 20, 0.8)
    elif t >= TAG:
        u = ease_out(clamp((t - TAG) / 0.25)); pp = (lerp(SHX + 60, 560, u), lerp(1450, 1260, u))
        capsule(d, (SHX + 60, 1500), pp, 80, SHOKO['FUR'], SHOKO['OUT'], 4); paw(d, pp, SHOKO, -90, 0.9)
    else:
        capsule(d, (SHX - 60, 1500), (SHX - 140, 1420), 80, SHOKO['FUR'], SHOKO['OUT'], 4); paw(d, (SHX - 140, 1420), SHOKO, 0, 0.85)
    # the traffic light, seen high through the windshield (red → green at ZERO)
    tl = (900, 360)
    d.rounded_rectangle([S(tl[0] - 50), S(tl[1] - 120), S(tl[0] + 50), S(tl[1] + 120)], radius=S(16), fill=(30, 30, 34), outline=(10, 10, 12), width=iw(4))
    g = story_t(t) >= ZERO and t >= BREAK
    E(d, tl[0], tl[1] - 60, 34, 34, fill=(255, 60, 50) if not g else (80, 20, 20))
    E(d, tl[0], tl[1] + 60, 34, 34, fill=(60, 230, 90) if g else (20, 70, 30))
    if stalled and t < TAG + 0.6:                             # the stall: a puff from the hood
        u = t - BREAK
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k_ in range(5): E(od, 540 + (k_ - 2) * 120 + 40 * u, 1680 - 200 * u - k_ * 20, 90 + 60 * u, 60 + 40 * u, fill=(220, 220, 224, int(150 * max(0, 1 - u))))
        img.alpha_composite(ov)
    return img

# ------------------------------------------------------------------ the mirror insert (plant again)
def scene_mirror(t, i):
    img = CAR_BG.copy(); img.alpha_composite(Image.new('RGBA', img.size, (20, 20, 26, 200)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(60), S(560), S(1020), S(1360)], radius=S(120), fill=(24, 24, 28), outline=(10, 10, 12), width=iw(10))
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle([0, 0, W * K, H * K], fill=(170, 196, 222))
    truck_face(lay, 540, 1000, 1.25, t, 0.0)
    mask = Image.new('L', img.size, 0); ImageDraw.Draw(mask).rounded_rectangle([S(90), S(590), S(990), S(1330)], radius=S(100), fill=255)
    lay.putalpha(mask)
    img.alpha_composite(lay)
    # the ginger's eyes at the bottom edge of the mirror (he checks it)
    st = E3.base_state(); st.update(lid=0.0, pupil='big', brow='up', mouth='flat', look=(0, -20), sweat=0.6)
    head(img, st, i, 540, 1700, 0.9, 0, GINGER)
    return img

# ------------------------------------------------------------------ the road (side view): first at the light, the line grows
def build_road_bg():
    return B.build_road_bg()

def truck_side(img, x, y, sc, t, horn=False):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(x - 420 * sc), S(y - 380 * sc), S(x + 120 * sc), S(y - 40 * sc)], radius=S(16 * sc), fill=(230, 230, 236), outline=(30, 30, 34), width=iw(4))
    poly(d, [(x + 120 * sc, y - 40 * sc), (x + 120 * sc, y - 300 * sc), (x + 230 * sc, y - 300 * sc), (x + 300 * sc, y - 170 * sc), (x + 300 * sc, y - 40 * sc)], fill=ORANGE, outline=(60, 30, 10), width=5)
    poly(d, [(x + 140 * sc, y - 280 * sc), (x + 220 * sc, y - 280 * sc), (x + 278 * sc, y - 180 * sc), (x + 140 * sc, y - 180 * sc)], fill=(170, 200, 224))
    av = SH_AV_BIG; sz = (int(av.width * sc * 0.7), int(av.height * sc * 0.7))
    img.alpha_composite(av.resize(sz, Image.BICUBIC), (int(S(x + 200 * sc) - sz[0] / 2), int(S(y - 230 * sc) - sz[1] / 2)))
    d = ImageDraw.Draw(img)
    for wx in (-320, -170, 200): E(d, x + wx * sc, y - 20 * sc, 54 * sc, 54 * sc, fill=(24, 24, 28)); E(d, x + wx * sc, y - 20 * sc, 22 * sc, 22 * sc, fill=(160, 160, 170))

def traffic_pole(d, x, y, green):
    d.rectangle([S(x - 10), S(y - 700), S(x + 10), S(y)], fill=(60, 62, 70))
    d.rounded_rectangle([S(x - 60), S(y - 900), S(x + 60), S(y - 640)], radius=S(18), fill=(30, 30, 34), outline=(10, 10, 12), width=iw(4))
    E(d, x, y - 840, 40, 40, fill=(255, 60, 50) if not green else (80, 20, 20))
    E(d, x, y - 700, 40, 40, fill=(60, 230, 90) if green else (20, 70, 30))

def scene_road(t, i, kind):
    img = ROAD_BG.copy(); d = ImageDraw.Draw(img)
    B.buildings(d, 400); B.lanes(d, 0)
    green = kind == 'road3' and t >= ZERO
    sc = {'road1': 0.9, 'road2': 0.38, 'road3': 0.8}[kind]
    stop_x = 980
    d.rectangle([S(stop_x - 8), S(1080), S(stop_x + 8), S(1620)], fill=(240, 240, 240))
    traffic_pole(d, stop_x + 40, 1080, green)
    y = 1560
    x_our = stop_x - 260 * sc
    gst = dict(lid=0.0, pupil='tiny', brow='annoyed', mouth='flat', ear_dy=-16, sweat=1.0, look=(30, -10))
    sst = dict(lid=0.6, brow='annoyed', mouth='smile_small', look=(-20, 0))
    if kind == 'road3':
        u = t - BREAK
        gst.update(brow='up', mouth='w', ear_dy=-36 * math.exp(-u * 3), look=(-30, 0))
    jolt = (-20 * math.exp(-(t - BREAK) * 5) * math.sin((t - BREAK) * 40)) if kind == 'road3' else 0.0
    car_side(img, x_our + jolt * sc, y, sc, (236, 238, 242), [('ginger', gst, 60, 0.42), ('shoko', sst, -70, 0.38)], 1, None, t)
    truck_side(img, x_our - 600 * sc, y, sc, t)
    n = {'road1': 2, 'road2': 9, 'road3': 4}[kind]
    for k_ in range(n):
        x = x_our - (1150 + 480 * k_) * sc
        if x > -400:
            car_side(img, x, y, sc, B.CAR_COLS[k_ % 7], [(('c1', 'c0', 'c3', 'c2', 'c4')[k_ % 5], 2 if kind != 'road3' else 1, 40, 0.30)], 1, None, t)
    d = ImageDraw.Draw(img)
    if kind == 'road3':
        u = t - BREAK
        for k_, (hx, hy) in enumerate(((x_our - 400 * sc, 1080), (200, 1000), (60, 1150), (420, 900))):
            if k_ > 0 and t < ZERO: continue
            ph = (t * 6 + k_ * 0.7) % 1.0
            for j in range(3):
                r = 40 + 50 * j + 30 * ph
                d.arc([S(hx - r), S(hy - r), S(hx + r), S(hy + r)], 200, 340, fill=(255, 230, 60), width=iw(8))
            d.text((S(hx), S(hy - 150 - 10 * ph)), 'טוּט!', font=font(S(64 if k_ == 0 else 50), 900), fill=(255, 230, 60), anchor='mm', stroke_width=iw(6), stroke_fill=(20, 20, 24))
        if u < 1.0:
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            for k_ in range(4): E(od, x_our + 200 * sc + k_ * 30, 1420 - 120 * u - k_ * 26, 70 + 50 * u, 50 + 30 * u, fill=(230, 230, 230, int(160 * (1 - u))))
            img.alpha_composite(ov)
    return img

def scene(t, i):
    name = shot(t)[0]
    if name.startswith('road'): img = scene_road(t, i, name)
    elif name == 'mirror': img = scene_mirror(t, i)
    else: img = scene_car(t, i)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= t < c_ + 0.5: E18.burst(img, (540, 1250), t - c_, (120, 255, 160) if c_ != CHK3 else (255, 220, 120), 170, 10, 0.4)
    if GOLDT <= t < BREAK: E18.confetti(img, t - GOLDT + 0.3)
    return img

# ------------------------------------------------------------------ overlays
CHIP_Y = 200
CHIPS = [('מראות', 820, CHK1), ('חגורה', 540, CHK2), ('הילוך', 260, CHK3)]
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
        d.text((cx + 22 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], outline=ink, width=4)

CLOCK_LABEL = ['ירוק', 'בעוד']
def clock_state(t):
    name = shot(t)[0]
    st = story_t(t)
    if name == 'rewind': return C.secs_left(st, ZERO), 'run', True
    s = C.secs_left(st, ZERO)
    return s, ('hot' if s <= 5 else 'run'), False

CAR_BG = ROAD_BG = SH_AV_BIG = PILL_EP = PILL_Q = PILL_SER = None
def init_all():
    global CAR_BG, ROAD_BG, SH_AV_BIG, PILL_EP, PILL_Q, PILL_SER
    B.init_all()
    CAR_BG = B.build_car_bg(); ROAD_BG = build_road_bg()
    st = SH.base(); st.update(mouth='grin', lid=0.5, look=(-10, 6), blush=0.8)
    lay = SH.draw(st, 0).crop((S(110), S(90), S(590), S(520)))
    SH_AV_BIG = lay.resize((S(150), int(S(150) * lay.height / lay.width)), Image.LANCZOS)
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_SER = HUD._pill(SERIES_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'car':
        z, cx, cy = 1.08 + 0.01 * pu, 560, 1060
        if a == 0.0:                                   # cold open: on the ginger, rigid, the truck big behind them
            z, cx, cy = 1.14 + 0.03 * t, 600, 1020
            if t < 0.3: z = 1.32 - 0.18 * ease_out(t / 0.3)
        elif a == T0: z, cx, cy = 1.10, 470, 1080       # the bet: Shoko + the note
        elif a == INT4:                                # the ritual → the peak: a slow push on the ginger
            k = ease_io(clamp((t - INT4) / (BREAK - INT4))); z, cx, cy = lerp(1.08, 1.30, k), lerp(560, 700, k), lerp(1060, 1000, k)
        elif a == TAG: z, cx, cy = 1.06, 540, 1080
    elif name == 'rewind': z, cx, cy = 1.10, 560 + 30 * math.sin(t * 90), 1060
    elif name == 'mirror': z, cx, cy = 1.0 + 0.04 * pu, 540, 1000
    elif name.startswith('road'): z, cx, cy = 1.0, 540, 960
    elif name == 'frozen': z, cx, cy = 1.12 + 0.03 * pu, 600, 1040
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    elif name == 'frozen': img = scene(FREEZE - 0.01, i)
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
    if t < COLD_END: frame = frame.rotate(3, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(236, 238, 242, 255))
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.24 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(50 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: B.rewind_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK, ROAD1, INT2, MIRROR, INT3, ROAD2, INT4, TAG):
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
            m.paste_center(frame, B.sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < ROAD1) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_SER, (40, 70 + PILL_EP.height + 6))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    if t < DUR - 0.25 and t < BREAK + 0.9:
        s, state, scr = clock_state(t)
        if t >= BREAK: s, state = (1, 'hot') if t < ZERO else (0, 'zero')
        C.draw(frame, CLOCK_LABEL, s, state, t, scr)
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio: voices + SFX + the comic underscore (music arm)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(46)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        add(voice, y, s0, 0.95 if i0 != 4 else 0.75)
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
    def horn(t0, f=420, ln=0.5, g=0.12):
        tt = tt_(ln); sig = np.sign(np.sin(2 * np.pi * f * tt)) * 0.5 + np.sign(np.sin(2 * np.pi * f * 1.26 * tt)) * 0.5
        add(sfx, m.lowpass(sig, 2500) * np.minimum(1, np.minimum(tt / 0.02, (ln - tt) / 0.03)), t0, g)
    add(sfx, thud(0.5), 0.0)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    idle = m.lowpass(nz(BREAK), 110) * (1 + 0.3 * np.sin(2 * np.pi * 14 * tt_(BREAK)))   # the engine idling
    add(sfx, idle, 0.0, 0.05)
    for t_ in (ROAD1, MIRROR, ROAD2, BREAK): whoosh(t_ + 0.05, 0.08, 0.25)
    check(CHK1, 0.15)
    add(sfx, m.highpass(nz(0.04), 2000) * np.exp(-tt_(0.04) * 80), CHK2 - 0.05, 0.4); check(CHK2, 0.16)   # the belt click
    add(sfx, thud(0.3), CHK3 - 0.05); check(CHK3, 0.2, True)                               # into first
    heartbeat(HOLD[0] + 0.02); heartbeat(HOLD[0] + 0.26, 0.5)
    horn(BREAK, 300, 0.9, 0.35); horn(BREAK, 225, 0.9, 0.25)                               # the truck's huge horn
    add(sfx, m.lowpass(nz(0.5), 200) * np.exp(-tt_(0.5) * 6), BREAK + 0.15, 0.3)          # the stall: a cough
    for k, (f, dt) in enumerate(((420, 0.0), (360, 0.12), (500, 0.25), (330, 0.38), (450, 0.55), (390, 0.75))):
        horn(ZERO + dt, f, 0.45 + 0.1 * (k % 2), 0.10)
    add(sfx, m.tone(82.4, 1.0, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), FREEZE - 0.2, 0.10)
    B.RW, B.PEAK = RW, PEAK                                                             # the underscore: ◀◀ → the peak
    mus = B.underscore(n)
    env = np.abs(voice); win = int(0.08 * SR)
    env = np.convolve(env, np.ones(win) / win, mode='same')
    duck = np.where(env > 0.01, 0.22, 1.0)
    sm = int(0.06 * SR); duck = np.convolve(duck, np.ones(sm) / sm, mode='same')
    mus = mus / (np.max(np.abs(mus)) + 1e-9) * 0.30 * duck
    out = voice + sfx + mus
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
        print('ROAD1', round(ROAD1, 2), 'INT2', round(INT2, 2), 'MIRROR', round(MIRROR, 2), 'INT3', round(INT3, 2), 'ROAD2', round(ROAD2, 2), 'INT4', round(INT4, 2))
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'PEAK', round(PEAK, 2), 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'ZERO', round(ZERO, 2), 'TAG', round(TAG, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        print('clock frame0', C.secs_left(story_t(0), ZERO), 'after rewind', C.secs_left(story_t(T0 + 0.01), ZERO), 'peak', C.secs_left(PEAK, ZERO))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, os.environ.get('SHEET', 'ep46_contact.png'))); print('ok'); return
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
