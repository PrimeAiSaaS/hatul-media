#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 43: תור אונליין: אפריל (season 9 "הקו פנוי" ep5, season finale, VOICED, built 20.11 under §P, ~22 s).
Voices = voice bank 2026-11-19 lines 4300–4305 (Benji = cat, Delia = Sharit) + 2703 "שרית?! גם פה?" + stock 9103 "יש!!!",
prepared by voice/ep43_prep.py.
Set: the משרד הפנים lobby, window 3 behind glass (Sharit inside, typing with one finger), the door sign
"קבלת קהל בזימון תור בלבד" — he is IN the lobby and still has to book online.
Want: a slot before April — his ID is valid until 3.12 (the card in his paw in the want shot).
Plant: the paper taped on window 3's glass: "שרית · חלון 3" + grey "חופשה: 2.12–4.12" (cold open + want), and again
on the phone as the chat header under her avatar mid-climb. Never pointed at.
Climb (3 chips): פברואר ✓ (after "תרענן, מותק.") → ינואר ✓ → מחר ✓ gold (Sharit, from 2 m away on the chat:
"מחר, חלון שלוש. רק בשבילך, חמוד.", "יש!!!").
Peak: he books it — "התור נקבע ✓ · מחר 2.12 · 08:00 · חלון 3" — the phone hugged to his cheek, eyes closed, hush + heartbeat.
Break (reversal_of_help): next morning 2.12 08:00, the empty lobby, window 3 dark, a sign with her photo and a little
speaker: "אני בחופש, מותק." — she found him her own window on the day she is away. Frozen face; whip into the cold open.
Experiment (follows): part_label — "חלק 5 מתוך 5" pill in frame 0 (and the first caption line).
No music (voiced rule): voices + SFX + lobby room tone. Serial pills "פרק 43" + live ticket number (hud.stage_of, §O4).

  python3 voice/ep43_prep.py
  python3 ep43.py times | test t1 t2 ... | render   -> out/ep43_april.mp4
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
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep43', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 70, 150)
SHARIT_SUB = (255, 182, 210)
QUEUE = int(os.environ.get('QUEUE', '438'))
EP_LABEL = 'פרק 43'
PART_LABEL = 'חלק 5 מתוך 5'
OUTNAME = os.environ.get('OUTNAME', 'ep43_april')
LIMIT = float(os.environ.get('LIMIT', '0'))
VAC = 'בחופשה מ-2.12 עד 4.12'

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
COLD_END = round(D[0] + 0.40, 2)            # cold open = 4300 "ינואר! תרענן! תרענן!" (the loudest climb line)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "משרד הפנים. התור הכי קרוב: אפריל." — the ID card (valid until 3.12)
FF = (L[1] + D[1] + 0.10, L[1] + D[1] + 1.20)   # x64: refresh, refresh, refresh — אפריל, אפריל, אפריל
CHAT = FF[1] + 0.02                         # the chat window pops up: Sharit's avatar (the plant again in the header)
L[2] = CHAT + 0.25                          # Sharit (chat): "תרענן, מותק."
L[27] = L[2] + D[2] + 0.10                  # he looks up from the phone: she is right there behind the glass — "שרית?! גם פה?"
REF1 = L[27] + D[27] + 0.08                 # refresh → פברואר
CHK1 = REF1 + 0.30
L[3] = CHK1 + 0.12                          # "פברואר! ינואר!"
CHK2 = L[3] + ss(3, 1) - 0.02               # ינואר lands on the second word
L['0b'] = L[3] + D[3] + 0.08                # "ינואר! תרענן! תרענן!" in context (= the cold open)
L[4] = L['0b'] + D[0] + 0.10                # Sharit: "מחר, חלון שלוש. רק בשבילך, חמוד."
CHK3 = L[4] + ss(4, 1) - 0.05; GOLDT = CHK3 + 0.05
L[103] = L[4] + D[4] + 0.08                 # "יש!!!"
BOOK = L[103] + D[103] + 0.05               # taps "קבע תור" → confirmation
HOLD = (BOOK + 0.30, BOOK + 0.80)           # the peak: the phone hugged to his cheek, eyes closed
BREAK = HOLD[1]                             # cut: next morning
L[5] = BREAK + 0.40                         # her recorded voice on the sign: "אני בחופש, מותק."
FREEZE = L[5] + D[5]
DUR = round(FREEZE + 0.42, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (27, L[27]), (3, L[3]), (0, L['0b']), (4, L[4]), (103, L[103]), (5, L[5])]
SPEAKER = {0: 'cat', 1: 'cat', 27: 'cat', 3: 'cat', 103: 'cat', 2: 'sh', 4: 'sh', 5: 'rec'}

