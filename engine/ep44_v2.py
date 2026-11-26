#!/usr/bin/env python3
"""
ep44_v2 (27.11, Gabi's note on episodes/ep44 26.11): the left turn rebuilt as a top-down DRIFT. Before it, their straight
lane has a GREEN straight arrow and they fly; the nav says left at the last moment; Shoko flicks it: the rear steps out
(oversteer, counter-steer, tyre smoke, skid marks, screech) and the car slides into the empty head of the left-turn lane
exactly as the left arrow turns green and the clock stops on 00:01 — then it turns away. Voices, plant, climb, break,
clock and the music arm untouched.

"חתול בהמתנה" — פרק 44: שמאלה. עכשיו. — Series 2 "שוקו והג׳ינג׳י", season 1 "על הכביש", ep1 (VOICED, built 25.11
under §P, ~22.8 s). Gabi's idea ideas/2026-11-23-gabi-waze. Music arm: an original comic underscore made in code,
◀◀ → the peak only, ducked ≥12 dB under the voices, cut to silence at the peak.
Voices = voice bank 2026-11-23 lines 4400–4408 (Benji = the ginger, Knox = Shoko, Delia = Sharit as the navigation
voice; Gabi's picks 25.11: 4405 B), prepared by voice/ep44_prep.py. The tag 4409 is not used in this cut.
Set: the car interior seen through the windshield (frontal two-shot: the ginger riding on the image left, Shoko
driving on the image right, one paw on the wheel, the navigation phone on the dash between them, the rear-view
mirror at the top, the driver's side mirror outside on the right). Cut-outs to the road (side view) for every
escalation step: the empty straight lane, the absurd left-turn queue, the bus with Sharit, the junction on orange.
Want: the ginger's appointment at משרד הפנים in a minute (the slip "תור · 08:00"). Stakes: miss it = April.
Plants: (a) the nav screen, small grey "בעוד 400 מ׳: פנה שמאלה" (the distance shrinks), Shoko never looks at it;
(b) a motorbike rider in the side mirror. Both in frame 0 and mid-climb.
Clock: "התור בעוד 00:SS", real seconds from frame 0; it never hits 00:00 — it stops green on 00:01 when they are through.
Climb: נתיב ✓ ("רגוע. אין פקקים.") → פקק ✓ (the queue: a sleeper on a pillow, a family with sandwiches, a man
watering a plant on his roof; then the bus, Sharit waving, "שרית?! גם בפקק?!") → the nav (Sharit): "בעוד מאה מטר,
פנה שמאלה, מותק." → "שמאלה?! שמאלה!!!" → orange, Shoko: "מחזיק." — he cuts to the head of the line, horns ✓ gold.
Peak: silence, they are through; the ginger, eyes squeezed shut, "...עברנו?" heartbeat.
Break (wrong_one_wins): the rider from the mirror rolls up, lifts his visor and claps slowly; Shoko nods like a star:
"תודה, תודה."; the ginger frozen; whip into the cold open.

  python3 voice/ep44_prep.py
  python3 ep44.py times | test t1 t2 ... | render   -> out/ep44_smola.mp4
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
import ep18 as E18
import ep21_v1 as V1
import hud as HUD
import clock_overlay as C
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, lerp2, clamp, epoly, xform,
                        ease_io, ease_out, ease_in, font, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep44', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 70, 150); ORANGE = (255, 150, 20)
SHARIT_SUB = (255, 182, 210); SHOKO_SUB = (190, 230, 120)
QUEUE = int(os.environ.get('QUEUE', '434'))
EP_LABEL = 'פרק 44'
SERIES_LABEL = 'שוקו והג׳ינג׳י'
OUTNAME = os.environ.get('OUTNAME', 'ep44_smola_v2')
LIMIT = float(os.environ.get('LIMIT', '0'))

GINGER = dict(FUR=m.FUR, FUR_D=m.FUR_D, OUT=m.OUT, CREAM=m.CREAM, PINK=m.PINK, IRIS=m.IRIS)
SHOKO = dict(FUR=(62, 62, 74), FUR_D=(38, 38, 48), OUT=(14, 14, 18), CREAM=(128, 128, 142), PINK=(178, 104, 124), IRIS=(206, 214, 58))
def palette(p):
    for k, v in p.items(): setattr(m, k, v)

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
COLD_END = round(D[0] + 0.40, 2)            # cold open = 4400 "שמאלה?! שמאלה!!!" (the loudest climb line)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "יש לנו תור במשרד הפנים. בעוד דקה! סע!" — the slip "תור · 08:00"
ROAD1 = L[1] + D[1] + 0.08                  # cut out: the empty straight lane
L[2] = ROAD1 + 0.15                         # Shoko: "רגוע. אין פקקים."
CHK1 = L[2] + ss(2, 1) - 0.03
INT2 = L[2] + D[2] + 0.05                   # interior: he looks out at the left queue
L[3] = INT2 + 0.05                          # "תראה את המסכנים האלה בשמאל..."
ROAD2 = L[3] + D[3] + 0.05                  # the absurd queue passing
CHK2 = ROAD2 + 0.95
ROAD3 = ROAD2 + 1.55                        # the bus: Sharit waving from the window
INT3 = ROAD3 + 0.85
L[4] = INT3 + 0.03                          # "שרית?! גם בפקק?!"
L[5] = L[4] + D[4] + 0.10                   # the nav (Sharit): "בעוד מאה מטר, פנה שמאלה, מותק."
L['0b'] = L[5] + D[5] + 0.08                # "שמאלה?! שמאלה!!!" in context (= the cold open)
ROAD4 = L['0b'] + D[0] + 0.05               # the junction: the light turns orange
L[6] = ROAD4 + 0.55                         # Shoko: "מחזיק." (top-down: flying in the green straight lane)
SWERVE = (L[6] + D[6] - 0.05, L[6] + D[6] + 1.55)   # the drift: flick, slide, land at the head of the left lane
CHK3 = SWERVE[1] - 0.12; GOLDT = CHK3 + 0.05   # the exact second: they land as the left arrow turns green
PEAK = SWERVE[1] + 0.70                     # interior: silence — they are through (after the turn-away)
L[7] = PEAK + 0.25                          # "...עברנו?"
HOLD = (L[7] + D[7] + 0.04, L[7] + D[7] + 0.56)
BREAK = HOLD[1]                             # the rider rolls up, visor up, slow claps
L[8] = BREAK + 0.45                         # Shoko: "תודה, תודה."
FREEZE = L[8] + D[8]
DUR = round(FREEZE + 0.42, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (3, L[3]), (4, L[4]), (5, L[5]), (0, L['0b']), (6, L[6]), (7, L[7]), (8, L[8])]
SPEAKER = {0: 'cat', 1: 'cat', 3: 'cat', 4: 'cat', 7: 'cat', 2: 'shoko', 6: 'shoko', 8: 'shoko', 5: 'sh'}

SUBS = {
    0: [['שמאלה?! שמאלה!!!']],
    1: [['יש לנו תור במשרד הפנים.'], ['בעוד דקה! סע!']],
    2: [['רגוע.'], ['אין פקקים.']],
    3: [['תראה את המסכנים האלה בשמאל...']],
    4: [['שרית?! גם בפקק?!']],
    5: [['בעוד מאה מטר,'], ['פנה שמאלה, מותק.']],
    6: [['מחזיק.']],
    7: [['...עברנו?']],
    8: [['תודה, תודה.']],
}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]
    if len(ch) > 1 and len(SEG[li]) < len(ch): ch = [[' '.join(sum(ch, []))]]
    starts = [0.0] + [ss(li, k) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 7: b = min(b, HOLD[0])
        if li == 8: b = DUR - 0.25
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('car', 0.0, COLD_END), ('rewind', COLD_END, T0), ('car', T0, ROAD1), ('road1', ROAD1, INT2), ('car', INT2, ROAD2),
         ('road2', ROAD2, ROAD3), ('road3', ROAD3, INT3), ('car', INT3, ROAD4), ('road4', ROAD4, PEAK), ('car', PEAK, FREEZE),
         ('frozen', FREEZE, DUR + 1)]
HOOK = ['הניווט אמר שמאלה', 'ברגע האחרון']           # keyword: הניווט / שמאלה (the pain in the viewer's words)
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

# ------------------------------------------------------------------ drawing helpers
def paw(d, p, pal, ang=0.0, s=1.0):
    poly(d, epoly(p[0], p[1], 70 * s, 54 * s, ang), fill=pal['FUR'], outline=pal['OUT'], width=6)
    for dx in (-22, 0, 22):
        a, b = xform([(dx * s, 16 * s), (dx * s, 48 * s)], p[0], p[1], ang); line(d, [a, b], pal['OUT'], 4)

def shades(d):
    for cx in (205, 315):
        poly(d, [(cx - 50, 118), (cx + 50, 118), (cx + 42, 152), (cx - 42, 152)], fill=(20, 20, 26), outline=(0, 0, 0), width=5)
        line(d, [(cx - 34, 126), (cx - 14, 126)], (120, 160, 200), 4)
    line(d, [(255, 128), (265, 128)], (0, 0, 0), 7)

def toothpick(d, wob=0.0):
    a = (288, 318); b = (352, 296 + wob)
    line(d, [a, b], (222, 190, 130), 6); line(d, [a, b], (150, 116, 70), 1)

def head(img, st, i, hx, hy, f, rot=0.0, pal=GINGER, props=False, wob=0.0):
    palette(pal)
    Lh, _ = m.draw_head(st, i)
    if props:
        dl = ImageDraw.Draw(Lh); shades(dl); toothpick(dl, wob)
    palette(GINGER)
    if abs(rot) > 1e-3: Lh = Lh.rotate(rot, resample=Image.BICUBIC, center=(260 * K, 245 * K))
    sz = int(520 * K * f)
    Lh = Lh.resize((sz, sz), Image.BICUBIC)
    img.alpha_composite(Lh, dest=(int(S(hx) - 260 * K * f), int(S(hy) - 245 * K * f)))

def shadow_paste(img, lay, c, ang=0.0, sc=1.0, a=90):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    V1.shadow_paste(img, lay, c, a, (10, 14), 8)

# ------------------------------------------------------------------ states
def ginger_state(t):
    st = E3.base_state(); st.update(red=0.0, blush=0.2)
    rot, dy = 0.0, 0.0
    s_t = story_t(t)
    v = voice_v(s_t, 'cat')
    if L['0b'] <= s_t < ROAD4 and t < PEAK:                 # "שמאלה?! שמאלה!!!" — panic, pointing across
        u = s_t - L['0b']
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=mouth_of(s_t, 'cat', 'w', 'w'), ear_dy=-32, sweat=1.0, look=(30, -6), blush=0.0)
        rot = 8 * math.sin(u * 14); dy = -18 * v - 8 * abs(math.sin(u * 10))
    elif t < ROAD1:                                         # want: the slip, "בעוד דקה! סע!"
        st.update(lid=0.0, pupil='big', brow='sad', mouth=mouth_of(t, 'cat', 'flat', 'w'), ear_dy=-14, sweat=0.9, look=(26, 6))
        rot = 3 * math.sin(t * 6); dy = -12 * v
    elif t < ROAD2:                                         # "תראה את המסכנים האלה בשמאל..." — smug pity out of his window
        st.update(lid=0.35, pupil='normal', brow='annoyed', mouth=mouth_of(t, 'cat', 'smile_small', 'smile'), ear_dy=-6, look=(-40, 4), blush=0.4)
        rot = -4; dy = -8 * v
    elif t < L[5]:                                          # "שרית?! גם בפקק?!"
        u = t - L[4]
        st.update(lid=0.0, pupil='tiny', brow='up', mouth=mouth_of(t, 'cat', 'w', 'w'), ear_dy=-26 * math.exp(-max(0, u) * 2), sweat=1.0, look=(-40, -4))
        rot = 7 * math.sin(u * 20) * math.exp(-max(0, u) * 3); dy = -26 * math.exp(-max(0, u) * 5)
    elif t < L['0b']:                                       # the nav speaks: he stares at it; "שמאלה" lands
        u = t - L[5]
        late = u > ss(5, 1)
        st.update(lid=0.0, pupil='tiny' if late else 'big', brow='up', mouth='w' if late else 'flat', ear_dy=-22 if late else -8, look=(26, 30), sweat=0.6 + 0.4 * late)
        dy = -10 * late
    elif t < PEAK:                                          # the swerve (outside) — here: bracing
        st.update(lid=0.0, pupil='tiny', brow='up', mouth='w', ear_dy=-30, sweat=1.0, look=(20, 0))
    elif t < BREAK:                                         # THE PEAK: eyes squeezed shut, then "...עברנו?"
        st.update(eye_mode='closed', brow='sad', mouth='flat', ear_dy=-20, sweat=1.0, look=(0, 0), blush=0.0)
        if t >= L[7]: st.update(eye_mode='open', lid=0.62, pupil='normal', brow='up', mouth=mouth_of(t, 'cat', 'flat', 'smile_small'), look=(24, 0))
        rot = 2 * math.sin(t * 30) * (t < L[7])
    else:                                                   # the break: the rider claps — frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none' if u < 0.9 else 'sad', mouth='flat', ear_dy=-24 * math.exp(-u * 4),
                  ear_droop=clamp((u - 1.0) / 0.8) * 0.6, look=(38, 10), twitch=(u > 0.9 and int(t * 12) % 2 == 0), sweat=1.0, blush=0.0)
        dy = -6
    return st, rot, dy

def shoko_state(t):
    st = E3.base_state(); st.update(lid=0.55, brow='annoyed', mouth='smile_small', look=(-8, 4), red=0.0, blush=0.0)
    rot, dy = 0.0, 0.0
    s_t = story_t(t)
    v = voice_v(s_t, 'shoko')
    if v > 0.12: st['mouth'] = 'w' if v > 0.32 else 'smile_small'
    if L['0b'] <= s_t < ROAD4 and t < PEAK:                 # unbothered while the ginger screams
        st.update(lid=0.62, look=(-4, 2), mouth='smile_small'); rot = 1.5 * math.sin(t * 2)
    elif t < ROAD1:
        st.update(lid=0.58, look=(-6, 2))
    elif L[4] <= t < L[5]:
        st.update(lid=0.5, look=(-30, 0), mouth='smile_small')
    elif L[5] <= t < L['0b']:                               # he does not look at the nav
        st.update(lid=0.6, look=(-6, -4), mouth='smile_small')
    elif PEAK <= t < BREAK:
        st.update(lid=0.55, mouth='goofy', look=(-10, 2))
    elif t >= BREAK:                                        # the star nod
        u = t - BREAK
        st.update(lid=0.5, mouth='goofy' if v < 0.12 else st['mouth'], look=(30, 2))
        if u > 0.35: rot = 6 * math.sin((u - 0.35) * 7) * math.exp(-max(0, u - 1.6) * 2); dy = 8 * abs(math.sin((u - 0.35) * 7))
    return st, rot, dy

# ------------------------------------------------------------------ the nav phone
def nav_dist(t):
    s_t = story_t(t)
    if s_t >= L[5]: return 100
    if s_t >= L[4] - 0.3: return 200
    if s_t >= INT2: return 300
    return 400

NW, NH = 360, 220
def nav_layer(dist, talk=-1, arrow_k=0.0):
    lay = Image.new('RGBA', (S(NW), S(NH)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(NW) - 1, S(NH) - 1], radius=S(28), fill=(18, 18, 22))
    d.rounded_rectangle([S(10), S(10), S(NW - 10), S(NH - 10)], radius=S(20), fill=(214, 222, 214))
    for (a, b) in (((20, 150), (340, 120)), ((120, 20), (150, 210)), ((250, 20), (230, 210))):
        line(d, [a, b], (250, 250, 250), 14)
    line(d, [(70, 200), (150, 120), (150, 70), (90, 60)], (40, 120, 255), 12)
    E(d, 150, 160, 11, 11, fill=(40, 120, 255), outline=WHITE, width=3)
    d.rounded_rectangle([S(10), S(10), S(NW - 10), S(70)], radius=S(20), fill=(30, 140, 80))
    d.rectangle([S(10), S(50), S(NW - 10), S(70)], fill=(30, 140, 80))
    ax, ay = NW - 50, 40                                       # big left-turn arrow (top right, RTL)
    poly(d, [(ax + 14, ay + 20), (ax + 14, ay - 4), (ax - 10, ay - 4), (ax - 10, ay - 16), (ax - 30, ay + 2), (ax - 10, ay + 20), (ax - 10, ay + 8), (ax + 2, ay + 8), (ax + 2, ay + 20)], fill=WHITE)
    big = f'{dist} מ׳'
    d.text((S(NW - 86), S(40)), big, font=font(S(34), 900), fill=WHITE, anchor='rm')
    d.text((S(NW / 2), S(98)), 'הניווט', font=font(S(22), 800), fill=(70, 80, 70), anchor='mm')
    d.rounded_rectangle([S(18), S(176), S(NW - 18), S(206)], radius=S(10), fill=(240, 244, 240))
    d.text((S(NW / 2), S(191)), f'בעוד {dist} מ׳: פנה שמאלה', font=font(S(24), 900), fill=(140, 144, 150), anchor='mm')
    if talk >= 0:                                              # Sharit's little avatar while the nav speaks
        av = SH_AV[talk]; lay.alpha_composite(av, (int(S(22)), int(S(78))))
    return lay

_NC = {}
def nav_at(t):
    s_t = story_t(t)
    talk = -1
    if L[5] <= s_t < L[5] + D[5]:
        sv = voice_v(s_t, 'sh'); talk = 2 if sv > 0.3 else (1 if sv > 0.1 else 0)
    key = (nav_dist(t), talk)
    if key not in _NC:
        if len(_NC) > 40: _NC.clear()
        _NC[key] = nav_layer(*key)
    return _NC[key]

def slip_layer():
    w_, h_ = 250, 150
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(w_) - 1, S(h_) - 1], fill=(252, 252, 246), outline=(160, 160, 150), width=iw(3))
    d.rectangle([0, 0, S(w_), S(40)], fill=BLUE)
    d.text((S(w_ / 2), S(21)), 'משרד הפנים', font=font(S(26), 900), fill=WHITE, anchor='mm')
    d.text((S(w_ / 2), S(92)), 'תור · 08:00', font=font(S(44), 900), fill=RED, anchor='mm')
    return lay

# ------------------------------------------------------------------ the rider (plant b)
def rider_layer(visor=0.0, clap=0.0, mood=0):
    """a motorbike rider, head + shoulders + gloves; visor 0 down .. 1 up"""
    w_, h_ = 520, 640
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    poly(d, [(60, 640), (460, 640), (430, 400), (330, 340), (190, 340), (90, 400)], fill=(30, 32, 40), outline=(10, 10, 14), width=6)
    poly(d, [(220, 380), (300, 380), (290, 640), (230, 640)], fill=(220, 60, 50))
    face = CROWD_FACE[mood]
    lay.alpha_composite(face, (int(S(260)) - face.width // 2, int(S(205)) - face.height // 2))
    d = ImageDraw.Draw(lay)
    # helmet shell around the face
    d.arc([S(105), S(45), S(415), S(395)], 160, 380, fill=(240, 240, 244), width=iw(46))
    d.arc([S(105), S(45), S(415), S(395)], 160, 380, fill=(20, 20, 24), width=iw(4))
    vy = lerp(250, 70, visor)
    poly(d, [(140, vy - 60), (380, vy - 60), (370, vy + 20), (150, vy + 20)], fill=(40, 60, 90, 230), outline=(10, 10, 14), width=5)
    line(d, [(170, vy - 44), (230, vy - 44)], (160, 200, 240), 5)
    # gloves: clapping in front of the chest
    g = 36 + 60 * clap
    for sx in (-1, 1):
        E(d, 260 + sx * g, 500, 44, 52, fill=(20, 20, 24), outline=(0, 0, 0), width=4)
    return lay

def mirror_rider(d, c, sc=1.0):
    """the side-mirror view: a rider's helmet + headlight (small, plant b)"""
    x, y = c
    E(d, x, y + 6 * sc, 26 * sc, 26 * sc, fill=(240, 240, 244), outline=(20, 20, 24), width=3)
    poly(d, [(x - 18 * sc, y), (x + 18 * sc, y), (x + 16 * sc, y + 14 * sc), (x - 16 * sc, y + 14 * sc)], fill=(40, 60, 90))
    E(d, x, y + 44 * sc, 14 * sc, 8 * sc, fill=(255, 250, 200), outline=(120, 120, 120), width=2)

