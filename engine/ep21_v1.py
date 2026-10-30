#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 21: הבנק שלי: החשבון הוקפא (season 5 "החשבון" opener, built 28.10, 12.0 s;
experiment everyday_setting_open = the episode opens in an everyday place, not an office).
Frame 0: the chill cat big and facing camera at a kiosk checkout (shelves of snack bags, a queue of shoppers' faces behind
him), his card already coming down on the payment terminal; BEEP-BOOP at 0.1 → red "נדחה", snap pull-back; second try at
0.8 → "נדחה" again + dun-dun. Hook "הבנק שלי הקפיא / לך את החשבון?".
Phone close-up (still in the kiosk, faces behind): "הבנק שלי · החשבון הוקפא" + red chip "פעילות חריגה: 47 שקיות חטיפים".
Sharit at window 3 of הבנק שלי: "פעילות חריגה, מותק." → snap zoom "לשחרור: תפקיד 50 ₪."
Two-shot: the cat slaps a ₪50 note on the counter "הנה! 50 ₪!" → STAMP "שוחרר", fist pump.
Sharit snap zoom: "...ירדה עמלת שחרור: 50 ₪, מותק." + dun-dun. Cat frozen at the window (faces behind):
"50 ₪ להפקדה. / 50 ₪ עמלת שחרור." (send beat) + slow blink. Two-shot: "וואלה." + munch, "כל. פעם. מחדש.",
Sharit offers her snack bag "חטיף, מותק? על חשבון הבנק.", yellow "מחר: הפרטים שלי דלפו".
Back at the kiosk, the card comes down again = frame 0 (loop, ticket pill flickers). Pills "פרק 21" + 🎟 (hud.stage_of, §O4).
Hint-level only. SFX + kiosk/branch murmur, no groove.

  python3 ep21.py test 0 0.15 0.5 0.9 1.6 2.1 3.0 3.5 4.2 4.8 5.6 6.6 7.2 8.2 9.0 9.8 11.4 11.95  -> out/ep21_contact.png
  python3 ep21.py render                                                                     -> out/ep21_frozen.mp4
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

DUR = 12.0
NF = int(round(DUR * FPS))
OUTDIR = m.OUTDIR
YELLOW = (255, 221, 51)
BEAT = 60 / 80
QUEUE = int(os.environ.get('QUEUE', '482'))
EP_LABEL = 'פרק 21'
TAG_OUT = os.environ.get('OUTNAME', 'ep21_frozen')
KZ = float(os.environ.get('KZ', '1.0'))          # probe: base zoom of the kiosk shot
TWOONLY = os.environ.get('TWOONLY', '0') == '1'   # probe: Sharit's solo close-ups become two-shots

SHOTS = [('kiosk', 0.0, 1.5), ('cat', 1.5, 2.8), ('two' if TWOONLY else 'sh', 2.8, 3.9), ('two', 3.9, 5.4),
         ('two' if TWOONLY else 'sh', 5.4, 6.4), ('cat', 6.4, 7.8), ('two', 7.8, 11.3), ('kiosk', 11.3, DUR + 1)]
DECL1 = 0.1            # card on the terminal -> נדחה
DECL2 = 0.8            # second try -> נדחה again
PHONE_IN = 1.5
FLAG = 1.95            # "פעילות חריגה" chip slams in
SH_TALK = 2.95         # "פעילות חריגה, מותק."
SH_TALK2 = 3.35        # "לשחרור: תפקיד 50 ₪."
CSLAP = 4.05           # the ₪50 note on the counter
STAMP = 4.65           # "שוחרר"
FEE = 5.55             # "עמלת שחרור: 50 ₪, מותק."
FROZE = 6.4
BLINK1 = (7.1, 7.45)
WALLA = (8.0, 8.5)
MUNCH = 8.45
OFFER = 9.4            # Sharit offers her snack bag
LOOPIN = 11.3

CAPTIONS = [  # (t0, t1, lines, size, y, fill)
    (0.0, 1.5, ['הבנק שלי הקפיא', 'לך את החשבון?'], 100, 290, WHITE),          # keyword on frame 1
    (1.5, 2.8, ['החשבון הוקפא?', 'פעילות חריגה: חטיפים.'], 88, 290, WHITE),
    (3.9, 5.4, ['לשחרר את החשבון?', 'תפקיד 50 ₪.'], 92, 290, WHITE),
    (FROZE, 7.8, ['50 ₪ להפקדה.', '50 ₪ עמלת שחרור.'], 96, 290, WHITE),
    (8.15, OFFER, ['כל. פעם. מחדש.'], 100, 270, WHITE),
    (OFFER, LOOPIN, ['מחר: הפרטים שלי דלפו'], 82, 280, YELLOW),
    (LOOPIN, DUR + 0.1, ['הבנק שלי הקפיא', 'לך את החשבון?'], 100, 290, WHITE),
]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

sway = E18.sway; burst = E18.burst; imprint = E18.imprint; stamp_tool = E18.stamp_tool; paste_sh = E18.paste_sh

# ------------------------------------------------------------------ props
BLUE = (28, 104, 226); RED = (214, 44, 52)