SUBS = {
    0: [['ינואר! תרענן! תרענן!']],
    1: [['משרד הפנים.'], ['התור הכי קרוב: אפריל.']],
    2: [['תרענן, מותק.']],
    27: [['שרית?! גם פה?']],
    3: [['פברואר! ינואר!']],
    4: [['מחר, חלון שלוש.'], ['רק בשבילך, חמוד.']],
    103: [['יש!!!']],
    5: [['אני בחופש, מותק.']],
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
        if li == 5: b = DUR - 0.25
        if li == 103: b = min(b, HOLD[0])
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('two', 0.0, COLD_END), ('rewind', COLD_END, T0), ('two', T0, BREAK), ('morning', BREAK, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['תור במשרד הפנים?', 'רק באפריל']          # keyword: משרד הפנים / תור (F16 pain question)
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

# ------------------------------------------------------------------ the site on his phone
def slot_of(t):
    s_t = story_t(t)
    if s_t >= CHK3: return 'מחר'
    if s_t >= CHK2: return 'ינואר'
    if s_t >= CHK1: return 'פברואר'
    return 'אפריל'

def refreshing(t):
    """the spinner: x64 taps, the refresh before February, and the frantic taps of the cold-open line"""
    s_t = story_t(t)
    if FF[0] <= s_t < FF[1]: return (s_t - FF[0]) % 0.3 < 0.16
    if REF1 <= s_t < CHK1: return True
    if L['0b'] <= s_t < L[4]: return (s_t - L['0b']) % 0.55 < 0.18
    return False

PW, PH = 400, 720
def phone_layer(slot, spin, chat, booked, talk=0):
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=(246, 246, 250))
    pd.rounded_rectangle([S(PW / 2 - 56), S(28), S(PW / 2 + 56), S(52)], radius=S(12), fill=(10, 10, 12))
    pd.rectangle([S(14), S(66), S(PW - 14), S(132)], fill=BLUE)
    pd.text((S(PW / 2), S(99)), 'זימון תור · משרד הפנים', font=font(S(28), 900), fill=WHITE, anchor='mm')
    if booked:
        E(pd, PW / 2, 250, 70, 70, fill=GREEN)
        pd.line([(S(PW / 2 - 34), S(250)), (S(PW / 2 - 8), S(278)), (S(PW / 2 + 36), S(222))], fill=WHITE, width=iw(14), joint='curve')
        pd.text((S(PW / 2), S(360)), 'התור נקבע!', font=font(S(48), 900), fill=INK, anchor='mm')
        pd.rounded_rectangle([S(40), S(410), S(PW - 40), S(560)], radius=S(22), fill=(232, 250, 238), outline=GREEN, width=iw(5))
        pd.text((S(PW / 2), S(452)), 'מחר · 2.12 · 08:00', font=font(S(36), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(512)), 'חלון 3', font=font(S(40), 900), fill=GREEN, anchor='mm')
        return lay
    pd.text((S(PW / 2), S(168)), 'חידוש תעודת זהות', font=font(S(28), 800), fill=(90, 92, 104), anchor='mm')
    pd.text((S(PW / 2), S(214)), 'התור הפנוי הקרוב:', font=font(S(30), 800), fill=INK, anchor='mm')
    good = slot in ('ינואר', 'מחר')
    col = GOLD if slot == 'מחר' else (GREEN if good else RED)
    pd.rounded_rectangle([S(50), S(248), S(PW - 50), S(388)], radius=S(26), fill=(255, 248, 220) if slot == 'מחר' else ((232, 250, 238) if good else (255, 236, 236)),
                         outline=col, width=iw(6))
    if spin:
        for k in range(8):
            a = math.radians(k * 45); r0, r1 = 26, 46
            pd.line([(S(PW / 2 + r0 * math.cos(a)), S(318 + r0 * math.sin(a))), (S(PW / 2 + r1 * math.cos(a)), S(318 + r1 * math.sin(a)))],
                    fill=(120 + 15 * k, 124 + 15 * k, 140 + 12 * k), width=iw(9))
    else:
        pd.text((S(PW / 2), S(318)), slot, font=font(S(86), 900), fill=(200, 140, 0) if slot == 'מחר' else col, anchor='mm')
    # the refresh button
    pd.rounded_rectangle([S(110), S(408), S(PW - 110), S(464)], radius=S(28), fill=BLUE)
    pd.text((S(PW / 2), S(436)), 'רענון', font=font(S(30), 900), fill=WHITE, anchor='mm')
    if chat:   # the chat panel: Sharit's avatar + the header (the plant again)
        pd.rounded_rectangle([S(26), S(484), S(PW - 26), S(PH - 30)], radius=S(26), fill=(232, 236, 248), outline=(150, 160, 190), width=iw(3))
        lay.alpha_composite(SH_AV[talk], (int(S(PW - 26 - 12)) - SH_AV[talk].width, int(S(494))))
        pd = ImageDraw.Draw(lay)
        pd.text((S(PW - 140), S(520)), 'שרית · חלון 3', font=font(S(26), 900), fill=INK, anchor='rm')
        pd.text((S(PW - 140), S(552)), VAC, font=font(S(20), 700), fill=(140, 140, 150), anchor='rm')
        pd.rounded_rectangle([S(44), S(590), S(PW - 44), S(660)], radius=S(20), fill=WHITE, outline=(190, 196, 214), width=iw(2))
        pd.text((S(PW / 2), S(625)), 'הנציגה מקלידה...' if talk else 'צ׳אט עם נציגה', font=font(S(24), 800), fill=(110, 114, 130), anchor='mm')
    return lay

_PHC = {}
def phone_at(t):
    s_t = story_t(t)
    booked = s_t >= BOOK and t >= COLD_END
    chat = s_t >= CHAT and not booked
    talk = 0
    if chat:
        sv = voice_v(t, 'sh'); talk = 2 if sv > 0.3 else (1 if sv > 0.1 else 0)
    key = (slot_of(t), refreshing(t), chat, booked, talk)
    if key not in _PHC:
        if len(_PHC) > 80: _PHC.clear()
        _PHC[key] = phone_layer(*key)
    return _PHC[key]

def id_layer():
    """his ID card: valid until 3.12 (the stake)"""
    w_, h_ = 330, 236
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, S(w_) - 1, S(h_) - 1], radius=S(18), fill=(214, 230, 246), outline=(70, 90, 130), width=iw(4))
    d.rectangle([S(0), S(0), S(w_), S(46)], fill=BLUE)
    d.text((S(w_ / 2), S(24)), 'תעודת זהות', font=font(S(28), 900), fill=WHITE, anchor='mm')
    d.rounded_rectangle([S(w_ - 116), S(62), S(w_ - 22), S(170)], radius=S(10), fill=(255, 196, 120), outline=(120, 90, 60), width=iw(3))
    E(d, w_ - 69, 104, 26, 24, fill=FUR, outline=OUT, width=3)
    for k in range(2): d.rounded_rectangle([S(26), S(72 + k * 28), S(w_ - 140), S(86 + k * 28)], radius=S(5), fill=(170, 186, 210))
    d.text((S(w_ / 2), S(206)), 'בתוקף עד: 3.12', font=font(S(32), 900), fill=RED, anchor='mm')
    return lay

