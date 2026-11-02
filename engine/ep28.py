#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 28: ארנונה 2027: עוד 3% (season 6 "סוף סוף", VOICED, built 3.11 under §P; experiment voiced_length
arm short_21: 20–22 s, cold open ≤1.5 s, rewind 0.25 s, gaps ≈0.05 s, MAXP 0.12 / 0.25, L05+L06 dropped).
Voices = voice bank 2800–2810 (Benji = cat, Delia = Sharit), prepared by voice/ep28_prep.py.
Want: a discount on the new ארנונה bill ("+3%"). Plant: the wall clock behind Sharit (12:57 → 12:59) and the sign
"הפסקת צהריים 13:00"; she glances at it at L01 and L07, never explained. Reversal of help: she is suspiciously fast and
helpful the whole climb because she wants to finish before her break.
Climb (4-chip meter טופס / זכאות / הנחה / חותמת): she fills the form herself, typing with BOTH hands ✓ → "גר לבד?" "רק אני
והחטיפים." ✓ → "הנחת יחיד. עשרים וחמישה אחוז!" -25% on the bill ✓, the queue cheers → "שרית, את מלכה!".
Peak: the stamp raised high, "רק חותמת אחת, מותק...", 12:59:5x, hush + heartbeat, the last chip pulsing.
Break (reversal_of_help): 13:00 DING, she sets the stamp down unstamped, the "בהפסקה" sign drops, "...הפסקה. חמש דקות,
מותק." and she drifts off in her little cloud. Frozen cat → whip into the cold open (loop).
No music (voiced rule). Serial pills "פרק 28" + live ticket (hud.stage_of, §O4).

  python3 ep28.py times | test t1 t2 ... | render
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep8 as E8
import ep12 as E12
import ep13 as E13
import ep26 as E26
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep28', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {i: META[i]['dur'] for i in META}
PINKSUB = (255, 182, 210); GOLD = (255, 196, 40); GREEN = (40, 170, 80)
QUEUE = int(os.environ.get('QUEUE', '468'))
EP_LABEL = 'פרק 28'
OUTNAME = os.environ.get('OUTNAME', 'ep28_arnona')
LIMIT = float(os.environ.get('LIMIT', '0'))    # render only the first LIMIT seconds (predictor cuts)
TWO1 = os.environ.get('TWO1', '0') == '1'      # predictor probe: L01 (she types for him) as a two-shot with his face
SPEAKER = {0: 'cat', 1: 'sh', 2: 'cat', 3: 'sh', 4: 'cat', 5: 'sh', 6: 'cat', 7: 'sh', 8: 'cat', 9: 'sh', 10: 'sh'}
ORDER = [0, 1, 3, 4, 7, 8, 9, 10]   # short_21: L02 lives in the cold open only, L05+L06 dropped (no want/plant/win/peak/break)

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
COLD_OFF = SEG[2][-1][0] - 0.05            # cold open = "מקלידה בשתי ידיים?!" (the loudest line of the climb)
COLD_END = round(D[2] - COLD_OFF + 0.08, 2)
RW = (COLD_END, COLD_END + 0.25)
T0 = RW[1]
L = {}
GAP = {0: 0.05, 1: 0.06, 3: 0.04, 4: 0.06, 7: 0.05, 8: 0.05, 9: 0.40}
t_ = T0 + 0.03
for i in ORDER:
    L[i] = t_; t_ += D[i] + GAP.get(i, 0.0)
HOLD = (L[9] + D[9], L[10])
DING = L[10] - 0.12
FREEZE = L[10] + D[10]
DUR = round(FREEZE + 0.4, 2)
NF = int(round(DUR * FPS))
OCC = [(2, 0.0, COLD_OFF)] + [(i, L[i], 0.0) for i in ORDER]   # (line, start on the timeline, offset into the line)

CHK1 = L[1] + SEG[1][-1][0] + 0.35         # "...מהר, מהר." the form flies out ✓ טופס
CHK2 = L[4] + 0.75                         # "רק אני והחטיפים." ✓ זכאות
CHK3 = L[7] + SEG[7][-1][0]                # "עשרים וחמישה אחוז!" -25% ✓ הנחה
GLANCE = [(L[1] - 0.05, L[1] + 0.55), (L[7] - 0.05, L[7] + 0.6)]
SLAP = L[0] + 0.15
EXIT = (L[10] + 0.75, L[10] + 1.15)        # she drifts off right after "...הפסקה."
SIGN_T = L[10] + 1.15

