#!/usr/bin/env python3
"""
ep44_v3 (28.11, Gabi's note on episodes/ep44 28.11 14:36: v2 not approved): the whole ride from INSIDE the car.
The camera sits behind the two front seats at shoulder height, looking forward through the windshield. Shoko drives
(image left, seen from behind, both paws on the wheel), the ginger rides (image right, turned toward him). Between them,
on the dash, a big generic navigation screen ("הניווט") is the star of the shot: the route, the arrow and the distance.
Before the turn they fly up the straight lane on green while the left-turn lane stands in a queue (seen through the
windshield, left). At the last second the screen jumps to a giant orange LEFT arrow + "פנה שמאלה" with the metres
dropping fast, the nav voice (4405), the ginger panics and points left, gripping the handle (4400), the straight light
goes orange. The cut: Shoko spins the wheel in one go (wheel + paws), the frame rolls, the view whips left, the ginger is
pressed against his door, screech, and they slot in right in front of the first car of the left lane (a 0.9 s top-down
insert from v2 shows the landing on the green arrow). Shoko: "מחזיק." (4406). After: the screen says "✓ במסלול", the
clock stops on 00:01, "...עברנו?" (4407), the rider from the side mirror rolls up and claps, "תודה, תודה." (4408).
Kept from v2 (imported as B): voices 4400–4408 + timeline, audio (SFX + the music-arm underscore), the real-seconds
clock, chips, the plants (nav + the rider in the side mirror), the queue gags (seen out of the driver's window), break.

  python3 voice/ep44_prep.py
  python3 ep44_v3.py times | test t1 t2 ... | render   -> out/ep44_smola_v3.mp4
"""
import math, os, sys, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import ep44_v2 as B
import ep13 as E13
import ep18 as E18
import clock_overlay as C
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, clamp, epoly, xform,
                        ease_io, ease_out, ease_in, font, WHITE, INK)

OUTDIR = m.OUTDIR
OUTNAME = os.environ.get('OUTNAME', 'ep44_smola_v3')
LIMIT = float(os.environ.get('LIMIT', '0'))
L, D = B.L, B.D
GINGER, SHOKO = B.GINGER, B.SHOKO
COLD_END, RW, T0 = B.COLD_END, B.RW, B.T0
ROAD1, INT2, ROAD2, ROAD3, INT3, ROAD4 = B.ROAD1, B.INT2, B.ROAD2, B.ROAD3, B.INT3, B.ROAD4
SWERVE, CHK1, CHK2, CHK3, GOLDT = B.SWERVE, B.CHK1, B.CHK2, B.CHK3, B.GOLDT
PEAK, HOLD, BREAK, FREEZE, DUR = B.PEAK, B.HOLD, B.BREAK, B.FREEZE, B.DUR
NF = int(round((LIMIT or DUR) * FPS))
SW_IN = 0.85                                   # interior part of the swerve (the wheel spin, the whip)
INS0 = SWERVE[0] + SW_IN                       # the 0.9 s top-down insert: the landing on the green arrow
INS1 = SWERVE[1] + 0.15
B.our_car = lambda *a, **k: None               # from inside: our own car is never drawn in the window shots

SHOTS = [('pov', 0.0, COLD_END), ('rewind', COLD_END, T0), ('pov', T0, ROAD2), ('window', ROAD2, INT3),
         ('pov', INT3, INS0), ('top', INS0, INS1), ('pov', INS1, FREEZE), ('frozen', FREEZE, DUR + 1)]
def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]
story_t = B.story_t

# ------------------------------------------------------------------ the world ahead (perspective through the windshield)
HOR, FOC, CAMH = 560, 900, 1.30
V_MS = 16.0                                     # ~58 km/h up the straight lane
LANE_W = 3.4
def zst(t):
    """distance (m) from the driver's eyes to the stop line, in story time"""
    if t < SWERVE[0]: return 12 + V_MS * (SWERVE[0] - t)
    if t < INS1: return 12 - 8 * ease_out(clamp((t - SWERVE[0]) / (INS1 - SWERVE[0])))
    return 4 - 1.5 * ease_io(clamp((t - INS1) / 1.2))
def swerve_u(t): return clamp((t - SWERVE[0]) / SW_IN)
def cam_pose(t):
    """(lateral x of the driver's eyes, heading rad, + = left)"""
    if t < SWERVE[0]: return -0.4, 0.0
    u = swerve_u(t)
    x = lerp(-0.4, -0.4 - LANE_W, ease_io(u))
    h = math.radians(34) * math.sin(math.pi * min(1.0, u * 1.05)) ** 0.8
    if t >= INS1: x, h = -0.4 - LANE_W, math.radians(3)
    return x, h

class Proj:
    def __init__(self, t):
        self.cx, self.h = cam_pose(t); self.c, self.s = math.cos(self.h), math.sin(self.h)
    def cam(self, x, z):
        dx = x - self.cx
        return dx * self.c + z * self.s, -dx * self.s + z * self.c
    def p(self, x, z, y=0.0):
        xr, zr = self.cam(x, z); zr = max(zr, 0.35)
        return (540 + FOC * xr / zr, HOR + (CAMH - y) * FOC / zr)
    def zr(self, x, z): return self.cam(x, z)[1]

def quad(d, P, pts, fill, outline=None, width=0):
    """world (x, z, y) points → polygon; skipped when any point is behind the camera"""
    if any(P.zr(x, z) < 0.4 for x, z, _ in pts): return
    poly(d, [P.p(x, z, y) for x, z, y in pts], fill=fill, outline=outline, width=width)

def ground_strip(d, P, x0, x1, z0, z1, fill, n=12):
    zs = [z0 + (z1 - z0) * (k / n) ** 2 for k in range(n + 1)]
    pts = [(x0, z, 0) for z in zs] + [(x1, z, 0) for z in reversed(zs)]
    pts = [q for q in pts if P.zr(q[0], q[1]) >= 0.4]
    if len(pts) >= 3: poly(d, [P.p(*q[:2]) for q in pts], fill=fill)