def sign_layer(night=False):
    """the paper on window 3's glass (the plant): name + grey vacation dates"""
    w_, h_ = 340, 124
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(w_) - 1, S(h_) - 1], fill=(252, 252, 246), outline=(170, 170, 160), width=iw(3))
    for x in (30, w_ - 30): d.rectangle([S(x - 22), S(-6), S(x + 22), S(10)], fill=(230, 220, 160, 200))
    d.text((S(w_ / 2), S(42)), 'שרית · חלון 3', font=font(S(36), 900), fill=INK, anchor='mm')
    d.text((S(w_ / 2), S(90)), VAC, font=font(S(25), 700), fill=(150, 150, 158), anchor='mm')
    return lay

def away_layer():
    """the next morning: the sign on the dark window — her photo + "אני בחופש, מותק." + the little speaker"""
    w_, h_ = 420, 520
    lay = Image.new('RGBA', (S(w_), S(h_)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, S(w_) - 1, S(h_) - 1], fill=(252, 252, 246), outline=(160, 160, 150), width=iw(4))
    for x in (40, w_ - 40): d.rectangle([S(x - 28), S(-8), S(x + 28), S(14)], fill=(230, 220, 160, 220))
    d.rounded_rectangle([S(110), S(40), S(w_ - 110), S(270)], radius=S(16), fill=(255, 224, 236), outline=(200, 140, 170), width=iw(3))
    lay.alpha_composite(SH_AV_BIG, (int(S(w_ / 2)) - SH_AV_BIG.width // 2, int(S(52))))
    d = ImageDraw.Draw(lay)
    d.text((S(w_ / 2), S(316)), 'אני בחופש,', font=font(S(54), 900), fill=INK, anchor='mm')
    d.text((S(w_ / 2), S(378)), 'מותק.', font=font(S(54), 900), fill=INK, anchor='mm')
    d.text((S(w_ / 2), S(436)), VAC, font=font(S(30), 800), fill=RED, anchor='mm')
    E(d, w_ / 2, 486, 18, 18, fill=(40, 40, 46))
    return lay

def paste_rot(img, lay, c, ang=0.0, sc=1.0, a=100):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    V1.shadow_paste(img, lay, c, a, (14, 18), 10)

burst = E18.burst

# ------------------------------------------------------------------ the set: the משרד הפנים lobby, window 3 behind glass
BOARD_C = (300, 470)
WIN = (0, 600, 610, 1590)      # window 3 glass (x0, y0, x1, y1)
SIGN_C = (420, 700)
def build_lobby_bg(morning=False):
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        v = y / H
        c0 = (int(lerp(226, 206, v)), int(lerp(234, 216, v)), int(lerp(244, 226, v)))
        if morning: c0 = tuple(int(x * 0.86) for x in c0)
        d.rectangle([0, S(y), W * K, S(y + 8)], fill=c0)
    d.rectangle([0, S(1180), W * K, S(1210)], fill=BLUE)                              # ministry stripe
    # the LED board over window 3
    d.rounded_rectangle([S(BOARD_C[0] - 210), S(BOARD_C[1] - 90), S(BOARD_C[0] + 210), S(BOARD_C[1] + 90)], radius=S(16), fill=(22, 22, 26), outline=(92, 92, 104), width=iw(6))
    d.text((S(BOARD_C[0] + 140), S(BOARD_C[1])), 'חלון 3', font=font(S(36), 900), fill=E3.AMBER, anchor='mm')
    # the ministry plaque + the door rule on the right wall
    x0, y0, x1, y1 = 660, 360, 1050, 600
    d.rounded_rectangle([S(x0 + 8), S(y0 + 10), S(x1 + 8), S(y1 + 10)], radius=S(14), fill=(160, 168, 184))
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(14), fill=(252, 250, 246), outline=(120, 120, 130), width=iw(5))
    d.rectangle([S(x0), S(y0), S(x1), S(y0 + 84)], fill=BLUE)
    d.text((S((x0 + x1) / 2), S(y0 + 44)), 'משרד הפנים', font=font(S(50), 900), fill=WHITE, anchor='mm')
    d.text((S((x0 + x1) / 2), S(y0 + 132)), 'קבלת קהל', font=font(S(38), 900), fill=INK, anchor='mm')
    d.text((S((x0 + x1) / 2), S(y0 + 186)), 'בזימון תור בלבד', font=font(S(38), 900), fill=RED, anchor='mm')
    img = img.filter(ImageFilter.GaussianBlur(S(1.4)))
    return img

def glass(img, dark=False):
    """window 3's glass + frame, drawn over whoever sits behind it"""
    x0, y0, x1, y1 = WIN
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=(20, 24, 40, 225) if dark else (200, 226, 246, 46))
    if not dark:
        for k in range(3):
            xa = 120 + k * 160
            poly(od, [(xa, y0 + 20), (xa + 50, y0 + 20), (xa - 160, y1 - 60), (xa - 210, y1 - 60)], fill=(255, 255, 255, 30))
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    d.rectangle([S(x0 - 20), S(y0 - 16), S(x1 + 16), S(y0 + 6)], fill=(170, 176, 190))
    d.rectangle([S(x1 - 6), S(y0 - 16), S(x1 + 16), S(y1)], fill=(170, 176, 190))
    d.rounded_rectangle([S(x0 + 140), S(y1 - 70), S(x1 - 150), S(y1 - 40)], radius=S(12), fill=(60, 62, 72))   # the slot under the glass