SUBS = {
    0: [['עוד שלושה אחוז ארנונה?'], ['באתי לערער.']],
    1: [['בוא, מותק.'], ['אני ממלאה לך.'], ['מהר, מהר.']],
    2: [['שרית...'], ['מקלידה בשתי ידיים?!']],
    3: [['גר לבד, נכון?']],
    4: [['רק אני והחטיפים.']],
    7: [['אז מגיעה לך הנחת יחיד.'], ['עשרים וחמישה אחוז!']],
    8: [['עשרים וחמישה?!'], ['שרית, את מלכה!']],
    9: [['רק חותמת אחת, מותק...']],
    10: [['...הפסקה.'], ['חמש דקות, מותק.']],
}
def chunk_starts(i):
    chunks = SUBS[i]; segs = SEG[i]
    if len(segs) >= len(chunks):
        # pick the segment starts that best split the text proportionally
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

SUB_TIMES = []
for li, s0, off in OCC:
    for k, c in enumerate(SUBS[li]):
        a_rel = CS[li][k]; b_rel = CS[li][k + 1] if k + 1 < len(SUBS[li]) else D[li] + 0.2
        if b_rel <= off: continue
        a = s0 + max(0.0, a_rel - off - 0.05); b = s0 + (b_rel - off - 0.05)
        if li == 2: b = min(b, COLD_END)
        else:
            nxt = [L[j] for j in ORDER if L[j] > s0]
            if nxt: b = min(b, nxt[0] - 0.03)
        SUB_TIMES.append((a, b, c, li))

C = lambda i: L[i] - 0.06
SHOTS = [('two', 0.0, COLD_END), ('rewind', COLD_END, T0), ('cat', T0, C(1)), ('two' if TWO1 else 'sh', C(1), C(3)), ('two', C(3), C(4)),
         ('cat', C(4), C(7)), ('sh', C(7), C(8)), ('cat', C(8), C(9)), ('sh', C(9), FREEZE), ('frozen', FREEZE, DUR + 1)]
TOPCAPS = [(0.0, C(1), ['מי שקיבל חשבון ארנונה:'], 92, 222, WHITE)]   # hook F14 (callout; ep26 was F16), keyword ארנונה, from frame 1

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

def clock_secs(t):
    """12:57:30 at frame 0 → 12:59:5x at the peak → exactly 13:00:00 at the DING"""
    start = 12 * 3600 + 57 * 60 + 30
    return start + (13 * 3600 - start) * clamp(t / DING) ** 1.6 if t < DING else 13 * 3600 + (t - DING)

