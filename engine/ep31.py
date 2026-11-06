#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 31: כרטיס המועדון שלי עובר חברה (season 7 "הכסף בדרך" ep 2 in build order; built 6.11 under §P,
~12.3 s, silent; base = ep29.py). Idea 2026-10-31-4. Experiment share_moment_early: a recognisable "send this to…" line at
2.5–3.3 s ("2 כרטיסים. 3 הוראות קבע. חודש אחד.") over the x64 board, the break stays the last beat.
Beat sheet (§P):
  WANT (frame 0, in motion, R5/R6): move his standing orders to the new card before the old one dies. In the bright
  הבנק שלי lobby (window board "חלון 3" with a jumping red number + wall clock above him, the queue at the sides) the
  red card "עובר חברה · עד 30.11" slams onto the phone next to his sweating face. Hook F16
  "כרטיס המועדון עובר חברה? / מה עם הוראות הקבע?"  Meter: חשמל / סלולר / ארנונה.
  PLANT: the small grey 4th line "דמי כרטיס · 1 ₪ · מהכרטיס הישן" — on his phone's list in frame 0, and on the transfer
  form at window 3 (unchecked, grey) while the three rows get their ticks. Never pointed at.
  CLIMB: x64 board lands on his number → window 3, "שרית?! גם פה?", "הוראות קבע? בבקשה, מותק." → חשמל ✓ → סלולר ✓ →
  STAMP "הועבר" + ארנונה ✓ gold, the queue cheers + confetti, "עכשיו לגזור את הישן, מותק."
  PEAK: the old card in one paw, scissors open around it in the other, "3 מתוך 3", silence + heartbeat.
  BREAK (plant_payoff, last 0.5 s): SNIP — the halves fly, his phone slams in red: "חיוב נדחה · דמי כרטיס 1 ₪ ·
  הכרטיס החדש נחסם", chips reset, 0.45 s frozen face, hard cut to frame 0 (loop).

  python3 ep31.py test 0 0.5 1.5 2.6 3.4 4.3 5.0 5.9 7.0 8.0 9.0 9.6 10.4 11.2 11.6 11.9 12.2 -> out/ep31_contact.png
  python3 ep31.py render                                                                     -> out/ep31_club.mp4
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

DUR = float(os.environ.get('DUR', '12.25'))
NF = int(round(DUR * FPS))
OUTDIR = m.OUTDIR
YELLOW = (255, 221, 51); GREEN = (36, 168, 84); GOLD = (230, 170, 30)
BLUE = (28, 104, 226); RED = (214, 44, 52)
CHEESE = (246, 132, 24); CHEESE_D = (206, 92, 10)
BEAT = 60 / 80
QUEUE = int(os.environ.get('QUEUE', '466'))
EP_LABEL = 'פרק 31'
TAG_OUT = os.environ.get('OUTNAME', 'ep31_club')
BIGF = os.environ.get('BIGF', '0') == '1'
EXPR = os.environ.get('EXPR', '0') == '1'       # probe: big expressions 0.8-3.4 s (outrage, not sulk/bored)
FACES = os.environ.get('FACES', '0') == '1'
TILT = os.environ.get('TILT', '1') == '1'       # §O2: the first shot is tilted (differs from ep29's level frame 0)
FRAME0 = os.environ.get('FRAME0', '1') == '1'   # R5/R6 first shot: board + clock above him, head lower
CROWD = os.environ.get('CROWD', '0') == '1'     # probe: the board shot in a packed lobby crowd (ep13's 49)     # probe: front-row queue faces reacting in 0-4 s

SHOTS = [('cat', 0.0, 2.4), ('board', 2.4, 4.0), ('two', 4.0, 8.7), ('cat', 8.7, DUR + 1)]
SLAM = 0.08            # the "עובר חברה" card slams onto the phone
SHAKE = (0.85, 1.35)   # he flips the old card: "ישן"
BUB1 = (1.35, 2.35)    # "עד סוף החודש. חייב."
JUMPS = [(2.4, '17'), (2.62, '302'), (2.84, '8'), (3.04, '911'), (3.2, '45')]
SEND = (2.45, 3.3)     # experiment share_moment_early: the recognisable line
LAND = 3.36            # the board lands on his number
CHK1 = 5.2             # חשמל ✓
YES = (3.4, 3.95)
GAMPO = (4.05, 4.7)    # "שרית?! גם פה?"
FORMIN = 4.72          # the form slides across the counter
SH_FORM = (4.78, 5.55) # "הקדמת קצבה? בבקשה, מותק."
PRINT = 5.75           # paw slap = his signature
CHK2 = 5.85            # סלולר ✓
SH_LOOK = (6.0, 6.75)  # she looks at the orange print, shrugs, munches
STAMP = 6.9            # "הועבר"
CHK3 = 6.95            # ארנונה ✓ gold
CHEER = (6.95, 8.7)
SH_APP = (7.75, 8.65)  # "עכשיו לגזור את הישן, מותק."
PHONEUP = 8.7          # the old card + scissors come up
DIP = (9.25, 9.85)     # "ביי, כרטיס." he kisses the old card goodbye
PEAK = (10.95, 11.5)   # scissors open around the card, silence + heartbeat
SLIP = (11.52, 11.66)  # SNIP
BREAK = 11.74          # the phone slams in red
FREEZE = (BREAK + 0.05, DUR)

CAPTIONS = [  # (t0, t1, lines, size, y, fill)
    (0.0, 2.4, ['כרטיס המועדון עובר חברה?', 'מה עם הוראות הקבע?'], 74, 290, WHITE),     # keyword on frame 1 (F16)
    (7.0, 8.65, ['3 מתוך 3.', 'הכול עבר!'], 100, 290, WHITE),
    (9.9, 11.45, ['סוף סוף:', 'לגזור את הישן.'], 100, 290, WHITE),
]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def sway(t): return math.sin(2 * math.pi * t / (2 * BEAT))
burst = E18.burst; imprint = E18.imprint; confetti = E18.confetti

def paste_sh(img, st, rot, i, c, s):
    E18.paste_sh(img, st, rot, i, c, s)

