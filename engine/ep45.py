#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 45: פריקה וטעינה — Series 2 "שוקו והג׳ינג׳י", season 1 "על הכביש", ep2 (VOICED, built 26.11
under §P, ~23 s). CONTROL arm of the music experiment: no music at all (voices + SFX only).
Voices = voice bank 2026-11-23 lines 4500–4506 (Knox = Shoko, Benji = the ginger, Delia = Sharit; Gabi's picks 25.11:
4502 D, 4505 B), prepared by voice/ep45_prep.py.
Sets (fresh after ep44's car interior): a city street at night in front of a cinema (side view, the loading bay
"פריקה וטעינה" at the curb), one interior shot at night (the want), the cinema lobby (box office + the glass door to
the street), the popcorn counter, the dark auditorium, an insert of Shoko's phone.
Want: park and make the movie (they have circled for 20 minutes). Stakes: the movie (and the ginger's nerves).
Plant: in frame 0, behind them at the curb, a tow truck with its driver (Sharit) eating a sandwich, and the small
sign "גרירה מיידית" under the bay sign; seen again through the lobby's glass door mid-climb (the truck backing up to
their car, amber light) — never pointed at.
Clock: "הסרט בעוד 00:SS", real seconds from frame 0; it hits 00:00 when the lights dim (the peak).
Climb: the ginger: "עשרים דקות מסתובבים. הסרט מתחיל!" → Shoko swings into the bay ✓ חניה, out, keys twirling:
"חניה. בשנייה. תלמד." → the ginger: "זה 'פריקה וטעינה'!" → Shoko: "אני פורק. אותך." (pulls him out) →
tickets ✓ כרטיסים → a popcorn bucket bigger than the ginger ✓ gold פופקורן.
Peak: the seats, the lights dim at 00:00, the ginger relaxes for the first time: "טוב... אולי אתה צודק." heartbeat.
Break (plant_payoff): Shoko's phone lights up: a photo of his car on the tow truck, a selfie of Sharit in the cab,
her voice note "גררתי, מותק." — Shoko's rare panic face. Tag: the ginger munches, satisfied: "...אמרתי לך."

  python3 voice/ep45_prep.py
  python3 ep45.py times | test t1 t2 ... | render   -> out/ep45_prika.mp4
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
VDIR = os.path.join(HERE, 'voice', 'ep45', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); AMBER = (255, 170, 30)
SHARIT_SUB = (255, 182, 210); SHOKO_SUB = (190, 230, 120)
QUEUE = int(os.environ.get('QUEUE', '434'))
EP_LABEL = 'פרק 45'
SERIES_LABEL = 'שוקו והג׳ינג׳י'
OUTNAME = os.environ.get('OUTNAME', 'ep45_prika')
LIMIT = float(os.environ.get('LIMIT', '0'))
GINGER, SHOKO = B.GINGER, B.SHOKO

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
COLD_END = round(D[0] + 0.30, 2)            # cold open = 4500 "חניה. בשנייה. תלמד." (Shoko by the car in the bay)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # interior, night: "עשרים דקות מסתובבים. הסרט מתחיל!"
SWING = L[1] + D[1] + 0.06                  # cut out: the car swings into the bay
CHK1 = SWING + 0.95
L['0b'] = SWING + 1.25                      # Shoko out, keys twirling: "חניה. בשנייה. תלמד." (= the cold open)
SIGN = L['0b'] + D[0] + 0.04                # close: the ginger in the window, pointing up at the bay sign
L[2] = SIGN + 0.08                          # "זה 'פריקה וטעינה'!"
PULL = L[2] + D[2] + 0.06                   # wide: Shoko pulls him out by the paw
L[3] = PULL + 0.06                          # "אני פורק. אותך."
LOBBY = L[3] + D[3] + 0.05                  # the box office; through the glass door: the tow truck backing up (plant again)
CHK2 = LOBBY + 0.55
POP = LOBBY + 1.55                          # the popcorn counter: a bucket bigger than the ginger
CHK3 = POP + 0.55; GOLDT = CHK3 + 0.05
SEATS = POP + 1.30                          # the auditorium
ZERO = SEATS + 0.70                         # 00:00 — the lights dim
PEAK = ZERO
L[4] = ZERO + 0.25                          # "טוב... אולי אתה צודק."
HOLD = (L[4] + D[4] + 0.04, L[4] + D[4] + 0.52)
BREAK = HOLD[1]                             # Shoko's phone lights up
PHONE = BREAK + 0.05                        # insert: the photo of his car on the tow truck + Sharit's selfie
L[5] = BREAK + 0.10                         # the voice note: "גררתי, מותק."
SEATS2 = L[5] + D[5]                 # back: Shoko's rare panic face
L[6] = SEATS2 + 0.10                        # the ginger munches: "...אמרתי לך."
FREEZE = L[6] + D[6] + 0.03
DUR = round(FREEZE + 0.33, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (0, L['0b']), (2, L[2]), (3, L[3]), (4, L[4]), (5, L[5]), (6, L[6])]
SPEAKER = {0: 'shoko', 3: 'shoko', 1: 'cat', 2: 'cat', 4: 'cat', 6: 'cat', 5: 'sh'}