TMW, TMH = 260, 400
def terminal_layer(state):
    """payment terminal. state 0 = 'נא להצמיד כרטיס', 1 = red 'נדחה'"""
    lay = Image.new('RGBA', (S(TMW), S(TMH)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(TMW) - 1, S(TMH) - 1], radius=S(34), fill=(44, 46, 54), outline=(16, 16, 20), width=iw(6))
    scr = (RED if state else (210, 236, 214))
    d.rounded_rectangle([S(24), S(26), S(TMW - 24), S(150)], radius=S(14), fill=scr, outline=(16, 16, 20), width=iw(4))
    if state:
        d.text((S(TMW / 2), S(88)), 'נדחה', font=font(S(64), 900), fill=WHITE, anchor='mm')
    else:
        d.text((S(TMW / 2), S(70)), 'להצמיד', font=font(S(36), 800), fill=(30, 60, 40), anchor='mm')
        d.text((S(TMW / 2), S(112)), 'כרטיס', font=font(S(36), 800), fill=(30, 60, 40), anchor='mm')
    cols = [(230, 230, 236)] * 9 + [(220, 60, 60), (230, 230, 236), (60, 170, 90)]
    for k in range(12):
        x0 = 40 + (k % 3) * 64; y0 = 176 + (k // 3) * 54
        d.rounded_rectangle([S(x0), S(y0), S(x0 + 50), S(y0 + 40)], radius=S(8), fill=cols[k], outline=(16, 16, 20), width=iw(2))
    return lay

def card_layer():
    lay = Image.new('RGBA', (S(240), S(152)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(239), S(151)], radius=S(16), fill=BLUE, outline=(10, 30, 80), width=iw(4))
    d.rounded_rectangle([S(26), S(46), S(70), S(80)], radius=S(6), fill=(232, 196, 90))
    d.text((S(214), S(32)), 'הבנק שלי', font=font(S(28), 900), fill=WHITE, anchor='rm')
    d.text((S(120), S(118)), '•••• 4827', font=font(S(26), 800), fill=(220, 230, 255), anchor='mm')
    return lay

def note_layer():
    """a ₪50 note (generic, no real design)"""
    lay = Image.new('RGBA', (S(380), S(190)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(379), S(189)], radius=S(12), fill=(150, 210, 160), outline=(40, 100, 60), width=iw(5))
    d.rounded_rectangle([S(16), S(16), S(364), S(174)], radius=S(8), outline=(60, 130, 80), width=iw(3))
    E(d, 110, 95, 58, 58, fill=(120, 190, 136), outline=(60, 130, 80), width=3)
    d.text((S(260), S(96)), '50 ₪', font=font(S(78), 900), fill=(20, 70, 40), anchor='mm')
    return lay

PW, PH = 400, 700
def phone_layer():
    """phone: the bank app — the account is frozen"""
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(242, 244, 248))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.rectangle([S(14), S(70), S(PW - 14), S(160)], fill=BLUE)
    pd.text((S(PW / 2), S(116)), 'הבנק שלי', font=font(S(44), 900), fill=WHITE, anchor='mm')
    # padlock + "החשבון הוקפא"
    cx, cy = PW / 2, 280
    pd.arc([S(cx - 46), S(cy - 96), S(cx + 46), S(cy - 4)], 180, 360, fill=(90, 100, 120), width=iw(14))
    pd.rounded_rectangle([S(cx - 66), S(cy - 40), S(cx + 66), S(cy + 70)], radius=S(14), fill=(120, 170, 230), outline=(40, 70, 120), width=iw(5))
    E(pd, cx, cy + 8, 12, 12, fill=(40, 70, 120))
    pd.text((S(PW / 2), S(400)), 'החשבון הוקפא', font=font(S(46), 900), fill=INK, anchor='mm')
    pd.text((S(PW / 2), S(452)), 'הסיבה:', font=font(S(30), 800), fill=(110, 116, 130), anchor='mm')
    return lay

def flag_chip(img, c, u):
    """red "פעילות חריגה: 47 שקיות חטיפים" slams onto the phone"""
    if u < 0: return
    sc = 1.5 - 0.5 * ease_out(clamp(u / 0.12))
    lay = Image.new('RGBA', (S(420), S(170)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(420) - 1, S(170) - 1], radius=S(22), fill=RED)
    d.text((S(210), S(52)), 'פעילות חריגה:', font=font(S(46), 900), fill=WHITE, anchor='mm')
    d.text((S(210), S(118)), '47 שקיות חטיפים', font=font(S(46), 900), fill=(255, 236, 120), anchor='mm')
    lay = lay.rotate(-6, resample=Image.BICUBIC, expand=True)
    lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    m.paste_center(img, lay, S(c[0]), S(c[1]))

def shadow_paste(img, lay, c, a=100, off=(14, 18), blur=10):
    shd = Image.new('RGBA', lay.size, (0, 0, 0, 0)); shd.paste((0, 0, 0, a), mask=lay.split()[3]); shd = shd.filter(ImageFilter.GaussianBlur(S(blur)))
    m.paste_center(img, shd, S(c[0] + off[0]), S(c[1] + off[1])); m.paste_center(img, lay, S(c[0]), S(c[1]))

