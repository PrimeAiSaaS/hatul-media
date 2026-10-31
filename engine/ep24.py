#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 24: הבנק שלי: נציג אנושי (season 5 "החשבון" ep 4; built 31.10 under §P, ~12.4 s;
experiment one_take = the whole episode is ONE continuous camera move, no cuts; the loop seam is the camera arriving
back at its frame-0 position).
Beat sheet (§P1):
  WANT (frame 0, in motion): one human at הבנק שלי. Big face, his phone on speaker beside it, the IVR menu wheel spinning
  ("לנציג הקש 9"), his paw already tapping 9, 9, 0#. Hook "נציג אנושי בבנק שלי? / הפעם אני מגיע אליו."
  PLANT: his paw's habit of tapping 9 — frame 0 (the trick), again mid-hold under the x64 (nervous taps), and the paw
  resting on the keypad at the peak. Never pointed at. Misdirection: the battery icon, red 3% → 2% → 1% (stakes).
  CLIMB: the 9-9-0# trick beats the menu ✓ (chip 1) → camera drifts back through the branch lobby, the other waiters on
  speakerphone come into frame, x64 time-lapse inside the move: "מיקומך בתור" 47 → 12 ✓ (chip 2) → 3 → 2 → 1 ✓ (chip 3,
  gold), the waiters cheer + confetti.
  PEAK: the camera pushes back in to his face, ringing, "שלום, מדברת שרית..." — a human! He inhales for his speech
  (silence + heartbeat, 0.5 s). Battery 1%, it holds.
  BREAK (his_own_hand, last 0.75 s): his paw, out of habit, taps 9 — BEEP — "חזרת לתפריט הראשי", the wheel spins again,
  chips snap empty, 0.45 s frozen face; the camera is already at its frame-0 position (loop). No וואלה tail, no CTA.

  python3 ep24.py test 0 0.5 1.4 2.4 3.4 4.4 5.7 6.5 7.7 8.8 9.6 10.4 11.1 11.62 11.9 12.3 -> out/ep24_contact.png
  python3 ep24.py render                                                                      -> out/ep24_human.mp4
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
import ep12 as E12
import ep13 as E13
import ep18 as E18
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

DUR = float(os.environ.get('DUR', '12.4'))
NF = int(round(DUR * FPS))
OUTDIR = m.OUTDIR
YELLOW = (255, 221, 51); GREEN = (36, 168, 84); GOLD = (230, 170, 30)
BLUE = (28, 104, 226); RED = (214, 44, 52)
QUEUE = int(os.environ.get('QUEUE', '475'))
EP_LABEL = 'פרק 24'
TAG_OUT = os.environ.get('OUTNAME', 'ep24_human')
BIGF = os.environ.get('BIGF', '0') == '1'          # probe: bigger face

# ------------------------------------------------------------------ timeline
TAPS0 = (0.06, 0.42, 0.78)    # 9, 9, 0#  (frame 0: the trick = the plant)
TAPS_MID = (3.9, 4.25, 4.6)   # nervous 9-taps under the x64 (plant, mid-climb)
CHK1 = 1.2                    # "מעביר לנציג..." (menu beaten)
QSTART = 2.0                  # "מיקומך בתור: 47"
FF = (3.0, 5.6)               # x64 time-lapse inside the move
CHK2 = 5.6                    # 12
TICKS = ((6.3, 3), (6.95, 2), (7.6, 1))
CHK3 = 7.6                    # 1 -> cheer
CHEER = (7.6, 9.2)
RING = (9.25, 10.1)
HELLO = (10.12, 11.0)         # "שלום, מדברת שרית..."
PEAK = (11.0, 11.5)           # he inhales for his speech: silence + heartbeat
TAPB = 11.5                   # the habit tap
BEEP = 11.58                  # the break
FREEZE = (11.68, DUR)
BUB_TRICK = (1.3, 2.25)
BUB_CHEER = (7.85, 9.0)

CAPTIONS = [  # (t0, t1, lines, size, y, fill)
    (0.0, 2.0, ['נציג אנושי בבנק שלי?', 'הפעם אני מגיע אליו.'], 92, 290, WHITE),     # keyword on frame 1
    (5.65, 7.55, ['מיקומך בתור:', '12... 3... 2...'], 96, 290, WHITE),
    (7.6, 9.6, ['מיקומך בתור: 1.', 'נציג אנושי!'], 100, 290, WHITE),
]

