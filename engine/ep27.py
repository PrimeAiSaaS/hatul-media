#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 27: יום הרווקים: המארז הענק (season 6 "סוף סוף", VOICED, built 3.11 under §P; experiment voiced_length
arm short_21: 20–22 s, cold open ≤1.0 s, rewind 0.25 s, gaps ≈0.05 s, MAXP 0.12 / 0.25, L00 dropped, L07 only in the cold open).
Voices = voice bank 2700–2710 (Benji = cat, Delia = Sharit), prepared by voice/ep27_prep.py.
Want: pick up his singles'-day mega snack box ("חיכיתי לזה שנה."). Plant: the order card on his phone — a big photo of a
crate + a small grey line "כמות: 1 יחידה · 30 גרם": in his paw in the cold open, held up at L05 (the code), lying on the
counter at the peak. Never pointed at.
Climb (4-chip meter הגיעה / קוד / ארגז / חתימה): the SMS "החבילה שלך בנקודת האיסוף" ✓ → Sharit (second shift at the
kiosk, "גם פה?") asks for the code, "4821" (ep22's code) ✓ → she drags out an enormous crate, the shoppers go "וואו" ✓ →
"תחתום פה, חמוד." ✓ gold.
Peak: he hugs the crate, "שלי. סוף סוף... שלי.", opens the flaps, golden light, hush + heartbeat.
Break (win_is_loss): packing peanuts burst out; he digs; one tiny 30 g bag. "אוי... איזה חמוד הוא." Frozen → whip into the
cold open (loop). No music (voiced rule). Pills "פרק 27" + live ticket (hud.stage_of, §O4).

  python3 ep27.py times | test t1 t2 ... | render
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep7 as E7
import ep12 as E12
import ep13 as E13
import ep21_v1 as V1
import ep26 as E26
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep27', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {i: META[i]['dur'] for i in META}
PINKSUB = (255, 182, 210); GOLD = (255, 196, 40); GREEN = (40, 170, 80)
QUEUE = int(os.environ.get('QUEUE', '468'))
EP_LABEL = 'פרק 27'
OUTNAME = os.environ.get('OUTNAME', 'ep27_singles')
LIMIT = float(os.environ.get('LIMIT', '0'))    # render only the first LIMIT seconds (predictor cuts)
SPEAKER = {0: 'cat', 1: 'cat', 2: 'sh', 3: 'cat', 4: 'sh', 5: 'cat', 6: 'sh', 7: 'cat', 8: 'sh', 9: 'cat', 10: 'sh'}
ORDER = [1, 2, 3, 4, 5, 6, 8, 9, 10]   # short_21: L00 dropped (the SMS is already on the phone in L01), L07 only in the cold open

def segments(i, gap_frames=4, thr=0.08):
    env = META[i]['env']; segs = []; start = None; quiet = 0
    for k, v in enumerate(env):
        if v >= thr:
            if start is None: start = k
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet >= gap_frames:
                segs.append((start / FPS, (k - quiet + 1) / FPS)); start = None; quiet = 0
    if start is not None: segs.append((start / FPS, len(env) / FPS))
    return [s_ for s_ in segs if s_[1] - s_[0] >= 0.10]

SEG = {i: segments(i) for i in META}
# ------------------------------------------------------------------ timeline
COLD_OFF = max(0.0, SEG[7][-1][0] - 0.05) if len(SEG[7]) > 1 else 0.0   # cold open = "...זה כולו שלי?!"
COLD_END = round(D[7] - COLD_OFF + 0.08, 2)
RW = (COLD_END, COLD_END + 0.25)
T0 = RW[1]
L = {}
GAP = {1: 0.05, 2: 0.05, 3: 0.04, 4: 0.05, 5: 0.06, 6: 0.05, 8: 0.06, 9: 0.42}
t_ = T0 + 0.03
for i in ORDER:
    L[i] = t_; t_ += D[i] + GAP.get(i, 0.0)
HOLD = (L[9] + D[9], L[10] - 0.02)
BREAK = L[10] - 0.06                       # the peanuts burst
TINY = L[10] + 0.55                        # the tiny bag comes up
FREEZE = L[10] + D[10]
DUR = round(FREEZE + 0.4, 2)
NF = int(round(DUR * FPS))
OCC = [(7, 0.0, COLD_OFF)] + [(i, L[i], 0.0) for i in ORDER]

CHK1 = T0 + 0.35                           # SMS "החבילה שלך בנקודת האיסוף" ✓ הגיעה
CHK2 = L[5] + D[5] - 0.15                  # "...אחת!" ✓ קוד
CHK3 = L[6] + 1.25                         # "...ארגז ענק" ✓ ארגז
CHK4 = L[8] + D[8] - 0.05                  # signed ✓ חתימה (gold)
BOX_IN = (L[6] - 0.05, L[6] + 0.55)        # she drags the crate onto the counter
FLAPS = (L[9] + SEG[9][-1][0] - 0.1 if len(SEG[9]) > 1 else L[9] + 1.2, HOLD[0])   # flaps open on the last "שלי."

SUBS = {
    1: [['מארז החטיפים הענק.'], ['חיכיתי לזה שנה.']],
    2: [['ערב טוב, מותק.'], ['משמרת שנייה.']],
    3: [['שרית?! גם פה?']],
    4: [['קוד איסוף, חמוד?']],
    5: [['ארבע, שמונה,'], ['שתיים, אחת!']],
    6: [['יש לך פה...'], ['ארגז ענק, מותק.']],
    7: [['וואו...'], ['זה כולו שלי?!']],
    8: [['תחתום פה, חמוד.']],
    9: [['שלי.'], ['סוף סוף... שלי.']],
    10: [['אוי...'], ['איזה חמוד הוא.']],
}
def chunk_starts(i):
    chunks = SUBS[i]; segs = SEG[i]
    if len(segs) >= len(chunks):
        tot = sum(len(' '.join(c)) for c in chunks); acc = 0; out = [0.0]
        for k, c in enumerate(chunks[:-1]):
            acc += len(' '.join(c)); guess = D[i] * acc / tot
            cands = [s for s, _ in segs if s > out[-1] + 0.2]
            out.append(min(cands, key=lambda s: abs(s - guess)) if cands else guess)
        return out
    tot = sum(len(' '.join(c)) for c in chunks); acc = 0; out = []
    for c in chunks: out.append(D[i] * acc / tot); acc += len(' '.join(c))
    return out
CS = {i: chunk_starts(i) for i in SUBS}
CS[6] = [0.0, 1.0]                          # "יש לך פה..." / "ארגז ענק, מותק."

SUB_TIMES = []
for li, s0, off in OCC:
    for k, c in enumerate(SUBS[li]):
        a_rel = CS[li][k]; b_rel = CS[li][k + 1] if k + 1 < len(SUBS[li]) else D[li] + 0.2
        if b_rel <= off: continue
        a = s0 + max(0.0, a_rel - off - 0.05); b = s0 + (b_rel - off - 0.05)
        if li == 7: b = min(b, COLD_END)
        else:
            nxt = [L[j] for j in ORDER if L[j] > s0]
            if nxt: b = min(b, nxt[0] - 0.03)
        SUB_TIMES.append((a, b, c, li))

C = lambda i: L[i] - 0.06
SHOTS = [('box', 0.0, COLD_END), ('rewind', COLD_END, T0), ('street', T0, C(2)), ('sh', C(2), C(3)), ('cat', C(3), C(4)),
         ('two', C(4), C(5)), ('code', C(5), C(6)), ('two', C(6), C(9)), ('box', C(9), FREEZE), ('frozen', FREEZE, DUR + 1)]
TOPCAPS = [(0.0, C(2), ['תראו מה הגיע', 'ביום הרווקים'], 92, 222, WHITE)]   # hook F18 (cold-open demo; ep28 was F14), keyword יום הרווקים

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def speaking(t):
    for li, s0, off in OCC:
        if s0 <= t < s0 + D[li] - off: return li, s0, off
    return None

def v_of(t, who):
    sp = speaking(t)
    if not sp or SPEAKER[sp[0]] != who: return 0.0
    li, s0, off = sp; env = META[li]['env']; k = int((t - s0 + off) * FPS)
    return env[k] if k < len(env) else 0.0

def cat_mouth(t, rest='w', loud='smile'):
    v = v_of(t, 'cat')
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

# ------------------------------------------------------------------ props
CARD_BROWN = (196, 146, 92); CARD_D = (150, 104, 60); CARD_O = (84, 56, 28); TAPE = (226, 196, 140)

def crate_layer(flaps=0.0):
    """the enormous box, 640x560 world units (box body bottom-centred); flaps 0 closed → 1 open"""
    w, h = 640, 560
    lay = Image.new('RGBA', (S(w), S(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0, x1, y0, y1 = 20, 620, 180, 550
    if flaps > 0.02:   # the inside (dark) + the four flaps folding out
        poly(d, [(x0, y0), (x1, y0), (x1 - 60, y0 - 40), (x0 + 60, y0 - 40)], fill=(90, 60, 30), outline=CARD_O, width=4)
        a = flaps
        for side in (-1, 1):
            bx = x0 if side < 0 else x1
            tip = (bx + side * 150 * a, y0 - 170 * (1 - a) - 30 * a)
            poly(d, [(bx, y0), ((x0 + x1) / 2 + side * 0, y0), ((x0 + x1) / 2 + side * 60 * a, tip[1] - 20 * a), tip], fill=CARD_D, outline=CARD_O, width=5)
    d.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=CARD_BROWN, outline=CARD_O, width=iw(6))
    d.rectangle([S(x0), S(y0), S(x0 + 26), S(y1)], fill=CARD_D)
    if flaps <= 0.02:
        d.rectangle([S(x0), S(y0 - 10), S(x1), S(y0 + 14)], fill=CARD_D, outline=CARD_O, width=iw(4))
        d.rectangle([S(290), S(y0 - 10), S(350), S(y1)], fill=TAPE)          # tape strip down the middle
    else:
        d.rectangle([S(290), S(y0 + 10), S(350), S(y1)], fill=TAPE)
    d.rounded_rectangle([S(80), S(300), S(260), S(420)], radius=S(10), fill=(250, 250, 244), outline=(120, 120, 120), width=iw(3))
    d.text((S(170), S(340)), '11.11', font=font(S(46), 900), fill=(214, 36, 60), anchor='mm')
    d.text((S(170), S(390)), 'מארז ענק', font=font(S(30), 900), fill=(40, 40, 50), anchor='mm')
    for k in range(3):   # "this side up" arrows
        cx = 430 + k * 50
        poly(d, [(cx, 300), (cx - 16, 330), (cx + 16, 330)], fill=CARD_O); d.rectangle([S(cx - 5), S(330), S(cx + 5), S(370)], fill=CARD_O)
    return lay

def order_card(d, x, y, w, code=None):
    """the order card drawn into a phone screen at (x, y) top-left, width w (layer pixels at K)"""
    sc = w / S(260)
    def T(v): return v * sc
    d.rounded_rectangle([x, y, x + w, y + T(S(330))], radius=int(T(S(16))), fill=(255, 255, 255), outline=(210, 210, 216), width=max(2, int(T(S(2)))))
    d.text((x + w - T(S(14)), y + T(S(26))), 'ההזמנה שלך', font=font(int(T(S(22))), 800), fill=(110, 110, 120), anchor='rm')
    # a big photo of a crate
    bx0, by0, bx1, by1 = x + T(S(30)), y + T(S(70)), x + w - T(S(30)), y + T(S(200))
    d.rectangle([bx0, by0, bx1, by1], fill=CARD_BROWN, outline=CARD_O, width=max(2, int(T(S(4)))))
    d.rectangle([(bx0 + bx1) / 2 - T(S(14)), by0, (bx0 + bx1) / 2 + T(S(14)), by1], fill=TAPE)
    d.text(((bx0 + bx1) / 2, (by0 + by1) / 2), '11.11', font=font(int(T(S(34))), 900), fill=(214, 36, 60), anchor='mm')
    d.text((x + w / 2, y + T(S(232))), 'מארז החטיפים הענק', font=font(int(T(S(26))), 900), fill=(20, 20, 26), anchor='mm')
    d.text((x + w / 2, y + T(S(266))), 'כמות: 1 יחידה · 30 גרם', font=font(int(T(S(19))), 600), fill=(150, 150, 158), anchor='mm')   # THE PLANT
    if code is not None:
        for k in range(4):
            cx = x + w / 2 + T(S((k - 1.5) * 48))   # digits read left to right
            d.rounded_rectangle([cx - T(S(20)), y + T(S(284)), cx + T(S(20)), y + T(S(324))], radius=int(T(S(6))),
                                fill=(255, 246, 200) if k < len(code) else (240, 240, 244), outline=(160, 160, 170), width=max(1, int(T(S(2)))))
            if k < len(code): d.text((cx, y + T(S(305))), code[k], font=font(int(T(S(28))), 900), fill=(20, 20, 26), anchor='mm')

def phone_layer(sms=False, code=None):
    pw, ph = 300, 560
    lay = Image.new('RGBA', (S(pw), S(ph)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(pw) - 1, S(ph) - 1], radius=S(40), fill=(24, 24, 30), outline=(8, 8, 10), width=iw(5))
    d.rounded_rectangle([S(14), S(30), S(pw - 14), S(ph - 30)], radius=S(26), fill=(232, 236, 244))
    d.rounded_rectangle([S(120), S(12), S(180), S(22)], radius=S(5), fill=(60, 60, 70))
    order_card(d, S(20), S(150), S(260), code)
    if sms:
        d.rounded_rectangle([S(20), S(46), S(280), S(136)], radius=S(16), fill=(255, 255, 255), outline=(200, 204, 214), width=iw(2))
        d.rounded_rectangle([S(232), S(58), S(268), S(94)], radius=S(8), fill=(40, 170, 80))
        d.text((S(222), S(76)), 'SMS · עכשיו', font=font(S(18), 700), fill=(120, 120, 130), anchor='rm')
        d.text((S(266), S(116)), 'החבילה שלך בנקודת האיסוף', font=font(S(19), 900), fill=(20, 20, 26), anchor='rm')
    return lay

def tiny_bag_layer():
    lay = Image.new('RGBA', (S(160), S(200)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    SH.snack_bag(d, (80, 96), 0, 0.62)
    d.rounded_rectangle([S(26), S(150), S(134), S(192)], radius=S(10), fill=(255, 255, 255), outline=(30, 30, 30), width=iw(3))
    d.text((S(80), S(171)), '30 גרם', font=font(S(26), 900), fill=(20, 20, 26), anchor='mm')
    return lay

PEANUTS = [(random.Random(k).uniform(-260, 260), random.Random(k + 70).uniform(-1300, -500), random.Random(k + 7).uniform(0, 6.28),
            random.Random(k + 3).uniform(0.7, 1.3)) for k in range(70)]
def peanuts(img, c, u):
    """packing peanuts bursting out of the crate at c, u seconds after the break"""
    if u < 0: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for vx, vy, ph, s in PEANUTS:
        x = c[0] + vx * u * 2.2; y = c[1] + vy * u + 1500 * u * u
        if y > 1900: y = 1900 - 20 * s
        poly(od, epoly(x, y, 26 * s, 14 * s, math.degrees(ph + u * 6)), fill=(250, 246, 232, 255), outline=(190, 184, 160, 255), width=3)
    img.alpha_composite(ov)

def glow(img, c, k, r=520):
    if k <= 0: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for j in range(12):   # golden rays
        a = math.radians(-90 + (j - 5.5) * 13); r0, r1 = 60, r
        poly(od, [(c[0] + r0 * math.cos(a - 0.04), c[1] + r0 * math.sin(a - 0.04)), (c[0] + r1 * math.cos(a - 0.09), c[1] + r1 * math.sin(a - 0.09)),
                  (c[0] + r1 * math.cos(a + 0.09), c[1] + r1 * math.sin(a + 0.09)), (c[0] + r0 * math.cos(a + 0.04), c[1] + r0 * math.sin(a + 0.04))],
             fill=(255, 220, 90, int(80 * k)))
    E(od, c[0], c[1] + 60, 300, 90, fill=(255, 236, 140, int(110 * k)))
    img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(S(6))))

# ------------------------------------------------------------------ the kiosk at the counter: the crate scene (cold open + peak + break)
KX, KY, KF = 600, 860, 1.6
CR_C = (560, 1330)          # crate centre (world) in the box scene
CRS = 1.22                  # crate scale: enormous
def cat_box_state(t, i, frozen=False):
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.5)
    rot, dy = 0.0, 0.0
    if frozen or t >= TINY:
        u = t - TINY
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', look=(18, 4), sweat=1.0, blush=0.0, ear_droop=0.6 * clamp(u / 0.3),
                  ear_dy=-18 * math.exp(-max(0, u) * 5), twitch=(0.15 < u < 0.4 and int(t * 12) % 2 == 0))
        return st, 0.0, 0.0
    if t < COLD_END:                    # cold open: "וואו... זה כולו שלי?!" — sparkling
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-24, blush=1.0, look=(-8, 16))
        dy = -16 * abs(math.sin(t * 8)); rot = 3 * math.sin(t * 9)
        return st, rot, dy
    if t < BREAK:                       # peak: hug, "שלי. סוף סוף... שלי.", eyes closed in bliss, then the flaps
        u = t - L[9]
        st.update(lid=0.98 if t < FLAPS[0] else 0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), blush=1.0,
                  ear_dy=-10, look=(-4, 20))
        rot = 4 * math.sin(u * 2.4)
        if t >= FLAPS[0]: st.update(mouth='w', ear_dy=-22); rot = 0.0
        return st, rot, dy
    u = t - BREAK                       # digging
    st.update(lid=0.0, pupil='big', brow='annoyed', mouth='flat', look=(-4, 26), blush=0.4, ear_dy=-10)
    dy = 30 * abs(math.sin(u * 9)); rot = 4 * math.sin(u * 13)
    return st, rot, dy