# ------------------------------------------------------------------ the kiosk set
def build_kiosk_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):                                   # warm wall gradient
        v = y / H; d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(250, 214, v)), int(lerp(214, 168, v)), int(lerp(150, 110, v))))
    rng = random.Random(21)
    bag_cols = [(244, 160, 36), (226, 60, 60), (60, 150, 220), (90, 190, 90), (240, 210, 60), (170, 90, 200)]
    for row, y in enumerate((520, 820, 1120)):                 # shelves full of snack bags (generic, no brands)
        d.rectangle([S(-10), S(y + 70), S(W + 10), S(y + 96)], fill=(130, 84, 50), outline=(80, 50, 28), width=iw(4))
        x = 40 + (row % 2) * 50
        while x < W:
            col = rng.choice(bag_cols); s_ = rng.uniform(0.55, 0.7)
            pts = [(x - 52 * s_, y + 70 - 140 * s_), (x + 52 * s_, y + 70 - 140 * s_), (x + 48 * s_, y + 70), (x - 48 * s_, y + 70)]
            poly(d, pts, fill=col, outline=tuple(max(0, c - 90) for c in col), width=3)
            E(d, x, y + 70 - 70 * s_, 22 * s_, 22 * s_, fill=(255, 255, 255))
            x += 120 * s_ + 14
    # fridge glow on the right
    d.rounded_rectangle([S(880), S(380), S(1120), S(1500)], radius=S(20), fill=(200, 230, 246), outline=(90, 120, 140), width=iw(6))
    for y in (640, 900, 1160): d.rectangle([S(890), S(y), S(1110), S(y + 10)], fill=(150, 180, 200))
    E8.plaque(d, 300, 330, 'קיוסק', 260)
    return img

def build_counter(img):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1590), S(1100), S(1960)], radius=S(16), fill=(150, 96, 58), outline=(80, 50, 28), width=iw(6))
    d.rectangle([S(-20), S(1590), S(1100), S(1620)], fill=(190, 130, 80))

QUEUE_KIOSK = [('h0', 150, 820, 0.50, 0.3), ('c2', 330, 760, 0.46, 1.4), ('c3', 960, 800, 0.50, 2.2), ('h2', 1060, 900, 0.48, 0.9)]
QUEUE_BEHIND = [('c0', 140, 760, 0.55, 0.0), ('h1', 330, 700, 0.45, 1.1), ('c3', 1000, 1180, 0.55, 2.0)]

# ------------------------------------------------------------------ cat states
def cat_state_kiosk(t, i, back=False):
    st = E7.chill_state(); sw = sway(t)
    st.update(cobweb=1.0, red=0.9, blush=0.3, look=(-10, 10))
    rot, dy = 0.0, 0.0
    if back:
        if t < DUR - 0.62:                                 # chill, munching a bit, swaying
            st.update(lid=0.55, mouth='goofy', look=(-6, 10)); return st, 3.0 * sw, 4 * abs(sw)
        st.update(lid=0.1, pupil='normal', brow='none', mouth='smile', look=(-16, 12), blush=0.0); return st, 0.0, 0.0
    if t < DECL1:                                          # hopeful: card coming down
        st.update(lid=0.1, pupil='normal', brow='none', mouth='smile', look=(-16, 12), blush=0.0); return st, 0.0, 0.0
    if t < DECL2:                                          # BEEP: huge eyes
        u = t - DECL1
        st.update(lid=0.0, pupil='big', brow='up', ear_dy=-24 * math.exp(-u * 4), mouth='w', look=(-18, 12), blush=0.0)
        dy = -26 * math.exp(-u * 8) * math.cos(u * 26); rot = 5 * math.exp(-u * 5) * math.sin(u * 22)
        if u > 0.45: st.update(lid=0.1, pupil='normal', brow='annoyed', mouth='flat', look=(-14, 12))   # try again
        return st, rot, dy
    u = t - DECL2                                          # second נדחה: breaking
    st.update(lid=0.0, pupil='tiny', brow='sad', mouth='w', ear_droop=0.6 * clamp(u / 0.3), sweat=1.0, look=(-16, 10),
              ear_dy=-20 * math.exp(-u * 5), twitch=(0.2 < u < 0.7 and int(t * 12) % 2 == 0))
    rot = 5 * math.exp(-u * 4) * math.sin(u * 22)
    return st, rot, dy

def cat_state_close(t, i):
    st = E7.chill_state()
    st.update(cobweb=1.0, red=0.9, blush=0.3)
    rot, dy = 0.0, 0.0
    if t < 2.8:                                            # phone: "רגע, למה?!" then the chip -> shock, ears up
        if t < FLAG:
            st.update(lid=0.0, pupil='big', brow='annoyed', mouth='w', ear_dy=-14, blush=0.0, look=(-20, 4))
        else:
            v = t - FLAG
            st.update(lid=0.0, pupil='big' if v < 0.35 else 'tiny', brow='up', mouth='w', ear_dy=-26 * math.exp(-v * 3), sweat=1.0, look=(-16, 4),
                      blush=0.9 if v > 0.4 else 0.0)                         # caught: blush at the snack count
            rot = 5 * math.exp(-v * 4) * math.sin(v * 22)
    else:                                                  # frozen at the window + slow blink
        u = t - FROZE
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-18 * math.exp(-max(0, u) * 4), look=(0, 0),
                  twitch=(0.15 < u < 0.7 and int(t * 12) % 2 == 0))
        if u > 0.45: st.update(lid=0.1, pupil='normal', brow='sad', mouth='w', look=(-14, -6))
        if BLINK1[0] <= t < BLINK1[1]: st['lid'] = 1.0
        elif t >= BLINK1[1]: st.update(lid=0.55, mouth='goofy', ear_droop=0.6, look=(6, 10))
        rot = -2
    return st, rot, dy

