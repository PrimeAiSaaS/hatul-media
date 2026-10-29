#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 22: הבנק שלי: הפרטים דלפו (season 5 "החשבון" ep 2; built 29.10 under §P, ~13 s;
experiment ending_on_sharit = the episode ends on Sharit's punch, replication of ep13's keep).
Beat sheet (§P6):
  WANT (frame 0, in motion): keep his account safe. A scam SMS "הבנק שלי: חשבונך ייחסם!" slams onto the phone held next
  to his big face in the branch lobby. Hook "הודעה מהבנק שלי? / הפעם לא עובדים עליי."  Meter of 3 chips under the hook.
  PLANT: his orange snack bag with "קוד: 4821" scribbled in marker — in his paw from frame 0, again at 4.1–5.4 and 7.6–9.2,
  and on the counter at the peak. Never pointed at.
  CLIMB: swipes the SMS away → "נמחק" ✓ (chip 1) → calls the bank himself, right at window 3: Sharit's desk phone rings in
  front of him, "הבנק שלי, שרית." ✓ (chip 2) → "מה הקוד שלך, מותק?" "קוד? לא מוסרים!" ✓ (chip 3, gold) → Sharit applauds
  "כל הכבוד, מותק!", gold sticker "לקוח זהיר", the queue cheers + confetti, "הקוד שלי? רק אני יודע."
  PEAK: he puts the bag on the counter, leans back beaming, "סוף סוף: / חשבון מוגן.", eyes closed, silence + heartbeat.
  BREAK (plant_payoff, last 1.3 s): Sharit's hand takes his bag, munching, reads "...4821. תודה, מותק." STAMP "אומת",
  the chips snap back empty, 0.45 s frozen face, hard cut to frame 0 (loop). No וואלה tail, no on-screen CTA.

  python3 ep22.py test 0 0.5 1.5 2.0 2.8 3.3 3.8 4.6 5.0 6.0 6.5 8.0 9.6 10.6 11.4 11.9 12.4 12.9 -> out/ep22_contact.png
  python3 ep22.py render                                                                        -> out/ep22_leak.mp4
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

DUR = float(os.environ.get('DUR', '13.05'))
NF = int(round(DUR * FPS))
OUTDIR = m.OUTDIR
YELLOW = (255, 221, 51); GREEN = (36, 168, 84); GOLD = (230, 170, 30)
BEAT = 60 / 80
QUEUE = int(os.environ.get('QUEUE', '477'))
EP_LABEL = 'פרק 22'
TAG_OUT = os.environ.get('OUTNAME', 'ep22_leak')
CROWDX = os.environ.get('CROWDX', '0') == '1'     # probe: bigger queue faces in the two-shots
BIGF = os.environ.get('BIGF', '0') == '1'         # probe: bigger cat head in the close-ups

SHOTS = [('cat', 0.0, 2.3), ('two', 2.3, 4.1), ('cat', 4.1, 5.4), ('two', 5.4, 7.6), ('cat', 7.6, 9.2), ('two', 9.2, DUR + 1)]
SLAM = 0.08            # scam SMS slams onto the phone
SUSP = 0.85            # squint: "רגע..."
SWIPE = 1.35           # he swipes it away -> "נמחק", chip 1
CHK1 = 1.45
BUB1 = (1.55, 2.25)    # "לא עובדים עליי."
DIAL = 2.3
RING = (2.55, 2.95)    # Sharit's desk phone rings in front of him
PICK = 2.95
CHK2 = 3.05
SH_HI = (3.05, 3.55)   # "הבנק שלי, שרית."
SH_ASK = (3.55, 4.1)   # "מה הקוד שלך, מותק?"
REFUSE = (4.3, 5.35)   # "קוד? לא מוסרים!"
CHK3 = 4.75
CLAP = 5.45
BRAVO = (5.55, 6.6)    # "כל הכבוד, מותק!"
STICK = 6.2            # gold sticker "לקוח זהיר"
CHEER = (7.6, 9.2)
BUB2 = (7.85, 9.1)     # "הקוד שלי? רק אני יודע."
BAGDOWN = 9.5
PEAK = (11.2, 11.7)    # eyes closed, silence, heartbeat
GRAB = 11.75           # Sharit's hand takes his bag
READ = (12.0, 12.6)    # "...4821. תודה, מותק."
STAMP = 12.35          # "אומת"
FREEZE = (12.6, DUR)

CAPTIONS = [  # (t0, t1, lines, size, y, fill)
    (0.0, 2.3, ['הודעה מהבנק שלי?', 'הפעם לא עובדים עליי.'], 96, 290, WHITE),      # keyword on frame 1
    (2.3, 4.1, ['הודעה חשודה? מוחקים.', 'מתקשרים לבנק בעצמך.'], 80, 290, WHITE),
    (6.0, 7.6, ['3 מתוך 3.', 'לקוח זהיר!'], 100, 290, WHITE),
    (9.35, 11.15, ['סוף סוף:', 'חשבון מוגן.'], 100, 290, WHITE),
]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def sway(t): return math.sin(2 * math.pi * t / (2 * BEAT))
burst = E18.burst; imprint = E18.imprint; paste_sh = E18.paste_sh; confetti = E18.confetti
BLUE = (28, 104, 226); RED = (214, 44, 52)

