#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 40: תור לרופא: עוד 8 חודשים (season 9 "הקו פנוי" ep2, VOICED, built 19.11 under §P, ~22 s).
Voices = voice bank 2026-11-19 lines 4000–4005 (Benji = cat, Delia = Sharit) + stock 9104 "רגע... מה?!", 9103 "יש!!!",
9000 "שנייה, מותק.", prepared by voice/ep40_prep.py.
Set (new): his living room, the sofa, a window (day → night), a bedside alarm clock; the clinic app on his phone, Sharit on
the scheduling line (call screen).
Want: an appointment with the specialist sooner than July ("תור לרופא. בעוד שמונה חודשים.").
Plant: the small grey line under the slot on every app screen "לפי מרפאה: הקרובה לכתובת הרשומה (אילת)" — frame 0 (the
confirmation screen), the want, the confirmation mid-climb. The registered address = grandma's, Eilat (ep36). Never pointed at.
Climb (3 chips = the months): מרץ ✓ (cancellation list) → ינואר ✓ (Sharit on the line) → מחר ✓ gold ("מחר! שמונה בבוקר!").
Peak: "אני לוקח! אני לוקח!" — booked; night falls, alarm 06:00, he sleeps hugging the phone; hush + heartbeat.
Break (plant_payoff): the 06:00 reminder SMS "היום 08:00 · מרפאת אילת (352 ק״מ)". "רגע... מה?!" Frozen face; whip into the cold open.
Experiment (follows): part_label — "חלק 2 מתוך 5" pill in frame 0 (and the first caption line).
No music (voiced rule): voices + SFX + room tone. Serial pills "פרק 40" + live ticket number (§O4).

  python3 voice/ep40_prep.py
  python3 ep40.py times | test t1 t2 ... | render   -> out/ep40_rofe.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep7 as E7
import ep12 as E12
import ep18 as E18
import ep21_v1 as E21
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep40', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 104, 226)
TEAL = (20, 140, 140); SHARIT_SUB = (255, 182, 210)
QUEUE = int(os.environ.get('QUEUE', '441'))
EP_LABEL = 'פרק 40'
PART_LABEL = 'חלק 2 מתוך 5'
OUTNAME = os.environ.get('OUTNAME', 'ep40_rofe')
LIMIT = float(os.environ.get('LIMIT', '0'))
SMALL = 'לפי מרפאה: הקרובה לכתובת הרשומה (אילת)'

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
COLD_END = round(D[0] + 0.35, 2)            # cold open = 4000 "מחר! שמונה בבוקר! מחר!" (the last climb line)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "תור לרופא. בעוד שמונה חודשים." — the app: יולי
L[2] = L[1] + D[1] + 0.12                   # "רשימת ביטולים. מרץ!"
CHK1 = L[2] + ss(2, 1) - 0.05
L[103] = L[2] + D[2] + 0.06                 # "יש!!!"
FF = (L[103] + D[103] + 0.08, L[103] + D[103] + 1.18)   # x64: the days fly on the phone, he waits on the sofa
RING = (FF[1], FF[1] + 0.40)                # the scheduling line calls back: Sharit on the call screen
L[3] = RING[1] + 0.05                       # Sharit: "התפנה משהו, מותק. ינואר?"
CHK2 = L[3] + ss(3, 1) - 0.05
L[90] = L[3] + D[3] + 0.12                  # Sharit: "שנייה, מותק." (typing)
L[4] = L[90] + D[90] + 0.10                 # Sharit: "רגע... מחר בשמונה?"
L['0b'] = L[4] + D[4] + 0.08                # "מחר! שמונה בבוקר! מחר!" in context (= the cold open)
CHK3 = L['0b'] + 0.05; GOLDT = CHK3 + 0.05
L[5] = L['0b'] + D[0] + 0.10                # "אני לוקח! אני לוקח!" — books it
BOOK = L[5] + ss(5, 1) - 0.05
NIGHT = L[5] + D[5] + 0.08                  # night falls, alarm 06:00, he sleeps hugging the phone
HOLD = (NIGHT + 0.35, NIGHT + 0.85)
BREAK = HOLD[1]                             # buzz: the reminder SMS
L[104] = BREAK + 0.40                       # "רגע... מה?!"
FREEZE = L[104] + D[104]
DUR = round(FREEZE + 0.40, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (103, L[103]), (3, L[3]), (90, L[90]), (4, L[4]), (0, L['0b']), (5, L[5]), (104, L[104])]
SPEAKER = {0: 'cat', 1: 'cat', 2: 'cat', 103: 'cat', 5: 'cat', 104: 'cat', 3: 'sh', 90: 'sh', 4: 'sh'}

