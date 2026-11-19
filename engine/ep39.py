#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 39: השיחה מוקלטת (season 9 "הקו פנוי" ep1, VOICED, built 19.11 under §P, ~27 s).
Voices = voice bank 2026-11-19 lines 3900–3906 (Benji = cat, Delia = Sharit) + 2703 "שרית?! גם פה?" + stock 9101 "סבבה."
(his own voice on the recording) + 9103 "יש!!!", prepared by voice/ep39_prep.py.
Set: the internet company's service counter (window 3), router shelf, LED board, the brand wall "חברת האינטרנט שלי · מוקד שירות".
Want: prove the rep promised 49 ₪ a month — the bill says 89 ₪.
Plant: the grey small print on the bill "* לפי אישורך בשיחה מ-12.11" (cold open + the want, the bill held up) and again
as the subject line of the recording-request form mid-climb; plus the snack bag he munches from (his mouth full). Never pointed at.
Climb (3 chips): תאריך ✓ (12.11 · 14:02 written) → בכתב ✓ (the form slapped) → ההקלטה ✓ gold (Sharit hands the disc, the queue claps, "יש!!!").
Peak: he plays it at her: "ארבעים ותשעה שקלים לחודש, מותק." — pointing, triumphant; hush + heartbeat.
Break (his_own_hand): the recording goes on: "ומהחודש השלישי שמונים ותשעה. מאשר?" — and his own voice, mouth full: "סבבה."
The player label flips to "אתה". Chips drain; frozen face; whip into the cold open (loop).
Experiment (follows): part_label — "חלק 1 מתוך 5" pill in frame 0 (and the first caption line).
No music (voiced rule): voices + SFX + room tone. Serial pills "פרק 39" + live ticket number (hud.stage_of, §O4).

  python3 voice/ep39_prep.py
  python3 ep39.py times | test t1 t2 ... | render   -> out/ep39_hakalata.mp4
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
import ep18 as E18
import ep21_v1 as V1
import hud as HUD
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, xform, epoly, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, FUR_D, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep39', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 104, 226)
ORANGE = (240, 118, 30); SHARIT_SUB = (255, 182, 210); IVRSUB = (160, 214, 255)
QUEUE = int(os.environ.get('QUEUE', '441'))
EP_LABEL = 'פרק 39'
PART_LABEL = 'חלק 1 מתוך 5'
OUTNAME = os.environ.get('OUTNAME', 'ep39_hakalata')
LIMIT = float(os.environ.get('LIMIT', '0'))
SMALL = '* לפי אישורך בשיחה מ-12.11'

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
COLD_END = round(D[0] + 0.40, 2)            # cold open = 3900 "יש לי את ההקלטה!" (the loudest climb line), the disc held up
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "הבטיחו לי ארבעים ותשע בטלפון. בחשבון: שמונים ותשע." — the bill held up
FF = (L[1] + D[1] + 0.10, L[1] + D[1] + 1.30)   # x64: the board races to his number
DING = FF[1]
ARRIVE = DING + 0.05                        # Sharit slides into window 3
L[27] = ARRIVE + 0.30                       # "שרית?! גם פה?"
L[2] = L[27] + D[27] + 0.15                 # Sharit: "הקלטה? רק בבקשה בכתב, מותק. עם תאריך."
FORMIN = L[2] + ss(2, 1)
L[3] = L[2] + D[2] + 0.12                   # "שתים עשרה בנובמבר. הכול כתוב."
WRITE = (L[3] - 0.05, L[3] + ss(3, 1) - 0.05)
CHK1 = L[3] + ss(3, 1) - 0.10               # the date written
SLAP = L[3] + D[3] - 0.15                   # the form slapped on the counter
CHK2 = SLAP + 0.05
L[4] = L[3] + D[3] + 0.15                   # Sharit: "העותק הראשון חינם, מותק." — the disc slides over
DISC = L[4] + 0.25
CHK3 = L[4] + D[4] - 0.05; GOLDT = CHK3 + 0.05
L[103] = CHK3 + 0.20                        # "יש!!!"
L['0b'] = L[103] + D[103] + 0.12            # "יש לי את ההקלטה! עכשיו נראה אותם!" in context (= the cold open)
PLAY = L['0b'] + D[0] + 0.12                # the player slams in by his face, click
L[5] = PLAY + 0.25                          # the recording: "ארבעים ותשעה שקלים לחודש, מותק." (peak)
HOLD = (L[5] + D[5] + 0.03, L[5] + D[5] + 0.48)
BREAK = HOLD[1]
L[6] = BREAK                                # the recording goes on: "ומהחודש השלישי שמונים ותשעה. מאשר?"
L[101] = L[6] + D[6] + 0.08                 # his own voice, mouth full: "סבבה."
YOU = L[101] - 0.05
FREEZE = L[101] + D[101]
DUR = round(FREEZE + 0.42, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (27, L[27]), (2, L[2]), (3, L[3]), (4, L[4]), (103, L[103]), (0, L['0b']), (5, L[5]), (6, L[6]), (101, L[101])]
SPEAKER = {0: 'cat', 1: 'cat', 27: 'cat', 3: 'cat', 103: 'cat', 2: 'sh', 4: 'sh', 5: 'rec', 6: 'rec', 101: 'recme'}

