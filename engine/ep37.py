#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 37: נקודת איסוף (season 8 "בלאק פריידיי" ep4, VOICED, built 16.11 under §P, ~21 s).
Voices = voice bank 2026-11-13 lines 3700–3707 (Benji = cat, Delia = Sharit) + 2703 "שרית?! גם פה?" + stock 9103 "יש!!!",
prepared by voice/ep37_prep.py.
Set: the pickup point inside the kiosk (ep27/ep33 world): parcel shelves, a "נקודת איסוף" plaque, Sharit behind the counter
in the orange kiosk uniform (ep33), the queue behind him.
Want: pick up the Black Friday box himself ("באתי לאסוף. בעצמי. בלי שליחים." — after ep36 it went to grandma).
Plant: Sharit's own pickup slip lying by her till: "איסוף · שרית · 4417" — the same code as his SMS. Visible in the cold
open and again when he shows his SMS. Never pointed at.
Climb (3 chips): the SMS "קוד 4417" ✓ → the ID "בתוקף?" "חדשה! מלפני חודש!" ✓ → Sharit fetches the box, "וואו, כבד... אני
אעזור לך, חמוד." they carry it together ✓ → "יש!!!" gold, the queue cheers.
Peak: "סוף סוף... ביד." — the box in his arms, eyes closed, hush + heartbeat.
Break (reversal_of_help): "תודה, מותק. זה שלי." — she slides the box out of his arms to her side (her slip, the same
code); frozen face, his arms still round nothing; whip into the cold open (loop).
No music (voiced rule): voices + SFX + kiosk room tone. Serial pills "פרק 37" + live ticket number (hud.stage_of, §O4).

  python3 voice/ep37_prep.py
  python3 ep37.py times | test t1 t2 ... | render   -> out/ep37_isuf.mp4
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
VDIR = os.path.join(HERE, 'voice', 'ep37', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 104, 226)
ORANGE = (255, 120, 30); SHARIT_SUB = (255, 182, 210)
QUEUE = int(os.environ.get('QUEUE', '446'))
EP_LABEL = 'פרק 37'
OUTNAME = os.environ.get('OUTNAME', 'ep37_isuf')
LIMIT = float(os.environ.get('LIMIT', '0'))
CODE = '4417'

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
COLD_END = round(D[4] + 0.14, 2)            # cold open = 3704 "חדשה! מלפני חודש!" + the ID slap (the loudest line of the climb)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[0] = T0 + 0.05                            # want: "באתי לאסוף. בעצמי. בלי שליחים."
L[27] = L[0] + D[0] + 0.10                  # "שרית?! גם פה?"
L[1] = L[27] + D[27] + 0.08                 # Sharit: "הודעה, מותק?"
L[2] = L[1] + D[1] + 0.06                   # "הנה. החבילה מחכה לי." — the SMS held up
PHONE_UP = L[2] - 0.05
CHK1 = L[2] + ss(2, 1)
L[3] = L[2] + D[2] + 0.10                   # Sharit: "תעודת זהות. בתוקף?"
L['4b'] = L[3] + D[3] + 0.06                # "חדשה! מלפני חודש!" in context
IDSLAP = L['4b'] + 0.08
CHK2 = L['4b'] + 0.35
FETCH = L['4b'] + D[4] + 0.05               # she turns, the box comes off the shelf
L[5] = FETCH + 0.45                         # "וואו, כבד... אני אעזור לך, חמוד."
LAND = L[5] + 0.15                          # the box hits the counter
CHK3 = L[5] + D[5] - 0.35                   # the box in his arms
L[103] = L[5] + D[5] + 0.06                 # "יש!!!"
GOLDT = L[103] + 0.02
L[6] = L[103] + D[103] + 0.10               # "סוף סוף... ביד." (peak)
HOLD = (L[6] + D[6] + 0.03, L[6] + D[6] + 0.52)
BREAK = HOLD[1]
L[7] = BREAK                                # Sharit: "תודה, מותק. זה שלי."
TAKE = L[7] + ss(7, 1) - 0.05               # "זה שלי." — the box slides out of his arms
FREEZE = L[7] + D[7]
DUR = round(FREEZE + 0.42, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(4, 0.0), (0, L[0]), (27, L[27]), (1, L[1]), (2, L[2]), (3, L[3]), (4, L['4b']), (5, L[5]), (103, L[103]), (6, L[6]), (7, L[7])]
SPEAKER = {0: 'cat', 27: 'cat', 2: 'cat', 4: 'cat', 6: 'cat', 103: 'cat', 1: 'sh', 3: 'sh', 5: 'sh', 7: 'sh'}