# ------------------------------------------------------------------ the car interior (frontal, through the windshield)
GHX, GHY, SHX, SHY, F = 290, 950, 800, 935, 0.90
MIR = (890, 1236)
def build_car_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W * K, H * K], fill=(62, 64, 74))                           # cabin, the headliner
    # rear window: sky + a blurred street behind
    x0, y0, x1, y1 = 130, 540, 950, 820
    for y in range(y0, y1, 6):
        v = (y - y0) / (y1 - y0)
        d.rectangle([S(x0), S(y), S(x1), S(y + 6)], fill=(int(lerp(160, 214, v)), int(lerp(204, 226, v)), int(lerp(240, 236, v))))
    for k, x in enumerate(range(x0, x1, 120)):
        d.rectangle([S(x), S(650 - 40 * (k % 3)), S(x + 100), S(y1)], fill=(206, 196, 176) if k % 2 else (186, 180, 170))
    d.rectangle([S(x0), S(760), S(x1), S(y1)], fill=(110, 110, 116))
    d.rounded_rectangle([S(x0 - 20), S(y0 - 20), S(x1 + 20), S(y1 + 20)], radius=S(40), outline=(50, 52, 60), width=iw(30))
    # seats + headrests
    for hx in (GHX, SHX):
        d.rounded_rectangle([S(hx - 120), S(700), S(hx + 120), S(860)], radius=S(40), fill=(44, 46, 54), outline=(30, 30, 36), width=iw(5))
        d.rounded_rectangle([S(hx - 240), S(880), S(hx + 240), S(1700)], radius=S(90), fill=(52, 54, 64), outline=(30, 30, 36), width=iw(6))
    img = img.filter(ImageFilter.GaussianBlur(S(1.6)))
    return img