# ------------------------------------------------------------------ props
def smudges(d, rects, seed=3, a=150):
    """orange cheese-dust fingerprints on glass (the plant)"""
    r = random.Random(seed)
    for (x, y, rx, ry) in rects:
        for k in range(5):
            E(d, x + r.uniform(-rx, rx) * 0.5, y + r.uniform(-ry, ry) * 0.5, rx * r.uniform(0.4, 0.8), ry * r.uniform(0.4, 0.8),
              fill=CHEESE + (int(a * r.uniform(0.45, 0.8)),))
        for k in range(4):                                     # ridges of a paw pad
            E(d, x, y - ry * 0.2 + k * ry * 0.18, rx * (0.7 - k * 0.08), ry * 0.06, fill=CHEESE_D + (int(a * 0.5),))

PW, PH = 400, 700
GREY = (128, 132, 146)
def phone_layer(kind):
    """kind 'list' = the club-card app: his standing orders (+ the grey 4th line = the plant); 'cancel' = red, declined"""
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    scr = (244, 246, 250) if kind != 'cancel' else (255, 236, 236)
    pd.rounded_rectangle([S(16), S(16), S(PW - 16), S(PH - 16)], radius=S(44), fill=scr)
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.rectangle([S(16), S(70), S(PW - 16), S(150)], fill=(120, 40, 150))                       # app bar
    pd.text((S(PW / 2), S(111)), 'כרטיס המועדון', font=font(S(38), 900), fill=WHITE, anchor='mm')
    if kind == 'list':
        pd.text((S(PW - 40), S(190)), 'הוראות קבע', font=font(S(34), 900), fill=INK, anchor='rm')
        for k, (lab, amt) in enumerate((('חשמל', '312 ₪'), ('סלולר', '49 ₪'), ('ארנונה', '540 ₪'))):
            y = 250 + k * 72
            pd.rounded_rectangle([S(34), S(y - 28), S(PW - 34), S(y + 28)], radius=S(14), fill=WHITE, outline=(214, 218, 228), width=iw(2))
            pd.text((S(PW - 52), S(y)), lab, font=font(S(32), 900), fill=INK, anchor='rm')
            pd.text((S(52), S(y)), amt, font=font(S(28), 800), fill=(90, 96, 110), anchor='lm')
        pd.text((S(PW - 46), S(488)), 'דמי כרטיס · 1 ₪ · מהכרטיס הישן', font=font(S(25), 800), fill=GREY, anchor='rm')
    else:
        E(pd, PW / 2, 215, 56, 56, fill=RED)
        line(pd, [(PW / 2 - 24, 191), (PW / 2 + 24, 239)], WHITE, 11); line(pd, [(PW / 2 + 24, 191), (PW / 2 - 24, 239)], WHITE, 11)
        pd.text((S(PW / 2), S(318)), 'חיוב נדחה', font=font(S(58), 900), fill=RED, anchor='mm')
        pd.text((S(PW / 2), S(384)), 'דמי כרטיס · 1 ₪', font=font(S(34), 900), fill=INK, anchor='mm')
        pd.rounded_rectangle([S(36), S(424), S(PW - 36), S(500)], radius=S(16), fill=RED)
        pd.text((S(PW / 2), S(462)), 'הכרטיס החדש נחסם', font=font(S(32), 900), fill=WHITE, anchor='mm')
    return lay

def sat_card():
    lay = Image.new('RGBA', (S(360), S(150)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(359), S(149)], radius=S(26), fill=RED, outline=(110, 10, 20), width=iw(4))
    d.text((S(180), S(50)), 'עובר חברה', font=font(S(54), 900), fill=WHITE, anchor='mm')
    d.text((S(180), S(110)), 'עד 30.11', font=font(S(44), 900), fill=(255, 230, 120), anchor='mm')
    return lay

