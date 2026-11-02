#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 26: דרכון תוך 3 ימים (season 6 "סוף סוף" ep 1, VOICED, built 3.11 under §P; experiment voiced_length
arm control_30). Voices = voice bank 2600–2610 (Benji = cat, Delia = Sharit), prepared by voice/ep26_prep.py.
Want: a passport before his Sunday flight. Plant: his boarding pass ("אילת", and in small grey print "טיסת פנים") in his paw
in the cold open, pressed to the glass at L02, in the booth and raised at the peak. Never pointed at.
Climb: urgent appointment STAMP ✓ (תור) → the photo, this time without blinking (ep19 callback) ✓ (תמונה) → "ready in three
days!" ✓✓✓ gold (דרכון), the queue cheers → Sharit hands him the passport, he hugs it. Peak: passport + pass raised like a
trophy, "אילת, אני בא!", hush + heartbeat. Break (never_needed): Sharit, flat, munching: "לאילת? לא צריך דרכון, מותק." —
snap zoom on the pass, the chips drain, frozen face, whip into the cold open (loop).
No music (voiced rule): SFX + lobby murmur only. Serial pills "פרק 26" + live ticket (hud.stage_of, §O4).

  python3 ep26.py times
  python3 ep26.py test 0 0.5 1.9 2.4 3.5 5 7 8 9 10.5 12 14 16.6 17.5 19 21 23 23.8 25 27 28.4 29 30 31.2
  python3 ep26.py render                                  -> out/ep26_passport.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep12 as E12
import ep13 as E13
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep26', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
NL = 11
D = [META[i]['dur'] for i in range(NL)]
YELLOW = (255, 221, 51); PINKSUB = (255, 182, 210); GOLD = (255, 196, 40); GREEN = (40, 170, 80)
QUEUE = int(os.environ.get('QUEUE', '468'))
EP_LABEL = 'פרק 26'
OUTNAME = os.environ.get('OUTNAME', 'ep26_passport')
SPEAKER = {0: 'cat', 1: 'sh', 2: 'cat', 3: 'sh', 4: 'cat', 5: 'sh', 6: 'sh', 7: 'cat', 8: 'sh', 9: 'cat', 10: 'sh'}

# ------------------------------------------------------------------ timeline (from the real line lengths)
COLD_END = round(D[7] + 0.15, 2)          # cold open = L07 "שלושה ימים?! יש!!!" (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.35)          # ◀◀ רגע קודם
T0 = RW[1]
L = [0.0] * NL
t_ = T0 + 0.05
GAPS = {0: 0.10, 1: 0.10, 2: 0.10, 3: 0.15, 4: 0.35, 5: 0.10, 6: 0.10, 7: 0.10, 8: 0.10, 9: 0.50}
for i in range(NL):
    L[i] = t_
    t_ += D[i] + GAPS.get(i, 0.0)
FLASH = L[4] + D[4] + 0.05                # the camera flash right after "...בלי למצמץ."
HOLD = (L[9] + D[9], L[10])               # peak hold: hush + heartbeat
FREEZE = L[10] + D[10]
DUR = round(FREEZE + 0.45, 2)
NF = int(round(DUR * FPS))
OCC = [(7, 0.0)] + [(i, L[i]) for i in range(NL)]

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

SUBS = {
    0: [['אני צריך דרכון.'], ['טס ביום ראשון!']],
    1: [['דרכון?'], ['עוד שלושה שבועות, מותק.']],
    2: [['שלושה שבועות?!'], ['יש לי שלושה ימים!']],
    3: [['אוי, איזה חמוד אתה...'], ['טוב. תור דחוף.']],
    4: [['תמונה.'], ['הפעם... בלי למצמץ.']],
    5: [['יצאת מהמם, מותק.'], ['אושר.']],
    6: [['ובשבילך?'], ['הדרכון מוכן', 'תוך שלושה ימים!']],
    7: [['שלושה ימים?!'], ['יש!!!']],
    8: [['הנה, מותק.'], ['דרכון חדש.']],
    9: [['אילת, אני בא!']],
    10: [['לאילת?'], ['לא צריך דרכון, מותק.']],
}

def chunk_starts(i):
    """start (s, relative) of each subtitle chunk: proportional by text length, snapped to the nearest speech segment"""
    chunks = SUBS[i]; segs = segments(i)
    tot = sum(len(' '.join(c)) for c in chunks); acc = 0; out = []
    for k, c in enumerate(chunks):
        guess = D[i] * acc / tot; acc += len(' '.join(c))
        if k == 0 or not segs: out.append(0.0 if k == 0 else guess); continue
        best = min((s for s, _ in segs if s > out[-1] + 0.2), key=lambda s: abs(s - guess), default=guess)
        out.append(best)
    return out

CS = {i: chunk_starts(i) for i in range(NL)}
def at(i, k): return L[i] + CS[i][k]

CHK1 = at(3, 1)                           # "טוב. תור דחוף." → STAMP ✓ תור
CAL = at(1, 1)                            # "עוד שלושה שבועות" → the wall calendar flips
CHK2 = at(5, 1)                           # "אושר." ✓ תמונה
CHK3 = at(7, 1)                           # "יש!!!" ✓ דרכון, gold
CHK3_COLD = CS[7][1]
REVEAL = at(10, 1) - 0.05                 # "לא צריך דרכון, מותק." → snap to the pass
SLAP = L[2] + 0.22
GIVE = at(8, 1)                           # passport handed over

SUB_TIMES = []
for i0, s0 in OCC:
    for k, c in enumerate(SUBS[i0]):
        a = s0 + max(0.0, CS[i0][k] - 0.05)
        b = s0 + (CS[i0][k + 1] - 0.05 if k + 1 < len(SUBS[i0]) else D[i0] + 0.2)
        if s0 == 0.0 and i0 == 7: b = min(b, COLD_END)
        elif i0 + 1 < NL and s0 > 0: b = min(b, L[i0 + 1] - 0.03)
        SUB_TIMES.append((a, b, c, i0))

