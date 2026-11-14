#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 34: הפטור של 75 דולר (season 8 "בלאק פריידיי" ep1, VOICED, built 14.11 under §P, ~20 s).
Voices = voice bank 2026-11-13 lines 3400–3404 (Benji = cat) + stock 9103 "יש!!!" and 9104 "רגע... מה?!" (the break
reaction), prepared by voice/ep34_prep.py. No Sharit in this one (bible).
Set: the stairwell outside his door (floor 2) — an everyday place, not an office (lessons/20261113-experiments-keep).
Want: order the Black Friday snack mega-box from abroad under the $75 VAT exemption.
Plant: the small grey line in the cart "משלוח: $3.00 · יחושב בתשלום" — in the cold open, in the want close-up and again at
the coupon. Never pointed at.
Climb (meter = the price ticking DOWN toward the exemption line + 3 chips): $89 "מעל הפטור" → coupon BLACK15 ✓ $75.65 →
removes one bag ✓ $74.99 → "פטור ✓" gold, "יש!!!", he dances.
Peak: "סוף סוף... פטור." — paw over "לתשלום", eyes closed, hush + heartbeat.
Break (plant_payoff): tap → the total counts UP $74.99 → $77.99 (+$3.00 shipping), "חייב במע״מ", red stamp "מכס",
chips drain, "רגע... מה?!", frozen face, whip into the cold open (loop).
No music (voiced rule): voices + SFX + stairwell room tone. Serial pills "פרק 34" + live ticket number (hud.stage_of, §O4).

  python3 voice/ep34_prep.py
  python3 ep34.py times | test t1 t2 ... | render   -> out/ep34_ptor.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep12 as E12
import ep15 as E15
import ep18 as E18
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep34', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 104, 226)
ORANGE = (255, 120, 30); BF = (18, 18, 22)
QUEUE = int(os.environ.get('QUEUE', '456'))
EP_LABEL = 'פרק 34'
OUTNAME = os.environ.get('OUTNAME', 'ep34_ptor')
LIMIT = float(os.environ.get('LIMIT', '0'))
SPEAKER = {k: 'cat' for k in META}

def segments(i, gap_frames=4, thr=0.08):
    env = META[i]['env']; segs = []; start = None; quiet = 0
    for k, v in enumerate(env):
        if v >= thr:
            if start is None: start = k
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet >= gap_frames: segs.append((start / FPS, (k - quiet + 1) / FPS)); start = None; quiet = 0
    if start is not None: segs.append((start / FPS, len(env) / FPS))
    return [s_ for s_ in segs if s_[1] - s_[0] >= 0.10]
SEG = {i: segments(i) for i in META}
def ss(i, k):
    s = SEG[i]
    return s[k][0] if k < len(s) else D[i] * (k / max(1, len(s)))

# ------------------------------------------------------------------ timeline (from the real line lengths)
COLD_END = round(D[0] + 0.12, 2)            # cold open = 3400 "שבעים וארבע תשעים ותשע! פטור!" (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "בלאק פריידיי. מארז חטיפים מחו״ל. בלי מע״מ."
OVER = L[1] + D[1] + 0.05                   # the cart: $89 — red "מעל הפטור" buzz
L[2] = OVER + 0.85                          # "שמונים ותשע... קופון!"
TYPE = L[2] + ss(2, 2) + 0.05               # BLACK15 typed on "קופון!"
CHK1 = TYPE + 0.80                          # $75.65 ✓ קופון
L[3] = CHK1 + 0.45                          # "מוריד שקית אחת. שבעים וארבע תשעים ותשע."
BAGOUT = L[3] + ss(3, 0) + 0.45             # a bag flies out of the box
CHK2 = L[3] + ss(3, 1)                      # $74.99 ✓ שקית
CHK3 = L[3] + D[3] + 0.15                   # "פטור ✓" gold
L[103] = CHK3 + 0.08                        # "יש!!!"
DANCE = (L[103], L[103] + D[103] + 0.95)
L[4] = DANCE[1] + 0.15                      # "סוף סוף... פטור." (peak line)
HOLD = (L[4] + D[4] + 0.03, L[4] + D[4] + 0.63)
TAP = HOLD[1]                               # the paw comes down on "לתשלום"
BREAK = TAP + 0.12                          # total counts up: $77.99
STAMP = BREAK + 0.75                        # "מכס"
L[104] = STAMP + 0.30                       # "רגע... מה?!"
FREEZE = L[104] + D[104]
DUR = round(FREEZE + 0.45, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0)] + [(i, L[i]) for i in (1, 2, 3, 103, 4, 104)]