def car_front(img, t, rider_in_mirror=True):
    """everything in front of the cats: dash, wheel, nav, glass, the car body, mirrors"""
    d = ImageDraw.Draw(img)
    # dashboard
    poly(d, [(0, 1430), (W, 1430), (W, 1600), (0, 1600)], fill=(34, 36, 42))
    d.rectangle([0, S(1420), W * K, S(1446)], fill=(58, 60, 68))
    # the vent + the nav phone on its mount
    d.rounded_rectangle([S(470), S(1440), S(620), S(1480)], radius=S(8), fill=(20, 20, 24))
    shadow_paste(img, nav_at(t), (530, 1320), 0, 1.12, 80)
    d = ImageDraw.Draw(img)
    # steering wheel (top arc) in front of Shoko
    wc = (790, 1560); r = 175
    d.arc([S(wc[0] - r), S(wc[1] - r), S(wc[0] + r), S(wc[1] + r)], 180, 360, fill=(18, 18, 22), width=iw(36))
    d.ellipse([S(wc[0] - 50), S(wc[1] - 50), S(wc[0] + 50), S(wc[1] + 50)], fill=(26, 26, 30))
    # glass reflections
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k_, xa in enumerate((180, 300, 760)):
        poly(od, [(xa, 260), (xa + 70 + 30 * k_, 260), (xa - 200 + 30 * k_, 1420), (xa - 270, 1420)], fill=(255, 255, 255, 22))
    img.alpha_composite(ov); d = ImageDraw.Draw(img)
    # the car body: roof, A-pillars, hood, wipers
    BODY = (236, 238, 242); BODY_D = (190, 194, 204)
    d.rectangle([0, 0, W * K, S(250)], fill=BODY)
    d.rectangle([0, S(228), W * K, S(256)], fill=BODY_D)
    poly(d, [(0, 250), (120, 250), (30, 1450), (0, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(W, 250), (W - 120, 250), (W - 30, 1450), (W, 1450)], fill=BODY, outline=BODY_D, width=8)
    poly(d, [(-40, 1600), (W + 40, 1600), (W + 40, 1960), (-40, 1960)], fill=BODY)
    poly(d, [(-40, 1590), (W + 40, 1590), (W + 40, 1630), (-40, 1630)], fill=BODY_D)
    for k_ in range(2):
        line(d, [(150 + k_ * 420, 1598), (480 + k_ * 420, 1560)], (30, 30, 34), 9)
    E(d, 540, 1760, 90, 24, fill=(200, 204, 214))                                     # the hood emblem (generic)
    # rear-view mirror (inside, hanging from the roof)
    d.rectangle([S(532), S(250), S(548), S(300)], fill=(30, 30, 34))
    d.rounded_rectangle([S(420), S(296), S(660), S(366)], radius=S(22), fill=(24, 24, 28), outline=(10, 10, 12), width=iw(4))
    d.rounded_rectangle([S(432), S(306), S(648), S(356)], radius=S(16), fill=(150, 176, 200))
    # the driver's side mirror (outside, image right) with the rider in it (plant b)
    mx, my = MIR
    poly(d, [(mx - 70, my - 6), (W - 10, my - 40), (W - 10, my + 10)], fill=BODY_D)
    d.rounded_rectangle([S(mx - 92), S(my - 66), S(mx + 92), S(my + 66)], radius=S(34), fill=BODY, outline=BODY_D, width=iw(6))
    d.rounded_rectangle([S(mx - 78), S(my - 52), S(mx + 78), S(my + 52)], radius=S(26), fill=(150, 178, 204))
    d.rectangle([S(mx - 78), S(my + 10), S(mx + 78), S(my + 52)], fill=(120, 120, 128))
    if rider_in_mirror: mirror_rider(d, (mx + 10, my - 24 + 2 * math.sin(t * 6)), 0.9)

def scene_car(t, i):
    img = CAR_BG.copy()
    d = ImageDraw.Draw(img)
    s_t = story_t(t)
    # bodies + seatbelts
    for hx, pal in ((GHX, GINGER), (SHX, SHOKO)):
        E(d, hx, 1560, 250, 320, fill=pal['FUR'], outline=pal['OUT'], width=7)
        E(d, hx, 1600, 120, 230, fill=pal['CREAM'])
        line(d, [(hx + 170, 1250), (hx - 150, 1600)], (30, 30, 34), 26)
    gst, grot, gdy = ginger_state(t)
    sst, srot, sdy = shoko_state(t)
    head(img, gst, i, GHX, GHY + gdy, F, grot, GINGER)
    head(img, sst, i, SHX, SHY + sdy, F, srot, SHOKO, props=True, wob=6 * math.sin(t * 3))
    d = ImageDraw.Draw(img)
    # the ginger's paws: the slip in the want, pointing in the panic, gripping the seat otherwise
    if T0 <= t < ROAD1:
        sc_ = (215 + 6 * math.sin(t * 7), 1215 + 8 * math.sin(t * 9))
        capsule(d, (GHX - 60, 1470), (sc_[0] + 80, sc_[1] + 80), 84, GINGER['FUR'], GINGER['OUT'], 4)
        shadow_paste(img, SLIP, sc_, 6 + 3 * math.sin(t * 5), 1.0, 80)
        d = ImageDraw.Draw(img); paw(d, (sc_[0] + 80, sc_[1] + 80), GINGER, -20, 0.8)
    elif (L['0b'] <= s_t < ROAD4 and t < PEAK) or (shot(t)[0] == 'car' and ROAD4 <= t < PEAK):
        tip = (650 + 14 * math.sin(t * 16), 1080 - 10 * abs(math.sin(t * 10)))         # pointing across, at the left turn
        capsule(d, (GHX + 120, 1420), tip, 80, GINGER['FUR'], GINGER['OUT'], 4); paw(d, tip, GINGER, -60, 0.85)
    elif PEAK <= t < BREAK:                                          # bracing on the dash
        for px in (200, 400):
            capsule(d, (GHX + (px - 300) * 0.6, 1430), (px, 1440), 80, GINGER['FUR'], GINGER['OUT'], 4); paw(d, (px, 1440), GINGER, 0, 0.85)
    # Shoko: one paw on the wheel (top), the other lazy on the window
    car_front(img, t)
    d = ImageDraw.Draw(img)
    wp = (760 + (14 * math.sin(t * 2) if t < PEAK else 0), 1392)
    capsule(d, (SHX + 60, 1640), wp, 82, SHOKO['FUR'], SHOKO['OUT'], 4); paw(d, wp, SHOKO, 10, 0.85)
    if t >= BREAK:                                                   # the rider rolls up in front, visor up, slow claps
        u = t - BREAK
        x = lerp(1400, 850, ease_out(clamp(u / 0.35)))
        visor = ease_out(clamp((u - 0.25) / 0.25))
        clap = abs(math.cos(max(0, u - 0.5) * 3.2)) if u > 0.5 else 1.0
        shadow_paste(img, RIDERS[(int(round(visor * 4)), int(round(clap * 4)))], (x, 1480), -4, 1.0, 80)
        d = ImageDraw.Draw(img)
        if u > 0.5 and clap < 0.15:
            for k_ in range(3):
                a_ = math.radians(-120 + k_ * 30)
                line(d, [(x - 10 + 70 * math.cos(a_), 1410 + 70 * math.sin(a_)), (x - 10 + 110 * math.cos(a_), 1410 + 110 * math.sin(a_))], (255, 255, 255), 6)
    return img

# ------------------------------------------------------------------ the road (side view)
SKY = None
def build_road_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, 820, 8):
        v = y / 820
        d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(150, 210, v)), int(lerp(200, 228, v)), int(lerp(244, 244, v))))
    d.rectangle([0, S(1060), W * K, H * K], fill=(92, 94, 102))                     # asphalt
    d.rectangle([0, S(1600), W * K, H * K], fill=(170, 168, 164))                   # near sidewalk
    d.rectangle([0, S(1590), W * K, S(1606)], fill=(230, 230, 230))
    img = img.filter(ImageFilter.GaussianBlur(S(1.0)))
    return img

