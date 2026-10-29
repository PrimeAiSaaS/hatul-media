#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 20: הגרר (season 4 "הרכב" finale, built 27.10, 12.0 s; experiment opening_crowd_faces).
Frame 0 is already moving: the chill cat big at the wheel, ep16's notice still on the windshield, the car already tilting up
on the tow hook, amber beacon light sweeping, neighbours' faces in the rear window. CLANK at 0.1 (jolt), hook
"גרר לקח לך את הרכב? / ואתה עוד בפנים?". "רגע! אני בפנים!". The tow driver (Sharit's rig recoloured, hi-vis vest, tag "גרר"):
"בלי טסט? נגרר, מותק." → snap zoom "לכתובת הרשומה." + dun-dun. Cat close-up frozen: "הכתובת הרשומה? / של סבתא. באילת.",
slow blink. x64: towed backwards down the road, GPS "אילת" 350 → 0, munching. Grandma: "חמוד! הרכב שלך פה!" →
holds up "טסט ✓ עבר" "עשיתי לו טסט." (send beat). Cat: "עשית לו טסט?!" twitch, slow blink, "וואלה." + munch,
"כל. פעם. מחדש."; back in the car in Eilat a new notice slaps the windshield, the beacon starts again and the car tilts
= frame 0 (loop, ticket pill flickers). Serial pills "פרק 20" + 🎟 (live number from hud.stage_of, §O4). SFX only.

  python3 ep20.py test 0 0.3 1.0 1.6 2.2 3.0 3.8 4.6 5.4 6.2 7.0 7.8 8.7 9.4 9.9 10.5 11.0 11.9 -> out/ep20_contact.png
  python3 ep20.py render                                                                         -> out/ep20.mp4
"""
import math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep7 as E7
import ep10 as E10
import ep12 as E12
import ep13 as E13
import ep15 as E15
import ep16 as E16
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

DUR = 12.0
NF = int(round(DUR * FPS))
OUTDIR = m.OUTDIR
YELLOW = (255, 221, 51)
AMBER = (255, 170, 30)
BEAT = 60 / 80
QUEUE = int(os.environ.get('QUEUE', '482'))
EP_LABEL = 'פרק 20'
CARZ = float(os.environ.get('CARZ', '1.32')); CARY = float(os.environ.get('CARY', '1010'))
CROWDV = os.environ.get('CROWD', '1') == '1'
RIDECU = os.environ.get('RIDECU', '0') == '1'      # probe: the x64 ride as a big face close-up
CUCROWD = os.environ.get('CUCROWD', '0') == '1'    # probe: neighbours' faces behind the cat / grandma in the close-ups
FRONTC = os.environ.get('FRONTC', '0') == '1'      # probe: neighbours pressing their faces to the windshield (front row)        # experiment: neighbours' faces in the rear window

SHOTS = [('car', 0.0, 2.0), ('tow', 2.0, 3.6), ('cat', 3.6, 5.0), ('ride', 5.0, 6.8), ('gran', 6.8, 8.5),
         ('cat', 8.5, 10.3), ('car', 10.3, DUR + 1)]
CLANK = 0.1            # tow hook jolt
INSIDE = 0.85          # "רגע! אני בפנים!"
TOW_TALK = 2.15        # "בלי טסט? נגרר, מותק."
ADDR = 2.85            # snap zoom "לכתובת הרשומה."
FROZE = 3.6
BLINK1 = (4.35, 4.7)
FF = (5.0, 6.8)        # x64 ride
GRAN_HI = 6.85
TESTOK = 7.6           # "עשיתי לו טסט." + paper
JAW = 8.5
BLINK2 = (9.15, 9.5)
WALLA = (9.6, 10.1)
MUNCH = 9.85
SLAP2 = 10.75          # new notice slaps the windshield in Eilat
RETOW = 11.45          # beacon + tilt again -> frame 0

CAPTIONS = [  # (t0, t1, lines, size, y, fill)
    (0.0, 2.0, ['גרר לקח לך את הרכב?', 'ואתה עוד בפנים?'], 92, 290, WHITE),      # keyword on frame 1
    (2.0, 3.6, ['בלי טסט?', 'נגרר לכתובת הרשומה.'], 92, 290, WHITE),
    (FROZE, 5.0, ['הכתובת הרשומה?', 'של סבתא. באילת.'], 96, 290, WHITE),
    (FF[0], FF[1], ['350 ק״מ', 'בגרר.'], 96, 290, WHITE),
    (TESTOK, 8.5, ['סבתא עשתה לו טסט.', 'בלי תור.'], 92, 290, WHITE),
    (9.65, 10.3, ['כל. פעם. מחדש.'], 100, 270, WHITE),
    (RETOW - 0.25, DUR + 0.1, ['גרר לקח לך את הרכב?', 'ואתה עוד בפנים?'], 92, 290, WHITE),
]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def sway(t): return math.sin(2 * math.pi * t / (2 * BEAT))

def tilt(t):
    """roll of the car on the tow hook (deg). frame 0 = already lifting; the end lifts again into it."""
    if t >= RETOW: return 1.6 * ease_in(clamp((t - RETOW) / (DUR - RETOW)))
    if t >= 10.3: return 0.0
    if t < CLANK: return 1.6 + 2.0 * t
    u = t - CLANK
    base = 1.8 + 7.5 * ease_out(clamp(u / 0.9))
    return base + 3.0 * math.exp(-u * 6) * math.sin(u * 30)

def lift(t):
    """vertical rise of the car (world units, negative = up)"""
    if t >= RETOW: return -10 * ease_in(clamp((t - RETOW) / (DUR - RETOW)))
    if t >= 10.3: return 0.0
    if t < CLANK: return -10 - 20 * t
    u = t - CLANK
    return -12 - 60 * ease_out(clamp(u / 0.9)) - 14 * math.exp(-u * 7) * math.cos(u * 26)

def beacon_on(t):
    return (t < 2.0) or (t >= RETOW - 0.05) or (FF[0] <= t < FF[1])

# ------------------------------------------------------------------ props
NOTICE2 = None
def notice2_layer():
    NW, NH = E16.NW, E16.NH
    lay = Image.new('RGBA', (S(NW), S(NH)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(NW) - 1, S(NH) - 1], radius=S(10), fill=(252, 250, 244), outline=(150, 146, 136), width=iw(4))
    d.rectangle([0, 0, S(NW), S(64)], fill=(214, 44, 52))
    d.text((S(NW / 2), S(34)), 'הודעה', font=font(S(44), 900), fill=WHITE, anchor='mm')
    d.text((S(NW / 2), S(112)), 'רכב ללא טסט', font=font(S(48), 900), fill=INK, anchor='mm')
    d.text((S(NW / 2), S(172)), 'ייגרר', font=font(S(60), 900), fill=(214, 44, 52), anchor='mm')
    d.rounded_rectangle([S(60), S(216), S(NW - 60), S(272)], radius=S(12), outline=(28, 104, 226), width=iw(5))
    d.text((S(NW / 2), S(244)), 'לכתובת הרשומה', font=font(S(32), 900), fill=(28, 104, 226), anchor='mm')
    return lay

def test_paper():
    pw, ph = 330, 250
    lay = Image.new('RGBA', (S(pw), S(ph)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(pw) - 1, S(ph) - 1], radius=S(12), fill=(252, 250, 244), outline=(120, 120, 120), width=iw(4))
    d.rectangle([0, 0, S(pw), S(60)], fill=(40, 160, 80))
    d.text((S(pw / 2), S(32)), 'מכון הרישוי', font=font(S(36), 900), fill=WHITE, anchor='mm')
    d.text((S(pw / 2 + 20), S(126)), 'טסט', font=font(S(64), 900), fill=INK, anchor='mm')
    line(d, [(70, 120), (95, 150), (140, 92)], (40, 160, 80), 14)
    d.rounded_rectangle([S(80), S(178), S(pw - 80), S(230)], radius=S(12), outline=(40, 160, 80), width=iw(5))
    d.text((S(pw / 2), S(204)), 'עבר', font=font(S(36), 900), fill=(40, 160, 80), anchor='mm')
    return lay

def burst(img, c, u, col=(255, 236, 120), r0=150, n=10, dur=0.4):
    E16.burst(img, c, u, col, r0, n, dur)

def beacon(img, t, c, r=420, a=150):
    """amber rotating beacon light washing over the frame"""
    ph = (t * 2.6) % 1.0
    k = max(0.0, math.sin(2 * math.pi * ph)) ** 2
    if k < 0.02: return
    ov = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for s in range(6, 0, -1):
        rr = r * s / 6 / 4
        od.ellipse([c[0] / 4 - rr, c[1] / 4 - rr, c[0] / 4 + rr, c[1] / 4 + rr], fill=AMBER + (int(a * k * (1 - s / 7) * 0.6),))
    ov = ov.filter(ImageFilter.GaussianBlur(10)).resize(img.size, Image.BILINEAR)
    img.alpha_composite(ov)

# ------------------------------------------------------------------ tow driver (Sharit's rig recoloured: hi-vis vest, cap "ג")
TOW = dict(E15.TECH)
TOW.update(BLOUSE=(250, 150, 30), BLOUSE_D=(220, 120, 20), BLOUSE_O=(120, 60, 10), HAIR=(60, 34, 24), HAIR_D=(40, 22, 16))
TCAP = (40, 42, 52); TCAP_O = (10, 10, 14)

def tow_draw(st, i):
    saved = {k: getattr(SH, k) for k in TOW}
    for k, v in TOW.items(): setattr(SH, k, v)
    try: L = SH.draw(st, i)
    finally:
        for k, v in saved.items(): setattr(SH, k, v)
    d = ImageDraw.Draw(L)
    for y in (700, 760):   # reflective stripes on the vest
        d.rectangle([S(150), S(y), S(560), S(y + 20)], fill=(220, 226, 230))
    d.rounded_rectangle([S(372), S(600), S(492), S(656)], radius=S(8), fill=(250, 250, 248), outline=(60, 60, 70), width=iw(3))
    d.rectangle([S(372), S(600), S(492), S(613)], fill=AMBER)
    d.text((S(432), S(636)), 'גרר', font=font(S(30), 800), fill=INK, anchor='mm')
    cx, cy = SH.HC; a = math.radians(st['rot'])
    def R(x, y):
        dx, dy = x - cx, y - (cy + 150)
        return (cx + dx * math.cos(a) + dy * math.sin(a), cy + 150 - dx * math.sin(a) + dy * math.cos(a))
    dome = [R(cx + 150 * math.cos(math.radians(th)), cy - 112 - 120 * math.sin(math.radians(th))) for th in range(0, 181, 10)]
    poly(d, dome, fill=TCAP, outline=TCAP_O, width=6)
    brim = [R(cx - 150, cy - 112), R(cx + 150, cy - 112), R(cx + 230, cy - 92), R(cx + 150, cy - 80), R(cx - 150, cy - 86)]
    poly(d, brim, fill=TCAP, outline=TCAP_O, width=6)
    c = R(cx - 10, cy - 170)
    E(d, c[0], c[1], 40, 26, fill=AMBER, outline=TCAP_O, width=3)
    d.text((S(c[0]), S(c[1])), 'ג', font=font(S(30), 900), fill=TCAP_O, anchor='mm')
    return L

def tow_state(t, i):
    st = E15.tech_base(); rot = 0.0
    if t < TOW_TALK: st.update(mouth='lazy', lid=0.3, look=(12, 4))
    elif t < ADDR:
        u = t - TOW_TALK; st.update(mouth='talk', lid=0.25, look=(0, 0)); rot = -5 * math.exp(-u * 4) * math.cos(u * 10)
    else:
        u = t - ADDR; st.update(mouth='talk' if u < 0.55 else 'grin', lid=0.1, look=(0, -2), finger=True, hand_r=(560, 560))
        rot = 6 * math.exp(-u * 5) * math.sin(u * 18)
    return st, rot

def build_street_bg():
    img = Image.new('RGBA', (W * K, H * K)); d = ImageDraw.Draw(img)
    for y in range(0, H, 6):
        d.rectangle([0, S(y), W * K, S(y + 6)], fill=m.lerpc((130, 190, 236), (236, 220, 196), y / 1100))
    for (x0, x1, top, col) in ((-20, 300, 380, (214, 196, 170)), (300, 620, 260, (196, 186, 176)), (620, 1100, 420, (226, 206, 180))):
        d.rectangle([S(x0), S(top), S(x1), S(1300)], fill=col, outline=(150, 140, 130), width=iw(5))
        for wy in range(top + 60, 1240, 150):
            for wx in range(x0 + 50, x1 - 60, 110):
                d.rectangle([S(wx), S(wy), S(wx + 60), S(wy + 80)], fill=(120, 160, 200), outline=(90, 90, 96), width=iw(3))
    d.rectangle([0, S(1300), W * K, H * K], fill=(110, 110, 118))
    # the tow truck behind her: yellow cab + boom + beacon
    d.rounded_rectangle([S(620), S(900), S(1100), S(1500)], radius=S(40), fill=(250, 196, 40), outline=(120, 90, 10), width=iw(8))
    d.rectangle([S(680), S(960), S(1000), S(1150)], fill=(150, 196, 226), outline=(90, 90, 96), width=iw(5))
    line(d, [(640, 1100), (180, 700)], (60, 60, 70), 40)
    line(d, [(180, 700), (170, 1000)], (60, 60, 70), 10)
    d.rounded_rectangle([S(820), S(840), S(920), S(900)], radius=S(16), fill=AMBER, outline=(120, 70, 10), width=iw(4))
    return img.filter(ImageFilter.GaussianBlur(S(4)))

# ------------------------------------------------------------------ cat states
def cat_state_car(t, i):
    st = E7.chill_state(); sw = sway(t)
    st.update(cobweb=1.0, red=0.9, blush=0.3, look=(4, 8))
    rot, dy = 0.0, 0.0
    if t >= 10.3:                                          # Eilat: chill, then the new notice, then tilting again
        if t < SLAP2:
            st.update(lid=0.55, mouth='goofy', look=(6, 10)); return st, 3.0 * sw, 4 * abs(sw)
        u = t - SLAP2
        if t < RETOW:
            st.update(lid=0.0, pupil='big', brow='up', ear_dy=-22 * math.exp(-u * 4), mouth='w', look=(-18, 8), blush=0.0)
            return st, 6 * math.exp(-u * 5) * math.sin(u * 22), -26 * math.exp(-u * 8) * math.cos(u * 26)
        st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', ear_dy=-10, look=(-10, -8), sweat=1.0)   # = frame 0
        return st, 0.0, 0.0
    if t < CLANK:                                          # frame 0: lifting -> wide eyes, sweat
        st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', ear_dy=-10, look=(-10, -8), sweat=1.0); return st, 0.0, 0.0
    u = t - CLANK
    if u < 0.6:                                            # CLANK jolt
        st.update(lid=0.0, pupil='big', brow='up', ear_dy=-26 * math.exp(-u * 4), mouth='w', look=(-14, -10), blush=0.0, sweat=1.0)
        dy = -30 * math.exp(-u * 8) * math.cos(u * 26); rot = 6 * math.exp(-u * 5) * math.sin(u * 22)
    else:                                                  # "רגע! אני בפנים!" — waving, panicked
        st.update(lid=0.0, pupil='normal', brow='annoyed', mouth='w', ear_droop=0.2, sweat=1.0, look=(-18, -6),
                  twitch=(int(t * 12) % 2 == 0)); rot = 4 * math.sin(t * 9)
    return st, rot, dy

def cat_state_ride(t, i):
    st = E7.chill_state(); sw = sway(t)
    st.update(cobweb=1.0, red=1.0, blush=0.5, lid=0.6, mouth='munch' if (i // 3) % 2 == 0 else 'goofy', look=(6, 10))
    return st, 4 * sw, 5 * abs(sw)

def cat_state_close(t, i):
    st = E7.chill_state()
    st.update(cobweb=1.0, red=0.9, blush=0.3)
    rot, dy = 0.0, 0.0
    if t < 5.0:                                            # "הכתובת הרשומה? של סבתא. באילת." frozen + slow blink
        u = t - FROZE
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-20 * math.exp(-u * 4), look=(0, 0),
                  twitch=(0.15 < u < 0.6 and int(t * 12) % 2 == 0))
        rot = 5 * math.exp(-u * 4) * math.sin(u * 22)
        if BLINK1[0] <= t < BLINK1[1]: st['lid'] = 1.0
        elif t >= BLINK1[1]: st.update(lid=0.55, mouth='goofy', ear_droop=0.6, look=(6, 10), pupil='normal')
        return st, rot, dy
    u = t - JAW                                            # "עשית לו טסט?!" jaw drop -> blink -> וואלה + munch
    if t < BLINK2[0]:
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-24 * math.exp(-u * 3), look=(-14, -4), sweat=1.0,
                  twitch=(0.25 < u < 0.6 and int(t * 12) % 2 == 0)); rot = 4 * math.sin(u * 22) * math.exp(-u * 3)
        dy = -18 * math.exp(-u * 7) * math.cos(u * 20)
    elif t < BLINK2[1]: st.update(lid=1.0, mouth='flat')
    else:
        sw = sway(t); st.update(lid=0.55, mouth='goofy', ear_droop=0.5, look=(6, 10)); rot = 4.5 * sw; dy = 6 * abs(sw)
        if WALLA[0] <= t < WALLA[0] + 0.4:
            s_ = math.sin(math.pi * (t - WALLA[0]) / 0.4); st.update(ear_dy=-14 * s_, brow='up' if s_ > 0.3 else 'none', mouth='w'); dy -= 12 * s_
        if MUNCH + 0.05 <= t < MUNCH + 0.45: st['mouth'] = 'munch' if (i // 3) % 2 == 0 else 'w'
    return st, rot, dy

# ------------------------------------------------------------------ scenes
REST = (270, 1300)
def notice_pose(t):
    if t < 2.0: return REST, -8 + 3 * math.sin(t * 14) * math.exp(-max(0, t - CLANK) * 2), 1.0   # flaps on the jolt
    if t >= 10.3:
        u = clamp((t - (SLAP2 - 0.4)) / 0.4)
        if u <= 0: return None
        if u < 1:
            e = ease_in(u)
            return (lerp(-260, REST[0], e), lerp(700, REST[1], e)), lerp(40, -8, e), lerp(1.7, 1.0, e)
        v = t - SLAP2
        return REST, -8, 1.0 + 0.04 * math.exp(-v * 10) * math.cos(v * 30)
    return None

NEIGH = [('c1', 230, 650, 0.38, 0.4), ('h0', 450, 600, 0.30, 1.4), ('c3', 820, 640, 0.38, 2.3), ('h2', 960, 610, 0.30, 0.9)]

def scene_car(t, i, ride=False):
    if ride:
        sp = FF[0] * 1.2 + 9.0 * (t - FF[0])
    else:
        sp = 2.0 if t < 2.0 else 0.0                       # standing still (towed in place / parked in Eilat)
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255))
    E10.window_view(img, t, sp)
    if CROWDV and not ride:                               # neighbours staring in through the rear window
        mood = 1 if (t >= CLANK and t < 2.0) or t >= SLAP2 or t < CLANK else 2
        for name, x, y, sc, ph in NEIGH:
            E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4 + ph), sc, flip=x > 540)
    img.alpha_composite(CAR_MID)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_ride(t, i) if ride else cat_state_car(t, i)
    E(d, 540, 1262 + 0.5 * dy, 215, 215, fill=FUR, outline=OUT, width=6)
    E(d, 540, 1300 + 0.5 * dy, 98, 150, fill=CREAM)
    poly(d, [(700, 1080 + 0.5 * dy), (740, 1110 + 0.5 * dy), (420, 1500), (380, 1470)], fill=(40, 42, 50))
    wa = E10.wheel_ang(t) if ride or t >= 10.3 else 14 * math.sin(t * 11)     # yanking the wheel while lifted
    WC = E10.WHEEL_C; WR = E10.WHEEL_R
    paws = [xform([(dx, -150)], WC[0], WC[1], wa)[0] for dx in (-190, 190)]
    if ride:   # one paw to the snack bag
        paws[1] = (720 + 30 * math.sin(t * 6), 1180)
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
    if ride: SH.snack_bag(d, (paws[1][0] + 10, paws[1][1] - 70), -12, 0.9)
    m.draw_paw(d, paws[1], ang=wa)
    img.alpha_composite(CAR_FG)
    d = ImageDraw.Draw(img)
    if not ride: SH.snack_bag(d, (250, 1420), -10, 0.75)
    if ride and not RIDECU:
        E10.gps(img, 'אילת', E16_km(t), False)
    pose = notice_pose(t) if not ride else None
    if pose:
        (cx, cy), ang, sc = pose
        src = NOTICE2
        lay = src.rotate(ang, resample=Image.BICUBIC, expand=True)
        if abs(sc - 1) > 0.01: lay = lay.resize((int(lay.width * sc), int(lay.height * sc)), Image.BICUBIC)
        shd = Image.new('RGBA', lay.size, (0, 0, 0, 0)); shd.paste((0, 0, 0, 90), mask=lay.split()[3]); shd = shd.filter(ImageFilter.GaussianBlur(S(10)))
        m.paste_center(img, shd, S(cx + 14), S(cy + 18)); m.paste_center(img, lay, S(cx), S(cy))
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(2):
        ph = ((t * 0.3 + k * 0.5) % 1) * 1600 - 300
        poly(od, [(ph, 60), (ph + 90 - 40 * k, 60), (ph - 280 - 40 * k, 1440), (ph - 370, 1440)], fill=(255, 255, 255, 22 - 8 * k))
    img.alpha_composite(ov)
    if FRONTC and not ride:
        mood = 1 if (CLANK <= t < 2.0) or t >= SLAP2 or t < CLANK else 2
        for name, x, y, sc, ph, fl in (('c4', 215, 860, 0.72, 0.9, False), ('h1', 890, 880, 0.6, 2.2, True)):
            E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=fl)
    if t >= 10.3: burst(img, REST, t - SLAP2, (255, 255, 255), 190, 10, 0.3)
    if beacon_on(t): beacon(img, t, (860, 200), 700, 170)
    if INSIDE <= t < 2.0:
        SH.bubble(img, 'רגע! אני בפנים!', t - INSIDE, (720, 1130, 560, 120), (600, 1000), side=-1)
    # the car on the hook: roll + lift (world -> rotate the whole picture, keeps the cat big)
    a = tilt(t) if not ride else 6.5 + 1.2 * math.sin(t * 7)
    ly = lift(t) if not ride else -60
    if abs(a) > 0.01 or abs(ly) > 0.5:
        img = img.rotate(a, resample=Image.BICUBIC, center=(S(540), S(1300)), translate=(0, S(ly)), fillcolor=(40, 40, 48, 255))
    return img

def E16_km(t):
    u = clamp((t - FF[0] - 0.15) / (FF[1] - FF[0] - 0.4))
    return int(round(350 * (1 - ease_io(u))))

HX, HY, F = 690, 900, 1.8
def scene_cat(t, i):
    img = CAT_BG.copy()
    if CUCROWD:
        mood = 1 if (FROZE <= t < FROZE + 0.8) or (JAW <= t < BLINK2[0]) else 2
        for name, x, y, sc, ph in (('c1', 150, 720, 0.55, 0.4), ('h0', 340, 600, 0.42, 1.4), ('c3', 120, 1180, 0.7, 2.3)):
            E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4 + ph), sc)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_close(t, i)
    E(d, HX, 1640, 450, 470, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1700, 210, 320, fill=CREAM)
    rp = (950, 1500 + 8 * math.sin(t * 2.0))
    if t >= BLINK2[1] and t < 10.3:
        if MUNCH - 0.15 <= t < MUNCH + 0.6: rp = lerp2(rp, (HX + 60, 1180), math.sin(math.pi * (t - (MUNCH - 0.15)) / 0.75))
    capsule(d, (HX + 250, 1420), rp, 120, FUR, OUT, 4)
    if t >= 8.5: SH.snack_bag(d, (rp[0] - 20, rp[1] - 110), -12, 1.25)
    E12.big_paw(d, rp, -10)
    E12.paste_head(img, st, i, HX, HY + dy, F, rot)
    if JAW + 0.05 <= t < BLINK2[0]:
        SH.bubble(img, 'עשית לו טסט?!', t - JAW - 0.05, (560, 560, 560, 130), (700, 720), side=1)
    if WALLA[0] <= t < WALLA[1]:
        SH.bubble(img, 'וואלה.', t - WALLA[0], (560, 560, 300, 120), (680, 720), side=1)
    if t >= BLINK2[1]:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(3):
            ts = k * 0.7; age = ((t - ts) % 2.1) / 2.1
            m.draw_note(od, 300 + 40 * age + 20 * math.sin(age * 8 + k), 900 - 200 * age, int(170 * math.sin(math.pi * age)), k % 2 == 1)
        img.alpha_composite(ov)
    return img

TC_HEAD = (540, 880); TCS = 1.75
def scene_tow(t, i):
    img = TOW_BG.copy()
    beacon(img, t, (870, 870), 600, 150)
    st, rot = tow_state(t, i)
    L = tow_draw(dict(st, rot=rot), i)
    L = L.resize((int(L.width * TCS), int(L.height * TCS)), Image.BICUBIC)
    dx = lerp(-200, 0, ease_out(clamp((t - 2.0) / 0.2)))
    img.alpha_composite(L, dest=(int(S(TC_HEAD[0] - 350 * TCS + dx)), int(S(TC_HEAD[1] - 300 * TCS))))
    if TOW_TALK <= t < ADDR:
        SH.bubble(img, 'בלי טסט? נגרר, מותק.', t - TOW_TALK, (540, 560, 780, 130), (560, 720), side=-1)
    elif t >= ADDR:
        SH.bubble(img, 'לכתובת הרשומה.', t - ADDR, (540, 560, 600, 130), (560, 720), side=-1)
    return img

GF = 2.0
G_ORIGIN = (560 - 350 * GF, 830 - 300 * GF)
def scene_gran(t, i):
    img = GRAN_BG.copy()
    if CUCROWD:
        mood = 1 if t >= TESTOK else 0
        for name, x, y, sc, ph, fl in (('h2', 110, 820, 0.5, 0.3, False), ('c4', 985, 860, 0.55, 1.7, True)):
            E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4 + ph), sc, flip=fl)
    st = E10.gran_base()
    u = t - GRAN_HI
    st.update(hand_r=(520, 470), hand_l=(170, 760) if t < TESTOK else (190, 640), lid=0.1 if t < TESTOK else 0.3, mouth='grin' if u < 0.3 or t >= TESTOK + 0.6 else 'talk',
              look=(8, 0), blush=0.9, rot=(-6 * math.exp(-u * 4) * math.cos(u * 10)) if t < TESTOK else 4 * math.sin((t - TESTOK) * 5) * math.exp(-(t - TESTOK) * 2))
    L = E10.gran_draw(st, i)
    L = L.resize((int(L.width * GF), int(L.height * GF)), Image.BICUBIC)
    dx = lerp(-240, 0, ease_out(clamp(u / 0.2)))
    img.alpha_composite(L, dest=(int(S(G_ORIGIN[0] + dx)), int(S(G_ORIGIN[1]))))
    hand = (G_ORIGIN[0] + dx + 520 * GF, G_ORIGIN[1] + 470 * GF)
    d = ImageDraw.Draw(img)
    E(d, hand[0], hand[1] - 20, 64, 52, fill=SH.SKIN, outline=SH.SKIN_O, width=5)
    # the cat's car keys dangling from her raised hand (she drove it to the test)
    kx, ky = hand[0] - 10, hand[1] + 20
    sw_ = 14 * math.sin(t * 5)
    line(d, [(kx, ky), (kx + sw_, ky + 90)], (180, 180, 190), 5)
    d.ellipse([S(kx + sw_ - 26), S(ky + 80), S(kx + sw_ + 26), S(ky + 132)], outline=(200, 200, 210), width=iw(6))
    poly(d, epoly(kx + sw_, ky + 170, 22, 46, 8), fill=(40, 40, 48), outline=(10, 10, 14), width=3)
    if t >= TESTOK:                                        # the passed-test slip in her other hand, left of her face
        v = t - TESTOK
        hl = (G_ORIGIN[0] + dx + 150 * GF, G_ORIGIN[1] + 470 * GF)
        sc = 1.4 - 0.4 * ease_out(clamp(v / 0.15))
        lay = TEST.rotate(8 + 2 * math.sin(t * 3), resample=Image.BICUBIC, expand=True)
        lay = lay.resize((int(lay.width * sc), int(lay.height * sc)), Image.BICUBIC)
        c = (hl[0] + 130, hl[1] - 90)
        m.paste_center(img, lay, S(c[0]), S(c[1]))
        burst(img, c, v, (120, 230, 140), 170, 10, 0.4)
        d = ImageDraw.Draw(img)
        E(d, hl[0] + 130, hl[1] + 40, 60, 48, fill=SH.SKIN, outline=SH.SKIN_O, width=5)
    if t < TESTOK:
        SH.bubble(img, 'חמוד! הרכב שלך פה!', u, (520, 500, 720, 130), (480, 650), side=-1)
    else:
        SH.bubble(img, 'עשיתי לו טסט.', t - TESTOK, (520, 500, 560, 130), (480, 650), side=-1)
    return img

# ------------------------------------------------------------------ frame
CAT_BG = TOW_BG = GRAN_BG = NOTICE = NOTICE2 = TEST = CAR_MID = CAR_FG = PILL_EP = PILL_Q = None
def init_all():
    global CAT_BG, TOW_BG, GRAN_BG, NOTICE, NOTICE2, TEST, CAR_MID, CAR_FG, PILL_EP, PILL_Q
    m.init_static()
    CAR_MID = E10.build_car_mid(); CAR_FG = E10.build_car_fg()
    ci = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); E10.window_view(ci, 0, 0); ci.alpha_composite(CAR_MID)
    CAT_BG = ci.filter(ImageFilter.GaussianBlur(S(5)))       # inside the car, blurred
    TOW_BG = build_street_bg()
    GRAN_BG = E12.build_gran_bg()
    NOTICE = E16.notice_layer(); NOTICE2 = notice2_layer(); TEST = test_paper()
    if CROWDV or FRONTC or CUCROWD: E13.build_crowd()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 560.0, 980.0
    if name == 'car':
        rng = random.Random(int(t * FPS)); sh_ = 3.0
        if CLANK <= t < CLANK + 0.45: sh_ = 3 + 24 * math.exp(-(t - CLANK) * 8)
        if SLAP2 <= t < SLAP2 + 0.4: sh_ = 3 + 20 * math.exp(-(t - SLAP2) * 8)
        z, cx, cy = CARZ, 540.0, CARY
        if t < 2.0 and t >= CLANK: z = lerp(CARZ + 0.16, CARZ, ease_out(clamp((t - CLANK) / 0.25)))
        elif t < CLANK: z = CARZ + 0.16
        if t >= RETOW: z = lerp(CARZ, CARZ + 0.16, ease_in(clamp((t - RETOW) / (DUR - RETOW))))
        if t >= 10.3 and t < 10.6: z = lerp(CARZ + 0.15, CARZ, ease_out((t - 10.3) / 0.3))
        cx += rng.uniform(-sh_, sh_); cy += rng.uniform(-sh_, sh_)
    elif name == 'ride':
        rng = random.Random(int(t * FPS)); z, cx, cy = (1.75, 540.0, 960.0) if RIDECU else (1.05, 540.0, 980.0)
        cx += rng.uniform(-4, 4); cy += rng.uniform(-4, 4)
    elif name == 'tow':
        z = lerp(1.18, 1.0, ease_out(clamp((t - a) / 0.3))); cx, cy = 560.0, 960.0
        if t >= ADDR: e = ease_out(clamp((t - ADDR) / 0.12)); z, cy = lerp(1.0, 1.16, e), 880
    elif name == 'cat':
        z = lerp(1.2, 1.0, ease_out(clamp((t - a) / 0.3))); cx, cy = 600.0, 980.0
        if a == FROZE: e = ease_out(clamp((t - FROZE) / 0.12)); z, cx, cy = lerp(1.22, 1.08, e), 690, 930
    elif name == 'gran':
        z = lerp(1.15, 1.0, ease_out(clamp((t - a) / 0.3)))
        if t >= TESTOK: e = ease_out(clamp((t - TESTOK) / 0.12)); z, cx, cy = lerp(1.0, 1.1, e), 540, 900
    return z, cx, cy

def ff_overlay(frame, t):
    frame.alpha_composite(m.SCAN)
    fd = ImageDraw.Draw(frame)
    if int(t * 4) % 2 == 0 or t < FF[0] + 0.3:
        for x0 in (808, 852):
            fd.polygon([(x0, 470), (x0 + 44, 500), (x0, 530)], fill=WHITE, outline=(10, 10, 12), width=4)
        fd.text((955, 500), 'x64', font=font(46, 900), fill=WHITE, anchor='mm', stroke_width=6, stroke_fill=(10, 10, 12))

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'car': img = scene_car(t, i)
    elif name == 'ride': img = scene_car(t, i, ride=True)
    else: img = {'tow': scene_tow, 'cat': scene_cat, 'gran': scene_gran}[name](t, i)
    z, ccx, ccy = camera(t)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if name == 'ride': ff_overlay(frame, t)
    frame.alpha_composite(m.VIG)
    for s_ in (CLANK, ADDR, FROZE, TESTOK, JAW, SLAP2):
        if s_ <= t < s_ + 0.06:
            frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    for t0, t1, lines, size, yc, fill in CAPTIONS:
        if t0 <= t < t1:
            u = t - t0; sc = 1 + 0.25 * math.exp(-u * 12) * math.cos(u * 20)
            if t0 in (0.0, RETOW - 0.25): sc = 1.0
            cap = m.caption_layer(lines, size, fill)
            if abs(sc - 1) > 0.004:
                cap = cap.resize((max(1, int(cap.width * sc)), max(1, int(cap.height * sc))), Image.BICUBIC)
            m.paste_center(frame, cap, W / 2, yc)
    if name == 'car':
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (SFX only, no groove)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR); out = np.zeros(n); add = m.add
    rng = np.random.default_rng(220)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    def thump(t0, g=0.8):
        tt = tt_(0.4); f = 150 * np.exp(-tt * 9) + 45
        add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9), t0, g)
    def pop(t0, g=0.22):
        tt = tt_(0.12); f = 300 + 900 * np.exp(-tt * 40)
        add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30), t0, g)
    def whoosh(t0, wl=0.3, g=0.25):
        wt = tt_(wl); add(out, m.bandpass(nz(wl), 700, 6000) * np.sin(np.pi * wt / wl) ** 2 * (wt / wl), t0, g)
    def dundun(t0, g=0.3):
        for k_, f_ in enumerate((146.8, 138.6)):
            add(out, m.tone(f_, 0.5 if k_ else 0.3, harm=((1, 1), (2, 0.5), (3, 0.3)), decay=2.5), t0 + 0.22 * k_, g)
    def clank(t0, g=0.5):
        for f_, d_ in ((523, 0.5), (787, 0.4), (1290, 0.3)):
            add(out, m.tone(f_, d_, harm=((1, 1), (2.7, 0.4), (5.1, 0.2)), decay=7), t0, g * 0.35)
        add(out, m.bandpass(nz(0.08), 1500, 7000) * np.exp(-tt_(0.08) * 50), t0, g)
        thump(t0, g * 0.9)
    def chain(t0, t1, g=0.08):
        tc = t0; k = 0
        while tc < t1:
            add(out, m.bandpass(nz(0.03), 2500, 9000) * np.exp(-tt_(0.03) * 120), tc, g * (0.6 + 0.4 * (k % 3 == 0))); tc += 0.055; k += 1
    def winch(t0, t1, g=0.07):
        d_ = t1 - t0; tt = tt_(d_)
        f = 70 + 25 * np.sin(2 * np.pi * 0.7 * tt)
        add(out, np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.minimum(1, np.minimum(tt / 0.05, (d_ - tt) / 0.05)), t0, g * 0.5)
        add(out, m.lowpass(nz(d_), 500), t0, g)
    def beep(t0, t1, g=0.05):
        tc = t0
        while tc < t1:
            add(out, m.tone(1180, 0.18, harm=((1, 1),), decay=1), tc, g); tc += 0.5
    # tow: winch + chain + reverse beeper; CLANK at 0.1
    winch(0.0, 2.0, 0.08); chain(0.0, 2.0, 0.06); beep(0.02, 2.0, 0.05)
    clank(CLANK, 0.6); pop(INSIDE, 0.22)
    for tc in (2.0, 3.6, 5.0, 6.8, 8.5, 10.3): whoosh(tc - 0.08, 0.16, 0.08)
    pop(TOW_TALK, 0.24)
    pop(ADDR, 0.26); thump(ADDR, 0.5); dundun(ADDR + 0.12, 0.32)
    pop(FROZE, 0.26); thump(FROZE, 0.45)
    for k_, f_ in enumerate((392.0, 311.1)):
        add(out, m.tone(f_, 0.45, harm=((1, 1), (2, 0.4)), decay=3), BLINK1[0] + 0.2 * k_, 0.14)
    # x64 ride: tape riser + road
    tt = tt_(FF[1] - FF[0]); f = 300 + 900 * tt / (FF[1] - FF[0])
    add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 * np.minimum(1, (FF[1] - FF[0] - tt) / 0.1), FF[0], 0.05)
    add(out, m.lowpass(nz(FF[1] - FF[0]), 300), FF[0], 0.05); chain(FF[0], FF[1], 0.04); beep(FF[0], FF[1], 0.035)
    tc = FF[0] + 0.2
    while tc < FF[1] - 0.2:
        add(out, m.bandpass(nz(0.06), 1500, 7000) * np.exp(-tt_(0.06) * 45), tc, 0.09); tc += 0.26
    pop(GRAN_HI, 0.22)
    for k_, f_ in enumerate((523.3, 659.3, 784.0, 1046.5)):   # "עשיתי לו טסט." success arpeggio
        add(out, m.tone(f_, 0.3, harm=((1, 1), (2, 0.3)), decay=4), TESTOK + 0.07 * k_, 0.12)
    pop(TESTOK, 0.24)
    pop(JAW, 0.26); thump(JAW, 0.45)
    for k_, f_ in enumerate((392.0, 311.1)):
        add(out, m.tone(f_, 0.45, harm=((1, 1), (2, 0.4)), decay=3), BLINK2[0] + 0.2 * k_, 0.14)
    pop(WALLA[0])
    tc = MUNCH + 0.05
    while tc < MUNCH + 0.45:
        add(out, m.bandpass(nz(0.07), 1500, 7000) * np.exp(-tt_(0.07) * 45), tc, 0.15); tc += 0.13
    for k_, f_ in enumerate((392.0, 349.2, 329.6)):
        add(out, m.tone(f_, 0.5, harm=((1, 1), (2, 0.3)), decay=3), 9.7 + k_ * 0.18, 0.12)
    whoosh(SLAP2 - 0.12, 0.12, 0.35); thump(SLAP2, 0.7); add(out, m.highpass(nz(0.05), 1500) * np.exp(-tt_(0.05) * 90), SLAP2, 0.5)
    winch(RETOW, DUR, 0.08); chain(RETOW, DUR, 0.06); beep(RETOW + 0.02, DUR, 0.05)
    out += m.lowpass(nz(DUR), 300) * 0.01
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
    mp4 = os.path.join(OUTDIR, f'ep20{tag}.mp4')
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