SUBS = {
    0: [['באתי לאסוף.'], ['בעצמי.'], ['בלי שליחים.']],
    27: [['שרית?! גם פה?']],
    1: [['הודעה, מותק?']],
    2: [['הנה.'], ['החבילה מחכה לי.']],
    3: [['תעודת זהות.'], ['בתוקף?']],
    4: [['חדשה!'], ['מלפני חודש!']],
    5: [['וואו, כבד...'], ['אני אעזור לך, חמוד.']],
    103: [['יש!!!']],
    6: [['סוף סוף...'], ['ביד.']],
    7: [['תודה, מותק.'], ['זה שלי.']],
}
SUB_TIMES = []
for k_, (li, s0) in enumerate(OCC):
    nxt = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR
    ch = SUBS[li]
    starts = [0.0] + [ss(li, k) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.2)
        b = min(b, nxt - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 7 and k == len(ch) - 1: b = DUR - 0.25
        if li == 6 and k == len(ch) - 1: b = min(b, HOLD[0] + 0.02)
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('two', 0.0, COLD_END), ('rewind', COLD_END, T0), ('two', T0, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['אוספים חבילה', 'מנקודת איסוף?']       # keyword: חבילה / נקודת איסוף (F16 pain question)
TOPCAPS = [(0.0, COLD_END, HOOK), (T0, L[27] - 0.1, HOOK)]

def shot(t):
    for name, a, b in SHOTS:
        if a <= t < b: return name, a, b
    return SHOTS[-1]

def story_t(t):
    return L['4b'] + t if t < COLD_END else t

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
def sms_layer():
    pw, ph = 400, 720
    lay = Image.new('RGBA', (S(pw), S(ph)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(pw) - 1, S(ph) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(pw - 14), S(ph - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(pw / 2 - 56), S(28), S(pw / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.rounded_rectangle([S(30), S(110), S(pw - 30), S(470)], radius=S(26), fill=WHITE, outline=(200, 204, 214), width=iw(3))
    pd.text((S(pw - 56), S(156)), 'נקודת איסוף', font=font(S(32), 900), fill=(90, 96, 110), anchor='rm')
    pd.text((S(pw / 2), S(236)), 'החבילה שלך', font=font(S(44), 900), fill=INK, anchor='mm')
    pd.text((S(pw / 2), S(292)), 'מחכה לך!', font=font(S(44), 900), fill=GREEN, anchor='mm')
    pd.rounded_rectangle([S(70), S(336), S(pw - 70), S(436)], radius=S(18), fill=(255, 244, 214), outline=ORANGE, width=iw(4))
    pd.text((S(pw / 2), S(388)), f'קוד {CODE}', font=font(S(58), 900), fill=INK, anchor='mm')
    pd.text((S(pw / 2), S(540)), 'מארז חטיפים ענק', font=font(S(30), 800), fill=(110, 112, 124), anchor='mm')
    return lay

def id_layer():
    w_, h_ = 360, 230
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(w_) - 1, S(h_) - 1], radius=S(20), fill=(214, 236, 246), outline=(60, 90, 120), width=iw(5))
    d.rectangle([S(0), S(0), S(w_), S(46)], fill=(40, 90, 170))
    d.text((S(w_ / 2), S(24)), 'תעודת זהות', font=font(S(30), 900), fill=WHITE, anchor='mm')
    d.rounded_rectangle([S(w_ - 130), S(64), S(w_ - 24), S(196)], radius=S(10), fill=(255, 220, 160), outline=(120, 90, 60), width=iw(3))
    E(d, w_ - 77, 132, 40, 38, fill=FUR, outline=OUT, width=3)
    for side in (-1, 1): poly(d, [(w_ - 77 + side * 34, 112), (w_ - 77 + side * 28, 82), (w_ - 77 + side * 10, 100)], fill=FUR, outline=OUT, width=3)
    for k in range(3): d.rounded_rectangle([S(30), S(76 + k * 40), S(w_ - 150), S(96 + k * 40)], radius=S(6), fill=(150, 170, 190))
    d.rounded_rectangle([S(26), S(188), S(170), S(222)], radius=S(16), fill=GREEN)
    d.text((S(98), S(205)), 'חדשה', font=font(S(24), 900), fill=WHITE, anchor='mm')
    return lay

def slip_layer():
    """the plant: Sharit's own pickup slip by her till"""
    w_, h_ = 230, 150
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(w_) - 1, S(h_) - 1], fill=(252, 250, 240), outline=(170, 166, 150), width=iw(3))
    d.text((S(w_ / 2), S(34)), 'איסוף', font=font(S(30), 900), fill=(110, 110, 120), anchor='mm')
    d.text((S(w_ / 2), S(76)), 'שרית', font=font(S(30), 800), fill=(110, 110, 120), anchor='mm')
    d.text((S(w_ / 2), S(118)), CODE, font=font(S(34), 900), fill=(90, 90, 100), anchor='mm')
    return lay

def box_layer():
    w_, h_ = 520, 380
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(w_) - 1, S(h_) - 1], radius=S(12), fill=(214, 168, 112), outline=(110, 72, 36), width=iw(7))
    d.rectangle([S(w_ / 2 - 32), 0, S(w_ / 2 + 32), S(h_)], fill=(236, 206, 150))
    d.rounded_rectangle([S(40), S(50), S(230), S(150)], radius=S(8), fill=WHITE, outline=(120, 120, 130), width=iw(3))
    d.text((S(135), S(84)), 'בלאק פריידיי', font=font(S(28), 900), fill=INK, anchor='mm')
    d.text((S(135), S(124)), CODE, font=font(S(30), 900), fill=(90, 90, 100), anchor='mm')
    for x in (330, 400, 460):
        poly(d, [(x, 250), (x + 24, 300), (x - 24, 300)], fill=(150, 110, 70))
    return lay