SUBS = {
    0: [['מחר! שמונה בבוקר! מחר!']],
    1: [['תור לרופא.'], ['בעוד שמונה חודשים.']],
    2: [['רשימת ביטולים.'], ['מרץ!']],
    103: [['יש!!!']],
    3: [['התפנה משהו, מותק.'], ['ינואר?']],
    90: [['שנייה, מותק.']],
    4: [['רגע...'], ['מחר בשמונה?']],
    5: [['אני לוקח! אני לוקח!']],
    104: [['רגע... מה?!']],
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
        if li == 104: b = DUR - 0.25
        if li == 5: b = min(b, NIGHT)
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('room', 0.0, COLD_END), ('rewind', COLD_END, T0), ('room', T0, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['תור לרופא?', 'עוד 8 חודשים']          # keyword: תור לרופא (F1, everyone has waited)
TOPCAPS = [(0.0, COLD_END, HOOK), (T0, L[1] + D[1] - 0.1, HOOK)]

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

def cat_mouth(t, rest='w', loud='smile'):
    v = voice_v(t, 'cat')
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

def night_k(t):
    s_t = story_t(t)
    if t < COLD_END: return 0.0
    return ease_io(clamp((s_t - NIGHT) / 0.35))

# ------------------------------------------------------------------ the phone (clinic app / call / confirmation / SMS)
PW, PH = 400, 720
SH_CALL = None
def month_of(t):
    s_t = story_t(t)
    if s_t >= L['0b']: return 'מחר 08:00'
    if s_t >= CHK2: return 'ינואר'
    if s_t >= CHK1: return 'מרץ'
    return 'יולי'

def phone_state(t):
    s_t = story_t(t)
    if t >= BREAK and t >= COLD_END: return 'sms'
    if RING[0] <= s_t < L['0b']: return 'call'
    if s_t >= L['0b']: return 'confirm'
    return 'app'

def ff_date(t):
    s_t = story_t(t)
    if FF[0] <= s_t < FF[1]:
        u = (s_t - FF[0]) / (FF[1] - FF[0]); n = int(u * 40)
        return f'{20 + n % 10}.11' if n < 10 else (f'{n - 9}.12' if n < 40 else '31.12')
    return None

def phone_layer(state, month, talk=0, ffd=None):
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    if state == 'call':
        pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(20, 92, 92))
        pd.text((S(PW / 2), S(96)), 'מוקד זימון תורים', font=font(S(34), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(140)), 'שיחה נכנסת...', font=font(S(26), 800), fill=(180, 230, 230), anchor='mm')
        lay.alpha_composite(SH_CALL[talk], (int(S(PW / 2)) - SH_CALL[talk].width // 2, int(S(170))))
        pd = ImageDraw.Draw(lay)
        E(pd, PW / 2 - 90, 640, 40, 40, fill=RED); E(pd, PW / 2 + 90, 640, 40, 40, fill=GREEN)
        return lay
    if state == 'sms':
        pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(26, 30, 48))
        pd.text((S(PW / 2), S(150)), '06:00', font=font(S(96), 900), fill=WHITE, anchor='mm')
        pd.rounded_rectangle([S(30), S(250), S(PW - 30), S(520)], radius=S(26), fill=(250, 250, 252), outline=(200, 204, 214), width=iw(3))
        pd.text((S(PW - 56), S(290)), 'הקופה · תזכורת', font=font(S(26), 900), fill=TEAL, anchor='rm')
        pd.text((S(PW / 2), S(352)), 'היום 08:00', font=font(S(44), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(416)), 'מרפאת אילת', font=font(S(48), 900), fill=RED, anchor='mm')
        pd.text((S(PW / 2), S(474)), '352 ק״מ ממך', font=font(S(30), 800), fill=(110, 112, 124), anchor='mm')
        return lay
    pd.rectangle([S(14), S(66), S(PW - 14), S(132)], fill=TEAL)
    pd.text((S(PW / 2), S(99)), 'הקופה · זימון תורים', font=font(S(34), 900), fill=WHITE, anchor='mm')
    if state == 'confirm':
        E(pd, PW / 2, 220, 56, 56, fill=GREEN); line(pd, [(PW / 2 - 26, 220), (PW / 2 - 6, 242), (PW / 2 + 30, 198)], WHITE, 12)
        pd.text((S(PW / 2), S(318)), 'התור נקבע!', font=font(S(46), 900), fill=INK, anchor='mm')
        pd.rounded_rectangle([S(46), S(360), S(PW - 46), S(450)], radius=S(20), fill=(255, 240, 200), outline=GOLD, width=iw(5))
        pd.text((S(PW / 2), S(406)), 'מחר 08:00', font=font(S(54), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(486)), 'רופא מומחה', font=font(S(30), 800), fill=(90, 92, 104), anchor='mm')
        pd.text((S(PW / 2), S(560)), SMALL, font=font(S(19), 700), fill=(150, 152, 162), anchor='mm')   # the plant
        return lay
    pd.text((S(PW - 40), S(170)), 'רופא מומחה', font=font(S(32), 900), fill=INK, anchor='rm')
    pd.text((S(PW - 40), S(222)), 'התור הקרוב:', font=font(S(28), 800), fill=(90, 92, 104), anchor='rm')
    hot = month != 'יולי'
    pd.rounded_rectangle([S(46), S(250), S(PW - 46), S(340)], radius=S(20), fill=(232, 250, 238) if hot else (255, 236, 236),
                         outline=GREEN if hot else RED, width=iw(5))
    pd.text((S(PW / 2), S(296)), month, font=font(S(62), 900), fill=GREEN if hot else RED, anchor='mm')
    pd.text((S(PW / 2), S(368)), SMALL, font=font(S(19), 700), fill=(150, 152, 162), anchor='mm')        # the plant
    for k in range(2):
        y = 410 + k * 76
        pd.rounded_rectangle([S(46), S(y), S(PW - 46), S(y + 56)], radius=S(14), fill=(236, 238, 244))
        pd.text((S(PW - 64), S(y + 28)), ('אוגוסט', 'ספטמבר')[k], font=font(S(26), 800), fill=(160, 162, 172), anchor='rm')
    if month != 'יולי':
        pd.rounded_rectangle([S(46), S(580), S(PW - 46), S(640)], radius=S(30), fill=GREEN)
        pd.text((S(PW / 2), S(610)), 'ברשימת ביטולים', font=font(S(30), 900), fill=WHITE, anchor='mm')
    if ffd:
        pd.rounded_rectangle([S(90), S(540), S(PW - 90), S(580)], radius=S(12), fill=(20, 20, 24))
        pd.text((S(PW / 2), S(560)), f'היום: {ffd}', font=font(S(26), 900), fill=YELLOW, anchor='mm')
    return lay

_PHC = {}
def phone_at(t):
    st = phone_state(t); talk = 0
    if st == 'call':
        sv = voice_v(t, 'sh'); talk = 2 if sv > 0.3 else (1 if sv > 0.1 else 0)
    key = (st, month_of(t), talk, ff_date(t))
    if key not in _PHC:
        if len(_PHC) > 60: _PHC.clear()
        _PHC[key] = phone_layer(*key)
    return _PHC[key]

def paste_rot(img, lay, c, ang=0.0, sc=1.0):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    E21.shadow_paste(img, lay, c, 100, (16, 20), 12)

burst = E18.burst

# ------------------------------------------------------------------ the set: his living room (new)
CLOCK_C = (900, 1250)
def build_room_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        v = y / H; d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(214, 190, v)), int(lerp(232, 214, v)), int(lerp(224, 200, v))))
    # window (sky drawn per frame through a hole: here day sky; night handled by overlay)
    d.rounded_rectangle([S(80), S(230), S(500), S(720)], radius=S(10), fill=(170, 214, 246), outline=(240, 240, 236), width=iw(14))
    line(d, [(290, 230), (290, 720)], (240, 240, 236), 10); line(d, [(80, 475), (500, 475)], (240, 240, 236), 10)
    E(d, 420, 320, 34, 34, fill=(255, 228, 120))
    # wall calendar with July circled
    d.rectangle([S(640), S(260), S(960), S(600)], fill=(252, 252, 248), outline=(150, 150, 160), width=iw(4))
    d.rectangle([S(640), S(260), S(960), S(330)], fill=TEAL)
    d.text((S(800), S(296)), 'לוח שנה', font=font(S(34), 900), fill=WHITE, anchor='mm')
    for r in range(4):
        for c in range(5): d.rectangle([S(668 + c * 56), S(350 + r * 58), S(708 + c * 56), S(388 + r * 58)], fill=(226, 228, 236))
    d.text((S(800), S(570)), 'יולי?!', font=font(S(36), 900), fill=RED, anchor='mm')
    # sofa
    d.rounded_rectangle([S(-40), S(1080), S(1120), S(1500)], radius=S(70), fill=(96, 120, 170), outline=(50, 64, 100), width=iw(7))
    d.rounded_rectangle([S(-40), S(1380), S(1120), S(1720)], radius=S(50), fill=(112, 138, 190), outline=(50, 64, 100), width=iw(7))
    d.rectangle([0, S(1720), W * K, H * K], fill=(150, 116, 84))
    # side table + alarm clock frame (digits per frame)
    d.rounded_rectangle([S(790), S(1330), S(1010), S(1400)], radius=S(10), fill=(140, 96, 60), outline=(80, 52, 30), width=iw(5))
    img = img.filter(ImageFilter.GaussianBlur(S(1.4)))
    return img