T_HEAD = (240, 960); TS = 1.30
HX2, HY2, F2 = 820, 960, 1.46
QUEUE_TWO = [('c2', 700, 760, 0.40, 0.4), ('h0', 1000, 720, 0.38, 1.6)]
ID_C = (300, 1250)

def cat_state(t):
    st = E3.base_state(); st.update(red=0.9, cobweb=1.0, blush=0.4)
    rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    s_t = story_t(t)
    if L['0b'] <= s_t < L[4]:               # "ינואר! תרענן! תרענן!" — frantic hope, jabbing the screen
        u = s_t - L['0b']
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(s_t, rest='smile', loud='w'), ear_dy=-30, blush=1.0, look=(-26, 18))
        rot = 5 * math.sin(u * 11); dy = -16 * voice_v(s_t, 'cat') - 8 * abs(math.sin(u * 9))
    elif t < FF[0]:                         # the want: the ID card, April — despair
        st.update(lid=0.0, pupil='tiny', brow='sad', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-14, look=(-24, 14), sweat=0.8, blush=0.0)
        rot = 3 * math.sin(t * 5); dy = -12 * v
    elif t < CHAT:                          # x64: refresh, refresh — deflating
        u = (t - FF[0]) / (FF[1] - FF[0])
        st.update(lid=0.3 + 0.35 * u, pupil='normal', brow='annoyed', mouth='flat', look=(-24, 18), ear_droop=0.6 * u)
        dy = 8 * u
    elif t < L[27]:                         # the chat pops: "תרענן, מותק."
        u = t - CHAT
        st.update(lid=0.1, pupil='big', brow='up', mouth='w', look=(-26, 18), ear_dy=-16 * math.exp(-u * 3), blush=0.3)
    elif t < REF1:                          # "שרית?! גם פה?" — looks up: she is right there behind the glass
        u = t - L[27]
        st.update(lid=0.0, pupil='tiny', brow='up', ear_dy=-26 * math.exp(-max(0, u) * 2), mouth=cat_mouth(t, rest='w', loud='w'), sweat=1.0, look=(-40, -6))
        rot = 8 * math.sin(u * 20) * math.exp(-u * 3); dy = -30 * math.exp(-u * 5)
    elif t < L['0b']:                       # פברואר ✓ … "פברואר! ינואר!"
        u = t - REF1
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile_small', loud='w'), ear_dy=-22, blush=0.8, look=(-26, 18))
        dy = -10 * v - (14 * math.exp(-(t - CHK1) * 6) if t >= CHK1 else 0)
    elif t < L[103]:                        # "מחר, חלון שלוש. רק בשבילך, חמוד." — melting with love for Sharit
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', look=(-40, -4), ear_dy=-24, blush=1.0)
        if t >= CHK3: st.update(mouth='smile')
    elif t < HOLD[0]:                       # "יש!!!" + the tap: booked
        u = t - L[103]
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile', loud='w'), ear_dy=-28 * math.exp(-u * 2), blush=1.0, look=(-10, 0))
        dy = -24 * abs(math.sin(u * 9)) * math.exp(-u * 1.0)
    elif t < BREAK:                         # THE PEAK: the phone hugged to his cheek, eyes closed
        st.update(eye_mode='closed', mouth='smile', ear_dy=-14, blush=1.0, look=(0, 0)); rot = -6; dy = 6
    else:                                   # next morning: the dark window — frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none' if t < L[5] + 0.4 else 'up', mouth='flat' if t < L[5] + 0.5 else 'w', ear_dy=-24 * math.exp(-u * 4),
                  look=(-40, -4), twitch=(t >= L[5] + 0.5 and int(t * 12) % 2 == 0), sweat=clamp(u / 0.8), blush=0.0)
        dy = -8
    return st, rot, dy