def paste_rot(img, lay, c, ang=0.0, sc=1.0, a=100):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    V1.shadow_paste(img, lay, c, a, (14, 18), 10)

burst = E18.burst

# ------------------------------------------------------------------ the set: pickup point in the kiosk
def build_pickup_bg():
    kb = V1.build_kiosk_bg()
    d = ImageDraw.Draw(kb)
    # parcel shelf on the left (behind Sharit)
    d.rectangle([S(0), S(380), S(470), S(1180)], fill=(120, 84, 54))
    rng = random.Random(37)
    for row, y in enumerate((470, 690, 910, 1130)):
        d.rectangle([S(0), S(y), S(470), S(y + 18)], fill=(80, 54, 30))
        x = 20
        while x < 440:
            w_ = rng.uniform(80, 150); h_ = rng.uniform(70, 170)
            d.rectangle([S(x), S(y - h_), S(x + w_), S(y)], fill=(206, 160, 106), outline=(110, 72, 36), width=iw(3))
            d.rectangle([S(x + w_ / 2 - 8), S(y - h_), S(x + w_ / 2 + 8), S(y)], fill=(230, 200, 150))
            x += w_ + 8
    E8.plaque(d, 300, 330, 'נקודת איסוף', 360)
    kb = kb.filter(ImageFilter.GaussianBlur(S(2.0)))
    kb.alpha_composite(Image.new('RGBA', kb.size, (255, 252, 240, 50)))
    return kb

def kiosk_sharit(st, i):
    keep = (SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O)
    SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O = (240, 128, 40), (206, 96, 24), (110, 50, 10)
    try: return SH.draw(st, i)
    finally: SH.BLOUSE, SH.BLOUSE_D, SH.BLOUSE_O = keep

T_HEAD = (215, 920); TS = 1.32
HX2, HY2, F2 = 815, 950, 1.48
QUEUE_TWO = [('c2', 600, 700, 0.44, 0.4), ('h0', 720, 640, 0.40, 1.6), ('c3', 1010, 700, 0.42, 2.4)]
SLIP_C = (120, 1520); ID_C = (560, 1530)

def box_pos(t):
    """None before FETCH; the box from the shelf → counter → his arms → back to her side"""
    st = story_t(t)
    if st < FETCH: return None
    shelf, counter, arms, hers = (150, 900), (430, 1440), (740, 1360), (240, 1430)
    if st < LAND: return lerp2(shelf, counter, ease_in(clamp((st - FETCH) / (LAND - FETCH)))), 0.75
    if st < CHK3 - 0.4: return counter, 0.75
    if st < CHK3: return lerp2(counter, arms, ease_io(clamp((st - (CHK3 - 0.4)) / 0.4))), 0.75 + 0.1 * clamp((st - (CHK3 - 0.4)) / 0.4)
    if st < TAKE: return arms, 0.85
    return lerp2(arms, hers, ease_out(clamp((st - TAKE) / 0.35))), 0.85