def clock_text(t):
    if night_k(t) > 0.3 or (story_t(t) >= NIGHT and t >= COLD_END): return '06:00'
    return '16:42'

def base_cat():
    st = E7.chill_state(); st.update(cobweb=1.0, red=0.9, blush=0.3); return st

HXP, HYP, FP = 700, 980, 1.70

def cat_state(t):
    st = base_cat(); rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    s_t = story_t(t)
    if L['0b'] <= s_t < L[5]:                 # "מחר! שמונה בבוקר! מחר!" — bouncing on the sofa
        u = s_t - L['0b']
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(s_t, rest='smile', loud='w'), ear_dy=-30, look=(-24, 4), blush=1.0)
        rot = 7 * math.sin(u * 11); dy = -32 * abs(math.sin(u * 8)) - 10 * voice_v(s_t, 'cat')
    elif t < L[2]:                            # the want: deflated at "July"
        st.update(lid=0.35, pupil='normal', brow='annoyed', mouth=cat_mouth(t, rest='flat', loud='w'), ear_droop=0.6, look=(-26, 10), sweat=0.5, blush=0.0)
        rot = -3; dy = 6 - 8 * v
    elif t < FF[0]:                           # "רשימת ביטולים. מרץ!" + "יש!!!"
        up = t >= CHK1
        st.update(lid=0.0 if up else 0.2, pupil='big', brow='up' if up else 'none', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-24 if up else -8, look=(-24, 8), blush=0.8 if up else 0.3)
        if up: dy = -22 * abs(math.sin((t - CHK1) * 9)) * math.exp(-(t - CHK1) * 1.5)
    elif t < RING[0]:                         # x64: waiting, sinking into the sofa
        u = (t - FF[0]) / (FF[1] - FF[0])
        st.update(lid=0.3 + 0.4 * u, pupil='normal', brow='none', mouth='flat', look=(-24, 12), ear_droop=0.6 * u)
        dy = 30 * u
    elif t < L[3]:                            # ring!
        u = t - RING[0]
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-26 * math.exp(-u * 2), look=(-30, 6), blush=0.5)
        rot = 6 * math.sin(u * 28) * math.exp(-u * 3); dy = 30 - 40 * ease_out(clamp(u / 0.3))
    elif t < L['0b']:                         # Sharit on the line: hanging on every word
        hope = t >= CHK2
        st.update(lid=0.0, pupil='big', brow='up', mouth='w' if t >= L[4] else 'smile', ear_dy=-20 if hope else -10, look=(-30, 6), blush=0.6 + 0.4 * hope)
        dy = -10 if t >= L[4] else -4
    elif t < NIGHT:                           # "אני לוקח! אני לוקח!" — tapping, ecstatic
        u = t - L[5]
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28, look=(-28, 8), blush=1.0)
        dy = -18 * abs(math.sin(u * 10))
    elif t < BREAK:                           # THE PEAK: night, asleep hugging the phone
        st.update(eye_mode='closed', mouth='smile', ear_dy=-10, blush=1.0, look=(0, 0), ear_droop=0.2); rot = -8; dy = 24
    else:                                     # the SMS — eyes snap open, frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='up' if t >= L[104] else 'none', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-24 * math.exp(-u * 4),
                  look=(-30, 10), twitch=(u >= 0.5 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.5), blush=0.0)
        rot = -8 * math.exp(-u * 6); dy = 24 * math.exp(-u * 6) - 10
    return st, rot, dy

