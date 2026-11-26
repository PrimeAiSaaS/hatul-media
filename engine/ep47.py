#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 47: טסט — Series 2 "שוקו והג׳ינג׳י", season 1 "על הכביש", ep4 (VOICED, built 27.11 under §P,
~21–23 s). CONTROL arm of the music experiment: no music (voices + SFX only).
Voices = voice bank 2026-11-23 lines 4700–4707 (Benji = the ginger, Knox = Shoko, Delia = Sharit), voice/ep47_prep.py.
Set: the driving-test car (a "ל" sign on the roof). Interior through the windshield: the ginger DRIVES (image right),
Sharit the examiner in the passenger seat (image left) with a clipboard and the stamp; Shoko in the back seat (the next
examinee) cracking sunflower seeds. Cut-outs: side view pulling out, the rear-view mirror insert, a top-down parallel
park, the form insert (the break), the side view on the sidewalk (the tag).
Want: pass his third driving test (the clipboard: "ניסיון 3"). Stakes: a fourth test.
Plant: his seatbelt hanging unbuckled by the door (image right), in frame 0 and again on the signal shot. Never pointed at.
Clock: "הטסט נגמר בעוד 00:SS", real seconds, hits 00:00 on the stamp (the break).
Climb: "טסט שלישי. הפעם אני עובר." → "סע, מותק." → mirror ✓ (מראות) → signal ✓ (איתות) → "חניה במקביל, חמוד." the
perfect parallel park in one move ✓ gold (חניה); Sharit's eyebrows go up; from the back Shoko: "אחי, תנשום."
Peak: Sharit lifts the stamp: "עברת, מות... רגע." heartbeat — her eyes slide to the door.
Break (plant_payoff): "לא חגרת. נכשל, מותק." — the red stamp "נכשל" on a sheet of green checks, the buckle dangling.
Tag (wrong_one_wins): Shoko's turn — onto the sidewalk, a cone flies over the roof; "עברת, חמוד." Shoko winks.

  python3 voice/ep47_prep.py
  python3 ep47.py times | test t1 t2 ... | render   -> out/ep47_test.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep3 as E3
import ep13 as E13
import ep18 as E18
import ep44 as B
import hud as HUD
import clock_overlay as C
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, clamp, epoly, xform,
                        ease_io, ease_out, ease_in, font, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep47', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); ORANGE = (240, 140, 30)
SHARIT_SUB = (255, 182, 210); SHOKO_SUB = (190, 230, 120)
QUEUE = int(os.environ.get('QUEUE', '434'))
EP_LABEL = 'פרק 47'
SERIES_LABEL = 'שוקו והג׳ינג׳י'
OUTNAME = os.environ.get('OUTNAME', 'ep47_test')
LIMIT = float(os.environ.get('LIMIT', '0'))
GINGER, SHOKO = B.GINGER, B.SHOKO
paw, car_side = B.paw, B.car_side

def head(img, st, i, hx, hy, f, rot=0.0, pal=GINGER, props=False, wob=0.0, wink=False):
    B.palette(pal)
    Lh, _ = m.draw_head(st, i)
    dl = ImageDraw.Draw(Lh)
    if wink:                                         # one eye shut (image right eye), a sly arc
        ex, ey = m.EYE_R
        E(dl, ex, ey, 47, 53, fill=pal['FUR'])
        dl.arc([S(ex - 34), S(ey - 18), S(ex + 34), S(ey + 22)], 200, 340, fill=pal['OUT'], width=iw(8))
    if props: B.shades(dl); B.toothpick(dl, wob)
    B.palette(GINGER)
    if abs(rot) > 1e-3: Lh = Lh.rotate(rot, resample=Image.BICUBIC, center=(260 * K, 245 * K))
    sz = int(520 * K * f)
    Lh = Lh.resize((sz, sz), Image.BICUBIC)
    img.alpha_composite(Lh, dest=(int(S(hx) - 260 * K * f), int(S(hy) - 245 * K * f)))

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

# ------------------------------------------------------------------ timeline
COLD_END = round(D[0] + 0.25, 2)            # cold open = 4700 "מראה. איתות. מראה. מושלם." (tight on him, dutch)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "טסט שלישי. הפעם אני עובר." (clipboard: ניסיון 3)
L[2] = L[1] + D[1] + 0.10                   # Sharit: "סע, מותק."
ROAD1 = L[2] + D[2] + 0.05                  # side view: the test car pulls out, the ל sign
MIRROR = ROAD1 + 1.10                       # insert: the rear-view mirror (Shoko cracking seeds in it)
L['0b'] = MIRROR + 0.05                     # "מראה. איתות. מראה. מושלם." in context (= the cold open)
CHK1 = L['0b'] + ss(0, 0) + 0.20            # מראות ✓ on the first "מראה"
INTSIG = L['0b'] + ss(0, 1) - 0.06          # cut to the interior: the blinker (the belt hanging, plant again)
CHK2 = L['0b'] + ss(0, 1) + 0.12            # איתות ✓
PARK = L['0b'] + D[0] + 0.06                # top-down: the parallel park
L[3] = PARK + 0.10                          # Sharit (voice): "חניה במקביל, חמוד."
MOVE = (L[3] + D[3] - 0.30, L[3] + D[3] + 1.25)
CHK3 = MOVE[1]; GOLDT = CHK3 + 0.04         # חניה ✓ gold — one move, perfect
INT3 = CHK3 + 0.55                          # interior: Sharit's eyebrows up; Shoko from the back
L[4] = INT3 + 0.25                          # Shoko: "אחי, תנשום."
PEAK = L[4] + D[4] + 0.12                   # Sharit lifts the stamp
L[5] = PEAK + 0.05                          # "עברת, מות... רגע."
HOLD = (L[5] + D[5] + 0.02, L[5] + D[5] + 0.44)   # heartbeat — her eyes slide to the door
L[6] = HOLD[1]                              # "לא חגרת. נכשל, מותק."
BREAK = L[6] + 0.64                         # the stamp slams on "נכשל" (env: "לא חגרת" 0.07–0.57, "נכשל" from ~0.65) — 00:00
ZERO = BREAK
INSERT_END = BREAK + 0.95
TAG = L[6] + D[6] + 0.08                    # Shoko's turn: onto the sidewalk, a cone over the roof
L[7] = TAG + 0.45                           # Sharit: "עברת, חמוד."
WINK = L[7] + D[7] - 0.20                   # Shoko at the wheel winks at the camera; the ginger frozen in the back
FREEZE = WINK + 0.85
DUR = round(FREEZE + 0.33, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (0, L['0b']), (3, L[3]), (4, L[4]), (5, L[5]), (6, L[6]), (7, L[7])]
SPEAKER = {0: 'cat', 1: 'cat', 4: 'shoko', 2: 'sh', 3: 'sh', 5: 'sh', 6: 'sh', 7: 'sh'}