def sh_state(t):
    s_t = story_t(t)
    st = SH.base(); st.update(hand_l=(170, 760), hand_r=(540, 730), lid=0.55, red=0.8, blush=0.6, look=(22, 14), finger=True)
    talk = voice_v(t, 'sh') > 0.12
    st['mouth'] = 'talk' if talk else ('munch' if int(t * 7) % 2 and s_t < CHAT else 'lazy')
    tap = int(t * 6) % 2 == 0
    st['hand_r'] = (540, 712 if tap else 736)                                         # one-finger typing (she IS the chat)
    if s_t < CHAT: st.update(snack=True, lid=0.65, look=(20, 18))
    elif L[27] <= s_t < REF1: st.update(look=(34, 0), lid=0.4, mouth='grin' if not talk else 'talk', hand_r=(560, 640), finger=False)   # little wave
    elif L[4] <= s_t < BOOK: st.update(look=(32, 2), lid=0.45, blush=0.9)
    return st

def scene_two(t, i):
    img = BG.copy()
    s_t = story_t(t)
    E3.led_text(img, str(QUEUE), BOARD_C[0] - 60, BOARD_C[1] + 4, 96)
    cheer = GOLDT <= s_t < BREAK
    for name, x, y, sc, ph in QUEUE_TWO:
        jump = (-18 * abs(math.sin(t * 9 + ph))) if cheer else 0
        E13.paste_sprite(img, name, 1 if cheer else 2, x + 5 * math.sin(t * 3 + ph), y + 8 * math.sin(t * 4.4 + ph) + jump, sc, flip=x > 640)
    Ls = SH.draw(sh_state(t), i)
    Ls = Ls.resize((int(Ls.width * TS), int(Ls.height * TS)), Image.BICUBIC)
    img.alpha_composite(Ls, dest=(int(S(T_HEAD[0] - 350 * TS)), int(S(T_HEAD[1] - 300 * TS))))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1300), S(620), S(1360)], radius=S(8), fill=(120, 122, 134))   # her desk edge
    glass(img)
    paste_rot(img, SIGN, SIGN_C, 3, 1.0, 50)
    d = ImageDraw.Draw(img)
    st, rot, dy = cat_state(t)
    E(d, HX2, 1730, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1780, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    # counter in front
    d.rounded_rectangle([S(-20), S(1590), S(1100), S(1730)], radius=S(16), fill=(120, 122, 134), outline=(60, 62, 72), width=iw(6))
    d.rectangle([S(-20), S(1590), S(1100), S(1616)], fill=(160, 162, 176))
    want = T0 <= s_t < FF[0] and t >= T0
    peak = s_t >= BOOK and t >= COLD_END
    if want:                                                   # the ID card held up next to the phone
        ic = (ID_C[0] + 8 * math.sin(t * 6), ID_C[1] + 10 * math.sin(t * 8))
        capsule(d, (HX2 - 120, 1560), (ic[0] + 140, ic[1] + 70), 96, FUR, OUT, 4)
        paste_rot(img, IDL, ic, 8 + 4 * math.sin(t * 5), 1.0, 90)
        d = ImageDraw.Draw(img); E12.big_paw(d, (ic[0] + 140, ic[1] + 70), 30, 0.7)
    else:
        paste_rot(img, IDL, (960, 1660), -6, 0.6, 70)                                   # on the counter
    # the phone in his paw
    if peak and t < BREAK:
        u = s_t - BOOK
        k = ease_out(clamp((u - 0.15) / 0.25))
        pc = lerp2((600, 1250), (640, 1050), k); ang = lerp(6, -16, k); sc = lerp(0.66, 0.56, k)
    else:
        pc = (590, 1260 + 6 * math.sin(t * 7)); ang = 6; sc = 0.66
        if L['0b'] <= s_t < L[4]: pc = (590 + 8 * math.sin(t * 30), 1260 - 10 * abs(math.sin(t * 9)))
    grip = (pc[0] + 120, pc[1] + 170)
    capsule(d, (HX2 - 170, 1560), grip, 100, FUR, OUT, 4)
    paste_rot(img, phone_at(t), pc, ang, sc)
    d = ImageDraw.Draw(img)
    E12.big_paw(d, grip, -20, 0.8)
    if refreshing(t) or (CHK1 - 0.3 <= s_t < CHK1):                                     # the other paw jabs "רענון"
        tp = (pc[0] + 10, pc[1] + 80 * sc)
        capsule(d, (HX2 + 170, 1560), (tp[0] + 60, tp[1] + 40), 90, FUR, OUT, 4); E12.big_paw(d, (tp[0] + 40, tp[1] + 30), 20, 0.6)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= s_t < c_ + 0.5: burst(img, (pc[0], pc[1] - 60), s_t - c_, (120, 255, 160) if c_ != CHK3 else (255, 220, 120), 170, 10, 0.4)
    if cheer: E18.confetti(img, s_t - GOLDT + 0.3)
    return img

def scene_morning(t, i):
    """2.12, 08:00: the empty lobby, window 3 dark, her sign"""
    img = BGM.copy()
    E3.led_text(img, '--', BOARD_C[0] - 60, BOARD_C[1] + 4, 96)
    glass(img, dark=True)
    u = t - BREAK
    paste_rot(img, AWAY, (300, 1000), -3, 1.0, 80)
    d = ImageDraw.Draw(img)
    if L[5] <= t < L[5] + D[5]:                                # the little speaker pulses with her recorded voice
        v = voice_v(t, 'rec')
        for k in range(3):
            r = 24 + 16 * k + 14 * v
            d.arc([S(300 - r), S(1235 - r), S(300 + r), S(1235 + r)], -50, 50, fill=(80, 80, 90), width=iw(4))
            d.arc([S(300 - r), S(1235 - r), S(300 + r), S(1235 + r)], 130, 230, fill=(80, 80, 90), width=iw(4))
    st, rot, dy = cat_state(t)
    E(d, HX2, 1730, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1780, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(-20), S(1590), S(1100), S(1730)], radius=S(16), fill=(120, 122, 134), outline=(60, 62, 72), width=iw(6))
    d.rectangle([S(-20), S(1590), S(1100), S(1616)], fill=(160, 162, 176))
    pc = (660, 1290 + 4 * math.sin(t * 6)); grip = (pc[0] + 110, pc[1] + 150)
    capsule(d, (HX2 - 170, 1560), grip, 100, FUR, OUT, 4)
    paste_rot(img, PHONE_BOOKED, pc, 8, 0.52)
    d = ImageDraw.Draw(img); E12.big_paw(d, grip, -20, 0.8)
    return img