def scene_room(t, i):
    img = ROOM.copy()
    d = ImageDraw.Draw(img)
    s_t = story_t(t)
    # the alarm clock
    nk = night_k(t)
    d.rounded_rectangle([S(CLOCK_C[0] - 100), S(CLOCK_C[1] - 60), S(CLOCK_C[0] + 100), S(CLOCK_C[1] + 60)], radius=S(18), fill=(30, 30, 36), outline=(10, 10, 12), width=iw(5))
    d.text((S(CLOCK_C[0]), S(CLOCK_C[1])), clock_text(t), font=font(S(64), 900), fill=(255, 70, 60), anchor='mm')
    if nk > 0.3:
        E(d, CLOCK_C[0] - 80, CLOCK_C[1] - 78, 18, 18, fill=YELLOW, outline=INK, width=3)   # the alarm bell icon
    st, rot, dy = cat_state(t)
    E(d, HXP, 1680, 420, 440, fill=FUR, outline=OUT, width=7)
    E(d, HXP, 1740, 190, 290, fill=CREAM)
    asleep = NIGHT <= s_t < BREAK and t >= COLD_END
    if asleep:
        pc = (520, 1300); ang = 18; sc = 0.86
    else:
        pc = (300, 1120 + 5 * math.sin(t * 8)); ang = -6; sc = 0.98
        if t < COLD_END or L['0b'] <= s_t < L[5]: pc = (300 + 10 * math.sin(t * 30), 1110 - 14 * abs(math.sin(t * 8)))
        if RING[0] <= s_t < RING[0] + 0.4: sc += 0.18 * math.exp(-(s_t - RING[0]) * 9); pc = (300 + 8 * math.sin(t * 90), 1120)
        if BREAK <= s_t and t >= COLD_END:
            u = s_t - BREAK; pc = (300 + 6 * math.sin(t * 70) * math.exp(-u * 4), 1100); sc = 1.02
    grip = (pc[0] - 170, pc[1] + 160) if not asleep else (pc[0] + 40, pc[1] + 170)
    capsule(d, (HXP - 230, 1520), grip, 110, FUR, OUT, 4)
    E12.paste_head(img, st, i, HXP, HYP + dy, FP, rot)
    paste_rot(img, phone_at(t), pc, ang, sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, grip, 70, 0.9)
    if L[5] <= s_t < NIGHT and t >= COLD_END and abs(s_t - BOOK) < 0.12:
        burst(img, (pc[0], pc[1] + 100), s_t - BOOK + 0.12, (255, 220, 120), 150, 10, 0.3)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= s_t < c_ + 0.5: burst(img, (pc[0], pc[1] - 60), s_t - c_, (120, 255, 160), 160, 10, 0.4)
    if RING[0] <= s_t < RING[0] + 0.45: burst(img, pc, s_t - RING[0], (150, 230, 230), 220, 12, 0.45)
    if t >= COLD_END and 0 <= s_t - BREAK < 0.45: burst(img, pc, s_t - BREAK, (255, 120, 120), 240, 12, 0.45)
    if GOLDT <= s_t < NIGHT: E18.confetti(img, s_t - GOLDT + 0.3)
    if asleep:
        for k in range(3):                    # zzz
            u = ((t - NIGHT) * 0.9 + k * 0.33) % 1.0
            d = ImageDraw.Draw(img)
            d.text((S(HXP + 220 + 40 * u), S(700 - 160 * u)), 'z', font=font(S(int(50 + 40 * u)), 900), fill=(255, 255, 255, int(255 * (1 - u))), anchor='mm')
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('מרץ', 820, CHK1), ('ינואר', 540, CHK2), ('מחר', 260, CHK3)]
def chips(frame, t, y=330):
    s_t = story_t(t)
    if t < L[1] + D[1] - 0.1 or t >= BREAK + 0.6 or (NIGHT + 0.2 <= t < BREAK): return
    gold = t >= GOLDT
    drained = t >= BREAK
    d = ImageDraw.Draw(frame)
    for lab, cx, tk in CHIPS:
        ok = t >= tk and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if drained: sc = 1.0 + 0.15 * math.exp(-(t - BREAK) * 10)
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