def card_layer(s=1.0, old=True, half=0):
    """the club card ("הבנק שלי · מועדון"); half = 0 whole, 1/2 = left/right half after the snip"""
    w_, h_ = 340 * s, 214 * s
    lay = Image.new('RGBA', (int(S(w_)), int(S(h_))), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    col = (120, 40, 150) if old else (20, 120, 200)
    d.rounded_rectangle([0, 0, int(S(w_)) - 1, int(S(h_)) - 1], radius=S(22 * s), fill=col, outline=(30, 10, 40), width=iw(4))
    d.rounded_rectangle([S(28 * s), S(70 * s), S(86 * s), S(116 * s)], radius=S(8 * s), fill=(230, 196, 90))
    d.text((S(w_ - 24 * s), S(40 * s)), 'הבנק שלי · מועדון', font=font(S(26 * s), 900), fill=WHITE, anchor='rm')
    d.text((S(w_ / 2), S(160 * s)), '•••• 4821', font=font(S(36 * s), 900), fill=WHITE, anchor='mm')
    if old:
        d.rounded_rectangle([S(w_ - 110 * s), S(84 * s), S(w_ - 22 * s), S(126 * s)], radius=S(10 * s), fill=(255, 230, 120))
        d.text((S(w_ - 66 * s), S(106 * s)), 'ישן', font=font(S(28 * s), 900), fill=INK, anchor='mm')
    if half:
        mask = Image.new('L', lay.size, 0); md = ImageDraw.Draw(mask)
        mid = lay.width // 2
        if half == 1: md.rectangle([0, 0, mid, lay.height], fill=255)
        else: md.rectangle([mid, 0, lay.width, lay.height], fill=255)
        lay.putalpha(Image.fromarray(np.minimum(np.array(lay.split()[3]), np.array(mask))))
    return lay

def scissors(img, c, open_, ang=0.0, s=1.0):
    """two blades crossing at c, open_ 0..1; handles to the right"""
    d = ImageDraw.Draw(img)
    for sgn in (-1, 1):
        a = ang + sgn * 18 * open_
        blade = xform([(0, -10 * s), (-230 * s, -4 * s), (-250 * s, 0), (-230 * s, 6 * s), (0, 12 * s)], c[0], c[1], a)
        poly(d, blade, fill=(214, 220, 230), outline=(70, 76, 90), width=4)
        hc = xform([(110 * s, sgn * 40 * s)], c[0], c[1], a)[0]
        arm = xform([(0, 0), (90 * s, sgn * 34 * s)], c[0], c[1], a)
        line(d, arm, (226, 40, 52), int(18 * s))
        E(d, hc[0], hc[1], 44 * s, 32 * s, outline=(226, 40, 52), width=int(14 * s))
    E(d, c[0], c[1], 9 * s, 9 * s, fill=(70, 76, 90))

def bag_layer(s=1.0, empty=True):
    w_, h_ = 220 * s, 250 * s
    lay = Image.new('RGBA', (int(S(w_)), int(S(h_))), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = w_ / 2, h_ / 2 + 8 * s
    pts = [(cx - 82 * s, cy - 90 * s), (cx + 82 * s, cy - 96 * s), (cx + 70 * s, cy + 100 * s), (cx - 74 * s, cy + 96 * s)]
    poly(d, pts, fill=(244, 160, 36), outline=(120, 64, 10), width=5)
    line(d, [(cx - 60 * s, cy - 20 * s), (cx - 10 * s, cy + 10 * s), (cx + 50 * s, cy - 30 * s)], (196, 110, 20), 4)   # crumpled
    line(d, [(cx - 40 * s, cy + 50 * s), (cx + 30 * s, cy + 40 * s)], (196, 110, 20), 4)
    for (x, y) in ((-30, 70), (26, 76)):
        poly(d, epoly(cx + x * s, cy + y * s, 14 * s, 8 * s, 20), fill=(250, 214, 120), outline=(150, 96, 30), width=2)
    return lay

ROWS = [('חשמל', CHK1), ('סלולר', CHK2), ('ארנונה', CHK3)]
def form_layer():
    lay = Image.new('RGBA', (S(420), S(330)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(419), S(329)], radius=S(10), fill=(252, 252, 246), outline=(150, 150, 140), width=iw(3))
    d.rectangle([0, 0, S(419), S(58)], fill=(120, 40, 150))
    d.text((S(210), S(30)), 'העברת הוראות קבע', font=font(S(34), 900), fill=WHITE, anchor='mm')
    for k, (lab, _) in enumerate(ROWS):
        y = 100 + k * 58
        d.rectangle([S(330), S(y - 20), S(370), S(y + 20)], outline=INK, width=iw(3))
        d.text((S(316), S(y)), lab, font=font(S(32), 900), fill=INK, anchor='rm')
        d.line([S(40), S(y + 16), S(170), S(y + 16)], fill=(190, 190, 184), width=iw(3))
    d.text((S(392), S(292)), 'דמי כרטיס · הכרטיס הישן', font=font(S(28), 800), fill=GREY, anchor='rm')
    return lay

def form_ticks(img, fp, t):
    """green ticks in the form boxes (form centre fp, rotated 4°: ignore the tilt, the boxes are near the right edge)"""
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k, (lab, tc) in enumerate(ROWS):
        if t < tc: continue
        u = t - tc; sc = 1.0 + 0.6 * math.exp(-u * 12)
        bx, by = fp[0] - 210 + 350, fp[1] - 165 + 100 + k * 58 - 6
        line(od, [(bx - 18 * sc, by), (bx - 4 * sc, by + 16 * sc), (bx + 24 * sc, by - 22 * sc)], GREEN, int(9 * sc))
    img.alpha_composite(ov)

def print_layer():
    """his signature: a blue pen scribble"""
    lay = Image.new('RGBA', (S(170), S(80)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pts = [(10 + k * 6, 40 + 22 * math.sin(k * 0.9) * (1 - k / 30)) for k in range(26)]
    line(d, pts, (30, 60, 170), 5)
    return lay

def ticket_layer():
    lay = Image.new('RGBA', (S(170), S(200)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(169), S(199)], fill=(252, 250, 242), outline=(150, 150, 140), width=iw(3))
    d.text((S(85), S(48)), 'מספרך', font=font(S(32), 900), fill=(40, 40, 44), anchor='mm')
    d.text((S(85), S(128)), str(QUEUE), font=font(S(70), 900), fill=INK, anchor='mm')
    return lay

def sign_layer(s=1.0):
    """experiment cta_keyword_onscreen: Sharit's own counter sign (in-world)"""
    lay = Image.new("RGBA", (int(S(430 * s)), int(S(150 * s))), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, int(S(430 * s)) - 1, int(S(150 * s)) - 1], radius=S(14 * s), fill=(255, 236, 120), outline=(120, 90, 10), width=iw(4))
    d.text((S(215 * s), S(48 * s)), 'כתבו ״תור״ בתגובות', font=font(S(40 * s), 900), fill=INK, anchor='mm')
    d.text((S(215 * s), S(104 * s)), 'ואתן לכם מספר · שרית', font=font(S(34 * s), 800), fill=(70, 60, 30), anchor='mm')
    return lay

def chip_label(text, col):
    lay = Image.new('RGBA', (S(300), S(120)), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([0, 0, S(300) - 1, S(120) - 1], radius=S(24), fill=col, outline=(10, 40, 20), width=iw(5))
    dd.text((S(150), S(62)), text, font=font(S(72), 900), fill=WHITE, anchor='mm')
    return lay.rotate(-6, resample=Image.BICUBIC, expand=True)

def shadow_paste(img, lay, c, a=100, off=(14, 18), blur=10):
    shd = Image.new('RGBA', lay.size, (0, 0, 0, 0)); shd.paste((0, 0, 0, a), mask=lay.split()[3]); shd = shd.filter(ImageFilter.GaussianBlur(S(blur)))
    m.paste_center(img, shd, S(c[0] + off[0]), S(c[1] + off[1])); m.paste_center(img, lay, S(c[0]), S(c[1]))

def cheesy_paw(img, p, ang=0.0, s=1.0, dust=1.0):
    d = ImageDraw.Draw(img); E12.big_paw(d, p, ang, s); return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    r = random.Random(11)
    for k in range(int(14 * dust)):
        a_ = r.uniform(0, 2 * math.pi); rr = r.uniform(0, 1)
        E(od, p[0] + 60 * s * rr * math.cos(a_), p[1] + 44 * s * rr * math.sin(a_) + 14 * s, r.uniform(6, 13) * s, r.uniform(5, 10) * s,
          fill=CHEESE + (int(200 * min(1, dust)),))
    img.alpha_composite(ov)

def board(img, t):
    """the lobby display board: numbers jump (x64), then lands on his number"""
    d = ImageDraw.Draw(img)
    x0, y0 = 120, 560
    d.rounded_rectangle([S(x0), S(y0), S(x0 + 420), S(y0 + 220)], radius=S(16), fill=(24, 24, 30), outline=(90, 94, 110), width=iw(6))
    d.text((S(x0 + 210), S(y0 + 40)), 'מספר בחלון 3', font=font(S(34), 800), fill=(200, 204, 214), anchor='mm')
    num = JUMPS[0][1]
    for tj, n in JUMPS:
        if t >= tj: num = n
    if t >= LAND: num = str(QUEUE)
    col = (255, 70, 60) if t < LAND else (90, 255, 120)
    sc = 1.0 + (0.25 * math.exp(-(t - LAND) * 10) if t >= LAND else 0)
    d.text((S(x0 + 210), S(y0 + 135)), num, font=font(S(int(120 * sc)), 900), fill=col, anchor='mm')

# ------------------------------------------------------------------ meter (screen space, under the hook)
METER_Y = 470
METER = [('חשמל', CHK1), ('סלולר', CHK2), ('ארנונה', CHK3)]
def meter(frame, t):
    d = ImageDraw.Draw(frame)
    reset = t >= BREAK
    full = (t >= CHK3) and not reset
    xs = [850, 540, 230]                    # RTL: first chip on the right
    for k, (lab, tc) in enumerate(METER):
        done = (t >= tc) and not reset
        u = t - tc
        sc = 1.0 + (0.35 * math.exp(-u * 10) * math.cos(u * 20) if (0 <= u < 0.5 and not reset) else 0.0)
        if reset and t - BREAK < 0.3: sc = 1.0 + 0.2 * math.exp(-(t - BREAK) * 12)
        if full and PEAK[0] <= t < BREAK and k == 2: sc = 1.0 + 0.08 * (0.5 + 0.5 * math.cos(2 * math.pi * (t - PEAK[0]) / 0.5))
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

def cat_state_close(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < 2.4:
        u = t - SLAM
        if t < SHAKE[0]:                                   # the card slams: huge eyes, sweat (R5)
            st.update(lid=0.0, pupil='tiny' if t < SLAM + 0.35 else 'big', brow='up', mouth='w', ear_dy=-24 * math.exp(-max(0, u) * 4), look=(-20, 4), blush=0.0, sweat=1.0)
            dy = -22 * math.exp(-max(0, u) * 8) * math.cos(max(0, u) * 26); rot = 5 * math.exp(-max(0, u) * 5) * math.sin(max(0, u) * 22)
        elif t < SHAKE[1]:                                 # looks at the old card: worried
            st.update(lid=0.1, pupil='normal', brow='sad', mouth='squish', look=(18, 16), ear_droop=0.4, blush=0.0, sweat=1.0); rot = 3 * math.sin(t * 30)
            if EXPR: st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', look=(16, 18), ear_droop=0.0, ear_dy=-18); rot = 6 * math.sin(t * 30)
        else:                                              # determined
            v = t - SHAKE[1]
            st.update(lid=0.15, pupil='normal', brow='annoyed', mouth='w' if (i // 4) % 2 == 0 and v < 0.8 else 'flat', look=(-6, 0), ear_dy=-10)
            rot = -5 * math.exp(-v * 4) * math.cos(v * 14)
        return st, rot, dy
    if t < 4.0:                                            # the board
        if t < LAND:
            st.update(lid=0.3, pupil='normal', mouth='flat', look=(-26, -14), brow='sad'); dy = 4 * math.sin(t * 20)
            if EXPR: st.update(lid=0.0, pupil='big', brow='annoyed', mouth='w' if (i // 3) % 2 else 'flat', look=(-26, -14)); rot = 4 * math.sin(t * 14)
        else:
            v = t - LAND
            st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-20, -10), ear_dy=-24 * math.exp(-v * 3), blush=0.8)
            dy = -24 * abs(math.sin(v * 9)) * math.exp(-v * 2)
        return st, rot, dy
    # 8.7+: the phone, the peak, the break
    if t < DIP[0]:
        v = t - PHONEUP
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-22, 6), blush=0.7); dy = -10 * math.exp(-v * 4) * math.cos(v * 16)
    elif t < DIP[1]:                                       # kisses the old card goodbye
        st.update(lid=0.9, pupil='normal', mouth='squish', look=(-20, 8), blush=0.9); rot = -6 * math.sin(clamp((t - DIP[0]) / 0.6) * math.pi)
    elif t < PEAK[0]:
        st.update(lid=0.2, pupil='normal', brow='up', mouth='smile', look=(-22, 8), blush=0.7); rot = -3 + 2 * sway(t)
    elif t < BREAK:                                        # the held beat: eyes on the blades
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', look=(-24, 10), blush=0.4, ear_dy=-8); rot = -2
    else:                                                  # frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', look=(0, 0), blush=0.0, ear_droop=0.6 * clamp(u / 0.2), ear_dy=-20 * math.exp(-u * 6),
                  twitch=(0.25 < u < 0.6 and int(t * 12) % 2 == 0))
    return st, rot, dy

def cat_state_two(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < GAMPO[1]:                                       # double take: Sharit, here too?
        v = t - 4.0
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', look=(-22, 2), ear_dy=-20 * math.exp(-v * 3)); rot = 4 * math.exp(-v * 4) * math.sin(v * 18)
    elif t < PRINT:
        st.update(lid=0.1, pupil='normal', mouth='smile', look=(-16, 14), blush=0.4)
    elif t < STAMP:
        v = t - PRINT
        st.update(lid=0.2, pupil='normal', brow='annoyed', mouth='smile', look=(-18, 6), blush=0.5); dy = -10 * math.exp(-v * 5) * math.cos(v * 20)
    else:                                                  # approved: beaming
        v = t - STAMP
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-18, 2), blush=0.9, ear_dy=-22 * math.exp(-v * 2))
        dy = -16 * abs(math.sin(v * 9)) * math.exp(-v * 1.2)
        if t >= SH_APP[0]: st.update(look=(-22, 4), mouth='smile')
    return st, rot, dy

# ------------------------------------------------------------------ Sharit
def sh_state(t, i):
    st = SH.base(); rot = 0.0
    st.update(hand_l=(170, 760), hand_r=(530, 760))
    if t < GAMPO[1]:
        st.update(mouth='munch', lid=0.6, look=(16, 10), snack=True, hand_l=(200, 620))
    elif t < SH_FORM[1]:                                   # slides the form to him
        u = clamp((t - FORMIN) / 0.25)
        st.update(mouth='talk' if t >= SH_FORM[0] else 'lazy', lid=0.4, look=(20, 6), hand_r=lerp2((530, 760), (640, 820), ease_out(u)))
    elif t < STAMP - 0.25:                                 # looks at the orange print, shrugs, munches
        st.update(mouth='munch' if t >= SH_LOOK[0] + 0.3 else 'lazy', lid=0.3, look=(28, 26), snack=True, hand_l=(200, 620)); rot = 4 * math.sin(clamp((t - SH_LOOK[0]) / 0.4) * math.pi)
    elif t < STAMP + 0.3:                                  # the stamp
        u = clamp((t - (STAMP - 0.25)) / 0.25)
        st.update(mouth='grin', lid=0.2, look=(24, 24), hand_r=lerp2((560, 560), (620, 830), ease_in(u)))
    else:
        k = (i // 3) % 2
        st.update(mouth='talk' if SH_APP[0] <= t < SH_APP[1] else 'grin', lid=0.25, look=(18, 2),
                  hand_l=(300, 650) if k else (270, 660), hand_r=(400, 650) if k else (430, 660)); rot = -3 * math.sin(t * 9)
    return st, rot

# ------------------------------------------------------------------ scenes
HX, HY, F = 690, 900, (1.95 if BIGF else 1.8)
QUEUE_CAT = [('c0', 170, 640, 0.48, 0.0), ('h1', 960, 690, 0.42, 1.1), ('c3', 1010, 1130, 0.5, 2.0)]
QUEUE_CAT0 = [('c0', 980, 840, 0.46, 0.0), ('h1', 120, 860, 0.40, 1.1), ('c3', 1010, 1180, 0.5, 2.0)]   # R5: the queue at the sides, under the board/clock
QUEUE_PEAK = [('c0', 110, 800, 0.50, 0.0), ('h1', 1010, 900, 0.42, 1.1), ('c3', 1000, 1150, 0.55, 2.0), ('h2', 960, 680, 0.42, 0.7)]

JUMP0 = [(0.0, '17'), (0.45, '311'), (1.0, '9'), (1.6, '880')]
def waiting_kit(img, t):
    """R5: the waiting on screen in the first shot — window board with a jumping number + wall clock, sharp and bright"""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 90, 535, 560, 730
    d.rounded_rectangle([S(x0 + 8), S(y0 + 10), S(x1 + 8), S(y1 + 10)], radius=S(20), fill=(150, 158, 174))
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(20), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(6))
    d.line([(S(x1 - 120), S(y0 + 20)), (S(x1 - 120), S(y1 - 20))], fill=(60, 60, 70), width=iw(3))
    d.text((S(x1 - 60), S(y0 + 66)), 'חלון', font=font(S(36), 800), fill=E3.AMBER, anchor='mm')
    d.text((S(x1 - 60), S(y0 + 146)), '3', font=font(S(74), 900), fill=E3.AMBER, anchor='mm')
    txt = JUMP0[0][1]
    for tj, v in JUMP0:
        if t >= tj: txt = v
    blink = any(0 < t - tj < 0.21 and int((t - tj) / 0.07) % 2 == 1 for tj, _ in JUMP0[1:])
    if not blink: E3.led_text(img, txt, (x0 + x1 - 120) / 2, (y0 + y1) / 2 + 4, 120 if len(txt) < 3 else 92)
    d = ImageDraw.Draw(img)
    E3.clock_face(d, 900, 620, 88); E3.clock_hands(d, 900, 620, 88, 15 * 3600 + 58 * 60 + int(t * 40) % 60)

HY0 = 1010
def scene_cat(t, i):
    f0 = FRAME0 and t < 2.4
    img = (WIN0_BG if f0 else WIN_BG).copy()
    late = t >= PHONEUP
    qc = QUEUE_PEAK if late else (QUEUE_CAT0 if f0 else QUEUE_CAT)
    for name, x, y, sc, ph in qc:
        mood = 1 if (t < SLAM + 0.5 or (late and (t < DIP[0] or t >= BREAK))) else (0 if late else 2)
        lean = (-8 * clamp((t - PEAK[0]) / 0.4)) if late and t < BREAK else 0
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph) + lean, sc, flip=x > 540)
    if f0: waiting_kit(img, t)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_close(t, i)
    hy = HY0 if f0 else HY
    E(d, HX, 1640, 450, 470, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1700, 210, 320, fill=CREAM)
    if not late:
        # right paw: the old club card ("ישן")
        rp = (930, 1470 + 8 * math.sin(t * 2.0)); cang = 10 + 3 * math.sin(t * 4)
        if SHAKE[0] <= t < SHAKE[1]:
            u = (t - SHAKE[0]) / (SHAKE[1] - SHAKE[0]); rp = (930, 1250); cang = 10 + 340 * ease_io(u)
        capsule(d, (HX + 250, 1420), rp, 120, FUR, OUT, 4)
        shadow_paste(img, OLDC.rotate(cang, resample=Image.BICUBIC, expand=True), (rp[0] - 30, rp[1] - 120), 80, (10, 14), 8)
        E12.big_paw(ImageDraw.Draw(img), rp, -10)
    E12.paste_head(img, st, i, HX, hy + dy, F, rot)
    d = ImageDraw.Draw(img)
    if t < 2.4:                                        # phone next to his face (the list = the plant), the card slams on
        pdy = 100 if f0 else 0
        c = (250, 1060 + pdy + 6 * math.sin(t * 2.2))
        if t < SLAM: c = (250, lerp(1300 + pdy, 1060 + pdy, ease_out(clamp((t + 0.15) / 0.23))))
        capsule(d, (HX - 260, 1420), (c[0] + 10, c[1] + PH * 0.43), 120, FUR, OUT, 4)
        shadow_paste(img, PHONE_LIST.rotate(-6, resample=Image.BICUBIC, expand=True), c, 110, (18, 22), 14)
        u = t - SLAM
        sc = (1.7 - 0.7 * ease_out(clamp(u / 0.12))) if u >= 0 else 1.7
        lay = SAT.resize((max(1, int(SAT.width * sc)), max(1, int(SAT.height * sc))), Image.BICUBIC)
        shadow_paste(img, lay.rotate(-10, resample=Image.BICUBIC, expand=True), (c[0] + 40, c[1] - 330 + 4 * math.sin(t * 16) * (t < 0.6)), 90, (8, 12), 8)
        burst(img, (c[0] + 40, c[1] - 330), u, (255, 120, 120), 150, 10, 0.35)
        E12.big_paw(ImageDraw.Draw(img), (c[0] + 20, c[1] + PH * 0.47), 8)
        if BUB1[0] <= t < BUB1[1]: SH.bubble(img, 'עד סוף החודש. חייב.', t - BUB1[0], (700, 640, 520, 130), (720, 780), side=1)
    elif late:                                         # the old card + the scissors, the peak, the snip, the red phone
        v = t - PHONEUP
        cc = (330, 1150 + 5 * math.sin(t * 2.2))       # the old card, held up in the left paw
        if v < 0.2: cc = (330, lerp(1550, 1150, ease_out(v / 0.2)))
        if DIP[0] <= t < DIP[1]:                       # kiss goodbye: the card to his cheek
            e = math.sin(clamp((t - DIP[0]) / 0.6) * math.pi); cc = lerp2(cc, (470, 1050), e)
        capsule(d, (HX - 260, 1420), (cc[0] + 10, cc[1] + 110), 120, FUR, OUT, 4)
        if t < SLIP[1]:
            shadow_paste(img, OLDC_B.rotate(-6, resample=Image.BICUBIC, expand=True), cc, 100, (14, 18), 10)
        else:                                          # the halves fly apart
            u = t - SLIP[1]
            for half, dx, rr in ((OLD_H1, -1, -1), (OLD_H2, 1, 1)):
                pc = (cc[0] + dx * (40 + 500 * u), cc[1] - 220 * u + 1400 * u * u)
                shadow_paste(img, half.rotate(-6 + rr * 160 * u, resample=Image.BICUBIC, expand=True), pc, 80, (10, 14), 8)
        E12.big_paw(ImageDraw.Draw(img), (cc[0] - 10, cc[1] + 120), 10)
        # the scissors (right paw): come in, open around the card at the peak, SNIP
        if t >= DIP[1]:
            e = ease_io(clamp((t - DIP[1]) / 0.6))
            sp = lerp2((1000, 1500), (cc[0] + 260, cc[1] + 6), e)
            if t < PEAK[0]: op = 0.4 + 0.6 * e * (0.5 + 0.5 * math.sin(t * 12))
            elif t < SLIP[0]: op = 1.0
            else: op = 1.0 - clamp((t - SLIP[0]) / (SLIP[1] - SLIP[0]))
            if t >= PEAK[0] and t < SLIP[0]: sp = (sp[0] + 3 * math.sin(t * 30), sp[1])
            hp = (sp[0] + 170, sp[1] + 10)
            capsule(ImageDraw.Draw(img), (HX + 240, 1440), (hp[0] + 30, hp[1] + 40), 110, FUR, OUT, 4)
            scissors(img, sp, op, 0.0, 1.5)
            E12.big_paw(ImageDraw.Draw(img), hp, -20, 0.9)
            if t >= SLIP[1]: burst(img, (sp[0] - 260, sp[1]), t - SLIP[1], (255, 255, 255), 150, 10, 0.3)
        if DIP[0] <= t < DIP[1]: SH.bubble(img, 'ביי, כרטיס.', t - DIP[0], (720, 640, 420, 120), (720, 790), side=1)
        if t >= BREAK:                                 # the phone slams in, red
            u = t - BREAK
            c = (300, lerp(1700, 1020, ease_out(clamp(u / 0.1))))
            c = (c[0] + 10 * math.exp(-u * 10) * math.sin(u * 60), c[1])
            shadow_paste(img, PHONE_CANCEL.rotate(-4, resample=Image.BICUBIC, expand=True), c, 110, (18, 22), 14)
            burst(img, (c[0], c[1] - 60), u, (255, 90, 90), 190, 12, 0.35)
    return img

def scene_board(t, i):
    img = WIN_BG.copy()
    if CROWD:
        mood = 1 if t >= LAND else 0
        for name, x, y, sc, ph in E13.BACK + E13.MID:
            E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph) - (18 * abs(math.sin(t * 9 + ph)) if t >= LAND else 0), sc, flip=x > 540)
    for name, x, y, sc, ph in ([] if CROWD else QUEUE_CAT):
        mood = 1 if t >= LAND else 2
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    board(img, t)
    if FACES:
        for name, x, y, sc, ph in (('h2', 1000, 1250, 0.62, 0.3),):
            E13.paste_sprite(img, name, 1 if t >= LAND else 0, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=True)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_close(t, i)
    hx = 700
    E(d, hx, 1660, 440, 460, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1720, 200, 310, fill=CREAM)
    tp = (360, 1250 + 6 * math.sin(t * 3)) if t < LAND else (360, 1180 - 40 * abs(math.sin((t - LAND) * 9)) * math.exp(-(t - LAND) * 2))
    capsule(d, (hx - 250, 1420), tp, 120, FUR, OUT, 4)
    shadow_paste(img, TICKET.rotate(8, resample=Image.BICUBIC, expand=True), (tp[0], tp[1] - 120), 80, (8, 12), 6)
    cheesy_paw(img, tp, 10, 1.0, 1.0)
    E12.paste_head(img, st, i, hx, 920 + dy, 1.7, rot)
    if CROWD:
        for name, x, y, sc, ph, side in E13.FRONT:
            E13.paste_sprite(img, name, 1 if t >= LAND else 0, x - side * 40 + 6 * math.sin(t * 5 + ph), y + 10 * math.sin(t * 6 + ph), sc, flip=side > 0)
    if SEND[0] <= t < SEND[1]: SH.bubble(img, '2 כרטיסים. 3 הוראות קבע.', t - SEND[0], (650, 640, 760, 130), (720, 780), side=1)   # experiment share_moment_early
    if YES[0] <= t < YES[1]: SH.bubble(img, 'יש!', t - YES[0], (760, 640, 260, 120), (740, 780), side=1)
    burst(img, (330, 695), t - LAND, (120, 255, 160), 220, 12, 0.4)
    return img