SUBS = {
    0: [['חניה. בשנייה.'], ['תלמד.']],
    1: [['עשרים דקות מסתובבים.'], ['הסרט מתחיל!']],
    2: [["זה 'פריקה וטעינה'!"]],
    3: [['אני פורק.'], ['אותך.']],
    4: [['טוב...'], ['אולי אתה צודק.']],
    5: [['גררתי, מותק.']],
    6: [['...אמרתי לך.']],
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
        if li == 4: b = min(b, HOLD[0])
        if li == 6: b = DUR - 0.25
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('ctx', 0.0, COLD_END), ('rewind', COLD_END, T0), ('car', T0, SWING), ('swing', SWING, L['0b']), ('ctx', L['0b'], SIGN),
         ('sign', SIGN, PULL), ('pull', PULL, LOBBY), ('lobby', LOBBY, POP), ('pop', POP, SEATS), ('seats', SEATS, PHONE),
         ('phone', PHONE, SEATS2), ('seats', SEATS2, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['אין חניה ליד הקולנוע?', 'יש. רק לשנייה']        # keyword: חניה / קולנוע (the pain in the viewer's words)
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

head, paw, shadow_paste, car_side = B.head, B.paw, B.shadow_paste, B.car_side

# ------------------------------------------------------------------ props
def keys_ring(d, c, t, sc=1.0):
    """a key ring spinning around Shoko's claw"""
    a0 = t * 14
    rx, ry = c[0] + 46 * sc * math.cos(a0), c[1] + 46 * sc * math.sin(a0) * 0.6
    d.ellipse([S(c[0] - 46 * sc), S(c[1] - 28 * sc), S(c[0] + 46 * sc), S(c[1] + 28 * sc)], outline=(210, 210, 220), width=iw(5))
    for k_ in range(2):
        a = a0 + k_ * 0.9
        p = (c[0] + 46 * sc * math.cos(a), c[1] + 28 * sc * math.sin(a))
        q = (p[0] + 60 * sc * math.cos(a), p[1] + 60 * sc * math.sin(a))
        line(d, [p, q], (236, 200, 90) if k_ == 0 else (200, 204, 214), 12)
        E(d, p[0], p[1], 14 * sc, 14 * sc, fill=(236, 200, 90) if k_ == 0 else (200, 204, 214), outline=(60, 60, 60), width=2)

def tickets(d, c, ang=0.0, sc=1.0):
    for k_ in range(2):
        cx, cy = c[0] + k_ * 26 * sc, c[1] - k_ * 18 * sc
        pts = xform([(-90 * sc, -46 * sc), (90 * sc, -46 * sc), (90 * sc, 46 * sc), (-90 * sc, 46 * sc)], cx, cy, ang + k_ * 6)
        poly(d, pts, fill=(255, 230, 120) if k_ else (255, 214, 64), outline=(120, 80, 10), width=4)
        tc = xform([(0, 0)], cx, cy, ang)[0]
        d.text((S(tc[0]), S(tc[1])), 'כרטיס', font=font(S(34 * sc), 900), fill=(120, 60, 10), anchor='mm')

def popcorn(d, c, sc=1.0, munch=0.0):
    """a giant striped bucket, popcorn heaped on top; c = bottom centre"""
    x, y = c; w0, w1, h = 300 * sc, 400 * sc, 620 * sc
    pts = [(x - w0 / 2, y), (x + w0 / 2, y), (x + w1 / 2, y - h), (x - w1 / 2, y - h)]
    poly(d, pts, fill=(250, 250, 248), outline=(120, 20, 26), width=7)
    for k_ in range(5):
        u0, u1 = k_ / 5 + 0.03, k_ / 5 + 0.13
        poly(d, [(lerp(x - w0 / 2, x + w0 / 2, u0), y), (lerp(x - w0 / 2, x + w0 / 2, u1), y),
                 (lerp(x - w1 / 2, x + w1 / 2, u1), y - h), (lerp(x - w1 / 2, x + w1 / 2, u0), y - h)], fill=(214, 38, 46))
    rng = random.Random(45)
    for k_ in range(46):
        px = x + rng.uniform(-w1 * 0.48, w1 * 0.48); py = y - h - rng.uniform(-10, 120) * sc * (1 - abs(px - x) / w1)
        r = rng.uniform(22, 34) * sc
        E(d, px, py, r, r * 0.85, fill=(255, 238, 170), outline=(200, 150, 60), width=3)
    d.rounded_rectangle([S(x - 110 * sc), S(y - h * 0.55), S(x + 110 * sc), S(y - h * 0.38)], radius=S(16 * sc), fill=(255, 214, 64), outline=(120, 20, 26), width=iw(4))
    d.text((S(x), S(y - h * 0.465)), 'ענק', font=font(S(54 * sc), 900), fill=(120, 20, 26), anchor='mm')

def sandwich(d, c, sc=1.0):
    x, y = c
    poly(d, [(x - 40 * sc, y), (x + 40 * sc, y - 10 * sc), (x + 36 * sc, y + 18 * sc), (x - 36 * sc, y + 24 * sc)], fill=(236, 200, 140), outline=(140, 100, 60), width=3)
    line(d, [(x - 36 * sc, y + 10 * sc), (x + 36 * sc, y + 3 * sc)], (90, 170, 70), 5)

def tow_truck(img, x, y, sc=1.0, t=0.0, boom=0.0, sharit=True, lit=True):
    """side view, cab on the left (facing left), the boom + hook on the right. x,y = middle of the wheels line"""
    d = ImageDraw.Draw(img)
    YEL, YEL_D = (240, 176, 40), (170, 110, 20)
    # chassis + bed
    d.rounded_rectangle([S(x - 360 * sc), S(y - 120 * sc), S(x + 330 * sc), S(y - 20 * sc)], radius=S(14 * sc), fill=YEL_D, outline=(30, 24, 10), width=iw(4))
    # cab
    poly(d, [(x - 380 * sc, y - 20 * sc), (x - 380 * sc, y - 220 * sc), (x - 320 * sc, y - 330 * sc), (x - 120 * sc, y - 330 * sc), (x - 110 * sc, y - 20 * sc)], fill=YEL, outline=(30, 24, 10), width=5)
    poly(d, [(x - 360 * sc, y - 220 * sc), (x - 312 * sc, y - 310 * sc), (x - 140 * sc, y - 310 * sc), (x - 136 * sc, y - 220 * sc)], fill=(150, 186, 214) if lit else (60, 76, 96))
    if sharit:   # Sharit in the cab, eating a sandwich
        av = SH_AV_BIG; sz = (int(av.width * sc * 0.95), int(av.height * sc * 0.95))
        img.alpha_composite(av.resize(sz, Image.BICUBIC), (int(S(x - 240 * sc) - sz[0] / 2), int(S(y - 262 * sc) - sz[1] / 2)))
        d = ImageDraw.Draw(img)
        sandwich(d, (x - 300 * sc, y - 232 * sc + 6 * sc * math.sin(t * 9)), sc * 1.1)
    d.text((S(x - 245 * sc), S(y - 130 * sc)), 'גרירה', font=font(S(46 * sc), 900), fill=(30, 24, 10), anchor='mm')
    # amber light bar
    on = (int(t * 5) % 2 == 0) and lit
    d.rounded_rectangle([S(x - 300 * sc), S(y - 360 * sc), S(x - 150 * sc), S(y - 330 * sc)], radius=S(8 * sc), fill=AMBER if on else (120, 80, 20), outline=(30, 24, 10), width=iw(3))
    if on:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); E(ImageDraw.Draw(ov), x - 225 * sc, y - 345 * sc, 150 * sc, 80 * sc, fill=AMBER + (60,)); img.alpha_composite(ov)
        d = ImageDraw.Draw(img)
    # the boom + hook (rises with boom 0..1)
    bx0, by0 = x + 40 * sc, y - 120 * sc
    ang = math.radians(-14 - 26 * boom)
    bx1, by1 = bx0 + 330 * sc * math.cos(ang), by0 + 330 * sc * math.sin(ang)
    line(d, [(bx0, by0), (bx1, by1)], (60, 60, 66), int(26 * sc) + 2)
    line(d, [(bx1, by1), (bx1, by1 + (90 + 60 * (1 - boom)) * sc)], (30, 30, 34), 5)
    d.arc([S(bx1 - 22 * sc), S(by1 + (90 + 60 * (1 - boom)) * sc - 10 * sc), S(bx1 + 22 * sc), S(by1 + (130 + 60 * (1 - boom)) * sc)], 0, 270, fill=(30, 30, 34), width=iw(7))
    for wx in (-270, 220):
        E(d, x + wx * sc, y, 60 * sc, 60 * sc, fill=(24, 24, 28)); E(d, x + wx * sc, y, 26 * sc, 26 * sc, fill=(160, 160, 170))
    E(d, x - 384 * sc, y - 80 * sc, 12 * sc, 18 * sc, fill=(255, 246, 190))

# ------------------------------------------------------------------ the street at night (side view)
CURB_Y = 1310; CAR_Y = 1520; CAR_X = 650; TRUCK_X = 330; POLE_X = 470
def build_street_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, 1100, 8):
        v = y / 1100
        d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(14, 40, v)), int(lerp(18, 44, v)), int(lerp(46, 84, v))))
    rng = random.Random(4)
    for k_ in range(40): E(d, rng.uniform(0, W), rng.uniform(20, 500), 2.5, 2.5, fill=(230, 230, 250))
    # buildings (left) with lit windows
    for x, h, c in ((-40, 760, (46, 46, 66)), (230, 640, (56, 54, 74)), (440, 820, (42, 44, 62))):
        d.rectangle([S(x), S(CURB_Y - 160 - h), S(x + 230), S(CURB_Y - 160)], fill=c)
        for r_ in range(int(h / 110)):
            for c_ in range(2):
                on = rng.random() < 0.55
                d.rectangle([S(x + 40 + c_ * 92), S(CURB_Y - 160 - h + 40 + r_ * 110), S(x + 96 + c_ * 92), S(CURB_Y - 160 - h + 96 + r_ * 110)],
                            fill=(255, 214, 120) if on else (30, 34, 50))
    # the cinema (right): facade, marquee with bulbs, glass doors
    d.rectangle([S(640), S(260), S(W + 40), S(CURB_Y - 160)], fill=(120, 30, 46))
    d.rectangle([S(660), S(300), S(W + 40), S(560)], fill=(30, 22, 30), outline=(250, 210, 120), width=iw(8))
    for k_ in range(15):
        E(d, 676 + k_ * 28, 312, 7, 7, fill=(255, 236, 160)); E(d, 676 + k_ * 28, 548, 7, 7, fill=(255, 236, 160))
    d.text((S(870), S(430)), 'קולנוע', font=font(S(120), 900), fill=(255, 220, 120), anchor='mm')
    for k_ in range(3):
        d.rectangle([S(700 + k_ * 130), S(720), S(810 + k_ * 130), S(CURB_Y - 160)], fill=(250, 214, 150), outline=(60, 20, 30), width=iw(6))
        d.rectangle([S(700 + k_ * 130), S(720), S(810 + k_ * 130), S(760)], fill=(255, 240, 200))
    # sidewalk + curb (the bay: red-white? no — Israeli loading bay = yellow-white? kept red-yellow stripes generic)
    d.rectangle([0, S(CURB_Y - 160), W * K, S(CURB_Y)], fill=(96, 94, 104))
    d.rectangle([0, S(CURB_Y), W * K, H * K], fill=(44, 46, 56))
    for k_ in range(14):                                   # the painted curb of the bay
        col = (240, 200, 40) if k_ % 2 else (240, 240, 240)
        d.rectangle([S(380 + k_ * 50), S(CURB_Y - 16), S(430 + k_ * 50), S(CURB_Y + 8)], fill=col)
    for k_ in range(9): d.rectangle([S(k_ * 150 - 20), S(1760), S(k_ * 150 + 70), S(1774)], fill=(210, 210, 210))
    # street lamp glow
    d.rectangle([S(580), S(500), S(596), S(CURB_Y - 150)], fill=(40, 40, 48))
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for r in (420, 300, 190): E(od, 588, 520, r, r * 0.8, fill=(255, 220, 150, 26))
    img.alpha_composite(ov)
    img = img.filter(ImageFilter.GaussianBlur(S(1.2)))
    return img