SUBS = {
    0: [['שבעים וארבע תשעים ותשע!'], ['פטור!']],
    1: [['בלאק פריידיי.'], ['מארז חטיפים מחו״ל.'], ['בלי מע״מ.']],
    2: [['שמונים ותשע...'], ['קופון!']],
    3: [['מוריד שקית אחת.'], ['שבעים וארבע תשעים ותשע.']],
    103: [['יש!!!']],
    4: [['סוף סוף...'], ['פטור.']],
    104: [['רגע... מה?!']],
}
SPLIT = {0: [0, 1], 1: [0, 1, 2], 2: [0, 2], 3: [0, 1], 4: [0, 1], 104: [0]}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]; ks = SPLIT.get(li, [0])
    starts = [0.0] + [ss(li, ks[k]) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 104 and k == len(ch) - 1: b = DUR - 0.25
        SUB_TIMES.append((a, b, c, li))

C = lambda t: t - 0.08
WANTWIDE = os.environ.get('WANTWIDE', '0') == '1'   # 6א probe 14.11 → 45 (v1 46): the want + the $89 beat in the wide stairwell shot (frame 0 scored highest)
SHOTS = [('stair', 0.0, COLD_END), ('rewind', COLD_END, T0)] + ([('stair', T0, C(L[2])), ('close', C(L[2]), C(L[3]))] if WANTWIDE else [('close', T0, C(L[3]))]) + [ ('stair', C(L[3]), C(L[4])),
         ('close', C(L[4]), FREEZE - 0.02), ('frozen', FREEZE - 0.02, DUR + 1)]
TOPCAPS = [(0.0, COLD_END, ['פטור עד 75 דולר?']), (T0, OVER + 0.3, ['פטור עד 75 דולר?'])]   # hook F1/F16, keyword פטור / 75 דולר

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def speaking(t):
    for li, s0 in OCC:
        if s0 <= t < s0 + D[li]: return li, s0
    return None

def cat_v(t):
    sp = speaking(t)
    if not sp: return 0.0
    li, s0 = sp; env = META[li]['env']; k = int((t - s0) * FPS)
    return env[k] if k < len(env) else 0.0

def cat_mouth(t, rest='w', loud='smile'):
    v = cat_v(t)
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

# ------------------------------------------------------------------ price + cart
def price_at(t):
    """the cart total the phone shows (the meter): 89 → 75.65 → 74.99, then the break 77.99"""
    if t < COLD_END: return 74.99
    if t < TYPE: return 89.00
    if t < CHK1: return lerp(89.00, 75.65, ease_out(clamp((t - TYPE) / 0.65)))
    if t < CHK2: return 75.65
    if t < BREAK: return 74.99
    return lerp(74.99, 77.99, ease_out(clamp((t - BREAK) / 0.55)))

def bags_at(t):
    return 11 if (t < COLD_END or t >= BAGOUT) else 12

def cart_state(t):
    if t < COLD_END: return 'free'
    if t < TYPE: return 'over'
    if t < CHK2: return 'coupon'
    if t < BREAK: return 'free'
    return 'total'

PW, PH = 400, 720
def phone_layer(state, price, bags):
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.rectangle([S(14), S(66), S(PW - 14), S(132)], fill=BF)
    pd.text((S(PW / 2), S(99)), 'בלאק פריידיי', font=font(S(40), 900), fill=ORANGE, anchor='mm')
    if state == 'total':
        pd.text((S(PW / 2), S(186)), 'סה״כ לתשלום', font=font(S(36), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(270)), f'${price:.2f}', font=font(S(92), 900), fill=RED, anchor='mm')
        pd.text((S(PW / 2), S(350)), 'מוצרים $74.99', font=font(S(30), 800), fill=(90, 96, 110), anchor='mm')
        pd.text((S(PW / 2), S(392)), '+ משלוח $3.00', font=font(S(34), 900), fill=RED, anchor='mm')
        pd.rounded_rectangle([S(40), S(440), S(PW - 40), S(530)], radius=S(45), fill=RED, outline=(90, 10, 14), width=iw(5))
        pd.text((S(PW / 2), S(485)), 'חייב במע״מ', font=font(S(44), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(600)), 'מעל $75', font=font(S(40), 900), fill=RED, anchor='mm')
        return lay
    # the box: a stack of snack bags (bags = how many)
    cols = [(244, 160, 36), (226, 60, 60), (60, 150, 220), (90, 190, 90), (240, 210, 60), (170, 90, 200)]
    pd.rounded_rectangle([S(40), S(150), S(PW - 40), S(300)], radius=S(18), fill=(255, 240, 220), outline=(200, 160, 120), width=iw(3))
    for k in range(bags):
        x = 70 + (k % 6) * 46; y = 190 + (k // 6) * 58
        pts = [(x - 18, y - 24), (x + 18, y - 24), (x + 16, y + 24), (x - 16, y + 24)]
        poly(pd, pts, fill=cols[k % 6], outline=tuple(max(0, c - 90) for c in cols[k % 6]), width=2)
    pd.text((S(PW / 2), S(330)), f'מארז חטיפים ענק ×{bags}', font=font(S(30), 900), fill=INK, anchor='mm')
    if state == 'coupon':
        pd.rounded_rectangle([S(40), S(352), S(PW - 40), S(400)], radius=S(12), fill=(230, 246, 232), outline=GREEN, width=iw(3))
        pd.text((S(PW / 2 + 20), S(376)), 'BLACK15', font=font(S(30), 900), fill=GREEN, anchor='mm')
        E(pd, 80, 376, 16, 16, fill=GREEN)
        line(pd, [(72, 376), (78, 383), (89, 369)], WHITE, 5)
        pd.text((S(PW - 60), S(430)), '$89.00', font=font(S(30), 800), fill=(150, 150, 160), anchor='rm')
        line(pd, [(PW - 160, 430), (PW - 56, 430)], (150, 150, 160), 3)
    py = 470 if state == 'coupon' else 420
    over = price > 75.0
    pd.text((S(PW / 2), S(py)), f'${price:.2f}', font=font(S(80), 900), fill=RED if over else GREEN, anchor='mm')
    chip_y = py + 64
    if over:
        pd.rounded_rectangle([S(70), S(chip_y - 24), S(PW - 70), S(chip_y + 24)], radius=S(24), fill=RED)
        pd.text((S(PW / 2), S(chip_y)), 'מעל הפטור', font=font(S(30), 900), fill=WHITE, anchor='mm')
    else:
        pd.rounded_rectangle([S(70), S(chip_y - 24), S(PW - 70), S(chip_y + 24)], radius=S(24), fill=GREEN)
        pd.text((S(PW / 2), S(chip_y)), 'פטור ✓'.replace(' ✓', ''), font=font(S(32), 900), fill=WHITE, anchor='mm')
    if state != 'coupon':
        pd.text((S(PW / 2), S(560)), '* משלוח: $3.00 · יחושב בתשלום', font=font(S(22), 800), fill=(150, 152, 162), anchor='mm')   # the plant
    pd.rounded_rectangle([S(50), S(600), S(PW - 50), S(670)], radius=S(35), fill=BLUE, outline=(20, 40, 90), width=iw(4))
    pd.text((S(PW / 2), S(635)), 'לתשלום', font=font(S(38), 900), fill=WHITE, anchor='mm')
    return lay

_PHC = {}
def phone_at(t):
    st = cart_state(t); p = round(price_at(t), 2); b = bags_at(t)
    key = (st, p, b)
    if key not in _PHC:
        if len(_PHC) > 64: _PHC.clear()
        _PHC[key] = phone_layer(st, p, b)
    return _PHC[key]

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    m.paste_center(img, lay, S(c[0]), S(c[1]))

def burst(img, c, u, col=(255, 236, 120), r0=150, n=10, dur=0.4):
    if not (0 <= u < dur): return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(n):
        a_ = math.radians(k * 360 / n + 10); ra, rb = r0 + 60 * u, r0 + 80 + 200 * u
        line(od, [(c[0] + ra * math.cos(a_), c[1] + ra * math.sin(a_)), (c[0] + rb * math.cos(a_), c[1] + rb * math.sin(a_))], col + (int(230 * (1 - u / dur)),), 10)
    img.alpha_composite(ov)

def neighbour_door(img, t):
    """the neighbour's door across the landing: a parcel pile + a 'חבילה' note (the Black Friday world), sharp"""
    d = ImageDraw.Draw(img)
    for k, (x, y, w, h, c) in enumerate(((120, 1050, 170, 120, (196, 150, 100)), (150, 950, 130, 100, (210, 168, 116)), (300, 1080, 120, 90, (186, 140, 92)))):
        d.rectangle([S(x), S(y), S(x + w), S(y + h)], fill=c, outline=(110, 76, 40), width=iw(4))
        d.line([(S(x + w / 2), S(y)), (S(x + w / 2), S(y + h))], fill=(150, 110, 70), width=iw(6))
    # Black Friday flyer taped to the wall
    d.rounded_rectangle([S(50), S(600), S(280), S(780)], radius=S(10), fill=BF, outline=(60, 60, 70), width=iw(4))
    d.text((S(165), S(650)), 'בלאק', font=font(S(46), 900), fill=ORANGE, anchor='mm')
    d.text((S(165), S(702)), 'פריידיי', font=font(S(46), 900), fill=ORANGE, anchor='mm')
    d.text((S(165), S(750)), '-70%', font=font(S(36), 900), fill=WHITE, anchor='mm')

# ------------------------------------------------------------------ the stairwell, wide-ish: the cold open + the win dance
KX, KY, KF = 620, 860, 1.62
def scene_stair(t, i):
    img = STAIR.copy(); neighbour_door(img, t); d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    v = cat_v(t)
    replay = t < COLD_END
    dance = replay or t >= CHK3
    if replay or t >= DANCE[0]:     # "פטור!" / "יש!!!" — dancing, huge grin
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28, blush=1.0, look=(-6, -10))
        rot = 9 * math.sin(t * 11); dy = -26 * abs(math.sin(t * 9)) - 14 * v
    elif t < L[2]:                   # (WANTWIDE) the want: dreamy, then the $89 shock
        if t < OVER: st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-22, blush=0.8, look=(-22, 8)); rot = 4 * math.sin(t * 5); dy = -10 * v
        else: u = t - OVER; st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', sweat=1.0, ear_dy=-26 * math.exp(-u * 4), look=(-24, 8)); rot = 6 * math.sin(u * 30) * math.exp(-u * 5); dy = -20 * math.exp(-u * 8)
    else:                            # "מוריד שקית אחת." — concentrating, tongue-out squint, then the numbers
        u = t - L[3]
        st.update(lid=0.35, pupil='normal', brow='annoyed', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-8, look=(-24, 10))
        if t >= CHK2: st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-22, blush=0.8, look=(-18, 2))
        rot = 3 * math.sin(t * 5); dy = -10 * v
    E(d, KX, 1650 + 0.5 * dy, 430, 450, fill=FUR, outline=OUT, width=7)
    E(d, KX, 1710 + 0.5 * dy, 200, 300, fill=CREAM)
    # phone thrust up in the paw on the viewer's left (the plant line under the price)
    pc = (250, 1240 + 0.4 * dy + (10 * math.sin(t * 14) if dance else 0))
    grip = (pc[0] - 170, pc[1] + 130)
    capsule(d, (KX - 230, 1460 + 0.5 * dy), grip, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, KX + 40, KY + dy, KF, rot)
    paste_rot(img, phone_at(t), pc, -8 + (3 * math.sin(t * 10) if dance else 0), 0.86)
    d = ImageDraw.Draw(img); E12.big_paw(d, grip, 70, 0.85)
    # other paw: fist pumps while dancing / flicks the bag out
    if dance:
        lp = (930, 1200 - 120 * abs(math.sin(t * 9)))
    else:
        lp = lerp2((880, 1350), (980, 1150), ease_out(clamp((t - BAGOUT + 0.2) / 0.25)))
    capsule(d, (KX + 230, 1460 + 0.5 * dy), lp, 110, FUR, OUT, 4)
    E12.big_paw(d, lp, -30, 0.9)
    if not replay and BAGOUT - 0.05 <= t < BAGOUT + 0.6:       # one bag flies off the screen and out of frame
        u = (t - BAGOUT + 0.05) / 0.65
        bp = (lerp(300, 1150, u), 1150 - 520 * math.sin(math.pi * u * 0.8))
        SH.snack_bag(d, bp, 360 * u, 0.8)
    # the live queue ticket (§O4) stuck in his fur, a gag: he queues even at home
    tk = xform([(-44, -72), (44, -72), (44, 72), (-44, 72)], 760, 1560, 8)
    poly(d, tk, fill=(252, 250, 242), outline=(150, 150, 140), width=3)
    c_ = xform([(0, -16)], 760, 1560, 8)[0]
    d.text((S(c_[0]), S(c_[1])), str(QUEUE), font=font(S(38), 900), fill=INK, anchor='mm')
    if t < 0.45: burst(img, (300, 1200), t, (120, 255, 160), 230, 12, 0.45)
    if t >= CHK3: burst(img, (300, 1200), t - CHK3, (255, 220, 90), 230, 12, 0.5)
    if CHK3 <= t: E18.confetti(img, t - CHK3 + 0.4)
    if replay: E18.confetti(img, t + 1.0)
    return img