def cat_state(t):
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    s_t = story_t(t)
    if L['4b'] <= s_t < FETCH:              # "חדשה! מלפני חודש!" — proud, the ID slapped down
        u = s_t - L['4b']
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28, blush=1.0, look=(-26, 8))
        rot = 6 * math.sin(u * 12) * math.exp(-u * 1.5); dy = -24 * math.exp(-u * 4) - 12 * v
    elif t < L[27]:                         # the want: determined, chin up
        st.update(lid=0.2, pupil='big', brow='none', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-14, look=(-24, 6), blush=0.6)
        rot = 3 * math.sin(t * 4); dy = -10 * v
    elif t < L[1]:                          # "שרית?! גם פה?" double take
        u = t - L[27]
        st.update(lid=0.0, pupil='tiny', brow='up', ear_dy=-24 * math.exp(-u * 2), mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0, look=(-20, 4))
        rot = 8 * math.sin(u * 20) * math.exp(-u * 3); dy = -30 * math.exp(-u * 5)
    elif t < L[3]:                          # "הנה. החבילה מחכה לי." — phone up, confident
        st.update(lid=0.25, pupil='normal', brow='none', mouth=cat_mouth(t, rest='smile', loud='smile'), look=(-22, 8), blush=0.5)
        if t >= CHK1: dy = -14 * math.exp(-(t - CHK1) * 6)
    elif t < L['4b']:                       # "תעודת זהות. בתוקף?" — eyes narrow, a grin
        st.update(lid=0.45, pupil='normal', brow='annoyed', mouth='smile', look=(-26, 10))
    elif t < CHK3:                          # the box comes: eyes huge
        u = t - FETCH
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', ear_dy=-26, blush=0.9, look=(-30, 14))
        dy = -10 * abs(math.sin(u * 6))
    elif t < L[6]:                          # "יש!!!" — joy
        u = t - CHK3
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28 * math.exp(-u * 2), blush=1.0, look=(-8, 0))
        dy = -24 * abs(math.sin(u * 9)) * math.exp(-u * 1.2)
    elif t < BREAK:                         # THE PEAK: box hugged, eyes closed
        if t < HOLD[0]: st.update(lid=0.3, mouth=cat_mouth(t, rest='smile', loud='smile'), ear_dy=-14, blush=1.0, look=(-10, 10)); rot = -3
        else: st.update(eye_mode='closed', mouth='smile', ear_dy=-28, blush=1.0, look=(0, -8)); dy = -12; rot = -6
    else:                                   # "תודה, מותק. זה שלי." — frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none', mouth='flat', ear_dy=-20 * math.exp(-u * 4), look=(-26, 12) if t >= TAKE else (-14, 0),
                  twitch=(t >= TAKE + 0.3 and int(t * 12) % 2 == 0), sweat=clamp((t - TAKE) / 0.4), blush=0.0)
        dy = -8
    return st, rot, dy

def sh_state(t):
    s_t = story_t(t)
    st = SH.base(); st.update(hand_l=(170, 760), hand_r=(530, 760), lid=0.5, red=0.8, blush=0.6, look=(18, 6))
    talk = voice_v(t, 'sh') > 0.12
    st['mouth'] = 'talk' if talk else ('munch' if (int(t * 7)) % 2 and s_t < L[1] else 'grin')
    if s_t < L[1]: st.update(snack=True, lid=0.6)
    elif s_t < L['4b']: st.update(look=(24, 12), lid=0.45, hand_r=(560, 700))
    elif s_t < FETCH: st.update(look=(24, 20), lid=0.3, blush=0.8)                                # looks at the new ID
    elif s_t < CHK3: st.update(look=(-10, -4), lid=0.4, rot=-5, hand_r=(520, 600), hand_l=(200, 600))   # carrying
    elif s_t < BREAK: st.update(look=(20, 6), lid=0.5, blush=1.0, mouth='grin' if not talk else 'talk')
    else: st.update(look=(20, 10), lid=0.55, blush=0.7, hand_r=(560, 640))
    return st