SUBS = {
    0: [['יש לי את ההקלטה!'], ['עכשיו נראה אותם!']],
    1: [['הבטיחו לי 49 בטלפון.'], ['בחשבון: 89.']],
    27: [['שרית?! גם פה?']],
    2: [['הקלטה?'], ['רק בבקשה בכתב, מותק.'], ['עם תאריך.']],
    3: [['שתים עשרה בנובמבר.'], ['הכול כתוב.']],
    4: [['העותק הראשון חינם, מותק.']],
    103: [['יש!!!']],
    5: [['49 שקלים לחודש, מותק.']],
    6: [['ומהחודש השלישי 89.'], ['מאשר?']],
    101: [['סבבה.']],
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
        if li == 101: b = DUR - 0.25
        if li == 5 and k == len(ch) - 1: b = min(b, HOLD[0] + 0.02)
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('two', 0.0, COLD_END), ('rewind', COLD_END, T0), ('two', T0, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['השיחה מוקלטת?', 'אז תביאו את ההקלטה']       # keyword: השיחה / ההקלטה (F16 pain question)
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

# ------------------------------------------------------------------ props
def bill_layer():
    """the monthly bill: 89 ₪; the plant = the grey small print"""
    w_, h_ = 380, 300
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(w_) - 1, S(h_) - 1], fill=(252, 252, 248), outline=(150, 150, 160), width=iw(3))
    d.rectangle([0, 0, S(w_), S(52)], fill=ORANGE)
    d.text((S(w_ / 2), S(27)), 'חשבון חודשי', font=font(S(32), 900), fill=WHITE, anchor='mm')
    d.text((S(w_ - 26), S(82)), 'חברת האינטרנט שלי', font=font(S(22), 800), fill=(90, 90, 100), anchor='rm')
    d.text((S(w_ - 26), S(140)), 'לתשלום:', font=font(S(30), 800), fill=INK, anchor='rm')
    d.text((S(110), S(142)), '89 ₪', font=font(S(64), 900), fill=RED, anchor='mm')
    for k in range(2):
        d.rounded_rectangle([S(30), S(188 + k * 26), S(w_ - 30), S(202 + k * 26)], radius=S(5), fill=(214, 216, 224))
    d.text((S(w_ - 22), S(268)), SMALL, font=font(S(24), 700), fill=(140, 140, 150), anchor='rm')
    return lay

def form_layer(written=0.0):
    """the recording request; the plant again as its subject line"""
    w_, h_ = 420, 300
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(w_) - 1, S(h_) - 1], fill=(252, 252, 248), outline=(150, 150, 160), width=iw(3))
    d.rectangle([0, 0, S(w_), S(54)], fill=BLUE)
    d.text((S(w_ / 2), S(28)), 'בקשה להקלטת שיחה', font=font(S(30), 900), fill=WHITE, anchor='mm')
    d.text((S(w_ - 26), S(92)), 'תאריך השיחה:', font=font(S(24), 800), fill=(90, 90, 100), anchor='rm')
    d.rounded_rectangle([S(30), S(76), S(230), S(110)], radius=S(6), outline=(170, 174, 184), width=iw(2))
    if written > 0:
        txt = '12.11 · 14:02'
        n = max(1, int(round(len(txt) * clamp(written))))
        d.text((S(130), S(94)), txt[:n] if written < 1 else txt, font=font(S(28), 900), fill=(30, 60, 160), anchor='mm')
    d.text((S(w_ - 26), S(150)), 'נושא:', font=font(S(24), 800), fill=(90, 90, 100), anchor='rm')
    d.text((S(w_ - 100), S(150)), SMALL[2:], font=font(S(22), 700), fill=(140, 140, 150), anchor='rm')
    for k in range(2):
        d.rounded_rectangle([S(30), S(186 + k * 34), S(w_ - 30), S(204 + k * 34)], radius=S(5), fill=(214, 216, 224))
    d.text((S(w_ - 26), S(272)), 'חתימה: ________', font=font(S(22), 800), fill=(110, 110, 120), anchor='rm')
    if written >= 1:
        pts = [(lerp(180, 40, u), 268 - 12 * math.sin(u * 17)) for u in np.linspace(0, 1, 24)]
        line(d, pts, (30, 60, 160), 4)
    return lay