def cat_state_two(t, i):
    st = E7.chill_state(); sw = sway(t)
    st.update(cobweb=1.0, red=0.9, blush=0.3)
    rot, dy = 0.0, 0.0
    if t < 3.9:                                            # listening: side-eye, shock at "50 ₪"
        st.update(lid=0.4 if t < SH_TALK2 else 0.0, pupil='normal' if t < SH_TALK2 else 'big', brow='annoyed' if t < SH_TALK2 else 'up',
                  mouth='flat' if t < SH_TALK2 else 'w', look=(-18, 6), ear_dy=0 if t < SH_TALK2 else -16)
        return st, rot, dy
    if 5.4 <= t < 6.4:                                     # "עמלת שחרור: 50 ₪" — dread
        u = t - FEE
        st.update(lid=0.0, pupil='normal' if u < 0 else 'tiny', brow='up', mouth='smile' if u < 0 else 'w', ear_dy=-20 * math.exp(-max(0, u) * 4),
                  look=(-16, 2), sweat=1.0 if u > 0 else 0.0, twitch=(0.3 < u < 0.8 and int(t * 12) % 2 == 0))
        return st, rot, dy
    if t < STAMP:                                          # determined: slaps the note down
        u = t - CSLAP
        st.update(lid=0.0, pupil='big', brow='annoyed', mouth='w', ear_dy=-20, look=(-16, 4))
        if u >= 0: dy = 16 * math.exp(-u * 8) * math.cos(u * 20)
    elif t < 5.4:                                          # "שוחרר" — joy
        u = t - STAMP
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24 * math.exp(-u * 3), look=(-16, 0), blush=0.8)
        dy = -18 * abs(math.sin(u * 9)) * math.exp(-u * 2)
    else:                                                  # ending: chill
        st.update(look=(-6, 8), mouth='goofy'); rot = 4.5 * sw; dy = 6 * abs(sw)
        if WALLA[0] <= t < WALLA[0] + 0.4:
            s_ = math.sin(math.pi * (t - WALLA[0]) / 0.4); st.update(ear_dy=-14 * s_, brow='up' if s_ > 0.3 else 'none', mouth='w'); dy -= 12 * s_
        if MUNCH + 0.1 <= t < MUNCH + 0.7: st['mouth'] = 'munch' if (i // 3) % 2 == 0 else 'w'
        if t >= OFFER:                                     # the offer: eyes on the bag, delighted
            u = t - OFFER
            st.update(lid=0.0 if u < 0.6 else 0.45, pupil='big', brow='up', look=(-20, 0), mouth='smile' if u < 1.2 else ('munch' if (i // 3) % 2 == 0 else 'goofy'),
                      ear_dy=-16 * math.exp(-u * 3), blush=0.8)
    return st, rot, dy

# ------------------------------------------------------------------ Sharit
def sh_state(t, i):
    st = SH.base(); rot = 0.0
    st.update(hand_l=(170, 760), hand_r=(530, 760))
    if t < 3.9:                                            # close-up: munching, then talking
        if t < SH_TALK: st.update(mouth='munch', lid=0.6, look=(10, 8), snack=True, hand_l=(200, 600))
        else:
            u = t - (SH_TALK2 if t >= SH_TALK2 else SH_TALK)
            st.update(mouth='talk', lid=0.3, look=(0, 0), snack=True, hand_l=(200, 620), finger=t >= SH_TALK2, hand_r=(560, 560) if t >= SH_TALK2 else (530, 760))
            rot = -6 * math.exp(-u * 4) * math.cos(u * 10)
    elif t < 5.4:
        if t < STAMP - 0.25: st.update(mouth='munch', lid=0.55, look=(18, 10), snack=True)
        else: st.update(mouth='grin' if t < STAMP + 0.2 else 'talk', lid=0.3, look=(18, 6), snack=True); rot = -4 * math.exp(-max(0, t - STAMP) * 5)
    elif t < 6.4:                                          # close-up: "עמלת שחרור: 50 ₪, מותק."
        u = t - FEE
        st.update(mouth='grin' if u < 0 else 'talk', lid=0.45 if u < 0 else 0.2, look=(0, 0), finger=u >= 0, hand_r=(560, 560))
        if u >= 0: rot = -5 * math.exp(-u * 5)
    else:
        if t < OFFER: st.update(mouth='munch', lid=0.6, look=(16, 6), snack=True, hand_l=(200, 620))
        else:
            u = t - OFFER
            st.update(mouth='talk' if u < 1.1 else 'grin', lid=0.4, look=(14, 2), snack=True,
                      hand_l=lerp2((200, 620), (330, 520), ease_out(clamp(u / 0.3)))); rot = -4 * sway(t)
    return st, rot

# ------------------------------------------------------------------ scenes
HX, HY, F = 690, 900, 1.8
KX, KY, KF = 640, 900, 1.72
TERM_C = (250, 1380)

def card_pos(t, back=False):
    """card centre in the kiosk shot: comes down onto the terminal at DECL1, lifts, comes down again at DECL2"""
    if back:
        u = (t - (DUR - 0.6)) / 0.7
        if u < 0: return (560, 1250), 20
        return lerp2((560, 1250), (300, 1215), ease_in(clamp(u))), lerp(20, 6, clamp(u))
    if t < DECL1:
        u = (t + 0.6) / 0.7
        return lerp2((560, 1250), (300, 1215), ease_in(clamp(u))), lerp(20, 6, clamp(u))
    if t < DECL2 - 0.3: return lerp2((300, 1215), (500, 1110), ease_out(clamp((t - DECL1 - 0.04) / 0.12))), 14
    if t < DECL2: return lerp2((500, 1110), (300, 1215), ease_in(clamp((t - (DECL2 - 0.3)) / 0.3))), 6
    return lerp2((300, 1215), (520, 1100), ease_out(clamp((t - DECL2 - 0.04) / 0.12))), 16 + 4 * math.sin(t * 9)

def scene_kiosk(t, i, back=False):
    img = KIOSK_BG.copy()
    mood = 1 if (not back and DECL2 <= t < 1.5) else 0
    for name, x, y, sc, ph in QUEUE_KIOSK:
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_kiosk(t, i, back)
    E(d, KX, 1640, 430, 450, fill=FUR, outline=OUT, width=7)
    E(d, KX, 1700, 200, 300, fill=CREAM)
    build_counter(img); d = ImageDraw.Draw(img)
    for k, (x, ang) in enumerate(((640, -8), (790, 6), (930, -4))):          # his purchase on the counter
        SH.snack_bag(d, (x, 1560 + 4 * math.sin(t * 3 + k)), ang, 0.8)
    declined = (not back) and t >= DECL1 and not (DECL2 - 0.3 <= t < DECL2)
    lay = TERM_RED if declined else TERM_OK
    shadow_paste(img, lay.rotate(4, resample=Image.BICUBIC, expand=True), TERM_C)
    d = ImageDraw.Draw(img)
    c, ang = card_pos(t, back)
    cl = CARD.rotate(ang, resample=Image.BICUBIC, expand=True)
    paw = (c[0] + 120, c[1] + 40)
    capsule(d, (KX - 180, 1440 + dy * 0.4), paw, 110, FUR, OUT, 4)
    shadow_paste(img, cl, c, 90, (10, 14), 8)
    d = ImageDraw.Draw(img); E12.big_paw(d, paw, -20, 0.9)
    E12.paste_head(img, st, i, KX, KY + dy, KF, rot)
    if not back:
        for td in (DECL1, DECL2):
            burst(img, (TERM_C[0], TERM_C[1] - 110), t - td, (255, 120, 120), 150, 10, 0.35)
        if t >= DECL1 and not (DECL2 - 0.3 <= t < DECL2):    # big red "נדחה" pops over the terminal
            u = t - (DECL2 if t >= DECL2 else DECL1)
            sc = (1.6 if t >= DECL2 else 1.4) - 0.4 * ease_out(clamp(u / 0.12))
            lay = DECL_CHIP.resize((max(1, int(DECL_CHIP.width * sc)), max(1, int(DECL_CHIP.height * sc))), Image.BICUBIC)
            shadow_paste(img, lay, (TERM_C[0] + 10, TERM_C[1] - 290 + 6 * math.sin(t * 14)), 110, (10, 14), 8)
    return img

def scene_cat(t, i):
    inq = t >= 6.0
    img = (WIN_BG if inq else KIOSK_BLUR).copy()
    mood = 1 if (FROZE <= t < FROZE + 0.9 or FLAG <= t < 2.8) else 0
    for name, x, y, sc, ph in (QUEUE_BEHIND if inq else QUEUE_KIOSK[:2] + [('c3', 1000, 1180, 0.55, 2.0)]):
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_close(t, i)
    E(d, HX, 1640, 450, 470, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1700, 210, 320, fill=CREAM)
    rp = (950, 1500 + 8 * math.sin(t * 2.0))
    capsule(d, (HX + 250, 1420), rp, 120, FUR, OUT, 4)
    if t >= 6.0:                                            # the card in his paw
        lay = CARD.resize((int(CARD.width * 0.75), int(CARD.height * 0.75)), Image.BICUBIC).rotate(14 + 4 * math.sin(t * 5), resample=Image.BICUBIC, expand=True)
        m.paste_center(img, lay, S(rp[0] - 40), S(rp[1] - 110))
        d = ImageDraw.Draw(img)
    E12.big_paw(d, rp, -10)
    E12.paste_head(img, st, i, HX, HY + dy, F, rot)
    d = ImageDraw.Draw(img)
    if t < 2.8:                                             # phone held up next to his face
        u = t - PHONE_IN
        c = (250, lerp(1600, 1060, ease_out(clamp(u / 0.25))) + 6 * math.sin(t * 2.2))
        lay = PHONE.rotate(-6, resample=Image.BICUBIC, expand=True)
        capsule(d, (HX - 260, 1420), (c[0] + 10, c[1] + PH * 0.43), 120, FUR, OUT, 4)
        shadow_paste(img, lay, c, 110, (18, 22), 14)
        d = ImageDraw.Draw(img); E12.big_paw(d, (c[0] + 20, c[1] + PH * 0.47), 8)
        flag_chip(img, (c[0] + 14, c[1] + 150), t - FLAG)
        burst(img, (c[0] + 14, c[1] + 150), t - FLAG, (255, 120, 120), 150, 8, 0.35)
        if 1.62 <= t < FLAG:
            SH.bubble(img, 'רגע, למה?!', t - 1.62, (690, 560, 420, 130), (720, 720), side=1)
    return img

SC_HEAD = (540, 880); SCS = 1.75
def scene_sh(t, i):
    img = SHP_BG.copy()
    st, rot = sh_state(t, i)
    paste_sh(img, st, rot, i, SC_HEAD, SCS)
    if SH_TALK <= t < SH_TALK2:
        SH.bubble(img, 'פעילות חריגה, מותק.', t - SH_TALK, (540, 560, 700, 130), (560, 720), side=-1)
    if SH_TALK2 <= t < 3.9:
        SH.bubble(img, 'לשחרור: תפקיד 50 ₪.', t - SH_TALK2, (540, 560, 740, 130), (560, 720), side=-1)
    if t >= FEE and t < 6.4:
        SH.bubble(img, 'עמלת שחרור: 50 ₪, מותק.', t - FEE, (540, 560, 860, 130), (560, 720), side=-1)
    elif 5.4 <= t < FEE:
        SH.bubble(img, 'שוחרר! רק דבר אחד...', t - 5.4, (540, 560, 760, 130), (560, 720), side=-1)
    return img

HX2, HY2, F2 = 790, 960, 1.45
T_HEAD = (225, 900); TS = 1.45
NOTE_C = (540, 1500)
def stamp_pos(t):
    u = t - STAMP
    top, down = (470, 1180), (520, 1470)
    if u < -0.3: return None
    if u < 0: return lerp2(top, down, ease_in(clamp((u + 0.3) / 0.3)))
    if u < 0.25: return down
    if u < 0.6: return lerp2(down, (330, 1250), ease_out((u - 0.25) / 0.35))
    return None

def scene_two(t, i):
    img = SH_BG.copy(); d = ImageDraw.Draw(img)
    st_s, rot_s = sh_state(t, i)
    paste_sh(img, st_s, rot_s, i, T_HEAD, TS)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_two(t, i)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    rp = (HX2 + 230, 1470 + 8 * math.sin(t * 2.0))
    if 3.9 <= t < 5.4:
        u = t - CSLAP
        rp = lerp2((HX2 - 120, 1150), (HX2 - 160, 1520), ease_in(clamp((u + 0.15) / 0.15))) if u < 0.5 else (HX2 + 230, 1470)
        if STAMP <= t < 5.4:   # fist pump
            v = t - STAMP; rp = (HX2 + 200, 1250 - 60 * abs(math.sin(v * 9)) * math.exp(-v * 1.5))
    if MUNCH - 0.15 <= t < MUNCH + 0.6:
        rp = lerp2(rp, (HX2 + 80, 1180), math.sin(math.pi * (t - (MUNCH - 0.15)) / 0.75))
    if t >= OFFER + 0.5:                                     # reaches for Sharit's bag
        rp = lerp2(rp, (HX2 - 260, 1200), math.sin(math.pi * clamp((t - OFFER - 0.5) / 1.2)) * 0.8)
    capsule(d, (HX2 + 220, 1520), rp, 100, FUR, OUT, 4)
    if t >= 7.8: SH.snack_bag(d, (rp[0] - 20, rp[1] - 100), -12, 1.2)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    u = t - CSLAP
    if 3.9 <= t < 5.4:
        if u >= 0:
            shadow_paste(img, NOTE.rotate(-5, resample=Image.BICUBIC, expand=True), (lerp(580, NOTE_C[0], ease_out(clamp(u / 0.1))), NOTE_C[1]), 80, (8, 12), 6)
            imprint(img, (NOTE_C[0] - 10, NOTE_C[1] + 10), t - STAMP, 'שוחרר', 0.75)
        else:
            shadow_paste(img, NOTE.rotate(-5, resample=Image.BICUBIC, expand=True), (HX2 - 120, 1120 + 380 * ease_in(clamp((u + 0.15) / 0.15))), 80, (8, 12), 6)
        d = ImageDraw.Draw(img)
        sp_ = stamp_pos(t)
        if sp_: stamp_tool(d, sp_, 1.1)
    if 5.4 <= t < 6.4:   # Sharit's fee: she slides the note back to her side
        v = clamp((t - FEE) / 0.4)
        shadow_paste(img, NOTE.rotate(-5, resample=Image.BICUBIC, expand=True), lerp2(NOTE_C, (260, 1500), ease_io(v)), 80, (8, 12), 6)
        imprint(img, lerp2((NOTE_C[0] - 10, NOTE_C[1] + 10), (250, 1510), ease_io(v)), 1.0, 'שוחרר', 0.75)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, rp, -10, 0.85)
    if 3.9 <= t < 5.4:
        burst(img, NOTE_C, u, (255, 255, 255), 140, 8, 0.3)
        burst(img, NOTE_C, t - STAMP, (255, 120, 120), 160, 10, 0.35)
    if TWOONLY:
        if SH_TALK <= t < SH_TALK2: SH.bubble(img, 'פעילות חריגה, מותק.', t - SH_TALK, (520, 560, 700, 130), (300, 720), side=-1)
        if SH_TALK2 <= t < 3.9: SH.bubble(img, 'לשחרור: תפקיד 50 ₪.', t - SH_TALK2, (520, 560, 740, 130), (300, 720), side=-1)
        if FEE <= t < 6.4: SH.bubble(img, 'עמלת שחרור: 50 ₪, מותק.', t - FEE, (520, 560, 860, 130), (300, 720), side=-1)
    if CSLAP + 0.05 <= t < STAMP:
        SH.bubble(img, 'הנה! 50 ₪!', t - CSLAP - 0.05, (640, 560, 460, 130), (740, 720), side=1)
    if STAMP + 0.1 <= t < 5.4:
        SH.bubble(img, 'שוחרר, מותק.', t - STAMP - 0.1, (480, 560, 520, 130), (300, 720), side=-1)
    if WALLA[0] <= t < WALLA[1]:
        SH.bubble(img, 'וואלה.', t - WALLA[0], (600, 560, 300, 120), (720, 720), side=1)
    if OFFER <= t < OFFER + 1.3:
        SH.bubble(img, 'חטיף, מותק? על חשבון הבנק.', t - OFFER, (540, 560, 880, 130), (300, 720), side=-1)
    if t >= 7.8:                                            # chill notes
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(3):
            ts = k * 0.7; age = ((t - ts) % 2.1) / 2.1
            m.draw_note(od, 1000 + 40 * age + 20 * math.sin(age * 8 + k), 1180 - 200 * age, int(170 * math.sin(math.pi * age)), k % 2 == 1)
        img.alpha_composite(ov)
    return img

# ------------------------------------------------------------------ frame
DECL_CHIP = KIOSK_BG = KIOSK_BLUR = SH_BG = SHP_BG = WIN_BG = PHONE = CARD = NOTE = TERM_OK = TERM_RED = PILL_EP = PILL_Q = None
def init_all():
    global DECL_CHIP, KIOSK_BG, KIOSK_BLUR, SH_BG, SHP_BG, WIN_BG, PHONE, CARD, NOTE, TERM_OK, TERM_RED, PILL_EP, PILL_Q
    m.init_static()
    kb = build_kiosk_bg()
    KIOSK_BG = kb.filter(ImageFilter.GaussianBlur(S(2)))
    KIOSK_BLUR = kb.filter(ImageFilter.GaussianBlur(S(5)))
    ob = E3.build_office_bg()
    SH_BG = ob.filter(ImageFilter.GaussianBlur(S(3)))
    SHP_BG = SH_BG.copy()
    E8.plaque(ImageDraw.Draw(SHP_BG), 540, 330, 'הבנק שלי · חלון 3', 460)
    WIN_BG = E3.build_window_bg().filter(ImageFilter.GaussianBlur(S(3)))
    PHONE = phone_layer(); CARD = card_layer(); NOTE = note_layer()
    TERM_OK = terminal_layer(0); TERM_RED = terminal_layer(1)
    DECL_CHIP = Image.new('RGBA', (S(300), S(120)), (0, 0, 0, 0)); dd = ImageDraw.Draw(DECL_CHIP)
    dd.rounded_rectangle([0, 0, S(300) - 1, S(120) - 1], radius=S(24), fill=RED, outline=(90, 10, 14), width=iw(5))
    dd.text((S(150), S(62)), 'נדחה', font=font(S(80), 900), fill=WHITE, anchor='mm')
    DECL_CHIP = DECL_CHIP.rotate(8, resample=Image.BICUBIC, expand=True)
    E13.build_crowd()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 560.0, 980.0
    if name == 'kiosk':
        rng = random.Random(int(t * FPS)); sh_ = 2.0
        z, cx, cy = KZ, 560.0, 1000.0
        if t < 1.5:
            for td in (DECL1, DECL2):
                us = t - td
                if 0 <= us < 0.4: sh_ = 3 + 20 * math.exp(-us * 8)
            if t < DECL1: z = KZ + 0.18
            elif t < DECL2: z = lerp(KZ + 0.18, KZ, ease_out(clamp((t - DECL1) / 0.25)))
            else: z = lerp(KZ + 0.12, KZ, ease_out(clamp((t - DECL2) / 0.25))); cx = lerp(470, 560, ease_out(clamp((t - DECL2) / 0.4)))
        else:
            z = lerp(KZ - 0.05, KZ + 0.18, ease_in(clamp((t - LOOPIN) / (DUR - LOOPIN))))
        cx += rng.uniform(-sh_, sh_); cy += rng.uniform(-sh_, sh_)
    elif name == 'two':
        if t - a < 0.3: z = lerp(1.18, 1.0, ease_out((t - a) / 0.3))
        u = t - CSLAP
        if 0 <= u < 0.4: z = max(z, 1.0 + 0.07 * math.exp(-u * 9)); cy = 1100
        us = t - STAMP
        if 0 <= us < 0.4: z = max(z, 1.0 + 0.1 * math.exp(-us * 8)); cy = 1150
        uo = t - OFFER
        if 0 <= uo < 0.4: z = max(z, 1.0 + 0.06 * math.exp(-uo * 8))
        if a == 2.8 and t >= SH_TALK2: e = ease_out(clamp((t - SH_TALK2) / 0.12)); z, cx, cy = lerp(1.0, 1.06, e), lerp(560, 540, e), 960
        if a == 5.4 and t >= FEE: e = ease_out(clamp((t - FEE) / 0.12)); z, cx, cy = lerp(1.0, 1.14, e), lerp(560, 520, e), lerp(980, 920, e)
    elif name == 'sh':
        z = lerp(1.18, 1.0, ease_out(clamp((t - a) / 0.3))); cx, cy = 560.0, 960.0
        if a == 2.8 and t >= SH_TALK2: e = ease_out(clamp((t - SH_TALK2) / 0.12)); z, cy = lerp(1.0, 1.12, e), 900
        if a == 5.4 and t >= FEE: e = ease_out(clamp((t - FEE) / 0.12)); z, cy = lerp(1.0, 1.2, e), 880
    elif name == 'cat':
        z = lerp(1.2, 1.0, ease_out(clamp((t - a) / 0.3))); cx, cy = 600.0, 980.0
        if a == 1.5 and t >= FLAG: e = ease_out(clamp((t - FLAG) / 0.12)); z, cx, cy = lerp(1.0, 1.15, e), lerp(600, 520, e), lerp(980, 1000, e)
        if a == 6.4: e = ease_out(clamp((t - FROZE) / 0.12)); z, cx, cy = lerp(1.0, 1.2, e), lerp(600, 690, e), lerp(980, 920, e)
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'kiosk': img = scene_kiosk(t, i, back=(t >= LOOPIN))
    else: img = {'sh': scene_sh, 'two': scene_two, 'cat': scene_cat}[name](t, i)
    z, ccx, ccy = camera(t)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    for s_ in (DECL1, DECL2, FLAG, CSLAP, STAMP, FEE, FROZE):
        if s_ <= t < s_ + 0.06:
            frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    for t0, t1, lines, size, yc, fill in CAPTIONS:
        if t0 <= t < t1:
            u = t - t0; sc = 1 + 0.25 * math.exp(-u * 12) * math.cos(u * 20)
            if t0 in (0.0, LOOPIN): sc = 1.0
            cap = m.caption_layer(lines, size, fill)
            if abs(sc - 1) > 0.004:
                cap = cap.resize((max(1, int(cap.width * sc)), max(1, int(cap.height * sc))), Image.BICUBIC)
            m.paste_center(frame, cap, W / 2, yc)
    if name == 'kiosk':
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (SFX + murmur, no groove)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR); out = np.zeros(n); add = m.add
    rng = np.random.default_rng(221)
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
    def murmur(t0, t1, g):
        d_ = t1 - t0; tt = tt_(d_)
        mod = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 1.7 * tt + 1))
        env = np.minimum(1, np.minimum(tt / 0.08, (d_ - tt) / 0.08))
        add(out, m.bandpass(nz(d_), 250, 2200) * mod * env, t0, g)
    def err_beep(t0, g=0.22):
        for k_, f_ in enumerate((880.0, 440.0)):
            tt = tt_(0.16); add(out, np.sign(np.sin(2 * np.pi * f_ * tt)) * np.minimum(1, (0.16 - tt) / 0.02), t0 + 0.17 * k_, g)
    murmur(0.0, 1.5, 0.08); murmur(1.5, 2.8, 0.07); murmur(2.8, LOOPIN, 0.09); murmur(LOOPIN, DUR, 0.08)
    whoosh(0.0, 0.1, 0.3); thump(DECL1, 0.6); err_beep(DECL1, 0.2)
    whoosh(DECL2 - 0.25, 0.2, 0.15); thump(DECL2, 0.6); err_beep(DECL2, 0.22); dundun(DECL2 + 0.3, 0.3)
    for tc in (1.5, 2.8, 3.9, 5.4, 6.4, 7.8, LOOPIN): whoosh(tc - 0.08, 0.16, 0.08)
    pop(PHONE_IN + 0.1, 0.22); pop(1.62, 0.2)
    pop(FLAG, 0.26); thump(FLAG, 0.5)
    pop(SH_TALK, 0.22); pop(SH_TALK2, 0.24); thump(SH_TALK2, 0.35)
    thump(CSLAP, 0.6); add(out, m.highpass(nz(0.05), 1500) * np.exp(-tt_(0.05) * 90), CSLAP, 0.4); pop(CSLAP + 0.08)
    thump(STAMP, 0.8); add(out, m.highpass(nz(0.04), 1200) * np.exp(-tt_(0.04) * 90), STAMP, 0.5)
    for k_, f_ in enumerate((523.3, 659.3, 784.0)):   # tiny "yay" under the joy
        add(out, m.tone(f_, 0.25, harm=((1, 1), (2, 0.3)), decay=6), STAMP + 0.12 + 0.09 * k_, 0.1)
    pop(5.4, 0.2); pop(FEE, 0.26)
    for k_ in range(2):                                # cash-register "cha-ching" for the fee
        add(out, m.tone(1320 + 400 * k_, 0.3, harm=((1, 1), (2.7, 0.3)), decay=9), FEE + 0.12 + 0.1 * k_, 0.12)
    thump(FEE + 0.35, 0.5); dundun(FEE + 0.4, 0.32)
    pop(FROZE, 0.26); thump(FROZE, 0.45)
    for k_, f_ in enumerate((392.0, 311.1)):
        add(out, m.tone(f_, 0.45, harm=((1, 1), (2, 0.4)), decay=3), BLINK1[0] + 0.2 * k_, 0.14)
    pop(WALLA[0])
    for t0 in (MUNCH + 0.1, OFFER + 1.2):
        tc = t0
        while tc < t0 + 0.6:
            add(out, m.bandpass(nz(0.07), 1500, 7000) * np.exp(-tt_(0.07) * 45), tc, 0.15); tc += 0.13
    for k_, f_ in enumerate((392.0, 349.2, 329.6)):   # ending sting under "כל. פעם. מחדש."
        add(out, m.tone(f_, 0.5, harm=((1, 1), (2, 0.3)), decay=3), 8.3 + k_ * 0.18, 0.12)
    pop(OFFER, 0.24); add(out, m.highpass(nz(0.12), 2500) * np.exp(-tt_(0.12) * 20), OFFER + 0.1, 0.1)   # bag rustle
    whoosh(DUR - 0.25, 0.25, 0.3)
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
