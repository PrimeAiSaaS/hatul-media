#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 23: הבנק שלי: קוד ה-SMS (season 5 "החשבון" ep 3; built 30.10 under §P, ~13.1 s;
experiment realtime_countdown = a clock on screen counts the real seconds to midnight through the whole episode).
Beat sheet (§P):
  WANT (frame 0, in motion): log in to הבנק שלי before the account locks at 00:00. He slides into frame at the kiosk
  (ep21's set, night), phone up next to his big face, the red LED clock on the wall at 23:59:46 and ticking in real time.
  Hook "קוד SMS מהבנק שלי? / 12 שניות לחצות." Meter = 6 empty digit boxes.
  PLANT: the small grey line under the login button "כל כניסה: 50 ₪ עמלת SMS" — on the phone in frame 0, again at
  6.2–7.4 (mid-climb close-up) and at the peak. Never pointed at.
  CLIMB: the code goes "למספר הרשום" = grandma in Eilat (split screen) → she picks up on the first ring "חמוד!" ✓ →
  reads 4… 8… 2… slowly, he types each one (3/6) ✓ → then fast "7! 1! 6!" (6/6, gold) ✓, the shoppers behind him cheer.
  PEAK: paw over "כניסה", 23:59:58, silence + heartbeat.
  BREAK (win_is_loss, last ~0.9 s): "ברוך הבא!" + confetti → the balance chip slams "יתרה: ‎-50 ₪ · עמלת קוד SMS",
  the boxes snap empty, 0.45 s frozen face, hard cut to frame 0 (he slides in again = loop). No tail, no on-screen CTA.

  python3 ep23.py test 0 0.15 0.6 1.3 2.0 2.6 3.9 5.5 6.6 7.8 8.6 9.6 11.4 12.3 12.7 13.0 -> out/ep23_contact.png
  python3 ep23.py render                                                                   -> out/ep23_sms.mp4
"""
import math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep7 as E7
import ep8 as E8
import ep10 as E10
import ep12 as E12
import ep13 as E13
import ep18 as E18
import ep21_v1 as E21
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

DUR = float(os.environ.get('DUR', '13.1'))
NF = int(round(DUR * FPS))
OUTDIR = m.OUTDIR
YELLOW = (255, 221, 51); GREEN = (36, 168, 84); GOLD = (230, 170, 30)
BLUE = (28, 104, 226); RED = (214, 44, 52)
BEAT = 60 / 80
QUEUE = int(os.environ.get('QUEUE', '476'))
EP_LABEL = 'פרק 23'
TAG_OUT = os.environ.get('OUTNAME', 'ep23_sms')
T0_CLOCK = 23 * 3600 + 59 * 60 + 46          # the wall clock at frame 0 (real time from there)
BIGP = os.environ.get('BIGP', '0') == '1'    # probe: phone bigger next to the face
BIGF = os.environ.get('BIGF', '0') == '1'    # probe: bigger cat head, already in frame at 0 (short slide)
NOSPLIT = os.environ.get('NOSPLIT', '0') == '1'   # probe: full-frame cuts between grandma and the cat instead of the split screen

SHOTS = [('cat', 0.0, 1.9), ('split', 1.9, 6.2), ('cat', 6.2, 7.4), ('split', 7.4, 9.2), ('cat', 9.2, DUR + 1)]
SLIDE = (0.0, 0.3)       # he slides into frame
SEND = 0.75              # taps "שלח קוד" -> toast "נשלח למספר הרשום"
REAL = (1.1, 1.85)       # "המספר הרשום... זה של סבתא!"
RING = (1.9, 2.25)
PICK = 2.25              # grandma picks up on the first ring -> win 1
GHI = (2.3, 2.95)        # "חמוד!"
CASK = (2.95, 3.65)      # "סבתא! הקוד! מהר!"
DIG = [3.95, 4.65, 5.35, 7.75, 8.15, 8.55]   # digits arrive (grandma reads, he types)
CODE = '482716'
SLOW_WORDS = ['ארבע...', 'שמונה...', 'שתיים...']
MID = (6.35, 7.3)        # "עוד שלוש!"
FAST = (7.6, 8.9)        # "שבע! אחת! שש!"
YES = (8.6, 9.2)         # "יש!!!"
CHEER = (9.2, 10.5)
PEAK = (11.2, 11.75)     # paw over the button, silence, heartbeat
TAP = 12.1               # "כניסה"
WELCOME = (12.1, 12.55)  # "ברוך הבא!" + confetti
BREAK = 12.55            # balance -50 ₪
FREEZE = (12.62, DUR)

CAPTIONS = [  # (t0, t1, lines, size, y, fill)
    (0.0, 1.9, ['קוד SMS מהבנק שלי?', '12 שניות לחצות.'], 96, 290, WHITE),      # keyword on frame 1
    (9.35, 11.05, ['6 מתוך 6.', 'סוף סוף: בזמן.'], 100, 290, WHITE),
]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def sway(t): return math.sin(2 * math.pi * t / (2 * BEAT))
burst = E18.burst; confetti = E18.confetti; shadow_paste = E21.shadow_paste

def n_digits(t):
    if t >= BREAK: return 0
    return sum(1 for d in DIG if t >= d)

def clock_secs(t): return T0_CLOCK + int(t)          # real time from 23:59:46
def clock_text(t):
    s = clock_secs(t) % 86400
    return f'{s // 3600:02d}:{(s // 60) % 60:02d}:{s % 60:02d}'

def amount(d, cx, cy, size, col, neg=True):
    """'-50 ₪' laid out by hand (left to right: minus, 50, shekel) so bidi never flips the minus"""
    f = font(size, 900)
    parts = (['-'] if neg else []) + ['50', ' ₪'] if neg else ['0', ' ₪']
    ws = [d.textlength(p_, font=f) for p_ in parts]
    x = cx - sum(ws) / 2
    for p_, w_ in zip(parts, ws):
        d.text((x + w_ / 2, cy), p_, font=f, fill=col, anchor='mm'); x += w_

# ------------------------------------------------------------------ props
PW, PH = 400, 700
_PH_CACHE = {}
def phone_layer(nd, state):
    """bank-app login. state: 'login' | 'sent' | 'welcome' | 'fee'"""
    key = (nd, state)
    if key in _PH_CACHE: return _PH_CACHE[key]
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(242, 244, 248))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.rectangle([S(14), S(70), S(PW - 14), S(150)], fill=BLUE)
    pd.text((S(PW / 2), S(111)), 'הבנק שלי', font=font(S(44), 900), fill=WHITE, anchor='mm')
    if state in ('welcome', 'fee'):
        pd.rectangle([S(14), S(150), S(PW - 14), S(PH - 60)], fill=(226, 246, 232))
        pd.text((S(PW / 2), S(260)), 'ברוך הבא!', font=font(S(58), 900), fill=GREEN, anchor='mm')
        pd.text((S(PW / 2), S(360)), 'יתרה:', font=font(S(36), 800), fill=(90, 96, 110), anchor='mm')
        amount(pd, S(PW / 2), S(430), S(64), RED if state == 'fee' else INK, state == 'fee')
    else:
        pd.text((S(PW / 2), S(196)), 'כניסה לחשבון', font=font(S(38), 900), fill=INK, anchor='mm')
        pd.rounded_rectangle([S(70), S(232), S(PW - 70), S(278)], radius=S(23), fill=RED)        # the stakes
        pd.text((S(PW / 2), S(256)), 'החשבון ננעל ב-00:00', font=font(S(26), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW - 36), S(316)), 'קוד SMS:', font=font(S(28), 800), fill=(90, 96, 110), anchor='rm')
        for k in range(6):                                  # digit boxes, typed right-to-left? codes read LTR
            x0 = 40 + k * 54
            done = k < nd
            pd.rounded_rectangle([S(x0), S(340), S(x0 + 46), S(404)], radius=S(10), fill=(226, 246, 232) if done else WHITE,
                                 outline=GREEN if done else (170, 176, 190), width=iw(4))
            if done: pd.text((S(x0 + 23), S(374)), CODE[k], font=font(S(40), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(440)), 'הקוד נשלח למספר הרשום ✓'.replace(' ✓', '') if state == 'sent' else 'שלח לי קוד ›',
                font=font(S(24), 800), fill=GREEN if state == 'sent' else BLUE, anchor='mm')
        pd.rounded_rectangle([S(40), S(476), S(PW - 40), S(556)], radius=S(40), fill=BLUE, outline=(10, 40, 110), width=iw(4))
        pd.text((S(PW / 2), S(517)), 'כניסה', font=font(S(46), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(586)), 'כל כניסה: 50 ₪ עמלת SMS', font=font(S(22), 700), fill=(150, 154, 164), anchor='mm')   # the plant
    _PH_CACHE[key] = lay
    return lay

def phone_state(t):
    if t >= BREAK: return 'fee'
    if t >= TAP: return 'welcome'
    return 'sent' if t >= SEND else 'login'

def fee_chip(img, c, u):
    if u < 0: return
    sc = 1.6 - 0.6 * ease_out(clamp(u / 0.12))
    lay = Image.new('RGBA', (S(470), S(170)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(470) - 1, S(170) - 1], radius=S(22), fill=RED, outline=(90, 10, 16), width=iw(5))
    amount(d, S(235), S(56), S(62), WHITE)
    d.text((S(235), S(122)), 'עמלת קוד SMS', font=font(S(44), 900), fill=(255, 236, 120), anchor='mm')
    lay = lay.rotate(-6, resample=Image.BICUBIC, expand=True)
    lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    m.paste_center(img, lay, S(c[0]), S(c[1]))

def led_clock(img, c, t, s=1.0):
    """red LED wall clock (world units) — the real seconds to midnight"""
    d = ImageDraw.Draw(img)
    s = 0.85 * s
    w_, h_ = 380 * s, 116 * s
    d.rounded_rectangle([S(c[0] - w_ / 2), S(c[1] - h_ / 2), S(c[0] + w_ / 2), S(c[1] + h_ / 2)], radius=S(14 * s),
                        fill=(26, 10, 12), outline=(70, 70, 76), width=iw(6))
    txt = clock_text(t)
    hot = clock_secs(t) % 86400 >= 23 * 3600 + 59 * 60 + 55 or clock_secs(t) % 86400 < 60
    col = (255, 60, 50) if not hot or int(t * 4) % 2 == 0 else (255, 150, 120)
    d.text((S(c[0]), S(c[1] + 4 * s)), txt, font=font(S(78 * s), 900), fill=col, anchor='mm')

def gran_phone(t):
    pw, ph = 300, 520
    lay = Image.new('RGBA', (S(pw), S(ph)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(pw) - 1, S(ph) - 1], radius=S(44), fill=(20, 20, 24))
    pd.rounded_rectangle([S(12), S(12), S(pw - 12), S(ph - 12)], radius=S(36), fill=(92, 52, 86))
    pd.text((S(pw / 2), S(80)), 'סבתא', font=font(S(30), 800), fill=(236, 220, 236), anchor='mm')
    pd.rounded_rectangle([S(20), S(140), S(pw - 20), S(280)], radius=S(18), fill=(246, 246, 250))
    pd.text((S(pw - 34), S(176)), 'הבנק שלי', font=font(S(26), 800), fill=(90, 90, 100), anchor='rm')
    pd.text((S(pw / 2), S(232)), CODE, font=font(S(54), 900), fill=(200, 40, 60), anchor='mm')
    return lay

# ------------------------------------------------------------------ meter (screen space): 6 digit boxes
def meter(frame, t, y):
    d = ImageDraw.Draw(frame)
    nd = n_digits(t)
    full = nd == 6
    reset = t >= BREAK
    bw, gap = 118, 18
    x0 = W / 2 - (6 * bw + 5 * gap) / 2
    for k in range(6):
        done = k < nd
        u = t - DIG[k]
        sc = 1.0 + (0.35 * math.exp(-u * 10) * math.cos(u * 20) if (0 <= u < 0.5 and not reset) else 0.0)
        if reset and t - BREAK < 0.3: sc = 1.0 + 0.2 * math.exp(-(t - BREAK) * 12)
        cx = x0 + k * (bw + gap) + bw / 2 + (random.Random(int(t * FPS) + k).uniform(-10, 10) if (reset and t - BREAK < 0.3) else 0)
        w_, h_ = bw * sc, 120 * sc
        fill = (GOLD if full else GREEN) if done else (250, 250, 250)
        d.rounded_rectangle([cx - w_ / 2 + 5, y - h_ / 2 + 8, cx + w_ / 2 + 5, y + h_ / 2 + 8], radius=18, fill=(0, 0, 0, 90))
        d.rounded_rectangle([cx - w_ / 2, y - h_ / 2, cx + w_ / 2, y + h_ / 2], radius=18, fill=fill, outline=INK, width=5)
        if done: d.text((cx, y + 3), CODE[k], font=font(int(84 * sc), 900), fill=WHITE, anchor='mm', stroke_width=4, stroke_fill=INK)
        else: d.text((cx, y + 3), '_', font=font(int(70 * sc), 900), fill=(190, 194, 204), anchor='mm')

# ------------------------------------------------------------------ cat states
def base_cat():
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.3); return st

def cat_state_close(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < 1.9:
        u = t - SLIDE[0]
        if t < REAL[0]:                                    # sliding in, determined
            st.update(lid=0.1, pupil='big', brow='annoyed', mouth='w', ear_dy=-22, look=(-22, 6), blush=0.0)
            rot = -10 * (1 - ease_out(clamp(t / 0.35))) + 4 * math.exp(-max(0, t - 0.3) * 5) * math.sin(max(0, t - 0.3) * 22)
        else:                                              # "...סבתא!" eyes huge
            v = t - REAL[0]
            st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', ear_dy=-26 * math.exp(-v * 3), look=(0, 0), blush=0.0)
            dy = -16 * math.exp(-v * 8) * math.cos(v * 26)
    elif t < 7.4:                                          # mid-climb: 3 down, typing hard
        v = t - 6.2
        st.update(lid=0.15, pupil='big', brow='annoyed', mouth='smile' if (i // 5) % 2 else 'w', look=(-20, 8), ear_dy=-14, blush=0.3)
        rot = 3 * math.sin(t * 10)
    else:
        if t < CHEER[1]:                                   # 6/6: beaming, the shoppers cheer
            v = t - CHEER[0]
            st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24 * math.exp(-v * 3), look=(-6, 2), blush=0.9)
            dy = -18 * abs(math.sin(v * 8)) * math.exp(-v * 1.2)
        elif t < PEAK[0]:                                  # paw rising to the button
            st.update(lid=0.2, pupil='big', brow='none', mouth='smile', look=(-22, 10), blush=0.6)
        elif t < TAP:                                      # the held beat: wide eyes, breath held
            st.update(lid=0.0, pupil='big', brow='up', mouth='flat', look=(-24, 12), blush=0.4, ear_dy=-10)
            rot = 0.6 * math.sin(t * 30)
        elif t < BREAK:                                    # "ברוך הבא!"
            v = t - TAP
            st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-28 * math.exp(-v * 4), look=(-8, 2), blush=1.0)
            dy = -20 * math.exp(-v * 6)
        else:                                              # frozen
            u = t - BREAK
            st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', look=(0, 0), blush=0.0, ear_droop=0.6 * clamp(u / 0.2),
                      ear_dy=-20 * math.exp(-u * 6), twitch=(0.2 < u < 0.55 and int(t * 12) % 2 == 0))
    return st, rot, dy

def cat_state_split(t, i):
    st = base_cat(); rot, dy = 0.0, 0.0
    if t < PICK:
        st.update(lid=0.1, pupil='big', brow='annoyed', mouth='flat', look=(-20, 6))
    elif t < CASK[1]:
        st.update(lid=0.0, pupil='big', brow='up', mouth='w' if (i // 4) % 2 == 0 else 'smile', look=(-14, -6), ear_dy=-16)
    elif t < 7.4:                                          # slow digits: leaning in, typing each
        k = sum(1 for d in DIG[:3] if t >= d)
        u = t - (DIG[k - 1] if k else 3.65)
        st.update(lid=0.25, pupil='normal', brow='annoyed', mouth='flat', look=(-22, 10), ear_dy=-8)
        if 0 <= u < 0.35 and k: st.update(mouth='smile', lid=0.0, pupil='big'); dy = -10 * math.exp(-u * 8)
    else:                                                  # fast digits: typing like crazy, then "יש!!!"
        if t < YES[0]: st.update(lid=0.0, pupil='big', brow='up', mouth='w', look=(-22, 10), ear_dy=-14); rot = 3 * math.sin(t * 24)
        else:
            v = t - YES[0]
            st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-4, -4), ear_dy=-26 * math.exp(-v * 3), blush=1.0)
            dy = -24 * abs(math.sin(v * 9)) * math.exp(-v * 2)
    return st, rot, dy

# ------------------------------------------------------------------ scenes
HX, HY, F = 690, 900, (2.05 if BIGF else 1.8)
QUEUE_BEHIND = [('c0', 150, 760, 0.55, 0.0), ('h1', 1000, 700, 0.45, 1.1), ('c3', 1010, 1150, 0.55, 2.0)]
CLOCK_C = (330, 640)

def crowd_mood(t):
    if t < 1.9: return 2
    if 6.2 <= t < 7.4: return 1
    if CHEER[0] <= t < CHEER[1] or t >= BREAK: return 1
    return 0

def phone_pos(t):
    """phone centre in the cat close-up (world units), and its scale"""
    s = 1.12 if BIGP else 1.0
    if t < 1.9:
        if t < SLIDE[1]:
            u = ease_out(clamp(t / SLIDE[1]))
            return (lerp(560, 250, u), lerp(1200, 1080, u)), s, lerp(-20, -6, u)
        return (250, 1080 + 6 * math.sin(t * 2.2)), s, -6
    if t < 7.4: return (260, 1060 + 4 * math.sin(t * 3)), s * 1.06, -4
    if t < PEAK[0]: return (250, 1070), s * 1.08, -4
    return (250, 1070), s * 1.1, -3

def scene_cat(t, i):
    img = KIOSK_BG.copy()
    led_clock(img, CLOCK_C, t)
    cheer = CHEER[0] <= t < CHEER[1]
    for name, x, y, sc, ph in QUEUE_BEHIND:
        jump = (-26 * abs(math.sin(t * 9 + ph))) if cheer else 0
        lean = 30 * math.sin(t * 2 + ph) * 0.2 if 6.2 <= t < 7.4 else 0
        E13.paste_sprite(img, name, crowd_mood(t), x + 6 * math.sin(t * 3 + ph) + lean, y + 10 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 540)
    if cheer: confetti(img, t - CHEER[0], 1.2)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_close(t, i)
    sx = 0.0
    if t < SLIDE[1]: sx = lerp(110 if BIGF else 280, 0, ease_out(clamp(t / SLIDE[1])))          # sliding in from the right
    hx = HX + sx + ((130 if BIGF else 80) if t >= 9.2 else 0)
    E(d, hx, 1640, 450, 470, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1700, 210, 320, fill=CREAM)
    if t < SLIDE[1] + 0.1:                                 # speed lines behind him
        for k in range(6):
            y = 700 + k * 150; x1 = hx + 380 + 40 * (k % 2)
            line(d, [(x1, y), (x1 + 260 * (1 - clamp(t / 0.4)), y)], (255, 255, 255), 10)
    c, ps, pang = phone_pos(t)
    c = (c[0] + sx, c[1])
    nd = n_digits(t)
    lay = phone_layer(nd if t < BREAK else 6, phone_state(t))
    if abs(ps - 1) > 1e-3: lay = lay.resize((int(lay.width * ps), int(lay.height * ps)), Image.BICUBIC)
    capsule(d, (hx - 260, 1420), (c[0] + 10, c[1] + PH * 0.43 * ps), 120, FUR, OUT, 4)
    shadow_paste(img, lay.rotate(pang, resample=Image.BICUBIC, expand=True), c, 110, (18, 22), 14)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (c[0] + 20, c[1] + PH * 0.47 * ps), 8)
    # right paw: tapping / hovering over the login button
    rp = (hx + 280, 1500 + 8 * math.sin(t * 2.0))
    btn = (c[0] + 30, c[1] + (517 - PH / 2) * ps)
    if t < 1.9 and SEND - 0.25 <= t < SEND + 0.25:
        rp = lerp2((hx + 280, 1500), (c[0] + 20, c[1] + (440 - PH / 2) * ps + 40), math.sin(math.pi * clamp((t - SEND + 0.25) / 0.5)))
    elif 6.2 <= t < 7.4:
        tap = abs(math.sin(t * 14))
        rp = lerp2((c[0] + 120, c[1] - 60), (c[0] + 60, c[1] - 30), tap)
    elif t >= 9.2:
        if t < 10.0: rp = (hx + 280, 1500 + 8 * math.sin(t * 2.0))
        elif t < PEAK[0]: rp = lerp2((hx + 280, 1500), (btn[0] + 70, btn[1] - 120), ease_io(clamp((t - 10.0) / 1.0)))
        elif t < TAP - 0.1: rp = (btn[0] + 70, btn[1] - 120 + 3 * math.sin(t * 40))
        elif t < TAP + 0.1: rp = lerp2((btn[0] + 70, btn[1] - 120), (btn[0] + 40, btn[1] - 50), ease_in(clamp((t - TAP + 0.1) / 0.2)))
        else: rp = lerp2((btn[0] + 40, btn[1] - 50), (hx + 280, 1500), ease_out(clamp((t - TAP - 0.1) / 0.2)))
    if t >= 9.2 or 6.2 <= t < 7.4 or SEND - 0.25 <= t < SEND + 0.25:
        capsule(d, (hx + 250, 1420), rp, 120, FUR, OUT, 4)
        E12.big_paw(d, rp, -30)
    E12.paste_head(img, st, i, hx, HY + dy, F, rot)
    d = ImageDraw.Draw(img)
    burst(img, (c[0], c[1] + (440 - PH / 2) * ps), t - SEND, (120, 255, 160), 120, 8, 0.3)
    burst(img, btn, t - TAP, (120, 255, 160), 170, 12, 0.35)
    if WELCOME[0] <= t: confetti(img, t - TAP, 1.0)
    burst(img, (c[0], c[1] - 40), t - BREAK, (255, 120, 120), 200, 12, 0.4)
    if t >= BREAK: fee_chip(img, (c[0] + 60, c[1] - 120 + 4 * math.sin(t * 14)), t - BREAK)
    if REAL[0] <= t < REAL[1]:
        SH.bubble(img, 'המספר הרשום... של סבתא!', t - REAL[0], (690, 1460, 760, 130), (720, 1330), side=1)
    if MID[0] <= t < MID[1]:
        SH.bubble(img, 'עוד שלוש!', t - MID[0], (720, 1520, 420, 130), (720, 1380), side=1)
    return img

def gran_state(t, i):
    st = E10.gran_base()
    st.update(hand_r=(520, 470), hand_l=(170, 760))
    if t < PICK:
        st.update(lid=0.5, mouth='lazy', look=(-10, 10), blush=0.5)
    elif t < GHI[1]:
        u = t - PICK
        st.update(lid=0.1, mouth='grin', look=(8, 0), blush=0.9, rot=-6 * math.exp(-u * 4))
    elif t < 7.4:                                          # reading slowly, squinting
        st.update(lid=0.62, mouth='talk', look=(16, 4), rot=3 * math.sin(t * 2.5), blush=0.5)
    else:                                                  # fast!
        st.update(lid=0.0, mouth='talk' if t < YES[0] else 'grin', look=(14, -2), blush=0.9, rot=-3 * math.sin(t * 12))
    return st

G_GF = 2.0
G_ORIGIN = (560 - 350 * G_GF, 830 - 300 * G_GF)
def scene_gran(t, i):
    img = GRAN_BG.copy()
    st = gran_state(t, i)
    L = E10.gran_draw(st, i)
    L = L.resize((int(L.width * G_GF), int(L.height * G_GF)), Image.BICUBIC)
    shake = 8 * math.sin(t * 90) if RING[0] <= t < RING[1] else 0
    img.alpha_composite(L, dest=(int(S(G_ORIGIN[0])), int(S(G_ORIGIN[1]))))
    hand = (G_ORIGIN[0] + 520 * G_GF + shake, G_ORIGIN[1] + 470 * G_GF)
    ph = gran_phone(t).rotate(-10 + 2 * math.sin(t * 3), resample=Image.BICUBIC, expand=True)
    m.paste_center(img, ph, S(hand[0] - 10), S(hand[1] - 210))
    d = ImageDraw.Draw(img)
    E(d, hand[0], hand[1] - 20, 64, 52, fill=SH.SKIN, outline=SH.SKIN_O, width=5)
    if RING[0] <= t < RING[1]:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        k = int((t - RING[0]) * 14) % 2
        cc = (hand[0] - 10, hand[1] - 210)
        for r in (180, 230):
            od.arc([S(cc[0] - r), S(cc[1] - r), S(cc[0] + r), S(cc[1] + r)], -40, 40, fill=(255, 236, 120, 230 if k else 120), width=iw(10))
        img.alpha_composite(ov)
    burst(img, (hand[0] - 10, hand[1] - 210), t - PICK, (255, 236, 120), 160, 10, 0.35)
    return img

def gran_talking(t):
    return (RING[0] <= t < GHI[1]) or (DIG[0] - 0.25 <= t < 5.7) or (FAST[0] <= t < YES[0])

def full_frame(t, i):
    if gran_talking(t):
        fr = scene_gran(t, i).resize((W, H), Image.LANCZOS)
        if GHI[0] <= t < GHI[1]: SH.bubble_scr(fr, 'חמוד!', t - GHI[0], (330, 330, 300, 120), (420, 470))
        if DIG[0] - 0.25 <= t < 5.7:
            k = max(0, min(2, sum(1 for d in DIG[:3] if t >= d - 0.2) - 1))
            SH.bubble_scr(fr, SLOW_WORDS[k], 0.8, (330, 330, 360, 120), (420, 470))
        if FAST[0] <= t < YES[0]: SH.bubble_scr(fr, 'שבע! אחת! שש!', t - FAST[0], (360, 330, 520, 120), (440, 470))
        return fr
    fr = scene_split_cat(t, i).resize((W, H), Image.LANCZOS)
    if CASK[0] <= t < CASK[1]: SH.bubble_scr(fr, 'סבתא! הקוד! מהר!', t - CASK[0], (600, 1560, 640, 120), (640, 1420), side=1)
    if YES[0] <= t < YES[1]: SH.bubble_scr(fr, 'יש!!!', t - YES[0], (640, 1560, 300, 120), (660, 1420), side=1)
    return fr

def split_frame(t, i):
    if NOSPLIT: return full_frame(t, i)
    g = scene_gran(t, i)
    c = scene_split_cat(t, i)
    top = g.crop((0, S(830 - 560), W * K, S(830 + 400))).resize((W, 960), Image.LANCZOS)
    bot = c.crop((0, S(900 - 520), W * K, S(900 + 440))).resize((W, 960), Image.LANCZOS)
    fr = Image.new('RGBA', (W, H)); fr.paste(top, (0, 0)); fr.paste(bot, (0, 960))
    ImageDraw.Draw(fr).rectangle([0, 954, W, 966], fill=(20, 20, 26))
    # bubbles in screen space
    if GHI[0] <= t < GHI[1]: SH.bubble_scr(fr, 'חמוד!', t - GHI[0], (300, 170, 300, 120), (380, 300))
    if CASK[0] <= t < CASK[1]: SH.bubble_scr(fr, 'סבתא! הקוד! מהר!', t - CASK[0], (560, 1240, 640, 120), (600, 1120))
    if DIG[0] - 0.2 <= t < 7.4:
        k = max(0, min(2, sum(1 for d in DIG[:3] if t >= d - 0.2) - 1))
        SH.bubble_scr(fr, SLOW_WORDS[k], 0.8, (300, 170, 360, 120), (380, 300))
    if FAST[0] <= t < FAST[1]:
        SH.bubble_scr(fr, 'שבע! אחת! שש!', t - FAST[0], (330, 170, 520, 120), (400, 300))
    if YES[0] <= t < YES[1]: SH.bubble_scr(fr, 'יש!!!', t - YES[0], (600, 1240, 300, 120), (620, 1120))
    return fr

def scene_split_cat(t, i):
    img = KIOSK_BG.copy()
    led_clock(img, CLOCK_C, t)
    for name, x, y, sc, ph in QUEUE_BEHIND:
        cheer = t >= YES[0]
        jump = (-22 * abs(math.sin(t * 9 + ph))) if cheer else 0
        E13.paste_sprite(img, name, 1 if (cheer or t >= DIG[2]) else 0, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state_split(t, i)
    E(d, HX, 1640, 450, 470, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1700, 210, 320, fill=CREAM)
    c = (300, 1080)
    lay = phone_layer(n_digits(t), 'sent')
    capsule(d, (HX - 260, 1420), (c[0] + 10, c[1] + PH * 0.43), 120, FUR, OUT, 4)
    shadow_paste(img, lay.rotate(-6, resample=Image.BICUBIC, expand=True), c, 110, (18, 22), 14)
    d = ImageDraw.Draw(img); E12.big_paw(d, (c[0] + 20, c[1] + PH * 0.47), 8)
    # typing paw: a tap at each digit
    rp = (c[0] + 150, c[1] - 30)
    for dt in DIG:
        u = t - dt + 0.12
        if 0 <= u < 0.24: rp = lerp2((c[0] + 150, c[1] - 30), (c[0] + 40, c[1] + 10), math.sin(math.pi * u / 0.24))
    if FAST[0] <= t < YES[0]: rp = lerp2((c[0] + 150, c[1] - 30), (c[0] + 40, c[1] + 10), abs(math.sin(t * 22)))
    capsule(d, (HX + 250, 1420), rp, 120, FUR, OUT, 4)
    E12.big_paw(d, rp, -30)
    E12.paste_head(img, st, i, HX, HY + dy, F, rot)
    for dt in DIG: burst(img, (c[0], c[1] + 10), t - dt, (120, 255, 160), 110, 8, 0.3)
    return img

# ------------------------------------------------------------------ frame
KIOSK_BG = GRAN_BG = PILL_EP = PILL_Q = None
def init_all():
    global KIOSK_BG, GRAN_BG, PILL_EP, PILL_Q
    m.init_static()
    kb = E21.build_kiosk_bg().filter(ImageFilter.GaussianBlur(S(3)))
    night = Image.new('RGBA', kb.size, (20, 24, 60, 70))                    # 23:59 — the kiosk at night
    kb.alpha_composite(night)
    KIOSK_BG = kb
    E12.SHARP = True
    GRAN_BG = E12.build_gran_bg()
    gn = Image.new('RGBA', GRAN_BG.size, (20, 24, 60, 50)); GRAN_BG.alpha_composite(gn)
    E13.build_crowd()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def _bubble_scr(fr, text, u, box, tip, side=-1):
    """speech bubble directly on a 1080x1920 frame (screen pixels): draw on a K-scaled layer, then downscale"""
    lay = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    SH.bubble(lay, text, u, box, tip, side)
    fr.alpha_composite(lay.resize((W, H), Image.LANCZOS))
SH.bubble_scr = _bubble_scr

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 560.0, 980.0
    rng = random.Random(int(t * FPS)); sh_ = 0.0
    if name == 'cat':
        z = lerp(1.18, 1.0, ease_out(clamp((t - a) / 0.3))); cx, cy = 600.0, 980.0
        if a == 0.0:
            z = 1.0
            us = t - SLIDE[1]
            if 0 <= us < 0.35: sh_ = 3 + 18 * math.exp(-us * 8); z = 1.0 + 0.08 * math.exp(-us * 8)
            if t >= REAL[0]: z = max(z, lerp(1.0, 1.1, ease_out(clamp((t - REAL[0]) / 0.12)))); cx, cy = 660, 900
        if a == 9.2:
            if t >= 10.0: z = lerp(1.0, 1.12, ease_io(clamp((t - 10.0) / (TAP - 10.0)))); cx = lerp(600, 520, clamp((t - 10.0) / 2)); cy = lerp(980, 1020, clamp((t - 10.0) / 2))
            if t >= BREAK:
                e = ease_out(clamp((t - BREAK) / 0.12)); z, cx, cy = lerp(1.12, 1.22, e), lerp(520, 600, e), lerp(1020, 980, e)
                us = t - BREAK
                if us < 0.35: sh_ = 3 + 18 * math.exp(-us * 9)
    elif name == 'split':
        if t - a < 0.25: z = lerp(1.1, 1.0, ease_out((t - a) / 0.25))
    cx += rng.uniform(-sh_, sh_); cy += rng.uniform(-sh_, sh_)
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'split':
        frame = split_frame(t, i)
        z, ccx, ccy = camera(t)
        if z > 1.0005:
            cw, ch = W / z, H / z
            frame = frame.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.LANCZOS)
    else:
        img = scene_cat(t, i)
        z, ccx, ccy = camera(t)
        if z > 1.0005:
            cw, ch = W * K / z, H * K / z
            left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
            img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
        frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if PEAK[0] <= t < TAP:                                  # the held beat: vignette pulse with the heartbeat
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - PEAK[0]) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(40 * k))))
    for s_ in [SLIDE[1], PICK, DIG[2], DIG[5], TAP, BREAK]:
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
    if name == 'split': meter(frame, t, (1560 if gran_talking(t) else 470) if NOSPLIT else 960)
    elif not (WELCOME[0] <= t < BREAK): meter(frame, t, 470)
    if t < 1.9:
        frame.alpha_composite(PILL_EP, (40, 70)); frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    elif t >= FREEZE[0] and int(t * 10) % 3 != 0:           # the ticket pill flickers over the frozen face (§O3)
        frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (SFX + kiosk murmur, no groove)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR); out = np.zeros(n); add = m.add
    rng = np.random.default_rng(23)
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
    def tick(t0, g=0.06):
        add(out, m.highpass(nz(0.02), 3000) * np.exp(-tt_(0.02) * 200), t0, g)
    def key(t0, g=0.14):
        add(out, m.bandpass(nz(0.03), 2000, 7000) * np.exp(-tt_(0.03) * 150), t0, g)
    def applause(t0, t1, g):
        tc = t0; r = random.Random(5)
        while tc < t1:
            add(out, m.bandpass(nz(0.03), 1200, 6000) * np.exp(-tt_(0.03) * 120), tc, g * r.uniform(0.5, 1.0)); tc += r.uniform(0.015, 0.045)
    murmur(0.0, PEAK[0] - 0.15, 0.07)
    for s in range(int(DUR) + 1):                          # the clock: one tick per real second
        if s < PEAK[0] or s >= TAP: tick(float(s), 0.07 if s < 11 else 0.12)
    whoosh(0.0, 0.3, 0.4); thump(SLIDE[1], 0.65)           # the slide-in + landing hit
    pop(SEND, 0.2); add(out, m.tone(1568, 0.18, harm=((1, 1),), decay=9), SEND + 0.05, 0.12)
    pop(REAL[0], 0.24); thump(REAL[0], 0.3)
    for tc in (1.9, 6.2, 7.4, 9.2): whoosh(tc - 0.08, 0.16, 0.08)
    tc = RING[0]
    while tc < RING[1]:                                    # grandma's phone rings
        tt = tt_(0.04); add(out, np.sin(2 * np.pi * 950 * tt) * np.sign(np.sin(2 * np.pi * 25 * tt)) * 0.6, tc, 0.12); tc += 0.05
    pop(PICK, 0.24); check(PICK + 0.02, 0.12, 523.3)
    pop(GHI[0], 0.18); pop(CASK[0], 0.2)
    for k_, dt in enumerate(DIG):
        key(dt - 0.02); check(dt, 0.09 + 0.012 * k_, 523.3 * (2 ** (k_ / 12 * 2)))
    thump(DIG[2], 0.3); pop(MID[0], 0.2); pop(FAST[0], 0.2)
    thump(DIG[5], 0.45)
    applause(YES[0], CHEER[1] - 0.1, 0.07)
    for k_ in range(5): pop(CHEER[0] + 0.05 + 0.11 * k_, 0.08)
    for hb in (PEAK[0] + 0.02, PEAK[0] + 0.5):             # heartbeat in silence
        thump(hb, 0.32); thump(hb + 0.16, 0.22)
    key(TAP, 0.2); check(TAP + 0.02, 0.15, 784.0)
    for k_ in range(4): pop(TAP + 0.05 + 0.08 * k_, 0.08)
    thump(BREAK, 0.95); add(out, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), BREAK, 0.6)   # the break: one THUNK
    add(out, m.tone(220, 0.5, harm=((1, 1), (2, 0.4)), decay=3), BREAK + 0.02, 0.12)                   # low buzz "-50"
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
        sheet.save(os.path.join(OUTDIR, f'ep23{tag}_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'ep23{tag}_audio.wav'); build_audio(wav); print('audio ok')
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
