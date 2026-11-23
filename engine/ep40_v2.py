#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 40 v2: תור לרופא: עוד 8 חודשים — polish (Gabi 23.11 13:07, rebuild_polish).
Same voices, plant, climb, break and timing as ep40.py. The only change: the red LED alarm clock (16:42 by day, 06:00 at
night) was drawn in the world at x 800–1000, and the camera's tight crops cut it at the right edge ("16:4"). Here the
clock is drawn on the finished frame at its camera-mapped position, scaled with the zoom, and nudged inward so the
whole box is always inside the frame (24 px margin). Night dims it like the room, the digits keep their glow.

  python3 ep40_v2.py times | test t1 t2 ... | render   -> out/ep40_rofe_v2.mp4
"""
import os, sys, math, random
os.environ.setdefault('OUTNAME', 'ep40_rofe_v2')
from PIL import Image, ImageDraw
import ep40 as E
import make_video as m
from make_video import W, H, K, S, clamp, font, lerp

WORLD_C = E.CLOCK_C
E.CLOCK_C = (-2000, -2000)          # the world clock is off-canvas; the frame overlay below replaces it
BW, BH = 200, 120                   # box size in world units (as in ep40.py)
MARGIN = 24

def cam_box(i):
    t = i / E.FPS
    z, ccx, ccy = E.camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (E.RING[0], E.BREAK):
        if 0 <= t - s_ < 0.3: shake = 14 * math.exp(-(t - s_) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
    else:
        cw, ch, left, top = W * K, H * K, 0, 0
    sc = W / (cw / K)               # frame px per world unit
    fx = (S(WORLD_C[0]) - left) / cw * W; fy = (S(WORLD_C[1]) - top) / ch * H
    return fx, fy, sc

def draw_clock(frame, i):
    t = i / E.FPS
    fx, fy, sc = cam_box(i)
    hw, hh = BW / 2 * sc, BH / 2 * sc
    fx = clamp(fx, hw + MARGIN, W - hw - MARGIN)
    nk = E.night_k(t)
    dim = 1 - 0.45 * nk
    box = tuple(int(c * dim) for c in (30, 30, 36))
    d = ImageDraw.Draw(frame)
    sh = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([fx - hw + 5, fy - hh + 8, fx + hw + 5, fy + hh + 8], radius=int(18 * sc), fill=(0, 0, 0, 90))
    frame.alpha_composite(sh)
    d.rounded_rectangle([fx - hw, fy - hh, fx + hw, fy + hh], radius=int(18 * sc), fill=box, outline=(10, 10, 12), width=max(3, int(5 * sc)))
    d.text((fx, fy), E.clock_text(t), font=font(int(64 * sc), 900), fill=(255, 70, 60), anchor='mm')
    if nk > 0.3:
        r = 18 * sc; bx, by = fx - 80 * sc, fy - 78 * sc
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=m.YELLOW if hasattr(m, 'YELLOW') else (255, 204, 64), outline=(20, 20, 24), width=max(2, int(3 * sc)))

_draw = E.draw_frame
def draw_frame(i):
    t = i / E.FPS
    fr = _draw(i)
    if t >= E.DUR - 0.25: return fr     # the whip blur: leave as is
    fr = fr.convert('RGBA'); draw_clock(fr, i)
    return fr.convert('RGB')
E.draw_frame = draw_frame

if __name__ == '__main__':
    E.main()