def scene_box(t, i, frozen=False):
    img = KIOSK_BG.copy()
    peakish = t >= C(9)
    mood = 2 if (frozen or t >= TINY) else (1 if (t < COLD_END or (peakish and t < BREAK)) else 0)
    for name, x, y, sc, ph in V1.QUEUE_KIOSK:
        hop = -24 * abs(math.sin(t * 7 + ph)) if mood == 1 and t < COLD_END else 0
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + hop + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_box_state(t, i, frozen)
    E(d, KX, 1600 + 0.5 * dy, 430, 450, fill=FUR, outline=OUT, width=7)
    E(d, KX, 1660 + 0.5 * dy, 200, 300, fill=CREAM)
    E12.paste_head(img, st, i, KX, KY + dy, KF, rot)
    V1.build_counter(img); d = ImageDraw.Draw(img)
    # the crate on the counter
    fl = ease_out(clamp((t - FLAPS[0]) / 0.3)) if (peakish or frozen) else 0.0
    if frozen or t >= BREAK: fl = 1.0
    gk = clamp((t - FLAPS[0]) / 0.25) if (peakish and FLAPS[0] <= t < BREAK + 0.15) else 0.0
    glow(img, (CR_C[0], CR_C[1] - 260), gk)
    E26.paste_rot(img, CRATE_OPEN if fl > 0.5 else CRATE, CR_C, 0, CRS)
    d = ImageDraw.Draw(img)
    # paws: hug the crate's top corners (cold open + peak), or dig (break)
    if t < COLD_END:
        lp = (CR_C[0] - 360, CR_C[1] - 150 + 6 * math.sin(t * 6))
        rp = (930, 1060 + 10 * math.sin(t * 5))              # phone paw
    elif t < BREAK and not frozen:
        sq = 10 * math.sin((t - L[9]) * 5)
        lp = (CR_C[0] - 360 - sq, CR_C[1] - 150); rp = (CR_C[0] + 360 + sq, CR_C[1] - 150)
    else:
        u = max(0.0, t - BREAK)
        lp = (CR_C[0] - 120 + 40 * math.sin(u * 18), CR_C[1] - 230 + 30 * abs(math.sin(u * 14)))
        rp = (870, 1180) if t >= TINY or frozen else (CR_C[0] + 140 - 40 * math.sin(u * 16), CR_C[1] - 230 + 30 * abs(math.cos(u * 15)))
    capsule(d, (KX - 230, 1420 + 0.5 * dy), lp, 110, FUR, OUT, 4)
    capsule(d, (KX + 230, 1420 + 0.5 * dy), rp, 110, FUR, OUT, 4)
    if t < COLD_END:   # the phone in his paw, order card toward camera (the plant)
        E26.paste_rot(img, PHONE, (rp[0] - 10, rp[1] - 230), -8, 0.95)
    else:              # the phone lying on the counter (the plant at the peak)
        E26.paste_rot(img, PHONE_FLAT, (175, 1640), -14, 0.85)
    d = ImageDraw.Draw(img)
    if t >= TINY or frozen:
        bu = clamp((t - TINY) / 0.2) if not frozen else 1.0
        E26.paste_rot(img, TINY_BAG, (rp[0] - 10, rp[1] - 150 - 40 * ease_out(bu)), 8, 1.0 + 0.45 * ease_out(bu))
        d = ImageDraw.Draw(img)
    E12.big_paw(d, lp, 20, 0.9); E12.big_paw(d, rp, -20 if t < COLD_END or t >= TINY or frozen else -10, 0.9)
    if t >= BREAK and not frozen: peanuts(img, (CR_C[0], CR_C[1] - 240), t - BREAK)
    if frozen:   # the peanuts settled all over the counter
        peanuts(img, (CR_C[0], CR_C[1] - 200), 1.4)
    if t < COLD_END:
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(7):   # sparkles around the crate
            a = math.radians(k * 51 + t * 120); r = 380
            poly(od, m.star(CR_C[0] + r * math.cos(a), CR_C[1] - 120 + 0.5 * r * math.sin(a), 24 + 8 * math.sin(t * 9 + k), 4, 0.3, -90), fill=(255, 236, 120, 230))
        img.alpha_composite(ov)
    return img