BUILD_COLS = [(214, 198, 170), (232, 216, 186), (200, 190, 176), (226, 210, 180), (210, 200, 184), (190, 182, 172)]
def light_state(t):
    """straight head: 'green' → 'orange' (the junction, ROAD4) → 'red'; left arrow: red until CHK3"""
    st = story_t(t)
    straight = 'green' if st < ROAD4 else ('orange' if st < SWERVE[0] + 0.6 else 'red')
    return straight, st >= CHK3

def signal(d, P, x, z, kind, state):
    yb, yt = (3.0, 5.4) if z > 0 and P.zr(x, z) > 0 and kind != 'near' else (1.9, 3.7)
    if kind == 'near': kind = 'straight'
    if P.zr(x, z) < 1.0: return
    a = P.p(x - 0.55, z, yt); b = P.p(x + 0.55, z, yb)
    d.rounded_rectangle([S(a[0]), S(a[1]), S(b[0]), S(b[1])], radius=S(max(2, (b[0] - a[0]) * 0.18)), fill=(26, 26, 30), outline=(8, 8, 10), width=iw(3))
    r = (b[0] - a[0]) * 0.36; cx = (a[0] + b[0]) / 2
    ys = [lerp(a[1], b[1], f) for f in (0.2, 0.5, 0.8)]
    if kind == 'straight':
        cols = [(255, 60, 50) if state == 'red' else (70, 20, 20), (255, 170, 30) if state == 'orange' else (70, 50, 14),
                (60, 230, 90) if state == 'green' else (16, 40, 20)]
        for y_, c_ in zip(ys, cols): E(d, cx, y_, r, r, fill=c_)
        lit = {'red': 0, 'orange': 1, 'green': 2}[state]
        ov_col = cols[lit]
        E(d, cx, ys[lit], r * 1.9, r * 1.9, outline=ov_col, width=max(2, int(r * 0.25)))
    else:
        green = state
        E(d, cx, ys[0], r, r, fill=(255, 60, 50) if not green else (70, 20, 20))
        E(d, cx, ys[1], r, r, fill=(70, 50, 14))
        E(d, cx, ys[2], r, r, fill=(16, 40, 20))
        ink = (60, 230, 90) if green else (40, 90, 50)
        s_ = r / 30
        poly(d, [(cx + 18 * s_, ys[2] + 16 * s_), (cx + 4 * s_, ys[2] + 16 * s_), (cx + 4 * s_, ys[2] + 2 * s_), (cx - 6 * s_, ys[2] + 2 * s_),
                 (cx - 6 * s_, ys[2] + 14 * s_), (cx - 26 * s_, ys[2] - 6 * s_), (cx - 6 * s_, ys[2] - 26 * s_), (cx - 6 * s_, ys[2] - 14 * s_),
                 (cx + 18 * s_, ys[2] - 14 * s_)], fill=ink)
        if green: E(d, cx, ys[2], r * 1.9, r * 1.9, outline=ink, width=max(2, int(r * 0.25)))

def car_rear(d, P, x, z, col, k):
    """a stopped car seen from behind (left-turn queue); k = index (gags on a few)"""
    if P.zr(x, z) < 1.2: return
    w2, hb, ht = 0.9, 0.35, 1.45
    a = P.p(x - w2, z, ht); b = P.p(x + w2, z, 0.18)
    sc = (b[0] - a[0]) / 180
    d.rounded_rectangle([S(a[0]), S(a[1]), S(b[0]), S(b[1])], radius=S(max(2, 26 * sc)), fill=col, outline=(20, 20, 24), width=iw(max(1, 4 * sc)))
    w = P.p(x - w2 * 0.78, z, ht - 0.06); w_ = P.p(x + w2 * 0.78, z, 0.95)
    d.rounded_rectangle([S(w[0]), S(w[1]), S(w_[0]), S(w_[1])], radius=S(max(1, 14 * sc)), fill=(120, 146, 170))
    for sx in (-1, 1):                                          # brake lights on (stopped)
        q = P.p(x + sx * w2 * 0.78, z, 0.78)
        E(d, q[0], q[1], 18 * sc, 11 * sc, fill=(255, 50, 40))
    for sx in (-1, 1):
        q = P.p(x + sx * w2 * 0.7, z, 0.12); E(d, q[0], q[1], 22 * sc, 12 * sc, fill=(20, 20, 24))
    if k == 2:                                                   # the plant on the roof (gag, plant of the queue)
        q = P.p(x, z, ht)
        poly(d, [(q[0] - 26 * sc, q[1]), (q[0] + 26 * sc, q[1]), (q[0] + 20 * sc, q[1] - 40 * sc), (q[0] - 20 * sc, q[1] - 40 * sc)], fill=(170, 90, 50))
        for j in range(5): E(d, q[0] - 28 * sc + j * 14 * sc, q[1] - 56 * sc - 8 * sc * (j % 2), 20 * sc, 14 * sc, fill=(70, 150, 70))
    if k == 1:                                                   # the sleeper: a pillow pressed to the rear window
        q = P.p(x, z, 1.15); E(d, q[0], q[1], 40 * sc, 20 * sc, fill=(240, 240, 252), outline=(150, 150, 170), width=2)

