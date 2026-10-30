#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 21 v2: הבנק שלי: החשבון הוקפא — rebuilt 30.10 under §P (Gabi, 28.10: "לבנות מחדש"); ~12.9 s.
v1 (28.10, the old fee formula) is kept in ep21_v1.py; this file reuses its kiosk, terminal, card and window sets.
Beat sheet (§P):
  WANT (frame 0, in motion): buy his snacks. His "הבנק שלי" card is already coming down on the kiosk terminal → "נדחה";
  again → "נדחה"; the red chip "פעילות חריגה: 47 שקיות חטיפים". Hook "הבנק שלי הקפיא / לך את החשבון?".
  PLANT: his snack habit — the three snack bags on the kiosk counter (frame 0), the bag he munches from at the bank
  (5.0–6.3) and the three bags again at the peak. Never pointed at.
  CLIMB (Sharit helps!): "בוא נשחרר אותך, מותק." → he slaps his ID on the counter ✓ (זהות) → signs the form ✓ (טופס) →
  STAMP "שוחרר" ✓ (חותמת, gold), Sharit applauds "חופשי, מותק!", the queue cheers + confetti.
  PEAK: back at the kiosk, "סוף סוף: / החשבון חופשי.", card over the terminal, silence + heartbeat.
  BREAK (his_own_hand, last ~1.1 s): "אושר" ✓ beep → the terminal flips red, chip "פעילות חריגה: 50 שקיות חטיפים" —
  his own three bags froze it again. 0.45 s frozen face, hard cut to frame 0 (the card coming down → "נדחה" = loop).
  No וואלה tail, no on-screen CTA, no fee.

  python3 ep21.py test 0 0.15 0.9 1.4 2.2 3.0 4.3 5.4 6.7 7.4 8.6 9.6 10.9 11.6 11.95 12.5 -> out/ep21_contact.png
  python3 ep21.py render                                                              -> out/ep21_frozen_v2.mp4
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
import ep21_v1 as V1
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

DUR = float(os.environ.get('DUR', '12.9'))
NF = int(round(DUR * FPS))
OUTDIR = m.OUTDIR
YELLOW = (255, 221, 51); GREEN = (36, 168, 84); GOLD = (230, 170, 30)
BLUE = (28, 104, 226); RED = (214, 44, 52)
BEAT = 60 / 80
QUEUE = int(os.environ.get('QUEUE', '476'))
EP_LABEL = 'פרק 21'
TAG_OUT = os.environ.get('OUTNAME', 'ep21_frozen_v2')

SHOTS = [('kiosk', 0.0, 1.9), ('two', 1.9, 5.0), ('cat', 5.0, 6.3), ('two', 6.3, 8.4), ('kiosk', 8.4, DUR + 1)]
DECL1, DECL2 = 0.1, 0.8
FLAG = 1.15            # "פעילות חריגה: 47 שקיות חטיפים"
SH_HELP = (2.05, 2.85) # "בוא נשחרר אותך, מותק."
IDSLAP = 2.95; CHK1 = 3.0
SH_OK = (3.1, 3.85)    # "תעודה? מושלם."
FORM_IN = 3.9; SIGN = (4.1, 4.6); CHK2 = 4.55
MUNCHB = (5.0, 6.3)    # close-up at the window: munching from his bag, "רק עוד חותמת!"
BUB_ONE = (5.2, 6.2)
STAMP = 6.6; CHK3 = 6.65
BRAVO = (6.8, 7.7)     # "חופשי, מותק!"
CHEER = (6.7, 8.4)
BACK = 8.4             # he runs back into the kiosk
PEAK = (10.7, 11.25)   # card over the terminal, silence, heartbeat
TAPC = 11.35           # card down -> "אושר"
BREAK = 11.8           # the terminal flips red: 50 bags
FREEZE = (11.9, DUR)

CAPTIONS = [  # (t0, t1, lines, size, y, fill)
    (0.0, 1.9, ['הבנק שלי הקפיא', 'לך את החשבון?'], 100, 290, WHITE),          # keyword on frame 1
    (9.0, 10.65, ['סוף סוף:', 'החשבון חופשי.'], 100, 290, WHITE),
]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