BUILD = [(x, h, c) for x, h, c in ((0, 420, (214, 198, 170)), (230, 520, (232, 216, 186)), (470, 380, (200, 190, 176)),
                                     (650, 560, (226, 210, 180)), (900, 450, (210, 200, 184)), (1130, 500, (232, 216, 186)))]
def buildings(d, off):
    span = 1360
    for x, h, c in BUILD:
        xx = (x - off * 0.35) % span - 160
        d.rectangle([S(xx), S(1060 - h), S(xx + 220), S(1060)], fill=c, outline=(170, 156, 130), width=iw(3))
        for r_ in range(int(h / 110)):
            for c_ in range(2):
                d.rectangle([S(xx + 34 + c_ * 92), S(1060 - h + 40 + r_ * 110), S(xx + 94 + c_ * 92), S(1060 - h + 100 + r_ * 110)], fill=(90, 110, 130))

def lanes(d, off):
    for x in range(-200, W + 200, 160):
        xx = (x - off) % (W + 320) - 160
        d.rectangle([S(xx), S(1318), S(xx + 90), S(1330)], fill=(240, 240, 240))
    d.rectangle([0, S(1062), W * K, S(1070)], fill=(240, 220, 80))

CAR_COLS = [(200, 60, 60), (70, 110, 190), (230, 230, 236), (60, 150, 110), (240, 190, 60), (130, 130, 140), (180, 90, 160)]
def car_side(img, x, y, sc, col, faces=(), facing=1, extra=None, t=0.0):
    """a side-view car; x,y = body centre bottom; faces = [(sprite name, mood, dx)] in the windows"""
    d = ImageDraw.Draw(img)
    w_, h_ = 480 * sc, 150 * sc
    d.rounded_rectangle([S(x - w_ / 2), S(y - h_), S(x + w_ / 2), S(y)], radius=S(40 * sc), fill=col, outline=(20, 20, 24), width=iw(4))
    poly(d, [(x - w_ * 0.30, y - h_), (x - w_ * 0.18, y - h_ - 100 * sc), (x + w_ * 0.22, y - h_ - 100 * sc), (x + w_ * 0.36, y - h_)], fill=col, outline=(20, 20, 24), width=4)
    poly(d, [(x - w_ * 0.26, y - h_ - 6 * sc), (x - w_ * 0.16, y - h_ - 88 * sc), (x + w_ * 0.20, y - h_ - 88 * sc), (x + w_ * 0.31, y - h_ - 6 * sc)], fill=(170, 200, 224))
    for fn in faces:
        name, mood, dx, fsc = fn
        if name in ('ginger', 'shoko'):
            st = E3.base_state(); st.update(mood)
            head(img, st, 0, x + dx * sc, y - h_ - 40 * sc, fsc * sc, 0, GINGER if name == 'ginger' else SHOKO, props=(name == 'shoko'))
        else:
            E13.paste_sprite(img, name, mood, x + dx * sc, y - h_ - 34 * sc, fsc * sc, flip=facing < 0)
    d = ImageDraw.Draw(img)
    line(d, [(x + w_ * 0.02, y - h_ - 6 * sc), (x + w_ * 0.02, y - h_ - 88 * sc)], (20, 20, 24), 6)
    for wx in (-0.30, 0.30):
        E(d, x + w_ * wx, y, 48 * sc, 48 * sc, fill=(24, 24, 28)); E(d, x + w_ * wx, y, 22 * sc, 22 * sc, fill=(160, 160, 170))
    hx_ = x + facing * w_ / 2
    E(d, hx_ - facing * 10 * sc, y - h_ * 0.6, 12 * sc, 9 * sc, fill=(255, 246, 190))
    if extra: extra(img, x, y, sc)