def count_at(t):
    if t < FF[0]: return 47
    if t < FF[1]: return int(round(lerp(47, 12, ease_io((t - FF[0]) / (FF[1] - FF[0])))))
    n = 12
    for tc, v in TICKS:
        if t >= tc: n = v
    return n

def battery_at(t):
    if t < 6.0: return 3
    if t < RING[0]: return 2
    return 1

def screen_mode(t):
    if t >= BEEP: return 'menu_back'
    if t < CHK1: return 'menu'
    if t < QSTART: return 'transfer'
    if t < RING[0]: return 'queue'
    if t < HELLO[0]: return 'ring'
    return 'call'

burst = E18.burst; confetti = E18.confetti

# ------------------------------------------------------------------ props
PW, PH = 300, 540
def wheel(d, cx, cy, r, ang, col=(255, 255, 255)):
    """the IVR 'menu' wheel: a ring with two chasing arrows"""
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], outline=col + (90,), width=iw(10))
    for k in range(2):
        a0 = ang + k * 180
        d.arc([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], a0, a0 + 110, fill=col, width=iw(12))
        a = math.radians(a0 + 110)
        tip = (cx + r * math.cos(a), cy + r * math.sin(a))
        tg = (-math.sin(a), math.cos(a)); nr = (math.cos(a), math.sin(a))
        poly(d, [(tip[0] + tg[0] * 24, tip[1] + tg[1] * 24), (tip[0] + nr[0] * 18, tip[1] + nr[1] * 18), (tip[0] - nr[0] * 18, tip[1] - nr[1] * 18)], fill=col)

def battery(d, x, y, pct, blink_on=True):
    col = (230, 40, 40) if blink_on else (120, 40, 40)
    d.rounded_rectangle([S(x - 44), S(y - 15), S(x + 10), S(y + 15)], radius=S(5), outline=WHITE, width=iw(3))
    d.rectangle([S(x + 10), S(y - 6), S(x + 15), S(y + 6)], fill=WHITE)
    d.rectangle([S(x - 40), S(y - 11), S(x - 40 + max(3, 4 * pct)), S(y + 11)], fill=col)
    d.text((S(x - 54), S(y + 1)), f'{pct}%', font=font(S(26), 900), fill=col if blink_on else WHITE, anchor='rm')