sway = E18.sway; burst = E18.burst; imprint = E18.imprint; stamp_tool = E18.stamp_tool; paste_sh = E18.paste_sh
confetti = E18.confetti; shadow_paste = V1.shadow_paste

# ------------------------------------------------------------------ props
def id_layer():
    lay = Image.new('RGBA', (S(260), S(170)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(259), S(169)], radius=S(14), fill=(236, 242, 250), outline=(60, 80, 120), width=iw(4))
    d.rectangle([S(4), S(4), S(255), S(40)], fill=(70, 110, 180))
    d.text((S(130), S(23)), 'תעודת זהות', font=font(S(26), 900), fill=WHITE, anchor='mm')
    E(d, 66, 102, 40, 40, fill=FUR, outline=OUT, width=3)
    for side in (-1, 1): poly(d, [(66 + side * 34, 86), (66 + side * 28, 52), (66 + side * 8, 72)], fill=FUR, outline=OUT, width=3)
    for k in range(3): d.rounded_rectangle([S(124), S(70 + k * 26), S(236), S(82 + k * 26)], radius=S(5), fill=(170, 180, 200))
    return lay

def form_layer(signed):
    lay = Image.new('RGBA', (S(300), S(380)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(299), S(379)], fill=(252, 252, 246), outline=(150, 150, 140), width=iw(3))
    d.text((S(150), S(42)), 'בקשת שחרור', font=font(S(34), 900), fill=INK, anchor='mm')
    for k in range(5): d.rectangle([S(30), S(90 + k * 36), S(270), S(96 + k * 36)], fill=(200, 202, 210))
    d.text((S(270), S(300)), 'חתימה:', font=font(S(24), 800), fill=(90, 96, 110), anchor='rm')
    d.line([S(30), S(330), S(190), S(330)], fill=(120, 124, 136), width=iw(3))
    return lay

def signature(d, c, u):
    """scribble drawn progressively (u 0..1), world units around c"""
    pts = []
    for k in range(int(60 * clamp(u)) + 1):
        a = k / 60
        pts.append((c[0] - 70 + 140 * a, c[1] - 14 * math.sin(a * 18) * (1 - 0.4 * a)))
    if len(pts) > 1: line(d, pts, (24, 30, 96), 5)

def terminal_green():
    lay = V1.terminal_layer(0); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(24), S(26), S(V1.TMW - 24), S(150)], radius=S(14), fill=(60, 190, 100), outline=(16, 16, 20), width=iw(4))
    d.text((S(V1.TMW / 2), S(88)), 'אושר', font=font(S(64), 900), fill=WHITE, anchor='mm')
    return lay

def red_chip(n):
    lay = Image.new('RGBA', (S(440), S(170)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(440) - 1, S(170) - 1], radius=S(22), fill=RED, outline=(90, 10, 14), width=iw(5))
    d.text((S(220), S(52)), 'פעילות חריגה:', font=font(S(46), 900), fill=WHITE, anchor='mm')
    d.text((S(220), S(118)), f'{n} שקיות חטיפים', font=font(S(48), 900), fill=(255, 236, 120), anchor='mm')
    return lay.rotate(-6, resample=Image.BICUBIC, expand=True)

def chip_at(img, lay, c, u, big=1.5):
    if u < 0: return
    sc = big - (big - 1) * ease_out(clamp(u / 0.12))
    l2 = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    shadow_paste(img, l2, c, 110, (10, 14), 8)