C = lambda i: L[i] - 0.08
SHOTS = [('cheer', 0.0, COLD_END), ('rewind', COLD_END, T0), ('runin', T0, C(1)), ('sh', C(1), C(2)), ('win', C(2), C(3)),
         ('sh', C(3), C(4)), ('booth', C(4), C(5)), ('two', C(5), C(6)), ('sh', C(6), C(7)), ('cheer', C(7), C(8)),
         ('two', C(8), C(9)), ('peak', C(9), L[10] - 0.05), ('sh', L[10] - 0.05, REVEAL), ('reveal', REVEAL, DUR + 1)]

TOPCAPS = [(0.0, C(1), ['דרכון תוך 3 ימים?'], 96, 222, WHITE)]   # hook (F16), keyword from frame 1

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def talk(t, i):
    for li, s0 in OCC:
        if li == i and s0 <= t < s0 + D[i]:
            env = META[i]['env']; k = int((t - s0) * FPS)
            return env[k] if k < len(env) else 0.0
    return 0.0

def speaking(t):
    for li, s0 in OCC:
        if s0 <= t < s0 + D[li]: return li
    return None

def cat_v(t):
    li = speaking(t)
    return talk(t, li) if li is not None and SPEAKER[li] == 'cat' else 0.0

def sh_v(t):
    li = speaking(t)
    return talk(t, li) if li is not None and SPEAKER[li] == 'sh' else 0.0

def cat_mouth(t, rest='w', loud='smile'):
    v = cat_v(t)
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

# ------------------------------------------------------------------ props
PASS_W, PASS_H = 330, 180
def pass_layer():
    """the boarding pass: big "אילת", and the small grey "טיסת פנים" that nobody reads"""
    lay = Image.new('RGBA', (S(PASS_W + 16), S(PASS_H + 16)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    o = 8; x1 = o + PASS_W; y1 = o + PASS_H
    d.rounded_rectangle([S(o), S(o), S(x1), S(y1)], radius=S(16), fill=(252, 252, 248), outline=(60, 80, 120), width=iw(4))
    d.rounded_rectangle([S(o), S(o), S(x1), S(o + 46)], radius=S(16), fill=(28, 104, 226))
    d.rectangle([S(o), S(o + 30), S(x1), S(o + 46)], fill=(28, 104, 226))
    d.text((S(x1 - 18), S(o + 24)), 'כרטיס טיסה', font=font(S(28), 900), fill=WHITE, anchor='rm')
    # little plane (drawn, no emoji)
    px, py = o + 40, o + 23
    poly(d, [(px - 22, py), (px + 22, py - 3), (px + 26, py), (px + 22, py + 3)], fill=WHITE)
    poly(d, [(px - 2, py), (px + 8, py - 16), (px + 12, py - 16), (px + 8, py)], fill=WHITE)
    poly(d, [(px - 2, py), (px + 8, py + 16), (px + 12, py + 16), (px + 8, py)], fill=WHITE)
    poly(d, [(px - 20, py), (px - 16, py - 9), (px - 12, py - 9), (px - 14, py)], fill=WHITE)
    # stub line
    for y in range(o + 56, y1 - 6, 14): line(d, [(o + 92, y), (o + 92, y + 7)], (160, 170, 190), 3)
    d.text((S(x1 - 18), S(o + 98)), 'אילת', font=font(S(64), 900), fill=(20, 30, 60), anchor='rm')
    d.text((S(x1 - 18), S(o + 150)), 'יום א׳ · 07:00', font=font(S(28), 800), fill=(60, 70, 96), anchor='rm')
    d.text((S(o + 48), S(o + 150)), 'טיסת פנים', font=font(S(23), 800), fill=(132, 136, 148), anchor='mm')
    d.text((S(o + 48), S(o + 95)), '7A', font=font(S(34), 900), fill=(60, 70, 96), anchor='mm')
    return lay

def passport_layer():
    lay = Image.new('RGBA', (S(220), S(300)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(6), S(6), S(214), S(294)], radius=S(16), fill=(24, 46, 110), outline=(10, 20, 56), width=iw(4))
    d.rectangle([S(22), S(6), S(28), S(294)], fill=(16, 32, 84))
    E(d, 120, 130, 48, 48, outline=(232, 190, 80), width=5)
    poly(d, m.star(120, 130, 30, 6, 0.55, -90), fill=(232, 190, 80))
    d.text((S(120), S(222)), 'דרכון', font=font(S(42), 900), fill=(232, 190, 80), anchor='mm')
    return lay

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    m.paste_center(img, lay, S(c[0]), S(c[1]))

def print_layer():
    """passport photo print: eyes wide open (this time)"""
    PRW, PRH = 260, 320
    lay = Image.new('RGBA', (S(PRW), S(PRH)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(PRW) - 1, S(PRH) - 1], fill=(252, 252, 248), outline=(150, 150, 140), width=iw(3))
    d.rectangle([S(16), S(16), S(PRW - 16), S(PRH - 70)], fill=(214, 226, 240))
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3, lid=0.0, pupil='big', mouth='smile', brow='up', ear_dy=-10)
    E(d, PRW / 2, PRH - 40, 110, 90, fill=FUR, outline=OUT, width=3)
    E12.paste_head(lay, st, 0, PRW / 2, 128, 0.36)
    d = ImageDraw.Draw(lay)
    d.rectangle([0, S(PRH - 54), S(PRW), S(PRH)], fill=(252, 252, 248))
    return lay

def stamp_layer(text, col=(214, 30, 44)):
    f = font(S(84), 900)
    tw = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(text, font=f)
    w, h = int(tw + S(80)), S(140)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(6), S(6), w - S(6), h - S(6)], radius=S(18), outline=col + (235,), width=iw(9))
    d.text((w / 2, h / 2), text, font=f, fill=col + (235,), anchor='mm')
    return lay