def phone_layer(t):
    mode = screen_mode(t)
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(42), fill=(20, 20, 24))
    top = {'menu': (40, 70, 150), 'menu_back': (40, 70, 150), 'transfer': (24, 120, 70), 'queue': (40, 70, 150),
           'ring': (30, 40, 70), 'call': (24, 110, 70)}[mode]
    bot = tuple(int(c * 0.55) for c in top)
    for y in range(12, PH - 12, 6):
        v = y / PH
        pd.rectangle([S(12), S(y), S(PW - 12), S(y + 6)], fill=tuple(int(lerp(a, b, v)) for a, b in zip(top, bot)))
    pd.rounded_rectangle([S(PW / 2 - 40), S(22), S(PW / 2 + 40), S(40)], radius=S(9), fill=(10, 10, 12))
    pct = battery_at(t)
    battery(pd, PW - 30, 64, pct, blink_on=(pct > 1 or int(t * 4) % 2 == 0))
    pd.text((S(36), S(64)), 'רמקול', font=font(S(22), 800), fill=(220, 226, 240), anchor='lm')
    pd.text((S(PW / 2), S(116)), 'הבנק שלי', font=font(S(40), 900), fill=WHITE, anchor='mm')
    if mode in ('menu', 'menu_back'):
        wheel(pd, PW / 2, 240, 66, (t * 360 * 1.3) % 360)
        pd.text((S(PW / 2), S(345)), 'לנציג', font=font(S(38), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(395)), 'הקש 9', font=font(S(48), 900), fill=YELLOW, anchor='mm')
        if mode == 'menu_back':
            pd.rounded_rectangle([S(10), S(90), S(PW - 10), S(150)], radius=S(14), fill=RED, outline=WHITE, width=iw(3))
            pd.text((S(PW / 2), S(121)), 'חזרת לתפריט הראשי', font=font(S(26), 900), fill=WHITE, anchor='mm')
    elif mode == 'transfer':
        u = t - CHK1
        wheel(pd, PW / 2, 250, 74, (t * 360 * 2.5) % 360, (180, 255, 200))
        pd.text((S(PW / 2), S(390)), 'מעביר לנציג...', font=font(S(36), 900), fill=WHITE, anchor='mm')
    elif mode == 'queue':
        n = count_at(t)
        pd.text((S(PW / 2), S(200)), 'מיקומך בתור:', font=font(S(36), 900), fill=(220, 226, 240), anchor='mm')
        sc = 1.0
        for tc in [CHK2] + [tc for tc, _ in TICKS]:
            if 0 <= t - tc < 0.3: sc = 1 + 0.4 * math.exp(-(t - tc) * 14)
        col = YELLOW if n > 1 else (120, 255, 150)
        pd.text((S(PW / 2), S(310)), str(n), font=font(S(int(150 * sc)), 900), fill=col, anchor='mm')
        for k in range(5):                                     # hold-music bars
            hgt = 14 + 26 * abs(math.sin(t * (9 if FF[0] <= t < FF[1] else 5) + k * 1.3))
            pd.rounded_rectangle([S(PW / 2 - 70 + k * 30), S(450 - hgt), S(PW / 2 - 52 + k * 30), S(450)], radius=S(5), fill=(170, 190, 240))
    elif mode == 'ring':
        k = 0.5 + 0.5 * math.sin(t * 14)
        E(pd, PW / 2, 270, 70 + 16 * k, 70 + 16 * k, outline=(200, 255, 210), width=5)
        E(pd, PW / 2, 270, 56, 56, fill=GREEN, outline=WHITE, width=4)
        pd.text((S(PW / 2), S(274)), 'נ', font=font(S(56), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(400)), 'מחבר לנציג...', font=font(S(34), 900), fill=WHITE, anchor='mm')
    else:   # call: a human
        E(pd, PW / 2, 250, 66, 66, fill=(236, 184, 146), outline=WHITE, width=4)
        for (x, y) in ((-46, -40), (-10, -56), (28, -50), (52, -20), (-56, -6)):
            E(pd, PW / 2 + x, 250 + y, 26, 26, fill=SH.HAIR)
        E(pd, PW / 2 - 20, 254, 6, 6, fill=INK); E(pd, PW / 2 + 20, 254, 6, 6, fill=INK)
        pd.arc([S(PW / 2 - 18), S(266), S(PW / 2 + 18), S(286)], 20, 160, fill=SH.LIP, width=iw(4))
        pd.text((S(PW / 2), S(360)), 'שרית', font=font(S(46), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(408)), 'נציגה אנושית', font=font(S(28), 800), fill=(200, 255, 210), anchor='mm')
        s_ = max(0, t - HELLO[0])
        pd.text((S(PW / 2), S(440)), f'00:0{min(9, int(s_))}', font=font(S(30), 800), fill=(220, 226, 240), anchor='mm')
    return lay