HX2, HY2, F2 = 790, 960, 1.45
T_HEAD = (225, 900); TS = 1.45
QUEUE_TWO = [('c2', 560, 720, 0.44, 0.4), ('h0', 720, 660, 0.40, 1.6)]
def form_pos(t):
    if t < FORMIN: return None
    u = clamp((t - FORMIN) / 0.25)
    return lerp2((300, 1500), (560, 1560), ease_out(u))

def scene_two(t, i):
    img = SH_BG.copy()
    for name, x, y, sc, ph in QUEUE_TWO:
        jump = (-20 * abs(math.sin(t * 9 + ph))) if t >= CHEER[0] else 0
        mood = 1 if (t >= CHEER[0] or t < 4.3) else 0
        E13.paste_sprite(img, name, mood, x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    st_s, rot_s = sh_state(t, i)
    paste_sh(img, st_s, rot_s, i, T_HEAD, TS)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_two(t, i)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    fp = form_pos(t)
    if fp is not None:
        shadow_paste(img, FORM.rotate(4, resample=Image.BICUBIC, expand=True), fp, 70, (6, 10), 5)
        if t >= PRINT:
            u = t - PRINT; sc = 1.3 - 0.3 * ease_out(clamp(u / 0.1))
            lay = PRINTL.resize((max(1, int(PRINTL.width * sc)), max(1, int(PRINTL.height * sc))), Image.BICUBIC)
            m.paste_center(img, lay, S(fp[0] - 110), S(fp[1] + 80))
        if t >= STAMP:
            imprint(img, (fp[0] - 60, fp[1] + 10), t - STAMP, 'הועבר', 0.9, -8, col=GREEN)
        form_ticks(img, fp, t)
    # his paw: rests, then slaps the form (signature), then cheers
    rp = (HX2 + 230, 1470 + 8 * math.sin(t * 2.0))
    if PRINT - 0.3 <= t < PRINT + 0.35 and fp is not None:
        u = clamp((t - (PRINT - 0.3)) / 0.3)
        rp = lerp2((HX2 + 200, 1300), (fp[0] - 40, fp[1] + 60), ease_in(u)) if t < PRINT else lerp2((fp[0] - 40, fp[1] + 60), (HX2 + 200, 1400), ease_out(clamp((t - PRINT - 0.1) / 0.25)))
    elif t >= CHEER[0]:
        v = t - CHEER[0]; rp = (HX2 + 200, 1300 - 80 * abs(math.sin(v * 8)) * math.exp(-v * 0.8))
    capsule(ImageDraw.Draw(img), (HX2 + 220, 1520), rp, 100, FUR, OUT, 4)
    cheesy_paw(img, rp, -10, 0.85, 1.0)
    if t >= CHEER[0]: confetti(img, t - CHEER[0], 1.8)
    burst(img, (fp[0] - 40, fp[1] + 70) if fp else (0, 0), t - PRINT, (255, 170, 60), 120, 10, 0.35)
    if fp: burst(img, (fp[0] + 90, fp[1] - 10), t - STAMP, (120, 255, 160), 190, 12, 0.4)
    if GAMPO[0] <= t < GAMPO[1]: SH.bubble(img, 'שרית?! גם פה?', t - GAMPO[0], (700, 640, 520, 130), (760, 780), side=1)
    if SH_FORM[0] <= t < SH_FORM[1]: SH.bubble(img, 'הוראות קבע? בבקשה, מותק.', t - SH_FORM[0], (540, 640, 820, 130), (300, 780), side=-1)
    if SH_APP[0] <= t < SH_APP[1]: SH.bubble(img, 'עכשיו לגזור את הישן, מותק.', t - SH_APP[0], (540, 680, 820, 130), (300, 820), side=-1)
    return img

# ------------------------------------------------------------------ frame
WIN0_BG = WIN_BG = SH_BG = PHONE_LIST = PHONE_CANCEL = SAT = OLDC = OLDC_B = OLD_H1 = OLD_H2 = FORM = PRINTL = TICKET = PILL_EP = PILL_Q = None
def init_all():
    global WIN0_BG, WIN_BG, SH_BG, PHONE_LIST, PHONE_CANCEL, SAT, OLDC, OLDC_B, OLD_H1, OLD_H2, FORM, PRINTL, TICKET, PILL_EP, PILL_Q
    m.init_static()
    wb = E3.build_window_bg()
    wb0 = wb.copy(); d0 = ImageDraw.Draw(wb0)                              # R8 base: nothing behind the board + clock
    d0.rectangle([S(440), S(400), S(1080), S(560)], fill=wb0.getpixel((S(300), S(460))))
    E8.plaque(ImageDraw.Draw(wb), 820, 640, 'הבנק שלי', 300)
    WIN_BG = wb.filter(ImageFilter.GaussianBlur(S(3)))
    w0 = wb0.filter(ImageFilter.GaussianBlur(S(1.2)))                     # R6: brighter, sharper office light in the first shot
    w0.alpha_composite(Image.new('RGBA', w0.size, (255, 252, 240, 40)))
    WIN0_BG = w0
    ob = E3.build_office_bg()
    E8.plaque(ImageDraw.Draw(ob), 780, 790, 'הבנק שלי · חלון 3', 440)
    SH_BG = ob.filter(ImageFilter.GaussianBlur(S(3)))
    PHONE_LIST = phone_layer('list'); PHONE_CANCEL = phone_layer('cancel')
    SAT = sat_card(); OLDC = card_layer(0.7); OLDC_B = card_layer(1.15)
    OLD_H1 = card_layer(1.15, half=1); OLD_H2 = card_layer(1.15, half=2)
    FORM = form_layer(); PRINTL = print_layer(); TICKET = ticket_layer()
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
            if t >= SHAKE[0]: z = max(z, 1.0 + 0.06 * math.exp(-(t - SHAKE[0]) * 8))
        else:
            if t >= PEAK[0]:                                # slow push toward the phone at the peak
                e = ease_io(clamp((t - PEAK[0]) / (SLIP[0] - PEAK[0])))
                z, cx, cy = lerp(1.0, 1.12, e), lerp(600, 480, e), lerp(980, 1020, e)
            if t >= BREAK:                                  # snap onto his frozen face + the red screen
                e = ease_out(clamp((t - BREAK) / 0.12)); z, cx, cy = lerp(1.12, 1.2, e), lerp(480, 520, e), lerp(1020, 1000, e)
                us = t - BREAK
                if us < 0.35: sh_ = 3 + 18 * math.exp(-us * 9)
    elif name == 'board':
        z = lerp(1.15, 1.0, ease_out(clamp((t - a) / 0.25)))
        if t >= LAND: us = t - LAND; z = max(z, 1.0 + 0.08 * math.exp(-us * 8)); cx = 500
    elif name == 'two':
        if t - a < 0.3: z = lerp(1.18, 1.0, ease_out((t - a) / 0.3))
        if PRINT <= t < PRINT + 0.4: z = max(z, 1.0 + 0.08 * math.exp(-(t - PRINT) * 8)); cy = 1200
        if STAMP <= t < STAMP + 0.4: z = max(z, 1.0 + 0.1 * math.exp(-(t - STAMP) * 8)); cy = 1150
    cx += rng.uniform(-sh_, sh_); cy += rng.uniform(-sh_, sh_)
    return z, cx, cy

def x64_badge(frame, t):
    d = ImageDraw.Draw(frame)
    for y in range(0, H, 6): d.line([(0, y), (W, y)], fill=(0, 0, 0, 26), width=2)
    d.rounded_rectangle([930, 350, 1060, 420], radius=16, fill=(230, 40, 40), outline=(10, 10, 12), width=4)
    d.text((995, 386), 'x64', font=font(46, 900), fill=WHITE, anchor='mm', stroke_width=5, stroke_fill=(10, 10, 12))

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    img = {'two': scene_two, 'cat': scene_cat, 'board': scene_board}[name](t, i)
    z, ccx, ccy = camera(t)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if TILT and t < 2.4:                                    # §O2: Dutch-angle first shot (ep29 opened level), snaps in from 11°
        ang = 4.0 + 7.0 * math.exp(-t * 9)
        zz = 1.09
        fr = frame.resize((int(W * zz), int(H * zz)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC)
        frame = fr.crop(((fr.width - W) // 2, (fr.height - H) // 2, (fr.width - W) // 2 + W, (fr.height - H) // 2 + H))
    frame.alpha_composite(m.VIG)
    if 2.4 <= t < LAND: x64_badge(frame, t)
    if PEAK[0] <= t < SLIP[0]:                             # the held beat: a soft vignette pulse with the heartbeat
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - PEAK[0]) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(36 * k))))
    for s_ in (SLAM, LAND, PRINT, STAMP, SLIP[1], BREAK):
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
    if t < 2.4:
        frame.alpha_composite(PILL_EP, (40, 70)); frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    elif t >= FREEZE[0] and int(t * 10) % 3 != 0:           # the ticket pill flickers over the frozen face (§O3)
        frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (SFX + murmur, no groove)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR); out = np.zeros(n); add = m.add
    rng = np.random.default_rng(229)
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
    def rustle(t0, d_, g=0.12):
        add(out, m.highpass(nz(d_), 2500) * np.exp(-tt_(d_) * 6), t0, g)
    murmur(0.0, PEAK[0] - 0.15, 0.08)
    whoosh(0.0, 0.08, 0.3); thump(SLAM, 0.65); add(out, m.tone(196, 0.5, decay=4), SLAM, 0.18)     # dun
    whoosh(SHAKE[0], 0.3, 0.12); pop(SHAKE[0] + 0.4, 0.1)                                            # flips the old card
    pop(BUB1[0], 0.2)
    for tc in (2.4, 4.0, 8.7): whoosh(tc - 0.08, 0.16, 0.1)
    for k_, (tj, _) in enumerate(JUMPS):                                                             # board blips (x64)
        add(out, m.tone(880 + 60 * k_, 0.06, harm=((1, 1),), decay=20), tj, 0.07)
    pop(SEND[0], 0.18); ding(LAND, 0.24); pop(YES[0], 0.2)
    pop(GAMPO[0], 0.22); thump(GAMPO[0], 0.3)
    whoosh(FORMIN - 0.05, 0.2, 0.25); pop(SH_FORM[0] + 0.05, 0.18)
    check(CHK1, 0.12, 523.3)
    thump(PRINT, 0.45); add(out, m.bandpass(nz(0.12), 2000, 7000) * np.exp(-tt_(0.12) * 20), PRINT - 0.1, 0.12)  # pen scribble + slap
    check(CHK2, 0.13, 587.3)
    tc = SH_LOOK[0] + 0.3
    while tc < SH_LOOK[1]:
        add(out, m.bandpass(nz(0.07), 1500, 7000) * np.exp(-tt_(0.07) * 45), tc, 0.12); tc += 0.13
    thump(STAMP, 0.9); add(out, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), STAMP, 0.5); check(CHK3, 0.16, 659.3)
    applause(CHEER[0] + 0.05, CHEER[1] - 0.1, 0.07)
    for k_ in range(6): pop(CHEER[0] + 0.1 + 0.11 * k_, 0.08)
    pop(SH_APP[0], 0.2)
    whoosh(PHONEUP, 0.2, 0.2); pop(PHONEUP + 0.15, 0.15)
    pop(DIP[0] + 0.25, 0.16); pop(DIP[0] + 0.3, 0.1)                                                   # kiss
    for k_ in range(3): add(out, m.highpass(nz(0.04), 3000) * np.exp(-tt_(0.04) * 80), DIP[1] + 0.1 + 0.18 * k_, 0.08)   # scissors open/close
    for hb in (PEAK[0] + 0.02, PEAK[0] + 0.5):                                                       # heartbeat in silence
        thump(hb, 0.32); thump(hb + 0.16, 0.22)
    add(out, m.highpass(nz(0.06), 2500) * np.exp(-tt_(0.06) * 60), SLIP[0] + 0.06, 0.45)               # SNIP
    add(out, m.tone(2200, 0.08, harm=((1, 1),), decay=30), SLIP[1] - 0.02, 0.12)
    thump(BREAK, 0.95); add(out, m.tone(110, 0.6, decay=3), BREAK, 0.3)                               # the break: one buzz-thunk
    tc = BREAK
    while tc < BREAK + 0.3:
        tt = tt_(0.05); add(out, np.sign(np.sin(2 * np.pi * 180 * tt)) * np.exp(-tt * 20), tc, 0.06); tc += 0.08
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
        sheet.save(os.path.join(OUTDIR, f'ep31{tag}_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'ep31{tag}_audio.wav'); build_audio(wav); print('audio ok')
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