# ------------------------------------------------------------------ props
def bill_layer(cut=False):
    lay = Image.new('RGBA', (S(300), S(380)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([S(6), S(6), S(294), S(374)], fill=(252, 252, 246), outline=(130, 130, 120), width=iw(4))
    d.rectangle([S(6), S(6), S(294), S(70)], fill=(40, 120, 90))
    d.text((S(150), S(38)), 'העירייה', font=font(S(34), 900), fill=WHITE, anchor='mm')
    d.text((S(150), S(118)), 'ארנונה 2027', font=font(S(40), 900), fill=(30, 30, 40), anchor='mm')
    for k in range(4): line(d, [(40, 168 + k * 30), (260 - 50 * (k % 2), 168 + k * 30)], (180, 184, 196), 5)
    d.text((S(150), S(320)), '+3%', font=font(S(78), 900), fill=(214, 36, 44), anchor='mm')
    return lay

def minus25():
    lay = Image.new('RGBA', (S(300), S(160)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(8), S(8), S(292), S(152)], radius=S(22), outline=(30, 150, 70, 240), width=iw(10))
    d.text((S(150), S(80)), '-25%', font=font(S(96), 900), fill=(30, 150, 70, 240), anchor='mm')
    return lay

def stamp_prop(d, p, ang=0.0, s=1.0):
    pts = xform([(-60 * s, 40 * s), (60 * s, 40 * s), (60 * s, 70 * s), (-60 * s, 70 * s)], p[0], p[1], ang)
    poly(d, pts, fill=(160, 30, 40), outline=(60, 10, 14), width=4)
    pts = xform([(-22 * s, -60 * s), (22 * s, -60 * s), (16 * s, 40 * s), (-16 * s, 40 * s)], p[0], p[1], ang)
    poly(d, pts, fill=(120, 80, 50), outline=(50, 30, 16), width=4)
    c = xform([(0, -80 * s)], p[0], p[1], ang)[0]
    E(d, c[0], c[1], 36 * s, 30 * s, fill=(120, 80, 50), outline=(50, 30, 16), width=4)

def break_sign_sign(d, cx, cy, s=1.0):
    d.rounded_rectangle([S(cx - 150 * s), S(cy - 42 * s), S(cx + 150 * s), S(cy + 42 * s)], radius=S(12), fill=(255, 246, 200), outline=(200, 160, 40), width=iw(4))
    d.text((S(cx), S(cy)), 'הפסקת צהריים 13:00', font=font(S(32 * s), 900), fill=(190, 40, 40), anchor='mm')

def wall_clock(d, cx, cy, r, t):
    E(d, cx + 6, cy + 8, r + 4, r + 4, fill=(120, 116, 110))
    E(d, cx, cy, r, r, fill=(58, 58, 64)); E(d, cx, cy, r - 10, r - 10, fill=(250, 248, 238))
    for k in range(12):
        a = math.radians(k * 30)
        line(d, [(cx + (r - 16) * math.sin(a), cy - (r - 16) * math.cos(a)), (cx + (r - 28) * math.sin(a), cy - (r - 28) * math.cos(a))], (40, 40, 44), 5)
    s_ = clock_secs(t)
    for ang, ln, wd, col in ((s_ / 43200 * 360, 0.5 * r, 9, (30, 30, 34)), ((s_ % 3600) / 3600 * 360, 0.78 * r, 6, (30, 30, 34)), ((s_ % 60) * 6, 0.84 * r, 3, (200, 40, 40))):
        a = math.radians(ang); line(d, [(cx, cy), (cx + ln * math.sin(a), cy - ln * math.cos(a))], col, wd)
    E(d, cx, cy, 7, 7, fill=(30, 30, 34))

# ------------------------------------------------------------------ the municipality lobby: the cat big at the counter
def build_iriya_bg():
    img = E3.wall_gradient(); d = ImageDraw.Draw(img)
    d.rectangle([0, S(1200), W * K, H * K], fill=E3.WAIN)
    d.rounded_rectangle([S(60), S(410), S(420), S(530)], radius=S(14), fill=(40, 120, 90), outline=(16, 60, 44), width=iw(5))
    d.text((S(240), S(470)), 'העירייה', font=font(S(56), 900), fill=WHITE, anchor='mm')
    d.rounded_rectangle([S(80), S(560), S(400), S(640)], radius=S(10), fill=(255, 246, 200), outline=(200, 160, 40), width=iw(4))
    d.text((S(240), S(600)), 'מחלקת ארנונה', font=font(S(40), 900), fill=(40, 40, 50), anchor='mm')
    x0, y0, x1, y1 = 600, 400, 1020, 640
    d.rounded_rectangle([S(x0 + 8), S(y0 + 10), S(x1 + 8), S(y1 + 10)], radius=S(20), fill=(160, 168, 184))
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(20), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(6))
    d.line([(S(x1 - 130), S(y0 + 20)), (S(x1 - 130), S(y1 - 20))], fill=(60, 60, 70), width=iw(3))
    d.text((S(x1 - 65), S(y0 + 70)), 'חלון', font=font(S(36), 800), fill=E3.AMBER, anchor='mm')
    d.text((S(x1 - 65), S(y0 + 150)), '3', font=font(S(76), 900), fill=E3.AMBER, anchor='mm')
    return img

JUMPS = [(0.0, '41'), (3.4, '7'), (6.5, '230'), (11.0, '2'), (15.5, '919')]
def board_text(t):
    txt = '41'
    for tj, v in JUMPS:
        if t >= tj: txt = v
    for tj, _ in JUMPS:
        if 0 < tj and 0 <= t - tj < 0.3: return txt, int((t - tj) / 0.07) % 2 == 0
    return txt, True

HX, HY, F = 540, 1010, 1.42
def cat_state(t, i, frozen=False):
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy = 0.0, 0.0
    v = v_of(t, 'cat')
    if frozen:
        u = t - FREEZE
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-20 * math.exp(-u * 4), look=(-16, -10), sweat=1.0, blush=0.0,
                  twitch=(0.1 < u < 0.35 and int(t * 12) % 2 == 0))
        return st, 0.0, -10.0
    if t < L[1]:         # "עוד שלושה אחוז ארנונה? באתי לערער." — indignant, then determined
        u = t - L[0]
        st.update(lid=0.0, pupil='tiny' if u < CS[0][1] else 'big', brow='annoyed' if u < CS[0][1] else 'up',
                  mouth=cat_mouth(t, rest='squish', loud='w'), ear_dy=-18, look=(0, 0), sweat=0.6 if u < CS[0][1] else 0.0)
        dy = -12 * v; rot = 5 * math.sin(u * 9) * math.exp(-max(0, u - CS[0][1]) * 2) if u >= CS[0][1] else -3
    elif t < L[7]:       # "רק אני והחטיפים." — sheepish grin, snacks piled up
        u = t - L[4]
        st.update(lid=0.35, pupil='normal', brow='sad', mouth=cat_mouth(t, rest='goofy', loud='smile'), blush=0.9, ear_droop=0.3, look=(-10, 6))
        if t >= CHK2: st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-16, blush=1.0, look=(0, -4)); dy = -20 * abs(math.sin((t - CHK2) * 7)) * math.exp(-(t - CHK2) * 2)
        rot = 3 * math.sin(t * 3)
    else:                # "עשרים וחמישה?! שרית, את מלכה!" — ecstatic
        u = t - L[8]
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-26, blush=1.0, look=(-12, -6))
        dy = -50 * abs(math.sin(u * 6.5)) * math.exp(-u * 0.8); rot = 6 * math.sin(u * 11) * math.exp(-u * 1.2)
    return st, rot, dy