QCOLS = [B.CAR_COLS[c] for c in (1, 3, 4, 5, 0, 2, 6)]
def world(img, t):
    """the road ahead, drawn on a full-frame layer (clipped to the windshield later)"""
    d = ImageDraw.Draw(img)
    for y in range(0, HOR + 8, 8):
        v = y / HOR
        d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(140, 206, v)), int(lerp(192, 226, v)), int(lerp(240, 244, v))))
    d.rectangle([0, S(HOR), W * K, H * K], fill=(150, 150, 146))
    P = Proj(story_t(t) if t < COLD_END else t)
    tt = story_t(t) if t < COLD_END else t
    Z = zst(tt)
    # sidewalks + buildings
    ground_strip(d, P, -40, -7.2, 0.5, 260, (176, 172, 164))
    ground_strip(d, P, 5.4, 40, 0.5, 260, (176, 172, 164))
    ground_strip(d, P, -7.2, 5.4, 0.5, 260, (88, 90, 98))
    ground_strip(d, P, -60, 60, Z, Z + 13, (98, 100, 108))      # the crossing road
    blds = []
    for side, xb in ((-1, -9.0), (1, 7.5)):
        for k in range(14):
            z0 = 6 + k * 19 - (Z % 19); z1 = z0 + 15
            if Z <= z1 + 2 and z0 <= Z + 14: continue            # the junction gap
            hgt = 9 + 6 * ((k * 7 + (side > 0)) % 3)
            blds.append((z0, side, xb, z1, hgt, BUILD_COLS[(k + (side > 0) * 3) % len(BUILD_COLS)]))
    for z0, side, xb, z1, hgt, col in sorted(blds, key=lambda b: -b[0]):
        quad(d, P, [(xb, z0, 0), (xb, z1, 0), (xb, z1, hgt), (xb, z0, hgt)], col, (150, 138, 118), 2)
        for r_ in range(int(hgt // 3.2)):
            for c_ in range(3):
                za, zb_ = z0 + 1.5 + c_ * 4.4, z0 + 3.6 + c_ * 4.4
                quad(d, P, [(xb, za, 1.6 + r_ * 3.2), (xb, zb_, 1.6 + r_ * 3.2), (xb, zb_, 3.2 + r_ * 3.2), (xb, za, 3.2 + r_ * 3.2)], (92, 112, 132))
    # zebra + stop line + lane markings
    for k in range(9):
        x0 = -7.0 + k * 1.4; quad(d, P, [(x0, Z + 0.6, 0), (x0 + 0.7, Z + 0.6, 0), (x0 + 0.7, Z + 3.2, 0), (x0, Z + 3.2, 0)], (236, 236, 232))
    quad(d, P, [(-5.1, Z - 0.35, 0), (5.4, Z - 0.35, 0), (5.4, Z, 0), (-5.1, Z, 0)], (246, 246, 244))
    ph = (-Z) % 9.0
    for xl, solid in ((-LANE_W / 2, False), (-LANE_W * 1.5, True), (LANE_W / 2 + 0.3, False)):
        if solid:
            quad(d, P, [(xl - 0.08, 0.6, 0), (xl + 0.08, 0.6, 0), (xl + 0.08, Z - 0.4, 0), (xl - 0.08, Z - 0.4, 0)], (240, 240, 236))
            continue
        z = ph - 9
        while z < Z - 0.5:
            za, zb_ = max(0.6, z), min(Z - 0.5, z + 4.5)
            if zb_ > za: quad(d, P, [(xl - 0.08, za, 0), (xl + 0.08, za, 0), (xl + 0.08, zb_, 0), (xl - 0.08, zb_, 0)], (240, 240, 236))
            z += 9.0
    # painted arrows: left-turn lane and straight lane, a few metres before the stop line
    for xc, kind in ((-LANE_W, 'left'), (0.0, 'straight')):
        z0 = Z - 9
        if kind == 'straight':
            quad(d, P, [(xc - 0.15, z0, 0), (xc + 0.15, z0, 0), (xc + 0.15, z0 + 3, 0), (xc - 0.15, z0 + 3, 0)], (236, 236, 232))
            quad(d, P, [(xc - 0.5, z0 + 3, 0), (xc + 0.5, z0 + 3, 0), (xc, z0 + 4.6, 0), (xc, z0 + 4.6, 0)], (236, 236, 232))
        else:
            quad(d, P, [(xc - 0.15 + 0.4, z0, 0), (xc + 0.15 + 0.4, z0, 0), (xc + 0.15 + 0.4, z0 + 3, 0), (xc - 0.15 + 0.4, z0 + 3, 0)], (236, 236, 232))
            quad(d, P, [(xc + 0.55, z0 + 2.7, 0), (xc + 0.55, z0 + 3.2, 0), (xc - 0.4, z0 + 3.4, 0), (xc - 0.4, z0 + 2.5, 0)], (236, 236, 232))
            quad(d, P, [(xc - 0.4, z0 + 2.2, 0), (xc - 0.4, z0 + 3.7, 0), (xc - 1.0, z0 + 2.95, 0), (xc - 1.0, z0 + 2.95, 0)], (236, 236, 232))
    # the left-turn queue: stopped on red; its first car a full length back (the gap at the head)
    cars = [(Z - 8.5 - 6.3 * k, k) for k in range(36)]
    for z, k in sorted(cars, key=lambda c: -c[0]):
        if 1.2 < P.zr(-LANE_W, z) < 160: car_rear(d, P, -LANE_W, z, QCOLS[k % len(QCOLS)], k)
    # the gantry + signals
    zg = Z + 14
    if P.zr(5.0, zg) > 1:
        a = P.p(5.0, zg, 0); b = P.p(5.0, zg, 5.6)
        line(d, [a, b], (60, 62, 70), max(3, 0.25 * FOC / max(1, P.zr(5, zg)) * 1.0))
        aa = P.p(-5.0, zg, 5.45); bb = P.p(5.0, zg, 5.45)
        line(d, [aa, bb], (60, 62, 70), max(3, 0.18 * FOC / max(1, P.zr(0, zg))))
        sst, lg = light_state(t)
        signal(d, P, -LANE_W, zg, 'left', lg)
        signal(d, P, 0.0, zg, 'straight', sst)
    if P.zr(4.9, Z + 1) > 1.5:                                   # the near pole at the stop line: the straight light, big
        a = P.p(4.9, Z + 1, 0); b = P.p(4.9, Z + 1, 1.9)
        line(d, [a, b], (60, 62, 70), max(3, 0.16 * FOC / max(1, P.zr(4.9, Z + 1))))
        signal(d, P, 4.9, Z + 1, 'near', light_state(t)[0])
    return P

# ------------------------------------------------------------------ the cabin (static parts)
WS = [(0, 250), (W, 250), (W, 1000), (0, 1000)]       # the windshield opening (pillars drawn over it)
def build_cabin():
    """returns (mask L for the windshield, RGBA overlay of the static cabin: roof, pillars, dash)"""
    mask = Image.new('L', (W * K, H * K), 0); md = ImageDraw.Draw(mask)
    md.polygon([(S(x), S(y)) for x, y in [(150, 262), (930, 262), (1050, 1000), (30, 1000)]], fill=255)
    ov = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    ROOF = (74, 76, 86); TRIM = (46, 48, 56); DASH = (38, 40, 46)
    d.rectangle([0, 0, W * K, S(262)], fill=ROOF)
    d.rectangle([0, S(236), W * K, S(266)], fill=TRIM)
    poly(d, [(0, 236), (150, 236), (30, 1010), (0, 1010)], fill=ROOF, outline=TRIM, width=8)        # A-pillars
    poly(d, [(W, 236), (930, 236), (1050, 1010), (W, 1010)], fill=ROOF, outline=TRIM, width=8)
    # dash
    poly(d, [(-20, 990), (W + 20, 990), (W + 20, 1260), (-20, 1260)], fill=DASH)
    d.rectangle([0, S(984), W * K, S(1004)], fill=(66, 68, 78))
    for x0 in (60, 860):                                                                                # vents
        d.rounded_rectangle([S(x0), S(1060), S(x0 + 160), S(1110)], radius=S(12), fill=(20, 20, 24))
        for k_ in range(4): d.line([S(x0 + 10), S(1070 + k_ * 11), S(x0 + 150), S(1070 + k_ * 11)], fill=(50, 50, 58), width=iw(3))
    # centre console + gear lever between the seats
    poly(d, [(420, 1260), (660, 1260), (720, 1920), (360, 1920)], fill=(34, 36, 42))
    E(d, 540, 1560, 34, 34, fill=(20, 20, 24)); line(d, [(540, 1560), (540, 1660)], (20, 20, 24), 22)
    # grab handle above the passenger door (top right)
    d.rounded_rectangle([S(920), S(286), S(1060), S(330)], radius=S(20), fill=(36, 38, 44))
    # rear-view mirror
    d.rectangle([S(532), S(262), S(548), S(300)], fill=(30, 30, 34))
    d.rounded_rectangle([S(410), S(294), S(670), S(366)], radius=S(22), fill=(24, 24, 28), outline=(10, 10, 12), width=iw(4))
    d.rounded_rectangle([S(422), S(304), S(658), S(356)], radius=S(16), fill=(120, 140, 160))
    # seat tops (behind the cats' shoulders)
    for cx in (230, 860):
        d.rounded_rectangle([S(cx - 260), S(1650), S(cx + 260), S(2000)], radius=S(90), fill=(50, 52, 62), outline=(30, 30, 36), width=iw(6))
    return mask, ov

def side_mirror(img, t, rider=True):
    """the driver's side mirror at the base of the left pillar, with the rider in it (plant b)"""
    d = ImageDraw.Draw(img)
    mx, my = 92, 905
    d.rounded_rectangle([S(mx - 86), S(my - 62), S(mx + 86), S(my + 62)], radius=S(32), fill=(236, 238, 242), outline=(170, 174, 184), width=iw(6))
    d.rounded_rectangle([S(mx - 72), S(my - 48), S(mx + 72), S(my + 48)], radius=S(24), fill=(150, 178, 204))
    d.rectangle([S(mx - 72), S(my + 8), S(mx + 72), S(my + 48)], fill=(120, 120, 128))
    if rider: B.mirror_rider(d, (mx - 4, my - 22 + 2 * math.sin(t * 6)), 0.85)

# ------------------------------------------------------------------ the navigation screen (the star of the shot)
NW_, NH_ = 420, 330
NAV_C = (560, 1010)
def nav_mode(t):
    s_t = story_t(t)
    if s_t >= GOLDT: return 'ok'
    if s_t >= L[5] + 0.15: return 'left'
    return 'straight'

def turn_dist(t):
    s_t = story_t(t)
    return max(0, int(zst(s_t) + 6))

def left_arrow(d, cx, cy, s, col):
    """a bold 'turn left' arrow: shaft up, bend, head pointing left"""
    w_ = 30 * s
    poly(d, [(cx + 40 * s - w_ / 2, cy + 70 * s), (cx + 40 * s + w_ / 2, cy + 70 * s), (cx + 40 * s + w_ / 2, cy - 20 * s),
             (cx + 40 * s - w_ / 2, cy - 20 * s - w_)], fill=col)
    poly(d, [(cx + 40 * s + w_ / 2, cy - 20 * s), (cx + 40 * s - w_ / 2, cy - 20 * s - w_), (cx - 20 * s, cy - 20 * s - w_), (cx - 20 * s, cy - 20 * s)], fill=col)
    poly(d, [(cx - 20 * s, cy - 20 * s - w_ - 30 * s), (cx - 20 * s, cy - 20 * s + 30 * s), (cx - 75 * s, cy - 20 * s - w_ / 2)], fill=col)

def straight_arrow(d, cx, cy, s, col):
    w_ = 28 * s
    poly(d, [(cx - w_ / 2, cy + 60 * s), (cx + w_ / 2, cy + 60 * s), (cx + w_ / 2, cy - 20 * s), (cx - w_ / 2, cy - 20 * s)], fill=col)
    poly(d, [(cx - 48 * s, cy - 18 * s), (cx + 48 * s, cy - 18 * s), (cx, cy - 72 * s)], fill=col)

def nav_layer(mode, dist, talk, flash, u_turn):
    lay = Image.new('RGBA', (S(NW_), S(NH_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(NW_) - 1, S(NH_) - 1], radius=S(26), fill=(16, 16, 20))
    d.rounded_rectangle([S(12), S(12), S(NW_ - 12), S(NH_ - 12)], radius=S(18), fill=(226, 230, 224))
    # the map: streets + the route (straight, then a left turn ahead)
    for (a, b) in (((12, 170), (NW_ - 12, 150)), ((150, 120), (170, NH_ - 12)), ((300, 120), (290, NH_ - 12))):
        line(d, [a, b], (250, 250, 250), 16)
    jy = lerp(170, 278, clamp(1 - dist / 260)) if mode != 'ok' else 300      # the junction slides down to the car marker
    line(d, [(12, jy), (NW_ - 12, jy - 10)], (250, 250, 250), 20)
    route = [(NW_ / 2 + 10, NH_ - 30), (NW_ / 2 + 10, jy), (30, jy - 6)] if mode != 'ok' else [(NW_ / 2 + 10, NH_ - 30), (30, NH_ - 40)]
    line(d, route, (40, 120, 255), 14)
    poly(d, [(NW_ / 2 + 10, NH_ - 52), (NW_ / 2 - 6, NH_ - 18), (NW_ / 2 + 26, NH_ - 18)], fill=(40, 120, 255), outline=WHITE, width=3)
    # the banner
    bh = 132 if mode == 'left' else 112
    if mode == 'straight': col = (30, 140, 80)
    elif mode == 'ok': col = (30, 150, 80)
    else: col = (255, 120, 20) if flash else (226, 48, 30)
    d.rounded_rectangle([S(12), S(12), S(NW_ - 12), S(12 + bh)], radius=S(18), fill=col)
    d.rectangle([S(12), S(bh - 6), S(NW_ - 12), S(12 + bh)], fill=col)
    if mode == 'straight':
        straight_arrow(d, NW_ - 70, 66, 0.62, WHITE)
        d.text((S(NW_ - 130), S(62)), 'ישר', font=font(S(56), 900), fill=WHITE, anchor='rm')
        d.text((S(40), S(62)), f'{int(round(dist / 50.0) * 50)} מ׳', font=font(S(34), 800), fill=(220, 240, 226), anchor='lm')
        # the plant: the next manoeuvre, small and grey, that Shoko never looks at
        d.rounded_rectangle([S(24), S(NH_ - 66), S(NW_ - 150), S(NH_ - 26)], radius=S(12), fill=(246, 248, 246))
        d.text((S((NW_ - 126) / 2 + 12), S(NH_ - 46)), f'אחר כך: שמאלה · {int(round(dist / 50.0) * 50)} מ׳', font=font(S(22), 900), fill=(140, 144, 150), anchor='mm')
    elif mode == 'left':
        sc = 1.0 + 0.10 * math.sin(u_turn * 20)
        left_arrow(d, 96, 84, 0.78 * sc, WHITE)
        d.text((S(NW_ - 26), S(50)), 'פנה שמאלה', font=font(S(42), 900), fill=WHITE, anchor='rm')
        d.text((S(NW_ - 26), S(106)), f'{dist} מ׳', font=font(S(48), 900), fill=(255, 246, 180), anchor='rm')
    else:
        d.text((S(NW_ / 2 + 40), S(66)), 'במסלול', font=font(S(54), 900), fill=WHITE, anchor='mm')
        d.ellipse([S(40), S(36), S(100), S(96)], fill=WHITE)
        d.line([S(54), S(66), S(66), S(80), S(88), S(50)], fill=col, width=iw(9), joint='curve')
    d.text((S(NW_ - 30), S(bh + 34)), 'הניווט', font=font(S(20), 800), fill=(110, 116, 110), anchor='rm')
    if talk >= 0:
        av = B.SH_AV[talk]; lay.alpha_composite(av, (int(S(24)), int(S(bh + 18))))
    return lay

_NC = {}
def nav_at(t):
    s_t = story_t(t)
    mode = nav_mode(t)
    talk = -1
    if L[5] <= s_t < L[5] + D[5]:
        sv = B.voice_v(s_t, 'sh'); talk = 2 if sv > 0.3 else (1 if sv > 0.1 else 0)
    if mode == 'left':
        dist = max(0, int(min(100, zst(s_t) + 6) // 10 * 10)) if s_t < SWERVE[0] else 0
        flash = int(s_t * 6) % 2 == 0
        u = round((s_t - L[5]) * 10) / 10
    else:
        dist = turn_dist(t); flash = False; u = 0.0
        if mode == 'straight': dist = int(round(dist / 50.0) * 50)
    key = (mode, dist, talk, flash, u if mode == 'left' else 0)
    if key not in _NC:
        if len(_NC) > 60: _NC.clear()
        _NC[key] = nav_layer(mode, dist, talk, flash, u)
    return _NC[key]

# ------------------------------------------------------------------ the cats
def back_head(img, hx, hy, f, pal, props=False, rot=0.0, ear=0.0, bob=0.0):
    """a cat head seen from behind (Shoko driving): fur dome, ears, the arms of his shades, the toothpick tip"""
    lay = Image.new('RGBA', (520 * K, 520 * K), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for side in (-1, 1):
        bo = (260 + side * 160, 170); bi = (260 + side * 40, 110); tip = (260 + side * 118, 26 - ear)
        poly(d, [bo, tip, bi], fill=pal['FUR'], outline=pal['OUT'], width=6)
        poly(d, [(lerp(bo[0], tip[0], 0.3), lerp(bo[1], tip[1], 0.3)), (lerp(bi[0], tip[0], 0.75), lerp(bi[1], tip[1], 0.75)), (lerp(bo[0], bi[0], 0.5), lerp(bo[1], bi[1], 0.5) - 6)], fill=pal['FUR_D'])
    E(d, 260, 270, 205, 190, fill=pal['FUR'], outline=pal['OUT'], width=7)
    for k_ in range(3):                                            # a few fur strokes on the back of the head
        line(d, [(220 + k_ * 40, 190 + 10 * (k_ % 2)), (214 + k_ * 40, 240)], pal['FUR_D'], 5)
    if props:
        for side in (-1, 1): line(d, [(260 + side * 120, 250), (260 + side * 206, 244)], (18, 18, 22), 9)   # the shades' arms
        line(d, [(464, 330), (520, 318 + bob)], (222, 190, 130), 7)                                           # the toothpick tip
    if abs(rot) > 1e-3: lay = lay.rotate(rot, resample=Image.BICUBIC, center=(260 * K, 270 * K))
    sz = int(520 * K * f); lay = lay.resize((sz, sz), Image.BICUBIC)
    img.alpha_composite(lay, dest=(int(S(hx) - 260 * K * f), int(S(hy) - 270 * K * f)))

GHX, GHY, GF = 862, 1400, 0.86
SHX, SHY, SF = 238, 1410, 0.92
WHEEL_C, WHEEL_R = (236, 1150), 168
def wheel_angle(t):
    if t < SWERVE[0]: return 4 * math.sin(t * 1.3)
    if t < INS1:
        u = clamp((t - SWERVE[0]) / SW_IN)
        return -230 * ease_out(clamp(u / 0.35)) + 150 * ease_io(clamp((u - 0.45) / 0.55))
    return -60 * (1 - ease_io(clamp((t - INS1) / 0.6)))

def wheel(img, t):
    d = ImageDraw.Draw(img)
    cx, cy = WHEEL_C; r = WHEEL_R; a = math.radians(wheel_angle(t))
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], outline=(16, 16, 20), width=iw(34))
    d.ellipse([S(cx - r + 8), S(cy - r + 8), S(cx + r - 8), S(cy + r - 8)], outline=(40, 40, 46), width=iw(6))
    for ang in (90, 210, 330):                                    # spokes (rotate with the wheel)
        aa = math.radians(ang) + a
        line(d, [(cx, cy), (cx + (r - 14) * math.cos(aa), cy + (r - 14) * math.sin(aa))], (24, 24, 28), 26)
    E(d, cx, cy, 52, 52, fill=(28, 28, 32), outline=(10, 10, 12), width=4)
    mk = (cx + (r) * math.cos(-math.pi / 2 + a), cy + (r) * math.sin(-math.pi / 2 + a))   # top-centre marker: shows the spin
    E(d, mk[0], mk[1], 14, 14, fill=(230, 60, 40))
    return [(cx + r * math.cos(math.radians(ang) + a), cy + r * math.sin(math.radians(ang) + a)) for ang in (-150, -30)]

def ginger_state(t):
    st, rot, dy = B.ginger_state(t)
    lx, ly = st.get('look', (0, 0)); st['look'] = (-lx, ly)          # mirrored layout: the left lane is image left now
    return st, -rot, dy

def scene_pov(t, i):
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255))
    wl = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    world(wl, t)
    s_t = story_t(t)
    if SWERVE[0] <= s_t < INS1:                                     # motion blur on the whip
        wl = wl.filter(ImageFilter.GaussianBlur(S(1 + 2.5 * math.sin(math.pi * swerve_u(s_t)))))
    img.paste(wl, (0, 0), CAB_MASK)
    # glass reflections
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k_, xa in enumerate((260, 420, 820)):
        poly(od, [(xa, 262), (xa + 60 + 26 * k_, 262), (xa - 150 + 26 * k_, 1000), (xa - 210, 1000)], fill=(255, 255, 255, 18))
    img.alpha_composite(ov)
    img.alpha_composite(CAB_OV)
    side_mirror(img, t, rider=t < BREAK)
    d = ImageDraw.Draw(img)
    # the break: the rider rolls up at Shoko's window (left), visor up, slow claps
    if t >= BREAK:
        u = t - BREAK
        x = lerp(-320, 210, ease_out(clamp(u / 0.35)))
        visor = ease_out(clamp((u - 0.25) / 0.25))
        clap = abs(math.cos(max(0, u - 0.5) * 3.2)) if u > 0.5 else 1.0
        B.shadow_paste(img, B.RIDERS[(int(round(visor * 4)), int(round(clap * 4)))], (x, 720), 4, 1.0, 80)
        d = ImageDraw.Draw(img)
        if u > 0.5 and clap < 0.15:
            for k_ in range(3):
                a_ = math.radians(-120 + k_ * 30)
                line(d, [(x - 10 + 70 * math.cos(a_), 650 + 70 * math.sin(a_)), (x - 10 + 110 * math.cos(a_), 650 + 110 * math.sin(a_))], (255, 255, 255), 6)
    swing = (SWERVE[0] <= s_t < INS1)
    us = swerve_u(s_t) if swing else 0.0
    # Shoko (driver, image left): from behind, paws on the wheel
    d = ImageDraw.Draw(img)
    E(d, SHX, 1720, 300, 230, fill=SHOKO['FUR'], outline=SHOKO['OUT'], width=7)
    grips = wheel(img, t)
    d = ImageDraw.Draw(img)
    for sx, g in zip((-1, 1), grips):
        capsule(d, (SHX + sx * 190, 1640), g, 78, SHOKO['FUR'], SHOKO['OUT'], 4)
        B.paw(d, g, SHOKO, 0, 0.72)
    sv = B.voice_v(s_t, 'shoko')
    if t >= BREAK:                                                   # he turns to the rider: the star nod
        sst, srot, sdy = B.shoko_state(t)
        sst['look'] = (-30, 2)
        B.head(img, sst, i, SHX + 10, SHY - 30 + sdy, SF * 0.95, -srot, SHOKO, props=True, wob=6 * math.sin(t * 3))
    else:
        back_head(img, SHX, SHY - 10 * sv - (6 * math.sin(us * math.pi) if swing else 0), SF, SHOKO, props=True,
                  rot=(-10 * math.sin(us * math.pi) if swing else 1.5 * math.sin(t * 2)), ear=10 * sv, bob=8 * math.sin(t * 3))
    # the ginger (passenger, image right): turned toward Shoko / the left lane
    gst, grot, gdy = ginger_state(t)
    gx, gy, gf = GHX, GHY + gdy, GF
    d = ImageDraw.Draw(img)
    if swing:                                                        # pressed against his door
        k = math.sin(math.pi * us); gx += 60 * k; grot += -18 * k; gy -= 20 * k
    E(d, gx, 1730, 270, 230, fill=GINGER['FUR'], outline=GINGER['OUT'], width=7)
    E(d, gx, 1780, 120, 170, fill=GINGER['CREAM'])
    panic = (L['0b'] <= s_t < INS1 and t < PEAK)
    if panic or swing or (L[5] + 1.0 <= s_t < L['0b']):              # one paw on the grab handle, top right
        hp = (990, 316)
        capsule(d, (gx + 110, 1560), hp, 76, GINGER['FUR'], GINGER['OUT'], 4); B.paw(d, hp, GINGER, 180, 0.8)
    B.head(img, gst, i, gx, gy, gf, grot, GINGER)
    d = ImageDraw.Draw(img)
    if T0 <= t < ROAD1:                                              # the want: the slip held up to Shoko
        sc_ = (640 + 6 * math.sin(t * 7), 1330 + 8 * math.sin(t * 9))
        capsule(d, (gx - 80, 1620), (sc_[0] + 60, sc_[1] + 70), 80, GINGER['FUR'], GINGER['OUT'], 4)
        B.shadow_paste(img, B.SLIP, sc_, -6 + 3 * math.sin(t * 5), 1.0, 80)
        d = ImageDraw.Draw(img); B.paw(d, (sc_[0] + 60, sc_[1] + 70), GINGER, 20, 0.8)
    elif panic and not swing:                                        # pointing LEFT, across (behind the nav) at the left lane
        tip = (250 + 16 * math.sin(t * 16), 790 - 12 * abs(math.sin(t * 10)))
        capsule(d, (gx - 150, 1330), tip, 74, GINGER['FUR'], GINGER['OUT'], 4); B.paw(d, tip, GINGER, 60, 0.85)
        line(d, [(tip[0] - 70, tip[1] - 40), (tip[0] - 130, tip[1] - 60)], (255, 255, 255), 8)
        line(d, [(tip[0] - 70, tip[1]), (tip[0] - 140, tip[1])], (255, 255, 255), 8)
    elif PEAK <= t < BREAK:                                          # bracing on the dash
        for px in (720, 1010):
            capsule(d, (gx + (px - 890) * 0.5, 1650), (px, 1600), 80, GINGER['FUR'], GINGER['OUT'], 4); B.paw(d, (px, 1600), GINGER, 0, 0.85)
    B.shadow_paste(img, nav_at(t), NAV_C, 0, 1.0, 90)
    d = ImageDraw.Draw(img)
    # the exact second: a ring on the nav as it turns "במסלול"
    if GOLDT <= t < GOLDT + 0.6 or (INS1 <= t < INS1 + 0.5):
        u = clamp((t - max(GOLDT, INS1)) / 0.5)
        r = 140 + 200 * u
        d.ellipse([S(NAV_C[0] - r), S(NAV_C[1] - r * 0.8), S(NAV_C[0] + r), S(NAV_C[1] + r * 0.8)], outline=(255, 230, 90), width=iw(10 * (1 - u) + 1))
    return img

# ------------------------------------------------------------------ out of the driver's window (the queue gags, the bus)
def build_window():
    mask = Image.new('L', (W * K, H * K), 0); md = ImageDraw.Draw(mask)
    md.rounded_rectangle([S(70), S(400), S(1010), S(1240)], radius=S(70), fill=255)
    ov = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W * K, H * K], fill=(60, 62, 72))
    d.rounded_rectangle([S(70), S(400), S(1010), S(1240)], radius=S(70), fill=(0, 0, 0, 0))
    d.rounded_rectangle([S(56), S(386), S(1024), S(1254)], radius=S(78), outline=(30, 30, 36), width=iw(22))
    d.rectangle([0, S(1250), W * K, S(1320)], fill=(80, 82, 92))                                     # the door sill
    d.rounded_rectangle([S(120), S(1340), S(420), S(1400)], radius=S(24), fill=(40, 42, 50))       # the door handle
    return mask, ov