SUBS = {
    0: [['מראה. איתות.'], ['מראה. מושלם.']],
    1: [['טסט שלישי.'], ['הפעם אני עובר.']],
    2: [['סע, מותק.']],
    3: [['חניה במקביל, חמוד.']],
    4: [['אחי, תנשום.']],
    5: [['עברת, מות...'], ['רגע.']],
    6: [['לא חגרת.'], ['נכשל, מותק.']],
    7: [['עברת, חמוד.']],
}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]
    if len(ch) > 1 and len(SEG[li]) < len(ch): ch = [[' '.join(sum(ch, []))]]
    segs = SEG[li]; n = len(ch)
    idx = [round(k * len(segs) / n) for k in range(n)]
    starts = [0.0] + [ss(li, idx[k]) for k in range(1, n)]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < n else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 5: b = min(b, HOLD[0] + 0.1)
        if li == 7: b = DUR - 0.25
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('car', 0.0, COLD_END), ('rewind', COLD_END, T0), ('car', T0, ROAD1), ('road1', ROAD1, MIRROR), ('mirror', MIRROR, INTSIG),
         ('car', INTSIG, PARK), ('park', PARK, INT3), ('car', INT3, BREAK), ('form', BREAK, INSERT_END), ('car', INSERT_END, TAG),
         ('road3', TAG, WINK), ('wink', WINK, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['טסט שלישי?', 'הפעם עוברים']              # keyword: טסט (the pain in the viewer's words)
TOPCAPS = [(0.0, COLD_END, HOOK), (T0, L[1] + D[1] - 0.1, HOOK)]
HOOK_END = max(t1 for _, t1, _ in TOPCAPS)

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def story_t(t):
    return L['0b'] + t if t < COLD_END else t

def speaking(t):
    for li, s0 in OCC:
        if s0 <= t < s0 + D[li]: return li, s0
    return None

def voice_v(t, who='cat'):
    sp = speaking(t)
    if not sp or SPEAKER[sp[0]] != who: return 0.0
    li, s0 = sp; env = META[li]['env']; k = int((t - s0) * FPS)
    return env[k] if k < len(env) else 0.0

def mouth_of(t, who, rest='flat', loud='w'):
    v = voice_v(t, who)
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

# ------------------------------------------------------------------ states
def ginger_state(t):
    st = E3.base_state(); st.update(red=0.0, blush=0.0, mouth='flat')
    rot, dy = 0.0, 0.0
    s_t = story_t(t)
    if t < COLD_END or (L['0b'] <= t < PARK):                  # the ritual: mirror, signal, mirror, perfect
        u = s_t - L['0b']
        look = (0, -30) if u < ss(0, 1) else ((36, 0) if u < ss(0, 2) else (0, -30))
        st.update(lid=0.0, pupil='big', brow='up', mouth=mouth_of(s_t, 'cat', 'flat', 'w'), ear_dy=-14, sweat=0.7, look=look)
        dy = -8 * voice_v(s_t, 'cat'); rot = 3 * math.sin(s_t * 9)
    elif t < L[2]:                                            # the want: determined
        st.update(lid=0.1, pupil='normal', brow='annoyed', mouth=mouth_of(t, 'cat', 'flat', 'w'), ear_dy=-10, sweat=0.6, look=(0, -6))
        dy = -10 * voice_v(t, 'cat')
    elif t < INT3:
        st.update(lid=0.1, pupil='normal', brow='annoyed', mouth='flat', ear_dy=-10, sweat=0.6, look=(-24, 0))
    elif t < PEAK:                                            # after the park: proud, tense
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile_small', ear_dy=-12, sweat=0.9, look=(-30, 0))
    elif t < HOLD[0] - 0.55:                                  # "עברת..." — joy
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24, sweat=0.4, look=(-34, -10), blush=0.6)
        dy = -18 * math.sin(clamp((t - PEAK) / 0.5) * math.pi)
    elif t < BREAK:                                           # "...רגע." / the hush / "לא חגרת." — he looks down at the door
        u = t - (HOLD[0] - 0.55)
        st.update(lid=0.0, pupil='tiny', brow='up', mouth='flat', ear_dy=-24 + 20 * clamp(u / 0.6), sweat=1.0,
                  look=(lerp(-34, 34, clamp(u / 0.5)), lerp(-10, 30, clamp(u / 0.5))))
        rot = 1.2 * math.sin(t * 30)
    else:                                                     # failed, frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none' if u < 0.9 else 'sad', mouth='flat', ear_droop=clamp((u - 0.4) / 0.8) * 0.7,
                  look=(-10, 10), twitch=(u > 0.9 and int(t * 12) % 2 == 0), sweat=1.0)
    return st, rot, dy

def shoko_state(t, wink=False):
    st = E3.base_state(); st.update(lid=0.55, brow='annoyed', mouth='munch' if int(t * 5) % 2 else 'smile_small', look=(10, 6), red=0.0, blush=0.0)
    v = voice_v(t, 'shoko')
    if v > 0.12: st['mouth'] = 'w' if v > 0.32 else 'smile_small'
    if PEAK <= t < BREAK: st.update(lid=0.5, mouth='goofy', look=(20, 10))
    if wink: st.update(lid=0.35, mouth='goofy', look=(0, 0))
    return st

def sharit_state(t):
    st = SH.base(); st.update(snack=False, mouth='lazy', lid=0.55, look=(14, 4), hand_l=(160, 700), hand_r=(545, 730), rot=0.0)
    v = voice_v(t, 'sh')
    talk = v > 0.12
    if talk: st['mouth'] = 'talk'
    if INT3 <= t < PEAK:                                      # eyebrows up: eyes wide open, a tilt
        st.update(lid=0.12, look=(22, -4), rot=-5)
        if talk: st['mouth'] = 'talk'
    if PEAK <= t < HOLD[0] - 0.55:                            # "עברת, מות..." — the stamp goes up
        st.update(lid=0.35, look=(26, 0), mouth='talk' if talk else 'grin', rot=-3)
    elif HOLD[0] - 0.55 <= t < BREAK:                         # "...רגע." — her eyes slide to the door
        st.update(lid=0.25, look=(30, 22), mouth='talk' if talk else 'lazy', rot=4)
    elif t >= BREAK: st.update(lid=0.6, look=(24, 4), mouth='talk' if talk else 'grin')
    return st