def burst(img, c, u, col=(255, 236, 120), r0=150, n=10, dur=0.4):
    if not (0 <= u < dur): return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(n):
        a_ = math.radians(k * 360 / n + 10); ra, rb = r0 + 60 * u, r0 + 80 + 200 * u
        line(od, [(c[0] + ra * math.cos(a_), c[1] + ra * math.sin(a_)), (c[0] + rb * math.cos(a_), c[1] + rb * math.sin(a_))], col + (int(230 * (1 - u / dur)),), 10)
    img.alpha_composite(ov)

CONF = [(random.Random(k).uniform(40, 1040), random.Random(k + 50).uniform(-300, 200), random.Random(k + 9).uniform(0, 6.28),
         [(255, 214, 64), (255, 92, 120), (64, 186, 186), (120, 200, 90), (255, 255, 255)][k % 5]) for k in range(46)]
def confetti(img, u):
    if not (0 <= u < 2.2): return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for x, y0, ph, col in CONF:
        y = y0 + 900 * u + 40 * math.sin(u * 5 + ph); xx = x + 30 * math.sin(u * 3 + ph)
        a = math.degrees(u * 8 + ph)
        poly(od, xform([(-12, -7), (12, -7), (12, 7), (-12, 7)], xx, y, a), fill=col + (230,))
    img.alpha_composite(ov)

# ------------------------------------------------------------------ the lobby (לשכת הדרכונים), camera on the cat
def build_lobby_bg():
    img = E3.wall_gradient(); d = ImageDraw.Draw(img)
    d.rectangle([0, S(1200), W * K, H * K], fill=E3.WAIN)
    d.rounded_rectangle([S(50), S(410), S(440), S(530)], radius=S(14), fill=(28, 70, 150), outline=(14, 36, 80), width=iw(5))
    d.text((S(245), S(470)), 'לשכת הדרכונים', font=font(S(48), 900), fill=WHITE, anchor='mm')
    d.rounded_rectangle([S(70), S(560), S(420), S(640)], radius=S(10), fill=(255, 246, 200), outline=(200, 160, 40), width=iw(4))
    d.text((S(245), S(600)), 'זמן המתנה: 3 שבועות', font=font(S(34), 900), fill=(200, 40, 40), anchor='mm')
    x0, y0, x1, y1 = 600, 400, 1020, 640
    d.rounded_rectangle([S(x0 + 8), S(y0 + 10), S(x1 + 8), S(y1 + 10)], radius=S(20), fill=(160, 168, 184))
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(20), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(6))
    d.line([(S(x1 - 130), S(y0 + 20)), (S(x1 - 130), S(y1 - 20))], fill=(60, 60, 70), width=iw(3))
    d.text((S(x1 - 65), S(y0 + 70)), 'חלון', font=font(S(36), 800), fill=E3.AMBER, anchor='mm')
    d.text((S(x1 - 65), S(y0 + 150)), '3', font=font(S(76), 900), fill=E3.AMBER, anchor='mm')
    return img

# the called number jumps around for no reason (running gag #1 lives on the board, §O4)
JUMPS = [(0.0, '17'), (3.0, '904'), (5.6, '12'), (9.0, '3'), (13.0, '388'), (23.1, '1'), (27.0, '76'), (29.2, '17')]
def board_text(t):
    txt = '17'
    for tj, v in JUMPS:
        if t >= tj: txt = v
    for tj, _ in JUMPS:
        if 0 < tj and 0 <= t - tj < 0.3: return txt, int((t - tj) / 0.07) % 2 == 0
    return txt, True

BACK = E13.BACK; MID = E13.MID
HX, HY, F = 540, 1010, 1.38

def lobby_mode(t):
    """cheer (cold open / L07), runin (L00), peak (L09 + hold), reveal (L10 2nd half)"""
    return shot(t)[0]

def crowd_mood_lobby(t, mode):
    if mode in ('cheer',): return 1
    if mode == 'peak': return 1 if t < HOLD[0] else 2
    if mode == 'reveal': return 1
    return 0

def cheer_u(t):
    """time since the cheer moment ("יש!!!") for the cheer shots"""
    return t - (CHK3_COLD if t < COLD_END else CHK3)

def cat_lobby(t, i, mode):
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy, dx = 0.0, 0.0, 0.0
    v = cat_v(t)
    if mode == 'cheer':
        u = cheer_u(t)
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-20, blush=0.9, look=(0, -4))
        if u < 0:   # "שלושה ימים?!" — disbelief, leaning in
            st.update(pupil='big', mouth=cat_mouth(t, rest='w', loud='w'), sweat=0.0, look=(0, 0))
            dy = -10 * v; rot = 4 * math.sin(t * 9)
        else:       # "יש!!!" — the jump
            dy = -70 * abs(math.sin(u * 6.5)) * math.exp(-u * 0.9); rot = 6 * math.sin(u * 13) * math.exp(-u * 1.2)
            st['ear_dy'] = -26
    elif mode == 'runin':
        u = t - T0
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile_small', loud='smile'), ear_dy=-14, look=(-6, -2), blush=0.6)
        dx = 420 * (1 - ease_out(clamp(u / 0.32))); rot = -10 * (1 - ease_out(clamp(u / 0.45)))
        dy = -14 * abs(math.sin(u * 14)) * math.exp(-u * 2.5) - 8 * v
    elif mode == 'peak':
        u = t - (L[9] - 0.08)
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-24, blush=1.0, look=(0, -10))
        dy = -24 * ease_out(clamp(u / 0.25)); rot = 3 * math.sin(t * 4)
        if t >= HOLD[0]: st.update(mouth='smile', eye_mode='closed'); rot = 0.0   # eyes closed, beaming: the held "this is it"
    else:   # reveal: frozen
        u = t - REVEAL
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-18 * math.exp(-max(0, u) * 4), look=(-14, -6),
                  twitch=(0.2 < u < 0.7 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.3), blush=0.0)
        dy = -24
    return st, rot, dy, dx