def roof_plant(img, x, y, sc):
    d = ImageDraw.Draw(img)
    top = y - 250 * sc
    poly(d, [(x - 30 * sc, top), (x + 30 * sc, top), (x + 22 * sc, top - 50 * sc), (x - 22 * sc, top - 50 * sc)], fill=(170, 90, 50), outline=(80, 40, 20), width=3)
    for k_ in range(5): E(d, x - 30 * sc + k_ * 15 * sc, top - 70 * sc - 10 * sc * (k_ % 2), 22 * sc, 16 * sc, fill=(70, 150, 70), outline=(40, 90, 40), width=2)
    E13.paste_sprite(img, 'c1', 0, x + 110 * sc, top - 40 * sc, 0.34 * sc)          # a man standing by the car, watering
    d = ImageDraw.Draw(img)
    poly(d, [(x + 40 * sc, top - 40 * sc), (x + 80 * sc, top - 60 * sc), (x + 80 * sc, top - 30 * sc)], fill=(60, 120, 200))
    for k_ in range(4): line(d, [(x + 36 * sc - k_ * 6 * sc, top - 40 * sc + k_ * 4), (x + 20 * sc - k_ * 6 * sc, top - 10 * sc)], (120, 180, 255), 3)

def pillow(img, x, y, sc):
    d = ImageDraw.Draw(img)
    E(d, x - 30 * sc, y - 210 * sc, 50 * sc, 26 * sc, fill=(240, 240, 252), outline=(150, 150, 170), width=3)
    for k_ in range(3):
        d.text((S(x + 10 * sc + k_ * 30 * sc), S(y - 300 * sc - k_ * 34 * sc)), 'Z', font=font(S(40 * sc + k_ * 10 * sc), 900), fill=(40, 40, 80), anchor='mm')

def sandwiches(img, x, y, sc):
    d = ImageDraw.Draw(img)
    for k_, dx in enumerate((-60, 60)):
        cx = x + dx * sc; cy = y - 190 * sc
        poly(d, [(cx - 34 * sc, cy), (cx + 34 * sc, cy - 8 * sc), (cx + 30 * sc, cy + 16 * sc), (cx - 30 * sc, cy + 20 * sc)], fill=(236, 200, 140), outline=(140, 100, 60), width=3)
        line(d, [(cx - 30 * sc, cy + 8 * sc), (cx + 30 * sc, cy + 2 * sc)], (90, 170, 70), 4)

def bus(img, x, y, sc, t):
    d = ImageDraw.Draw(img)
    w_, h_ = 1200 * sc, 380 * sc
    d.rounded_rectangle([S(x - w_ / 2), S(y - h_), S(x + w_ / 2), S(y)], radius=S(30 * sc), fill=(240, 240, 236), outline=(20, 20, 24), width=iw(4))
    d.rectangle([S(x - w_ / 2), S(y - 70 * sc), S(x + w_ / 2), S(y - 40 * sc)], fill=(40, 120, 200))
    for k_ in range(6):
        wx = x - w_ / 2 + 60 * sc + k_ * 185 * sc
        d.rectangle([S(wx), S(y - h_ + 40 * sc), S(wx + 150 * sc), S(y - h_ + 190 * sc)], fill=(160, 196, 222), outline=(30, 30, 34), width=iw(3))
    # Sharit in the 4th window, waving
    wx = x - w_ / 2 + 60 * sc + 3 * 185 * sc + 75 * sc
    av = SH_AV_BIG; sz = (int(av.width * sc * 1.2), int(av.height * sc * 1.2))
    img.alpha_composite(av.resize(sz, Image.BICUBIC), (int(S(wx) - sz[0] / 2), int(S(y - h_ + 120 * sc) - sz[1] / 2)))
    d = ImageDraw.Draw(img)
    hw = x and (wx + 70 * sc, y - h_ + 70 * sc + 12 * sc * math.sin(t * 14))
    E(d, hw[0], hw[1], 22 * sc, 26 * sc, fill=SH.SKIN, outline=SH.SKIN_O, width=3)
    for wx2 in (-0.36, 0.36):
        E(d, x + w_ * wx2, y, 56 * sc, 56 * sc, fill=(24, 24, 28)); E(d, x + w_ * wx2, y, 26 * sc, 26 * sc, fill=(160, 160, 170))

QUEUE_CARS = [  # (x in the queue world, colour, faces, extra)
    (0, 0, [('c1', 2, 40, 0.30)], None),
    (560, 1, [('c0', 2, 40, 0.30)], pillow),                       # the sleeper on his pillow
    (1120, 3, [('c2', 0, -10, 0.26), ('c4', 0, 70, 0.24)], sandwiches),   # the family with sandwiches
    (1680, 4, [('c3', 2, 40, 0.30)], roof_plant),                  # watering a plant on his roof
    (2240, 5, [('c4', 0, 40, 0.30)], None),
]
def queue_lane(img, off, t, y=1060, sc=0.82, bus_at=None):
    for qx, ci, faces, extra in QUEUE_CARS:
        x = qx * sc - off
        if -400 < x < W + 400:
            car_side(img, x, y, sc, CAR_COLS[ci], faces, 1, extra, t)
    if bus_at is not None:
        x = bus_at - off
        if -800 < x < W + 800: bus(img, x, y, sc, t)

OUR_Y = 1520
def our_car(img, x, y, t, sc=1.0, faces=None):
    gst = dict(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-16, sweat=0.8, look=(-30, 0))
    sst = dict(lid=0.6, brow='annoyed', mouth='smile_small', look=(-20, 0))
    car_side(img, x, y, sc, (236, 238, 242), faces or [('shoko', sst, 50, 0.36), ('ginger', gst, -60, 0.40)], 1, None, t)

def scene_road(t, i, kind):
    img = ROAD_BG.copy(); d = ImageDraw.Draw(img)
    s_t = t
    if kind == 'road1':                         # the empty straight lane: fast, the queue just starting on the left lane
        u = t - ROAD1; off = 900 * u
        buildings(d, off); lanes(d, off)
        queue_lane(img, -700 + off * 0.9, t)
        our_car(img, 540 + 10 * math.sin(t * 20), OUR_Y, t)
        d = ImageDraw.Draw(img)
        for k_ in range(6):                     # speed lines
            yy = 1300 + k_ * 40; xx = (k_ * 170 - u * 2600) % 1300 - 200
            line(d, [(xx, yy), (xx + 160, yy)], (255, 255, 255), 5)
    elif kind == 'road2':                       # the absurd queue passing
        u = t - ROAD2; off = 150 + 900 * u
        buildings(d, off); lanes(d, off)
        queue_lane(img, off, t)
        our_car(img, 520, OUR_Y, t)
    elif kind == 'road3':                       # the bus, Sharit waving
        u = t - ROAD3; off = 2650 + 260 * u
        buildings(d, off); lanes(d, off)
        queue_lane(img, off, t, bus_at=3280)
        our_car(img, 420, OUR_Y, t)
    else:                                       # road4 v2: top-down junction — green straight, last-second left, the drift
        return scene_drift(t, i)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= s_t < c_ + 0.5: E18.burst(img, (540, 1300), s_t - c_, (120, 255, 160) if c_ != CHK3 else (255, 220, 120), 170, 10, 0.4)
    if GOLDT <= s_t < BREAK: E18.confetti(img, s_t - GOLDT + 0.3)
    return img

def scene(t, i):
    name = shot(t)[0]
    if name in ('road1', 'road2', 'road3', 'road4'): return scene_road(t, i, name)
    img = scene_car(t, i)
    if GOLDT <= t < BREAK: E18.confetti(img, t - GOLDT + 0.3)
    return img


# ------------------------------------------------------------------ v2: the drift (top-down)
LANE_L, LANE_S, STOP_Y = 380, 640, 640          # left-turn lane centre, straight lane centre, stop line
HEAD = (LANE_L, STOP_Y + 180)                  # the empty head of the left lane (car centre)
def _bez(p, u):
    a, b, c, d_ = p; v = 1 - u
    return (v ** 3 * a[0] + 3 * v * v * u * b[0] + 3 * v * u * u * c[0] + u ** 3 * d_[0],
            v ** 3 * a[1] + 3 * v * v * u * b[1] + 3 * v * u * u * c[1] + u ** 3 * d_[1])