def scene_window(t, i):
    kind = 'road2' if t < ROAD3 else 'road3'
    road = B.scene_road(t, i, kind)
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255))
    road = road.crop((0, S(300), W * K, S(300) + H * K)) if False else road
    shifted = Image.new('RGBA', road.size, (0, 0, 0, 255)); shifted.paste(road, (0, S(-80)))
    img.paste(shifted, (0, 0), WIN_MASK)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    poly(od, [(300, 400), (420, 400), (200, 1240), (80, 1240)], fill=(255, 255, 255, 16))
    img.alpha_composite(ov)
    img.alpha_composite(WIN_OV)
    # over Shoko's shoulder (back of his head, bottom left) and the ginger leaning in (bottom right)
    s_t = t
    back_head(img, 260, 1560, 1.0, SHOKO, props=True, rot=-6, ear=10 * B.voice_v(s_t, 'shoko'), bob=8 * math.sin(t * 3))
    gst, grot, gdy = ginger_state(t)
    d = ImageDraw.Draw(img)
    E(d, 850, 1840, 280, 220, fill=GINGER['FUR'], outline=GINGER['OUT'], width=7)
    B.head(img, gst, i, 840, 1520 + gdy, 0.92, grot - 6, GINGER)
    return img

def scene(t, i):
    name = shot(t)[0]
    if name == 'window': img = scene_window(t, i)
    elif name == 'top': img = B.scene_drift(t, i)
    else: img = scene_pov(t, i)
    if GOLDT <= t < BREAK: E18.confetti(img, t - GOLDT + 0.3)
    return img