def disc_layer():
    """the recording: a disc in a clear sleeve, label 12.11 · 14:02"""
    w_ = 260
    lay = Image.new('RGBA', (S(w_), S(w_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(w_) - 1, S(w_) - 1], radius=S(10), fill=(230, 236, 244, 200), outline=(120, 130, 150), width=iw(3))
    c = w_ / 2
    E(d, c, c, 110, 110, fill=(214, 220, 232), outline=(90, 96, 110), width=4)
    for r, col in ((96, (190, 220, 240)), (78, (236, 206, 240)), (60, (210, 240, 210))):
        d.arc([S(c - r), S(c - r), S(c + r), S(c + r)], 200, 300, fill=col, width=iw(8))
    d.rounded_rectangle([S(c - 90), S(c + 26), S(c + 90), S(c + 86)], radius=S(8), fill=WHITE, outline=(90, 96, 110), width=iw(2))
    d.text((S(c), S(c + 56)), 'שיחה 12.11 · 14:02', font=font(S(22), 900), fill=INK, anchor='mm')
    E(d, c, c - 20, 20, 20, fill=(250, 250, 252), outline=(90, 96, 110), width=3)
    return lay

def player_layer(t):
    """the recording playing on his phone: waveform + speaker tag; at the break the tag flips to 'אתה'"""
    pw, ph = 400, 640
    lay = Image.new('RGBA', (S(pw), S(ph)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(pw) - 1, S(ph) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(pw - 14), S(ph - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(pw / 2 - 56), S(28), S(pw / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.text((S(pw / 2), S(110)), 'הקלטת שיחה', font=font(S(38), 900), fill=INK, anchor='mm')
    pd.text((S(pw / 2), S(156)), '12.11 · 14:02', font=font(S(30), 800), fill=(110, 112, 124), anchor='mm')
    me = t >= YOU
    tag, col = ('דובר: אתה', RED) if me else ('דובר: נציגה', BLUE)
    tw = pd.textlength(tag, font=font(S(34), 900))
    pd.rounded_rectangle([S(pw / 2) - tw / 2 - S(22), S(196), S(pw / 2) + tw / 2 + S(22), S(254)], radius=S(29), fill=col)
    pd.text((S(pw / 2), S(225)), tag, font=font(S(34), 900), fill=WHITE, anchor='mm')
    sp = speaking(t); v = 0.0
    if sp and SPEAKER[sp[0]] in ('rec', 'recme'):
        li, s0 = sp; env = META[li]['env']; k = int((t - s0) * FPS); v = env[k] if k < len(env) else 0.0
    rng = random.Random(int(t * 30))
    for k in range(17):
        x = 52 + k * 18; hh = 14 + 120 * v * rng.uniform(0.3, 1.0) * (1 - abs(k - 8) / 11)
        pd.rounded_rectangle([S(x), S(370 - hh / 2), S(x + 10), S(370 + hh / 2)], radius=S(5), fill=col if me else (60, 70, 90))
    prog = clamp((t - L[5] + 0.3) / (FREEZE - L[5] + 0.3)) if t >= PLAY else 0.0
    pd.rounded_rectangle([S(46), S(470), S(pw - 46), S(484)], radius=S(7), fill=(214, 216, 224))
    pd.rounded_rectangle([S(pw - 46 - (pw - 92) * prog), S(470), S(pw - 46), S(484)], radius=S(7), fill=col)
    E(pd, 200, 560, 44, 44, fill=INK)
    pd.rectangle([S(184), S(538), S(194), S(582)], fill=WHITE); pd.rectangle([S(206), S(538), S(216), S(582)], fill=WHITE)
    return lay

def paste_rot(img, lay, c, ang=0.0, sc=1.0, a=100):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    V1.shadow_paste(img, lay, c, a, (14, 18), 10)

burst = E18.burst

# ------------------------------------------------------------------ the set: the internet company's service counter
BOARD_C = (300, 620)
def router_icon(d, x, y, s=1.0, led=(60, 230, 90)):
    for ax, ang in ((-50, -14), (0, 0), (50, 14)):
        a_ = math.radians(ang); tip = (x + ax * s + 70 * s * math.sin(a_), y - 70 * s * math.cos(a_))
        capsule(d, (x + ax * s, y), tip, 8 * s, (52, 54, 62), (20, 20, 24), 3)
    d.rounded_rectangle([S(x - 80 * s), S(y), S(x + 80 * s), S(y + 44 * s)], radius=S(10 * s), fill=(58, 60, 70), outline=(20, 20, 24), width=iw(3))
    for k in range(4): E(d, x - 45 * s + k * 30 * s, y + 20 * s, 6 * s, 6 * s, fill=led if k < 3 else (70, 70, 76))

def build_service_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        v = y / H; d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(236, 214, v)), int(lerp(226, 204, v)), int(lerp(214, 190, v))))
    d.rectangle([0, S(1080), W * K, S(1120)], fill=ORANGE)                         # brand stripe
    # router shelf on the left (behind Sharit)
    d.rectangle([S(0), S(770), S(470), S(1180)], fill=(96, 100, 112))
    for y in (930, 1100):
        d.rectangle([S(0), S(y), S(470), S(y + 18)], fill=(60, 62, 72))
        for x in (90, 240, 390): router_icon(d, x, y - 50, 0.75, (60, 230, 90) if (x + y) % 3 else (255, 60, 50))
    # the LED board frame (numbers drawn per frame)
    d.rounded_rectangle([S(BOARD_C[0] - 230), S(BOARD_C[1] - 110), S(BOARD_C[0] + 230), S(BOARD_C[1] + 110)], radius=S(16), fill=(24, 24, 28), outline=(70, 70, 80), width=iw(6))
    d.text((S(BOARD_C[0]), S(BOARD_C[1] - 72)), 'עמדה 3', font=font(S(34), 900), fill=(200, 200, 210), anchor='mm')
    # the brand wall on the right
    x0, y0, x1, y1 = 640, 250, 1040, 560
    d.rounded_rectangle([S(x0 + 8), S(y0 + 10), S(x1 + 8), S(y1 + 10)], radius=S(14), fill=(170, 150, 130))
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(14), fill=(252, 250, 246), outline=(120, 120, 130), width=iw(5))
    d.rectangle([S(x0), S(y0), S(x1), S(y0 + 90)], fill=ORANGE)
    d.text((S((x0 + x1) / 2), S(y0 + 46)), 'מוקד שירות', font=font(S(54), 900), fill=WHITE, anchor='mm')
    d.text((S((x0 + x1) / 2), S(y0 + 150)), 'חברת האינטרנט שלי', font=font(S(40), 900), fill=INK, anchor='mm')
    d.text((S((x0 + x1) / 2), S(y0 + 222)), 'השיחה מוקלטת לשיפור השירות', font=font(S(28), 800), fill=(90, 90, 100), anchor='mm')
    router_icon(d, (x0 + x1) / 2, y1 - 80, 0.6)
    img = img.filter(ImageFilter.GaussianBlur(S(1.6)))
    img.alpha_composite(Image.new('RGBA', img.size, (255, 248, 236, 40)))
    return img

def board_num(t):
    s_t = story_t(t)
    if s_t < FF[0]: return QUEUE - 66
    if s_t < FF[1]: return int(lerp(QUEUE - 66, QUEUE, ease_in(clamp((s_t - FF[0]) / (FF[1] - FF[0] - 0.1)))))
    return QUEUE

T_HEAD = (215, 920); TS = 1.32
HX2, HY2, F2 = 815, 950, 1.48
QUEUE_TWO = [('c2', 600, 700, 0.44, 0.4), ('h0', 760, 640, 0.40, 1.6), ('c3', 1010, 700, 0.42, 2.4)]
FORM_C = (450, 1500); BILL_C = (770, 1495); SNACK_C = (1000, 1520)

def sh_dx(t):
    s_t = story_t(t)
    if s_t < ARRIVE: return -900
    return -900 * (1 - ease_out(clamp((s_t - ARRIVE) / 0.3)))

def cat_state(t):
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    s_t = story_t(t)
    if L['0b'] <= s_t < PLAY:               # "יש לי את ההקלטה! עכשיו נראה אותם!" — the disc held up, fierce joy
        u = s_t - L['0b']
        st.update(lid=0.0, pupil='big', brow='annoyed', mouth=cat_mouth(s_t, rest='smile', loud='w'), ear_dy=-30, blush=1.0, look=(-10, -6))
        rot = 4 * math.sin(u * 9); dy = -14 * voice_v(s_t, 'cat') - 6 * abs(math.sin(u * 7))
    elif t < FF[0]:                         # the want: outraged at the bill, crumbs
        st.update(lid=0.0, pupil='tiny', brow='annoyed', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-18, look=(-18, 6), sweat=0.6, blush=0.0)
        rot = 4 * math.sin(t * 5); dy = -12 * v
    elif t < ARRIVE:                        # x64: waiting, munching, glancing at the board
        u = (t - FF[0]) / (FF[1] - FF[0])
        st.update(lid=0.5 - 0.4 * u, pupil='normal', brow='none', mouth='flat' if int(t * 8) % 2 else 'w', look=(-30, -20), ear_droop=0.4 * (1 - u))
        dy = -6 * abs(math.sin(t * 14))
    elif t < L[2]:                          # "שרית?! גם פה?" double take
        u = t - L[27]
        st.update(lid=0.0, pupil='tiny', brow='up', ear_dy=-24 * math.exp(-max(0, u) * 2), mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0, look=(-20, 4))
        if u >= 0: rot = 8 * math.sin(u * 20) * math.exp(-u * 3); dy = -30 * math.exp(-u * 5)
    elif t < L[3]:                          # "בכתב, מותק. עם תאריך." — narrowed eyes, accepting the challenge
        st.update(lid=0.35, pupil='normal', brow='annoyed', mouth='flat', look=(-28, 12), blush=0.2)
    elif t < L[4]:                          # "שתים עשרה בנובמבר. הכול כתוב." — writing fast, proud
        st.update(lid=0.1, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='smile'), look=(-24, 18), blush=0.7, ear_dy=-12)
        dy = -10 * v + (-18 * math.exp(-(t - SLAP) * 7) if t >= SLAP else 0)
    elif t < L[103]:                        # "העותק הראשון חינם" — eyes huge on the disc
        u = t - DISC
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', look=(-30, 14), ear_dy=-20, blush=0.8)
        if u >= 0: dy = -8 * math.exp(-u * 3)
    elif t < L['0b']:                       # "יש!!!" — joy
        u = t - L[103]
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28 * math.exp(-u * 2), blush=1.0, look=(-8, 0))
        dy = -26 * abs(math.sin(u * 9)) * math.exp(-u * 1.0)
    elif t < BREAK:                         # THE PEAK: pointing at her, triumphant smirk
        st.update(lid=0.25, pupil='big', brow='up', mouth='smile', ear_dy=-22, blush=1.0, look=(-30, 2))
        if t >= L[5] + ss(5, 0) + 0.6: st.update(eye_mode='closed', ear_dy=-28); rot = -6; dy = -14
    else:                                   # his own voice — frozen
        u = t - BREAK
        me = t >= YOU
        st.update(lid=0.0, pupil='tiny', brow='none' if not me else 'up', mouth='flat' if not me else 'w', ear_dy=-24 * math.exp(-u * 4), look=(-22, 20),
                  twitch=(me and int(t * 12) % 2 == 0), sweat=clamp(u / 0.6), blush=0.0)
        dy = -8 - 14 * math.exp(-u * 8)
    return st, rot, dy