# ------------------------------------------------------------------ the street: he runs to the pickup point, phone by his face
def build_street_bg():
    w = W + 1400
    img = Image.new('RGBA', (w * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        v = y / H; d.rectangle([0, S(y), w * K, S(y + 8)], fill=(int(lerp(36, 120, v)), int(lerp(40, 86, v)), int(lerp(90, 110, v))))
    rng = random.Random(27)
    x = -40
    while x < w:
        bw = rng.uniform(220, 360); bh = rng.uniform(600, 1100); top = 1450 - bh
        col = rng.choice([(70, 66, 96), (88, 76, 110), (60, 70, 100)])
        d.rectangle([S(x), S(top), S(x + bw), S(1460)], fill=col, outline=(30, 30, 46), width=iw(4))
        for wy in range(int(top + 60), 1400, 110):
            for wx in range(int(x + 30), int(x + bw - 50), 80):
                lit = rng.random() < 0.55
                d.rectangle([S(wx), S(wy), S(wx + 44), S(wy + 60)], fill=(255, 214, 120) if lit else (44, 44, 64))
        x += bw + rng.uniform(10, 60)
    d.rectangle([0, S(1460), w * K, H * K], fill=(96, 96, 106))
    d.rectangle([0, S(1460), w * K, S(1480)], fill=(150, 150, 160))
    for lx in range(200, w, 600):   # street lamps
        d.rectangle([S(lx - 8), S(700), S(lx + 8), S(1470)], fill=(40, 40, 50))
        E(d, lx, 690, 40, 26, fill=(255, 236, 160))
    return img

def scene_street(t, i):
    u = t - T0
    off = int(S(min(1400, 520 * u)))
    img = STREET.crop((off, 0, off + W * K, H * K)).copy()
    d = ImageDraw.Draw(img)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(7):   # speed lines
        y = 520 + k * 170; x0 = (900 - (u * 2400 + k * 330) % 1400)
        line(od, [(x0, y), (x0 + 320, y)], (255, 255, 255, 150), 9)
    img.alpha_composite(ov); d = ImageDraw.Draw(img)
    bob = -36 * abs(math.sin(u * 11))
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, lid=0.0, pupil='big', brow='up', blush=0.9, ear_dy=-20,
                                     mouth=cat_mouth(t, rest='smile', loud='smile'), look=(16, 6))
    hx, hy = 470, 900 + bob
    E(d, hx, 1600 + bob, 400, 430, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1660 + bob, 190, 290, fill=CREAM)
    E12.paste_head(img, st, i, hx, hy, 1.55, 6 + 3 * math.sin(u * 11))
    d = ImageDraw.Draw(img)
    rp = (870, 1260 + 0.6 * bob)
    capsule(d, (hx + 230, 1440 + bob), rp, 110, FUR, OUT, 4)
    E26.paste_rot(img, PHONE_SMS, (rp[0] - 20, rp[1] - 250), -6, 1.0)
    d = ImageDraw.Draw(img); E12.big_paw(d, rp, -20, 0.9)
    E26.burst(img, (rp[0] - 20, rp[1] - 470), t - (T0 + 0.1), (120, 255, 160), 120, 10, 0.35)
    return img

# ------------------------------------------------------------------ Sharit at the kiosk counter, second shift (orange uniform)
def kiosk_sharit(st, i):
    keep = (SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O)
    SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O = (240, 128, 40), (206, 96, 24), (110, 50, 10)
    try: return SH.draw(st, i)
    finally: SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O = keep

def scene_sh(t, i):
    img = KSH_BG.copy()
    st = SH.base(); st.update(lid=0.5, red=0.8, look=(0, 6), blush=0.6, snack=True, hand_l=(190, 720))
    st['mouth'] = 'talk' if v_of(t, 'sh') > 0.12 else ('munch' if (i // 4) % 2 else 'grin')
    st['rot'] = -3 * math.sin(t * 3)
    img.alpha_composite(kiosk_sharit(st, i), dest=(int(S(E3.SH_POS[0])), int(S(E3.SH_POS[1]))))
    V1.build_counter(img); d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(660), S(1640), S(1000), S(1730)], radius=S(12), fill=(255, 246, 200), outline=(200, 160, 40), width=iw(4))
    d.text((S(830), S(1685)), 'נקודת איסוף', font=font(S(42), 900), fill=(40, 40, 50), anchor='mm')
    return img

# ------------------------------------------------------------------ the cat at the counter (double take) / holding up the code
def scene_cat(t, i, code_mode=False):
    img = KIOSK_BG.copy()
    for name, x, y, sc, ph in V1.QUEUE_KIOSK:
        E13.paste_sprite(img, name, 0, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.4)
    rot, dy = 0.0, 0.0
    hx = 640 if not code_mode else 700
    if not code_mode:      # "שרית?! גם פה?" — double take
        u = t - L[3]
        st.update(lid=0.0, pupil='tiny' if u < 0.6 else 'big', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-26 * math.exp(-u * 2),
                  sweat=1.0, look=(-20, 4) if int(u * 6) % 2 == 0 and u < 0.5 else (-16, 0))
        rot = 8 * math.sin(u * 20) * math.exp(-u * 3); dy = -30 * math.exp(-u * 5)
    else:                  # reading out the code, proud
        u = t - L[5]
        st.update(lid=0.1, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), blush=0.8, ear_dy=-12, look=(-22, 10))
        if t >= CHK2: st.update(mouth='smile', ear_dy=-24); dy = -22 * abs(math.sin((t - CHK2) * 8)) * math.exp(-(t - CHK2) * 2)
        rot = 2 * math.sin(t * 4)
    E(d, hx, 1620 + 0.5 * dy, 430, 450, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1680 + 0.5 * dy, 200, 300, fill=CREAM)
    E12.paste_head(img, st, i, hx, 880 + dy, 1.7, rot)
    V1.build_counter(img); d = ImageDraw.Draw(img)
    if code_mode:          # the phone held up big toward camera (the plant, mid-climb), digits filling in
        n = sum(1 for a_, _ in SEG[5][:4] if t >= L[5] + a_ + 0.1)
        if t >= CHK2: n = 4
        lay = PHONE_CODES[n]
        rp = (330, 1330 + 8 * math.sin(t * 3))
        capsule(d, (hx - 230, 1450 + 0.5 * dy), rp, 110, FUR, OUT, 4)
        E26.paste_rot(img, lay, (rp[0] + 10, rp[1] - 300), 6, 1.25)
        d = ImageDraw.Draw(img); E12.big_paw(d, rp, 20, 0.9)
        if t >= CHK2: E26.burst(img, (rp[0] + 10, rp[1] - 300), t - CHK2, (120, 255, 160), 260, 12, 0.4)
    else:
        rp = (hx + 200, 1450)
        capsule(d, (hx + 230, 1460), rp, 110, FUR, OUT, 4); E12.big_paw(d, rp, -10, 0.9)
    return img