def bay_sign(d, sc=1.0, glow=0.0):
    """the pole on the sidewalk: 'פריקה וטעינה' + the small 'גרירה מיידית' (plant)"""
    x = POLE_X
    d.rectangle([S(x - 8), S(820), S(x + 8), S(CURB_Y - 150)], fill=(150, 150, 160))
    d.rounded_rectangle([S(x - 130), S(820), S(x + 130), S(1000)], radius=S(12), fill=(250, 250, 250), outline=(30, 60, 140), width=iw(7))
    # a little truck icon
    d.rectangle([S(x + 30), S(846), S(x + 100), S(884)], fill=(30, 60, 140)); d.rectangle([S(x + 6), S(860), S(x + 30), S(884)], fill=(30, 60, 140))
    E(d, x + 20, 888, 8, 8, fill=(30, 60, 140)); E(d, x + 86, 888, 8, 8, fill=(30, 60, 140))
    d.text((S(x - 46), S(866)), 'פריקה', font=font(S(40), 900), fill=(30, 60, 140), anchor='mm')
    d.text((S(x), S(950)), 'וטעינה', font=font(S(52), 900), fill=(30, 60, 140), anchor='mm')
    d.rounded_rectangle([S(x - 110), S(1012), S(x + 110), S(1062)], radius=S(8), fill=(250, 250, 250), outline=(200, 30, 40), width=iw(5))
    d.text((S(x), S(1037)), 'גרירה מיידית', font=font(S(30), 900), fill=(200, 30, 40), anchor='mm')

def our_car(img, x, y, t, sc=1.0, faces=None, door=0.0):
    car_side(img, x, y, sc, (236, 238, 242), faces or [], -1, None, t)

def stand(img, x, yf, pal, st, i, f=0.62, props=False, wob=0.0, rot=0.0, arm=None, lean=0.0):
    """a standing cat seen from the side-ish front: feet at yf; arm = fn(d, shoulder) for a raised paw"""
    d = ImageDraw.Draw(img)
    bx, by = x + lean * 30, yf - 230
    for sx in (-1, 1): capsule(d, (bx + sx * 50, by + 120), (x + sx * 60, yf - 10), 54, pal['FUR'], pal['OUT'], 4)
    E(d, bx, by, 150, 200, fill=pal['FUR'], outline=pal['OUT'], width=6)
    E(d, bx, by + 30, 72, 130, fill=pal['CREAM'])
    if arm: arm(d, (bx + 110, by - 90))
    head(img, st, i, bx + lean * 20, by - 250, f, rot, pal, props=props, wob=wob)