def pass_pose_lobby(t, mode, dy):
    """(centre, angle, scale) of the boarding pass in the cat's right paw (viewer's left)"""
    if mode == 'cheer':
        u = cheer_u(t)
        if u < 0: return (300, 1180 + 0.5 * dy), -10 + 5 * math.sin(t * 8), 1.0
        return (250, 820 + 0.6 * dy + 30 * math.sin(u * 13)), -18 + 14 * math.sin(u * 15), 1.0     # waved overhead, flapping
    if mode == 'runin': return (300, 1180 + 0.5 * dy), -12 + 6 * math.sin(t * 11), 1.0
    if mode in ('peak', 'reveal'): return (320, 770 + 0.5 * dy), -10 + (2 * math.sin(t * 6) if t < HOLD[0] else 0), 1.0
    return (300, 1180), -10, 1.0

def scene_lobby(t, i, mode=None):
    mode = mode or lobby_mode(t)
    img = LOBBY.copy()
    txt, on = board_text(t)
    E3.led_text(img, txt, 735, 520, 140 if len(txt) < 3 else 112, on)
    mood = crowd_mood_lobby(t, mode)
    jit = 1.0 if mood == 1 else 0.4
    hush = mode == 'peak' and t >= HOLD[0]
    for name, x, y, sc, ph in BACK:
        hop = -24 * abs(math.sin(t * 7 + ph)) if (mood == 1 and not hush and mode != 'reveal') else 0
        E13.paste_sprite(img, name, mood, x + 6 * math.sin(t * 3 + ph) * jit, y + hop + 10 * math.sin(t * 4.4 + ph) * jit * (0 if hush else 1), sc, flip=x > 540)
    for name, x, y, sc, ph in MID:
        hop = -30 * abs(math.sin(t * 6 + ph)) if (mood == 1 and not hush and mode != 'reveal') else 0
        E13.paste_sprite(img, name, mood, x + 8 * math.sin(t * 3.4 + ph), y + hop + 12 * math.sin(t * 5 + ph) * jit * (0 if hush else 1), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    st, rot, dy, dx = cat_lobby(t, i, mode)
    hx = HX + dx
    E(d, hx, 1660 + 0.5 * dy, 430, 460, fill=FUR, outline=OUT, width=7)
    E(d, hx, 1720 + 0.5 * dy, 200, 310, fill=CREAM)
    # left paw (viewer's right): ticket with the live number, or the passport at the peak
    if mode in ('peak', 'reveal'):
        lp = (hx + 300, 780 + 0.5 * dy + (6 * math.sin(t * 6) if t < HOLD[0] else 0))
        capsule(d, (hx + 250, 1480 + 0.5 * dy), lp, 110, FUR, OUT, 4)
        paste_rot(img, PASSPORT, (lp[0] + 10, lp[1] - 120), 8, 0.95); d = ImageDraw.Draw(img)
        E12.big_paw(d, lp, -170, 0.9)
    else:
        lp = (hx + 175, 1360 + 8 * math.sin(t * 2.0) + 0.5 * dy)
        if mode == 'cheer' and cheer_u(t) >= 0: lp = (hx + 300, 1000 + 0.6 * dy)            # fist pump
        capsule(d, (hx + 230, 1440 + 0.5 * dy), lp, 110, FUR, OUT, 4)
        if not (mode == 'cheer' and cheer_u(t) >= 0):
            tk = xform([(-48, -78), (48, -78), (48, 78), (-48, 78)], lp[0] + 10, lp[1] - 120, 8)
            poly(d, tk, fill=(252, 250, 242), outline=(150, 150, 140), width=3)
            c_ = xform([(0, -20)], lp[0] + 10, lp[1] - 120, 8)[0]
            d.text((S(c_[0]), S(c_[1])), str(QUEUE), font=font(S(40), 900), fill=INK, anchor='mm')
        E12.big_paw(d, lp, -10 if lp[1] > 1100 else -170, 0.9)
    # right paw (viewer's left): the boarding pass, always
    pc, pa, ps = pass_pose_lobby(t, mode, dy)
    rp = (pc[0] + 30, pc[1] + 110) if mode not in ('peak', 'reveal') else (pc[0] + 50, pc[1] + 128)   # grip the bottom edge: the small print stays clear
    capsule(d, (hx - 230, 1440 + 0.5 * dy), rp, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, hx, HY + dy, F, rot)
    paste_rot(img, PASS, pc, pa, ps)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, rp, 10 if rp[1] > 1100 else 170, 0.9)
    if mode == 'cheer':
        u = cheer_u(t)
        if u >= 0: confetti(img, u); burst(img, (HX, 900), u, (255, 236, 120), 360, 12, 0.5)
    if mode == 'runin':   # speed lines while he skids in
        u = t - T0
        if u < 0.45:
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            a = int(220 * (1 - u / 0.45))
            for k in range(7):
                y = 700 + k * 120; x0 = hx + 420 + 60 * (k % 2)
                line(od, [(x0, y), (x0 + 260, y)], (255, 255, 255, a), 10)
            img.alpha_composite(ov)
    if mode == 'peak' and t < HOLD[0]:
        burst(img, (250, 700), t - (L[9] + 0.05), (255, 236, 120), 170, 10, 0.5)
    return img