def scene_cat(t, i, frozen=False):
    img = IRIYA.copy()
    txt, on = board_text(t)
    E3.led_text(img, txt, 735, 520, 140 if len(txt) < 3 else 112, on)
    cheer = t >= CHK3 or (L[4] <= t and t >= CHK2 and t < L[7])
    mood = 2 if frozen else (1 if cheer else 0)
    for name, x, y, sc, ph in E13.BACK:
        hop = -26 * abs(math.sin(t * 7 + ph)) if mood == 1 else 0
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph), y + hop + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    for name, x, y, sc, ph in E13.MID:
        hop = -30 * abs(math.sin(t * 6 + ph)) if mood == 1 else 0
        E13.paste_sprite(img, name, mood, x + 8 * math.sin(t * 3.4 + ph), y + hop + 12 * math.sin(t * 5 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state(t, i, frozen)
    E(d, HX, 1660 + 0.5 * dy, 430, 460, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1720 + 0.5 * dy, 200, 310, fill=CREAM)
    # snack bags piled beside him (the "יחיד" answer), from L04 on
    if t >= L[4] - 0.06 and not frozen or (frozen):
        for k, (bx, by, a) in enumerate(((150, 1560, -14), (250, 1600, 10), (120, 1690, 6), (300, 1720, -8), (200, 1500, 18))):
            SH.snack_bag(d, (bx, by), a, 1.0)
    # left paw (viewer's right): ticket with the live number
    lp = (HX + 175, 1360 + 8 * math.sin(t * 2.0) + 0.5 * dy)
    if t >= L[8] and not frozen: lp = (HX + 300, 980 + 0.6 * dy)                # fist pump on "את מלכה!"
    capsule(d, (HX + 230, 1440 + 0.5 * dy), lp, 110, FUR, OUT, 4)
    if lp[1] > 1100:
        tk = xform([(-48, -78), (48, -78), (48, 78), (-48, 78)], lp[0] + 10, lp[1] - 120, 8)
        poly(d, tk, fill=(252, 250, 242), outline=(150, 150, 140), width=3)
        c_ = xform([(0, -20)], lp[0] + 10, lp[1] - 120, 8)[0]
        d.text((S(c_[0]), S(c_[1])), str(QUEUE), font=font(S(40), 900), fill=INK, anchor='mm')
    # right paw (viewer's left): the bill (L00 slapped toward camera)
    bill_on = t < L[1] or frozen or t >= L[8]
    if bill_on:
        if t < L[1]:
            e = ease_out(clamp((t - (SLAP - 0.15)) / 0.15))
            bc, ba, bs = lerp2((300, 1300), (250, 1160), e), lerp(-20, -6, e), lerp(0.9, 1.15, e)
        else:
            bc, ba, bs = (300, 1150 + 0.4 * dy), -8, 1.0
        rp = (bc[0] + 40, bc[1] + 150 * bs)
        capsule(d, (HX - 230, 1440 + 0.5 * dy), rp, 110, FUR, OUT, 4)
    else:
        rp = (HX - 175, 1360 + 8 * math.sin(t * 2.0) + 0.5 * dy)
        capsule(d, (HX - 230, 1440 + 0.5 * dy), rp, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HX, HY + dy, F, rot)
    d = ImageDraw.Draw(img)
    if bill_on:
        E26.paste_rot(img, BILL_CUT if (t >= CHK3 or frozen) else BILL, bc, ba, bs)
        d = ImageDraw.Draw(img)
    E12.big_paw(d, rp, 10 if rp[1] > 1100 else 170, 0.9)
    E12.big_paw(d, lp, -10 if lp[1] > 1100 else -170, 0.9)
    if t < L[1] and t >= SLAP: E26.burst(img, (250, 1160), t - SLAP, (255, 255, 255), 180, 10, 0.3)
    if CHK2 <= t < L[7]: E26.burst(img, (HX, 900), t - CHK2, (255, 236, 120), 320, 12, 0.5)
    if t >= L[8] and not frozen:
        E26.confetti(img, t - L[8] + 0.6)
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)   # little crown sparkles around his head
        for k in range(6):
            a = math.radians(k * 60 + t * 90); r = 360
            poly(od, m.star(HX + r * math.cos(a), 880 + 0.6 * r * math.sin(a), 26 + 8 * math.sin(t * 9 + k), 4, 0.3, -90), fill=(255, 236, 120, 230))
        img.alpha_composite(ov)
    return img

# ------------------------------------------------------------------ Sharit (customer POV): both hands typing, clock + sign, stamp, break
def sh_state(t, i):
    st = SH.base(); st.update(lid=0.5, red=0.8, hand_l=(190, 700))
    v = v_of(t, 'sh')
    st['mouth'] = 'talk' if v > 0.12 else 'grin'
    glance = any(a <= t < b for a, b in GLANCE)
    if t < L[3]:                       # L01: both hands typing in a blur
        k = (i // 2) % 2
        st.update(finger=False, hand_r=(560, 712 + (14 if k else 0)), hand_l=(190, 712 + (0 if k else 14)), look=(6, 14), blush=0.6, rot=2 * math.sin(t * 20))
    elif t < L[9]:                     # L07: "הנחת יחיד. 25%!" leaning in, big grin
        st.update(look=(0, 2), lid=0.42, blush=0.9, rot=-4 * math.sin((t - L[7]) * 3))
    elif t < DING:                     # L09 + hold: the stamp raised high
        st.update(look=(0, -6), lid=0.4, blush=0.7, hand_r=(560, 400), rot=0.0)
        if t >= HOLD[0]: st['mouth'] = 'grin'
    else:                              # break: sets it down, flat, "...הפסקה."
        st.update(look=(10, 8), lid=0.72, red=1.0, blush=0.3, hand_r=(560, 760), snack=True, rot=0.0)
    if glance: st.update(look=(24, -22), rot=6)
    return st

def sh_offset(t):
    if t < EXIT[0]: return 0.0, 0.0
    e = ease_in(clamp((t - EXIT[0]) / (EXIT[1] - EXIT[0]))); return 760 * e, -120 * math.sin(math.pi * e * 0.5)

def scene_sh(t, i):
    img = E3.OFFICE.copy(); d = ImageDraw.Draw(img)
    if t >= EXIT[0]: E3.chair(d, t - EXIT[0] + E3.EXIT[0])
    ox, oy = sh_offset(t)
    if t < EXIT[1]:
        img.alpha_composite(SH.draw(sh_state(t, i), i), dest=(int(S(E3.SH_POS[0] + ox)), int(S(E3.SH_POS[1] + oy))))
    d = ImageDraw.Draw(img)
    # the stamp in her raised hand (peak) or on the desk (break, unstamped)
    if L[9] - 0.06 <= t < DING:
        u = t - (L[9] - 0.06)
        stamp_prop(d, (E3.SH_POS[0] + 560 + ox, E3.SH_POS[1] + lerp(700, 330, ease_out(clamp(u / 0.3))) - 10 * math.sin(t * 3)), 0, 1.1)
    elif t >= DING:
        stamp_prop(d, (720, 1290), 0, 1.0)
    if t < L[3]:   # papers flying out as she types
        u = t - L[1]
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(5):
            pu = (u * 1.6 + k * 0.21) % 1.0
            px, py = 540 + 380 * pu * (1 if k % 2 else -1), 1080 - 500 * pu + 300 * pu * pu
            poly(od, xform([(-40, -52), (40, -52), (40, 52), (-40, 52)], px, py, pu * 300 + k * 40), fill=(252, 252, 246, int(240 * (1 - pu))), outline=(150, 150, 150, int(240 * (1 - pu))), width=2)
        img.alpha_composite(ov)
        # blur streaks on her hands
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(6):
            y = 1180 + k * 18; line(od, [(260 + 30 * (k % 2), y), (820 - 30 * (k % 2), y)], (255, 255, 255, 120), 6)
        img.alpha_composite(ov)
    if t >= DING and t >= EXIT[0]:   # her little cloud (hint level)
        sm = Image.new('RGBA', img.size, (0, 0, 0, 0))
        SH.smoke(ImageDraw.Draw(sm), t, 900, 900, n=6, spread=1.1, alpha=0.8, seed=4, drift=(60, -40))
        img.alpha_composite(sm)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); E3.glass_tint(ImageDraw.Draw(ov)); img.alpha_composite(ov)
    if t >= SIGN_T: E3.break_sign(img, t - SIGN_T + E3.SIGN)
    img.alpha_composite(E3.GLASS_FG)
    wall_clock(ImageDraw.Draw(img), 900, 420, 72, t)
    break_sign_sign(ImageDraw.Draw(img), 235, 470, 1.05)
    if CHK3 <= t < L[8]:   # -25% slams onto the bill on the counter
        u = t - CHK3
        E26.paste_rot(img, BILL, (540, 1560), 4, 1.0)
        E26.paste_rot(img, MINUS25, (540, 1580), -10, 1.6 - 0.6 * ease_out(clamp(u / 0.1)))
    return img

# ------------------------------------------------------------------ two-shot: Sharit typing / asking, his big face; clock + sign between them
T_HEAD = (225, 900); TS = 1.45
HX2, HY2, F2 = 790, 960, 1.45
def scene_two(t, i):
    img = SH_BG.copy(); d = ImageDraw.Draw(img)
    wall_clock(d, 560, 525, 70, t); break_sign_sign(d, 250, 470, 0.85)
    cold = t < COLD_END
    typing = cold or (C(1) <= t < C(3))
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.45, red=0.8, blush=0.8, look=(18, 6))
    st_s['mouth'] = 'talk' if v_of(t, 'sh') > 0.12 else 'grin'
    if typing:
        k = (i // 2) % 2
        st_s.update(hand_r=(540, 700 + (16 if k else 0)), hand_l=(180, 700 + (0 if k else 16)), look=(10, 16), rot=3 * math.sin(t * 22))
        if cold: st_s['mouth'] = 'grin'
        if any(a_ <= t < b_ for a_, b_ in GLANCE): st_s.update(look=(24, -22))
    Ls = SH.draw(st_s, i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy = 0.0, 0.0
    if cold:   # jaw drop at the two-handed typing
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=cat_mouth(t, rest='w', loud='w'), ear_dy=-24, sweat=1.0, look=(-18, 4))
        rot = 4 * math.sin(t * 18) * math.exp(-t * 1.5); dy = -10 * v_of(t, 'cat')
    elif typing:   # she fills it in for him: delighted, then the ✓
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-14, blush=0.8, look=(-18, 2))
        if t >= CHK1: dy = -24 * abs(math.sin((t - CHK1) * 7)) * math.exp(-(t - CHK1) * 2); st['ear_dy'] = -22
    else:      # "גר לבד, נכון?" — caught, shy
        st.update(lid=0.3, pupil='normal', brow='sad', mouth='goofy', blush=1.0, ear_droop=0.3, look=(-18, 6))
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    if typing:   # keyboard blur + flying papers
        d.rounded_rectangle([S(60), S(1480), S(520), S(1580)], radius=S(12), fill=(60, 62, 70), outline=(30, 30, 36), width=iw(4))
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(5):
            y = 1300 + k * 26; line(od, [(80 + 20 * (k % 2), y), (520 - 20 * (k % 2), y)], (255, 255, 255, 140), 7)
        for k in range(4):
            pu = (t * 1.8 + k * 0.25) % 1.0
            px, py = 300 + 300 * pu, 1300 - 600 * pu + 400 * pu * pu
            poly(od, xform([(-40, -52), (40, -52), (40, 52), (-40, 52)], px, py, pu * 300 + k * 40), fill=(252, 252, 246, int(240 * (1 - pu))))
        img.alpha_composite(ov)
    else:
        for k, (bx, by, a) in enumerate(((620, 1530, -14), (700, 1545, 10), (780, 1520, 6))):
            SH.snack_bag(d, (bx, by), a, 0.8)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('טופס', 860), ('זכאות', 650), ('הנחה', 430), ('חותמת', 215)]