def sh_state(t):
    s_t = story_t(t)
    st = SH.base(); st.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.5, red=0.8, blush=0.6, look=(18, 6))
    talk = voice_v(t, 'sh') > 0.12
    st['mouth'] = 'talk' if talk else ('munch' if (int(t * 7)) % 2 and s_t < L[2] else 'grin')
    if s_t < L[2]: st.update(snack=True, lid=0.6)
    elif s_t < L[4]: st.update(look=(24, 20), lid=0.45, hand_r=(560, 720))               # slides the form
    elif s_t < PLAY: st.update(look=(24, 16), lid=0.4, blush=0.8)
    elif s_t < BREAK: st.update(look=(30, 4), lid=0.7, blush=0.6, mouth='lazy' if not talk else 'talk')   # listening, unbothered
    else: st.update(look=(28, 8), lid=0.55, blush=0.9, mouth='grin', snack=True)
    return st

def scene_two(t, i):
    img = BG.copy()
    s_t = story_t(t)
    E3.led_text(img, str(board_num(t)), BOARD_C[0], BOARD_C[1] + 20, 110)
    cheer = GOLDT <= s_t < PLAY
    for name, x, y, sc, ph in QUEUE_TWO:
        jump = (-20 * abs(math.sin(t * 9 + ph))) if cheer else 0
        mood = 1 if cheer else (0 if s_t >= YOU else 2)
        E13.paste_sprite(img, name, mood, x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    dx = sh_dx(t)
    if dx > -880:
        Ls = SH.draw(sh_state(t), i)
        Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
        img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] + dx - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state(t)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    # crumbs on his chest (the snack plant)
    rng = random.Random(39)
    for _ in range(9):
        E(d, HX2 + rng.uniform(-120, 120), 1360 + rng.uniform(0, 120), 7, 5, fill=(250, 214, 120), outline=(150, 96, 30), width=2)
    # counter
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1720)], radius=S(16), fill=(120, 122, 134), outline=(60, 62, 72), width=iw(6))
    d.rectangle([S(-20), S(1580), S(1100), S(1606)], fill=(160, 162, 176))
    # the snack bag on the counter (always)
    SH.snack_bag(d, SNACK_C, 14, 0.8)
    # the bill: held up during the want, then on the counter (always visible: the plant)
    held = T0 <= s_t < L[27] and t >= T0
    if not held:
        paste_rot(img, BILL, BILL_C, -4, 0.8, 80)
    # the form
    if s_t >= FORMIN:
        u = s_t - FORMIN
        c = lerp2((150, 1500), FORM_C, ease_out(clamp(u / 0.3)))
        wr = clamp((s_t - WRITE[0]) / (WRITE[1] - WRITE[0]))
        lay = FORM_DONE if s_t >= SLAP else (form_layer(wr) if wr > 0 else FORM0)
        paste_rot(img, lay, c, 3, 0.85, 80)
    d = ImageDraw.Draw(img)
    # the disc: slides over from Sharit, then in his paw
    disc_in_paw = s_t >= L[103]
    if DISC <= s_t < L[103]:
        u = s_t - DISC
        paste_rot(img, DISCL, lerp2((260, 1460), (620, 1440), ease_out(clamp(u / 0.35))), -8, 0.8, 80)
        if 0 <= s_t - GOLDT < 0.3: burst(img, (620, 1440), s_t - GOLDT, (255, 220, 120), 200, 12, 0.3)
    d = ImageDraw.Draw(img)
    if held:                                                   # the bill held up in his paw during the want
        bc = (600 + 10 * math.sin(t * 6), 1210 + 12 * math.sin(t * 9))
        capsule(d, (HX2 - 160, 1540), (bc[0] + 170, bc[1] + 20), 100, FUR, OUT, 4)
        paste_rot(img, BILL, bc, -8 + 5 * math.sin(t * 5), 0.95, 90)
        d = ImageDraw.Draw(img); E12.big_paw(d, (bc[0] + 170, bc[1] + 20), 20, 0.7)
    elif WRITE[0] <= s_t < SLAP + 0.25:                         # writing + the slap
        if s_t < WRITE[1]:
            u = clamp((s_t - WRITE[0]) / (WRITE[1] - WRITE[0]))
            pp = (FORM_C[0] + 60 - 120 * u, FORM_C[1] - 60 + 6 * math.sin(u * 30))
        elif s_t < SLAP:
            pp = lerp2((FORM_C[0], FORM_C[1] - 60), (FORM_C[0] + 40, FORM_C[1] - 200), ease_out(clamp((s_t - WRITE[1]) / 0.3)))
        else:
            pp = lerp2((FORM_C[0] + 40, FORM_C[1] - 200), FORM_C, ease_in(clamp((s_t - SLAP) / 0.08)))
        capsule(d, (HX2 - 160, 1540), pp, 100, FUR, OUT, 4)
        if s_t < WRITE[1]: line(d, [(pp[0] - 10, pp[1] - 10), (pp[0] - 60, pp[1] - 70)], (30, 60, 160), 12)
        E12.big_paw(d, pp, -20, 0.7)
        if s_t >= SLAP: burst(img, FORM_C, s_t - SLAP, (255, 255, 255), 140, 8, 0.25)
    elif disc_in_paw and s_t < PLAY:                           # the disc held up high (the cold-open shot)
        u = s_t - L[103]
        dc = (560 + 8 * math.sin(t * 7), 1120 - 30 * ease_out(clamp(u / 0.3)) + 10 * math.sin(t * 9))
        capsule(d, (HX2 - 160, 1540), (dc[0] + 50, dc[1] + 120), 100, FUR, OUT, 4)
        paste_rot(img, DISCL, dc, -10 + 6 * math.sin(t * 6), 1.1, 90)
        d = ImageDraw.Draw(img); E12.big_paw(d, (dc[0] + 50, dc[1] + 120), -10, 0.75)
    elif s_t >= PLAY:                                          # the player by his face, the other paw points at her
        u = s_t - PLAY
        pc = lerp2((760, 2100), (560, 1130), ease_out(clamp(u / 0.18)))
        capsule(d, (HX2 - 160, 1540), (pc[0] + 30, pc[1] + 160), 100, FUR, OUT, 4)
        shake_ = 3 * math.sin(u * 30) * math.exp(-u * 5) + (2 * math.sin(t * 40) if t >= YOU else 0)
        paste_rot(img, player_layer(t), pc, 5 + shake_, 0.62)
        d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 30, pc[1] + 160), -10, 0.7)
    else:
        rp = (HX2 - 140, 1480 + 8 * math.sin(t * 2.0))
        capsule(d, (HX2 - 160, 1540), rp, 100, FUR, OUT, 4); E12.big_paw(d, rp, 10, 0.85)
    if cheer: E18.confetti(img, s_t - GOLDT + 0.3)
    burst(img, FORM_C, s_t - CHK1, (120, 255, 160), 160, 10, 0.4)
    if s_t >= YOU: burst(img, (560, 1000), s_t - YOU, (255, 120, 120), 220, 12, 0.4)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('תאריך', 820, CHK1), ('בכתב', 540, CHK2), ('ההקלטה', 260, CHK3)]