# ------------------------------------------------------------------ two-shot: Sharit (left) and the cat (right) at the kiosk counter
T_HEAD = (225, 900); TS = 1.45
HX2, HY2, F2 = 800, 960, 1.45
QUEUE_TWO = [('c2', 560, 700, 0.44, 0.4), ('h0', 700, 640, 0.40, 1.6), ('c3', 1000, 700, 0.42, 2.4)]
def scene_two(t, i):
    img = KSH_BG.copy()
    wow = CHK3 - 0.1 <= t < L[8] + 0.2
    cheer = t >= CHK4
    for name, x, y, sc, ph in QUEUE_TWO:
        jump = (-20 * abs(math.sin(t * 9 + ph))) if cheer else 0
        E13.paste_sprite(img, name, 2 if wow else (1 if cheer else 0), x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.45, red=0.8, blush=0.8, look=(18, 6))
    st_s['mouth'] = 'talk' if v_of(t, 'sh') > 0.12 else 'grin'
    if BOX_IN[0] <= t < BOX_IN[1] + 0.2: st_s.update(hand_r=(600, 640), hand_l=(420, 640), rot=-6, look=(20, 14))   # dragging the crate
    if t >= L[8] - 0.06 and t < CHK4 + 0.3: st_s.update(hand_r=(600, 700), look=(22, 18))                       # holding out the pad
    Ls = kiosk_sharit(st_s, i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.5)
    rot, dy = 0.0, 0.0
    if t < L[6]:            # "קוד איסוף, חמוד?" — eager, phone ready
        st.update(lid=0.1, pupil='big', brow='up', mouth='smile', look=(-18, 4), blush=0.6)
    elif t < L[8]:          # the crate: jaw drop, sparkles
        u = t - L[6]
        st.update(lid=0.0, pupil='big' if t >= CHK3 else 'normal', brow='up', mouth='w', ear_dy=-24 * clamp(u / 0.3), blush=1.0, look=(-16, 14))
        dy = -14 * abs(math.sin(u * 8)) if t >= CHK3 else 0
    else:                   # signing, then joy
        u = t - L[8]
        st.update(lid=0.3, pupil='normal', brow='annoyed', mouth='flat', look=(-14, 18))
        if t >= CHK4: v = t - CHK4; st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24 * math.exp(-v * 3), look=(-10, 0), blush=1.0); dy = -20 * abs(math.sin(v * 9)) * math.exp(-v * 1.5)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1720)], radius=S(16), fill=(150, 96, 58), outline=(80, 50, 28), width=iw(6))
    d.rectangle([S(-20), S(1580), S(1100), S(1606)], fill=(190, 130, 80))
    rp = (HX2 + 220, 1480 + 8 * math.sin(t * 2.0))
    if t >= BOX_IN[0]:      # the crate dragged onto the counter, from her side
        e = ease_out(clamp((t - BOX_IN[0]) / (BOX_IN[1] - BOX_IN[0])))
        c = lerp2((-300, 1300), (420, 1300), e)
        E26.paste_rot(img, CRATE, c, -2 * (1 - e), 0.78)
        d = ImageDraw.Draw(img)
        if t >= CHK3:
            E26.burst(img, (420, 1150), t - CHK3, (255, 236, 120), 280, 14, 0.5)
    if t >= L[8] - 0.06:    # the signing pad
        pad_c = (700, 1500)
        d.rounded_rectangle([S(pad_c[0] - 130), S(pad_c[1] - 80), S(pad_c[0] + 130), S(pad_c[1] + 80)], radius=S(14), fill=(40, 40, 46), outline=(10, 10, 12), width=iw(4))
        d.rounded_rectangle([S(pad_c[0] - 116), S(pad_c[1] - 66), S(pad_c[0] + 116), S(pad_c[1] + 66)], radius=S(8), fill=(246, 246, 240))
        a = clamp((t - (L[8] + 0.3)) / max(0.2, CHK4 - L[8] - 0.35))
        pts = [(pad_c[0] - 90 + 180 * k / 20, pad_c[1] + 10 - 26 * math.sin(k * 1.3) * (0.5 + 0.5 * math.cos(k * 0.7))) for k in range(int(20 * a) + 1)]
        if len(pts) > 1: line(d, pts, (30, 60, 160), 6)
        if t >= L[8] + 0.3 and t < CHK4 + 0.1: rp = (pts[-1][0] + 40, pts[-1][1] + 60)
        if t >= CHK4: rp = (HX2 + 200, 1250 - 60 * abs(math.sin((t - CHK4) * 9)) * math.exp(-(t - CHK4) * 1.2))   # fist pump
    capsule(d, (HX2 + 220, 1540), rp, 100, FUR, OUT, 4)
    E12.big_paw(d, rp, -10, 0.85)
    if cheer: E26.confetti(img, t - CHK4 + 0.5)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('הגיעה', 860), ('קוד', 650), ('ארגז', 430), ('חתימה', 215)]