# ------------------------------------------------------------------ props
def bag_layer(s=1.0):
    """his orange snack bag with the code scribbled on it in marker (the plant)"""
    w_, h_ = 220 * s, 250 * s
    lay = Image.new('RGBA', (int(S(w_)), int(S(h_))), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = w_ / 2, h_ / 2 + 8 * s
    pts = [(cx - 82 * s, cy - 96 * s), (cx + 82 * s, cy - 96 * s), (cx + 74 * s, cy + 100 * s), (cx - 74 * s, cy + 100 * s)]
    poly(d, pts, fill=(244, 160, 36), outline=(120, 64, 10), width=5)
    zig = [(cx + x * s, cy - 96 * s - (10 * s if k % 2 else 0)) for k, x in enumerate(range(-82, 83, 14))]
    line(d, zig, (120, 64, 10), 4)
    for (x, y) in ((-40, 70), (30, 76), (-4, 84)):
        poly(d, epoly(cx + x * s, cy + y * s, 16 * s, 9 * s, 20), fill=(250, 214, 120), outline=(150, 96, 30), width=2)
    ink = (24, 30, 96)
    d.text((S(cx), S(cy - 38 * s)), 'קוד:', font=font(S(46 * s), 900), fill=ink, anchor='mm')
    d.text((S(cx), S(cy + 18 * s)), '4821', font=font(S(60 * s), 900), fill=ink, anchor='mm')
    line(d, [(cx - 60 * s, cy + 52 * s), (cx + 58 * s, cy + 48 * s)], ink, 4)        # marker underline
    return lay

PW, PH = 400, 700
def phone_layer(kind):
    """kind 'lock' = lock screen (the SMS card is pasted on top), 'call' = calling the bank, 'gone' = SMS deleted"""
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    for y in range(14, PH - 14, 6):
        v = y / PH
        pd.rectangle([S(16), S(y), S(PW - 16), S(y + 6)], fill=(int(lerp(70, 30, v)), int(lerp(60, 40, v)), int(lerp(140, 90, v))))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    if kind == 'call':
        E(pd, PW / 2, 220, 70, 70, fill=BLUE, outline=WHITE, width=4)
        pd.text((S(PW / 2), S(224)), 'ב', font=font(S(70), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(340)), 'הבנק שלי', font=font(S(48), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(392)), 'המספר הרשמי', font=font(S(30), 800), fill=(200, 210, 240), anchor='mm')
        E(pd, PW / 2, 580, 50, 50, fill=(220, 50, 50))
    else:
        pd.text((S(PW / 2), S(150)), '10:32', font=font(S(90), 900), fill=WHITE, anchor='mm')
    return lay

def sms_card():
    lay = Image.new('RGBA', (S(360), S(190)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(359), S(189)], radius=S(26), fill=(248, 248, 250), outline=(180, 180, 190), width=iw(3))
    d.rounded_rectangle([S(286), S(18), S(338), S(70)], radius=S(12), fill=BLUE)
    d.text((S(312), S(46)), 'ב', font=font(S(36), 900), fill=WHITE, anchor='mm')
    d.text((S(272), S(44)), 'הבנק שלי', font=font(S(34), 900), fill=INK, anchor='rm')
    d.text((S(340), S(108)), 'חשבונך ייחסם!', font=font(S(40), 900), fill=RED, anchor='rm')
    d.text((S(340), S(156)), 'לאימות לחצו כאן ›', font=font(S(32), 800), fill=BLUE, anchor='rm')
    return lay

def chip_label(text, col):
    lay = Image.new('RGBA', (S(300), S(120)), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([0, 0, S(300) - 1, S(120) - 1], radius=S(24), fill=col, outline=(10, 40, 20), width=iw(5))
    dd.text((S(150), S(62)), text, font=font(S(72), 900), fill=WHITE, anchor='mm')
    return lay.rotate(-6, resample=Image.BICUBIC, expand=True)

def sticker_layer():
    lay = Image.new('RGBA', (S(190), S(190)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(16):                                    # scalloped gold seal
        a = math.radians(k * 22.5); E(d, 95 + 78 * math.cos(a), 95 + 78 * math.sin(a), 18, 18, fill=GOLD, outline=(140, 96, 10), width=3)
    E(d, 95, 95, 80, 80, fill=(250, 200, 50), outline=(140, 96, 10), width=4)
    d.text((S(95), S(70)), 'לקוח', font=font(S(40), 900), fill=(90, 54, 0), anchor='mm')
    d.text((S(95), S(118)), 'זהיר', font=font(S(46), 900), fill=(90, 54, 0), anchor='mm')
    return lay

def shadow_paste(img, lay, c, a=100, off=(14, 18), blur=10):
    shd = Image.new('RGBA', lay.size, (0, 0, 0, 0)); shd.paste((0, 0, 0, a), mask=lay.split()[3]); shd = shd.filter(ImageFilter.GaussianBlur(S(blur)))
    m.paste_center(img, shd, S(c[0] + off[0]), S(c[1] + off[1])); m.paste_center(img, lay, S(c[0]), S(c[1]))

def desk_phone(d, t, picked):
    """Sharit's desk phone on the counter (left), rings at RING"""
    x0, y0 = 250, 1545
    sh_ = 6 * math.sin(t * 90) if RING[0] <= t < RING[1] else 0
    d.rounded_rectangle([S(x0 - 100 + sh_), S(y0 - 30), S(x0 + 100 + sh_), S(y0 + 40)], radius=S(16), fill=(52, 54, 62), outline=(16, 16, 20), width=iw(5))
    for k in range(6):
        d.rounded_rectangle([S(x0 - 60 + (k % 3) * 44 + sh_), S(y0 - 14 + (k // 3) * 24), S(x0 - 32 + (k % 3) * 44 + sh_), S(y0 + 2 + (k // 3) * 24)], radius=S(4), fill=(200, 204, 212))
    if not picked:
        capsule(d, (x0 - 90 + sh_, y0 - 44), (x0 + 90 + sh_, y0 - 44), 34, (40, 42, 48), (12, 12, 14), 4)

def handset(img, c, ang):
    lay = Image.new('RGBA', (S(60), S(190)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(6), S(0), S(54), S(189)], radius=S(22), fill=(40, 42, 48), outline=(12, 12, 14), width=iw(4))
    m.paste_center(img, lay.rotate(ang, resample=Image.BICUBIC, expand=True), S(c[0]), S(c[1]))

def ring_lines(img, c, t):
    if not (RING[0] <= t < RING[1]): return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    k = int((t - RING[0]) * 14) % 2
    for side in (-1, 1):
        for r in (70, 110):
            od.arc([S(c[0] - r), S(c[1] - r), S(c[0] + r), S(c[1] + r)], 200 if side < 0 else -20, 250 if side < 0 else 30, fill=(255, 236, 120, 230 if k else 120), width=iw(8))
    img.alpha_composite(ov)

# ------------------------------------------------------------------ meter (screen space, under the hook)
METER_Y = 470
METER = [('מחקתי', CHK1), ('התקשרתי', CHK2), ('סירבתי', CHK3)]
def meter(frame, t):
    d = ImageDraw.Draw(frame)
    reset = t >= STAMP
    full = (t >= CHK3) and not reset
    xs = [850, 540, 230]                    # RTL: first chip on the right
    for k, (lab, tc) in enumerate(METER):
        done = (t >= tc) and not reset
        u = t - tc
        sc = 1.0 + (0.35 * math.exp(-u * 10) * math.cos(u * 20) if (0 <= u < 0.5 and not reset) else 0.0)
        if reset and t - STAMP < 0.3: sc = 1.0 + 0.2 * math.exp(-(t - STAMP) * 12)
        w_, h_ = 290 * sc, 76 * sc
        cx = xs[k] + (random.Random(int(t * FPS) + k).uniform(-10, 10) if (reset and t - STAMP < 0.3) else 0)
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

def cat_state_close(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < 2.3:
        u = t - SLAM
        if t < SUSP:                                       # SMS slams: huge eyes
            st.update(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-24 * math.exp(-max(0, u) * 4), look=(-20, 4), blush=0.0)
            dy = -22 * math.exp(-max(0, u) * 8) * math.cos(max(0, u) * 26); rot = 5 * math.exp(-max(0, u) * 5) * math.sin(max(0, u) * 22)
        elif t < SWIPE:                                    # suspicious squint
            st.update(lid=0.5, pupil='normal', brow='annoyed', mouth='flat', look=(-22, 2), blush=0.0); rot = -4
        else:                                              # smug
            v = t - SWIPE
            st.update(lid=0.25, pupil='normal', brow='annoyed', mouth='smile', look=(-8, 6), blush=0.2); rot = 4 * math.exp(-v * 3) * math.sin(v * 12)
    elif t < 5.4:                                          # on the phone: refuses the code
        v = t - REFUSE[0]
        if v < 0: st.update(lid=0.0, pupil='big', brow='up', mouth='w', look=(-16, 0), ear_dy=-18)       # "...הקוד שלך?"
        else:
            st.update(lid=0.15, pupil='normal', brow='annoyed', mouth='w' if (i // 4) % 2 == 0 and v < 0.9 else 'flat', look=(-6, 0), ear_dy=-10)
            rot = -6 * math.exp(-v * 4) * math.cos(v * 14)
        if t >= CHK3: st.update(mouth='smile', brow='annoyed', lid=0.2)
    else:                                                  # the queue cheers: beaming
        v = t - CHEER[0]
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24 * math.exp(-v * 3), look=(-6, 2), blush=0.9)
        dy = -18 * abs(math.sin(v * 8)) * math.exp(-v * 1.2)
    return st, rot, dy

def cat_state_two(t, i):
    st = base_cat(); sw = sway(t); rot, dy = 0.0, 0.0
    if t < 4.1:                                            # dialing, then face to face on the phone
        if t < PICK: st.update(lid=0.1, pupil='normal', brow='annoyed', mouth='flat', look=(-18, 4))
        else: st.update(lid=0.0, pupil='big', brow='up', mouth='smile' if t < SH_ASK[0] else 'w', look=(-20, 4), ear_dy=-12 if t >= SH_ASK[0] else 0)
        return st, rot, dy
    if t < 7.6:                                            # applause + sticker: proud
        u = t - CLAP
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-18, 2), blush=0.8, ear_dy=-16 * math.exp(-max(0, u) * 2))
        if t >= STICK: v = t - STICK; dy = -14 * abs(math.sin(v * 10)) * math.exp(-v * 2); st['look'] = (-4, 16) if v < 0.5 else (-18, 2)
        return st, rot, dy
    # 9.2+: the peak and the break
    if t < BAGDOWN + 0.2:
        st.update(lid=0.1, pupil='normal', mouth='smile', look=(-10, 12), blush=0.6)
    elif t < PEAK[0]:                                      # leaning back, beaming, swaying
        st.update(lid=0.45, pupil='normal', mouth='smile', look=(-6, 6), blush=0.7); rot = -5 + 2 * sw; dy = 10
    elif t < GRAB + 0.15:                                  # eyes closed, bliss
        st.update(lid=1.0, mouth='smile', blush=0.8); rot = -7; dy = 12
    elif t < STAMP:                                        # eyes open: what is she doing
        st.update(lid=0.0, pupil='normal', brow='up', mouth='flat', look=(-22, 6), blush=0.2); rot = -3
    else:                                                  # frozen
        u = t - STAMP
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', look=(0, 0), blush=0.0, ear_droop=0.6 * clamp(u / 0.2), ear_dy=-20 * math.exp(-u * 6),
                  twitch=(0.25 < u < 0.6 and int(t * 12) % 2 == 0))
    return st, rot, dy

# ------------------------------------------------------------------ Sharit
def sh_state(t, i):
    st = SH.base(); rot = 0.0
    st.update(hand_l=(170, 760), hand_r=(530, 760))
    if t < PICK:                                           # munching, phone rings
        st.update(mouth='munch', lid=0.6, look=(16, 10), snack=True, hand_l=(200, 620))
        if t >= RING[0]: st.update(mouth='lazy', lid=0.4, look=(30, 20))
    elif t < 4.1:                                          # on the phone, looking right at him
        u = t - PICK
        st.update(mouth='talk', lid=0.3, look=(20, 2), snack=False, hand_r=(500, 390)); rot = -4 * math.exp(-u * 4)
    elif t < 7.6:                                          # applause
        u = t - CLAP
        if u < 0: st.update(mouth='talk', lid=0.3, look=(20, 2), hand_r=(500, 390))
        else:
            k = (i // 3) % 2
            st.update(mouth='talk' if t < BRAVO[1] else 'grin', lid=0.2, look=(18, 2),
                      hand_l=(300, 650) if k else (270, 660), hand_r=(400, 650) if k else (430, 660)); rot = -3 * math.sin(t * 9)
    else:                                                  # peak + break: no snack of her own anymore
        if t < GRAB - 0.2: st.update(mouth='lazy', lid=0.55, look=(20, 12), hand_l=(170, 760), hand_r=(530, 760))
        elif t < GRAB + 0.2:
            u = clamp((t - (GRAB - 0.2)) / 0.4)
            st.update(mouth='lazy', lid=0.4, look=(24, 24), hand_r=lerp2((530, 760), (585, 715), ease_io(u)))
        else:
            u = clamp((t - (GRAB + 0.2)) / 0.25)
            st.update(mouth='munch', lid=0.35, look=(14, 18), hand_r=lerp2((585, 715), (500, 470), ease_out(u)))
            if t >= STAMP: st.update(mouth='grin', lid=0.3, look=(20, 0))
    return st, rot

def sh_bag_pos(t):
    """where his bag is in the final two-shot (world units), or None"""
    if t < BAGDOWN - 0.25: return None
    if t < BAGDOWN: return lerp2((900, 1300), (520, 1470), ease_in(clamp((t - (BAGDOWN - 0.25)) / 0.25))), -6
    if t < GRAB + 0.2: return (520, 1470), -6
    u = clamp((t - (GRAB + 0.2)) / 0.25)
    return lerp2((520, 1470), (460, 1130), ease_out(u)), lerp(-6, 8, u)

# ------------------------------------------------------------------ scenes
HX, HY, F = 690, 900, (1.95 if BIGF else 1.8)
QUEUE_CAT = [('c0', 170, 640, 0.48, 0.0), ('h1', 960, 690, 0.42, 1.1), ('c3', 1010, 1130, 0.5, 2.0)]
QUEUE_CHEER = [('c0', 150, 760, 0.55, 0.0), ('h1', 330, 700, 0.45, 1.1), ('c3', 1000, 1180, 0.55, 2.0), ('h2', 990, 760, 0.45, 0.7)]

def crowd_mood(t):
    if t < SLAM + 0.5: return 1
    if CHK3 <= t < 9.2: return 1                 # impressed, then cheering
    return 2 if t < 2.3 else 0

def scene_cat(t, i):
    cheer = t >= CHEER[0]
    img = WIN_BG.copy()
    for name, x, y, sc, ph in (QUEUE_CHEER if cheer else QUEUE_CAT):
        jump = (-26 * abs(math.sin(t * 9 + ph))) if cheer else 0
        E13.paste_sprite(img, name, crowd_mood(t), x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 540)
    if cheer: confetti(img, t - CHEER[0], 1.8)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_close(t, i)
    E(d, HX, 1640, 450, 470, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1700, 210, 320, fill=CREAM)
    rp = (930, 1470 + 8 * math.sin(t * 2.0))           # right paw: the bag (plant)
    if cheer: v = t - CHEER[0]; rp = (930, 1400 - 70 * abs(math.sin(v * 8)) * math.exp(-v * 1.0))
    capsule(d, (HX + 250, 1420), rp, 120, FUR, OUT, 4)
    shadow_paste(img, BAG.rotate(10 + 3 * math.sin(t * 4), resample=Image.BICUBIC, expand=True), (rp[0] - 40, rp[1] - 130), 80, (10, 14), 8)
    d = ImageDraw.Draw(img); E12.big_paw(d, rp, -10)
    E12.paste_head(img, st, i, HX, HY + dy, F, rot)
    d = ImageDraw.Draw(img)
    if t < 2.3:                                        # phone held up next to his face, the SMS slams on
        c = (250, 1060 + 6 * math.sin(t * 2.2))
        if t < SLAM: c = (250, lerp(1300, 1060, ease_out(clamp((t + 0.15) / 0.23))))
        capsule(d, (HX - 260, 1420), (c[0] + 10, c[1] + PH * 0.43), 120, FUR, OUT, 4)
        shadow_paste(img, PHONE_LOCK.rotate(-6, resample=Image.BICUBIC, expand=True), c, 110, (18, 22), 14)
        u = t - SLAM
        if t < SWIPE:
            sc = 1.6 - 0.6 * ease_out(clamp(u / 0.12)) if u >= 0 else 1.6
            lay = SMS.resize((max(1, int(SMS.width * sc)), max(1, int(SMS.height * sc))), Image.BICUBIC)
            shadow_paste(img, lay.rotate(-6, resample=Image.BICUBIC, expand=True), (c[0] + 6, c[1] + 60 + 4 * math.sin(t * 16) * (t < SUSP)), 90, (8, 12), 8)
        else:                                          # swiped off to the left, "נמחק"
            v = clamp((t - SWIPE) / 0.18)
            if v < 1:
                shadow_paste(img, SMS.rotate(-6 - 30 * v, resample=Image.BICUBIC, expand=True), (c[0] + 6 - 500 * ease_in(v), c[1] + 60 - 80 * v), 90, (8, 12), 8)
            w = t - CHK1
            if w >= 0:
                sc = 1.4 - 0.4 * ease_out(clamp(w / 0.12))
                lay = DEL_CHIP.resize((max(1, int(DEL_CHIP.width * sc)), max(1, int(DEL_CHIP.height * sc))), Image.BICUBIC)
                shadow_paste(img, lay, (c[0] + 10, c[1] + 70), 100, (10, 14), 8)
        d = ImageDraw.Draw(img)
        paw = (c[0] + 20, c[1] + PH * 0.47)
        if SWIPE - 0.1 <= t < SWIPE + 0.25:            # the swipe paw
            paw = lerp2((c[0] + 120, c[1] + 80), (c[0] - 160, c[1] + 40), ease_io(clamp((t - SWIPE + 0.1) / 0.3)))
        E12.big_paw(d, paw, 8)
        burst(img, (c[0] + 6, c[1] + 60), u, (255, 120, 120), 150, 10, 0.35)
        burst(img, (c[0] + 10, c[1] + 70), t - CHK1, (120, 255, 160), 150, 10, 0.35)
        if SUSP <= t < SWIPE: SH.bubble(img, 'רגע...', t - SUSP, (720, 640, 300, 120), (720, 780), side=1)
        if BUB1[0] <= t < BUB1[1]: SH.bubble(img, 'לא עובדים עליי.', t - BUB1[0], (700, 640, 560, 130), (720, 780), side=1)
    elif t < 5.4:                                      # phone at his ear
        lay = PHONE_BACK.rotate(-14, resample=Image.BICUBIC, expand=True)
        c = (300, 930)
        capsule(d, (HX - 260, 1420), (c[0] + 20, c[1] + 140), 120, FUR, OUT, 4)
        shadow_paste(img, lay, c, 100, (14, 18), 10)
        d = ImageDraw.Draw(img); E12.big_paw(d, (c[0] + 30, c[1] + 160), 12)
        if t < REFUSE[0]: SH.bubble(img, '...הקוד שלך?', t - 4.1, (720, 640, 460, 120), (380, 780), side=-1)
        if REFUSE[0] <= t < REFUSE[1]: SH.bubble(img, 'קוד? לא מוסרים!', t - REFUSE[0], (690, 640, 600, 130), (720, 780), side=1)
    else:
        if BUB2[0] <= t < BUB2[1]: SH.bubble(img, 'הקוד שלי? רק אני יודע.', t - BUB2[0], (580, 640, 780, 130), (700, 780), side=1)
    return img

HX2, HY2, F2 = 790, 960, 1.45
T_HEAD = (225, 900); TS = 1.45
QUEUE_TWO = [('c2', 560, 700, 0.36, 0.4), ('h0', 700, 660, 0.32, 1.6)]
QUEUE_TWO_X = [('c2', 560, 720, 0.48, 0.4), ('h0', 720, 660, 0.42, 1.6)]
def scene_two(t, i):
    img = SH_BG.copy()
    for name, x, y, sc, ph in (QUEUE_TWO_X if CROWDX else QUEUE_TWO):     # faces in the queue between them
        jump = (-20 * abs(math.sin(t * 9 + ph))) if 5.6 <= t < 7.6 else 0
        mood = 1 if (5.6 <= t < 7.6 or t >= STAMP) else (2 if t < 4.1 else 0)
        E13.paste_sprite(img, name, mood, x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    st_s, rot_s = sh_state(t, i)
    paste_sh(img, st_s, rot_s, i, T_HEAD, TS)
    if PICK <= t < CLAP + 0.1:                              # handset at her ear
        handset(img, (450, 980), 18)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_two(t, i)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    if t >= STICK and t < 9.2:                              # gold sticker on his chest
        u = t - STICK; sc = 1.5 - 0.5 * ease_out(clamp(u / 0.12))
        lay = STICKER.resize((max(1, int(STICKER.width * sc)), max(1, int(STICKER.height * sc))), Image.BICUBIC)
        shadow_paste(img, lay.rotate(-8, resample=Image.BICUBIC, expand=True), (690, 1430), 80, (6, 10), 6)
    elif t >= 9.2:
        shadow_paste(img, STICKER.rotate(-8, resample=Image.BICUBIC, expand=True), (700, 1440), 80, (6, 10), 6)
    rp = (HX2 + 230, 1470 + 8 * math.sin(t * 2.0))
    if t < 4.1:                                             # his phone at his ear (calling the bank)
        rp = (HX2 + 210, 1060 if t >= DIAL + 0.15 else lerp(1470, 1060, ease_out(clamp((t - DIAL) / 0.15))))
    elif 9.2 <= t < BAGDOWN + 0.05:                         # bag in his paw, comes down onto the counter
        rp = lerp2((HX2 + 120, 1320), (620, 1540), ease_in(clamp((t - (BAGDOWN - 0.25)) / 0.25)))
    capsule(d, (HX2 + 220, 1520), rp, 100, FUR, OUT, 4)
    if t < 4.1:
        lay = PHONE_BACK.resize((int(PHONE_BACK.width * 0.8), int(PHONE_BACK.height * 0.8)), Image.BICUBIC).rotate(14, resample=Image.BICUBIC, expand=True)
        m.paste_center(img, lay, S(rp[0] - 30), S(rp[1] - 90)); d = ImageDraw.Draw(img)
    if 5.4 <= t < 9.2:                                      # bag in his other paw (mid-climb plant)
        shadow_paste(img, BAG_S.rotate(12, resample=Image.BICUBIC, expand=True), (rp[0] - 40, rp[1] - 120), 80, (8, 12), 6)
        d = ImageDraw.Draw(img)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    desk_phone(d, t, picked=PICK <= t < CLAP + 0.1)
    ring_lines(img, (250, 1480), t)
    bp = sh_bag_pos(t)
    if bp is not None:
        lay = BAG
        shadow_paste(img, lay.rotate(bp[1], resample=Image.BICUBIC, expand=True), bp[0], 80, (8, 12), 6)
        if t >= GRAB:                                       # Sharit's hand on the bag
            hp = (bp[0][0] + 10, bp[0][1] + 125) if t >= GRAB + 0.2 else lerp2((380, 1560), (530, 1590), ease_io(clamp((t - GRAB) / 0.2)))
            d = ImageDraw.Draw(img)
            E(d, hp[0], hp[1], 46, 38, fill=SH.SKIN, outline=SH.SKIN_O, width=5)
            for dx in (-26, -8, 10, 28): poly(d, epoly(hp[0] + dx, hp[1] - 34, 8, 11), fill=SH.NAIL, outline=(120, 10, 30), width=2)
    d = ImageDraw.Draw(img)
    if not (9.2 <= t < BAGDOWN + 0.05) and t >= 4.1:
        E12.big_paw(d, rp, -10, 0.85)
    elif t < 4.1:
        E12.big_paw(d, (rp[0] - 10, rp[1] + 40), -20, 0.85)
    else:
        E12.big_paw(d, rp, -10, 0.85)
    if t >= STAMP:                                          # "אומת" slammed on the counter, by his card
        imprint(img, (300, 1440), t - STAMP, 'אומת', 1.0, -8)
        burst(img, (300, 1440), t - STAMP, (255, 120, 120), 170, 12, 0.35)
    burst(img, (450, 980), t - PICK, (255, 236, 120), 110, 8, 0.3)
    burst(img, (690, 1430), t - STICK, (255, 214, 64), 120, 10, 0.4)
    if SH_HI[0] <= t < SH_HI[1]: SH.bubble(img, 'הבנק שלי, שרית.', t - SH_HI[0], (520, 640, 560, 130), (300, 780), side=-1)
    if SH_ASK[0] <= t < SH_ASK[1]: SH.bubble(img, 'מה הקוד שלך, מותק?', t - SH_ASK[0], (520, 640, 680, 130), (300, 780), side=-1)
    if BRAVO[0] <= t < BRAVO[1]: SH.bubble(img, 'כל הכבוד, מותק!', t - BRAVO[0], (520, 640, 580, 130), (300, 780), side=-1)
    if READ[0] <= t < READ[1] + 0.45: SH.bubble(img, '4821. תודה, מותק.', t - READ[0], (620, 730, 600, 130), (380, 860), side=-1)
    return img

# ------------------------------------------------------------------ frame
WIN_BG = SH_BG = PHONE_LOCK = PHONE_BACK = SMS = BAG = BAG_S = DEL_CHIP = STICKER = PILL_EP = PILL_Q = None
def init_all():
    global WIN_BG, SH_BG, PHONE_LOCK, PHONE_BACK, SMS, BAG, BAG_S, DEL_CHIP, STICKER, PILL_EP, PILL_Q
    m.init_static()
    wb = E3.build_window_bg()
    E8.plaque(ImageDraw.Draw(wb), 820, 640, 'הבנק שלי', 300)
    WIN_BG = wb.filter(ImageFilter.GaussianBlur(S(3)))
    ob = E3.build_office_bg()
    E8.plaque(ImageDraw.Draw(ob), 780, 790, 'הבנק שלי · חלון 3', 440)
    SH_BG = ob.filter(ImageFilter.GaussianBlur(S(3)))
    PHONE_LOCK = phone_layer('lock'); PHONE_BACK = E12.phone_back(0.8)
    SMS = sms_card(); BAG = bag_layer(1.0); BAG_S = bag_layer(0.8)
    DEL_CHIP = chip_label('נמחק ✓'.replace(' ✓', ''), GREEN)
    STICKER = sticker_layer()
    E13.build_crowd()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 560.0, 980.0
    rng = random.Random(int(t * FPS)); sh_ = 0.0
    if name == 'cat':
        z = lerp(1.2, 1.0, ease_out(clamp((t - a) / 0.3))); cx, cy = 600.0, 980.0
        if a == 0.0:
            z = lerp(1.16, 1.0, ease_out(clamp((t - SLAM) / 0.3))) if t >= SLAM else 1.16
            us = t - SLAM
            if 0 <= us < 0.4: sh_ = 3 + 20 * math.exp(-us * 8)
            if t >= SWIPE: z = max(z, 1.0 + 0.06 * math.exp(-(t - SWIPE) * 8))
        if a == 4.1 and t >= REFUSE[0]: e = ease_out(clamp((t - REFUSE[0]) / 0.12)); z, cx, cy = lerp(1.0, 1.14, e), lerp(600, 680, e), lerp(980, 930, e)
    elif name == 'two':
        if t - a < 0.3: z = lerp(1.18, 1.0, ease_out((t - a) / 0.3))
        if a == 2.3 and t >= SH_ASK[0]: e = ease_out(clamp((t - SH_ASK[0]) / 0.12)); z, cx, cy = lerp(1.0, 1.08, e), lerp(560, 480, e), 960
        if a == 5.4:
            us = t - STICK
            if 0 <= us < 0.4: z = max(z, 1.0 + 0.1 * math.exp(-us * 8)); cy = 1150
        if a == 9.2:
            z = lerp(1.0, 1.1, ease_io(clamp((t - 9.6) / (PEAK[1] - 9.6)))); cx = lerp(560, 600, clamp((t - 9.6) / 2))
            if t >= STAMP:                                  # snap onto his frozen face
                e = ease_out(clamp((t - STAMP) / 0.12)); z, cx, cy = lerp(1.1, 1.2, e), lerp(600, 640, e), lerp(980, 1000, e)
                us = t - STAMP
                if us < 0.35: sh_ = 3 + 18 * math.exp(-us * 9)
    cx += rng.uniform(-sh_, sh_); cy += rng.uniform(-sh_, sh_)
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    img = {'two': scene_two, 'cat': scene_cat}[name](t, i)
    z, ccx, ccy = camera(t)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if PEAK[0] <= t < GRAB:                                 # the held beat: a soft vignette pulse with the heartbeat
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - PEAK[0]) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(36 * k))))
    for s_ in (SLAM, CHK1, PICK, CHK3, STICK, STAMP):
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
    if t < GRAB:
        meter(frame, t)
    elif t >= STAMP:
        meter(frame, t)
    if t < 2.3:
        frame.alpha_composite(PILL_EP, (40, 70)); frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    elif t >= FREEZE[0] and int(t * 10) % 3 != 0:           # the ticket pill flickers over the frozen face (§O3)
        frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (SFX + murmur, no groove)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR); out = np.zeros(n); add = m.add
    rng = np.random.default_rng(222)
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
    def ding(t0, g=0.2):
        for k_, f_ in enumerate((1318.5, 1760.0)):
            add(out, m.tone(f_, 0.35, harm=((1, 1), (2, 0.2)), decay=7), t0 + 0.09 * k_, g)
    def check(t0, g=0.12, base=523.3):
        for k_, f_ in enumerate((base, base * 1.26, base * 1.5)):
            add(out, m.tone(f_, 0.22, harm=((1, 1), (2, 0.3)), decay=7), t0 + 0.07 * k_, g)
    def applause(t0, t1, g):
        tc = t0; r = random.Random(5)
        while tc < t1:
            add(out, m.bandpass(nz(0.03), 1200, 6000) * np.exp(-tt_(0.03) * 120), tc, g * r.uniform(0.5, 1.0)); tc += r.uniform(0.015, 0.045)
    murmur(0.0, PEAK[0] - 0.15, 0.08)
    whoosh(0.0, 0.08, 0.3); thump(SLAM, 0.6); ding(SLAM, 0.22)
    pop(SUSP, 0.18)
    whoosh(SWIPE - 0.05, 0.22, 0.32); thump(CHK1, 0.35); check(CHK1, 0.12)
    for tc in (2.3, 4.1, 5.4, 7.6, 9.2): whoosh(tc - 0.08, 0.16, 0.08)
    for k_ in range(3):                                   # dial tones
        add(out, m.tone(697 + 120 * k_, 0.07, harm=((1, 1), (1.7, 0.6)), decay=1), DIAL + 0.06 + 0.07 * k_, 0.08)
    tc = RING[0]
    while tc < RING[1]:                                    # desk phone ring
        tt = tt_(0.04); add(out, np.sin(2 * np.pi * 950 * tt) * np.sign(np.sin(2 * np.pi * 25 * tt)) * 0.6, tc, 0.12); tc += 0.05
    pop(PICK, 0.24); check(CHK2, 0.13, 587.3); pop(SH_HI[0] + 0.05, 0.18); pop(SH_ASK[0], 0.2); thump(SH_ASK[0], 0.3)
    pop(REFUSE[0], 0.24); thump(CHK3, 0.4); check(CHK3, 0.15, 659.3)
    applause(CLAP, 7.5, 0.05); pop(BRAVO[0], 0.2)
    thump(STICK, 0.5); check(STICK + 0.05, 0.14, 784.0)
    applause(CHEER[0], CHEER[1] - 0.1, 0.07)
    for k_ in range(6): pop(CHEER[0] + 0.05 + 0.11 * k_, 0.08)
    pop(BUB2[0], 0.2)
    thump(BAGDOWN, 0.35); add(out, m.highpass(nz(0.12), 2500) * np.exp(-tt_(0.12) * 20), BAGDOWN, 0.1)   # bag rustle
    for hb in (PEAK[0] + 0.02, PEAK[0] + 0.5):                                                          # heartbeat in silence
        thump(hb, 0.32); thump(hb + 0.16, 0.22)
    add(out, m.highpass(nz(0.12), 2500) * np.exp(-tt_(0.12) * 20), GRAB + 0.2, 0.12)                   # she takes the bag
    tc = GRAB + 0.3
    while tc < STAMP - 0.02:                                                                            # munch
        add(out, m.bandpass(nz(0.07), 1500, 7000) * np.exp(-tt_(0.07) * 45), tc, 0.15); tc += 0.13
    pop(READ[0], 0.2)
    thump(STAMP, 0.95); add(out, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), STAMP, 0.6)     # the break: one THUNK
    murmur(STAMP + 0.05, DUR, 0.03)
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
        sheet.save(os.path.join(OUTDIR, f'ep22{tag}_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'ep22{tag}_audio.wav'); build_audio(wav); print('audio ok')
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