def stamp_pos(t):
    """Sharit's stamp hand (world units of the Sharit layer): resting, raised (peak), then down (break)"""
    rest = (545, 730); up = (560, 330)
    if t < PEAK: return rest, 0.0
    if t < BREAK - 0.12: return (lerp(rest[0], up[0], ease_out((t - PEAK) / 0.35)), lerp(rest[1], up[1], ease_out((t - PEAK) / 0.35))), 1.0
    return rest, 0.0

# ------------------------------------------------------------------ props
def l_sign(d, c, sc=1.0):
    """the learner sign: a white square with a red ל"""
    d.rounded_rectangle([S(c[0] - 46 * sc), S(c[1] - 46 * sc), S(c[0] + 46 * sc), S(c[1] + 46 * sc)], radius=S(8 * sc), fill=(250, 250, 248), outline=(30, 30, 34), width=iw(4))
    d.text((S(c[0]), S(c[1] + 2 * sc)), 'ל', font=font(S(78 * sc), 900), fill=RED, anchor='mm')

def clipboard(img, c, sc, ang, t, n_checks=None):
    """examiner's clipboard: 'טסט מעשי · ניסיון 3' + rows that tick with the chips"""
    lay = Image.new('RGBA', (S(300), S(380)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(10), S(10), S(290), S(370)], radius=S(16), fill=(150, 104, 60), outline=(70, 44, 20), width=iw(5))
    d.rectangle([S(30), S(50), S(270), S(355)], fill=(252, 250, 240))
    d.rounded_rectangle([S(110), S(18), S(190), S(62)], radius=S(8), fill=(190, 192, 200), outline=(80, 80, 90), width=iw(3))
    d.text((S(150), S(86)), 'טסט מעשי', font=font(S(30), 900), fill=INK, anchor='mm')
    d.text((S(150), S(122)), 'ניסיון 3', font=font(S(30), 900), fill=RED, anchor='mm')
    ticks = [CHK1, CHK2, CHK3] if n_checks is None else []
    for k, lab in enumerate(('מראות', 'איתות', 'חניה')):
        y = 170 + k * 52
        d.text((S(254), S(y)), lab, font=font(S(26), 800), fill=(60, 60, 70), anchor='rm')
        d.rectangle([S(46), S(y - 16), S(78), S(y + 16)], outline=(80, 80, 90), width=iw(3))
        ok = (t >= ticks[k]) if ticks else (k < n_checks)
        if ok: line(d, [(48, y), (60, y + 12), (84, y - 16)], (30, 150, 70), 6)
    if n_checks is not None:                                  # the break insert: the belt row, failed
        y = 170 + 3 * 52
        d.text((S(254), S(y)), 'חגורה', font=font(S(26), 900), fill=RED, anchor='rm')
        d.rectangle([S(46), S(y - 16), S(78), S(y + 16)], outline=RED, width=iw(3))
        line(d, [(48, y - 14), (76, y + 14)], RED, 6); line(d, [(48, y + 14), (76, y - 14)], RED, 6)
    lay = lay.resize((int(lay.width * sc), int(lay.height * sc)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(lay, (int(S(c[0]) - lay.width / 2), int(S(c[1]) - lay.height / 2)))

def stamp_tool(d, c, sc=1.0, face='עבר', col=GREEN):
    d.rounded_rectangle([S(c[0] - 26 * sc), S(c[1] - 90 * sc), S(c[0] + 26 * sc), S(c[1] - 20 * sc)], radius=S(12 * sc), fill=(120, 70, 40), outline=(50, 26, 10), width=iw(4))
    d.rounded_rectangle([S(c[0] - 70 * sc), S(c[1] - 24 * sc), S(c[0] + 70 * sc), S(c[1] + 24 * sc)], radius=S(8 * sc), fill=col, outline=(30, 30, 34), width=iw(4))
    d.text((S(c[0]), S(c[1] + 1 * sc)), face, font=font(S(34 * sc), 900), fill=WHITE, anchor='mm')

def belt_hanging(d, x, top, bot, sw=0.0, sc=1.0):
    """the ginger's seatbelt, unbuckled, hanging by the door (the plant)"""
    if sc != 1.0:
        bx = x + sw
        line(d, [(x, top), (lerp(x, bx, 0.6), lerp(top, bot, 0.6)), (bx, bot)], (26, 26, 30), 34 * sc)
        d.rounded_rectangle([S(bx - 30 * sc), S(bot - 6 * sc), S(bx + 30 * sc), S(bot + 34 * sc)], radius=S(6 * sc), fill=(46, 46, 52), outline=(14, 14, 16), width=iw(3 * sc))
        poly(d, [(bx - 20 * sc, bot + 30 * sc), (bx + 20 * sc, bot + 30 * sc), (bx + 16 * sc, bot + 96 * sc), (bx - 16 * sc, bot + 96 * sc)], fill=(206, 210, 218), outline=(90, 94, 104), width=4 * sc)
        d.rectangle([S(bx - 8 * sc), S(bot + 52 * sc), S(bx + 8 * sc), S(bot + 76 * sc)], fill=(70, 74, 84))
        return
    bx = x + sw
    line(d, [(x, top), (lerp(x, bx, 0.6), lerp(top, bot, 0.6)), (bx, bot)], (26, 26, 30), 34)
    line(d, [(x - 8, top), (bx - 8, bot)], (60, 60, 68), 4)
    d.rounded_rectangle([S(bx - 30), S(bot - 6), S(bx + 30), S(bot + 34)], radius=S(6), fill=(46, 46, 52), outline=(14, 14, 16), width=iw(3))
    poly(d, [(bx - 20, bot + 30), (bx + 20, bot + 30), (bx + 16, bot + 96), (bx - 16, bot + 96)], fill=(206, 210, 218), outline=(90, 94, 104), width=4)
    d.rectangle([S(bx - 8), S(bot + 52), S(bx + 8), S(bot + 76)], fill=(70, 74, 84))

def seed(d, c, ang):
    poly(d, epoly(c[0], c[1], 11, 6, ang), fill=(40, 40, 44), outline=(200, 200, 200), width=2)

# ------------------------------------------------------------------ the car interior
GHX, SHX, HY, F = 800, 290, 950, 0.90
BKX, BKY, BKF = 590, 740, 0.52              # the back seat (Shoko, or the ginger in the tag)
SHSC = 1.02                                 # Sharit layer scale (head centre lands on (SHX, HY))

def paste_sharit(img, st, i):
    lay = SH.draw(st, i)
    sz = (int(lay.width * SHSC), int(lay.height * SHSC))
    lay = lay.resize(sz, Image.BICUBIC)
    img.alpha_composite(lay, (int(S(SHX) - S(350) * SHSC), int(S(HY) - S(300) * SHSC)))
    return lambda p: (SHX + (p[0] - 350) * SHSC, HY + (p[1] - 300) * SHSC)

def scene_car(t, i, swap=False):
    img = CAR_BG.copy()
    d = ImageDraw.Draw(img)
    # the back seat: Shoko cracking seeds (or, in the tag, the ginger frozen)
    d.rounded_rectangle([S(BKX - 200), S(820), S(BKX + 200), S(1000)], radius=S(40), fill=(48, 50, 60), outline=(30, 30, 36), width=iw(5))
    if not swap:
        sst = shoko_state(t)
        head(img, sst, i, BKX, BKY, BKF, 3 * math.sin(t * 2), SHOKO, props=True, wob=5 * math.sin(t * 6))
        if int(t * 2.5) % 2 == 0:                                  # a shell flies off
            d = ImageDraw.Draw(img); u = (t * 2.5) % 1.0
            seed(d, (BKX + 60 + 90 * u, BKY + 40 - 120 * u + 160 * u * u), 400 * u)
    else:
        gst = E3.base_state(); gst.update(lid=0.0, pupil='tiny', brow='sad', mouth='flat', ear_droop=0.7, sweat=1.0, look=(10, 4), red=0.0, blush=0.0,
                                          twitch=int(t * 12) % 2 == 0)
        head(img, gst, i, BKX, BKY, BKF, 0, GINGER)
    d = ImageDraw.Draw(img)
    for hx in (GHX, SHX):
        d.rounded_rectangle([S(hx - 120), S(700), S(hx + 120), S(860)], radius=S(40), fill=(44, 46, 54), outline=(30, 30, 36), width=iw(5))
    # the driver (image right): the ginger, or Shoko in the tag
    E(d, GHX, 1560, 250, 320, fill=(GINGER if not swap else SHOKO)['FUR'], outline=(GINGER if not swap else SHOKO)['OUT'], width=7)
    E(d, GHX, 1600, 120, 230, fill=(GINGER if not swap else SHOKO)['CREAM'])
    if not swap:
        gst, grot, gdy = ginger_state(t)
        head(img, gst, i, GHX, HY + gdy, F, grot, GINGER)
        d = ImageDraw.Draw(img)
        belt_hanging(d, 968, 560, 1150, 10 * math.sin(t * 2.2) + (24 * math.sin((t - BREAK) * 14) * math.exp(-(t - BREAK) * 3) if t >= BREAK else 0), 1.45)
    else:
        sst = shoko_state(t, wink=t >= WINK + 0.15)
        head(img, sst, i, GHX, HY - 10, F, 2 * math.sin(t * 3), SHOKO, props=True, wink=t >= WINK + 0.15, wob=6 * math.sin(t * 4))
    # Sharit (image left), belt across her
    sst = sharit_state(t)
    hp, up = stamp_pos(t) if not swap else ((560, 340), 1.0)
    sst['hand_r'] = hp
    to_frame = paste_sharit(img, sst, i)
    d = ImageDraw.Draw(img)
    line(d, [(SHX - 190, 1150), (SHX + 150, 1560)], (30, 30, 34), 26)
    # her clipboard (left paw), and the stamp in the right paw
    clipboard(img, to_frame((175, 640)), 0.78, 8, t)
    d = ImageDraw.Draw(img)
    sp = to_frame(hp)
    stamp_tool(d, (sp[0], sp[1] - 20), 0.9, 'עבר', GREEN)
    SH.hand(d, (sp[0], sp[1] + 10))
    # dash
    poly(d, [(0, 1430), (W, 1430), (W, 1600), (0, 1600)], fill=(34, 36, 42))
    d.rectangle([0, S(1420), W * K, S(1446)], fill=(58, 60, 68))
    # the blinker on the dash (signal step): a green arrow blinking + the stalk
    blink = (CHK2 - 0.15 <= t < PARK) or (t < COLD_END and story_t(t) >= CHK2 - 0.15)
    tt = story_t(t)
    if blink and int(tt * 3.4) % 2 == 0:
        poly(d, [(700, 1490), (640, 1520), (700, 1550)], fill=(60, 230, 90), outline=(10, 60, 20), width=4)
        d.rectangle([S(700), S(1508), S(746), S(1532)], fill=(60, 230, 90))
    # the wheel
    wc = (GHX, 1560); r = 175
    d.arc([S(wc[0] - r), S(wc[1] - r), S(wc[0] + r), S(wc[1] + r)], 180, 360, fill=(18, 18, 22), width=iw(36))
    BODY = (236, 238, 242); BODY_D = (190, 194, 204)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k_, xa in enumerate((180, 300, 760)):
        poly(od, [(xa, 260), (xa + 70 + 30 * k_, 260), (xa - 200 + 30 * k_, 1420), (xa - 270, 1420)], fill=(255, 255, 255, 20))
    img.alpha_composite(ov); d = ImageDraw.Draw(img)
    # the driver's seatbelt hanging unbuckled by the door, image right (THE PLANT) — inside the windshield frame
    d.rectangle([0, 0, W * K, S(250)], fill=BODY); d.rectangle([0, S(228), W * K, S(256)], fill=BODY_D)
    poly(d, [(0, 250), (120, 250), (30, 1450), (0, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(W, 250), (W - 120, 250), (W - 30, 1450), (W, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(-40, 1600), (W + 40, 1600), (W + 40, 1960), (-40, 1960)], fill=BODY)
    poly(d, [(-40, 1590), (W + 40, 1590), (W + 40, 1630), (-40, 1630)], fill=BODY_D)
    l_sign(d, (150, 330), 0.9)                                   # the ל sign on the windshield corner
    # the rear-view mirror
    d.rectangle([S(532), S(250), S(548), S(300)], fill=(30, 30, 34))
    d.rounded_rectangle([S(420), S(296), S(660), S(366)], radius=S(22), fill=(24, 24, 28), outline=(10, 10, 12), width=iw(4))
    d.rounded_rectangle([S(432), S(306), S(648), S(356)], radius=S(16), fill=(150, 176, 204))
    # paws on the wheel
    pal = GINGER if not swap else SHOKO
    if not swap and (L['0b'] <= t < PARK or t < COLD_END) and (tt - L['0b']) >= ss(0, 1) - 0.1 and (tt - L['0b']) < ss(0, 2):
        lp = (GHX - 230, 1450)                                    # flicking the blinker stalk
        line(d, [(GHX - 200, 1470), (GHX - 330, 1500)], (40, 40, 46), 14)
    else:
        lp = (GHX - 160, 1410)
    for p_ in (lp, (GHX + 160, 1410)):
        capsule(d, (GHX + (p_[0] - GHX) * 0.5, 1520), p_, 78, pal['FUR'], pal['OUT'], 4); paw(d, p_, pal, 0, 0.85)
    return img

# ------------------------------------------------------------------ the mirror insert (Shoko + seeds; the ginger's eyes)
def scene_mirror(t, i):
    img = CAR_BG.copy(); img.alpha_composite(Image.new('RGBA', img.size, (20, 20, 26, 200)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(60), S(560), S(1020), S(1360)], radius=S(120), fill=(24, 24, 28), outline=(10, 10, 12), width=iw(10))
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rectangle([0, 0, W * K, H * K], fill=(62, 64, 74))
    for y in range(640, 900, 6):
        v = (y - 640) / 260; ld.rectangle([S(140), S(y), S(940), S(y + 6)], fill=(int(lerp(160, 214, v)), int(lerp(204, 226, v)), int(lerp(240, 236, v))))
    ld.rounded_rectangle([S(220), S(1000), S(860), S(1330)], radius=S(60), fill=(48, 50, 60))
    sst = shoko_state(t); sst.update(look=(-10, 6))
    head(lay, sst, i, 540, 1040, 0.95, -3, SHOKO, props=True, wob=6 * math.sin(t * 6))
    ld = ImageDraw.Draw(lay)
    u = (t * 2.2) % 1.0
    seed(ld, (650 + 160 * u, 1120 - 200 * u + 300 * u * u), 500 * u)
    mask = Image.new('L', img.size, 0); ImageDraw.Draw(mask).rounded_rectangle([S(90), S(590), S(990), S(1330)], radius=S(100), fill=255)
    lay.putalpha(mask)
    img.alpha_composite(lay)
    st = E3.base_state(); st.update(lid=0.0, pupil='big', brow='up', mouth='flat', look=(0, -24), sweat=0.6, red=0.0, blush=0.0)
    head(img, st, i, 540, 1700, 0.9, 0, GINGER)
    return img

# ------------------------------------------------------------------ side views (pull out / the sidewalk tag)
def roof_l(img, x, y, sc):
    d = ImageDraw.Draw(img)
    d.rectangle([S(x - 6 * sc), S(y - 150 * sc - 128 * sc), S(x + 6 * sc), S(y - 150 * sc - 96 * sc)], fill=(40, 40, 44))
    l_sign(d, (x, y - 150 * sc - 150 * sc), 0.75 * sc)

def cone(d, c, sc=1.0, ang=0.0):
    pts = xform([(-34 * sc, 40 * sc), (34 * sc, 40 * sc), (0, -60 * sc)], c[0], c[1], ang)
    poly(d, pts, fill=(255, 120, 30), outline=(90, 40, 10), width=4)
    a, b = xform([(-18 * sc, 0), (18 * sc, 0)], c[0], c[1], ang); line(d, [a, b], WHITE, 10 * sc)
    a, b = xform([(-46 * sc, 44 * sc), (46 * sc, 44 * sc)], c[0], c[1], ang); line(d, [a, b], (90, 40, 10), 10 * sc)

def scene_road(t, i, kind):
    img = ROAD_BG.copy(); d = ImageDraw.Draw(img)
    off = (t - ROAD1) * 500 if kind == 'road1' else (t - TAG) * 380
    B.buildings(d, off); B.lanes(d, off)
    sc = 0.95
    if kind == 'road1':
        u = clamp((t - ROAD1) / (MIRROR - ROAD1))
        x, y = lerp(380, 640, ease_io(u)), 1530
        gst = dict(lid=0.0, pupil='big', brow='annoyed', mouth='flat', ear_dy=-12, sweat=0.8, look=(30, -8))
        car_side(img, x, y, sc, (236, 238, 242), [('ginger', gst, 70, 0.42), ('c3', 0, -60, 0.30)], 1, roof_l, t)
        av = SH_AV; img.alpha_composite(av, (int(S(x - 60 * sc) - av.width / 2), int(S(y - 190 * sc) - av.height / 2)))
        d = ImageDraw.Draw(img)
        for k_, cx in enumerate((120, 980)): cone(d, (cx, 1660), 0.9)
    else:                                                    # Shoko on the sidewalk, a cone flies over the roof
        u = t - TAG
        bump = 220 if u > 0.15 else 220 * u / 0.15
        x, y = lerp(260, 700, ease_io(clamp(u / (WINK - TAG)))), 1530 + bump + 8 * math.sin(u * 40) * (u < 0.4)
        d.rectangle([0, S(1606), W * K, H * K], fill=(186, 184, 180))
        for xx in range(-40, W + 80, 120): d.line([S(xx - off % 120), S(1606), S(xx - off % 120), H * K], fill=(160, 158, 154), width=iw(3))
        sst = dict(lid=0.6, brow='annoyed', mouth='goofy', look=(20, 0))
        car_side(img, x, y, sc, (236, 238, 242), [('shoko', sst, 70, 0.40)], 1, roof_l, t)
        av = SH_AV; img.alpha_composite(av, (int(S(x - 60 * sc) - av.width / 2), int(S(y - 190 * sc) - av.height / 2)))
        d = ImageDraw.Draw(img)
        k = clamp((u - 0.25) / 0.9)
        if k <= 0: cone(d, (x + 330, 1720), 1.0)
        else:
            cx = lerp(x + 330, x - 420, k); cy = 1720 - 900 * k * (1 - k) * 1.6 - 120 * k
            cone(d, (cx, cy), 1.0, 720 * k)
        for k2 in range(2): cone(d, (1000 - k2 * 120, 1820), 0.8)
        if 0.1 < u < 0.7:                                    # the curb bump: dust
            ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            for j in range(5): E(od, x - 180 + j * 50, 1640 - 60 * (u - 0.1), 60 + 40 * u, 30 + 20 * u, fill=(220, 214, 200, int(160 * (0.7 - u))))
            img.alpha_composite(ov)
    return img

# ------------------------------------------------------------------ top-down: the parallel park
def car_top(sc=1.0, col=(240, 242, 246), learner=False):
    lay = Image.new('RGBA', (S(220), S(380)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([S(20), S(14), S(200), S(366)], radius=S(46), fill=col, outline=(30, 30, 34), width=iw(5))
    d.rounded_rectangle([S(38), S(96), S(182), S(150)], radius=S(16), fill=(120, 150, 180))
    d.rounded_rectangle([S(42), S(270), S(178), S(316)], radius=S(16), fill=(120, 150, 180))
    d.rounded_rectangle([S(40), S(150), S(180), S(270)], radius=S(12), fill=tuple(max(0, c - 22) for c in col))
    for x in (44, 176): E(d, x, 30, 16, 10, fill=(255, 246, 190))
    for x in (44, 176): E(d, x, 356, 16, 8, fill=(220, 50, 50))
    if learner: l_sign(d, (110, 210), 0.8)
    return lay

def scene_park(t, i):
    img = PARK_BG.copy(); d = ImageDraw.Draw(img)
    u = clamp((t - MOVE[0]) / (MOVE[1] - MOVE[0])) if t >= MOVE[0] else 0.0
    if t < MOVE[0]:                                           # rolling up beside the front car
        k = ease_out(clamp((t - PARK) / (MOVE[0] - PARK)))
        x, y, ang = 470, lerp(1500, 600, k), 0.0
    else:                                                     # one smooth reverse S into the gap
        x = lerp(470, 735, ease_io(u)); y = lerp(600, 905, ease_io(u)); ang = -38 * math.sin(math.pi * u)
    lay = CAR_TOP_L.rotate(ang, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(lay, (int(S(x) - lay.width / 2), int(S(y) - lay.height / 2)))
    d = ImageDraw.Draw(img)
    if t >= MOVE[0] and u < 1:                               # tyre marks / motion lines
        for j in range(4): line(d, [(x - 60 + j * 40, y + 200), (x - 60 + j * 40 - 30 * u, y + 260)], (255, 255, 255), 5)
    if t >= CHK3:                                             # perfect: a gold frame around the bay
        k = clamp((t - CHK3) / 0.2)
        d.rounded_rectangle([S(625), S(705), S(845), S(1105)], radius=S(30), outline=GOLD, width=iw(10 * k + 1))
    # the examiner's face in a corner bubble (second character in the shot)
    bub = SH_BUB[1 if voice_v(t, 'sh') > 0.12 and int(t * 8) % 2 else 0] if t < CHK3 else SH_BUB[2]
    img.alpha_composite(bub, (S(40), S(1340)))
    sst = shoko_state(t); sst.update(look=(-20, -10))
    if t >= CHK3: sst.update(mouth='goofy', lid=0.4)
    head(img, sst, i, 900, 1500, 0.55, 0, SHOKO, props=True, wob=6 * math.sin(t * 6))
    return img

def build_park_bg():
    img = Image.new('RGBA', (W * K, H * K), (96, 98, 106, 255)); d = ImageDraw.Draw(img)
    d.rectangle([S(860), 0, W * K, H * K], fill=(186, 184, 180))                   # sidewalk (image right)
    for y in range(0, H, 110): d.line([S(860), S(y), W * K, S(y)], fill=(160, 158, 154), width=iw(3))
    d.rectangle([S(846), 0, S(866), H * K], fill=(226, 226, 222))                   # curb
    for y in range(-40, H, 200): d.rectangle([S(372), S(y), S(384), S(y + 110)], fill=(240, 240, 240))   # lane dashes
    for y in (720, 1090): d.rectangle([S(640), S(y), S(840), S(y + 8)], fill=(240, 240, 240))           # bay lines
    front = car_top(1.0, (200, 60, 60)); back = car_top(1.0, (70, 110, 190))
    img.alpha_composite(front, (S(735) - front.width // 2, S(500) - front.height // 2))
    img.alpha_composite(back, (S(735) - back.width // 2, S(1310) - back.height // 2))
    for y in (380, 980): E(d, 960, y, 70, 70, fill=(70, 140, 70), outline=(40, 90, 40), width=5)   # trees on the sidewalk
    return img.filter(ImageFilter.GaussianBlur(S(0.6)))

# ------------------------------------------------------------------ the form insert (the break)
def scene_form(t, i):
    img = CAR_BG.copy(); img.alpha_composite(Image.new('RGBA', img.size, (30, 26, 24, 160)))
    u = t - BREAK
    d = ImageDraw.Draw(img)
    clip = Image.new('RGBA', img.size, (0, 0, 0, 0))
    clipboard(clip, (520, 980), 2.6, 6, t, n_checks=3)
    img.alpha_composite(clip)
    d = ImageDraw.Draw(img)
    # the belt row (empty box) under the checks
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    # the red stamp "נכשל" slams down
    k = clamp(u / 0.08); sc = lerp(1.7, 1.0, ease_in(k)); a = int(255 * clamp(u / 0.04))
    st = Image.new('RGBA', (S(560), S(240)), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([S(10), S(10), S(550), S(230)], radius=S(24), outline=(220, 30, 40, 235), width=iw(16))
    sd.text((S(280), S(124)), 'נכשל', font=font(S(150), 900), fill=(220, 30, 40, 235), anchor='mm')
    st = st.resize((int(st.width * sc), int(st.height * sc)), Image.BICUBIC).rotate(-12, resample=Image.BICUBIC, expand=True)
    if a > 0:
        alpha = st.split()[3].point(lambda v: int(v * a / 255)); st.putalpha(alpha)
        img.alpha_composite(st, (int(S(520) - st.width / 2), int(S(1000) - st.height / 2)))
    if u < 0.12:                                              # her paw with the stamp tool coming down
        d = ImageDraw.Draw(img); hy = lerp(600, 900, clamp(u / 0.08))
        stamp_tool(d, (520, hy), 2.2, 'נכשל', RED)
    d = ImageDraw.Draw(img)
    # the buckle in the foreground, swinging (the plant, paid off)
    belt_hanging(d, 930, 0, 1180, 60 * math.sin(u * 9) * math.exp(-u * 2), 2.6)
    if u < 0.3: E18.burst(img, (520, 1000), u, (255, 120, 120), 260, 12, 0.3)
    return img

def scene(t, i):
    name = shot(t)[0]
    if name.startswith('road'): img = scene_road(t, i, name)
    elif name == 'mirror': img = scene_mirror(t, i)
    elif name == 'park': img = scene_park(t, i)
    elif name == 'form': img = scene_form(t, i)
    elif name == 'wink': img = scene_car(t, i, swap=True)
    else: img = scene_car(t, i)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= t < c_ + 0.5: E18.burst(img, (540, 1150), t - c_, (120, 255, 160) if c_ != CHK3 else (255, 220, 120), 170, 10, 0.4)
    if GOLDT <= t < PEAK + 0.6: E18.confetti(img, t - GOLDT + 0.3)
    return img

# ------------------------------------------------------------------ overlays
CHIP_Y = 200
CHIPS = [('מראות', 820, CHK1), ('איתות', 540, CHK2), ('חניה', 260, CHK3)]
def chips(frame, t, y=CHIP_Y):
    if t < max(T0 + 0.2, HOOK_END) or t >= BREAK: return
    gold = t >= GOLDT
    d = ImageDraw.Draw(frame)
    for lab, cx, tk in CHIPS:
        ok = t >= tk
        fill = GOLD if gold else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or gold) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        w, h = 230 * sc, 62 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 22 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], outline=ink, width=4)

CLOCK_LABEL = ['הטסט נגמר', 'בעוד']
def clock_state(t):
    name = shot(t)[0]
    st = story_t(t)
    if name == 'rewind': return C.secs_left(st, ZERO), 'run', True
    s = C.secs_left(st, ZERO)
    return s, ('hot' if s <= 5 else 'run'), False

CAR_BG = ROAD_BG = PARK_BG = CAR_TOP_L = SH_AV = PILL_EP = PILL_Q = PILL_SER = None
SH_BUB = []
def init_all():
    global CAR_BG, ROAD_BG, PARK_BG, CAR_TOP_L, SH_AV, SH_BUB, PILL_EP, PILL_Q, PILL_SER
    B.init_all()
    CAR_BG = B.build_car_bg(); ROAD_BG = B.build_road_bg(); PARK_BG = build_park_bg(); CAR_TOP_L = car_top(1.0, learner=True)
    st = SH.base(); st.update(mouth='lazy', lid=0.55, look=(-10, 6))
    lay = SH.draw(st, 0).crop((S(110), S(90), S(590), S(520)))
    SH_AV = lay.resize((S(110), int(S(110) * lay.height / lay.width)), Image.LANCZOS)
    SH_BUB = []
    for mo, lid in (('lazy', 0.55), ('talk', 0.55), ('lazy', 0.12)):
        st = SH.base(); st.update(mouth=mo, lid=lid, look=(16, 4))
        lay = SH.draw(st, 3).crop((S(110), S(90), S(590), S(520))).resize((S(300), S(269)), Image.LANCZOS)
        bub = Image.new('RGBA', (S(320), S(320)), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)
        bd.ellipse([0, 0, S(320) - 1, S(320) - 1], fill=(250, 250, 248), outline=(20, 20, 24), width=iw(8))
        mask = Image.new('L', bub.size, 0); ImageDraw.Draw(mask).ellipse([S(12), S(12), S(308), S(308)], fill=255)
        inner = Image.new('RGBA', bub.size, (0, 0, 0, 0)); inner.alpha_composite(lay, (S(10), S(40)))
        inner.putalpha(Image.fromarray(np.minimum(np.array(inner.split()[3]), np.array(mask))))
        bub.alpha_composite(inner)
        SH_BUB.append(bub)
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_SER = HUD._pill(SERIES_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'car':
        z, cx, cy = 1.08 + 0.01 * pu, 560, 1060
        if a == 0.0:                                   # cold open: tight on the ginger, the dangling belt beside him
            z, cx, cy = 1.62 + 0.03 * t, 850, 1000
            if t < 0.3: z = 1.85 - 0.23 * ease_out(t / 0.3)
        elif a == T0: z, cx, cy = 1.06, 560, 1060      # the want: all three
        elif a == INTSIG: z, cx, cy = 1.25, 760, 1080   # the signal: the ginger + the blinker + the belt
        elif a == INT3:                                # eyebrows up → the stamp → the hush: a slow push
            k = ease_io(clamp((t - INT3) / (BREAK - INT3)))
            if t < PEAK: z, cx, cy = 1.15, 470, 1000   # Sharit + Shoko behind
            else: z, cx, cy = lerp(1.12, 1.32, k), lerp(560, 720, k), lerp(1060, 1040, k)
        elif a == INSERT_END: z, cx, cy = 1.45, 780, 1020   # his frozen face, the belt
    elif name == 'rewind': z, cx, cy = 1.10, 560 + 30 * math.sin(t * 90), 1060
    elif name == 'mirror': z, cx, cy = 1.0 + 0.04 * pu, 540, 1000
    elif name == 'park': z, cx, cy = 1.0, 540, 960
    elif name == 'form': z, cx, cy = 1.0 + 0.02 * pu, 540, 980
    elif name == 'wink': z, cx, cy = 1.10 + 0.04 * pu, 640, 1020
    elif name == 'frozen': z, cx, cy = 1.14, 640, 1020
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene(lerp(L['0b'] + 0.6, T0 + 0.3, ease_in(u)), i)
    elif name == 'frozen': img = scene_car(FREEZE - 0.01, i, swap=True)
    else: img = scene(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 12 * math.exp(-t * 5)
    for s_ in (CHK3, BREAK, TAG + 0.15):
        if 0 <= t - s_ < 0.35: shake = 20 * math.exp(-(t - s_) * 7)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if t < COLD_END: frame = frame.rotate(-4, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(236, 238, 242, 255))
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.24 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(50 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: B.rewind_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK, ROAD1, MIRROR, INTSIG, PARK, INT3, INSERT_END, TAG, WINK):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(90 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    for t0, t1, lines in TOPCAPS:
        if t0 <= t < t1:
            band = frame.crop((0, 0, W, 470)).filter(ImageFilter.GaussianBlur(14))
            mask = Image.new('L', (W, 470), 0); md = ImageDraw.Draw(mask)
            for yy in range(470): md.line([(0, yy), (W, yy)], fill=int(255 * min(1, (470 - yy) / 90)))
            frame.paste(band, (0, 0), mask)
            dk = Image.new('RGBA', (W, 470), (0, 0, 0, 0)); dd = ImageDraw.Draw(dk)
            for yy in range(470): dd.line([(0, yy), (W, yy)], fill=(8, 10, 18, int(150 * min(1, (470 - yy) / 120))))
            frame.alpha_composite(dk, (0, 0))
            m.paste_center(frame, m.caption_layer(lines, 92, WHITE), W / 2, 290)
    if name not in ('frozen',): chips(frame, t)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            col = {'sh': SHARIT_SUB, 'shoko': SHOKO_SUB}.get(SPEAKER[li], WHITE)
            m.paste_center(frame, B.sub_layer(lines, col), W / 2, 1240 if name == 'road3' else 1560)
    if t < COLD_END or (T0 <= t < ROAD1) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_SER, (40, 70 + PILL_EP.height + 6))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    if t < DUR - 0.25 and t < BREAK + 1.2:
        s, state, scr = clock_state(t)
        if t >= BREAK: s, state = 0, 'zero'
        C.draw(frame, CLOCK_LABEL, s, state, t, scr)
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio: voices + SFX (control arm: NO music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(47)
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
    def heartbeat(t0, g=0.7):
        for dt, gg in ((0.0, 1.0), (0.14, 0.7)):
            tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 10) + 38) / SR) * np.exp(-tt * 22), t0 + dt, g * gg)
    def click(t0, g=0.25): add(sfx, m.highpass(nz(0.03), 2500) * np.exp(-tt_(0.03) * 90), t0, g)
    add(sfx, thud(0.45), 0.0)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    eng = m.lowpass(nz(DUR), 120) * (1 + 0.3 * np.sin(2 * np.pi * 16 * tt_(DUR)))   # the engine
    add(sfx, eng, 0.0, 0.045)
    for t_ in (ROAD1, MIRROR, PARK, TAG): whoosh(t_ + 0.05, 0.08, 0.25)
    add(sfx, m.lowpass(nz(0.9), 300) * np.sin(np.pi * tt_(0.9) / 0.9), ROAD1, 0.12)        # pulling out
    check(CHK1, 0.15)
    # the blinker: tick-tock (story time), also under the cold open
    for base, t_end in ((CHK2 - 0.15, PARK), ):
        tk = base
        while tk < t_end:
            click(tk, 0.22); click(tk + 0.29, 0.14); tk += 0.59
    tk = CHK2 - 0.15 - L['0b']
    while tk < COLD_END:
        if tk >= 0: click(tk, 0.18); click(tk + 0.29, 0.11)
        tk += 0.59
    check(CHK2, 0.16)
    sq = MOVE[0] + 0.25                                                                    # the park: a tyre squeak + glide
    add(sfx, m.bandpass(nz(0.35), 1800, 3200) * np.sin(np.pi * tt_(0.35) / 0.35), sq, 0.06)
    add(sfx, m.lowpass(nz(MOVE[1] - MOVE[0]), 400) * np.sin(np.pi * tt_(MOVE[1] - MOVE[0]) / (MOVE[1] - MOVE[0])), MOVE[0], 0.08)
    add(sfx, thud(0.25), CHK3 - 0.03); check(CHK3, 0.2, True)
    whoosh(PEAK + 0.05, 0.07, 0.3)                                                         # the stamp goes up
    heartbeat(HOLD[0] + 0.02); heartbeat(HOLD[0] + 0.26, 0.5)
    add(sfx, thud(1.0), BREAK); add(sfx, m.lowpass(nz(0.12), 900) * np.exp(-tt_(0.12) * 30), BREAK, 0.6)   # STAMP
    tt = tt_(0.5); add(sfx, np.sign(np.sin(2 * np.pi * 180 * tt)) * np.exp(-tt * 5) * 0.4, BREAK + 0.02, 0.10)   # the fail buzz
    add(sfx, thud(0.55), TAG + 0.15)                                                       # the curb
    tt = tt_(0.08); add(sfx, np.sin(2 * np.pi * 520 * tt) * np.exp(-tt * 40), TAG + 0.25 + 0.0, 0.25)   # bonk (the cone)
    whoosh(TAG + 0.55, 0.08, 0.4)
    add(sfx, m.tone(1046.5, 0.25, harm=((1, 1), (3, 0.2)), decay=12), WINK + 0.15, 0.10)   # the wink ding
    add(sfx, m.tone(82.4, 1.0, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), FREEZE - 0.2, 0.10)
    out = voice + sfx
    out = out[:int(DUR * SR)]
    wl_ = 0.3; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.28)
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
    ticks, prev = [], None
    for i in range(int(DUR * FPS)):
        tq = i / FPS; s, state, scr = clock_state(tq)
        if scr or tq >= BREAK: prev = None; continue
        if prev is not None and s != prev and s > 0: ticks.append(tq)
        prev = s
    C.add_ticks(path, ticks, loud_from=ZERO - 5.0, final=ZERO)

def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if mode == 'times':
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', round(T0, 2))
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('ROAD1', round(ROAD1, 2), 'MIRROR', round(MIRROR, 2), 'INTSIG', round(INTSIG, 2), 'PARK', round(PARK, 2), 'MOVE', [round(x, 2) for x in MOVE], 'INT3', round(INT3, 2))
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'PEAK', round(PEAK, 2), 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'TAG', round(TAG, 2), 'WINK', round(WINK, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        print('clock frame0', C.secs_left(story_t(0), ZERO), 'after rewind', C.secs_left(story_t(T0 + 0.01), ZERO), 'peak', C.secs_left(PEAK, ZERO))
        print('SEG0', SEG[0], 'SEG6', SEG[6])
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, os.environ.get('SHEET', 'ep47_contact.png'))); print('ok'); return
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