def key_pop(img, c, u, label):
    """the little key that pops off the phone when he taps"""
    if not (0 <= u < 0.35): return
    sc = 1.2 - 0.2 * ease_out(clamp(u / 0.1)); a = int(255 * clamp((0.35 - u) / 0.15))
    lay = Image.new('RGBA', (S(120), S(120)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([S(6), S(6), S(114), S(114)], fill=(250, 250, 250, a), outline=(20, 20, 24, a), width=iw(5))
    d.text((S(60), S(62)), label, font=font(S(54 if len(label) == 1 else 40), 900), fill=(20, 20, 24, a), anchor='mm')
    lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    m.paste_center(img, lay, S(c[0]), S(c[1] - 60 * u))

def shadow_paste(img, lay, c, a=100, off=(14, 18), blur=10):
    shd = Image.new('RGBA', lay.size, (0, 0, 0, 0)); shd.paste((0, 0, 0, a), mask=lay.split()[3]); shd = shd.filter(ImageFilter.GaussianBlur(S(blur)))
    m.paste_center(img, shd, S(c[0] + off[0]), S(c[1] + off[1])); m.paste_center(img, lay, S(c[0]), S(c[1]))

def small_phone(d, c, ang=0):
    pts = xform([(-26, -46), (26, -46), (26, 46), (-26, 46)], c[0], c[1], ang)
    poly(d, pts, fill=(28, 28, 34), outline=(8, 8, 10), width=3)
    pts = xform([(-19, -36), (19, -36), (19, 36), (-19, 36)], c[0], c[1], ang)
    poly(d, pts, fill=(70, 100, 170))

# ------------------------------------------------------------------ meter (screen space, under the hook)
METER_Y = 470
METER = [('תפריט', CHK1), ('בתור', CHK2), ('נציג', CHK3)]
def meter(frame, t):
    d = ImageDraw.Draw(frame)
    reset = t >= BEEP
    full = (t >= CHK3) and not reset
    xs = [850, 540, 230]                    # RTL: first chip on the right
    for k, (lab, tc) in enumerate(METER):
        done = (t >= tc) and not reset
        u = t - tc
        sc = 1.0 + (0.35 * math.exp(-u * 10) * math.cos(u * 20) if (0 <= u < 0.5 and not reset) else 0.0)
        if reset and t - BEEP < 0.3: sc = 1.0 + 0.2 * math.exp(-(t - BEEP) * 12)
        w_, h_ = 290 * sc, 76 * sc
        cx = xs[k] + (random.Random(int(t * FPS) + k).uniform(-10, 10) if (reset and t - BEEP < 0.3) else 0)
        fill = (GREEN if not full else GOLD) if done else (250, 250, 250)
        d.rounded_rectangle([cx - w_ / 2 + 5, METER_Y - h_ / 2 + 8, cx + w_ / 2 + 5, METER_Y + h_ / 2 + 8], radius=int(h_ / 2), fill=(0, 0, 0, 90))
        d.rounded_rectangle([cx - w_ / 2, METER_Y - h_ / 2, cx + w_ / 2, METER_Y + h_ / 2], radius=int(h_ / 2), fill=fill, outline=INK, width=4)
        ccx = cx + w_ / 2 - 40 * sc
        d.ellipse([ccx - 24 * sc, METER_Y - 24 * sc, ccx + 24 * sc, METER_Y + 24 * sc], fill=WHITE if done else (220, 222, 228), outline=INK, width=3)
        if done:
            d.line([(ccx - 12 * sc, METER_Y), (ccx - 3 * sc, METER_Y + 10 * sc), (ccx + 13 * sc, METER_Y - 11 * sc)], fill=GREEN, width=int(7 * sc), joint='curve')
        d.text((cx - 26 * sc, METER_Y + 2), lab, font=font(int(36 * sc), 900), fill=WHITE if done else (120, 124, 136), anchor='mm')

# ------------------------------------------------------------------ the cat
def base_cat():
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.3); return st

def all_taps():
    return [(x, '9' if k < 2 else '0#') for k, x in enumerate(TAPS0)] + [(x, '9') for x in TAPS_MID] + [(TAPB, '9')]

def tap_amt(t):
    """0..1 how far the tapping paw is pressed"""
    v = 0.0
    for tc, _ in all_taps():
        u = t - tc
        if -0.08 <= u < 0.14: v = max(v, 1 - abs(u - 0.0) / 0.1 if u < 0 else 1 - u / 0.14)
    return clamp(v)

def cat_state(t, i):
    st = base_cat(); rot, dy, puff = 0.0, 0.0, 0.0
    if t < CHK1:                                         # the trick: focused, tongue-in-cheek
        st.update(lid=0.25, pupil='normal', brow='annoyed', mouth='squish', look=(-26, 6), blush=0.1)
        rot = -3 + 3 * tap_amt(t)
    elif t < 2.4:                                        # it works!
        u = t - CHK1
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-26 * math.exp(-u * 3), look=(-12, 0), blush=0.6)
        dy = -20 * abs(math.sin(u * 9)) * math.exp(-u * 2)
    elif t < FF[0]:
        st.update(lid=0.3, pupil='normal', mouth='smile_small', look=(-22, 6), blush=0.4)
    elif t < FF[1]:                                      # the hold, x64: chill bob, nervous taps
        st.update(lid=0.55, pupil='normal', mouth='goofy', look=(-18, 8), blush=0.5)
        rot = 4 * math.sin(t * 14); dy = 6 * math.sin(t * 28)
        if TAPS_MID[0] - 0.1 <= t < TAPS_MID[-1] + 0.2: st.update(lid=0.2, mouth='flat', brow='annoyed', look=(-26, 8))
    elif t < CHK3:                                       # 12 ... 3 ... 2 ...: eyes widen on every tick
        k = 0
        for tc, _ in TICKS:
            if t >= tc: k += 1
        u = t - max([CHK2] + [tc for tc, _ in TICKS if t >= tc])
        st.update(lid=0.0, pupil='big', brow='up', mouth='w' if k >= 1 else 'smile_small', look=(-20, 2), ear_dy=-14 - 6 * k, blush=0.3 + 0.15 * k)
        dy = -16 * math.exp(-u * 8) * abs(math.cos(u * 18))
    elif t < CHEER[1]:                                   # 1!
        u = t - CHK3
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-28 * math.exp(-u * 2), look=(-8, 0), blush=0.9)
        dy = -24 * abs(math.sin(u * 8)) * math.exp(-u * 1.1)
    elif t < HELLO[0]:                                   # ringing: hope
        st.update(lid=0.0, pupil='big', brow='up', mouth='flat', look=(-24, 4), ear_dy=-12, blush=0.3)
        rot = 1.5 * math.sin(t * 20) * (RING[0] <= t)
    elif t < PEAK[0]:                                    # a human voice
        u = t - HELLO[0]
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-10, 0), ear_dy=-22 * math.exp(-u * 2), blush=1.0)
    elif t < BEEP:                                       # the peak: he inhales for his speech
        u = clamp((t - PEAK[0]) / 0.35)
        st.update(lid=0.0, pupil='big', brow='up', mouth='squish', look=(0, -4), ear_dy=-18, blush=0.8)
        puff = ease_out(u); dy = -14 * ease_out(u)
        st['sx'] = 1.0 + 0.05 * puff; st['sy'] = 1.0 + 0.03 * puff
    else:                                                # frozen
        u = t - BEEP
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', look=(0, 0), blush=0.0, ear_droop=0.6 * clamp(u / 0.2),
                  ear_dy=-20 * math.exp(-u * 6), twitch=(0.25 < u < 0.6 and int(t * 12) % 2 == 0))
        puff = max(0.0, 1 - u / 0.12); dy = -14 * puff
    return st, rot, dy, puff