def chips(frame, t):
    if RW[0] <= t < T0 + 0.2: return
    if t < COLD_END: done = [True, False, False, False]; tk = [None] * 4
    else:
        done = [t >= CHK1, t >= CHK2, t >= CHK3, False]; tk = [CHK1, CHK2, CHK3, None]
    drained = t >= DING + 0.15
    d = ImageDraw.Draw(frame)
    y = 330
    gold = done[2] and not drained
    for k, (lab, cx) in enumerate(CHIPS):
        ok = done[k] and not drained
        pulse = (k == 3 and L[9] - 0.06 <= t < DING)
        fill = GOLD if (ok and gold) else ((255, 255, 255) if ok else (40, 42, 52))
        if pulse: fill = lerpc_((40, 42, 52), (255, 140, 40), 0.5 + 0.5 * math.sin(t * 14))
        ink = INK if (ok or pulse) else (190, 194, 206)
        u = t - tk[k] if tk[k] is not None else -1
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else (1.08 + 0.06 * math.sin(t * 14) if pulse else 1.0)
        w, h = 190 * sc, 68 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 20 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 32 * sc
        if ok:
            d.ellipse([bx - 19 * sc, y - 19 * sc, bx + 19 * sc, y + 19 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 17 * sc, y - 17 * sc, bx + 17 * sc, y + 17 * sc], outline=ink, width=4)