def chips(frame, t, y=330):
    if t < T0 + 0.2 or t >= YOU + 0.6: return
    gold = t >= GOLDT
    drained = t >= YOU
    d = ImageDraw.Draw(frame)
    for lab, cx, tk in CHIPS:
        ok = t >= tk and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if drained: sc = 1.0 + 0.15 * math.exp(-(t - YOU) * 10)
        w, h = 230 * sc, 70 * sc
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
    f = font(size, 900); lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

BG = BILL = FORM0 = FORM_DONE = DISCL = PILL_EP = PILL_Q = PILL_PART = None
def init_all():
    global BG, BILL, FORM0, FORM_DONE, DISCL, PILL_EP, PILL_Q, PILL_PART
    m.init_static(); E3.init_all()
    E13.build_crowd()
    BG = build_service_bg()
    BILL = bill_layer(); FORM0 = form_layer(0); FORM_DONE = form_layer(1.0); DISCL = disc_layer()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_PART = HUD._pill(PART_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'two':
        z, cx, cy = 1.05 + 0.01 * pu, 540, 1000
        if a == 0.0:                                   # cold open: straight-on and tight, the disc pushed at the lens
            z, cx, cy = 1.42 + 0.03 * t, 690, 1150
            if t < 0.3: z = 1.62 - 0.20 * ease_out(t / 0.3)
        elif t < FF[0]: z, cx, cy = 1.22, 720, 1080   # the want: close on him and the bill
        elif t < ARRIVE: z, cx, cy = 1.0, 540, 960     # x64 wide: the board races
        elif L[27] <= t < L[27] + 0.8: z, cx, cy = 1.12, 520, 980
        elif FORMIN <= t < L[4]: z, cx, cy = 1.15, 460, 1080
        elif L['0b'] <= t < PLAY: z, cx, cy = 1.42, 690, 1150
        elif PLAY <= t < HOLD[0]: z, cx, cy = 1.10, 560, 1040
        if HOLD[0] <= t < BREAK:
            k = ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0]))); z, cx, cy = 1.10 + 0.12 * k, lerp(560, 660, k), lerp(1040, 1080, k)
        if t >= BREAK: z, cx, cy = 1.22 + (0.10 * ease_out(clamp((t - YOU) / 0.2)) if t >= YOU else 0), 660, 1080
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1000
    elif name == 'frozen':
        z, cx, cy = 1.34 + 0.03 * pu, 680, 1080
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_two(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    else: img = scene_two(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (SLAP, PLAY, YOU):
        if 0 <= t - s_ < 0.3: shake = 14 * math.exp(-(t - s_) * 8)
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
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(60 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if FF[0] <= t < FF[1]: ff_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, YOU):
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
            col = {'sh': SHARIT_SUB, 'rec': IVRSUB, 'recme': IVRSUB}.get(SPEAKER[li], WHITE)
            m.paste_center(frame, sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < FF[0]) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_PART, (40 + PILL_EP.width + 10, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + service-centre room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(39)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] in ('rec', 'recme'): y = m.phone_line(y) * 1.6
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
    def slap(t0, g=0.5): add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), t0, g)
    def crunch(t0, g=0.10, k=3):
        for j in range(k): add(sfx, m.bandpass(nz(0.05), 1500, 6000) * np.exp(-tt_(0.05) * 50), t0 + j * 0.09, g)
    def cheer(t0, ln=1.0, g=0.10):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    def ding(t0, g=0.16):
        add(sfx, m.tone(1046.5, 0.6, harm=((1, 1), (2.76, 0.2)), decay=5), t0, g); add(sfx, m.tone(784.0, 0.8, harm=((1, 1), (2.76, 0.2)), decay=4), t0 + 0.16, g)
    def click(t0, g=0.3): add(sfx, m.highpass(nz(0.02), 2500) * np.exp(-tt_(0.02) * 150), t0, g)
    # cold open: impact + the cheer tail
    add(sfx, thud(0.8), 0.0); slap(0.0, 0.4); cheer(0.0, COLD_END, 0.06)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(HOLD[0]), 150, 900) * 0.6, 0.0, 0.012)                       # room tone
    add(sfx, m.bandpass(nz(DUR - BREAK + 0.3), 150, 900) * 0.6, BREAK, 0.012)
    crunch(L[1] + D[1] + 0.02); crunch(FF[0] + 0.4, 0.08); crunch(FF[0] + 0.9, 0.08)   # he munches (the plant)
    add(sfx, m.bandpass(nz(0.4), 600, 5000) * np.linspace(0, 1, int(0.4 * SR)), FF[0] - 0.3, 0.06)
    tc = FF[0]
    while tc < FF[1]:
        add(sfx, m.tone(1200 + 200 * math.sin(tc * 9), 0.03, harm=((1, 1),), decay=40), tc, 0.025); tc += 0.07
    ding(DING); whoosh(ARRIVE, 0.08, 0.3)
    add(sfx, m.bandpass(nz(0.3), 300, 3000) * np.sin(np.pi * tt_(0.3) / 0.3), FORMIN, 0.08)     # the form slides
    for k in range(int((WRITE[1] - WRITE[0]) / 0.09)):                                        # pen scratch
        add(sfx, m.bandpass(nz(0.05), 2500, 7000) * np.exp(-tt_(0.05) * 30), WRITE[0] + k * 0.09, 0.05)
    check(CHK1, 0.15)
    slap(SLAP, 0.6); add(sfx, thud(0.5), SLAP); check(CHK2, 0.15)
    add(sfx, m.bandpass(nz(0.35), 300, 3000) * np.sin(np.pi * tt_(0.35) / 0.35), DISC, 0.08)   # the disc slides
    check(CHK3, 0.2, True); cheer(GOLDT + 0.1, L['0b'] + 0.5 - GOLDT, 0.09)
    whoosh(PLAY, 0.1, 0.2); click(PLAY + 0.12); add(sfx, m.bandpass(nz(FREEZE - PLAY), 300, 3400) * 0.5, PLAY + 0.15, 0.010)  # line hiss
    heartbeat(HOLD[0] + 0.04); heartbeat(HOLD[0] + 0.30, 0.5)
    crunch(L[101] - 0.02, 0.12, 2)                                                            # the crunch on the recording
    add(sfx, thud(0.6), YOU)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), YOU + 0.15, 0.16)
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
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', T0, 'FF', [round(x, 2) for x in FF])
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'WRITE', [round(x, 2) for x in WRITE], 'PLAY', round(PLAY, 2),
              'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK, 2), 'YOU', round(YOU, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        print('SEG', {k: len(v) for k, v in SEG.items()})
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep39_contact.png')); print('ok'); return
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