# ------------------------------------------------------------------ window 3, clerk POV (the cat slaps the pass to the glass)
def scene_win(t, i):
    img = E3.WIN_BG.copy(); d = ImageDraw.Draw(img)
    E3.clock_hands(d, 880, 470, 86, 11 * 3600 + 5 * 60 + t * 20)
    cx = 540
    u = t - L[2]
    v = cat_v(t)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.3)
    st.update(lid=0.0, pupil='tiny' if u < CS[2][1] else 'big', brow='up' if u < CS[2][1] else 'sad', ear_dy=-18 if u < CS[2][1] else -6,
              mouth=cat_mouth(t, rest='w', loud='w' if u < CS[2][1] else 'smile'), look=(0, 0), sweat=1.0 if u < CS[2][1] else 0.3)
    E3.draw_body(d, cx, 1.0, feet=False)
    capsule(d, (cx + 122, 1180), (cx + 170, 1330), 62, FUR, OUT, 3)
    e = ease_in(clamp((t - (SLAP - 0.2)) / 0.2))
    lp = lerp2((cx - 200, 860), (cx - 150, 1040), e)
    capsule(d, (cx - 122, 1180), lp, 62, FUR, OUT, 3)
    shake = 10 * math.sin(t * 70) * math.exp(-(t - SLAP) * 7) if t >= SLAP else 0
    E3.composite_head(img, st, i, cx + shake, 960 - 10 * v)
    d = ImageDraw.Draw(img)
    # the pass slapped flat against the glass (readable for ~0.6 s+)
    pc = (lerp(330, 320, e), lerp(900, 1190, e))
    paste_rot(img, PASS, pc, lerp(-20, -4, e), lerp(1.0, 1.3, e))
    d = ImageDraw.Draw(img)
    m.draw_paw(d, (pc[0] + 120, pc[1] + 40), ang=-8)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = E3.WIN
    od.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=(210, 230, 245, 38))
    for k, (a_, b_) in enumerate(((x0 + 60, x0 + 140), (x0 + 190, x0 + 220))):
        poly(od, [(a_, y1), (b_, y1), (b_ + 300, y0), (a_ + 300, y0)], fill=(255, 255, 255, 34 if k == 0 else 26))
    img.alpha_composite(ov)
    img.alpha_composite(E3.WIN_FG)
    SH.snack_bag(ImageDraw.Draw(img), (180, 1560), 12, 1.1)
    if t >= SLAP: burst(img, (pc[0], pc[1]), t - SLAP, (255, 255, 255), 170, 10, 0.3)
    return img

# ------------------------------------------------------------------ Sharit at window 3 (customer POV)
def calendar(img, t):
    """wall calendar: 5 → flips three weeks → 26 on "עוד שלושה שבועות"""
    d = ImageDraw.Draw(img)
    cx, cy = 178, 650
    d.rectangle([S(cx - 98), S(cy - 96), S(cx + 98), S(cy + 112)], fill=(250, 250, 246), outline=(120, 120, 130), width=iw(4))
    d.rectangle([S(cx - 98), S(cy - 96), S(cx + 98), S(cy - 46)], fill=(210, 40, 46))
    d.text((S(cx), S(cy - 71)), 'נובמבר', font=font(S(34), 900), fill=WHITE, anchor='mm')
    u = t - CAL
    if u < 0: num = '5'
    elif u < 0.6: num = str(5 + int(21 * u / 0.6))
    else: num = '26'
    d.text((S(cx), S(cy + 30)), num, font=font(S(96), 900), fill=(30, 30, 40), anchor='mm')
    if 0 <= u < 0.6:   # flying page
        k = (u * 10) % 1
        pts = [(cx - 98, cy - 46), (cx + 98, cy - 46), (cx + 98 - 60 * k, cy + 112 - 260 * k), (cx - 98 + 20 * k, cy + 112 - 300 * k)]
        poly(d, pts, fill=(240, 240, 232), outline=(150, 150, 150), width=2)

def sh_state(t, i):
    st = SH.base(); st.update(lid=0.55, red=0.8, hand_l=(190, 700))
    v = sh_v(t)
    st['mouth'] = 'talk' if v > 0.12 else 'grin'
    li = speaking(t)
    if L[1] - 0.1 <= t < L[2]:          # "דרכון? עוד שלושה שבועות" — munching, unbothered
        st.update(snack=True, look=(6, 6), rot=3 * math.sin(t * 2))
        if v <= 0.12: st['mouth'] = 'munch'
    elif L[3] - 0.1 <= t < L[4]:        # "אוי, איזה חמוד אתה... טוב. תור דחוף." + STAMP
        st.update(blush=0.9, look=(0, 2), lid=0.5)
        u = t - CHK1
        if -0.25 <= u < 0.25:
            st['hand_r'] = lerp2((545, 600), (560, 820), ease_in(clamp((u + 0.25) / 0.25))) if u < 0 else (560, 820)
        if t < CHK1 - 0.3: st['rot'] = -6 * math.sin((t - L[3]) * 2.5)
    elif L[6] - 0.1 <= t < L[7]:        # "ובשבילך? ... תוך שלושה ימים!" — leans in, wink
        st.update(blush=1.0, look=(0, 0), lid=0.45, rot=5 * math.sin((t - L[6]) * 3))
        if at(6, 1) <= t < at(6, 1) + 0.25: st['blink'] = True
    else:                                 # the break: flat, munching, heavy lids
        st.update(snack=True, lid=0.72, red=1.0, look=(4, 10), rot=0.0, blush=0.3)
        if v <= 0.12: st['mouth'] = 'munch'
    return st

def scene_sh(t, i):
    img = E3.OFFICE.copy()
    if t < L[3]: calendar(img, t)
    img.alpha_composite(SH.draw(sh_state(t, i), i), dest=(int(S(E3.SH_POS[0])), int(S(E3.SH_POS[1]))))
    d = ImageDraw.Draw(img)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); E3.glass_tint(ImageDraw.Draw(ov)); img.alpha_composite(ov)
    img.alpha_composite(E3.GLASS_FG)
    E3.clock_hands(ImageDraw.Draw(img), 900, 420, 66, 11 * 3600 + 6 * 60 + t * 20)
    if L[3] - 0.1 <= t < L[4] and t >= CHK1:   # the urgent stamp on the form
        u = t - CHK1
        d.rectangle([S(320), S(1150), S(760), S(1370)], fill=(252, 252, 246), outline=(150, 150, 150), width=iw(3))
        for k in range(5): line(d, [(360, 1190 + k * 40), (720 - 60 * (k % 2), 1190 + k * 40)], (170, 176, 190), 5)
        sc = 1.8 - 0.8 * ease_out(clamp(u / 0.1))
        paste_rot(img, STAMP_URG, (540, 1265), 8, sc)
    return img