# ------------------------------------------------------------------ meter (screen space)
METER_Y = 470
METER = [('זהות', CHK1), ('טופס', CHK2), ('חותמת', CHK3)]
def meter(frame, t):
    d = ImageDraw.Draw(frame)
    reset = t >= BREAK
    full = (t >= CHK3) and not reset
    xs = [850, 540, 230]
    for k, (lab, tc) in enumerate(METER):
        done = (t >= tc) and not reset
        u = t - tc
        sc = 1.0 + (0.35 * math.exp(-u * 10) * math.cos(u * 20) if (0 <= u < 0.5 and not reset) else 0.0)
        if reset and t - BREAK < 0.3: sc = 1.0 + 0.2 * math.exp(-(t - BREAK) * 12)
        w_, h_ = 290 * sc, 76 * sc
        cx = xs[k] + (random.Random(int(t * FPS) + k).uniform(-10, 10) if (reset and t - BREAK < 0.3) else 0)
        fill = (GREEN if not full else GOLD) if done else (250, 250, 250)
        d.rounded_rectangle([cx - w_ / 2 + 5, METER_Y - h_ / 2 + 8, cx + w_ / 2 + 5, METER_Y + h_ / 2 + 8], radius=int(h_ / 2), fill=(0, 0, 0, 90))
        d.rounded_rectangle([cx - w_ / 2, METER_Y - h_ / 2, cx + w_ / 2, METER_Y + h_ / 2], radius=int(h_ / 2), fill=fill, outline=INK, width=4)
        ccx = cx + w_ / 2 - 40 * sc
        d.ellipse([ccx - 24 * sc, METER_Y - 24 * sc, ccx + 24 * sc, METER_Y + 24 * sc], fill=WHITE if done else (220, 222, 228), outline=INK, width=3)
        if done:
            d.line([(ccx - 12 * sc, METER_Y), (ccx - 3 * sc, METER_Y + 10 * sc), (ccx + 13 * sc, METER_Y - 11 * sc)], fill=GREEN, width=int(7 * sc), joint='curve')
        d.text((cx - 26 * sc, METER_Y + 2), lab, font=font(int(36 * sc), 900), fill=WHITE if done else (120, 124, 136), anchor='mm')

# ------------------------------------------------------------------ cat states
def base_cat():
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.3); return st

def cat_state_kiosk(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < 1.9:
        if t < DECL1: st.update(lid=0.1, pupil='normal', mouth='smile', look=(-16, 12), blush=0.0)
        elif t < DECL2:
            u = t - DECL1
            st.update(lid=0.0, pupil='big', brow='up', ear_dy=-24 * math.exp(-u * 4), mouth='w', look=(-18, 12), blush=0.0)
            dy = -26 * math.exp(-u * 8) * math.cos(u * 26); rot = 5 * math.exp(-u * 5) * math.sin(u * 22)
            if u > 0.45: st.update(lid=0.1, pupil='normal', brow='annoyed', mouth='flat', look=(-14, 12))
        else:
            u = t - DECL2
            st.update(lid=0.0, pupil='tiny', brow='sad', mouth='w', ear_droop=0.6 * clamp(u / 0.3), sweat=1.0, look=(-16, 10),
                      ear_dy=-20 * math.exp(-u * 5))
            rot = 5 * math.exp(-u * 4) * math.sin(u * 22)
            if t >= FLAG: st.update(brow='annoyed', pupil='big', mouth='flat', ear_droop=0.2, sweat=0.0)     # determined
        return st, rot, dy
    v = t - BACK                                           # back at the kiosk
    if t < 9.6:
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-12, 10), blush=0.9, ear_dy=-20 * math.exp(-v * 3))
        dy = -14 * abs(math.sin(v * 9)) * math.exp(-v * 2)
    elif t < PEAK[0]:
        st.update(lid=0.2, pupil='big', mouth='smile', look=(-18, 14), blush=0.6)
    elif t < TAPC:
        st.update(lid=0.0, pupil='big', brow='up', mouth='flat', look=(-20, 14), blush=0.4, ear_dy=-10); rot = 0.6 * math.sin(t * 30)
    elif t < BREAK:
        u = t - TAPC
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-28 * math.exp(-u * 4), look=(-10, 6), blush=1.0); dy = -20 * math.exp(-u * 6)
    else:
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', look=(0, 0), blush=0.0, ear_droop=0.6 * clamp(u / 0.2),
                  ear_dy=-20 * math.exp(-u * 6), twitch=(0.2 < u < 0.55 and int(t * 12) % 2 == 0))
    return st, rot, dy