DRIFT_P = [(LANE_S, 1250), (LANE_S, 980), (LANE_L + 30, 1060), HEAD]
def _slip(u):
    """slip angle (°): the rear steps out fast after the flick, holds, then is caught as the car lands"""
    if u < 0.10: return 0.0
    if u < 0.35: return 36 * ease_out((u - 0.10) / 0.25)
    if u < 0.75: return 36 - 4 * (u - 0.35) / 0.40
    return 32 * (1 - ease_io((u - 0.75) / 0.25))
def car_pose(t):
    """(x, y, body angle ° CCW from 'up', slip °, front-wheel steer °, phase)"""
    if t < SWERVE[0]:                                           # flying up the straight lane on green
        k = clamp((t - ROAD4) / max(0.01, SWERVE[0] - ROAD4))
        return LANE_S, lerp(2150, DRIFT_P[0][1], k), 0.0, 0.0, 0.0, 'fly'
    if t < SWERVE[1]:
        u = (t - SWERVE[0]) / (SWERVE[1] - SWERVE[0])
        e = 1 - (1 - u) ** 2.0                                   # fast in, scrubbing speed
        x, y = _bez(DRIFT_P, e)
        x2, y2 = _bez(DRIFT_P, min(1.0, e + 0.01))
        if e >= 0.99: x2, y2 = x - (DRIFT_P[3][0] - DRIFT_P[2][0]) * 0.01, y - 1.0
        vel = math.degrees(math.atan2(-(x2 - x), -(y2 - y)))     # CCW from up
        sl = _slip(u)
        flick = -9 * math.sin(math.pi * clamp(u / 0.10))         # the feint right before the rear steps out
        steer = 16 * math.sin(math.pi * clamp(u / 0.10)) if u < 0.10 else -0.55 * sl   # counter-steer
        return x, y, vel + sl + flick, sl, steer, 'drift'
    u = clamp((t - SWERVE[1]) / 0.70)                           # the turn-away to the left, on the green arrow
    k = ease_in(u)
    x = lerp(HEAD[0], -300, k); y = lerp(HEAD[1], STOP_Y - 330, ease_out(u))
    return x, y, lerp(6, 90, ease_out(u)), 0.0, 28 * (1 - u), 'away'