def ff_overlay(frame, t):
    frame.alpha_composite(m.SCAN)
    d = ImageDraw.Draw(frame)
    for x0 in (850, 906):
        d.polygon([(x0, 600), (x0 + 50, 634), (x0, 668)], fill=WHITE, outline=(10, 10, 12), width=5)
    d.text((780, 634), 'x64', font=font(70, 900), fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(10, 10, 12))

def sub_layer(lines, fill, size=64):
    lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

ROOM = PILL_EP = PILL_Q = PILL_PART = None
def init_all():
    global ROOM, PILL_EP, PILL_Q, PILL_PART, SH_CALL
    m.init_static()
    ROOM = build_room_bg()
    SH_CALL = []
    for mo in ('lazy', 'talk', 'grin'):     # Sharit on the scheduling line, 3 mouth states (headset-free crop, like ep36)
        st = SH.base(); st.update(mouth=mo, lid=0.6, look=(0, 6), snack=False)
        lay = SH.draw(st, 3 if mo == 'talk' else 0).crop((S(60), S(60), S(640), S(700)))
        SH_CALL.append(lay.resize((S(330), int(S(330) * lay.height / lay.width)), Image.LANCZOS))
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_PART = HUD._pill(PART_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'room':
        z, cx, cy = 1.04 + 0.01 * pu, 540, 1000
        if a == 0.0:                                   # cold open: low and tight on the phone + his face, rising
            z, cx, cy = 1.30 + 0.04 * t, 540, 1180 - 40 * t
            if t < 0.3: z = 1.50 - 0.20 * ease_out(t / 0.3)
        elif t < L[2]: z, cx, cy = 1.18, 560, 1080
        elif FF[0] <= t < RING[0]: z, cx, cy = 1.0, 540, 960
        elif L[3] <= t < L['0b']: z, cx, cy = 1.12 + 0.02 * (t - L[3]), 470, 1100
        elif L['0b'] <= t < NIGHT: z, cx, cy = 1.30, 470, 1100
        if HOLD[0] - 0.35 <= t < BREAK:
            k = ease_io(clamp((t - (HOLD[0] - 0.35)) / 0.85)); z, cx, cy = 1.10 + 0.14 * k, lerp(540, 600, k), lerp(1000, 1100, k)
        if t >= BREAK: z, cx, cy = 1.26, 480, 1080
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1000
    elif name == 'frozen':
        z, cx, cy = 1.36 + 0.03 * pu, 500, 1080
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_room(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    else: img = scene_room(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (RING[0], BREAK):
        if 0 <= t - s_ < 0.3: shake = 14 * math.exp(-(t - s_) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    nk = night_k(t)
    if nk > 0:                                         # night: blue dark, the phone/clock glow stays readable
        frame.alpha_composite(Image.new('RGBA', frame.size, (12, 18, 50, int(150 * nk))))
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if FF[0] <= t < FF[1]: ff_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    if name != 'frozen': chips(frame, t)
    for t0, t1, lines in TOPCAPS:
        if t0 <= t < t1: m.paste_center(frame, m.caption_layer(lines, 96, WHITE), W / 2, 270)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            col = SHARIT_SUB if SPEAKER[li] == 'sh' else WHITE
            m.paste_center(frame, sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < L[2]) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_PART, (40 + PILL_EP.width + 10, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(40)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'sh': y = m.phone_line(y) * 1.5
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
    def buzz(t0, g=0.22):
        for k in range(2):
            tt = tt_(0.12); add(sfx, m.lowpass(np.sign(np.sin(2 * np.pi * 150 * tt)), 400) * np.sin(np.pi * tt / 0.12), t0 + k * 0.15, g)
    def ring(t0, ln):
        k = 0
        while k * 0.22 < ln:
            add(sfx, m.tone(1318.5, 0.1, harm=((1, 1), (2, 0.3)), decay=20), t0 + k * 0.22, 0.12)
            add(sfx, m.tone(1568.0, 0.1, harm=((1, 1), (2, 0.3)), decay=20), t0 + k * 0.22 + 0.08, 0.12); k += 1
    def tap(t0, g=0.25): add(sfx, m.highpass(nz(0.02), 2500) * np.exp(-tt_(0.02) * 150), t0, g)
    def cheer(t0, ln=1.0, g=0.08):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    add(sfx, thud(0.8), 0.0); check(0.05, 0.16, True)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(NIGHT), 120, 700) * 0.6, 0.0, 0.010)                     # room tone
    add(sfx, m.bandpass(nz(DUR - NIGHT + 0.3), 80, 400) * 0.6, NIGHT, 0.008)          # night hush
    tap(L[1] + 0.4); tap(CHK1 - 0.15); check(CHK1, 0.15)
    add(sfx, m.bandpass(nz(0.4), 600, 5000) * np.linspace(0, 1, int(0.4 * SR)), FF[0] - 0.3, 0.06)
    tc = FF[0]
    while tc < FF[1]:
        add(sfx, m.tone(1200 + 200 * math.sin(tc * 9), 0.03, harm=((1, 1),), decay=40), tc, 0.025); tc += 0.07
    ring(RING[0], 0.45); whoosh(RING[0], 0.08, 0.25)
    check(CHK2, 0.15)
    for k in range(int(D[90] / 0.11)): tap(L[90] + k * 0.11, 0.10)              # Sharit types
    check(CHK3, 0.2, True); cheer(GOLDT + 0.05, NIGHT - GOLDT, 0.08)
    tap(BOOK, 0.3)
    add(sfx, m.tone(523.3, 0.6, harm=((1, 1), (2, 0.2)), decay=4), NIGHT + 0.05, 0.08)   # the alarm set "bip"
    heartbeat(HOLD[0] + 0.05); heartbeat(HOLD[0] + 0.31, 0.5)
    buzz(BREAK); add(sfx, m.tone(1046.5, 0.4, harm=((1, 1), (2.76, 0.2)), decay=6), BREAK + 0.02, 0.18); add(sfx, thud(0.6), BREAK)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), BREAK + 0.3, 0.16)
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
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', T0, 'FF', [round(x, 2) for x in FF], 'RING', [round(x, 2) for x in RING])
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'NIGHT', round(NIGHT, 2), 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep40_contact.png')); print('ok'); return
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