# ------------------------------------------------------------------ photo booth (camera POV): eyelid held open, FLASH
def viewfinder(od, t):
    a = 230
    for (x, y, sx, sy) in ((70, 470, 1, 1), (1010, 470, -1, 1), (70, 1760, 1, -1), (1010, 1760, -1, -1)):
        line(od, [(x, y + sy * 110), (x, y), (x + sx * 110, y)], (255, 255, 255, a), 9)
    if int(t * 3) % 2 == 0: E(od, 980, 1700, 16, 16, fill=(230, 40, 40, 230))

def scene_booth(t, i):
    img = LOBBY_BLUR.copy()
    for name, x, y, sc, ph in BACK:
        E13.paste_sprite(img, name, 0 if t < FLASH else 1, x + 6 * math.sin(t * 3 + ph), y + 10 * math.sin(t * 4.4 + ph), sc, flip=x > 540)
    d = ImageDraw.Draw(img)
    u = t - L[4]
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.5, lid=0.0, pupil='big', brow='up', ear_dy=-16,
                                     mouth=cat_mouth(t, rest='smile', loud='w'), look=(0, 0))
    if t >= FLASH: st.update(pupil='tiny', mouth='smile', brow='up', ear_dy=-24)   # dazzled but OPEN
    twitch = (int(t * 14) % 2 == 0) and t < FLASH and u > CS[4][1]
    if twitch: st['twitch'] = True
    E(d, HX, 1660, 430, 460, fill=FUR, outline=OUT, width=7)
    E(d, HX, 1720, 200, 310, fill=CREAM)
    # left paw (viewer's right): the pass, low
    bp = (HX + 230, 1390 + 8 * math.sin(t * 2.0))
    capsule(d, (HX + 250, 1500), bp, 110, FUR, OUT, 4)
    paste_rot(img, PASS, (bp[0] - 30, bp[1] - 120), 10, 0.9); d = ImageDraw.Draw(img)
    E12.big_paw(d, bp, -10, 0.9)
    # right paw (viewer's left) comes up and holds his eyelid open
    e = ease_out(clamp((u - 0.15) / 0.3))
    rp = lerp2((HX - 260, 1500), (HX - 120, 900), e)
    capsule(d, (HX - 250, 1500), rp, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HX, HY, F, 2 * math.sin(t * 20) if twitch else 0.0)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, (rp[0] + 10, rp[1] - 10), 160, 0.8)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); viewfinder(ImageDraw.Draw(ov), t); img.alpha_composite(ov)
    return img

# ------------------------------------------------------------------ two-shot: Sharit hands over the print / the passport
T_HEAD = (225, 900); TS = 1.45
HX2, HY2, F2 = 790, 960, 1.45
def scene_two(t, i):
    img = SH_BG.copy()
    give = t >= L[8] - 0.1
    st_s = SH.base(); st_s.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.45, red=0.8, blush=0.8, look=(18, 6))
    st_s['mouth'] = 'talk' if sh_v(t) > 0.12 else 'grin'
    Ls = SH.draw(st_s, i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.8)
    rot, dy = 0.0, 0.0
    if not give:   # the photo: proud, then "אושר." ✓
        u = t - CHK2
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-12, look=(-18, 2))
        dy = -6 * abs(math.sin(t * 6))
        if u >= 0: dy = -30 * abs(math.sin(u * 7)) * math.exp(-u * 1.5); st.update(ear_dy=-24, blush=1.0)
    else:          # the passport: grabs it and hugs it
        u = t - GIVE
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-16, look=(-18, 4))
        if u >= 0.15: st.update(eye_mode='closed', mouth='smile', blush=1.0, look=(0, 0)); rot = 5 * math.sin(u * 5)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1700)], radius=S(16), fill=(200, 204, 212), outline=(130, 136, 148), width=iw(5))
    if not give:
        u = t - L[5]
        sc = lerp(1.15, 1.5, ease_out(clamp(u / 0.2)))
        paste_rot(img, PRINT_OK, (430, 1250), 6, sc)
        SH.hand(ImageDraw.Draw(img), (430 - 110, 1250 + 170))
        if t >= CHK2:
            uu = t - CHK2; s2 = 1.6 - 0.6 * ease_out(clamp(uu / 0.12)); r = 66 * s2
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            c = (520, 1110)
            E(od, c[0], c[1], r, r, fill=GREEN + (235,), outline=WHITE + (255,), width=6)
            line(od, [(c[0] - 0.45 * r, c[1]), (c[0] - 0.1 * r, c[1] + 0.35 * r), (c[0] + 0.5 * r, c[1] - 0.35 * r)], WHITE + (255,), int(14 * s2))
            img.alpha_composite(ov)
            burst(img, (HX2, 900), uu, (255, 236, 120), 300, 12, 0.5)
    else:
        u = t - GIVE
        e = ease_io(clamp(u / 0.35))
        pc = lerp2((380, 1250), (HX2 - 20, 1380), e)
        paste_rot(img, PASSPORT, pc, lerp(-8, 10, e), lerp(1.0, 1.15, e))
        d = ImageDraw.Draw(img)
        if u < 0.35: SH.hand(d, (pc[0] - 90, pc[1] + 130))
        if u >= 0.15:   # his paws wrap around it
            for side in (-1, 1): E12.big_paw(d, (pc[0] + side * 120, pc[1] + 40), 90 * side, 0.85)
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            for k in range(3):   # little hearts drifting up
                hu = (u * 0.8 + k * 0.33) % 1.0
                hx, hy = HX2 - 160 + k * 150, 820 - 260 * hu
                a = int(220 * math.sin(math.pi * hu))
                s_ = 16
                E(od, hx - s_, hy, s_, s_, fill=(255, 92, 120, a)); E(od, hx + s_, hy, s_, s_, fill=(255, 92, 120, a))
                poly(od, [(hx - 2 * s_, hy + 4), (hx + 2 * s_, hy + 4), (hx, hy + 2.4 * s_)], fill=(255, 92, 120, a))
            img.alpha_composite(ov)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('תור', 770), ('תמונה', 545), ('דרכון', 320)]