def lerpc_(a, b, u): return tuple(int(lerp(x, y, u)) for x, y in zip(a, b))
def chips(frame, t):
    if RW[0] <= t < T0 + 0.15: return
    if t < COLD_END: done = [True, True, True, False]; tk = [None] * 4
    else:
        done = [t >= CHK1, t >= CHK2, t >= CHK3, t >= CHK4]; tk = [CHK1, CHK2, CHK3, CHK4]
    drained = t >= TINY
    d = ImageDraw.Draw(frame)
    y = 330
    gold = done[3] and not drained
    for k, (lab, cx) in enumerate(CHIPS):
        ok = done[k] and not drained
        fill = GOLD if (ok and gold) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if ok else (190, 194, 206)
        u = t - tk[k] if tk[k] is not None else -1
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if gold and HOLD[0] <= t < BREAK: sc = 1.04 + 0.04 * math.sin(t * 14)
        w, h = 190 * sc, 68 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 20 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 32 * sc
        if ok:
            d.ellipse([bx - 19 * sc, y - 19 * sc, bx + 19 * sc, y + 19 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 17 * sc, y - 17 * sc, bx + 17 * sc, y + 17 * sc], outline=ink, width=4)

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

# ------------------------------------------------------------------ frame
KIOSK_BG = KSH_BG = STREET = CRATE = CRATE_OPEN = PHONE = PHONE_SMS = PHONE_FLAT = TINY_BAG = PILL_EP = PILL_Q = None
PHONE_CODES = []
def init_all():
    global KIOSK_BG, KSH_BG, STREET, CRATE, CRATE_OPEN, PHONE, PHONE_SMS, PHONE_FLAT, TINY_BAG, PILL_EP, PILL_Q, PHONE_CODES
    m.init_static(); E3.init_all()
    kb = V1.build_kiosk_bg()
    ov = Image.new('RGBA', kb.size, (30, 26, 70, 60)); kb.alpha_composite(ov)                 # evening
    KIOSK_BG = kb.filter(ImageFilter.GaussianBlur(S(2)))
    KSH_BG = kb.filter(ImageFilter.GaussianBlur(S(3)))
    KIOSK_BG = kb.filter(ImageFilter.GaussianBlur(S(2)))
    STREET = build_street_bg()
    E13.build_crowd()
    CRATE = crate_layer(0.0); CRATE_OPEN = crate_layer(1.0)
    PHONE = phone_layer(); PHONE_SMS = phone_layer(sms=True); PHONE_FLAT = phone_layer()
    PHONE_CODES = [phone_layer(code='4821'[:n]) for n in range(5)]
    TINY_BAG = tiny_bag_layer()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'box':
        if t < COLD_END: z = 1.20 - 0.14 * ease_out(clamp(t / 0.3)); cy = 980
        else:
            z = 1.04 + 0.04 * pu; cy = 1000
            if HOLD[0] <= t < BREAK: z += 0.08 * ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0])))
            if t >= BREAK: z = 1.06; cy = 960
            if 0 <= t - TINY < 0.3: z = 1.06 + 0.14 * ease_out(clamp((t - TINY) / 0.12))
            elif t >= TINY + 0.3: z = 1.20; cy = 880
    elif name == 'rewind': z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'street': z = 1.04 + 0.02 * pu
    elif name == 'sh': z = 1.10 + 0.03 * pu; cy = 900
    elif name in ('cat', 'code'):
        cy = 900; z = 1.05 + 0.03 * pu
        for s_ in (L[3] + 0.05, CHK2):
            u = t - s_
            if 0 <= u < 0.35: z = max(z, 1.05 + 0.10 * math.exp(-u * 9))
    elif name == 'two':
        z = 1.02 + 0.02 * pu
        for s_ in (CHK3, CHK4):
            u = t - s_
            if 0 <= u < 0.35: z = max(z, 1.02 + 0.08 * math.exp(-u * 9))
    elif name == 'frozen':
        z, cy = 1.22 + 0.08 * (t - FREEZE), 880
    if name not in ('rewind',) and a > 0 and pu < 0.2: z = z + 0.08 * (1 - ease_out(pu / 0.2))
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'box': img = scene_box(t, i)
    elif name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_street(lerp(C(2) - 0.2, T0 + 0.05, ease_in(u)), i)
    elif name == 'street': img = scene_street(t, i)
    elif name == 'sh': img = scene_sh(t, i)
    elif name == 'cat': img = scene_cat(t, i)
    elif name == 'code': img = scene_cat(t, i, code_mode=True)
    elif name == 'two': img = scene_two(t, i)
    else: img = scene_box(t, i, frozen=True)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.4: shake = 14 * math.exp(-t * 6)
    if 0 <= t - BREAK < 0.35: shake = max(shake, 14 * math.exp(-(t - BREAK) * 8))
    if 0 <= t - CHK3 < 0.3: shake = max(shake, 8 * math.exp(-(t - CHK3) * 9))
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:     # the hush + heartbeat pulse (warm)
        k = clamp((t - HOLD[0]) / 0.12)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.04 + 0.2 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(40 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CHK3, BREAK):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.22:
        k_ = (t - (DUR - 0.22)) / 0.22
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    chips(frame, t)
    for t0, t1, lines, size, yc, fill in TOPCAPS:
        if t0 <= t < t1: m.paste_center(frame, m.caption_layer(lines, size, fill), W / 2, yc)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            cap = E26.sub_layer(lines, PINKSUB if SPEAKER[li] == 'sh' else WHITE)
            m.paste_center(frame, cap, W / 2, 1450 if len(lines) == 1 else 1420)
    if name in ('box', 'frozen', 'two', 'cat', 'code', 'street'):
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(27)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for li, s0, off in OCC:
        y = np.load(os.path.join(VDIR, f'line{li:02d}.npy')).astype(np.float64)
        y = y[int(off * SR):]
        if off > 0: f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f)
        add(voice, y, s0, 0.95 if SPEAKER[li] == 'cat' else 0.9)
    def whoosh(t0, g=0.06, wl=0.14): add(sfx, m.bandpass(nz(wl), 600, 5000) * np.sin(np.pi * tt_(wl) / wl) ** 2, t0 - 0.07, g)
    def thud(g=0.9):
        tt = tt_(0.45); freq = 150 * np.exp(-tt * 6) + 42
        return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) + m.lowpass(nz(0.45), 420) * np.exp(-tt * 30) * 0.8) * g
    def cheer(t0, ln=1.4, g=0.22):
        tt = tt_(ln); env = np.minimum(1, tt / 0.06) * np.exp(-tt * 1.6)
        add(sfx, m.bandpass(nz(ln), 300, 3200) * env * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    def wow(t0, g=0.05):   # the shoppers' "וואו" (a rising-falling vowel cloud, no words)
        for k, f in enumerate((300, 360, 420, 250)):
            tw = tt_(0.9); fr = f + 80 * np.sin(np.pi * tw / 0.9)
            add(sfx, m.lowpass(np.sin(2 * np.pi * np.cumsum(fr) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(fr) / SR), 1500) * np.sin(np.pi * tw / 0.9), t0 + k * 0.05, g)
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def sparkle(t0, g=0.08):
        for k in range(6): add(sfx, m.tone(2093 + 300 * k, 0.25, harm=((1, 1),), decay=14), t0 + k * 0.05, g)
    def dtmf(t0, g=0.09):
        add(sfx, (np.sin(2 * np.pi * 770 * tt_(0.09)) + np.sin(2 * np.pi * 1336 * tt_(0.09))) * 0.5, t0, g)
    def ding(t0):
        add(sfx, m.tone(1318.5, 0.5, harm=((1, 1), (2.76, 0.2)), decay=7), t0, 0.2)
        add(sfx, m.tone(1760.0, 0.6, harm=((1, 1), (2.76, 0.2)), decay=7), t0 + 0.09, 0.18)
    # cold open: impact + sparkle
    add(sfx, thud(0.9), 0.0); sparkle(0.05, 0.08)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    # street: night ambience + running steps, the SMS ding
    st_len = C(2) - T0; add(sfx, m.lowpass(nz(st_len), 600) * 0.6, T0, 0.03)
    for k in range(int(st_len / 0.19)): add(sfx, m.lowpass(nz(0.05), 900) * np.exp(-tt_(0.05) * 60), T0 + k * 0.19, 0.22)
    ding(T0 + 0.08); check(CHK1, 0.14)
    # kiosk murmur under everything after the street, until the hush
    ml = HOLD[0] - C(2); mur = m.bandpass(nz(ml), 200, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * tt_(ml))); add(sfx, mur, C(2), 0.025)
    add(sfx, m.bandpass(nz(0.6), 200, 1400) * np.exp(-tt_(0.6) * 3), 0.0, 0.02)
    for name, a, b in SHOTS[2:]: whoosh(a)
    add(sfx, thud(0.4), L[3] + 0.02)                                # the double take
    for a_, _ in SEG[5][:4]: dtmf(L[5] + a_ + 0.1)     # the code digits
    check(CHK2)
    # the crate dragged in: cardboard scrape + thump, the wow
    add(sfx, m.lowpass(nz(0.55), 700) * np.sin(np.pi * tt_(0.55) / 0.55), BOX_IN[0], 0.22); add(sfx, thud(0.8), BOX_IN[1])
    check(CHK3); wow(CHK3 - 0.05, 0.06)
    # signing scribble
    sl = max(0.2, CHK4 - L[8] - 0.3); add(sfx, m.bandpass(nz(sl), 2000, 7000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 6 * tt_(sl)))), L[8] + 0.3, 0.05)
    check(CHK4, 0.18, True); cheer(CHK4, 1.4, 0.2)
    # peak: flaps creak + golden shimmer, hush + heartbeat
    add(sfx, m.bandpass(nz(0.3), 300, 2000) * np.sin(np.pi * tt_(0.3) / 0.3), FLAPS[0], 0.12); sparkle(FLAPS[0] + 0.1, 0.07)
    heartbeat(HOLD[0] + 0.03); heartbeat(HOLD[0] + 0.23, 0.5)
    # the break: peanuts burst (dry rustle), digging, the tiny bag
    add(sfx, thud(0.5), BREAK)
    bl = 1.3; add(sfx, m.bandpass(nz(bl), 1500, 7000) * np.exp(-tt_(bl) * 2.2) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 9 * tt_(bl)))), BREAK, 0.2)
    add(sfx, m.tone(1760, 0.12, harm=((1, 1),), decay=20), TINY, 0.12)     # a tiny "pip"
    out = voice + sfx
    out = out[:int(DUR * SR)]
    wl_ = 0.26; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.24)
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
        print('DUR', DUR, 'NF', NF, 'COLD', round(COLD_OFF, 2), COLD_END); print('L', {k: round(v, 2) for k, v in L.items()})
        print('CS', {k: [round(x, 2) for x in v] for k, v in CS.items()})
        print('CHK', round(CHK1, 2), round(CHK2, 2), round(CHK3, 2), round(CHK4, 2), 'FLAPS', [round(x, 2) for x in FLAPS], 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'TINY', round(TINY, 2), 'FREEZE', round(FREEZE, 2))
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep27_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'{OUTNAME}_audio.wav'); build_audio(wav); print('audio ok')
    if mode == 'audio': return
    mp4 = os.path.join(OUTDIR, f'{OUTNAME}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count() or 2, initializer=_init_worker) as pool:
        for k, b in enumerate(pool.imap(_render, range(int(LIMIT * FPS) if LIMIT else NF), chunksize=4)):
            proc.stdin.write(b)
            if k % 150 == 0: print('frame', k, '/', NF, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