# ------------------------------------------------------------------ the scene (one world, one camera)
HX, HY, F = 690, 1080, (1.9 if BIGF else 1.75)
PHONE_C = (310, 1000)
# waiters on the benches (sprite, x, y, scale, phase, flip, phone dx, phone dy)
WAIT = [('h1', 120, 800, 0.40, 0.3, False, 95, 40), ('c3', 980, 720, 0.42, 1.4, True, -92, 50),
        ('c0', 70, 1450, 0.58, 2.2, False, 120, 40), ('h2', 1030, 1420, 0.52, 0.9, True, -110, 60)]

def waiter_mood(t):
    if t < CHK2: return 2                    # bored
    if t < CHK3: return 0                    # leaning in
    if t < RING[1]: return 1                 # cheering
    return 2 if t < BEEP else 1

def draw_world(t, i):
    img = BG.copy(); d = ImageDraw.Draw(img)
    # branch board: the number being called jumps for no reason (gag #1, §O4)
    seq = [17, 64, 9, 311, 12, 880, 17, 5, 402]
    sp = 16 if FF[0] <= t < FF[1] else 1.3
    num = seq[int(t * sp) % len(seq)]
    d.rounded_rectangle([S(760), S(548), S(1000), S(652)], radius=S(14), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(5))
    d.text((S(935), S(600)), str(num), font=font(S(64), 900), fill=E3.AMBER, anchor='mm')
    d.text((S(812), S(600)), 'מספר', font=font(S(28), 800), fill=(200, 160, 80), anchor='mm')
    # waiters
    mood = waiter_mood(t)
    cheer = CHEER[0] <= t < RING[1]
    ff = FF[0] <= t < FF[1]
    for name, x, y, sc, ph, flip, pdx, pdy in WAIT:
        jump = (-30 * abs(math.sin(t * 9 + ph))) if cheer else 0
        bob = (10 * math.sin(t * 30 + ph)) if ff else 6 * math.sin(t * 3 + ph)
        E13.paste_sprite(img, name, mood, x + 4 * math.sin(t * 2 + ph), y + bob + jump, sc, flip=flip)
        d = ImageDraw.Draw(img)
        pc = (x + pdx * sc / 0.45, y + pdy + bob + jump)
        small_phone(d, pc, -12 if not flip else 12)
        if t < CHK3 or t >= RING[1]:                  # their own hold music
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            ph2 = (t * (2.4 if ff else 0.8) + ph) % 1.0
            m.draw_note(od, pc[0] + (14 if not flip else -40), pc[1] - 60 - 70 * ph2, int(200 * math.sin(math.pi * ph2)), (int(ph * 10) % 2) == 0)
            img.alpha_composite(ov); d = ImageDraw.Draw(img)
    if cheer: confetti(img, t - CHEER[0], 1.9)
    d = ImageDraw.Draw(img)
    # the cat
    st, rot, dy, puff = cat_state(t, i)
    E(d, HX, 1700 - 10 * puff, 450 + 30 * puff, 470 + 20 * puff, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1760, 210 + 20 * puff, 320, fill=CREAM)
    E12.paste_head(img, st, i, HX, HY + dy, F, rot)
    d = ImageDraw.Draw(img)
    # phone held up beside the face (left paw), screen to camera
    pc = (PHONE_C[0] + 4 * math.sin(t * 2.0), PHONE_C[1] + 6 * math.sin(t * 2.6))
    if t < 0.12: pc = (pc[0] - 30 * (1 - t / 0.12), pc[1] + 40 * (1 - t / 0.12))
    capsule(d, (HX - 250, 1500), (pc[0] + 30, pc[1] + PH * 0.42), 120, FUR, OUT, 4)
    lay = phone_layer(t).rotate(-5, resample=Image.BICUBIC, expand=True)
    shadow_paste(img, lay, pc, 110, (16, 20), 12)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (pc[0] + 10, pc[1] + PH * 0.47), 8)                  # holding paw
    # tapping paw (the plant): hovers over the keypad, presses on each tap
    a = tap_amt(t)
    rest = (pc[0] + 120, pc[1] + 170)
    press = (pc[0] + 60, pc[1] + 140)
    tp = lerp2(rest, press, a)
    capsule(d, (HX + 180, 1540), (tp[0] + 30, tp[1] + 40), 110, FUR, OUT, 4)
    E12.big_paw(d, tp, -30, 0.9)
    for tc, lab in all_taps():
        key_pop(img, (pc[0] - 40, pc[1] + 40), t - tc, lab)
    burst(img, (pc[0], pc[1]), t - CHK1, (120, 255, 160), 170, 10, 0.35)
    burst(img, (pc[0], pc[1]), t - CHK3, (255, 236, 120), 170, 12, 0.45)
    burst(img, (pc[0], pc[1]), t - BEEP, (255, 120, 120), 170, 12, 0.35)
    return img