def card_pos(t):
    if t < 1.9: return V1.card_pos(t)
    if t < PEAK[0]:
        u = clamp((t - 9.6) / 1.1)
        return lerp2((560, 1250), (330, 1150), ease_io(u)), lerp(20, 8, u)
    if t < TAPC - 0.12: return (330, 1150 + 4 * math.sin(t * 30)), 8
    if t < TAPC: return lerp2((330, 1150), (300, 1215), ease_in(clamp((t - (TAPC - 0.12)) / 0.12))), 6
    return (300, 1215), 6

def scene_kiosk(t, i):
    img = KIOSK_BG.copy()
    cheer_k = BACK <= t < 9.6
    mood = 1 if (DECL2 <= t < 1.9 or t >= BREAK or cheer_k) else 0
    for name, x, y, sc, ph in V1.QUEUE_KIOSK:
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_kiosk(t, i)
    kx = V1.KX
    if BACK <= t < BACK + 0.3: kx += lerp(300, 0, ease_out((t - BACK) / 0.3))          # runs back in
    E(d, kx, 1640, 430, 450, fill=FUR, outline=OUT, width=7)
    E(d, kx, 1700, 200, 300, fill=CREAM)
    if BACK <= t < BACK + 0.35:
        for k in range(5):
            y = 700 + k * 160; x1 = kx + 380
            line(d, [(x1, y), (x1 + 240 * (1 - clamp((t - BACK) / 0.35)), y)], (255, 255, 255), 10)
    V1.build_counter(img); d = ImageDraw.Draw(img)
    for k, (x, ang) in enumerate(((640, -8), (790, 6), (930, -4))):          # the plant: his three bags
        SH.snack_bag(d, (x, 1560 + 4 * math.sin(t * 3 + k)), ang, 0.8)
    if t < 1.9:
        declined = t >= DECL1 and not (DECL2 - 0.3 <= t < DECL2)
        lay = TERM_RED if declined else TERM_OK
    else:
        lay = TERM_RED if t >= BREAK else (TERM_GREEN if t >= TAPC else TERM_OK)
    shadow_paste(img, lay.rotate(4, resample=Image.BICUBIC, expand=True), V1.TERM_C)
    d = ImageDraw.Draw(img)
    c, ang = card_pos(t)
    paw = (c[0] + 120, c[1] + 40)
    capsule(d, (kx - 180, 1440 + dy * 0.4), paw, 110, FUR, OUT, 4)
    shadow_paste(img, CARD.rotate(ang, resample=Image.BICUBIC, expand=True), c, 90, (10, 14), 8)
    d = ImageDraw.Draw(img); E12.big_paw(d, paw, -20, 0.9)
    E12.paste_head(img, st, i, kx, V1.KY + dy, V1.KF, rot)
    tc = V1.TERM_C
    if t < 1.9:
        for td in (DECL1, DECL2): burst(img, (tc[0], tc[1] - 110), t - td, (255, 120, 120), 150, 10, 0.35)
        if t >= DECL1 and not (DECL2 - 0.3 <= t < DECL2) and t < FLAG:
            u = t - (DECL2 if t >= DECL2 else DECL1)
            chip_at(img, DECL_CHIP, (tc[0] + 10, tc[1] - 290 + 6 * math.sin(t * 14)), u, 1.6 if t >= DECL2 else 1.4)
        if t >= FLAG: chip_at(img, CHIP47, (tc[0] + 40, tc[1] - 300 + 4 * math.sin(t * 12)), t - FLAG)
        burst(img, (tc[0] + 40, tc[1] - 300), t - FLAG, (255, 120, 120), 150, 8, 0.35)
    else:
        if cheer_k: confetti(img, t - BACK + 0.6, 1.2)
        burst(img, (tc[0], tc[1] - 110), t - TAPC, (120, 255, 160), 170, 12, 0.35)
        burst(img, (tc[0], tc[1] - 110), t - BREAK, (255, 120, 120), 200, 12, 0.4)
        if t >= BREAK: chip_at(img, CHIP50, (tc[0] + 60, tc[1] - 330 + 4 * math.sin(t * 14)), t - BREAK, 1.7)
    return img