# ------------------------------------------------------------------ overlays
CHIPS = [('פברואר', 820, CHK1), ('ינואר', 540, CHK2), ('מחר', 260, CHK3)]
def chips(frame, t, y=330):
    if t < T0 + 0.2 or t >= BREAK: return
    gold = t >= GOLDT
    d = ImageDraw.Draw(frame)
    for lab, cx, tk in CHIPS:
        ok = t >= tk
        fill = GOLD if gold else ((255, 255, 255) if ok else (40, 42, 52))
        ink = INK if (ok or gold) else (190, 194, 206)
        u = t - tk
        sc = 1 + 0.35 * math.exp(-u * 10) * math.cos(u * 22) if (0 <= u < 0.5 and ok) else 1.0
        w, h = 230 * sc, 70 * sc
        d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], radius=h / 2, fill=fill, outline=(10, 10, 12), width=5)
        d.text((cx + 22 * sc, y), lab, font=font(int(36 * sc), 900), fill=ink, anchor='mm')
        bx = cx - w / 2 + 34 * sc
        if ok:
            d.ellipse([bx - 20 * sc, y - 20 * sc, bx + 20 * sc, y + 20 * sc], fill=GREEN if not gold else (30, 130, 60))
            d.line([(bx - 10 * sc, y), (bx - 3 * sc, y + 9 * sc), (bx + 11 * sc, y - 9 * sc)], fill=WHITE, width=int(6 * sc), joint='curve')
        else:
            d.ellipse([bx - 18 * sc, y - 18 * sc, bx + 18 * sc, y + 18 * sc], outline=ink, width=4)