def chips(frame, t):
    if RW[0] <= t < T0 + 0.25: return
    if t < COLD_END: done = [True, True, CHK3_COLD <= t]; gold = done[2]
    else:
        done = [t >= CHK1, t >= CHK2, t >= CHK3]; gold = done[2]
    drained = t >= REVEAL + 0.25
    d = ImageDraw.Draw(frame)
    y = 330
    for k, (lab, cx) in enumerate(CHIPS):
        ok = done[k] and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        tkey = [CHK1, CHK2, CHK3][k] if t >= COLD_END else CHK3_COLD
        u = t - tkey
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        w, h = 200 * sc, 70 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 22 * sc, y), lab, font=font(int(38 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], outline=ink, width=4)

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
LOBBY = LOBBY_BLUR = SH_BG = PASS = PASSPORT = PRINT_OK = STAMP_URG = PILL_EP = PILL_Q = None
def init_all():
    global LOBBY, LOBBY_BLUR, SH_BG, PASS, PASSPORT, PRINT_OK, STAMP_URG, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    LOBBY = build_lobby_bg()
    LOBBY_BLUR = LOBBY.filter(ImageFilter.GaussianBlur(S(2.5)))
    E13.build_crowd()
    SH_BG = E3.build_office_bg().filter(ImageFilter.GaussianBlur(S(3)))
    PASS = pass_layer(); PASSPORT = passport_layer(); PRINT_OK = print_layer(); STAMP_URG = stamp_layer('דחוף')
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'cheer':
        cy = 900
        z = 1.08
        if t < 0.3: z = 1.24 - 0.16 * ease_out(t / 0.3)                      # frame 0: snap pull-back, already moving
        u = cheer_u(t)
        if 0 <= u < 0.4: z = max(z, 1.08 + 0.08 * math.exp(-u * 9))
    elif name == 'rewind':
        z, cx = 1.06, 540.0 + 30 * math.sin(t * 90)
    elif name == 'runin':
        cy = 900; z = 1.05 + 0.03 * pu
    elif name == 'sh':
        z = 1.16 + 0.03 * pu; cy = 880
        if t >= CHK1 and L[3] <= t < L[4]: z, cy = 1.08, 1000                          # show the stamp on the form
        if L[10] - 0.1 <= t: z, cy = 1.28 + 0.04 * pu, 860                            # the flat break line, tighter
    elif name == 'win':
        z = 1.18 + 0.04 * pu; cy = 930
    elif name == 'booth':
        cy = 940; z = 1.04 + 0.05 * pu
        if t >= FLASH: z = lerp(1.16, 1.04, ease_out(clamp((t - FLASH) / 0.3)))
    elif name == 'two':
        z = 1.0 + 0.03 * pu
    elif name == 'peak':
        cy = 880; z = 1.04 + 0.02 * pu
        if t >= HOLD[0]: z = 1.06 + 0.10 * ease_io(clamp((t - HOLD[0]) / (HOLD[1] - HOLD[0])))   # the slow push of the hold
    elif name == 'reveal':
        e = ease_out(clamp((t - REVEAL) / 0.14))
        z, cx, cy = lerp(1.16, 1.7, e), lerp(540, 370, e), lerp(880, 820, e)                     # snap onto the pass, his face in frame
        if t >= FREEZE - 0.05: z, cx, cy = lerp(1.7, 1.24, ease_in(clamp((t - FREEZE + 0.05) / 0.4))), lerp(370, 540, ease_in(clamp((t - FREEZE + 0.05) / 0.4))), lerp(820, 900, ease_in(clamp((t - FREEZE + 0.05) / 0.4)))
    if name not in ('rewind', 'cheer', 'reveal') and pu < 0.2: z = z + 0.07 * (1 - ease_out(pu / 0.2))   # snap-zoom on every cut
    if name == 'cheer' and a > 0 and pu < 0.2: z = z + 0.07 * (1 - ease_out(pu / 0.2))
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name in ('cheer', 'runin', 'peak', 'reveal'): img = scene_lobby(t, i)
    elif name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_lobby_rewind(lerp(C(1) - 0.2, T0 + 0.3, ease_in(u)), i)
    elif name == 'sh': img = scene_sh(t, i)
    elif name == 'win': img = scene_win(t, i)
    elif name == 'booth': img = scene_booth(t, i)
    else: img = scene_two(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 18 * math.exp(-t * 5)
    if name == 'cheer' and 0 <= cheer_u(t) < 0.4: shake = max(shake, 12 * math.exp(-cheer_u(t) * 6))
    if name == 'reveal' and t - REVEAL < 0.3: shake = 10 * math.exp(-(t - REVEAL) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if name == 'peak' and t >= HOLD[0]:     # the hush: everything but him dims a touch, heartbeat pulse
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.24 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(60 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if FLASH <= t < FLASH + 0.22:
        frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(235 * (1 - (t - FLASH) / 0.22) ** 1.5))))
    for s_ in (CHK1, REVEAL):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:   # whip out -> loops into the cold open
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    chips(frame, t)
    for t0, t1, lines, size, yc, fill in TOPCAPS:
        if t0 <= t < t1:
            cap = m.caption_layer(lines, size, fill)
            m.paste_center(frame, cap, W / 2, yc)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            cap = sub_layer(lines, PINKSUB if SPEAKER[li] == 'sh' else WHITE)
            m.paste_center(frame, cap, W / 2, 1450 if len(lines) == 1 else 1420)
    if name in ('cheer', 'runin', 'peak', 'reveal', 'booth'):   # serial markers (§O3); the ticket flickers in the last second
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0):
            frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