# ------------------------------------------------------------------ states
def ginger_state(t):
    st = E3.base_state(); st.update(red=0.0, blush=0.2, mouth='flat')
    rot, dy = 0.0, 0.0
    s_t = story_t(t)
    v = voice_v(s_t, 'cat')
    if t < SWING and t >= T0:                                 # the want: "עשרים דקות מסתובבים. הסרט מתחיל!"
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=mouth_of(t, 'cat', 'w', 'w'), ear_dy=-24, sweat=1.0, look=(26, 4))
        rot = 5 * math.sin(t * 9); dy = -16 * v
    elif s_t < SIGN:                                          # the cold open / in context: panicking in the window
        st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', ear_dy=-20, sweat=1.0, look=(30, -14))
        rot = 4 * math.sin(t * 11)
    elif t < PULL:                                            # "זה 'פריקה וטעינה'!" — pointing at the sign
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=mouth_of(t, 'cat', 'w', 'w'), ear_dy=-30, sweat=1.0, look=(-30, -26))
        rot = 6 * math.sin(t * 16); dy = -18 * v
    elif t < LOBBY:                                           # pulled out
        st.update(lid=0.0, pupil='big', brow='sad', mouth='w', ear_dy=-10, sweat=0.9, look=(20, 0))
        rot = -10
    elif t < POP:                                             # tickets: a first small smile
        st.update(lid=0.2, pupil='big', brow='up', mouth='smile_small', ear_dy=-6, sweat=0.5, look=(14, -10))
    elif t < SEATS:                                           # the bucket: amazed
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-18, sweat=0.0, look=(0, -24), blush=0.7)
    elif t < BREAK:                                           # THE PEAK: the lights dim, he relaxes for the first time
        k = clamp((t - ZERO) / 0.5)
        st.update(lid=lerp(0.2, 0.62, k), pupil='normal', brow='none', mouth=mouth_of(t, 'cat', 'smile_small', 'smile_small'), ear_dy=0, ear_droop=0.2 * k, sweat=0.0, look=(10, 0), blush=0.5)
        dy = 10 * k; rot = -4 * k
    else:                                                     # the tag: munching, satisfied, eyes closed
        st.update(eye_mode='closed', brow='none', mouth='smile' if int(t * 8) % 2 else 'flat', ear_dy=0, sweat=0.0, blush=0.6)
        if t >= L[6]: st.update(mouth=mouth_of(t, 'cat', 'smile_small', 'smile_small'))
        rot = -6; dy = 6 * abs(math.sin(t * 8))
    return st, rot, dy

def shoko_state(t):
    st = E3.base_state(); st.update(lid=0.55, brow='annoyed', mouth='smile_small', look=(-8, 4), red=0.0, blush=0.0)
    rot, dy = 0.0, 0.0
    s_t = story_t(t)
    v = voice_v(s_t, 'shoko')
    if v > 0.12: st['mouth'] = 'w' if v > 0.32 else 'smile_small'
    if T0 <= t < SWING: st.update(lid=0.62, look=(-6, 2))
    elif s_t < SIGN: st.update(lid=0.5, look=(-20, 4)); rot = 3 * math.sin(t * 2)
    elif t < LOBBY: st.update(lid=0.55, look=(-26, 0))
    elif t < SEATS: st.update(lid=0.5, look=(-20, 0), mouth='goofy' if v < 0.12 else st['mouth'])
    elif t < BREAK: st.update(lid=0.66, look=(-10, 4), mouth='goofy')
    else:                                                     # the rare panic face
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', ear_dy=-30 * math.exp(-u * 2), sweat=1.0, look=(14, 20), blush=0.0,
                  twitch=(int(t * 12) % 2 == 0))
        dy = -24 * math.exp(-u * 5)
    return st, rot, dy

# ------------------------------------------------------------------ scenes
def scene_street(t, i, kind):
    img = STREET_BG.copy(); d = ImageDraw.Draw(img)
    s_t = story_t(t)
    truck_boom = 0.0
    tow_truck(img, TRUCK_X, CAR_Y - 10, 0.8, t, truck_boom)
    d = ImageDraw.Draw(img)
    bay_sign(d)
    gst, grot, gdy = ginger_state(t)
    sst, srot, sdy = shoko_state(t)
    if kind == 'swing':                                       # the car swings in from the road
        u = clamp((t - SWING) / 0.9)
        k = ease_out(u)
        x = lerp(1300, CAR_X, k); y = lerp(1760, CAR_Y, ease_io(u)); sc = lerp(1.15, 1.0, k)
        car_side(img, x, y, sc, (236, 238, 242), [('shoko', dict(lid=0.6, brow='annoyed', mouth='smile_small', look=(-20, 0)), -60, 0.38),
                                                 ('ginger', dict(lid=0.0, pupil='tiny', brow='up', mouth='w', ear_dy=-20, sweat=1.0, look=(-20, -10)), 70, 0.40)], -1, None, t)
        d = ImageDraw.Draw(img)
        if u < 1:
            for k_ in range(5):
                yy = 1600 + k_ * 34; xx = x + 260 + k_ * 40
                line(d, [(xx, yy), (xx + 180, yy)], (220, 220, 230), 5)
        if t >= CHK1 - 0.05:                                   # Shoko gets out, keys first
            stand(img, 930, 1820, SHOKO, sst, i, 0.60, props=True, wob=6 * math.sin(t * 3), arm=lambda d_, sh_: (capsule(d_, sh_, (sh_[0] + 60, sh_[1] - 150), 54, SHOKO['FUR'], SHOKO['OUT'], 4), paw(d_, (sh_[0] + 60, sh_[1] - 150), SHOKO, 0, 0.7), keys_ring(d_, (sh_[0] + 60, sh_[1] - 230), t, 0.9)))
    else:
        faces = []
        if kind in ('ctx', 'sign'): faces = [('ginger', gst, 70, 0.46 if kind == 'ctx' else 0.50)]
        car_side(img, CAR_X, CAR_Y, 1.0, (236, 238, 242), faces, -1, None, t)
        d = ImageDraw.Draw(img)
        if kind == 'sign':                                     # his paw out of the window, pointing up at the sign
            tip = (CAR_X - 210 + 10 * math.sin(t * 14), 1160 - 12 * abs(math.sin(t * 9)))
            capsule(d, (CAR_X + 40, 1330), tip, 60, GINGER['FUR'], GINGER['OUT'], 4); paw(d, tip, GINGER, -40, 0.7)
        if kind in ('ctx', 'sign'):
            stand(img, 870, 1820, SHOKO, sst, i, 0.60, props=True, wob=6 * math.sin(t * 3), rot=srot,
                  arm=lambda d_, sh_: (capsule(d_, sh_, (sh_[0] + 60, sh_[1] - 150), 54, SHOKO['FUR'], SHOKO['OUT'], 4), paw(d_, (sh_[0] + 60, sh_[1] - 150), SHOKO, 0, 0.7), keys_ring(d_, (sh_[0] + 60, sh_[1] - 230), t, 0.9)))
        elif kind == 'pull':                                   # Shoko drags the ginger out by the paw toward the cinema
            u = clamp((t - PULL) / (LOBBY - PULL))
            sx_ = lerp(760, 1000, u); gx_ = lerp(420, 720, ease_out(u))
            stand(img, gx_, 1830, GINGER, gst, i, 0.58, rot=grot, lean=0.8)
            stand(img, sx_, 1820, SHOKO, sst, i, 0.60, props=True, wob=6 * math.sin(t * 3), lean=-0.3)
            d = ImageDraw.Draw(img)
            capsule(d, (sx_ - 100, 1500), (gx_ + 110, 1480), 50, SHOKO['FUR'], SHOKO['OUT'], 4)
            capsule(d, (gx_ + 90, 1560), (gx_ + 110, 1480), 50, GINGER['FUR'], GINGER['OUT'], 4); paw(d, (gx_ + 110, 1480), SHOKO, 90, 0.6)
    if CHK1 <= t < CHK1 + 0.5: E18.burst(img, (CAR_X, 1250), t - CHK1, (120, 255, 160), 170, 10, 0.4)
    return img