def scene_two(t, i):
    img = BG.copy()
    s_t = story_t(t)
    cheer = GOLDT <= s_t < BREAK - 0.05
    for name, x, y, sc, ph in QUEUE_TWO:
        jump = (-20 * abs(math.sin(t * 9 + ph))) if cheer else 0
        mood = 1 if cheer else (0 if s_t >= TAKE + 0.2 else 2)
        E13.paste_sprite(img, name, mood, x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    Ls = kiosk_sharit(sh_state(t), i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state(t)
    E(d, HX2, 1720, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1770, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    # counter
    d.rounded_rectangle([S(-20), S(1580), S(1100), S(1720)], radius=S(16), fill=(150, 96, 58), outline=(80, 50, 28), width=iw(6))
    d.rectangle([S(-20), S(1580), S(1100), S(1606)], fill=(190, 130, 80))
    paste_rot(img, SLIP, SLIP_C, 6, 0.8, 80)                                                  # the plant
    if s_t >= IDSLAP - 0.12 and s_t < FETCH + 0.6:
        u = s_t - IDSLAP
        c = lerp2((760, 1250), ID_C, ease_in(clamp((u + 0.12) / 0.12))) if u < 0 else ID_C
        paste_rot(img, IDC, c, -6, 0.85, 90)
        if 0 <= u < 0.3: burst(img, ID_C, u, (255, 255, 255), 120, 8, 0.25)
    d = ImageDraw.Draw(img)
    bp = box_pos(t)
    hug = bp is not None and story_t(t) >= CHK3 - 0.05 and story_t(t) < TAKE
    if bp is not None:
        paste_rot(img, BOX, bp[0], -3 if hug else 2, bp[1], 100)
        d = ImageDraw.Draw(img)
    # his paws
    if hug:
        for side in (-1, 1):
            rp = (bp[0][0] + side * 210, bp[0][1] + 20)
            capsule(d, (HX2 + side * 200, 1520), rp, 100, FUR, OUT, 4); E12.big_paw(d, rp, side * 30, 0.85)
    elif s_t >= TAKE:                         # arms still round nothing
        for side in (-1, 1):
            rp = (740 + side * 190, 1380)
            capsule(d, (HX2 + side * 200, 1520), rp, 100, FUR, OUT, 4); E12.big_paw(d, rp, side * 30, 0.85)
    elif PHONE_UP <= s_t < L['4b']:
        e = ease_out(clamp((s_t - PHONE_UP) / 0.25))
        pc = lerp2((780, 1700), (540, 1180), e)
        capsule(d, (HX2 - 160, 1540), (pc[0] + 30, pc[1] + 170), 100, FUR, OUT, 4)
        paste_rot(img, SMS, pc, 4, 0.62)
        d = ImageDraw.Draw(img); E12.big_paw(d, (pc[0] + 30, pc[1] + 170), -10, 0.7)
    else:
        rp = (HX2 - 140, 1480 + 8 * math.sin(t * 2.0))
        if IDSLAP - 0.12 <= s_t < IDSLAP + 0.3: rp = (ID_C[0] + 90, ID_C[1] - 30)
        capsule(d, (HX2 - 160, 1540), rp, 100, FUR, OUT, 4); E12.big_paw(d, rp, 10, 0.85)
    if cheer: E18.confetti(img, s_t - GOLDT + 0.3)
    burst(img, (540, 1180), s_t - CHK1, (120, 255, 160), 160, 10, 0.4)
    burst(img, ID_C, s_t - CHK2, (120, 255, 160), 140, 10, 0.4)
    burst(img, (740, 1360), s_t - CHK3, (255, 236, 120), 220, 12, 0.4)
    if s_t >= TAKE: burst(img, (740, 1300), s_t - TAKE, (255, 120, 120), 200, 12, 0.4)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('הודעה', 820, CHK1), ('תעודה', 540, CHK2), ('חבילה', 260, CHK3)]
def chips(frame, t, y=330):
    if t < COLD_END or t >= TAKE + 0.6: return
    gold = t >= GOLDT
    drained = t >= TAKE
    d = ImageDraw.Draw(frame)
    for lab, cx, tk in CHIPS:
        ok = t >= tk and not drained
        fill = GOLD if (gold and not drained) else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or (gold and not drained)) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        if drained: sc = 1.0 + 0.15 * math.exp(-(t - TAKE) * 10)
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

def sub_layer(lines, fill, size=64):
    f = font(size, 900); lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

BG = SMS = IDC = SLIP = BOX = PILL_EP = PILL_Q = None
def init_all():
    global BG, SMS, IDC, SLIP, BOX, PILL_EP, PILL_Q
    m.init_static(); E3.init_all()
    E13.build_crowd()
    BG = build_pickup_bg()
    SMS = sms_layer(); IDC = id_layer(); SLIP = slip_layer(); BOX = box_layer()
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'two':
        z, cx, cy = 1.05 + 0.01 * pu, 540, 1000
        if a == 0.0:                                   # cold open: tight on his face + the ID slap
            z, cx, cy = 1.38 + 0.03 * t, 700, 1080
            if t < 0.3: z = 1.55 - 0.17 * ease_out(t / 0.3)
        elif L[27] <= t < L[27] + 0.8: z, cx, cy = 1.12, 520, 980
        elif L[1] <= t < L[2] or L[3] <= t < L['4b']:   # Sharit's questions: lean toward her
            z, cx, cy = 1.15, 380, 1000
        elif L['4b'] <= t < FETCH: z, cx, cy = 1.15, 680, 1080
        if HOLD[0] <= t < BREAK:
            k = ease_io(clamp((t - HOLD[0]) / (BREAK - HOLD[0]))); z, cx, cy = 1.05 + 0.15 * k, lerp(540, 700, k), lerp(1000, 1060, k)
        if t >= BREAK: z, cx, cy = 1.12, 520, 1020
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1000
    elif name == 'frozen':
        z, cx, cy = 1.32 + 0.03 * pu, 760, 1000
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_two(lerp(L['4b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    else: img = scene_two(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (IDSLAP, LAND, TAKE):
        if 0 <= t - s_ < 0.3: shake = 12 * math.exp(-(t - s_) * 8)
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
    for s_ in (CHK1, CHK2, CHK3, GOLDT, TAKE):
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
            m.paste_center(frame, sub_layer(lines, SHARIT_SUB if SPEAKER[li] == 'sh' else WHITE), W / 2, 1560)
    if t < COLD_END or (T0 <= t < L[27] - 0.1) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + kiosk room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(37)
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
    def slap(t0, g=0.5): add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), t0, g)
    def cheer(t0, ln=1.0, g=0.10):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    # cold open: the ID slap on its in-context time
    slap(0.0, 0.5); add(sfx, thud(0.7), 0.0)
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(HOLD[0]), 150, 900) * 0.6, 0.0, 0.012)                       # kiosk room tone
    add(sfx, m.bandpass(nz(DUR - BREAK + 0.3), 150, 900) * 0.6, BREAK, 0.012)
    for k in range(int((L[1] - T0) / 0.5)):                                             # Sharit munching
        add(sfx, m.bandpass(nz(0.06), 1500, 6000) * np.exp(-tt_(0.06) * 40), T0 + 0.2 + k * 0.5, 0.05)
    whoosh(PHONE_UP); check(CHK1, 0.15)
    slap(IDSLAP, 0.5); add(sfx, thud(0.5), IDSLAP); check(CHK2, 0.15)
    whoosh(FETCH, 0.08, 0.3)
    add(sfx, thud(1.0), LAND); add(sfx, m.lowpass(nz(0.3), 500) * np.exp(-tt_(0.3) * 12), LAND, 0.4)  # the heavy box lands
    add(sfx, m.bandpass(nz(0.5), 200, 1200) * np.sin(np.pi * tt_(0.5) / 0.5), CHK3 - 0.4, 0.1)        # cardboard scrape
    check(CHK3, 0.15); check(GOLDT, 0.2, True); cheer(GOLDT + 0.1, L[6] - GOLDT, 0.08)
    heartbeat(HOLD[0] + 0.04); heartbeat(HOLD[0] + 0.30, 0.5)
    add(sfx, m.bandpass(nz(0.4), 200, 1200) * np.sin(np.pi * tt_(0.4) / 0.4), TAKE, 0.16)              # the box slides away
    add(sfx, thud(0.6), TAKE + 0.3)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), TAKE + 0.35, 0.20)
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
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'FETCH', round(FETCH, 2), 'LAND', round(LAND, 2), 'GOLDT', round(GOLDT, 2),
              'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK, 2), 'TAKE', round(TAKE, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep37_contact.png')); print('ok'); return
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