# ------------------------------------------------------------------ camera: one continuous move
Z0, C0 = 1.38, (495.0, 1000.0)          # frame-0 framing = the loop seam
ZW, CW_ = 1.0, (540.0, 960.0)
def camera(t):
    if t < 1.5:
        z, c = lerp(Z0, Z0 - 0.03, t / 1.5), (C0[0] + 10 * t / 1.5, C0[1])
        z0b, c0b = z, c
    if t < 1.5: pass
    elif t < 5.0:                                    # drift back through the lobby (waiters come into frame)
        e = ease_io((t - 1.5) / 3.5)
        z = lerp(Z0 - 0.03, ZW, e); c = lerp2((C0[0] + 10, C0[1]), CW_, e)
    elif t < 8.4:                                    # wide, slow lateral drift
        e = ease_io((t - 5.0) / 3.4)
        z = lerp(ZW, ZW + 0.04, e); c = (lerp(CW_[0], 560, e), lerp(CW_[1], 970, e))
    elif t < 10.1:                                   # push back in to his face
        e = ease_io((t - 8.4) / 1.7)
        z = lerp(ZW + 0.04, Z0, e); c = lerp2((560, 970), C0, e)
    elif t < BEEP:                                   # creeping in on the peak
        e = ease_io((t - 10.1) / (BEEP - 10.1))
        z = lerp(Z0, Z0 + 0.06, e); c = lerp2(C0, (495, 1010), e)
    else:                                            # snap on the break, then settle back to frame 0
        u = t - BEEP
        e = ease_out(clamp(u / 0.1))
        z = lerp(Z0 + 0.06, Z0 + 0.12, e); c = lerp2((495, 1010), (505, 1030), e)
        if t >= FREEZE[0] + 0.3:
            e2 = ease_io(clamp((t - (FREEZE[0] + 0.3)) / (DUR - (FREEZE[0] + 0.3))))
            z = lerp(Z0 + 0.12, Z0, e2); c = lerp2((505, 1030), C0, e2)
    sh_ = 0.0
    for s0, amp in ((TAPS0[0], 10), (CHK1, 8), (CHK3, 12), (BEEP, 20)):
        us = t - s0
        if 0 <= us < 0.35: sh_ = max(sh_, 2 + amp * math.exp(-us * 9))
    rng = random.Random(int(t * FPS))
    return z, c[0] + rng.uniform(-sh_, sh_), c[1] + rng.uniform(-sh_, sh_)

def ff_overlay(frame):
    frame.alpha_composite(m.SCAN)
    fd = ImageDraw.Draw(frame)
    for x0 in (858, 902):
        fd.polygon([(x0, 360), (x0 + 44, 390), (x0, 420)], fill=WHITE, outline=(10, 10, 12), width=4)
    fd.text((1005, 390), 'x64', font=font(46, 900), fill=WHITE, anchor='mm', stroke_width=6, stroke_fill=(10, 10, 12))