def build_lobby_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W * K, H * K], fill=(92, 30, 44))                                   # wall
    for k_ in range(6): d.rectangle([S(k_ * 200), 0, S(k_ * 200 + 18), S(1250)], fill=(110, 40, 56))
    d.rectangle([0, S(1250), W * K, H * K], fill=(150, 34, 46))                             # carpet
    for k_ in range(18): E(d, 60 * k_ + 30, 1320 + 40 * (k_ % 3), 14, 8, fill=(190, 150, 60))
    # the glass entrance door (left): the night street behind it, framed
    d.rectangle([S(40), S(380), S(460), S(1250)], fill=(14, 18, 40), outline=(220, 190, 120), width=iw(14))
    line(d, [(250, 380), (250, 1250)], (220, 190, 120), 10)
    # the box office counter (right)
    d.rectangle([S(560), S(420), S(W), S(760)], fill=(30, 22, 30), outline=(250, 210, 120), width=iw(6))
    d.text((S(820), S(500)), 'קופות', font=font(S(80), 900), fill=(255, 220, 120), anchor='mm')
    d.rectangle([S(600), S(560), S(W - 40), S(1000)], fill=(190, 214, 230))
    d.rectangle([S(560), S(1000), S(W), S(1250)], fill=(70, 40, 40), outline=(40, 20, 20), width=iw(6))
    return img

def glass_view(img, t):
    """through the lobby door: the tow truck backs up to their car (the plant, seen again; never pointed at)"""
    lay = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    u = clamp((t - LOBBY) / 1.4)
    car_side(lay, 170, 1120, 0.50, (236, 238, 242), [], -1, None, t)
    tow_truck(lay, lerp(-40, 30, ease_out(u)) + 360, 1120, 0.44, t, boom=0.6 * u, sharit=True)
    mask = Image.new('L', lay.size, 0); ImageDraw.Draw(mask).rectangle([S(54), S(394), S(446), S(1236)], fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(mask))))
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for xa in (100, 300): poly(od, [(xa, 394), (xa + 60, 394), (xa - 40, 1236), (xa - 100, 1236)], fill=(255, 255, 255, 26))
    img.alpha_composite(ov)
    line(ImageDraw.Draw(img), [(250, 380), (250, 1250)], (220, 190, 120), 10)

def scene_lobby(t, i):
    img = LOBBY_BG.copy()
    glass_view(img, t)
    d = ImageDraw.Draw(img)
    E13.paste_sprite(img, 'c2', 2, 820, 780, 0.55)                                         # the bored cashier behind the glass
    d = ImageDraw.Draw(img)
    gst, grot, gdy = ginger_state(t); sst, srot, sdy = shoko_state(t)
    for hx, pal in ((420, GINGER), (790, SHOKO)):
        E(d, hx, 1720, 230, 300, fill=pal['FUR'], outline=pal['OUT'], width=7); E(d, hx, 1760, 110, 210, fill=pal['CREAM'])
    head(img, gst, i, 420, 1280 + gdy, 0.82, grot, GINGER)
    head(img, sst, i, 790, 1270 + sdy, 0.82, srot, SHOKO, props=True, wob=6 * math.sin(t * 3))
    d = ImageDraw.Draw(img)
    tk = CHK2 - 0.25
    up = ease_out(clamp((t - tk) / 0.3))
    tc = (lerp(840, 610, up), lerp(900, 1120, up))
    capsule(d, (790 - 120, 1600), (tc[0] + 20, tc[1] + 70), 74, SHOKO['FUR'], SHOKO['OUT'], 4)
    tickets(d, tc, -8 + 4 * math.sin(t * 6), 1.0)
    paw(d, (tc[0] + 20, tc[1] + 70), SHOKO, 0, 0.8)
    if CHK2 <= t < CHK2 + 0.5: E18.burst(img, tc, t - CHK2, (120, 255, 160), 170, 10, 0.4)
    return img

def scene_pop(t, i):
    img = LOBBY_BG.copy(); d = ImageDraw.Draw(img)
    d.rectangle([0, S(1000), W * K, S(1250)], fill=(70, 40, 40), outline=(40, 20, 20), width=iw(6))       # the snack counter
    d.rectangle([0, S(420), W * K, S(760)], fill=(30, 22, 30), outline=(250, 210, 120), width=iw(6))
    d.text((S(540), S(520)), 'פופקורן', font=font(S(100), 900), fill=(255, 220, 120), anchor='mm')
    E13.paste_sprite(img, 'c4', 0, 230, 860, 0.5)
    d = ImageDraw.Draw(img)
    gst, grot, gdy = ginger_state(t); sst, srot, sdy = shoko_state(t)
    u = ease_out(clamp((t - POP) / 0.45))
    for hx, pal in ((470, GINGER), (860, SHOKO)):
        E(d, hx, 1760, 220, 290, fill=pal['FUR'], outline=pal['OUT'], width=7); E(d, hx, 1800, 105, 200, fill=pal['CREAM'])
    head(img, sst, i, 860, 1300 + sdy, 0.70, srot, SHOKO, props=True, wob=6 * math.sin(t * 3))
    head(img, gst, i, 470, 1340 + gdy, 0.74, grot, GINGER)
    d = ImageDraw.Draw(img)
    bc = (lerp(470, 470, u), lerp(1100, 1880, u))                                         # the bucket lands in his arms
    popcorn(d, bc, 1.15 + 0.05 * math.sin(t * 3))
    for sx in (-1, 1):
        capsule(d, (470 + sx * 180, 1700), (470 + sx * 200, 1560), 64, GINGER['FUR'], GINGER['OUT'], 4); paw(d, (470 + sx * 200, 1560), GINGER, sx * 70, 0.7)
    if CHK3 <= t < CHK3 + 0.5: E18.burst(img, (470, 900), t - CHK3, (255, 220, 120), 200, 12, 0.4)
    return img