def lerpc_(a, b, u): return tuple(int(lerp(x, y, u)) for x, y in zip(a, b))

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
IRIYA = SH_BG = BILL = BILL_CUT = MINUS25 = PILL_EP = PILL_Q = None
def init_all():
    global IRIYA, SH_BG, BILL, BILL_CUT, MINUS25, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    IRIYA = build_iriya_bg()
    E13.build_crowd()
    SH_BG = E3.build_office_bg().filter(ImageFilter.GaussianBlur(S(3)))
    E8.plaque(ImageDraw.Draw(SH_BG), 860, 330, 'העירייה', 260)
    BILL = bill_layer(); MINUS25 = minus25()
    BILL_CUT = BILL.copy(); m.paste_center(BILL_CUT, MINUS25.rotate(-10, resample=Image.BICUBIC, expand=True).resize((S(250), S(160)), Image.BICUBIC), S(150), S(230))
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'two':
        if t < COLD_END: z = 1.22 - 0.16 * ease_out(clamp(t / 0.3)); cx = 560
        else: z = 1.02 + 0.03 * pu
    elif name == 'rewind': z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'cat':
        cy = 900; z = 1.06 + 0.03 * pu
        for s_ in (SLAP, CHK2, L[8] + CS[8][1]):
            u = t - s_
            if 0 <= u < 0.35: z = max(z, 1.06 + 0.10 * math.exp(-u * 9))      # snap-zoom on every strong line
    elif name == 'sh':
        z = 1.14 + 0.03 * pu; cy = 900
        for s_ in (CHK3,):
            u = t - s_
            if 0 <= u < 0.6: z, cy = 1.0, 1000                                   # show the -25% on the bill
        if L[9] - 0.06 <= t < DING: z, cy = 1.0 + 0.06 * ease_out(clamp((t - L[9]) / 0.4)) + (0.10 * ease_io(clamp((t - HOLD[0]) / (HOLD[1] - HOLD[0]))) if t >= HOLD[0] else 0), 760
        if t >= DING: z, cy = 1.0, 880
        if 0 <= t - DING < 0.25: z = 1.0 + 0.12 * math.exp(-(t - DING) * 10)
    elif name == 'frozen':
        z, cy = 1.28 + 0.1 * (t - FREEZE), 900
    if name not in ('rewind',) and a > 0 and pu < 0.2: z = z + 0.08 * (1 - ease_out(pu / 0.2))   # snap-zoom on every cut
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'two': img = scene_two(t, i)
    elif name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_cat(lerp(C(1) - 0.2, T0 + 0.2, ease_in(u)), i)
    elif name == 'cat': img = scene_cat(t, i)
    elif name == 'sh': img = scene_sh(t, i)
    else: img = scene_cat(t, i, frozen=True)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.4: shake = 16 * math.exp(-t * 6)
    if 0 <= t - SLAP < 0.3: shake = max(shake, 12 * math.exp(-(t - SLAP) * 9))
    if 0 <= t - DING < 0.3: shake = max(shake, 10 * math.exp(-(t - DING) * 9))
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < DING:     # the hush + heartbeat pulse
        k = clamp((t - HOLD[0]) / 0.12)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.04 + 0.2 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(55 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CHK3, DING):
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
    if name in ('cat', 'frozen', 'two'):
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(28)
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
        for k, f in enumerate((520, 610, 700)):
            tw = tt_(0.5); fr = f + 220 * tw / 0.5
            add(sfx, m.lowpass(np.sin(2 * np.pi * np.cumsum(fr) / SR), 2000) * np.sin(np.pi * tw / 0.5), t0 + 0.08 + k * 0.11, 0.035)
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def typing(t0, t1, g=0.16):
        tk = t0; r = random.Random(3)
        while tk < t1:
            add(sfx, m.highpass(nz(0.02), 2500) * np.exp(-tt_(0.02) * 160), tk, g * r.uniform(0.6, 1.0)); tk += r.uniform(0.035, 0.07)
    # cold open: impact + the two-handed typing storm
    add(sfx, thud(1.0), 0.0); typing(0.0, COLD_END, 0.18)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    mur = m.bandpass(nz(HOLD[0]), 200, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * tt_(HOLD[0]))); add(sfx, mur, 0.0, 0.025)
    for name, a, b in SHOTS[2:]: whoosh(a)
    add(sfx, m.highpass(nz(0.08), 1200) * np.exp(-tt_(0.08) * 60), SLAP, 0.55); add(sfx, thud(0.5), SLAP)
    typing(L[1] + 0.1, L[3] - 0.1, 0.14)
    for k in range(4): add(sfx, m.bandpass(nz(0.12), 800, 5000) * np.sin(np.pi * tt_(0.12) / 0.12) ** 2, L[1] + 0.5 + k * 0.5, 0.05)   # papers
    check(CHK1); check(CHK2); cheer(CHK2 - 0.02, 0.9, 0.12)
    add(sfx, thud(0.9), CHK3); check(CHK3 + 0.08, 0.18, True); cheer(CHK3 + 0.05, 1.6, 0.24)
    cheer(L[8] + CS[8][1], 1.0, 0.18)
    # clock tick through the peak, then hush + heartbeat
    for k in range(int((DING - L[9]) / 0.5) + 1): add(sfx, m.highpass(nz(0.015), 3000) * np.exp(-tt_(0.015) * 200), L[9] + k * 0.5, 0.12)
    heartbeat(HOLD[0] + 0.03); heartbeat(HOLD[0] + 0.23, 0.5)
    # 13:00 DING (the break): one bright bell, then the stamp set down + the sign
    add(sfx, m.tone(1568.0, 1.4, harm=((1, 1), (2.76, 0.25), (5.4, 0.08)), decay=2.4), DING, 0.36)
    add(sfx, thud(0.45), DING + 0.25)
    add(sfx, m.tone(620, 0.5, harm=((1, 1), (1.5, 0.3)), decay=6) * 0.5, SIGN_T + 0.12, 0.12)
    add(sfx, m.bandpass(nz(0.25), 500, 4000) * np.sin(np.pi * tt_(0.25) / 0.25) ** 2, EXIT[0], 0.18)
    add(sfx, m.lowpass(nz(0.9), 900) * np.sin(np.pi * tt_(0.9) / 0.9), EXIT[0] + 0.1, 0.18)
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
        print('DUR', DUR, 'NF', NF, 'COLD', COLD_OFF, COLD_END); print('L', {k: round(v, 2) for k, v in L.items()})
        print('CS', {k: [round(x, 2) for x in v] for k, v in CS.items()})
        print('CHK', round(CHK1, 2), round(CHK2, 2), round(CHK3, 2), 'HOLD', [round(x, 2) for x in HOLD], 'DING', round(DING, 2), 'FREEZE', round(FREEZE, 2))
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep28_contact.png')); print('ok'); return
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
