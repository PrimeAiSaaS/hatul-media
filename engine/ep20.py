#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 20: הגרר — v2, rebuilt 29.10 under §P (Gabi, 28.10: "לבנות מחדש"); v1 kept in ep20_v1.py.
Beat sheet (§P):
  WANT (frame 0, in motion): get his towed car out of the tow lot. He sprints up to the lot's window (clerk POV), the tow
  notice held high; hook "גררו לך את הרכב? / יאללה, למגרש הגרירה!"; meter of 3 chips (שילמתי / שוחרר / מצאתי).
  PLANT: a red LED clock — on the lot office wall from frame 0 (15:57), on the pole in the lot mid-climb (15:59), on the
  gate booth wall, and on the pole right in front of the barrier. Never pointed at, never explained.
  CLIMB: pays ✓ → the tow-lot clerk (Sharit's tow rig from v1) stamps "שוחרר" ✓ and dangles his keys "שורה 3, מותק." →
  he races through the lot and finds his car ✓ "הנה אתה!" (meter gold) → at the gate booth she presses the button:
  "יאללה, סע, מותק!", the barrier rises.
  PEAK: in the car, engine running, the barrier up in front of him, "סוף סוף: / הרכב שלי!", one bite from the snack bag, he
  leans back, eyes closed — silence + heartbeat (10.9–11.4).
  BREAK (one_second_late, 11.45–12.3): the clock flips to 16:00 (beep) and the barrier SLAMS down across the frame, the booth
  light reads "סגור", the chips snap back empty, 0.45 s frozen face, hard cut to frame 0 (loop). No וואלה tail, no CTA.

  python3 ep20.py test 0 0.4 1.3 2.0 2.9 3.4 4.4 5.3 6.3 6.9 7.6 8.6 10.2 11.0 11.5 11.6 11.9 12.25 -> out/ep20_contact.png
  python3 ep20.py render                                                                            -> out/ep20_tow_v2.mp4
"""
import math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep7 as E7
import ep8 as E8
import ep10 as E10
import ep12 as E12
import ep13 as E13
import ep15 as E15
import ep18 as E18
import ep20_v1 as V1
import ep21 as E21
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

DUR = 12.3
NF = int(round(DUR * FPS))
OUTDIR = m.OUTDIR
YELLOW = (255, 221, 51); GREEN = (36, 168, 84); GOLD = (230, 170, 30); AMBER = (255, 170, 30)
BEAT = 60 / 80
QUEUE = int(os.environ.get('QUEUE', '477'))
EP_LABEL = 'פרק 20'
TAG_OUT = os.environ.get('OUTNAME', 'ep20_tow_v2')
CARZ = float(os.environ.get('CARZ', '1.18')); CARY = float(os.environ.get('CARY', '1000'))

SHOTS = [('win', 0.0, 2.3), ('two', 2.3, 4.1), ('lot', 4.1, 6.0), ('booth', 6.0, 7.4), ('car', 7.4, DUR + 1)]
RUN = 0.3
SH_PAY = (0.5, 1.15)    # off-screen: "תשלום, מותק."
PAY = 1.25              # notes slapped up -> chip 1
CHK1 = 1.32
STAMP = 2.8             # "שוחרר" -> chip 2
CHK2 = 2.85
KEYS = (3.2, 4.0)       # "שורה 3, מותק." + keys dangling
GRABK = 3.7
SPOT = 5.0              # "הנה אתה!" -> chip 3
CHK3 = 5.3
GO = (6.1, 6.85)        # booth: "יאללה, סע, מותק!"
BUTTON = 6.75           # barrier starts rising
ENGINE = 7.5
MUNCH = (9.9, 10.5)
PEAK = (10.9, 11.4)
TICK = 11.45            # clock flips to 16:00
SLAM = 11.55            # barrier slams down
FREEZE = (11.85, DUR)

CAPTIONS = [  # (t0, t1, lines, size, y, fill)
    (0.0, 2.3, ['גררו לך את הרכב?', 'יאללה, למגרש הגרירה!'], 92, 290, WHITE),     # keyword on frame 1
    (2.3, 4.1, ['שילמתי. שוחרר.', 'רק למצוא אותו.'], 92, 290, WHITE),
    (7.75, 9.8, ['סוף סוף:', 'הרכב שלי!'], 100, 290, WHITE),
]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def sway(t): return math.sin(2 * math.pi * t / (2 * BEAT))
burst = E18.burst; imprint = E18.imprint; stamp_tool = E18.stamp_tool; confetti = E18.confetti; _check = E18._check

def clock_text(t):
    if t >= TICK: return '16:00'
    if t < 2.3: return '15:57'
    if t < 4.1: return '15:58'
    return '15:59'

# ------------------------------------------------------------------ props
CLOCKS = {}
def clock_layer(text, w=300):
    if (text, w) in CLOCKS: return CLOCKS[(text, w)]
    h = int(w * 0.42)
    lay = Image.new('RGBA', (S(w), S(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(w) - 1, S(h) - 1], radius=S(16), fill=(30, 30, 36), outline=(8, 8, 10), width=iw(5))
    d.rounded_rectangle([S(14), S(14), S(w - 14), S(h - 14)], radius=S(10), fill=(18, 6, 8))
    d.text((S(w / 2), S(h / 2 + 2)), text, font=font(S(int(h * 0.62)), 900), fill=(255, 54, 54), anchor='mm')
    CLOCKS[(text, w)] = lay
    return lay

def paste_clock(img, t, c, w=300, colon=True):
    tx = clock_text(t)
    if not colon and t < TICK and int(t * 2) % 2: tx = tx.replace(':', ' ')
    lay = clock_layer(tx, w)
    m.paste_center(img, lay, S(c[0]), S(c[1]))

def keys_layer():
    lay = Image.new('RGBA', (S(150), S(200)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([S(45), S(6), S(105), S(66)], outline=(200, 200, 210), width=iw(8))
    d.rounded_rectangle([S(40), S(60), S(110), S(120)], radius=S(16), fill=(40, 42, 50), outline=(10, 10, 14), width=iw(4))
    d.rectangle([S(68), S(120), S(82), S(190)], fill=(200, 200, 210))
    for y in (150, 172): d.rectangle([S(82), S(y), S(96), S(y + 10)], fill=(200, 200, 210))
    d.rounded_rectangle([S(10), S(72), S(46), S(130)], radius=S(8), fill=(255, 214, 64), outline=(120, 90, 10), width=iw(3))
    d.text((S(28), S(101)), '3', font=font(S(34), 900), fill=INK, anchor='mm')
    return lay

def slip_layer():
    lay = Image.new('RGBA', (S(330), S(220)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(329), S(219)], radius=S(12), fill=(252, 250, 244), outline=(120, 120, 120), width=iw(4))
    d.rectangle([0, 0, S(330), S(56)], fill=AMBER)
    d.text((S(165), S(30)), 'מגרש גרירה', font=font(S(34), 900), fill=INK, anchor='mm')
    d.text((S(165), S(100)), 'טופס שחרור רכב', font=font(S(32), 900), fill=INK, anchor='mm')
    for y in (140, 170): d.line([S(40), S(y), S(290), S(y)], fill=(170, 170, 170), width=iw(3))
    return lay

def barrier(img, ang, piv=(1060, 1150), L=1150, th=46):
    """striped barrier arm; ang 0 = down (pointing left, across the frame), 90 = up"""
    d = ImageDraw.Draw(img)
    a = math.radians(180 - ang)
    tip = (piv[0] + L * math.cos(a), piv[1] - L * math.sin(a))
    n = 9
    for k in range(n):
        p0 = lerp2(piv, tip, k / n); p1 = lerp2(piv, tip, (k + 1) / n)
        capsule(d, p0, p1, th, (230, 40, 46) if k % 2 == 0 else (250, 250, 248), (60, 20, 20), 3)
    E(d, piv[0], piv[1], 60, 60, fill=(250, 196, 40), outline=(120, 90, 10), width=5)

def barrier_ang(t):
    if t < BUTTON: return 0.0
    if t < SLAM - 0.08: return 82 * ease_out(clamp((t - BUTTON) / 0.7))
    if t < SLAM: return lerp(82, 0, ease_in(clamp((t - (SLAM - 0.08)) / 0.08)))
    u = t - SLAM
    return 6 * math.exp(-u * 10) * abs(math.sin(u * 30))

# ------------------------------------------------------------------ the tow-lot clerk (v1's tow rig)
def paste_tow(img, st, rot, i, head, sc):
    L = V1.tow_draw(dict(st, rot=rot), i)
    L = L.resize((int(L.width * sc), int(L.height * sc)), Image.BICUBIC)
    img.alpha_composite(L, dest=(int(S(head[0] - 350 * sc)), int(S(head[1] - 300 * sc))))

def tow_state(t, i):
    st = E15.tech_base(); rot = 0.0
    if t < 6.0:                                            # two-shot at the window
        if t < STAMP - 0.3: st.update(mouth='lazy', lid=0.35, look=(18, 10))
        elif t < KEYS[0]: st.update(mouth='grin', lid=0.3, look=(18, 8)); rot = -4 * math.exp(-max(0, t - STAMP) * 5)
        else:
            u = t - KEYS[0]
            st.update(mouth='talk' if u < 0.6 else 'grin', lid=0.3, look=(16, 4), hand_r=(560, 520)); rot = -4 * math.exp(-u * 4)
    else:                                                  # booth close-up
        u = t - GO[0]
        st.update(mouth='talk' if GO[0] <= t < GO[1] else 'grin', lid=0.2, look=(0, 0), finger=t >= BUTTON - 0.1,
                  hand_r=(560, 560) if t >= BUTTON - 0.1 else (530, 760))
        rot = -5 * math.exp(-max(0, u) * 4) * math.cos(max(0, u) * 10)
    return st, rot

# ------------------------------------------------------------------ cat states
def base_cat():
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.3); return st

def cat_state_win(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < RUN:
        st.update(lid=0.0, pupil='big', brow='annoyed', mouth='w', ear_dy=-18, look=(-6, 2), blush=0.0)
        dy = -26 * abs(math.sin(t * 22)); rot = 5 * math.sin(t * 18)
    elif t < PAY:
        u = t - RUN
        st.update(lid=0.0, pupil='big', brow='annoyed', mouth='w' if t < SH_PAY[0] else 'flat', ear_dy=-20 * math.exp(-u * 4), look=(-8, 0), blush=0.0)
        dy = 14 * math.exp(-u * 9) * math.cos(u * 24)
    else:
        u = t - PAY
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-16 * math.exp(-u * 4), look=(-6, 0), blush=0.6)
        dy = -14 * abs(math.sin(u * 10)) * math.exp(-u * 3)
    return st, rot, dy

def cat_state_two(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < STAMP - 0.3: st.update(lid=0.0, pupil='big', brow='up', mouth='smile_small', look=(-18, 4), blush=0.4)
    elif t < STAMP: st.update(lid=0.0, pupil='tiny', brow='up', mouth='flat', ear_dy=-10, look=(-18, 10))
    else:
        u = t - STAMP
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24 * math.exp(-u * 3), look=(-16, 0), blush=0.8)
        dy = -18 * abs(math.sin(u * 9)) * math.exp(-u * 2)
        if t >= KEYS[0]: st.update(look=(-20, -6), mouth='w' if t < GRABK else 'smile')
    return st, rot, dy

def cat_state_lot(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < SPOT:                                           # racing through the rows, looking around
        st.update(lid=0.0, pupil='big', brow='annoyed', mouth='w', look=(-22 if int(t * 3) % 2 else 18, 2), blush=0.0, ear_dy=-14)
        dy = -24 * abs(math.sin(t * 16)); rot = 5 * math.sin(t * 16)
    else:
        u = t - SPOT
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-26 * math.exp(-u * 3), look=(22, 4), blush=1.0)
        dy = -20 * abs(math.sin(u * 9)) * math.exp(-u * 1.5)
    return st, rot, dy

def cat_state_car(t, i):
    st = base_cat(); sw = sway(t)
    rot, dy = 0.0, 0.0
    if t < 9.8:                                            # engine on, beaming
        u = t - ENGINE
        st.update(lid=0.0 if t < 8.4 else 0.35, pupil='big' if t < 8.4 else 'normal', brow='up', mouth='smile', look=(-4, 0), blush=0.8,
                  ear_dy=-18 * math.exp(-max(0, u) * 3))
        if 0 <= u < 0.5: dy = 10 * math.sin(u * 60) * math.exp(-u * 5)
        if t >= 8.4: rot = 3 * sw
        return st, rot, dy
    if t < PEAK[0]:                                        # one bite, then leaning back
        st.update(lid=0.5, mouth='munch' if (MUNCH[0] <= t < MUNCH[1] and (i // 3) % 2 == 0) else 'goofy', look=(6, 8), blush=0.8)
        if t >= PEAK[0] - 0.35: st.update(lid=0.85, mouth='smile', blush=0.9)
        return st, 3 * sw, 4 * abs(sw)
    if t < TICK:                                           # PEAK: eyes closed, bliss
        st.update(lid=1.0, mouth='smile', blush=1.0, ear_droop=0.4)
        return st, -4.0, -6 * ease_out(clamp((t - PEAK[0]) / 0.3))
    u = t - TICK
    if t < FREEZE[0]:                                      # beep -> SLAM: eyes snap open
        st.update(lid=0.0, pupil='big', brow='up', ear_dy=-24 * math.exp(-u * 4), mouth='w', look=(-6, 14), blush=0.0)
        v = t - SLAM
        return st, (6 * math.exp(-v * 5) * math.sin(v * 22) if v > 0 else 0.0), (-30 * math.exp(-v * 8) * math.cos(v * 26) if v > 0 else 0.0)
    st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_droop=0.6, sweat=1.0, look=(0, 10), blush=0.0,
              twitch=(int(t * 12) % 2 == 0))
    return st, -2.0, 0.0

# ------------------------------------------------------------------ scenes
HX, HY, F = 700, 900, 1.8
QUEUE_BEHIND = [('c0', 130, 1060, 0.55, 0.0), ('h1', 330, 1090, 0.45, 1.1), ('c3', 1010, 1160, 0.55, 2.0)]

def scene_win(t, i):
    img = WIN_BG.copy()
    paste_clock(img, t, (240, 680), 300)
    mood = 2 if t < CHK1 else 0
    for name, x, y, sc, ph in QUEUE_BEHIND:
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_win(t, i)
    sc_in = lerp(0.82, 1.0, ease_out(t / RUN)) if t < RUN else 1.0
    hx, hy = HX + (1 - sc_in) * 180, HY + (1 - sc_in) * 300
    E(d, hx, 1640, 450 * sc_in, 470, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1700, 210 * sc_in, 320, fill=CREAM)
    rp = (960 + 10 * math.sin(t * 9), lerp(1180, 1330, ease_out(clamp((t - RUN) / 0.2))) + (20 * math.sin(t * 22) if t < RUN else 0))
    capsule(d, (hx + 250, 1420), (rp[0], rp[1] + 60), 120, FUR, OUT, 4)
    lay = NOTICE.resize((int(NOTICE.width * 0.62), int(NOTICE.height * 0.62)), Image.BICUBIC).rotate(-8 + 6 * math.sin(t * 5), resample=Image.BICUBIC, expand=True)
    m.paste_center(img, lay, S(rp[0] - 20), S(rp[1] - 110))
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (rp[0], rp[1] + 40), -10)
    E12.paste_head(img, st, i, hx, hy + dy, F * sc_in, rot)
    d = ImageDraw.Draw(img)
    if t >= PAY - 0.12:                                    # the cash slapped up next to his face
        u = t - (PAY - 0.12)
        c = (250, lerp(1700, 1250, ease_out(clamp(u / 0.12))))
        capsule(d, (hx - 260, 1450), (c[0] + 20, c[1] + 110), 120, FUR, OUT, 4)
        for k in range(3):
            lay = NOTE.rotate(-8 + 9 * k, resample=Image.BICUBIC, expand=True)
            m.paste_center(img, lay, S(c[0] - 10 + 14 * k), S(c[1] - 16 * k))
        _check(img, (c[0] + 120, c[1] - 40), t - CHK1)
        d = ImageDraw.Draw(img); E12.big_paw(d, (c[0] + 30, c[1] + 120), 8)
        burst(img, c, t - PAY, (255, 255, 255), 150, 8, 0.3)
    if t < RUN + 0.3: burst(img, (960, 1200), t - RUN, (255, 236, 120), 120, 10, 0.3)
    if SH_PAY[0] <= t < SH_PAY[1]:
        SH.bubble(img, 'תשלום, מותק.', t - SH_PAY[0], (560, 640, 440, 120), (330, 800), side=-1)
    return img

HX2, HY2, F2 = 790, 960, 1.45
T_HEAD = (225, 900); TS = 1.45
SLIP_C = (320, 1500)
def stamp_pos(t):
    u = t - STAMP
    top, down = (SLIP_C[0] - 40, 1180), (SLIP_C[0], SLIP_C[1] - 20)
    if -0.3 <= u < 0: return lerp2(top, down, ease_in(clamp((u + 0.3) / 0.3)))
    if 0 <= u < 0.2: return down
    if 0.2 <= u < 0.45: return lerp2(down, (330, 1250), ease_out((u - 0.2) / 0.25))
    return None

def scene_two(t, i):
    img = SH_BG.copy()
    paste_clock(img, t, (840, 760), 260)
    st_s, rot_s = tow_state(t, i)
    paste_tow(img, st_s, rot_s, i, T_HEAD, TS)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_two(t, i)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    if t < STAMP: rp = (HX2 + 150, 1330 + 6 * math.sin(t * 6))
    elif t < GRABK: v = t - STAMP; rp = (HX2 + 200, 1250 - 60 * abs(math.sin(v * 9)) * math.exp(-v * 1.5))
    else: rp = lerp2((HX2 - 200, 1080), (HX2 + 160, 1200), ease_out(clamp((t - GRABK) / 0.25)))
    if KEYS[0] + 0.2 <= t < GRABK: rp = lerp2((HX2 + 200, 1250), (HX2 - 200, 1080), ease_io(clamp((t - KEYS[0] - 0.2) / (GRABK - KEYS[0] - 0.2))))
    capsule(d, (HX2 + 220, 1520), rp, 100, FUR, OUT, 4)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    m.paste_center(img, SLIP.rotate(-5, resample=Image.BICUBIC, expand=True), S(SLIP_C[0]), S(SLIP_C[1]))
    imprint(img, (SLIP_C[0] - 6, SLIP_C[1] + 6), t - STAMP, 'שוחרר', 0.62, -10, GREEN)
    d = ImageDraw.Draw(img)
    sp_ = stamp_pos(t)
    if sp_: stamp_tool(d, sp_, 1.1)
    if t >= KEYS[0]:                                       # the keys: dangling from her hand, then in his paw
        kp = (470 + 14 * math.sin(t * 9), 1020) if t < GRABK else (rp[0] - 10, rp[1] - 90)
        m.paste_center(img, KEYSL.rotate(10 * math.sin(t * 9), resample=Image.BICUBIC, expand=True), S(kp[0]), S(kp[1]))
        d = ImageDraw.Draw(img)
    E12.big_paw(d, rp, -10, 0.85)
    if t < STAMP: E12.big_paw(d, (rp[0] - 70, rp[1] + 20), 10, 0.85)
    burst(img, SLIP_C, t - STAMP, (120, 255, 160), 160, 10, 0.35)
    _check(img, (SLIP_C[0] + 150, SLIP_C[1] - 90), t - CHK2)
    if KEYS[0] <= t < KEYS[1]:
        SH.bubble(img, 'שורה 3, מותק.', t - KEYS[0], (540, 640, 460, 120), (300, 760), side=-1)
    if STAMP + 0.05 <= t < KEYS[0]:
        SH.bubble(img, 'שוחרר, מותק.', t - STAMP - 0.05, (540, 640, 440, 120), (300, 760), side=-1)
    return img

def build_lot_bg():
    img = Image.new('RGBA', (W * K, H * K)); d = ImageDraw.Draw(img)
    for y in range(0, H, 6):
        d.rectangle([0, S(y), W * K, S(y + 6)], fill=m.lerpc((130, 190, 236), (236, 220, 196), y / 1000))
    d.rectangle([0, S(860), W * K, H * K], fill=(118, 118, 126))
    for x in range(-20, 1100, 60):                         # chain-link fence
        line(d, [(x, 560), (x + 120, 860)], (150, 156, 164), 3); line(d, [(x + 120, 560), (x, 860)], (150, 156, 164), 3)
    line(d, [(-10, 560), (1100, 560)], (110, 116, 124), 8)
    rng = random.Random(20)
    for row, (y, s) in enumerate(((900, 0.55), (1060, 0.8))):   # rows of towed cars
        x = -60 + row * 90
        while x < 1150:
            col = rng.choice([(200, 60, 60), (60, 110, 200), (230, 230, 230), (60, 60, 70), (230, 200, 60)])
            d.rounded_rectangle([S(x), S(y - 70 * s), S(x + 260 * s), S(y + 60 * s)], radius=S(40 * s), fill=col, outline=(30, 30, 36), width=iw(4))
            d.rounded_rectangle([S(x + 50 * s), S(y - 130 * s), S(x + 210 * s), S(y - 60 * s)], radius=S(26 * s), fill=col, outline=(30, 30, 36), width=iw(4))
            d.rectangle([S(x + 70 * s), S(y - 118 * s), S(x + 190 * s), S(y - 70 * s)], fill=(150, 196, 226))
            for wx in (x + 50 * s, x + 210 * s): E(d, wx, y + 60 * s, 30 * s, 30 * s, fill=(24, 24, 28))
            x += 300 * s
    E8.plaque(d, 760, 470, 'מגרש גרירה', 340)
    line(d, [(240, 760), (240, 980)], (80, 80, 90), 18)    # clock pole
    return img.filter(ImageFilter.GaussianBlur(S(3)))

def scene_lot(t, i):
    img = LOT_BG.copy()
    paste_clock(img, t, (240, 690), 280)
    d = ImageDraw.Draw(img)
    if t >= SPOT - 0.3:                                    # his teal car slides in on the right
        x = lerp(1250, 900, ease_out(clamp((t - (SPOT - 0.3)) / 0.3)))
        d.rounded_rectangle([S(x - 200), S(1280), S(x + 260), S(1560)], radius=S(70), fill=(40, 170, 170), outline=(10, 70, 70), width=iw(7))
        d.rounded_rectangle([S(x - 120), S(1160), S(x + 200), S(1300)], radius=S(50), fill=(40, 170, 170), outline=(10, 70, 70), width=iw(7))
        d.rectangle([S(x - 90), S(1180), S(x + 170), S(1290)], fill=(160, 210, 236))
        _check(img, (x + 20, 1040), t - CHK3)
        d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_lot(t, i)
    E(d, 560, 1640 + dy * 0.4, 440, 460, fill=FUR, outline=OUT, width=7)
    E(d, 560, 1700 + dy * 0.4, 200, 300, fill=CREAM)
    rp = (280 + 30 * math.sin(t * 16), 1380 + 40 * math.sin(t * 16)) if t < SPOT else (220, 1150 - 40 * abs(math.sin((t - SPOT) * 8)))
    capsule(d, (330, 1440), rp, 120, FUR, OUT, 4)
    m.paste_center(img, KEYSL.rotate(20 * math.sin(t * 16), resample=Image.BICUBIC, expand=True), S(rp[0]), S(rp[1] - 90))
    d = ImageDraw.Draw(img); E12.big_paw(d, rp, 10)
    E12.paste_head(img, st, i, 560, 900 + dy, 1.75, rot)
    if t < SPOT:                                           # speed lines
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(8):
            y = 700 + k * 120; x0 = ((t * 2600 + k * 333) % 1500) - 200
            line(od, [(x0, y), (x0 + 220, y)], (255, 255, 255, 140), 8)
        img.alpha_composite(ov)
    if SPOT <= t < SPOT + 0.8:
        SH.bubble(img, 'הנה אתה!', t - SPOT, (400, 640, 360, 120), (500, 780), side=-1)
    return img

def build_booth_bg():
    img = Image.new('RGBA', (W * K, H * K), (200, 196, 186, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        d.rectangle([0, S(y), W * K, S(y + 8)], fill=m.lerpc((214, 210, 198), (176, 170, 160), y / H))
    d.rounded_rectangle([S(600), S(380), S(1080), S(980)], radius=S(16), fill=(150, 200, 236), outline=(90, 90, 100), width=iw(10))
    d.rectangle([S(600), S(860), S(1080), S(980)], fill=(118, 118, 126))
    E8.plaque(d, 300, 470, 'יציאה', 220)
    return img

def scene_booth(t, i):
    img = BOOTH_BG.copy()
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    barrier(ov, barrier_ang(t), piv=(1030, 860), L=440, th=26)
    mask = Image.new('L', img.size, 0); ImageDraw.Draw(mask).rectangle([S(606), S(386), S(1074), S(974)], fill=255)
    img.paste(ov, (0, 0), Image.composite(ov.split()[3], Image.new('L', img.size, 0), mask))
    paste_clock(img, t, (250, 680), 280)
    st, rot = tow_state(t, i)
    paste_tow(img, st, rot, i, (540, 900), 1.75)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1560), S(1100), S(1960)], radius=S(16), fill=(90, 92, 102), outline=(40, 40, 48), width=iw(6))
    E(d, 820, 1640, 70, 40, fill=(30, 170, 80) if t < BUTTON else (90, 240, 130), outline=(10, 60, 30), width=5)
    if GO[0] <= t < GO[1]:
        SH.bubble(img, 'יאללה, סע, מותק!', t - GO[0], (540, 560, 560, 120), (560, 720), side=-1)
    burst(img, (840, 620), t - BUTTON, (120, 255, 160), 140, 10, 0.35)
    return img

def lot_rear_view(img, t):
    """the lot behind the car (seen through the rear window): fence, towed cars, other owners cheering"""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = E10.RW
    for y in range(y0, y1, 6):
        d.rectangle([S(x0), S(y), S(x1), S(y + 6)], fill=m.lerpc((130, 190, 236), (236, 220, 196), (y - y0) / (y1 - y0)))
    d.rectangle([S(x0), S(820), S(x1), S(y1)], fill=(118, 118, 126))
    for x in range(x0, x1, 50):
        line(d, [(x, 600), (x + 100, 820)], (150, 156, 164), 3); line(d, [(x + 100, 600), (x, 820)], (150, 156, 164), 3)
    for k, (x, col) in enumerate(((180, (200, 60, 60)), (520, (60, 110, 200)), (860, (230, 200, 60)))):
        d.rounded_rectangle([S(x - 130), S(780), S(x + 130), S(880)], radius=S(30), fill=col, outline=(30, 30, 36), width=iw(4))
    mood = 1 if ENGINE <= t < 9.8 else (1 if t >= SLAM else 2)
    for name, x, y, sc, ph in (('c1', 230, 690, 0.36, 0.4), ('h0', 450, 650, 0.30, 1.4), ('c3', 820, 690, 0.36, 2.3)):
        jump = -16 * abs(math.sin(t * 9 + ph)) if ENGINE <= t < 9.8 else 0
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4 + ph) + jump, sc, flip=x > 540)

def scene_car(t, i):
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255))
    lot_rear_view(img, t)
    img.alpha_composite(CAR_MID)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_car(t, i)
    E(d, 540, 1262 + 0.5 * dy, 215, 215, fill=FUR, outline=OUT, width=6)
    E(d, 540, 1300 + 0.5 * dy, 98, 150, fill=CREAM)
    poly(d, [(700, 1080 + 0.5 * dy), (740, 1110 + 0.5 * dy), (420, 1500), (380, 1470)], fill=(40, 42, 50))
    WC = E10.WHEEL_C; WR = E10.WHEEL_R
    wa = 4 * math.sin(t * 3)
    paws = [xform([(dx, -150)], WC[0], WC[1], wa)[0] for dx in (-190, 190)]
    if MUNCH[0] - 0.2 <= t < MUNCH[1]:
        paws[1] = lerp2(paws[1], (620, 1060), math.sin(math.pi * clamp((t - MUNCH[0] + 0.2) / (MUNCH[1] - MUNCH[0] + 0.2))))
    capsule(d, (418, 1180 + 0.5 * dy), paws[0], 62, FUR, OUT, 3)
    capsule(d, (662, 1180 + 0.5 * dy), paws[1], 62, FUR, OUT, 3)
    E12.paste_head(img, st, i, 540, 905 + dy, 1.0, rot)
    d = ImageDraw.Draw(img)
    d.ellipse([S(WC[0] - WR), S(WC[1] - WR), S(WC[0] + WR), S(WC[1] + WR)], outline=(24, 24, 30), width=iw(46))
    d.ellipse([S(WC[0] - WR + 6), S(WC[1] - WR + 6), S(WC[0] + WR - 6), S(WC[1] + WR - 6)], outline=(58, 58, 68), width=iw(30))
    for a0 in (-25, 205, 90):
        ra = math.radians(a0 + wa)
        line(d, [(WC[0] + 60 * math.cos(ra), WC[1] + 60 * math.sin(ra)), (WC[0] + (WR - 20) * math.cos(ra), WC[1] + (WR - 20) * math.sin(ra))], (46, 46, 54), 30)
    E(d, WC[0], WC[1], 74, 64, fill=(46, 46, 54), outline=(20, 20, 24), width=5)
    m.draw_paw(d, paws[0], ang=wa)
    if MUNCH[0] - 0.2 <= t < MUNCH[1]: SH.snack_bag(d, (paws[1][0] + 10, paws[1][1] - 70), -12, 0.8)
    m.draw_paw(d, paws[1], ang=wa)
    img.alpha_composite(CAR_FG)
    d = ImageDraw.Draw(img)
    if not (MUNCH[0] - 0.2 <= t < MUNCH[1]): SH.snack_bag(d, (250, 1420), -10, 0.75)
    # outside, in front of the windshield: the clock on the booth pole + the barrier arm
    line(d, [(800, 860), (800, 1150)], (70, 70, 80), 22)
    paste_clock(img, t, (800, 800), 240, colon=(t < PEAK[0] - 0.6 or t >= TICK))
    if t >= TICK:                                          # booth light: סגור
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([S(700), S(660), S(900), S(720)], radius=S(12), fill=(214, 44, 52), outline=(90, 10, 14), width=iw(4))
        d.text((S(800), S(691)), 'סגור', font=font(S(40), 900), fill=WHITE, anchor='mm')
    barrier(img, barrier_ang(t))
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(2):
        ph = ((t * 0.08 + k * 0.5) % 1) * 1600 - 300
        poly(od, [(ph, 60), (ph + 90 - 40 * k, 60), (ph - 280 - 40 * k, 1440), (ph - 370, 1440)], fill=(255, 255, 255, 22 - 8 * k))
    img.alpha_composite(ov)
    burst(img, (540, 1150), t - SLAM, (255, 255, 255), 200, 12, 0.35)
    if ENGINE <= t < ENGINE + 0.5:                         # exhaust puff / vroom lines
        burst(img, (540, 1500), t - ENGINE, (255, 236, 120), 260, 10, 0.5)
    return img

# ------------------------------------------------------------------ frame
METER_Y = 470
METER = [('שילמתי', CHK1), ('שוחרר', CHK2), ('מצאתי', CHK3)]
def meter(frame, t):
    d = ImageDraw.Draw(frame)
    reset = t >= SLAM
    full = (t >= CHK3) and not reset
    xs = [850, 540, 230]
    for k, (lab, tc) in enumerate(METER):
        done = (t >= tc) and not reset
        u = t - tc
        sc = 1.0 + (0.35 * math.exp(-u * 10) * math.cos(u * 20) if (0 <= u < 0.5 and not reset) else 0.0)
        if reset and t - SLAM < 0.3: sc = 1.0 + 0.2 * math.exp(-(t - SLAM) * 12)
        w_, h_ = 270 * sc, 76 * sc
        cx = xs[k] + (random.Random(int(t * FPS) + k).uniform(-10, 10) if (reset and t - SLAM < 0.3) else 0)
        fill = (GREEN if not full else GOLD) if done else (250, 250, 250)
        d.rounded_rectangle([cx - w_ / 2 + 5, METER_Y - h_ / 2 + 8, cx + w_ / 2 + 5, METER_Y + h_ / 2 + 8], radius=int(h_ / 2), fill=(0, 0, 0, 90))
        d.rounded_rectangle([cx - w_ / 2, METER_Y - h_ / 2, cx + w_ / 2, METER_Y + h_ / 2], radius=int(h_ / 2), fill=fill, outline=INK, width=4)
        ccx = cx + w_ / 2 - 40 * sc
        d.ellipse([ccx - 24 * sc, METER_Y - 24 * sc, ccx + 24 * sc, METER_Y + 24 * sc], fill=WHITE if done else (220, 222, 228), outline=INK, width=3)
        if done:
            d.line([(ccx - 12 * sc, METER_Y), (ccx - 3 * sc, METER_Y + 10 * sc), (ccx + 13 * sc, METER_Y - 11 * sc)], fill=GREEN, width=int(7 * sc), joint='curve')
        d.text((cx - 26 * sc, METER_Y + 2), lab, font=font(int(38 * sc), 900), fill=WHITE if done else (120, 124, 136), anchor='mm')

WIN_BG = SH_BG = LOT_BG = BOOTH_BG = NOTICE = NOTE = SLIP = KEYSL = CAR_MID = CAR_FG = PILL_EP = PILL_Q = None
def init_all():
    global WIN_BG, SH_BG, LOT_BG, BOOTH_BG, NOTICE, NOTE, SLIP, KEYSL, CAR_MID, CAR_FG, PILL_EP, PILL_Q
    m.init_static()
    wb = E3.build_window_bg()
    E8.plaque(ImageDraw.Draw(wb), 700, 640, 'מגרש גרירה', 360)
    WIN_BG = wb.filter(ImageFilter.GaussianBlur(S(2)))
    ob = E3.build_office_bg()
    E8.plaque(ImageDraw.Draw(ob), 560, 560, 'מגרש גרירה · קופה', 420)
    SH_BG = ob.filter(ImageFilter.GaussianBlur(S(3)))
    LOT_BG = build_lot_bg(); BOOTH_BG = build_booth_bg().filter(ImageFilter.GaussianBlur(S(2)))
    NOTICE = V1.notice2_layer()
    n = E21.note_layer(); NOTE = n.resize((int(n.width * 0.7), int(n.height * 0.7)), Image.BICUBIC)
    SLIP = slip_layer(); KEYSL = keys_layer()
    CAR_MID = E10.build_car_mid(); CAR_FG = E10.build_car_fg()
    E13.build_crowd()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 560.0, 980.0
    rng = random.Random(int(t * FPS)); sh_ = 0.0
    if name == 'win':
        if t < RUN: z = lerp(1.12, 1.0, ease_out(t / RUN))
        us = t - PAY
        if 0 <= us < 0.4: z = max(z, 1.0 + 0.08 * math.exp(-us * 8)); sh_ = 10 * math.exp(-us * 8)
    elif name == 'two':
        if t - a < 0.3: z = lerp(1.18, 1.0, ease_out((t - a) / 0.3))
        us = t - STAMP
        if 0 <= us < 0.4: z = max(z, 1.0 + 0.1 * math.exp(-us * 8)); cy = 1150
    elif name == 'lot':
        z = lerp(1.2, 1.0, ease_out(clamp((t - a) / 0.3))); sh_ = 4 if t < SPOT else 0
        if t >= SPOT: e = ease_out(clamp((t - SPOT) / 0.12)); z, cx = lerp(1.0, 1.08, e), lerp(560, 600, e)
    elif name == 'booth':
        z = lerp(1.18, 1.0, ease_out(clamp((t - a) / 0.3))); cx, cy = 560.0, 960.0
        if t >= BUTTON: e = ease_out(clamp((t - BUTTON) / 0.15)); z, cx, cy = lerp(1.0, 1.06, e), lerp(560, 640, e), 900
    elif name == 'car':
        z, cx, cy = CARZ, 540.0, CARY
        if t - a < 0.3: z = lerp(CARZ + 0.15, CARZ, ease_out((t - a) / 0.3))
        if 9.8 <= t < TICK: z = lerp(CARZ, CARZ + 0.1, ease_io(clamp((t - 9.8) / (PEAK[1] - 9.8))))
        if t >= TICK: z = CARZ + 0.1
        if t >= SLAM:
            us = t - SLAM; sh_ = 3 + 26 * math.exp(-us * 8)
            e = ease_out(clamp(us / 0.12)); z = lerp(CARZ + 0.1, CARZ + 0.3, e); cy = lerp(CARY, 950, e); cx = lerp(540, 600, e)
        if ENGINE <= t < ENGINE + 0.5: sh_ = max(sh_, 8 * math.exp(-(t - ENGINE) * 5))
    cx += rng.uniform(-sh_, sh_); cy += rng.uniform(-sh_, sh_)
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    img = {'win': scene_win, 'two': scene_two, 'lot': scene_lot, 'booth': scene_booth, 'car': scene_car}[name](t, i)
    z, ccx, ccy = camera(t)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if PEAK[0] <= t < TICK:
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - PEAK[0]) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(36 * k))))
    for s_ in (PAY, STAMP, CHK3, BUTTON, SLAM):
        if s_ <= t < s_ + 0.06:
            frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    for t0, t1, lines, size, yc, fill in CAPTIONS:
        if t0 <= t < t1:
            u = t - t0; sc = 1 + 0.25 * math.exp(-u * 12) * math.cos(u * 20)
            if t0 == 0.0: sc = 1.0
            cap = m.caption_layer(lines, size, fill)
            if abs(sc - 1) > 0.004:
                cap = cap.resize((max(1, int(cap.width * sc)), max(1, int(cap.height * sc))), Image.BICUBIC)
            m.paste_center(frame, cap, W / 2, yc)
    meter(frame, t)
    if t < 2.3:
        frame.alpha_composite(PILL_EP, (40, 70)); frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    elif t >= FREEZE[0] and int(t * 10) % 3 != 0:
        frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (SFX + murmur, no groove)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR); out = np.zeros(n); add = m.add
    rng = np.random.default_rng(220)
    nz = lambda d_: rng.standard_normal(max(1, int(d_ * SR)))
    tt_ = lambda d_: np.arange(max(1, int(d_ * SR))) / SR
    def thump(t0, g=0.8):
        tt = tt_(0.4); f = 150 * np.exp(-tt * 9) + 45
        add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9), t0, g)
    def pop(t0, g=0.22):
        tt = tt_(0.12); f = 300 + 900 * np.exp(-tt * 40)
        add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30), t0, g)
    def whoosh(t0, wl=0.3, g=0.25):
        wt = tt_(wl); add(out, m.bandpass(nz(wl), 700, 6000) * np.sin(np.pi * wt / wl) ** 2 * (wt / wl), t0, g)
    def murmur(t0, t1, g):
        d_ = t1 - t0; tt = tt_(d_)
        mod = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 1.7 * tt + 1))
        env = np.minimum(1, np.minimum(tt / 0.08, (d_ - tt) / 0.08))
        add(out, m.bandpass(nz(d_), 250, 2200) * mod * env, t0, g)
    def check(t0, g=0.12, base=523.3):
        for k_, f_ in enumerate((base, base * 1.26, base * 1.5)):
            add(out, m.tone(f_, 0.22, harm=((1, 1), (2, 0.3)), decay=7), t0 + 0.07 * k_, g)
    def applause(t0, t1, g):
        tc = t0; r = random.Random(7)
        while tc < t1:
            add(out, m.bandpass(nz(0.03), 1200, 6000) * np.exp(-tt_(0.03) * 120), tc, g * r.uniform(0.5, 1.0)); tc += r.uniform(0.015, 0.045)
    murmur(0.0, 4.1, 0.08)
    for k_ in range(4): thump(0.02 + 0.075 * k_, 0.2)                 # running steps into frame
    whoosh(0.0, 0.1, 0.3); thump(RUN, 0.5)
    pop(SH_PAY[0], 0.2)
    thump(PAY, 0.55); add(out, m.highpass(nz(0.06), 2500) * np.exp(-tt_(0.06) * 50), PAY, 0.25); check(CHK1, 0.12)
    for tc in (2.3, 4.1, 6.0, 7.4): whoosh(tc - 0.08, 0.16, 0.08)
    thump(STAMP, 0.8); add(out, m.highpass(nz(0.04), 1200) * np.exp(-tt_(0.04) * 90), STAMP, 0.5); check(CHK2, 0.13, 587.3)
    tc = KEYS[0] + 0.1
    while tc < GRABK:                                                   # key jingle
        add(out, m.tone(3200 + 400 * ((tc * 10) % 2), 0.05, harm=((1, 1), (2.3, 0.4)), decay=30), tc, 0.05); tc += 0.06
    murmur(4.1, 6.0, 0.05)
    for k_ in range(10): thump(4.15 + 0.17 * k_, 0.18)                  # running in the lot
    pop(SPOT, 0.26); check(CHK3, 0.15, 659.3)
    murmur(6.0, 7.4, 0.04); pop(GO[0], 0.22)
    add(out, m.tone(880, 0.12, harm=((1, 1),), decay=8), BUTTON - 0.05, 0.15)       # button beep
    tt = tt_(0.7); add(out, m.bandpass(nz(0.7), 200, 900) * np.exp(-tt * 2) * 0.6, BUTTON, 0.18)   # barrier motor
    tt = tt_(1.0); f = 60 + 40 * np.exp(-tt * 3)                                       # engine start + idle
    add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * tt)) * np.exp(-tt * 0.8), ENGINE, 0.35)
    tt = tt_(PEAK[0] - ENGINE - 1.0); add(out, np.sin(2 * np.pi * 52 * tt) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * tt)), ENGINE + 1.0, 0.08)
    applause(ENGINE + 0.1, 9.7, 0.05)
    tc = MUNCH[0]
    while tc < MUNCH[1]:
        add(out, m.bandpass(nz(0.07), 1500, 7000) * np.exp(-tt_(0.07) * 45), tc, 0.15); tc += 0.13
    for hb in (PEAK[0] + 0.02, PEAK[0] + 0.5 - 0.1):                     # heartbeat in silence
        thump(hb, 0.32); thump(hb + 0.16, 0.22)
    add(out, m.tone(1760, 0.18, harm=((1, 1),), decay=4), TICK, 0.2)  # the clock beep: 16:00
    thump(SLAM, 1.0); add(out, m.highpass(nz(0.06), 900) * np.exp(-tt_(0.06) * 60), SLAM, 0.7)   # the break: one SLAM
    out += m.lowpass(nz(DUR), 300) * 0.008
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
    tag = os.environ.get('TAG', '')
    if mode == 'audio':
        build_audio(sys.argv[2]); print('ok'); return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames):
            sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, f'ep20{tag}_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'ep20{tag}_audio.wav'); build_audio(wav); print('audio ok')
    mp4 = os.path.join(OUTDIR, f'{TAG_OUT}{tag}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=_init_worker) as pool:
        for k, buf in enumerate(pool.imap(_render, range(NF), chunksize=4)):
            proc.stdin.write(buf)
            if k % 60 == 0: print('frame', k, '/', NF, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