def scene_lobby_rewind(ts, i):
    """the rewind scrubs back through the run-in"""
    return scene_lobby(ts, i, 'runin')

# ------------------------------------------------------------------ audio (voices + SFX + lobby murmur; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(26)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:02d}.npy')).astype(np.float64)
        add(voice, y, s0, 0.95 if SPEAKER[i0] == 'cat' else 0.9)
    def whoosh(t0, g=0.06, wl=0.16): add(sfx, m.bandpass(nz(wl), 600, 5000) * np.sin(np.pi * tt_(wl) / wl) ** 2, t0 - 0.08, g)
    def thud(g=0.9):
        tt = tt_(0.45); freq = 150 * np.exp(-tt * 6) + 42
        return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) + m.lowpass(nz(0.45), 420) * np.exp(-tt * 30) * 0.8) * g
    def cheer(t0, ln=1.6, g=0.22):
        tt = tt_(ln); env = np.minimum(1, tt / 0.06) * np.exp(-tt * 1.6)
        sig = m.bandpass(nz(ln), 300, 3200) * env * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt))
        add(sfx, sig, t0, g)
        for k, f in enumerate((520, 610, 700)):   # a few "woo"s
            tw = tt_(0.5); fr = f + 220 * tw / 0.5
            add(sfx, m.lowpass(np.sin(2 * np.pi * np.cumsum(fr) / SR), 2000) * np.sin(np.pi * tw / 0.5), t0 + 0.08 + k * 0.11, 0.035)
    def check(t0, g=0.18, gold=False):
        notes = (659.3, 784.0, 1046.5) + ((1318.5,) if gold else ())
        for k, f in enumerate(notes): add(sfx, m.tone(f, 0.5, harm=((1, 1), (2, 0.3)), decay=6), t0 + k * 0.06, g)
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    # cold open: impact + the cheer on "יש!!!"
    add(sfx, thud(1.0), 0.0); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), 0.0, 0.4)
    check(CHK3_COLD, 0.16, True); cheer(CHK3_COLD - 0.05, 1.4, 0.2)
    # rewind tape
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    # run-in skid
    add(sfx, m.bandpass(nz(0.35), 1500, 7000) * np.exp(-tt_(0.35) * 7), T0, 0.12)
    # lobby murmur (room tone) everywhere except the hush
    mur_len = HOLD[0]; mur = m.bandpass(nz(mur_len), 200, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * tt_(mur_len)))
    add(sfx, mur, 0.0, 0.025)
    mur2 = m.bandpass(nz(DUR - HOLD[1] + 0.3), 200, 1400); add(sfx, mur2, HOLD[1], 0.02)
    # cuts
    for name, a, b in SHOTS[2:]:
        if name not in ('reveal',): whoosh(a)
    # calendar flutter on "עוד שלושה שבועות"
    for k in range(9): add(sfx, m.bandpass(nz(0.05), 1200, 6000) * np.exp(-tt_(0.05) * 50), CAL + k * 0.065, 0.12)
    # slap to the glass
    add(sfx, m.highpass(nz(0.08), 1200) * np.exp(-tt_(0.08) * 60), SLAP, 0.55); add(sfx, thud(0.5), SLAP)
    # STAMP דחוף ✓1
    add(sfx, thud(1.0), CHK1); check(CHK1 + 0.1)
    # booth: charge whine + flash pop
    cl = 0.7; tc = tt_(cl); add(sfx, np.sin(2 * np.pi * np.cumsum(2000 + 3000 * tc / cl) / SR) * (tc / cl), FLASH - cl, 0.05)
    add(sfx, m.highpass(nz(0.12), 2000) * np.exp(-tt_(0.12) * 30), FLASH, 0.5)
    # ✓2
    check(CHK2, 0.17)
    # ✓3 gold + cheer
    check(CHK3, 0.18, True); cheer(CHK3 - 0.05, 1.6, 0.24)
    # the passport handed over: swish + small "aww" chord
    add(sfx, m.bandpass(nz(0.2), 800, 5000) * np.sin(np.pi * tt_(0.2) / 0.2) ** 2, GIVE - 0.1, 0.08)
    for k, f in enumerate((523.3, 659.3, 784.0)): add(sfx, m.tone(f, 0.9, harm=((1, 1), (2, 0.2)), decay=3), GIVE + 0.15 + k * 0.03, 0.05)
    # peak: short cheer on "אני בא!", then hush + heartbeat
    cheer(L[9] + 0.6, 0.6, 0.14)
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.05 + 0.28, 0.5)
    # break: one low "dun" + the snap zoom hit
    add(sfx, thud(0.9), REVEAL)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), REVEAL + 0.02, 0.32)
    out = voice + sfx
    out = out[:int(DUR * SR)]
    wl_ = 0.3; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.28)
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
    if mode == 'times':
        print('DUR', DUR, 'NF', NF); print('L', [round(x, 2) for x in L]); print('D', D)
        print('CS', {k: [round(x, 2) for x in v] for k, v in CS.items()})
        print('CHK', round(CHK1, 2), round(CHK2, 2), round(CHK3, 2), 'FLASH', round(FLASH, 2), 'HOLD', [round(x, 2) for x in HOLD], 'REVEAL', round(REVEAL, 2))
        for s in SHOTS: print(s[0], round(s[1], 2), round(s[2], 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames):
            sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep26_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'{OUTNAME}_audio.wav'); build_audio(wav); print('audio ok')
    if mode == 'audio': return
    mp4 = os.path.join(OUTDIR, f'{OUTNAME}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count() or 2, initializer=_init_worker) as pool:
        for k, b in enumerate(pool.imap(_render, range(NF), chunksize=4)):
            proc.stdin.write(b)
            if k % 150 == 0: print('frame', k, '/', NF, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