def car_top_v2(col, steer=0.0):
    lay = Image.new('RGBA', (S(240), S(400)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for wx, wy, st_ in ((26, 88, steer), (214, 88, steer), (26, 312, 0), (214, 312, 0)):
        poly(d, xform([(-16, -36), (16, -36), (16, 36), (-16, 36)], wx, wy, st_), fill=(20, 20, 24))
    d.rounded_rectangle([S(30), S(20), S(210), S(380)], radius=S(46), fill=col, outline=(30, 30, 34), width=iw(5))
    d.rounded_rectangle([S(48), S(100), S(192), S(156)], radius=S(16), fill=(120, 150, 180))
    d.rounded_rectangle([S(52), S(276), S(188), S(322)], radius=S(16), fill=(120, 150, 180))
    d.rounded_rectangle([S(50), S(156), S(190), S(276)], radius=S(12), fill=tuple(max(0, c - 22) for c in col))
    for x in (54, 186): E(d, x, 34, 16, 10, fill=(255, 246, 190))
    for x in (54, 186): E(d, x, 366, 16, 8, fill=(255, 60, 60))
    return lay

def rear_wheels(x, y, ang, sc):
    a = math.radians(ang); out = []
    for wx in (-94, 94):
        dx, dy = wx * sc, 112 * sc                  # rear axle (the car points up; +y = back)
        out.append((x + dx * math.cos(a) + dy * math.sin(a), y - dx * math.sin(a) + dy * math.cos(a)))
    return out

def signal_head(d, cx, cy, kind, green):
    d.rounded_rectangle([S(cx - 60), S(cy - 120), S(cx + 60), S(cy + 120)], radius=S(18), fill=(26, 26, 30), outline=(8, 8, 10), width=iw(5))
    E(d, cx, cy - 58, 42, 42, fill=(255, 60, 50) if not green else (70, 20, 20))
    E(d, cx, cy + 58, 42, 42, fill=(16, 30, 18))
    ink = (60, 230, 90) if green else (24, 70, 34)
    if kind == 'straight':
        poly(d, [(cx - 9, cy + 88), (cx + 9, cy + 88), (cx + 9, cy + 58), (cx + 24, cy + 58), (cx, cy + 30), (cx - 24, cy + 58), (cx - 9, cy + 58)], fill=ink)
    else:
        poly(d, [(cx + 20, cy + 88), (cx + 4, cy + 88), (cx + 4, cy + 66), (cx - 6, cy + 66), (cx - 6, cy + 80), (cx - 32, cy + 56), (cx - 6, cy + 32), (cx - 6, cy + 46), (cx + 20, cy + 46)], fill=ink)

DRIFT_BG = None; QTOP = []
def build_drift_bg():
    img = Image.new('RGBA', (W * K, H * K), (88, 90, 98, 255)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S(150), H * K], fill=(170, 168, 164)); d.rectangle([S(150), 0, S(162), H * K], fill=(226, 226, 222))
    d.rectangle([S(918), 0, W * K, H * K], fill=(170, 168, 164)); d.rectangle([S(906), 0, S(918), H * K], fill=(226, 226, 222))
    d.rectangle([0, S(300), W * K, S(STOP_Y - 20)], fill=(80, 82, 90))                         # the crossing road
    for x in range(0, W, 140): d.rectangle([S(x), S(460), S(x + 80), S(472)], fill=(236, 236, 236))
    for y in range(STOP_Y + 20, H, 60): d.rectangle([S(504), S(y), S(516), S(y + 30)], fill=(240, 240, 240))   # left | straight
    for y in range(STOP_Y + 20, H, 120): d.rectangle([S(772), S(y), S(784), S(y + 60)], fill=(240, 240, 240))
    d.rectangle([S(162), S(STOP_Y), S(906), S(STOP_Y + 14)], fill=(244, 244, 244))              # stop line
    for cx, kind in ((LANE_L, 'left'), (LANE_S, 'straight')):                                  # arrows painted on the road
        y0 = STOP_Y + 1180
        if kind == 'straight':
            poly(d, [(cx - 14, y0 + 120), (cx + 14, y0 + 120), (cx + 14, y0 + 40), (cx + 36, y0 + 40), (cx, y0), (cx - 36, y0 + 40), (cx - 14, y0 + 40)], fill=(236, 236, 236))
        else:
            poly(d, [(cx + 14, y0 + 120), (cx - 14, y0 + 120), (cx - 14, y0 + 40), (cx - 40, y0 + 40), (cx - 40, y0 + 60), (cx - 80, y0 + 20), (cx - 40, y0 - 20), (cx - 40, y0), (cx + 14, y0)], fill=(236, 236, 236))
    for k in range(6): E(d, 75, 300 + k * 330, 60, 60, fill=(70, 140, 70), outline=(40, 90, 40), width=5)
    for k in range(6): E(d, 1000, 140 + k * 330, 60, 60, fill=(70, 140, 70), outline=(40, 90, 40), width=5)
    return img.filter(ImageFilter.GaussianBlur(S(0.6)))

QCOLS = [1, 3, 4, 5, 0]
def scene_drift(t, i):
    img = DRIFT_BG.copy(); d = ImageDraw.Draw(img)
    x, y, ang, slip, steer, phase = car_pose(t)
    green_left = t >= CHK3
    if t > SWERVE[0] + 0.05:                                    # skid marks: the rear wheels' path while sliding
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        trail = [[], []]; tt = SWERVE[0] + 0.05
        while tt <= min(t, SWERVE[1]):
            xx, yy, aa, sl, _, _ = car_pose(tt)
            for j, p in enumerate(rear_wheels(xx, yy, aa, 0.86)): trail[j].append(p)
            tt += 1 / 60
        for tr in trail:
            if len(tr) > 1: line(od, tr, (22, 22, 24, 140), 24)
        img.alpha_composite(ov); d = ImageDraw.Draw(img)
    # the left-turn queue, stopped on red; its first car (the sleeper) a full length back — the gap at the head
    for k_, yy in enumerate((1230, 1590, 1950)):
        c = QTOP[k_]; img.alpha_composite(c, (S(LANE_L) - c.width // 2, S(yy) - c.height // 2))
    for k_, yy in enumerate((1230, 1590)):                     # faces through the windshields (they watch)
        E13.paste_sprite(img, ('c0', 'c2')[k_], 1 if t >= SWERVE[0] + 0.3 else 0, LANE_L, yy - 60, 0.22)
    # the straight lane is moving on green: a car ahead already through the junction
    c = QTOP[3]; img.alpha_composite(c, (S(LANE_S) - c.width // 2, int(S(lerp(380, -320, clamp((t - ROAD4) / 1.0)))) - c.height // 2))
    if SWERVE[0] + 0.05 < t < SWERVE[1] + 1.0:                  # tyre smoke from the rear wheels
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for n_ in range(40):
            te = SWERVE[0] + 0.12 + n_ * 0.045
            if te > min(t, SWERVE[1] - 0.08): break
            age = t - te
            if age > 0.9: continue
            xx, yy, aa, sl, _, _ = car_pose(te)
            for j, p in enumerate(rear_wheels(xx, yy, aa, 0.86)):
                r = 36 + 170 * age
                a = int(180 * (1 - age / 0.9) * min(1.0, sl / 20 + 0.2))
                E(od, p[0] + 70 * age * (1 if j else -1), p[1] + 110 * age, r, r * 0.8, fill=(228, 228, 232, a))
        img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(S(5))))
    sp = car_top_v2((236, 238, 242), steer).resize((S(206), S(344)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', sp.size, (0, 0, 0, 0)); sh.putalpha(sp.split()[3].point(lambda v: int(v * 0.35)))
    img.alpha_composite(sh, (int(S(x + 14) - sp.width / 2), int(S(y + 20) - sp.height / 2)))
    img.alpha_composite(sp, (int(S(x) - sp.width / 2), int(S(y) - sp.height / 2)))
    d = ImageDraw.Draw(img)
    if phase == 'fly':                                          # speed lines behind the car
        for k_ in range(5):
            yy = y + 220 + k_ * 60 + (t * 3000) % 120
            line(d, [(x - 90 + k_ * 45, yy), (x - 90 + k_ * 45, yy + 130)], (255, 255, 255), 5)
    # the gantry: straight = green all along (they were moving), left arrow red → green on the exact second
    d.rectangle([S(170), S(140), S(900), S(166)], fill=(60, 62, 70))
    signal_head(d, LANE_L, 270, 'left', green_left)
    signal_head(d, LANE_S, 270, 'straight', True)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for cx, g in ((LANE_L, green_left), (LANE_S, True)):
        if g: E(od, cx, 328, 110, 110, fill=(60, 230, 90, 60))
    img.alpha_composite(ov); d = ImageDraw.Draw(img)
    if CHK3 <= t < CHK3 + 0.45:                                 # the exact second: rings on the arrow and on the car
        u = (t - CHK3) / 0.45
        for c_ in ((LANE_L, 328), HEAD):
            r = 80 + 220 * u
            d.ellipse([S(c_[0] - r), S(c_[1] - r), S(c_[0] + r), S(c_[1] + r)], outline=(255, 230, 90), width=iw(10 * (1 - u) + 1))
    if t >= SWERVE[0] + 0.35:                                   # horns from the queue
        for k_, (hx, hy) in enumerate(((LANE_L + 150, 1150), (LANE_L + 150, 1510))):
            ph = (t * 6 + k_ * 0.7) % 1.0
            for j in range(3):
                r = 30 + 40 * j + 24 * ph
                d.arc([S(hx - r), S(hy - r), S(hx + r), S(hy + r)], 290, 70, fill=(255, 230, 60), width=iw(7))
            d.text((S(hx + 60), S(hy - 110 - 10 * ph)), 'טוּט!', font=font(S(50), 900), fill=(255, 230, 60), anchor='mm', stroke_width=iw(6), stroke_fill=(20, 20, 24))
    # the duo in a corner bubble (second character in the shot): the ginger screaming, Shoko cool
    gst = E3.base_state(); gst.update(lid=0.0, pupil='tiny', brow='up', mouth='w', ear_dy=-30, sweat=1.0, look=(-20, -10), red=0.0, blush=0.0)
    if t >= CHK3: gst.update(lid=0.97)
    sst = E3.base_state(); sst.update(lid=0.55, brow='annoyed', mouth='smile_small', look=(-10, 0), red=0.0, blush=0.0)
    d.ellipse([S(735), S(1395), S(1065), S(1725)], fill=(250, 250, 248), outline=(20, 20, 24), width=iw(8))
    head(img, gst, i, 840, 1575, 0.44, 8 * math.sin(t * 30) if phase == 'drift' else 0, GINGER)
    head(img, sst, i, 965, 1565, 0.40, 0, SHOKO, props=True)
    return img

def drift_view(t):
    """camera for the drift: follow the car, tilt with the slide (opposite to the yaw, like a chase cam)"""
    x, y, ang, slip, steer, phase = car_pose(t)
    cy = clamp(y - 100, 760, 1200) if phase != 'away' else 900
    return 1.10, lerp(560, clamp(x, 430, 680), 0.6), cy, -0.10 * slip

# ------------------------------------------------------------------ overlays
CHIP_Y = 200
CHIPS = [('נתיב', 820, CHK1), ('פקק', 540, CHK2), ('שמאלה', 260, CHK3)]
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
    lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

# ------------------------------------------------------------------ the real-seconds clock: "התור בעוד 00:SS"
CLOCK_LABEL = ['התור', 'בעוד']
ZERO = CHK3 + 1.0                           # through with one second to spare: the clock stops green on 00:01
def clock_state(t):
    name = shot(t)[0]
    st = story_t(t)
    if name == 'rewind': return C.secs_left(st, ZERO), 'run', True
    if t >= CHK3: return C.secs_left(CHK3, ZERO), 'done', False
    s = C.secs_left(st, ZERO)
    return s, ('hot' if s <= 5 else 'run'), False

CAR_BG = ROAD_BG = SLIP = SH_AV = SH_AV_BIG = PILL_EP = PILL_Q = PILL_SER = None
RIDERS = {}; CROWD_FACE = []
def init_all():
    global CAR_BG, ROAD_BG, SLIP, SH_AV, SH_AV_BIG, PILL_EP, PILL_Q, PILL_SER, CROWD_FACE
    m.init_static(); E3.init_all()
    E13.build_crowd()
    CAR_BG = build_car_bg(); ROAD_BG = build_road_bg(); SLIP = slip_layer()
    global DRIFT_BG, QTOP
    DRIFT_BG = build_drift_bg(); QTOP = [car_top_v2(CAR_COLS[c]).resize((S(190), S(318)), Image.LANCZOS) for c in QCOLS]
    SH_AV = []
    for mo in ('lazy', 'talk', 'grin'):
        st = SH.base(); st.update(mouth=mo, lid=0.6, look=(0, 6), snack=False)
        lay = SH.draw(st, 3 if mo == 'talk' else 0).crop((S(130), S(110), S(570), S(500)))
        SH_AV.append(lay.resize((S(84), int(S(84) * lay.height / lay.width)), Image.LANCZOS))
    st = SH.base(); st.update(mouth='grin', lid=0.5, look=(-10, 6), blush=0.8)
    lay = SH.draw(st, 0).crop((S(110), S(90), S(590), S(520)))
    SH_AV_BIG = lay.resize((S(150), int(S(150) * lay.height / lay.width)), Image.LANCZOS)
    face = E13.CROWD['c3'][0]                                          # the rider: a generic grey cat (not Sharit, she has her own role)
    CROWD_FACE = [face.resize((S(200), S(200)), Image.LANCZOS)]
    for v_ in range(5):
        for c_ in range(5): RIDERS[(v_, c_)] = rider_layer(v_ / 4, c_ / 4)
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_SER = HUD._pill(SERIES_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'car':
        z, cx, cy = 1.06 + 0.01 * pu, 540, 1060
        if a == 0.0:                                   # cold open: on the ginger screaming, the nav + Shoko's calm in frame
            z, cx, cy = 1.16 + 0.03 * t, 520, 1080
            if t < 0.3: z = 1.36 - 0.20 * ease_out(t / 0.3)
        elif t < ROAD1: z, cx, cy = 1.12, 500, 1100     # the want: the slip
        elif t < ROAD2: z, cx, cy = 1.10, 520, 1060     # "המסכנים" — the ginger looks out
        elif t < L[5]: z, cx, cy = 1.14, 500, 1040      # "שרית?! גם בפקק?!"
        elif t < L['0b']:                               # the nav speaks: push to the nav + both faces
            k = ease_io(clamp((t - L[5]) / 1.2)); z, cx, cy = lerp(1.08, 1.30, k), 545, lerp(1060, 1180, k)
        elif t < ROAD4: z, cx, cy = 1.14, 520, 1080
        elif t < BREAK:                                 # the peak
            k = ease_io(clamp((t - PEAK) / (BREAK - PEAK))); z, cx, cy = lerp(1.10, 1.24, k), lerp(540, 470, k), 1060
        else:
            z, cx, cy = 1.04, 560, 1100                 # the break: wide enough for the rider + both faces
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1060
    elif name.startswith('road'):
        z, cx, cy = 1.0, 540, 960
        if name == 'road4': z, cx, cy, _r = drift_view(t)
    elif name == 'frozen':
        z, cx, cy = 1.12 + 0.03 * pu, 520, 1080
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    else: img = scene(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (CHK3, BREAK):
        if 0 <= t - s_ < 0.3: shake = 12 * math.exp(-(t - s_) * 8)
    if name == 'road4' and SWERVE[0] <= t < SWERVE[1]: shake = max(shake, 5)
    if name == 'road4':
        _r = drift_view(t)[3]
        if abs(_r) > 0.05: img = img.rotate(_r, resample=Image.BICUBIC, center=(S(ccx), S(ccy)), fillcolor=(88, 90, 98, 255))
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if t < COLD_END: frame = frame.rotate(4, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(236, 238, 242, 255))
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(50 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK, ROAD1, ROAD2, INT2, INT3, ROAD4, PEAK):
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
            m.paste_center(frame, sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < ROAD1) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_SER, (40, 70 + PILL_EP.height + 6))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    if t < DUR - 0.25 and t < BREAK:
        s, state, scr = clock_state(t)
        C.draw(frame, CLOCK_LABEL, s, state, t, scr)
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio: voices + SFX + road tone + the comic underscore (music arm)
SR = m.SR
def underscore(n):
    """original comic underscore made in code: a bouncy pizzicato bass + a sneaky plucked line, 150 bpm, F minor-ish"""
    out = np.zeros(n)
    beat = 60 / 150
    bass = [41, 41, 48, 41, 44, 44, 46, 48]           # midi
    mel = [65, None, 68, 67, None, 65, 63, None, 65, None, 68, 70, None, 72, 70, 68]
    t = RW[1]; k = 0
    while t < PEAK - 0.05:
        f = m.midi(bass[k % len(bass)])
        m.add(out, m.tone(f, 0.32, harm=((1, 1), (2, 0.5), (3, 0.2)), decay=9), t, 0.55)
        mn = mel[(k * 2) % len(mel)]
        if mn: m.add(out, m.tone(m.midi(mn + 12), 0.18, harm=((1, 1), (3, 0.25)), decay=14), t, 0.22)
        mn2 = mel[(k * 2 + 1) % len(mel)]
        if mn2: m.add(out, m.tone(m.midi(mn2 + 12), 0.18, harm=((1, 1), (3, 0.25)), decay=14), t + beat / 2, 0.20)
        if k % 2 == 1: m.add(out, m.highpass(np.random.default_rng(k).standard_normal(int(0.03 * SR)), 5000) * np.exp(-np.arange(int(0.03 * SR)) / SR * 120), t, 0.05)
        t += beat; k += 1
    cut = int(PEAK * SR); out[cut:] = 0
    fade = int(0.04 * SR); out[max(0, cut - fade):cut] *= np.linspace(1, 0, min(fade, cut))
    return out

def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(44)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'sh': y = m.phone_line(y) * 1.6                       # the nav voice through the phone
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
    def horn(t0, f=420, ln=0.5, g=0.12):
        tt = tt_(ln); sig = np.sign(np.sin(2 * np.pi * f * tt)) * 0.5 + np.sign(np.sin(2 * np.pi * f * 1.26 * tt)) * 0.5
        add(sfx, m.lowpass(sig, 2500) * np.minimum(1, np.minimum(tt / 0.02, (ln - tt) / 0.03)), t0, g)
    def clap(t0, g=0.25): add(sfx, m.bandpass(nz(0.05), 900, 5000) * np.exp(-tt_(0.05) * 70), t0, g)
    add(sfx, thud(0.6), 0.0)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.lowpass(nz(DUR), 160) * 0.8, 0.0, 0.03)                          # engine / road rumble
    for t_ in (ROAD1, ROAD2, ROAD3, ROAD4): whoosh(t_ + 0.05, 0.10, 0.3)
    check(CHK1, 0.15); check(CHK2, 0.16)
    tt = tt_(0.18); add(sfx, np.sin(2 * np.pi * 880 * tt) * np.exp(-tt * 20), L[5] - 0.25, 0.10)   # the nav chime
    tt = tt_(SWERVE[0] - ROAD4); add(sfx, m.lowpass(np.sign(np.sin(2 * np.pi * np.cumsum(90 + 60 * tt / max(tt[-1], 1e-3)) / SR)), 900) * 0.5, ROAD4, 0.05)   # flying: the engine up
    add(sfx, m.highpass(nz(0.04), 1500) * np.exp(-tt_(0.04) * 60), SWERVE[0] - 0.02, 0.35)               # the handbrake click
    dl = SWERVE[1] - SWERVE[0] + 0.1; tt = tt_(dl)
    sq = np.sin(2 * np.pi * np.cumsum(1500 + 500 * np.sin(2 * np.pi * 7 * tt) + 300 * np.sin(2 * np.pi * 2.3 * tt)) / SR)
    env_ = np.minimum(1, tt / 0.05) * np.minimum(1, (dl - tt) / 0.25)
    add(sfx, (m.bandpass(nz(dl), 1200, 3800) * 0.6 + sq * 0.5) * env_, SWERVE[0] + 0.02, 0.10)            # the screech
    add(sfx, m.lowpass(nz(dl), 300) * env_, SWERVE[0], 0.10)                                              # the slide rumble
    tt = tt_(0.6); add(sfx, m.lowpass(np.sign(np.sin(2 * np.pi * np.cumsum(110 + 160 * tt) / SR)), 1200) * np.exp(-tt * 2) * 0.5, CHK3, 0.07)   # away on the green
    for k, (f, dt) in enumerate(((420, 0.0), (360, 0.12), (500, 0.25), (330, 0.38), (450, 0.55))):
        horn(SWERVE[0] + 0.40 + dt, f, 0.45 + 0.1 * (k % 2), 0.10)
    check(CHK3, 0.2, True)
    heartbeat(HOLD[0] + 0.04); heartbeat(HOLD[0] + 0.30, 0.5)
    add(sfx, m.lowpass(nz(0.5), 300) * np.linspace(1, 0, int(0.5 * SR)), BREAK, 0.08)   # the bike pulls up
    u0 = BREAK + 0.5
    for k in range(4): clap(u0 + k * 0.98 / 1.0, 0.3)                                    # slow claps (one every ~1 s)
    add(sfx, m.tone(82.4, 1.0, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), FREEZE - 0.2, 0.12)
    # the underscore, ducked ≥12 dB under the voices
    mus = underscore(n)
    env = np.abs(voice); win = int(0.08 * SR)
    env = np.convolve(env, np.ones(win) / win, mode='same')
    duck = np.where(env > 0.01, 0.22, 1.0)                                     # 0.22 ≈ -13 dB
    sm = int(0.06 * SR); duck = np.convolve(duck, np.ones(sm) / sm, mode='same')
    mus = mus / (np.max(np.abs(mus)) + 1e-9) * 0.30 * duck
    out = voice + sfx + mus
    out = out[:int(DUR * SR)]
    wl_ = 0.3; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.28)
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
    ticks, prev = [], None
    for i in range(int(DUR * FPS)):
        tq = i / FPS; s, state, scr = clock_state(tq)
        if scr or state == 'done' or tq >= BREAK: prev = None; continue
        if prev is not None and s != prev and s > 0: ticks.append(tq)
        prev = s
    C.add_ticks(path, ticks, loud_from=ZERO - 5.0, final=None)

def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if mode == 'times':
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', round(T0, 2))
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('ROAD1', round(ROAD1, 2), 'INT2', round(INT2, 2), 'ROAD2', round(ROAD2, 2), 'ROAD3', round(ROAD3, 2), 'INT3', round(INT3, 2), 'ROAD4', round(ROAD4, 2))
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'SWERVE', [round(x, 2) for x in SWERVE], 'PEAK', round(PEAK, 2), 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        print('clock frame0', C.secs_left(story_t(0), ZERO), 'after rewind', C.secs_left(story_t(T0 + 0.01), ZERO), 'stop', C.secs_left(CHK3, ZERO))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, os.environ.get('SHEET', 'ep44v2_contact.png'))); print('ok'); return
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