def morning_card(frame, t):
    u = t - BREAK
    sc = 1 + 0.3 * math.exp(-u * 10) * math.cos(u * 22)
    d = ImageDraw.Draw(frame)
    lab = 'למחרת · 2.12 · 08:00'
    f = font(int(46 * sc), 900); tw = d.textlength(lab, font=f)
    d.rounded_rectangle([W / 2 - tw / 2 - 34, 330 - 42 * sc, W / 2 + tw / 2 + 34, 330 + 42 * sc], radius=int(42 * sc), fill=WHITE, outline=(10, 10, 12), width=5)
    d.text((W / 2, 330), lab, font=f, fill=INK, anchor='mm')

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

BG = BGM = SIGN = AWAY = IDL = PHONE_BOOKED = SH_AV = SH_AV_BIG = PILL_EP = PILL_Q = PILL_PART = None
def init_all():
    global BG, BGM, SIGN, AWAY, IDL, PHONE_BOOKED, SH_AV, SH_AV_BIG, PILL_EP, PILL_Q, PILL_PART
    m.init_static(); E3.init_all()
    E13.build_crowd()
    BG = build_lobby_bg(); BGM = build_lobby_bg(morning=True)
    SH_AV = []
    for mo in ('lazy', 'talk', 'grin'):     # Sharit's chat avatar, 3 mouth states (head crop)
        st = SH.base(); st.update(mouth=mo, lid=0.6, look=(0, 6), snack=False)
        lay = SH.draw(st, 3 if mo == 'talk' else 0).crop((S(130), S(110), S(570), S(500)))
        SH_AV.append(lay.resize((S(100), int(S(100) * lay.height / lay.width)), Image.LANCZOS))
    st = SH.base(); st.update(mouth='grin', lid=0.6, look=(0, 6), blush=0.8)
    lay = SH.draw(st, 0).crop((S(110), S(90), S(590), S(520)))
    SH_AV_BIG = lay.resize((S(190), int(S(190) * lay.height / lay.width)), Image.LANCZOS)
    SIGN = sign_layer(); AWAY = away_layer(); IDL = id_layer()
    PHONE_BOOKED = phone_layer('מחר', False, False, True)
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_PART = HUD._pill(PART_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'two':
        z, cx, cy = 1.05 + 0.01 * pu, 540, 1000
        if a == 0.0:                                   # cold open: low and tight, the phone jabbed at the lens, her sign over his shoulder
            z, cx, cy = 1.30 + 0.03 * t, 600, 1010
            if t < 0.3: z = 1.50 - 0.20 * ease_out(t / 0.3)
        elif t < FF[0]: z, cx, cy = 1.16, 560, 1120   # the want: the ID card + April
        elif t < CHAT: z, cx, cy = 1.0, 540, 960       # x64 wide
        elif t < L[27]: z, cx, cy = 1.30, 600, 1220    # the chat on the phone (the plant in the header)
        elif t < REF1: z, cx, cy = 1.06, 480, 980      # "גם פה?": the glass, Sharit waving
        elif L['0b'] <= t < L[4]: z, cx, cy = 1.30, 600, 1010
        elif L[4] <= t < L[103]: z, cx, cy = 1.10, 500, 1040
        if HOLD[0] - 0.3 <= t < BREAK:
            k = ease_io(clamp((t - (HOLD[0] - 0.3)) / (BREAK - HOLD[0] + 0.3))); z, cx, cy = 1.12 + 0.16 * k, lerp(540, 700, k), lerp(1040, 1020, k)
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1000
    elif name == 'morning':
        z, cx, cy = 1.04 + 0.02 * pu, 540, 1000
    elif name == 'frozen':
        z, cx, cy = 1.30 + 0.03 * pu, 640, 1060
    return z, cx, cy

def draw_frame(i):
    t = i / FPS
    name, a, b = shot(t)
    if name == 'rewind':
        u = (t - a) / (b - a)
        img = scene_two(lerp(L['0b'] - 0.4, T0 + 0.3, ease_in(u)), i)
    elif name in ('morning', 'frozen'): img = scene_morning(t, i)
    else: img = scene_two(t, i)
    z, ccx, ccy = camera(t)
    shake = 0.0
    if t < 0.5: shake = 16 * math.exp(-t * 5)
    for s_ in (CHK3, BREAK):
        if 0 <= t - s_ < 0.3: shake = 12 * math.exp(-(t - s_) * 8)
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if t < COLD_END: frame = frame.rotate(3, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(200, 210, 226, 255))
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(50 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if FF[0] <= t < FF[1]: ff_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if t >= DUR - 0.25:
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    if name in ('two', 'rewind'): chips(frame, t)
    if name in ('morning', 'frozen') and t < DUR - 0.25: morning_card(frame, t)
    for t0, t1, lines in TOPCAPS:
        if t0 <= t < t1: m.paste_center(frame, m.caption_layer(lines, 96, WHITE), W / 2, 270)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            col = SHARIT_SUB if SPEAKER[li] in ('sh', 'rec') else WHITE
            m.paste_center(frame, sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < FF[0]) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_PART, (40 + PILL_EP.width + 10, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + lobby room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(43)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'rec': y = m.phone_line(y) * 1.6                     # the little speaker on the sign
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
    def tap(t0, g=0.25): add(sfx, m.highpass(nz(0.02), 2500) * np.exp(-tt_(0.02) * 150), t0, g)
    def pop(t0, g=0.16): add(sfx, m.tone(1568.0, 0.12, harm=((1, 1),), decay=18), t0, g)
    def cheer(t0, ln=1.0, g=0.10):
        tt = tt_(ln); add(sfx, m.bandpass(nz(ln), 500, 3500) * np.sin(np.pi * tt / ln) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)), t0, g)
    def keys(t0, t1, g=0.05):
        tc = t0
        while tc < t1: add(sfx, m.highpass(nz(0.015), 3000) * np.exp(-tt_(0.015) * 200), tc, g); tc += 0.17
    add(sfx, thud(0.7), 0.0)
    for k in range(4): tap(0.25 + 0.55 * k, 0.2)                                           # the frantic refresh taps of the cold open
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.bandpass(nz(BREAK), 150, 900) * 0.6, 0.0, 0.012)                             # lobby room tone
    add(sfx, m.bandpass(nz(DUR - BREAK), 120, 500) * 0.6, BREAK, 0.006)                     # the empty morning lobby
    add(sfx, m.bandpass(nz(0.4), 600, 5000) * np.linspace(0, 1, int(0.4 * SR)), FF[0] - 0.3, 0.06)
    tc = FF[0]
    while tc < FF[1]:
        tap(tc, 0.12); tc += 0.3
    pop(CHAT, 0.18); keys(CHAT, L[27], 0.04)
    keys(L[4], L[103], 0.04)
    tap(REF1, 0.25); check(CHK1, 0.15); check(CHK2, 0.16)
    for k in range(3): tap(L['0b'] + 0.55 * k, 0.2)
    check(CHK3, 0.2, True); cheer(GOLDT + 0.1, BOOK - GOLDT, 0.08)
    tap(BOOK, 0.3); add(sfx, m.tone(1046.5, 0.5, harm=((1, 1), (2.76, 0.2)), decay=5), BOOK + 0.05, 0.12)
    heartbeat(HOLD[0] + 0.04); heartbeat(HOLD[0] + 0.30, 0.5)
    add(sfx, thud(0.6), BREAK); whoosh(BREAK, 0.08, 0.2)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), L[5] + D[5] - 0.2, 0.14)
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
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', T0, 'FF', [round(x, 2) for x in FF], 'CHAT', round(CHAT, 2))
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'BOOK', round(BOOK, 2), 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, 'ep43_contact.png')); print('ok'); return
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