# ------------------------------------------------------------------ close-up: his face + the cart beside it (want, coupon, peak, break)
BIGF = os.environ.get('BIGF', '0') == '1'      # 6א probe 14.11 → 45 (v1 46): bigger face, smaller phone in the close-ups
HXP, HYP, FP = (750, 930, 1.95) if BIGF else (720, 960, 1.70)
def scene_close(t, i):
    img = STAIR_BLUR.copy(); d = ImageDraw.Draw(img)
    v = cat_v(t)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    rot, dy = 0.0, 0.0
    if t < OVER:                     # want: dreamy-determined, eyes on the box
        k = 0 if t < L[1] + ss(1, 1) else (1 if t < L[1] + ss(1, 2) else 2)
        pose = [dict(lid=0.0, pupil='big', brow='up', ear_dy=-22, look=(-22, 6), blush=0.6),
                dict(lid=0.3, pupil='big', brow='none', ear_dy=-12, look=(-26, 10), blush=0.9),
                dict(lid=0.15, pupil='normal', brow='annoyed', ear_dy=-6, look=(-8, 0), blush=0.4)][k]
        st.update(pose); st['mouth'] = cat_mouth(t, rest='smile', loud='w'); dy = -8 * v; rot = 3 * math.sin(t * 4)
    elif t < L[2]:                   # $89: "מעל הפטור" — ears flat, shock
        u = t - OVER
        st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', sweat=1.0, ear_dy=-26 * math.exp(-u * 4), look=(-24, 8))
        rot = 6 * math.sin(u * 30) * math.exp(-u * 5); dy = -20 * math.exp(-u * 8)
    elif t < TYPE:                   # "שמונים ותשע... קופון!" — the idea
        idea = t >= L[2] + ss(2, 2) - 0.05
        st.update(lid=0.25 if not idea else 0.0, pupil='normal' if not idea else 'big', brow='annoyed' if not idea else 'up',
                  mouth=cat_mouth(t, rest='flat', loud='w' if not idea else 'smile'), ear_dy=-24 if idea else -4, look=(-20, 8) if not idea else (-4, -12))
        rot = -4 if not idea else 6 * math.sin(t * 12); dy = -10 * v
    elif t < C(L[3]):                # typing BLACK15, price drops ✓
        u = t - TYPE
        st.update(lid=0.1, pupil='big', brow='up', mouth='smile', ear_dy=-18, look=(-24, 10), blush=0.7)
        if t >= CHK1: st.update(blush=1.0, look=(-10, -4)); dy = -16 * abs(math.sin((t - CHK1) * 9))
    elif t < HOLD[0]:                # "סוף סוף... פטור." — paw rising over the button
        st.update(lid=0.2, pupil='normal', brow='none', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-10, blush=0.9, look=(-22, 10))
        rot = -3 + 2 * math.sin(t * 3)
    elif t < BREAK:                  # THE PEAK: eyes closed, paw hovering, hush
        st.update(eye_mode='closed', mouth='smile', ear_dy=-24, blush=1.0, look=(0, -6)); rot = -6; dy = -8
    else:                            # the total: eyes snap open, frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat' if speaking(t) is None else cat_mouth(t, rest='flat', loud='w'),
                  ear_dy=-20 * math.exp(-u * 4), look=(-24, 10), twitch=(0.5 < u < 1.4 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.4))
        dy = -6
    E(d, HXP, 1760, 400, 430, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1810, 180, 290, fill=CREAM)
    pc = (300, 1000 + 5 * math.sin(t * 8))
    sc = 1.06
    if BIGF: pc = (255, 1080 + 5 * math.sin(t * 8)); sc = 0.92
    if t < L[1] + 0.4: sc += 0.16 * math.exp(-(t - T0) * 9)
    if t >= BREAK: sc = 1.12 + 0.12 * math.exp(-(t - BREAK) * 9); pc = (300 + 6 * math.sin(t * 50) * math.exp(-(t - BREAK) * 6), 1000)
    grip = (pc[0] - 200, pc[1] + 140)
    capsule(d, (HXP - 240, 1560), grip, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP, HYP + dy - 8 * v, FP, rot)
    paste_rot(img, phone_at(t), pc, -6, sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, grip, 70, 0.9)
    # the other paw: typing (coupon) / hovering over "לתשלום" (peak) / down on it (tap)
    btn = (pc[0], pc[1] + 0.5 * (635 - PH / 2) * 2 * sc / 1.0 * 0.5 + 0)   # rough button spot
    btn = (pc[0] + 10, pc[1] + (635 - PH / 2) * sc)
    rp = None
    if L[4] <= t < TAP:
        hov = 180 - 70 * ease_io(clamp((t - L[4]) / (HOLD[0] - L[4])))
        rp = (btn[0] + 30, btn[1] - hov)
    elif TAP <= t < BREAK + 0.6:
        rp = (btn[0] + 30, lerp(btn[1] - 110, btn[1] - 10, ease_in(clamp((t - TAP) / 0.1))))
    if rp is not None:
        capsule(d, (HXP + 160, 1560), (rp[0] + 60, rp[1] + 60), 100, FUR, OUT, 4)
        E12.big_paw(d, rp, -20, 0.8)
    if t < L[1] + 0.4: burst(img, (300, 1000), t - T0, (255, 255, 255), 140, 8, 0.3)
    if OVER <= t < OVER + 0.4: burst(img, (300, 1080), t - OVER, (255, 120, 120), 200, 12, 0.4)
    if CHK1 <= t < CHK1 + 0.5: burst(img, (300, 1080), t - CHK1, (120, 255, 160), 220, 12, 0.5)
    if t >= BREAK: burst(img, (300, 1000), t - BREAK, (255, 120, 120), 240, 12, 0.4)
    if t >= STAMP:
        E18.imprint(img, (330, 760), t - STAMP, 'מכס', 1.15, -12)
        burst(img, (330, 760), t - STAMP, (255, 90, 90), 200, 12, 0.35)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('קופון', 820, CHK1), ('שקית', 540, CHK2), ('פטור', 260, CHK3)]