def build_seats_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W * K, H * K], fill=(54, 26, 40))
    d.rectangle([S(60), S(140), S(W - 60), S(560)], fill=(214, 226, 240), outline=(30, 20, 26), width=iw(10))   # the screen
    for k_ in range(2): d.rectangle([S(-40 + k_ * (W - 60)), S(80), S(100 + k_ * (W - 60)), S(700)], fill=(140, 20, 34))   # curtains
    for r_ in range(3):                                       # rows of red seats in front
        y = 900 + r_ * 170
        for k_ in range(8):
            x = k_ * 150 - 40 + (r_ % 2) * 70
            d.rounded_rectangle([S(x), S(y), S(x + 128), S(y + 150)], radius=S(26), fill=(150 - r_ * 10, 28, 40), outline=(60, 10, 18), width=iw(4))
    return img

def scene_seats(t, i):
    img = SEATS_BG.copy(); d = ImageDraw.Draw(img)
    for k_, (x, nm) in enumerate(((140, 'c0'), (420, 'c3'), (900, 'c1'))):                 # a few heads in the rows in front
        E13.paste_sprite(img, nm, 2, x, 880, 0.34)
    d = ImageDraw.Draw(img)
    gst, grot, gdy = ginger_state(t); sst, srot, sdy = shoko_state(t)
    for hx in (330, 780):                                     # their two seats
        d.rounded_rectangle([S(hx - 240), S(1120), S(hx + 240), S(1920)], radius=S(70), fill=(166, 30, 44), outline=(60, 10, 18), width=iw(6))
    for hx, pal in ((330, GINGER), (780, SHOKO)):
        E(d, hx, 1720, 220, 290, fill=pal['FUR'], outline=pal['OUT'], width=7); E(d, hx, 1760, 105, 200, fill=pal['CREAM'])
    head(img, sst, i, 780, 1250 + sdy, 0.80, srot, SHOKO, props=True, wob=6 * math.sin(t * 3))
    head(img, gst, i, 330, 1270 + gdy, 0.80, grot, GINGER)
    d = ImageDraw.Draw(img)
    popcorn(d, (300, 2010), 0.80)
    for sx in (-1, 1): paw(d, (300 + sx * 130, 1720), GINGER, sx * 60, 0.75)
    if t >= SEATS2 or t >= L[6]:                               # the tag: a paw full of popcorn to the mouth
        u = (t * 3) % 1.0
        pc = (lerp(380, 400, u), lerp(1500, 1420, u))
        paw(d, pc, GINGER, -30, 0.75)
        for k_ in range(3): E(d, pc[0] - 20 + k_ * 20, pc[1] - 40, 18, 15, fill=(255, 238, 170), outline=(200, 150, 60), width=2)
    # Shoko's phone (in his paw by the chin) — lights up at the break
    if t >= BREAK - 0.05:
        pc = (900, 1500)
        d.rounded_rectangle([S(pc[0] - 60), S(pc[1] - 110), S(pc[0] + 60), S(pc[1] + 110)], radius=S(16), fill=(18, 18, 22))
        d.rounded_rectangle([S(pc[0] - 50), S(pc[1] - 98), S(pc[0] + 50), S(pc[1] + 98)], radius=S(10), fill=(230, 240, 255))
        paw(d, (pc[0] - 20, pc[1] + 90), SHOKO, 20, 0.75)
    # the lights: warm before 00:00, dim after; the phone glows on Shoko's face
    dim = clamp((t - ZERO) / 0.5)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rectangle([0, 0, W * K, H * K], fill=(6, 4, 14, int(20 + 90 * dim)))
    img.alpha_composite(ov)
    if t >= BREAK - 0.05:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for r in (420, 300, 190): E(od, 860, 1350, r, r, fill=(180, 210, 255, 30))
        img.alpha_composite(ov)
    if dim > 0:                                               # the screen lights the room a little
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rectangle([S(60), S(140), S(W - 60), S(560)], fill=(240, 248, 255, int(120 * dim)))
        img.alpha_composite(ov)
    return img

def scene_phone(t, i):
    img = SEATS_BG.copy()
    img.alpha_composite(Image.new('RGBA', img.size, (4, 4, 10, 220)))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 150, 300, 930, 1720
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(70), fill=(16, 16, 20), outline=(60, 60, 70), width=iw(6))
    sx0, sy0, sx1, sy1 = x0 + 30, y0 + 40, x1 - 30, y1 - 40
    d.rounded_rectangle([S(sx0), S(sy0), S(sx1), S(sy1)], radius=S(46), fill=(236, 238, 244))
    d.rectangle([S(sx0), S(sy0 + 30), S(sx1), S(sy0 + 140)], fill=(40, 44, 56))
    E(d, sx1 - 80, sy0 + 85, 40, 40, fill=(255, 150, 190))
    d.text((S(sx1 - 140), S(sy0 + 85)), 'שרית', font=font(S(48), 900), fill=WHITE, anchor='rm')
    # the photo: their car up on the tow truck, Sharit's selfie in the cab
    px0, py0, px1, py1 = sx0 + 40, sy0 + 180, sx1 - 40, sy0 + 920
    photo = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0)); pd = ImageDraw.Draw(photo)
    pd.rectangle([S(px0), S(py0), S(px1), S(py1)], fill=(20, 26, 54))
    pd.rectangle([S(px0), S(py0 + 560), S(px1), S(py1)], fill=(50, 50, 60))
    tow_truck(photo, px0 + 300, py0 + 640, 0.62, 0.0, boom=1.0, sharit=False)
    car = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    car_side(car, 540, 960, 0.62, (236, 238, 242), [], -1, None, t)
    car = car.rotate(16, resample=Image.BICUBIC, center=(S(540), S(960)))
    photo.alpha_composite(car, (int(S(px0 + 470 - 540)), int(S(py0 + 470 - 960))))
    av = SH_AV_BIG; sz = (int(av.width * 2.1), int(av.height * 2.1))
    photo.alpha_composite(av.resize(sz, Image.BICUBIC), (int(S(px0 + 170) - sz[0] / 2), int(S(py0 + 230) - sz[1] / 2)))
    pd = ImageDraw.Draw(photo)
    capsule(pd, (px0 + 260, py0 + 330), (px0 + 330, py0 + 170), 30, SH.SKIN, SH.SKIN_O, 3)       # the selfie arm, peace sign
    for dx in (-10, 12): capsule(pd, (px0 + 330, py0 + 170), (px0 + 330 + dx, py0 + 110), 12, SH.SKIN, SH.SKIN_O, 2)
    mask = Image.new('L', photo.size, 0); ImageDraw.Draw(mask).rounded_rectangle([S(px0), S(py0), S(px1), S(py1)], radius=S(26), fill=255)
    photo.putalpha(Image.fromarray(np.minimum(np.array(photo.split()[3]), np.array(mask))))
    u = ease_out(clamp((t - PHONE) / 0.2))
    if u < 1: photo = photo.resize(photo.size).transform(photo.size, Image.AFFINE, (1, 0, 0, 0, 1, int(S(60) * (1 - u))))
    img.alpha_composite(photo)
    d = ImageDraw.Draw(img)
    # the voice note bubble
    by0 = py1 + 50
    d.rounded_rectangle([S(sx0 + 40), S(by0), S(sx1 - 40), S(by0 + 140)], radius=S(70), fill=(255, 214, 230), outline=(200, 120, 160), width=iw(4))
    prog = clamp((t - L[5]) / D[5])
    E(d, sx1 - 110, by0 + 70, 44, 44, fill=(200, 60, 110))
    poly(d, [(sx1 - 124, by0 + 46), (sx1 - 124, by0 + 94), (sx1 - 88, by0 + 70)], fill=WHITE)
    env = META[5]['env']
    for k_ in range(26):
        x = sx1 - 180 - k_ * 18
        v = env[min(len(env) - 1, int(k_ / 26 * len(env)))]
        hh = 12 + 70 * v
        played = (k_ / 26) <= prog
        d.rounded_rectangle([S(x - 5), S(by0 + 70 - hh / 2), S(x + 5), S(by0 + 70 + hh / 2)], radius=S(5), fill=(200, 60, 110) if played else (230, 160, 190))
    d.text((S(sx0 + 100), S(by0 + 70)), '0:01', font=font(S(36), 800), fill=(150, 70, 110), anchor='mm')
    d.text((S(540), S(py0 - 0)), '', font=font(S(10), 400), fill=WHITE)
    return img