def camera(t):
    name, a, b = shot(t)
    z, cx, cy, roll = 1.0, 540.0, 960.0, 0.0
    if name in ('pov', 'frozen'):
        s_t = story_t(t)
        z, cx, cy = 1.04, 540, 1000
        if t < COLD_END:                                        # cold open: the ginger pointing, the nav arrow, Shoko calm
            z, cx, cy = 1.10 + 0.03 * t, 560, 1040
            if t < 0.3: z = 1.30 - 0.20 * ease_out(t / 0.3)
        elif t < ROAD1: z, cx, cy = 1.08, 600, 1080            # the want: the slip
        elif t < ROAD2: z, cx, cy = 1.04 + 0.01 * (t - ROAD1), 540, 980
        elif t < L[5]: z, cx, cy = 1.06, 540, 1000            # "שרית?! גם בפקק?!"
        elif t < L['0b']:                                       # the nav speaks: push in on the screen + both of them
            k = ease_io(clamp((t - L[5]) / 1.0)); z, cx, cy = lerp(1.06, 1.38, k), 560, lerp(1000, 1060, k)
        elif t < ROAD4:                                         # "שמאלה?! שמאלה!!!": pull back, the pointing paw + the lane
            k = ease_out(clamp((t - L['0b']) / 0.35)); z, cx, cy = lerp(1.38, 1.06, k), lerp(560, 520, k), lerp(1060, 960, k)
        elif t < SWERVE[0]: z, cx, cy = 1.06 + 0.04 * (t - ROAD4), 540, 980
        elif t < INS0:
            u = swerve_u(t); z, cx, cy = 1.08, 540, 1000
            roll = 9 * math.sin(math.pi * u)                      # the whole frame leans with the turn
        elif t < PEAK: z, cx, cy = 1.06, 540, 1000
        elif t < BREAK:
            k = ease_io(clamp((t - PEAK) / (BREAK - PEAK))); z, cx, cy = lerp(1.06, 1.18, k), lerp(540, 640, k), lerp(1000, 1180, k)
        else: z, cx, cy = 1.02, 520, 980
        if name == 'frozen': z, cx, cy = 1.08 + 0.03 * (t - a), 520, 1000
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1000
    elif name == 'window':
        z, cx, cy = 1.0, 540, 960
    elif name == 'top':
        z, cx, cy, r_ = B.drift_view(t); roll = r_
    return z, cx, cy, roll

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    else: img = scene(t, i)
    z, ccx, ccy, roll = camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (CHK3, BREAK, SWERVE[0]):
        if 0 <= t - s_ < 0.3: shake = max(shake, 12 * math.exp(-(t - s_) * 8))
    if SWERVE[0] <= t < INS1: shake = max(shake, 6)
    if abs(roll) > 0.05:
        img = img.rotate(roll, resample=Image.BICUBIC, center=(S(ccx), S(ccy)), fillcolor=(40, 42, 48, 255)); z = max(z, 1.12)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if t < COLD_END: frame = frame.rotate(4, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(40, 42, 48, 255))
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(50 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: B.rewind_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK, ROAD2, INT3, INS0, INS1, PEAK):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(90 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    for t0, t1, lines in B.TOPCAPS:
        if t0 <= t < t1:
            band = frame.crop((0, 0, W, 470)).filter(ImageFilter.GaussianBlur(14))
            mask = Image.new('L', (W, 470), 0); md = ImageDraw.Draw(mask)
            for yy in range(470): md.line([(0, yy), (W, yy)], fill=int(255 * min(1, (470 - yy) / 90)))
            frame.paste(band, (0, 0), mask)
            dk = Image.new('RGBA', (W, 470), (0, 0, 0, 0)); dd = ImageDraw.Draw(dk)
            for yy in range(470): dd.line([(0, yy), (W, yy)], fill=(8, 10, 18, int(150 * min(1, (470 - yy) / 120))))
            frame.alpha_composite(dk, (0, 0))
            m.paste_center(frame, m.caption_layer(lines, 92, WHITE), W / 2, 290)
    if name not in ('frozen',): B.chips(frame, t)
    for t0, t1, lines, li in B.SUB_TIMES:
        if t0 <= t < t1:
            col = {'sh': B.SHARIT_SUB, 'shoko': B.SHOKO_SUB}.get(B.SPEAKER[li], WHITE)
            m.paste_center(frame, B.sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < ROAD1) or name == 'frozen':
        frame.alpha_composite(B.PILL_EP, (40, 70))
        frame.alpha_composite(B.PILL_SER, (40, 70 + B.PILL_EP.height + 6))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(B.PILL_Q, (W - 40 - B.PILL_Q.width, 70))
    if t < DUR - 0.25 and t < BREAK:
        s, state, scr = B.clock_state(t)
        C.draw(frame, B.CLOCK_LABEL, s, state, t, scr)
    return frame.convert('RGB')

CAB_MASK = CAB_OV = WIN_MASK = WIN_OV = None
def init_all():
    global CAB_MASK, CAB_OV, WIN_MASK, WIN_OV
    B.init_all()
    CAB_MASK, CAB_OV = build_cabin()
    WIN_MASK, WIN_OV = build_window()

def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if mode == 'times':
        print('DUR', DUR, 'SWERVE', [round(x, 2) for x in SWERVE], 'INS', round(INS0, 2), round(INS1, 2), 'CHK3', round(CHK3, 2),
              'L5', round(L[5], 2), 'zst@L5', round(zst(L[5]), 1), 'zst@0b', round(zst(L['0b']), 1), 'zst@ROAD4', round(zst(ROAD4), 1))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, os.environ.get('SHEET', 'ep44v3_contact.png'))); print('ok'); return
    if mode == 'frame':
        init_all(); tm = float(sys.argv[2]); draw_frame(int(round(tm * FPS))).save(os.path.join(OUTDIR, f'ep44v3_f{tm}.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'{OUTNAME}_audio.wav'); B.build_audio(wav); print('audio ok')
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
            if k % 60 == 0: print('frame', k, '/', nfr, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