def screen_bubble(frame, text, u, box, tip, side):
    lay = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    SH.bubble(lay, text, u, box, tip, side=side)
    bb = lay.getbbox()
    if not bb: return
    crop = lay.crop(bb).resize((max(1, (bb[2] - bb[0]) // K), max(1, (bb[3] - bb[1]) // K)), Image.LANCZOS)
    frame.alpha_composite(crop, (bb[0] // K, bb[1] // K))

def bubbles(frame, t):
    if BUB_TRICK[0] <= t < BUB_TRICK[1]: screen_bubble(frame, 'הטריק עובד!', t - BUB_TRICK[0], (720, 640, 420, 120), (720, 790), 1)
    if BUB_CHEER[0] <= t < BUB_CHEER[1]: screen_bubble(frame, 'יאללה, חתול!', t - BUB_CHEER[0], (820, 650, 400, 120), (960, 780), 1)
    if HELLO[0] <= t < HELLO[1]: screen_bubble(frame, 'שלום, מדברת שרית...', t - HELLO[0], (560, 650, 660, 130), (330, 800), -1)

BG = PILL_EP = PILL_Q = None
def init_all():
    global BG, PILL_EP, PILL_Q
    m.init_static()
    bg = E3.build_window_bg()
    d = ImageDraw.Draw(bg)
    E8.plaque(d, 330, 600, 'הבנק שלי', 300)
    # benches along the lobby
    for y0 in (930, 1560):
        d.rounded_rectangle([S(-20), S(y0), S(1100), S(y0 + 40)], radius=S(10), fill=(150, 108, 70), outline=(96, 66, 40), width=iw(4))
    BG = bg.filter(ImageFilter.GaussianBlur(S(2)))
    E13.build_crowd()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def draw_frame(i):
    t = i / FPS
    img = draw_world(t, i)
    z, ccx, ccy = camera(t)
    cw, ch = W * K / z, H * K / z
    left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
    img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if FF[0] <= t < FF[1]: ff_overlay(frame)
    if PEAK[0] <= t < BEEP:                                  # the held beat: vignette pulse with the heartbeat
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - PEAK[0]) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(40 * k))))
    for s_ in (TAPS0[0], CHK1, CHK2, CHK3, BEEP):
        if s_ <= t < s_ + 0.06:
            frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(100 * (1 - (t - s_) / 0.06)))))
    for t0, t1, lines, size, yc, fill in CAPTIONS:
        if t0 <= t < t1:
            u = t - t0; sc = 1 + 0.25 * math.exp(-u * 12) * math.cos(u * 20)
            if t0 == 0.0: sc = 1.0
            cap = m.caption_layer(lines, size, fill)
            if abs(sc - 1) > 0.004:
                cap = cap.resize((max(1, int(cap.width * sc)), max(1, int(cap.height * sc))), Image.BICUBIC)
            m.paste_center(frame, cap, W / 2, yc)
    meter(frame, t)
    bubbles(frame, t)
    if t < 2.0:
        frame.alpha_composite(PILL_EP, (40, 70)); frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    elif t >= FREEZE[0] and int(t * 10) % 3 != 0:            # the ticket pill flickers over the frozen face (§O3)
        frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (SFX + phone hold music + murmur, no groove)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR); out = np.zeros(n); add = m.add
    rng = np.random.default_rng(242)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    def thump(t0, g=0.8):
        tt = tt_(0.4); f = 150 * np.exp(-tt * 9) + 45
        add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9), t0, g)
    def pop(t0, g=0.22):
        tt = tt_(0.12); f = 300 + 900 * np.exp(-tt * 40)
        add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30), t0, g)
    def dtmf(t0, lo=852, hi=1477, g=0.16, d_=0.11):
        tt = tt_(d_); env = np.minimum(1, np.minimum(tt / 0.005, (d_ - tt) / 0.01))
        add(out, (np.sin(2 * np.pi * lo * tt) + np.sin(2 * np.pi * hi * tt)) * 0.5 * env, t0, g)
    def murmur(t0, t1, g):
        d_ = t1 - t0; tt = tt_(d_)
        mod = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 1.7 * tt + 1))
        env = np.minimum(1, np.minimum(tt / 0.08, (d_ - tt) / 0.08))
        add(out, m.bandpass(nz(d_), 250, 2200) * mod * env, t0, g)
    def check(t0, g=0.12, base=523.3):
        for k_, f_ in enumerate((base, base * 1.26, base * 1.5)):
            add(out, m.tone(f_, 0.22, harm=((1, 1), (2, 0.3)), decay=7), t0 + 0.07 * k_, g)
    def applause(t0, t1, g):
        tc = t0; r = random.Random(5)
        while tc < t1:
            add(out, m.bandpass(nz(0.03), 1200, 6000) * np.exp(-tt_(0.03) * 120), tc, g * r.uniform(0.5, 1.0)); tc += r.uniform(0.015, 0.045)
    # hold music from the speakerphone: normal, then x64 (chipmunk, resampled), then normal again
    hm = m.phone_line(m.hold_music(30.0))
    def seg(x, t0, t1, g, speed=1.0):
        L = int((t1 - t0) * SR)
        if speed == 1.0: y = x[:L]
        else:
            idx = (np.arange(L) * speed) % (len(x) - 1); y = x[idx.astype(int)]
        env = np.minimum(1, np.minimum(np.arange(L) / (0.03 * SR), (L - np.arange(L)) / (0.03 * SR)))
        add(out, y * env, t0, g)
    murmur(0.0, PEAK[0] - 0.1, 0.06)
    seg(hm, QSTART, FF[0], 0.10); seg(hm, FF[0], FF[1], 0.09, 3.2); seg(hm[int(6 * SR):], FF[1], RING[0] - 0.05, 0.10)
    # menu: a soft synthetic "menu" chime loop under frame 0 and after the break
    for t0 in (0.0, BEEP + 0.15):
        for k_, f_ in enumerate((659.3, 784.0, 987.8)):
            add(out, m.tone(f_, 0.2, harm=((1, 1),), decay=8), t0 + 0.1 * k_, 0.05)
    thump(TAPS0[0], 0.5)
    for k_, tc in enumerate(TAPS0): dtmf(tc, 941 if k_ == 2 else 852, 1336 if k_ == 2 else 1477)
    dtmf(TAPS0[2] + 0.13, 941, 1633, 0.12)                         # '#'
    thump(CHK1, 0.4); check(CHK1, 0.13)
    pop(BUB_TRICK[0], 0.18)
    for tc in TAPS_MID: dtmf(tc, g=0.07, d_=0.06)                    # nervous taps under the x64
    add(out, m.bandpass(nz(0.5), 600, 5000) * np.linspace(0, 1, int(0.5 * SR)), FF[0] - 0.25, 0.08)   # rewind-ish riser into x64
    thump(CHK2, 0.45); check(CHK2, 0.13, 587.3)
    for k_, (tc, _) in enumerate(TICKS): pop(tc, 0.2 + 0.05 * k_); thump(tc, 0.25 + 0.1 * k_)
    check(CHK3, 0.16, 659.3); applause(CHEER[0], CHEER[1] - 0.1, 0.08)
    for k_ in range(6): pop(CHEER[0] + 0.05 + 0.11 * k_, 0.08)
    pop(BUB_CHEER[0], 0.16)
    tc = RING[0]
    while tc < RING[1] - 0.05:                                       # ringback through the speaker
        L_ = min(0.32, RING[1] - tc); tt = tt_(L_)
        add(out, m.phone_line((np.sin(2 * np.pi * 425 * tt)) * 0.7), tc, 0.12); tc += 0.5
    pop(HELLO[0], 0.22)
    tt = tt_(0.7); add(out, m.phone_line(np.sin(2 * np.pi * (220 + 30 * np.sin(2 * np.pi * 5 * tt)) * tt) * np.exp(-tt * 2) * 0.5), HELLO[0] + 0.05, 0.10)   # a voice through the speaker (muffled)
    add(out, m.bandpass(nz(0.35), 300, 3000) * np.linspace(0, 1, int(0.35 * SR)) ** 2, PEAK[0], 0.06)   # the inhale
    for hb in (PEAK[0] + 0.02, PEAK[0] + 0.45):
        thump(hb, 0.32); thump(hb + 0.16, 0.22)
    dtmf(TAPB, g=0.22)                                                # the habit tap: 9
    thump(BEEP, 0.95); add(out, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), BEEP, 0.5)
    for k_, f_ in enumerate((987.8, 784.0, 523.3)):                  # descending "back to menu" tones
        add(out, m.tone(f_, 0.14, harm=((1, 1),), decay=10), BEEP + 0.03 + 0.09 * k_, 0.12)
    murmur(BEEP + 0.05, DUR, 0.03)
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
        sheet.save(os.path.join(OUTDIR, f'ep24{tag}_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'ep24{tag}_audio.wav'); build_audio(wav); print('audio ok')
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