def chips(frame, t):
    if t < OVER + 0.3: return                # the hook owns the top band until the cart
    gold = t >= CHK3
    drained = t >= STAMP
    if t >= STAMP + 0.7: return
    d = ImageDraw.Draw(frame); y = 330
    for k_, (lab, cx, tk) in enumerate(CHIPS):
        ok = t >= tk and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if drained: sc = 1.0 + 0.15 * math.exp(-(t - STAMP) * 10)
        w, h = 220 * sc, 70 * sc
        jx = random.Random(int(t * FPS) + cx).uniform(-8, 8) if drained else 0
        d.rounded_rectangle([cx + jx - w / 2, y - h / 2, cx + jx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + jx + 22 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx + jx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], outline=ink, width=4)

def limit_bar(frame, t):
    """the exemption line: a price bar under the chips — the needle drops under $75 (meter), then jumps over it (break)"""
    if t < OVER or t >= STAMP + 0.7: return
    d = ImageDraw.Draw(frame); y = 430; x0, x1 = 150, 930
    d.rounded_rectangle([x0, y - 16, x1, y + 16], radius=16, fill=(30, 32, 40), outline=(10, 10, 12), width=4)
    lo, hi = 70.0, 90.0
    xp = lambda p: x1 - (p - lo) / (hi - lo) * (x1 - x0)          # RTL: cheaper = right
    x75 = xp(75.0)
    d.rounded_rectangle([x75, y - 16, x1, y + 16], radius=16, fill=(40, 120, 70))
    d.line([(x75, y - 34), (x75, y + 34)], fill=WHITE, width=5)
    d.text((x75, y - 56), '$75', font=font(34, 900), fill=WHITE, anchor='mm', stroke_width=5, stroke_fill=(10, 10, 12))
    p = price_at(t); xn = xp(clamp(p, lo, hi))
    col = GREEN if p <= 75 else RED
    d.ellipse([xn - 26, y - 26, xn + 26, y + 26], fill=col, outline=WHITE, width=5)