def scene_car(t, i):
    """the one interior shot, at night (the want)"""
    img = CAR_BG.copy(); d = ImageDraw.Draw(img)
    for hx, pal in ((B.GHX, GINGER), (B.SHX, SHOKO)):
        E(d, hx, 1560, 250, 320, fill=pal['FUR'], outline=pal['OUT'], width=7)
        E(d, hx, 1600, 120, 230, fill=pal['CREAM'])
        line(d, [(hx + 170, 1250), (hx - 150, 1600)], (30, 30, 34), 26)
    gst, grot, gdy = ginger_state(t); sst, srot, sdy = shoko_state(t)
    head(img, gst, i, B.GHX, B.GHY + gdy, B.F, grot, GINGER)
    head(img, sst, i, B.SHX, B.SHY + sdy, B.F, srot, SHOKO, props=True, wob=6 * math.sin(t * 3))
    d = ImageDraw.Draw(img)
    tip = (560 + 16 * math.sin(t * 13), 1120 - 12 * abs(math.sin(t * 8)))      # the ginger points at the clock on the dash
    capsule(d, (B.GHX + 120, 1420), tip, 80, GINGER['FUR'], GINGER['OUT'], 4); paw(d, tip, GINGER, -50, 0.85)
    # dash + wheel + body (night)
    poly(d, [(0, 1430), (W, 1430), (W, 1600), (0, 1600)], fill=(24, 26, 30))
    d.rectangle([0, S(1420), W * K, S(1446)], fill=(44, 46, 52))
    wc = (790, 1560); r = 175
    d.arc([S(wc[0] - r), S(wc[1] - r), S(wc[0] + r), S(wc[1] + r)], 180, 360, fill=(14, 14, 18), width=iw(36))
    BODY = (170, 172, 180); BODY_D = (120, 124, 134)
    d.rectangle([0, 0, W * K, S(250)], fill=BODY); d.rectangle([0, S(228), W * K, S(256)], fill=BODY_D)
    poly(d, [(0, 250), (120, 250), (30, 1450), (0, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(W, 250), (W - 120, 250), (W - 30, 1450), (W, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(-40, 1600), (W + 40, 1600), (W + 40, 1960), (-40, 1960)], fill=BODY)
    wp = (760 + 30 * math.sin(t * 3), 1392)                                       # Shoko turns the wheel one-pawed
    capsule(d, (B.SHX + 60, 1640), wp, 82, SHOKO['FUR'], SHOKO['OUT'], 4); paw(d, wp, SHOKO, 10, 0.85)
    return img

def build_car_bg():
    img = B.build_car_bg()
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 130, 540, 950, 820                                       # rear window at night: a row of parked cars, "מלא"
    d.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=(18, 22, 46))
    for k_ in range(6):
        x = x0 + 20 + k_ * 140
        d.rounded_rectangle([S(x), S(700), S(x + 120), S(790)], radius=S(16), fill=B.CAR_COLS[k_ % 7])
        E(d, x + 20, 740, 8, 6, fill=(255, 60, 50)); E(d, x + 100, 740, 8, 6, fill=(255, 60, 50))
    d.rounded_rectangle([S(430), S(590), S(650), S(660)], radius=S(10), fill=(200, 30, 40))
    d.text((S(540), S(625)), 'חניון מלא', font=font(S(42), 900), fill=WHITE, anchor='mm')
    img.alpha_composite(Image.new('RGBA', img.size, (8, 10, 30, 90)))
    return img.filter(ImageFilter.GaussianBlur(S(0.8)))

def scene(t, i):
    name = shot(t)[0]
    if name in ('ctx', 'swing', 'sign', 'pull'): img = scene_street(t, i, name)
    elif name == 'car': img = scene_car(t, i)
    elif name == 'lobby': img = scene_lobby(t, i)
    elif name == 'pop': img = scene_pop(t, i)
    elif name == 'phone': img = scene_phone(t, i)
    else: img = scene_seats(t, i)
    if GOLDT <= t < SEATS + 0.6: E18.confetti(img, t - GOLDT + 0.3)
    return img

# ------------------------------------------------------------------ overlays
CHIP_Y = 200
CHIPS = [('חניה', 820, CHK1), ('כרטיסים', 540, CHK2), ('פופקורן', 260, CHK3)]
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
        w, h = 240 * sc, 62 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 22 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], outline=ink, width=4)

CLOCK_LABEL = ['הסרט', 'בעוד']
def clock_state(t):
    name = shot(t)[0]
    st = story_t(t)
    if name == 'rewind': return C.secs_left(st, ZERO), 'run', True
    s = C.secs_left(st, ZERO)
    if s == 0: return 0, 'zero', False
    return s, ('hot' if s <= 5 else 'run'), False