def cat_state_two(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < IDSLAP:                                         # hopeful, Sharit is helping
        st.update(lid=0.1, pupil='big', brow='up', mouth='smile', look=(-18, 4), blush=0.6)
    elif t < FORM_IN:
        u = t - IDSLAP
        st.update(lid=0.0, pupil='big', brow='annoyed', mouth='w' if u < 0.3 else 'smile', look=(-16, 8), ear_dy=-18 * math.exp(-u * 3))
        dy = 16 * math.exp(-u * 8) * math.cos(u * 20)
    elif t < 5.0:                                          # signing: focused
        st.update(lid=0.35, pupil='normal', brow='annoyed', mouth='flat', look=(-14, 18))
        if t >= CHK2: st.update(mouth='smile', lid=0.1, pupil='big')
    else:                                                  # stamp, joy
        u = t - STAMP
        if u < 0: st.update(lid=0.0, pupil='big', brow='up', mouth='flat', look=(-14, 14))
        else:
            st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24 * math.exp(-u * 3), look=(-12, 0), blush=0.9)
            dy = -18 * abs(math.sin(u * 9)) * math.exp(-u * 1.5)
    return st, rot, dy

def sh_state(t, i):
    st = SH.base(); rot = 0.0
    st.update(hand_l=(170, 760), hand_r=(530, 760))
    if t < 5.0:
        if SH_HELP[0] <= t < SH_HELP[1] or SH_OK[0] <= t < SH_OK[1]:
            st.update(mouth='talk', lid=0.3, look=(20, 2), blush=0.6); rot = -3 * math.sin(t * 6)
        else:
            st.update(mouth='grin', lid=0.4, look=(18, 14), blush=0.5)
    else:
        u = t - STAMP
        if u < 0.4: st.update(mouth='grin', lid=0.3, look=(20, 18))
        else:
            k = (i // 3) % 2
            st.update(mouth='talk' if t < BRAVO[1] else 'grin', lid=0.2, look=(18, 2),
                      hand_l=(300, 650) if k else (270, 660), hand_r=(400, 650) if k else (430, 660)); rot = -3 * math.sin(t * 9)
    return st, rot

HX2, HY2, F2 = 790, 960, 1.45
T_HEAD = (225, 900); TS = 1.45
QUEUE_TWO = [('c2', 560, 720, 0.44, 0.4), ('h0', 720, 660, 0.40, 1.6)]
ID_C = (560, 1500); FORM_C = (450, 1460)

def scene_two(t, i):
    img = SH_BG.copy()
    cheer = CHEER[0] <= t < CHEER[1]
    for name, x, y, sc, ph in QUEUE_TWO:
        jump = (-20 * abs(math.sin(t * 9 + ph))) if cheer else 0
        E13.paste_sprite(img, name, 1 if cheer else 0, x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    if cheer: confetti(img, t - CHEER[0], 1.7)
    st_s, rot_s = sh_state(t, i)
    paste_sh(img, st_s, rot_s, i, T_HEAD, TS)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_two(t, i)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    rp = (HX2 + 230, 1470 + 8 * math.sin(t * 2.0))
    u = t - IDSLAP
    if -0.2 <= u < 0.4: rp = lerp2((HX2 - 60, 1150), (ID_C[0] + 60, ID_C[1] + 20), ease_in(clamp((u + 0.2) / 0.2)))
    if SIGN[0] - 0.1 <= t < SIGN[1] + 0.1:                 # the signing paw
        a = clamp((t - SIGN[0]) / (SIGN[1] - SIGN[0]))
        rp = (FORM_C[0] - 40 + 140 * a, FORM_C[1] + 120 - 14 * math.sin(a * 18))
    if t >= STAMP: v = t - STAMP; rp = (HX2 + 200, 1250 - 60 * abs(math.sin(v * 9)) * math.exp(-v * 1.2))   # fist pump
    capsule(d, (HX2 + 220, 1520), rp, 100, FUR, OUT, 4)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    if t >= IDSLAP - 0.2:                                  # ID card on the counter
        idc = ID_C if u >= 0 else lerp2((HX2 - 60, 1120), ID_C, ease_in(clamp((u + 0.2) / 0.2)))
        shadow_paste(img, ID.rotate(-5, resample=Image.BICUBIC, expand=True), idc if t < FORM_IN else (790, 1520), 80, (8, 12), 6)
    if t >= FORM_IN:                                       # the form slides in, he signs
        fc = lerp2((150, 1500), FORM_C, ease_out(clamp((t - FORM_IN) / 0.2)))
        shadow_paste(img, FORM.rotate(-3, resample=Image.BICUBIC, expand=True), fc, 80, (8, 12), 6)
        d = ImageDraw.Draw(img)
        if t >= SIGN[0]: signature(d, (fc[0] - 30, fc[1] + 120), (t - SIGN[0]) / (SIGN[1] - SIGN[0]))
        if t >= STAMP: imprint(img, (fc[0] + 10, fc[1] - 40), t - STAMP, 'שוחרר', 0.8)
        sp_ = None
        us = t - STAMP
        if -0.3 <= us < 0: sp_ = lerp2((FORM_C[0] + 20, 1150), (FORM_C[0] + 10, 1420), ease_in(clamp((us + 0.3) / 0.3)))
        elif 0 <= us < 0.25: sp_ = (FORM_C[0] + 10, 1420)
        elif 0.25 <= us < 0.6: sp_ = lerp2((FORM_C[0] + 10, 1420), (300, 1250), ease_out((us - 0.25) / 0.35))
        d = ImageDraw.Draw(img)
        if sp_: stamp_tool(d, sp_, 1.1)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, rp, -10, 0.85)
    burst(img, ID_C, u, (255, 255, 255), 140, 8, 0.3)
    burst(img, (FORM_C[0], FORM_C[1] + 100), t - CHK2, (120, 255, 160), 140, 8, 0.3)
    burst(img, (FORM_C[0], FORM_C[1] - 40), t - STAMP, (255, 214, 64), 170, 12, 0.4)
    if SH_HELP[0] <= t < SH_HELP[1]: SH.bubble(img, 'בוא נשחרר אותך, מותק.', t - SH_HELP[0], (520, 640, 760, 130), (300, 780), side=-1)
    if SH_OK[0] <= t < SH_OK[1]: SH.bubble(img, 'תעודה? מושלם.', t - SH_OK[0], (520, 640, 520, 130), (300, 780), side=-1)
    if BRAVO[0] <= t < BRAVO[1]: SH.bubble(img, 'חופשי, מותק!', t - BRAVO[0], (520, 640, 480, 130), (300, 780), side=-1)
    return img

HX, HY, F = 690, 900, 1.8
def cat_state_close(t, i):
    st = base_cat()
    st.update(lid=0.1, pupil='big', brow='up', mouth='munch' if (i // 3) % 2 == 0 else 'smile', look=(-10, 6), blush=0.8, ear_dy=-10)
    if BUB_ONE[0] <= t < BUB_ONE[1] and (i // 4) % 3 == 0: st['mouth'] = 'w'
    return st, 2.5 * sway(t), -6 * abs(math.sin(t * 6))

def scene_cat(t, i):
    img = WIN_BG.copy()
    for name, x, y, sc, ph in V1.QUEUE_BEHIND:
        E13.paste_sprite(img, name, 0, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_close(t, i)
    E(d, HX, 1640, 450, 470, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1700, 210, 320, fill=CREAM)
    rp = (930, 1400 + 30 * math.sin(t * 7))                # the bag he munches from (mid-climb plant)
    capsule(d, (HX + 250, 1420), rp, 120, FUR, OUT, 4)
    SH.snack_bag(d, (rp[0] - 30, rp[1] - 120), 10 + 4 * math.sin(t * 5), 1.4)
    d = ImageDraw.Draw(img); E12.big_paw(d, rp, -10)
    E12.paste_head(img, st, i, HX, HY + dy, F, rot)
    if BUB_ONE[0] <= t < BUB_ONE[1]: SH.bubble(img, 'רק עוד חותמת!', t - BUB_ONE[0], (560, 1560, 560, 130), (640, 1420), side=1)
    return img

# ------------------------------------------------------------------ frame
KIOSK_BG = SH_BG = WIN_BG = CARD = TERM_OK = TERM_RED = TERM_GREEN = DECL_CHIP = CHIP47 = CHIP50 = ID = FORM = PILL_EP = PILL_Q = None
def init_all():
    global KIOSK_BG, SH_BG, WIN_BG, CARD, TERM_OK, TERM_RED, TERM_GREEN, DECL_CHIP, CHIP47, CHIP50, ID, FORM, PILL_EP, PILL_Q
    m.init_static()
    KIOSK_BG = V1.build_kiosk_bg().filter(ImageFilter.GaussianBlur(S(2)))
    ob = E3.build_office_bg()
    E8.plaque(ImageDraw.Draw(ob), 780, 790, 'הבנק שלי · חלון 3', 440)
    SH_BG = ob.filter(ImageFilter.GaussianBlur(S(3)))
    wb = E3.build_window_bg(); E8.plaque(ImageDraw.Draw(wb), 820, 640, 'הבנק שלי', 300)
    WIN_BG = wb.filter(ImageFilter.GaussianBlur(S(3)))
    CARD = V1.card_layer(); TERM_OK = V1.terminal_layer(0); TERM_RED = V1.terminal_layer(1); TERM_GREEN = terminal_green()
    DECL_CHIP = Image.new('RGBA', (S(300), S(120)), (0, 0, 0, 0)); dd = ImageDraw.Draw(DECL_CHIP)
    dd.rounded_rectangle([0, 0, S(300) - 1, S(120) - 1], radius=S(24), fill=RED, outline=(90, 10, 14), width=iw(5))
    dd.text((S(150), S(62)), 'נדחה', font=font(S(80), 900), fill=WHITE, anchor='mm')
    DECL_CHIP = DECL_CHIP.rotate(8, resample=Image.BICUBIC, expand=True)
    CHIP47 = red_chip(47); CHIP50 = red_chip(50)
    ID = id_layer(); FORM = form_layer(False)
    E13.build_crowd()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 560.0, 980.0
    rng = random.Random(int(t * FPS)); sh_ = 0.0
    if name == 'kiosk':
        cy = 1000.0
        if a == 0.0:
            for td in (DECL1, DECL2, FLAG):
                us = t - td
                if 0 <= us < 0.4: sh_ = 3 + 20 * math.exp(-us * 8)
            if t < DECL1: z = 1.18
            elif t < DECL2: z = lerp(1.18, 1.0, ease_out(clamp((t - DECL1) / 0.25)))
            else: z = lerp(1.12, 1.0, ease_out(clamp((t - DECL2) / 0.25))); cx = lerp(470, 560, ease_out(clamp((t - DECL2) / 0.4)))
        else:
            if t < 9.6: z = 1.0
            else: z = lerp(1.0, 1.14, ease_io(clamp((t - 9.6) / (TAPC - 9.6)))); cx = lerp(560, 450, clamp((t - 9.6) / 1.5)); cy = lerp(1000, 1080, clamp((t - 9.6) / 1.5))
            us = t - BACK
            if 0 <= us < 0.35: sh_ = 3 + 16 * math.exp(-us * 8)
            if t >= BREAK:
                e = ease_out(clamp((t - BREAK) / 0.12)); z, cx, cy = lerp(1.14, 1.22, e), lerp(450, 520, e), lerp(1080, 980, e)
                us = t - BREAK
                if us < 0.35: sh_ = 3 + 18 * math.exp(-us * 9)
    elif name == 'two':
        if t - a < 0.3: z = lerp(1.18, 1.0, ease_out((t - a) / 0.3))
        u = t - IDSLAP
        if 0 <= u < 0.4: z = max(z, 1.0 + 0.07 * math.exp(-u * 9)); cy = 1100
        us = t - STAMP
        if 0 <= us < 0.4: z = max(z, 1.0 + 0.1 * math.exp(-us * 8)); cy = 1150
    elif name == 'cat':
        z = lerp(1.2, 1.0, ease_out(clamp((t - a) / 0.3))); cx, cy = 600.0, 980.0
    cx += rng.uniform(-sh_, sh_); cy += rng.uniform(-sh_, sh_)
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    img = {'kiosk': scene_kiosk, 'two': scene_two, 'cat': scene_cat}[name](t, i)
    z, ccx, ccy = camera(t)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if PEAK[0] <= t < TAPC:
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - PEAK[0]) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(40 * k))))
    for s_ in (DECL1, DECL2, CHK1, CHK2, STAMP, TAPC, BREAK):
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
    if not (TAPC <= t < BREAK): meter(frame, t)
    if t < 1.9:
        frame.alpha_composite(PILL_EP, (40, 70)); frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    elif t >= FREEZE[0] and int(t * 10) % 3 != 0:
        frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (SFX + kiosk/branch murmur, no groove)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR); out = np.zeros(n); add = m.add
    rng = np.random.default_rng(2121)
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
    def murmur(t0, t1, g):
        d_ = t1 - t0; tt = tt_(d_)
        mod = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 1.7 * tt + 1))
        env = np.minimum(1, np.minimum(tt / 0.08, (d_ - tt) / 0.08))
        add(out, m.bandpass(nz(d_), 250, 2200) * mod * env, t0, g)
    def check(t0, g=0.12, base=523.3):
        for k_, f_ in enumerate((base, base * 1.26, base * 1.5)):
            add(out, m.tone(f_, 0.22, harm=((1, 1), (2, 0.3)), decay=7), t0 + 0.07 * k_, g)
    def beepboop(t0, g=0.18):
        add(out, m.tone(880, 0.12, harm=((1, 1),), decay=4), t0, g); add(out, m.tone(440, 0.22, harm=((1, 1), (3, 0.3)), decay=4), t0 + 0.13, g)
    def beep_ok(t0, g=0.18):
        add(out, m.tone(1568, 0.16, harm=((1, 1),), decay=5), t0, g)
    def applause(t0, t1, g):
        tc = t0; r = random.Random(5)
        while tc < t1:
            add(out, m.bandpass(nz(0.03), 1200, 6000) * np.exp(-tt_(0.03) * 120), tc, g * r.uniform(0.5, 1.0)); tc += r.uniform(0.015, 0.045)
    murmur(0.0, PEAK[0] - 0.15, 0.08)
    whoosh(0.0, 0.08, 0.3)
    beepboop(DECL1); thump(DECL1, 0.6); beepboop(DECL2, 0.22); thump(DECL2, 0.7)
    pop(FLAG, 0.24); thump(FLAG, 0.4)
    for tc in (1.9, 5.0, 6.3, 8.4): whoosh(tc - 0.08, 0.16, 0.08)
    pop(SH_HELP[0], 0.18)
    thump(IDSLAP, 0.5); check(CHK1, 0.12); pop(SH_OK[0], 0.18)
    whoosh(FORM_IN, 0.2, 0.15)
    tc = SIGN[0]
    while tc < SIGN[1]:
        add(out, m.bandpass(nz(0.05), 2500, 8000) * np.exp(-tt_(0.05) * 30), tc, 0.06); tc += 0.06
    check(CHK2, 0.13, 587.3)
    tc = MUNCHB[0] + 0.1
    while tc < MUNCHB[1] - 0.1:
        add(out, m.bandpass(nz(0.07), 1500, 7000) * np.exp(-tt_(0.07) * 45), tc, 0.12); tc += 0.2
    pop(BUB_ONE[0], 0.2)
    thump(STAMP, 0.9); add(out, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), STAMP, 0.4); check(CHK3, 0.15, 659.3)
    applause(CHEER[0], CHEER[1] - 0.1, 0.07); pop(BRAVO[0], 0.2)
    whoosh(BACK - 0.05, 0.3, 0.35); thump(BACK + 0.3, 0.5)
    for k_ in range(5): pop(BACK + 0.35 + 0.11 * k_, 0.07)
    for hb in (PEAK[0] + 0.02, PEAK[0] + 0.5):
        thump(hb, 0.32); thump(hb + 0.16, 0.22)
    beep_ok(TAPC, 0.2); check(TAPC + 0.05, 0.14, 784.0)
    thump(BREAK, 0.95); beepboop(BREAK + 0.02, 0.25); add(out, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), BREAK, 0.5)
    murmur(BREAK + 0.05, DUR, 0.03)
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
        sheet.save(os.path.join(OUTDIR, f'ep21{tag}_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'ep21{tag}_audio.wav'); build_audio(wav); print('audio ok')
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