def rewind_overlay(frame, t):
    frame.alpha_composite(m.SCAN)
    d = ImageDraw.Draw(frame)
    rng = random.Random(int(t * 120))
    for _ in range(5):
        y = rng.uniform(300, 1700); h = rng.uniform(4, 14)
        d.rectangle([0, y, W, y + h], fill=(255, 255, 255, 70))
    for x0 in (300, 344):
        d.polygon([(x0 + 44, 900), (x0, 930), (x0 + 44, 960)], fill=WHITE, outline=(10, 10, 12), width=5)
    d.text((610, 930), 'רגע קודם', font=font(76, 900), fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(10, 10, 12))

def sub_layer(lines, fill, size=64):
    f = font(size, 900); lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

# ------------------------------------------------------------------ frame
STAIR = STAIR_BLUR = PILL_EP = PILL_Q = None
def init_all():
    global STAIR, STAIR_BLUR, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    s0 = E15.build_door_bg()
    s0.alpha_composite(Image.new('RGBA', s0.size, (255, 248, 236, 40)))   # R6: warm, bright
    STAIR = s0
    STAIR_BLUR = s0.filter(ImageFilter.GaussianBlur(S(3)))
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'stair':
        z = 1.06 + 0.03 * pu; cy = 940
        if t < 0.3: z = 1.28 - 0.22 * ease_out(t / 0.3)
    elif name == 'rewind':
        z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'close':
        z = 1.04 + 0.02 * pu; cy = 1000; cx = 520
        if HOLD[0] <= t < BREAK:
            k = ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0]))); z += 0.08 * k
        if t >= BREAK: z, cx, cy = 1.16 + 0.03 * (t - BREAK), 430, 1040     # onto the total
        if t >= L[104]: z, cx, cy = lerp(1.16, 1.22, ease_out(clamp((t - L[104]) / 0.2))), lerp(430, 640, ease_out(clamp((t - L[104]) / 0.2))), 980
    elif name == 'frozen':
        z, cx, cy = 1.30 + 0.03 * pu, 700, 960
    if name not in ('rewind', 'frozen') and not (name == 'stair' and t < 0.3) and pu < 0.2:
        z = z + 0.07 * (1 - ease_out(pu / 0.2))
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'stair': img = scene_stair(t, i)
    elif name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_close(lerp(C(L[3]) - 0.2, T0 + 0.3, ease_in(u)), i)
    else: img = scene_close(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 18 * math.exp(-t * 5)
    if name == 'close' and 0 <= t - OVER < 0.3: shake = 10 * math.exp(-(t - OVER) * 8)
    if 0 <= t - STAMP < 0.35: shake = 14 * math.exp(-(t - STAMP) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.28 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(60 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CHK1, CHK3, BREAK, STAMP):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    chips(frame, t); limit_bar(frame, t)
    for t0, t1, lines in TOPCAPS:
        if t0 <= t < t1: m.paste_center(frame, m.caption_layer(lines, 104, WHITE), W / 2, 270)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1: m.paste_center(frame, sub_layer(lines, WHITE), W / 2, 1450)
    if t < OVER + 0.3 or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(34)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        add(voice, y, s0, 0.95)
    def whoosh(t0, g=0.06, wl=0.16): add(sfx, m.bandpass(nz(wl), 600, 5000) * np.sin(np.pi * tt_(wl) / wl) ** 2, t0 - 0.08, g)
    def thud(g=0.9):
        tt = tt_(0.45); freq = 150 * np.exp(-tt * 6) + 42
        return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) + m.lowpass(nz(0.45), 420) * np.exp(-tt * 30) * 0.8) * g
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def buzz(t0, g=0.16):
        tt = tt_(0.32); add(sfx, m.lowpass(np.sign(np.sin(2 * np.pi * 110 * tt)), 1200) * np.exp(-tt * 4), t0, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def tap(t0, g=0.12): add(sfx, m.tone(2093.0, 0.08, harm=((1, 1),), decay=30), t0, g)
    def tick(t0, g=0.06): add(sfx, m.tone(1500, 0.03, harm=((1, 1),), decay=60), t0, g)
    def cheer(t0, ln=1.0, g=0.10):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    add(sfx, thud(1.0), 0.0); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), 0.0, 0.4); check(ss(0, 1), 0.12, True)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(HOLD[0]), 150, 900) * 0.6, 0.0, 0.012)                       # stairwell room tone
    add(sfx, m.bandpass(nz(DUR - BREAK + 0.3), 150, 900) * 0.6, BREAK, 0.012)
    for name, a, b in SHOTS[2:]:
        if name != 'frozen': whoosh(a)
    buzz(OVER, 0.14); add(sfx, thud(0.5), OVER)                                        # $89: over the line
    for k in range(7): tap(TYPE + k * 0.07, 0.07)                                      # typing BLACK15
    tc = TYPE
    while tc < CHK1: tick(tc, 0.05); tc += 0.04                                        # the price ticking down
    check(CHK1, 0.15)
    add(sfx, m.bandpass(nz(0.3), 1500, 7000) * np.sin(np.pi * tt_(0.3) / 0.3), BAGOUT - 0.05, 0.10)   # the bag flies off
    check(CHK2, 0.16)
    check(CHK3, 0.2, True); cheer(CHK3 + 0.1, DANCE[1] - CHK3, 0.10)
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.33, 0.5)
    tap(TAP, 0.18)
    tc = BREAK
    while tc < BREAK + 0.55: tick(tc, 0.07); tc += 0.035                              # the total ticking UP
    add(sfx, thud(0.8), STAMP); add(sfx, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), STAMP, 0.5)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), STAMP + 0.02, 0.28)
    out = voice + sfx
    out = out[:int(DUR * SR)]
    wl_ = 0.3; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.28)
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())

def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if mode == 'times':
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', T0)
        print('L', {k: round(v, 2) for k, v in L.items()}, 'D', D)
        print('OVER', round(OVER, 2), 'TYPE', round(TYPE, 2), 'CHK1', round(CHK1, 2), 'BAGOUT', round(BAGOUT, 2), 'CHK2', round(CHK2, 2),
              'CHK3', round(CHK3, 2), 'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK, 2), 'STAMP', round(STAMP, 2), 'FREEZE', round(FREEZE, 2))
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep34_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'{OUTNAME}_audio.wav'); build_audio(wav); print('audio ok')
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
            if k % 150 == 0: print('frame', k, '/', nfr, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