STREET_BG = LOBBY_BG = SEATS_BG = CAR_BG = SH_AV_BIG = PILL_EP = PILL_Q = PILL_SER = None
def init_all():
    global STREET_BG, LOBBY_BG, SEATS_BG, CAR_BG, SH_AV_BIG, PILL_EP, PILL_Q, PILL_SER
    B.init_all()
    STREET_BG = build_street_bg(); LOBBY_BG = build_lobby_bg(); SEATS_BG = build_seats_bg(); CAR_BG = build_car_bg()
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
    if name == 'ctx':
        if a == 0.0:                                   # cold open: Shoko + keys big, the ginger in the window, the truck behind
            z, cx, cy = 1.10 + 0.03 * t, 520, 1250
            if t < 0.3: z = 1.20 - 0.10 * ease_out(t / 0.3)
        else: z, cx, cy = 1.12, 520, 1250
    elif name == 'swing': z, cx, cy = 1.0 + 0.02 * pu, 560, 1060
    elif name == 'sign': z, cx, cy = 1.40, 430, 1060
    elif name == 'pull': z, cx, cy = 1.05, 640, 1260
    elif name == 'rewind': z, cx, cy = 1.14, 560 + 30 * math.sin(t * 90), 1250
    elif name == 'car': z, cx, cy = 1.08 + 0.01 * pu, 540, 1060
    elif name == 'lobby': z, cx, cy = 1.0 + 0.02 * pu, 540, 960
    elif name == 'pop': z, cx, cy = 1.0 + 0.03 * pu, 600, 1100
    elif name == 'seats':
        if a == SEATS:
            k = ease_io(clamp((t - SEATS) / (BREAK - SEATS))); z, cx, cy = lerp(1.04, 1.18, k), lerp(540, 470, k), lerp(1100, 1200, k)
        else: z, cx, cy = 1.10, 560, 1200
    elif name == 'phone': z, cx, cy = 1.0 + 0.05 * pu, 540, 960
    elif name == 'frozen': z, cx, cy = 1.14 + 0.03 * pu, 540, 1200
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        tt = lerp(L['0b'] + 0.4, T0 + 0.3, ease_in(u))
        img = scene_street(tt, i, 'ctx') if tt >= L['0b'] else (scene_street(tt, i, 'swing') if tt >= SWING else scene_car(tt, i))
    elif name == 'frozen': img = scene(FREEZE - 0.01, i)
    else: img = scene(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 14 * math.exp(-t * 5)
    for s_ in (CHK1, CHK3, BREAK):
        if 0 <= t - s_ < 0.3: shake = 12 * math.exp(-(t - s_) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if t < COLD_END: frame = frame.rotate(-4, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(14, 18, 46, 255))
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(40 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: B.rewind_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK, SWING, SIGN, PULL, LOBBY, POP, SEATS, PHONE, SEATS2):
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
            m.paste_center(frame, m.caption_layer(lines, 88, WHITE), W / 2, 290)
    if name not in ('frozen',): chips(frame, t)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            col = {'sh': SHARIT_SUB, 'shoko': SHOKO_SUB}.get(SPEAKER[li], WHITE)
            m.paste_center(frame, B.sub_layer(lines, col), W / 2, 1560 if name != 'phone' else 1800)
    if t < COLD_END or (T0 <= t < SWING) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_SER, (40, 70 + PILL_EP.height + 6))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    if t < DUR - 0.25 and t < BREAK:
        s, state, scr = clock_state(t)
        C.draw(frame, CLOCK_LABEL, s, state, t, scr)
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio: voices + SFX (control arm: NO music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(45)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'sh': y = m.phone_line(y) * 1.6                       # the voice note through the phone
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
    def jingle(t0, d_=0.5, g=0.05):
        tc = t0; r = random.Random(int(t0 * 100))
        while tc < t0 + d_:
            add(sfx, m.tone(r.uniform(3000, 5200), 0.05, harm=((1, 1), (2.3, 0.4)), decay=40), tc, g); tc += r.uniform(0.04, 0.09)
    def crunch(t0, g=0.12): add(sfx, m.bandpass(nz(0.08), 1500, 7000) * np.exp(-tt_(0.08) * 40), t0, g)
    add(sfx, thud(0.55), 0.0)
    jingle(0.05, COLD_END - 0.2); jingle(L['0b'], D[0])
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.lowpass(nz(SEATS), 180) * 0.8, 0.0, 0.03)                                # night street / engine rumble
    add(sfx, m.lowpass(nz(L[1] + D[1] - T0), 120) * 1.2, T0, 0.04)                      # the engine inside
    add(sfx, m.bandpass(nz(0.7), 200, 2500) * np.linspace(1, 0, int(0.7 * SR)) ** 2, SWING + 0.1, 0.12)   # tyres into the bay
    add(sfx, thud(0.35), CHK1 - 0.1)                                                     # door
    for t_ in (SWING, SIGN, PULL, LOBBY, POP, SEATS, PHONE, SEATS2): whoosh(t_ + 0.05, 0.08, 0.25)
    check(CHK1, 0.15)
    tt = tt_(0.25); add(sfx, m.bandpass(nz(0.25), 1500, 6000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 30 * tt))), CHK2 - 0.3, 0.05)   # ticket printer
    check(CHK2, 0.16)
    add(sfx, thud(0.5), POP + 0.4)                                                       # the bucket lands
    for k in range(8): crunch(POP + 0.45 + 0.05 * k, 0.05)
    check(CHK3, 0.2, True)
    # the auditorium: murmur that hushes as the lights dim at 00:00
    d_ = ZERO - SEATS + 0.4; tt = tt_(d_)
    add(sfx, m.bandpass(nz(d_), 250, 2200) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 2.3 * tt))) * np.clip((d_ - tt) / 0.4, 0, 1), SEATS, 0.05)
    add(sfx, m.tone(110, 0.9, harm=((1, 1), (2, 0.3)), decay=3), ZERO, 0.05)            # the lights go down
    heartbeat(HOLD[0] + 0.04); heartbeat(HOLD[0] + 0.30, 0.5)
    for k in range(2):                                                                   # the phone buzz + ding
        tt = tt_(0.12); add(sfx, m.lowpass(np.sign(np.sin(2 * np.pi * 150 * tt)), 400) * np.sin(np.pi * tt / 0.12), BREAK + k * 0.15, 0.18)
    add(sfx, m.tone(1318.5, 0.4, harm=((1, 1), (2.76, 0.2)), decay=7), BREAK + 0.02, 0.14)
    add(sfx, m.tone(82.4, 1.0, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), SEATS2, 0.10)   # the panic sting
    for k in range(6): crunch(L[6] - 0.5 + 0.17 * k, 0.10)                               # the ginger munches
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
        print('SWING', round(SWING, 2), 'SIGN', round(SIGN, 2), 'PULL', round(PULL, 2), 'LOBBY', round(LOBBY, 2), 'POP', round(POP, 2), 'SEATS', round(SEATS, 2))
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'ZERO/PEAK', round(ZERO, 2), 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'PHONE', round(PHONE, 2), 'SEATS2', round(SEATS2, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        print('clock frame0', C.secs_left(story_t(0), ZERO), 'after rewind', C.secs_left(story_t(T0 + 0.01), ZERO))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, os.environ.get('SHEET', 'ep45_contact.png'))); print('ok'); return
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
