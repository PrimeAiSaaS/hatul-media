#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 41: המייל נפל (season 9 "הקו פנוי" ep3, VOICED, built 25.11 under §P, ~21.5 s).
Voices = voice bank 2026-11-19 lines 4100–4105 (Gabi's picks: 4100 B, 4102 C, 4104 D) + stock 9105 "לא. לא. לא...",
prepared by voice/ep41_prep.py. Built after ep42/ep43 because 4102/4104 waited for the pronunciation picks (25.11 13:38).
Set (fresh, lesson freshset: 40 living room, 42 dark kitchen, 43 the ministry lobby): an outdoor street café, daytime,
stone wall + awning behind, a paper coffee cup on the round table in front. Sharit is only the online chat on his phone.
Want: the משרד הפנים approval, "יישלח למייל".
Plant: the phone's notification strip "האחסון שלך מלא · 99%" at the top of the screen — in the cold open (the phone raised
overhead), and again flashing while the photo uploads. Never pointed at.
Climb (3 chips): טופס ✓ ("טופס. מולא.") → תמונה ✓ (a selfie with flash, the upload bar; the 99% strip flashes,
"תמונה. עלתה.") → אישור ✓ gold (Sharit on the chat: "הבקשה אושרה, מותק. בדוק את המייל.", confetti, "אושר! אני מאושר!").
Peak: he opens the mail app — "פותח... פותח..." — the spinner, the held breath + heartbeat.
Break (win_is_loss): "תיבת הדואר מלאה · ההודעה נדחתה" — and to reset: "לאיפוס, נשלח קוד למייל". "לא. לא. לא..."
Frozen face; whip into the cold open.
Clock (Gabi 22.11, §I 2026-11-22): the site's session timer "החיבור יתנתק בעוד 00:SS" counts real seconds from frame 0
(the cold open shows the in-context value), keeps ticking through the confetti and the spinner and hits 00:00 on the
break frame; the red 00:00 stays through the frozen face.
Experiment (follows): part_label — "חלק 3 מתוך 5" pill in frame 0 (and the first caption line), same arm as 39–43.
No music (voiced rule): voices + SFX + street room tone. Serial pills "פרק 41" + live ticket number (hud.stage_of, §O4).

  python3 voice/ep41_prep.py
  python3 ep41.py times | test t1 t2 ... | render   -> out/ep41_mail.mp4
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
from make_video import (W, H, K, FPS, S, iw, E, poly, line, capsule, lerp, lerp2, clamp,
                        ease_io, ease_out, ease_in, font, FUR, OUT, CREAM, WHITE, INK)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep41', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {k: v['dur'] for k, v in META.items()}
YELLOW = (255, 221, 51); GOLD = (255, 196, 40); GREEN = (40, 170, 80); RED = (214, 44, 52); BLUE = (28, 70, 150)
ORANGE = (240, 128, 20)
SHARIT_SUB = (255, 182, 210)
QUEUE = int(os.environ.get('QUEUE', '434'))
EP_LABEL = 'פרק 41'
PART_LABEL = 'חלק 3 מתוך 5'
OUTNAME = os.environ.get('OUTNAME', 'ep41_mail')
LIMIT = float(os.environ.get('LIMIT', '0'))
PLANT = 'האחסון שלך מלא · 99%'

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
COLD_END = round(D[0] + 0.40, 2)            # cold open = 4100 "אושר! אני מאושר!" (the loudest climb line)
RW = (COLD_END, COLD_END + 0.28)
T0 = RW[1]
L = {}
L[1] = T0 + 0.05                            # want: "משרד הפנים: האישור יישלח למייל."
FF = (L[1] + D[1] + 0.10, L[1] + D[1] + 1.50)   # x64: the form fills itself — שם, מספר זהות, כתובת
L[2] = FF[1] + 0.05                         # "טופס. מולא."
CHK1 = L[2] + ss(2, 1) - 0.03
CAM = L[2] + D[2] + 0.10                    # selfie: he holds the phone out, big grin
SNAP = CAM + 0.70                           # the flash
UP = (SNAP + 0.25, SNAP + 1.40)             # upload bar 0 -> 100 (the 99% strip flashes = the plant again)
L[3] = UP[1] - 0.25                         # "תמונה. עלתה."
CHK2 = L[3] + ss(3, 1) - 0.03
SEND = (L[3] + D[3] + 0.08, L[3] + D[3] + 0.78)   # "שולח בקשה..." spinner
CHAT = SEND[1]                              # the chat pops: Sharit's avatar
L[4] = CHAT + 0.25                          # Sharit (chat): "הבקשה אושרה, מותק. בדוק את המייל."
CHK3 = L[4] + ss(4, 0) + 0.55; GOLDT = CHK3 + 0.05   # gold on "אושרה"
L['0b'] = L[4] + D[4] + 0.40                # "אושר! אני מאושר!" in context (= the cold open)
MAIL = L['0b'] + D[0] + 0.08                # taps the mail app
L[5] = MAIL + 0.10                          # "פותח... פותח..." — the spinner
HOLD = (L[5] + D[5] + 0.04, L[5] + D[5] + 0.62)   # the peak held: breath held, heartbeat
BREAK = HOLD[1]                             # "תיבת הדואר מלאה · ההודעה נדחתה" (the clock hits 00:00 here)
RESET = BREAK + 0.55                        # "לאיפוס, נשלח קוד למייל"
L[105] = BREAK + 0.45                       # "לא. לא. לא..."
FREEZE = L[105] + D[105]
DUR = round(FREEZE + 0.42, 2)
NF = int(round((LIMIT or DUR) * FPS))
OCC = [(0, 0.0), (1, L[1]), (2, L[2]), (3, L[3]), (4, L[4]), (0, L['0b']), (5, L[5]), (105, L[105])]
SPEAKER = {0: 'cat', 1: 'cat', 2: 'cat', 3: 'cat', 5: 'cat', 105: 'cat', 4: 'sh'}

SUBS = {
    0: [['אושר! אני מאושר!']],
    1: [['משרד הפנים:'], ['האישור יישלח למייל.']],
    2: [['טופס. מולא.']],
    3: [['תמונה. עלתה.']],
    4: [['הבקשה אושרה, מותק.'], ['בדוק את המייל.']],
    5: [['פותח... פותח...']],
    105: [['לא. לא. לא...']],
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
        if li == 105: b = DUR - 0.25
        if li == 5: b = min(b, HOLD[0])
        SUB_TIMES.append((a, b, c, li))

SHOTS = [('two', 0.0, COLD_END), ('rewind', COLD_END, T0), ('two', T0, BREAK), ('break', BREAK, FREEZE), ('frozen', FREEZE, DUR + 1)]
HOOK = ['האישור נשלח למייל?', 'איזה מייל?']        # keyword: מייל / אישור (F16 pain question)
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

def cat_mouth(t, rest='w', loud='smile'):
    v = voice_v(t, 'cat')
    if v > 0.32: return loud
    if v > 0.12: return 'smile_small'
    return rest

# ------------------------------------------------------------------ the phone
def screen_mode(t):
    s_t = story_t(t)
    if s_t >= RESET and t >= COLD_END: return 'reset'
    if s_t >= BREAK and t >= COLD_END: return 'full'
    if s_t >= MAIL and t >= COLD_END: return 'mail'
    if s_t >= CHAT: return 'chat'
    if s_t >= SEND[0]: return 'send'
    if s_t >= SNAP + 0.25: return 'upload'
    if s_t >= CAM: return 'camera'
    if s_t >= FF[0]: return 'form'
    return 'site'

def form_k(t):
    return clamp((story_t(t) - FF[0]) / (FF[1] - FF[0]))

def up_k(t):
    return clamp((story_t(t) - UP[0]) / (UP[1] - UP[0] - 0.1))

PW, PH = 400, 720
def strip(pd, flash=0.0):
    """the plant: the phone's notification strip at the top of the screen"""
    col = tuple(int(lerp(a, b, flash)) for a, b in zip((255, 236, 214), (255, 120, 60)))
    pd.rounded_rectangle([S(22), S(62), S(PW - 22), S(106)], radius=S(14), fill=col, outline=(200, 110, 40), width=iw(3))
    pd.text((S(PW / 2), S(84)), PLANT, font=font(S(25), 900), fill=(150, 60, 10) if flash < 0.5 else WHITE, anchor='mm')

def header(pd, title, col=BLUE):
    pd.rectangle([S(14), S(114), S(PW - 14), S(170)], fill=col)
    pd.text((S(PW / 2), S(142)), title, font=font(S(27), 900), fill=WHITE, anchor='mm')

def spinner(pd, cx, cy, ph=0, r0=24, r1=44):
    for k in range(8):
        a = math.radians(k * 45 + ph * 45); g = (k * 18) % 160
        pd.line([(S(cx + r0 * math.cos(a)), S(cy + r0 * math.sin(a))), (S(cx + r1 * math.cos(a)), S(cy + r1 * math.sin(a)))],
                fill=(90 + g, 94 + g, 110 + g // 2), width=iw(9))

def check_mark(pd, cx, cy, r, col=GREEN):
    E(pd, cx, cy, r, r, fill=col)
    pd.line([(S(cx - r * 0.48), S(cy)), (S(cx - r * 0.12), S(cy + r * 0.4)), (S(cx + r * 0.52), S(cy - r * 0.42))], fill=WHITE, width=iw(max(6, r * 0.2)), joint='curve')

def phone_layer(mode, k=0.0, spin=0, flash=0.0, talk=0, gold=False):
    lay = Image.new('RGBA', (S(PW), S(PH)), (0, 0, 0, 0)); pd = ImageDraw.Draw(lay)
    pd.rounded_rectangle([0, 0, S(PW) - 1, S(PH) - 1], radius=S(56), fill=(20, 20, 24))
    bg = (246, 246, 250)
    pd.rounded_rectangle([S(14), S(14), S(PW - 14), S(PH - 14)], radius=S(46), fill=bg)
    pd.rounded_rectangle([S(PW / 2 - 56), S(26), S(PW / 2 + 56), S(50)], radius=S(12), fill=(10, 10, 12))
    strip(pd, flash)
    if mode in ('mail', 'full', 'reset'):
        header(pd, 'דואר', (60, 64, 76))
        if mode == 'mail':
            pd.text((S(PW / 2), S(230)), 'תיבת הדואר הנכנס', font=font(S(28), 800), fill=(90, 92, 104), anchor='mm')
            spinner(pd, PW / 2, 360, spin, 34, 62)
            pd.text((S(PW / 2), S(470)), 'טוען...', font=font(S(34), 900), fill=INK, anchor='mm')
            for j in range(3): pd.rounded_rectangle([S(46), S(530 + j * 50), S(PW - 46), S(560 + j * 50)], radius=S(10), fill=(228, 230, 238))
            return lay
        pd.rounded_rectangle([S(30), S(196), S(PW - 30), S(430)], radius=S(24), fill=(255, 232, 232), outline=RED, width=iw(6))
        E(pd, PW / 2, 258, 40, 40, fill=RED)
        pd.text((S(PW / 2), S(260)), '!', font=font(S(56), 900), fill=WHITE, anchor='mm')
        pd.text((S(PW / 2), S(332)), 'תיבת הדואר מלאה', font=font(S(36), 900), fill=RED, anchor='mm')
        pd.text((S(PW / 2), S(384)), 'ההודעה נדחתה', font=font(S(34), 900), fill=INK, anchor='mm')
        if mode == 'reset':
            pd.rounded_rectangle([S(30), S(456), S(PW - 30), S(640)], radius=S(24), fill=WHITE, outline=(150, 156, 176), width=iw(4))
            pd.text((S(PW / 2), S(500)), 'פינוי מקום? צריך להתחבר.', font=font(S(25), 800), fill=(90, 92, 104), anchor='mm')
            pd.text((S(PW / 2), S(552)), 'לאיפוס, נשלח קוד', font=font(S(34), 900), fill=INK, anchor='mm')
            pd.text((S(PW / 2), S(600)), 'למייל', font=font(S(38), 900), fill=RED, anchor='mm')
        return lay
    header(pd, 'משרד הפנים · שירות מקוון')
    if mode == 'site':
        pd.text((S(PW / 2), S(214)), 'בקשה לאישור', font=font(S(34), 900), fill=INK, anchor='mm')
        for j, lab in enumerate(('1. טופס', '2. תמונה', '3. אישור')):
            y = 280 + j * 70
            pd.rounded_rectangle([S(60), S(y - 26), S(PW - 60), S(y + 26)], radius=S(14), fill=(232, 236, 248), outline=(170, 178, 204), width=iw(3))
            pd.text((S(PW - 84), S(y)), lab, font=font(S(30), 800), fill=INK, anchor='rm')
        pd.rounded_rectangle([S(36), S(510), S(PW - 36), S(620)], radius=S(20), fill=(255, 248, 220), outline=GOLD, width=iw(5))
        pd.text((S(PW / 2), S(546)), 'האישור יישלח', font=font(S(34), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(590)), 'למייל', font=font(S(38), 900), fill=BLUE, anchor='mm')
        return lay
    if mode == 'form':
        pd.text((S(PW / 2), S(212)), 'טופס בקשה', font=font(S(32), 900), fill=INK, anchor='mm')
        for j, (lab, val) in enumerate((('שם', 'חתול'), ('מספר זהות', '0 3 2 1 5 4 9 8 7'), ('כתובת', 'רחוב הסבלנות 3'))):
            y = 270 + j * 104
            done = k >= (j + 1) / 3
            fill_k = clamp(k * 3 - j)
            pd.text((S(PW - 56), S(y)), lab, font=font(S(24), 800), fill=(110, 114, 130), anchor='rm')
            pd.rounded_rectangle([S(50), S(y + 18), S(PW - 50), S(y + 70)], radius=S(12), fill=WHITE, outline=GREEN if done else (180, 186, 204), width=iw(3))
            txt = val[:max(0, int(round(len(val) * fill_k)))]
            if txt: pd.text((S(PW - 66), S(y + 44)), txt, font=font(S(26), 800), fill=INK, anchor='rm')
            if done: check_mark(pd, 80, y + 44, 16)
        pd.rounded_rectangle([S(110), S(600), S(PW - 110), S(656)], radius=S(28), fill=BLUE)
        pd.text((S(PW / 2), S(628)), 'המשך', font=font(S(30), 900), fill=WHITE, anchor='mm')
        return lay
    if mode == 'camera':
        pd.rectangle([S(14), S(176), S(PW - 14), S(PH - 110)], fill=(48, 52, 62))
        pd.ellipse([S(80), S(210), S(PW - 80), S(560)], outline=WHITE, width=iw(6))
        E(pd, PW / 2, 340, 70, 64, fill=FUR, outline=OUT, width=4)
        for sx in (-1, 1): poly(pd, [(PW / 2 + sx * 30, 290), (PW / 2 + sx * 62, 248), (PW / 2 + sx * 66, 306)], fill=FUR, outline=OUT, width=3)
        for sx in (-1, 1): E(pd, PW / 2 + sx * 24, 334, 9, 11, fill=INK)
        pd.arc([S(PW / 2 - 24), S(350), S(PW / 2 + 24), S(384)], 20, 160, fill=INK, width=iw(5))
        pd.text((S(PW / 2), S(590)), 'צילום תמונה לבקשה', font=font(S(26), 800), fill=WHITE, anchor='mm')
        E(pd, PW / 2, PH - 64, 34, 34, fill=WHITE, outline=(150, 150, 160), width=4)
        return lay
    if mode == 'upload':
        pd.text((S(PW / 2), S(220)), 'העלאת תמונה', font=font(S(32), 900), fill=INK, anchor='mm')
        pd.rounded_rectangle([S(130), S(260), S(PW - 130), S(420)], radius=S(14), fill=(255, 196, 120), outline=(120, 90, 60), width=iw(3))
        E(pd, PW / 2, 336, 46, 44, fill=FUR, outline=OUT, width=3)
        pd.rounded_rectangle([S(50), S(470), S(PW - 50), S(510)], radius=S(20), fill=(220, 224, 234))
        if k > 0.02: pd.rounded_rectangle([S(50), S(470), S(50 + (PW - 100) * k), S(510)], radius=S(20), fill=GREEN)
        if k >= 1:
            check_mark(pd, PW / 2, 590, 34)
            pd.text((S(PW / 2), S(650)), 'עלתה', font=font(S(30), 900), fill=GREEN, anchor='mm')
        else:
            pd.text((S(PW / 2), S(560)), f'מעלה... {int(k * 100)}%', font=font(S(30), 900), fill=INK, anchor='mm')
        return lay
    if mode == 'send':
        pd.text((S(PW / 2), S(240)), 'שליחת הבקשה', font=font(S(32), 900), fill=INK, anchor='mm')
        spinner(pd, PW / 2, 380, spin, 34, 62)
        pd.text((S(PW / 2), S(500)), 'שולח...', font=font(S(34), 900), fill=INK, anchor='mm')
        return lay
    # chat
    if gold:
        check_mark(pd, PW / 2, 236, 46, GREEN)
        pd.text((S(PW / 2), S(316)), 'הבקשה אושרה!', font=font(S(40), 900), fill=INK, anchor='mm')
        pd.text((S(PW / 2), S(362)), 'האישור נשלח למייל', font=font(S(28), 900), fill=BLUE, anchor='mm')
    else:
        spinner(pd, PW / 2, 260, spin, 26, 46)
        pd.text((S(PW / 2), S(340)), 'בבדיקה...', font=font(S(32), 900), fill=INK, anchor='mm')
    pd.rounded_rectangle([S(26), S(400), S(PW - 26), S(PH - 30)], radius=S(26), fill=(232, 236, 248), outline=(150, 160, 190), width=iw(3))
    lay.alpha_composite(SH_AV[talk], (int(S(PW - 26 - 12)) - SH_AV[talk].width, int(S(410))))
    pd = ImageDraw.Draw(lay)
    pd.text((S(PW - 140), S(440)), 'שרית', font=font(S(28), 900), fill=INK, anchor='rm')
    pd.text((S(PW - 140), S(472)), 'נציגה מקוונת', font=font(S(21), 700), fill=(140, 140, 150), anchor='rm')
    pd.rounded_rectangle([S(44), S(560), S(PW - 44), S(650)], radius=S(20), fill=WHITE, outline=(190, 196, 214), width=iw(2))
    pd.text((S(PW / 2), S(605)), 'הנציגה מקלידה...' if talk else ('בדוק את המייל, מותק' if gold else 'צ׳אט עם נציגה'), font=font(S(24), 800), fill=(110, 114, 130), anchor='mm')
    return lay

_PHC = {}
def phone_at(t):
    mode = screen_mode(t)
    s_t = story_t(t)
    k = 0.0; spin = 0; flash = 0.0; talk = 0; gold = False
    if mode == 'form': k = round(form_k(t) * 24) / 24
    if mode == 'upload':
        k = round(up_k(t) * 25) / 25
        flash = 1.0 if (int(s_t * 6) % 2 == 0 and k < 1) else 0.0            # the 99% strip flashes while uploading
    if mode in ('send', 'mail') or (mode == 'chat' and s_t < CHK3): spin = int(s_t * 12) % 8
    if mode == 'chat':
        sv = voice_v(t, 'sh'); talk = 2 if sv > 0.3 else (1 if sv > 0.1 else 0)
        gold = s_t >= CHK3
    key = (mode, k, spin, flash, talk, gold)
    if key not in _PHC:
        if len(_PHC) > 120: _PHC.clear()
        _PHC[key] = phone_layer(*key)
    return _PHC[key]

def paste_rot(img, lay, c, ang=0.0, sc=1.0, a=100):
    if abs(sc - 1) > 1e-3: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if abs(ang) > 1e-3: lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    V1.shadow_paste(img, lay, c, a, (14, 18), 10)

burst = E18.burst

# ------------------------------------------------------------------ the set: an outdoor street café, daytime
def build_street_bg():
    img = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    for y in range(0, 560, 8):                                   # sky
        v = y / 560
        d.rectangle([0, S(y), W * K, S(y + 8)], fill=(int(lerp(150, 206, v)), int(lerp(200, 228, v)), int(lerp(244, 246, v))))
    # stone wall (Jerusalem-stone blocks)
    d.rectangle([0, S(300), W * K, S(1330)], fill=(232, 214, 178))
    rng = random.Random(41)
    for row, y in enumerate(range(300, 1330, 70)):
        off = 0 if row % 2 == 0 else 90
        for x in range(-180 + off, W + 180, 180):
            c = tuple(int(v * rng.uniform(0.93, 1.03)) for v in (232, 214, 178))
            d.rectangle([S(x + 4), S(y + 4), S(x + 176), S(y + 66)], fill=c)
    d.rectangle([0, S(292), W * K, S(306)], fill=(200, 182, 148))
    # two windows with green shutters
    for wx in (150, 760):
        d.rectangle([S(wx), S(400), S(wx + 180), S(640)], fill=(70, 86, 104), outline=(170, 150, 120), width=iw(10))
        for sx in (-1, 1):
            x0 = wx - 70 if sx < 0 else wx + 180
            d.rectangle([S(x0), S(400), S(x0 + 70), S(640)], fill=(60, 128, 96), outline=(40, 90, 66), width=iw(4))
            for yy in range(418, 640, 22): d.line([(S(x0 + 6), S(yy)), (S(x0 + 64), S(yy))], fill=(44, 100, 74), width=iw(3))
        d.line([(S(wx + 90), S(400)), (S(wx + 90), S(640))], fill=(170, 150, 120), width=iw(6))
    # the café awning (red / white) + a generic "קפה" board
    for k in range(0, W + 120, 120):
        d.rectangle([S(k), S(760), S(k + 60), S(880)], fill=(206, 50, 56))
        d.rectangle([S(k + 60), S(760), S(k + 120), S(880)], fill=(250, 246, 238))
    for k in range(0, W + 60, 60):
        poly(d, [(k, 880), (k + 60, 880), (k + 30, 912)], fill=(206, 50, 56) if (k // 60) % 2 == 0 else (250, 246, 238))
    d.rectangle([0, S(752), W * K, S(766)], fill=(120, 40, 44))
    d.rectangle([S(380), S(960), S(700), S(1260)], fill=(56, 46, 40))   # the café door/window, dark inside
    d.rectangle([S(380), S(960), S(700), S(1260)], outline=(150, 120, 90), width=iw(10))
    d.rounded_rectangle([S(820), S(1000), S(1000), S(1250)], radius=S(10), fill=(40, 44, 40), outline=(140, 110, 80), width=iw(8))
    d.text((S(910), S(1060)), 'קפה', font=font(S(44), 900), fill=(250, 246, 238), anchor='mm')
    for j in range(3): d.line([(S(850), S(1120 + j * 40)), (S(970), S(1120 + j * 40))], fill=(200, 200, 190), width=iw(4))
    # sidewalk
    d.rectangle([0, S(1330), W * K, H * K], fill=(178, 176, 172))
    for y in range(1330, H, 90): d.line([(0, S(y)), (W * K, S(y))], fill=(156, 154, 150), width=iw(4))
    for x in range(0, W, 150): d.line([(S(x), S(1330)), (S(x - 60), S(H))], fill=(156, 154, 150), width=iw(4))
    d.rectangle([0, S(1322), W * K, S(1336)], fill=(140, 138, 134))
    # a planter with a little olive tree at the left edge
    d.rounded_rectangle([S(-30), S(1180), S(130), S(1340)], radius=S(10), fill=(150, 96, 60), outline=(100, 60, 36), width=iw(5))
    for (x, y, r) in ((40, 1080, 90), (-10, 1020, 70), (90, 1010, 70), (40, 960, 60)):
        E(d, x, y, r, r * 0.8, fill=(120, 140, 90), outline=(80, 100, 60), width=4)
    img = img.filter(ImageFilter.GaussianBlur(S(1.5)))
    return img

def table(img):
    """the round café table in front + the paper coffee cup"""
    d = ImageDraw.Draw(img)
    d.ellipse([S(-160), S(1560), S(1240), S(1760)], fill=(196, 198, 204), outline=(90, 92, 100), width=iw(8))
    d.ellipse([S(-140), S(1574), S(1220), S(1740)], fill=(214, 216, 222))
    for k in range(0, 1100, 70): d.line([(S(k), S(1590)), (S(k - 40), S(1725))], fill=(198, 200, 206), width=iw(3))
    d.rectangle([S(-20), S(1700), S(1100), H * K], fill=(150, 150, 156))

def cup(img, t):
    d = ImageDraw.Draw(img)
    x, y = 170, 1520
    poly(d, [(x - 60, y - 120), (x + 60, y - 120), (x + 46, y + 70), (x - 46, y + 70)], fill=(250, 248, 240), outline=(120, 110, 96), width=5)
    poly(d, [(x - 56, y - 40), (x + 56, y - 40), (x + 52, y + 10), (x - 52, y + 10)], fill=(170, 120, 80))
    d.rounded_rectangle([S(x - 70), S(y - 146), S(x + 70), S(y - 116)], radius=S(10), fill=(240, 236, 226), outline=(120, 110, 96), width=iw(4))
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(3):
        u = (t * 0.6 + k / 3) % 1.0
        E(od, x + 18 * math.sin(t * 2 + k * 2) - 10 + k * 10, y - 170 - 120 * u, 18 + 20 * u, 14 + 16 * u, fill=(255, 255, 255, int(110 * math.sin(math.pi * u))))
    img.alpha_composite(ov)

WALKERS = [('c2', 0.35, 920, 0.30, 0.4, 55), ('h0', 0.80, 930, 0.28, 1.6, -45)]
HX2, HY2, F2 = 800, 960, 1.46

def cat_state(t):
    st = E3.base_state(); st.update(red=0.9, cobweb=0.0, blush=0.4)
    rot, dy = 0.0, 0.0
    v = voice_v(t, 'cat')
    s_t = story_t(t)
    if L['0b'] <= s_t < MAIL and t < BREAK:        # "אושר! אני מאושר!" — triumph, the phone overhead
        u = s_t - L['0b']
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(s_t, rest='smile', loud='w'), ear_dy=-32, blush=1.0, look=(-30, -26))
        rot = -6 * math.sin(u * 9); dy = -20 * voice_v(s_t, 'cat') - 10 * abs(math.sin(u * 8))
    elif t < FF[0]:                                  # the want: "האישור יישלח למייל" — hopeful, a bit wary
        st.update(lid=0.05, pupil='normal', brow='up', mouth=cat_mouth(t, rest='flat', loud='w'), ear_dy=-10, look=(-26, 16), blush=0.2)
        rot = 2 * math.sin(t * 5); dy = -12 * v
    elif t < L[2]:                                   # x64: the form fills — focused
        u = (t - FF[0]) / (FF[1] - FF[0])
        st.update(lid=0.2, pupil='normal', brow='annoyed', mouth='flat', look=(-26, 20), ear_dy=-6)
        rot = 1.5 * math.sin(t * 13)
    elif t < CAM:                                    # "טופס. מולא."
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile_small', loud='smile'), ear_dy=-18, blush=0.6, look=(-20, 14))
        dy = -10 * v - (14 * math.exp(-(t - CHK1) * 6) if t >= CHK1 else 0)
    elif t < SNAP + 0.25:                            # the selfie: the big posed grin, looking at the lens
        u = t - CAM
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', ear_dy=-24, blush=1.0, look=(-12, 4))
        rot = -5 * ease_out(clamp(u / 0.3)); dy = -6
        if t >= SNAP: st.update(lid=0.85)                                                  # blinded by his own flash
    elif t < L[3]:                                   # the upload bar: holding his breath
        st.update(lid=0.0, pupil='normal', brow='annoyed', mouth='flat', look=(-26, 18), ear_dy=-8, sweat=0.5)
        dy = 2 * math.sin(t * 20)
    elif t < SEND[0]:                                # "תמונה. עלתה."
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile_small', loud='smile'), ear_dy=-20, blush=0.7, look=(-22, 14))
        dy = -10 * v - (14 * math.exp(-(t - CHK2) * 6) if t >= CHK2 else 0)
    elif t < CHK3:                                   # sending... the chat: Sharit
        st.update(lid=0.0, pupil='big', brow='up', mouth='w', look=(-26, 18), ear_dy=-14, blush=0.3)
        dy = -4 * abs(math.sin(t * 6))
    elif t < L['0b']:                                # gold: approved!
        u = t - CHK3
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile', look=(-20, 8), ear_dy=-28 * math.exp(-u * 1.5) - 8, blush=1.0)
        dy = -20 * abs(math.sin(u * 9)) * math.exp(-u * 1.2)
    elif t < HOLD[0]:                                # the mail app: "פותח... פותח..."
        st.update(lid=0.0, pupil='big', brow='up', mouth=cat_mouth(t, rest='smile_small', loud='w'), look=(-28, 18), ear_dy=-18, blush=0.6)
        dy = -8 * v
    elif t < BREAK:                                  # THE PEAK: breath held, eyes huge on the spinner
        u = t - HOLD[0]
        st.update(lid=0.0, pupil='big', brow='up', mouth='smile_small', look=(-30, 20), ear_dy=-22, blush=0.8)
        dy = 4 * math.sin(u * 30) * 0.3
    else:                                            # the break: mailbox full — frozen
        u = t - BREAK
        st.update(lid=0.0, pupil='tiny', brow='none' if t < L[105] + 0.3 else 'sad', mouth='flat' if t < L[105] else cat_mouth(t, rest='flat', loud='w'),
                  ear_dy=-26 * math.exp(-u * 4), ear_droop=clamp((u - 0.8) / 0.8) * 0.6,
                  look=(-30, 18), twitch=(t >= RESET and int(t * 12) % 2 == 0), sweat=clamp(u / 0.6), blush=0.0)
        dy = -8 + 4 * clamp(u - 1.0)
    return st, rot, dy

def phone_pose(t):
    """phone centre, angle, scale + whether it is raised overhead"""
    s_t = story_t(t)
    if L['0b'] <= s_t < MAIL and t < BREAK:                       # overhead, triumphant (cold open + in context)
        u = s_t - L['0b']
        return (420 + 8 * math.sin(t * 9), 930 - 14 * abs(math.sin(u * 8))), -6 + 3 * math.sin(t * 7), 0.72, True
    if CAM <= s_t < SNAP + 0.25:                                  # selfie: held out, screen to us
        k = ease_out(clamp((s_t - CAM) / 0.3))
        return lerp2((590, 1260), (440, 1120), k), lerp(6, -4, k), lerp(0.66, 0.70, k), False
    if s_t >= BREAK and t >= COLD_END:                            # the break: pulled close to the face, readable
        k = ease_out(clamp((s_t - BREAK) / 0.25))
        return lerp2((560, 1230), (430, 1150), k), lerp(4, 0, k), lerp(0.68, 0.80, k), False
    if HOLD[0] - 0.3 <= s_t < BREAK:                              # the peak: drawn in toward the face
        k = ease_io(clamp((s_t - (HOLD[0] - 0.3)) / 0.5))
        return lerp2((590, 1260), (560, 1230), k), lerp(6, 4, k), lerp(0.66, 0.68, k), False
    return (590, 1260 + 6 * math.sin(t * 7)), 6, 0.66, False

def scene(t, i):
    img = BG.copy()
    s_t = story_t(t)
    st, rot, dy = cat_state(t)
    d = ImageDraw.Draw(img)
    E(d, HX2, 1730, 380, 420, fill=FUR, outline=OUT, width=7)
    E(d, HX2, 1780, 170, 280, fill=CREAM)
    E12.paste_head(img, st, i, HX2, HY2 + dy, F2, rot)
    table(img); cup(img, t)
    d = ImageDraw.Draw(img)
    pc, ang, sc, over = phone_pose(t)
    if over:
        grip = (pc[0] + 60, pc[1] + 200)
        capsule(d, (HX2 - 190, 1500), grip, 100, FUR, OUT, 4)
        paste_rot(img, phone_at(t), pc, ang, sc)
        d = ImageDraw.Draw(img); E12.big_paw(d, grip, -30, 0.8)
        capsule(d, (HX2 + 170, 1500), (HX2 + 300, 1060), 96, FUR, OUT, 4); E12.big_paw(d, (HX2 + 300, 1060), 10, 0.8)   # the other paw up: a fist
    else:
        grip = (pc[0] + 120 * sc / 0.66, pc[1] + 170 * sc / 0.66)
        capsule(d, (HX2 - 170, 1560), grip, 100, FUR, OUT, 4)
        paste_rot(img, phone_at(t), pc, ang, sc)
        d = ImageDraw.Draw(img)
        E12.big_paw(d, grip, -20, 0.8)
        mode = screen_mode(t)
        if (mode == 'form' and s_t < FF[1]) or (MAIL - 0.15 <= s_t < MAIL + 0.15) or (SEND[0] - 0.1 <= s_t < SEND[0] + 0.15) or (L[2] - 0.2 <= s_t < L[2] + 0.1):
            tp = (pc[0] + 10, pc[1] + 100 * sc)                   # the other paw taps the screen
            jab = 8 * math.sin(t * 40) if mode == 'form' else 0
            capsule(d, (HX2 + 170, 1560), (tp[0] + 60, tp[1] + 40 + jab), 90, FUR, OUT, 4); E12.big_paw(d, (tp[0] + 40, tp[1] + 30 + jab), 20, 0.6)
    for c_ in (CHK1, CHK2, CHK3):
        if c_ <= s_t < c_ + 0.5: burst(img, (pc[0], pc[1] - 60), s_t - c_, (120, 255, 160) if c_ != CHK3 else (255, 220, 120), 170, 10, 0.4)
    if GOLDT <= s_t < BREAK: E18.confetti(img, s_t - GOLDT + 0.3)
    return img

# ------------------------------------------------------------------ overlays
CHIP_Y = 200
CHIPS = [('טופס', 820, CHK1), ('תמונה', 540, CHK2), ('אישור', 260, CHK3)]
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

# ------------------------------------------------------------------ the real-seconds clock
CLOCK_LABEL = ['החיבור', 'יתנתק בעוד']
ZERO = BREAK
def clock_state(t):
    name = shot(t)[0]
    st = story_t(t)
    s = C.secs_left(st, ZERO)
    if name == 'rewind': return s, 'run', True
    if t >= BREAK: return 0, ('zero' if t < BREAK + 0.6 else 'run'), False
    return s, ('hot' if s <= 5 else 'run'), False

BG = SH_AV = PILL_EP = PILL_Q = PILL_PART = None
def init_all():
    global BG, SH_AV, PILL_EP, PILL_Q, PILL_PART
    m.init_static(); E3.init_all()
    E13.build_crowd()
    BG = build_street_bg()
    SH_AV = []
    for mo in ('lazy', 'talk', 'grin'):     # Sharit's chat avatar, 3 mouth states (head crop)
        st = SH.base(); st.update(mouth=mo, lid=0.6, look=(0, 6), snack=False)
        lay = SH.draw(st, 3 if mo == 'talk' else 0).crop((S(130), S(110), S(570), S(500)))
        SH_AV.append(lay.resize((S(100), int(S(100) * lay.height / lay.width)), Image.LANCZOS))
    PILL_EP = HUD._pill(EP_LABEL, None, fill=HUD.YELLOW, scale=0.8)
    PILL_Q = HUD._pill(str(QUEUE), 'ticket', scale=0.8)
    PILL_PART = HUD._pill(PART_LABEL, None, fill=(255, 255, 255), scale=0.8)

def camera(t):
    name, a, b = shot(t)
    z, cx, cy = 1.0, 540.0, 960.0
    pu = t - a
    if name == 'two':
        z, cx, cy = 1.06 + 0.01 * pu, 560, 1040
        s_t = t
        if a == 0.0:                                   # cold open: tight, the phone raised overhead, the plant strip on top
            z, cx, cy = 1.20 + 0.03 * t, 560, 1010
            if t < 0.3: z = 1.44 - 0.20 * ease_out(t / 0.3)
        elif t < FF[0]: z, cx, cy = 1.20, 600, 1140    # the want: the site "יישלח למייל" next to his face
        elif t < L[2]: z, cx, cy = 1.0, 540, 960       # x64 wide (the street, passers-by)
        elif t < CAM: z, cx, cy = 1.16, 600, 1120
        elif t < SNAP + 0.25: z, cx, cy = 1.22, 600, 1060   # the selfie
        elif t < SEND[0]: z, cx, cy = 1.30, 600, 1200  # the upload bar + the flashing 99% strip (plant again)
        elif t < CHK3: z, cx, cy = 1.24, 620, 1180     # the chat with Sharit
        elif t < L['0b']: z, cx, cy = 1.08, 560, 1040  # gold, confetti
        elif t < MAIL: z, cx, cy = 1.16, 560, 1010     # "אושר!" in context (= the cold open)
        elif t < HOLD[0]: z, cx, cy = 1.20, 640, 1160
        if HOLD[0] - 0.2 <= t < BREAK:
            k = ease_io(clamp((t - (HOLD[0] - 0.2)) / (BREAK - HOLD[0] + 0.2))); z, cx, cy = 1.20 + 0.14 * k, lerp(640, 640, k), lerp(1160, 1150, k)
    elif name == 'rewind':
        z, cx, cy = 1.06, 540.0 + 30 * math.sin(t * 90), 1000
    elif name == 'break':
        z, cx, cy = 1.24 + 0.02 * pu, 600, 1120
    elif name == 'frozen':
        z, cx, cy = 1.30 + 0.03 * pu, 620, 1100
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
    if shake:
        rng = random.Random(i); ccx += rng.uniform(-shake, shake); ccy += rng.uniform(-shake, shake); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if t < COLD_END: frame = frame.rotate(-5, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(170, 200, 236, 255))
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < BREAK:
        k = clamp((t - HOLD[0]) / 0.15)
        pulse = sum(math.exp(-((t - (HOLD[0] + 0.05 + 0.26 * j)) * 14) ** 2) for j in range(2))
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(50 * k + 30 * pulse))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if FF[0] <= t < FF[1]: ff_overlay(frame, t)
    for s_ in (CHK1, CHK2, CHK3, BREAK):
        if s_ <= t < s_ + 0.06: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if SNAP <= t < SNAP + 0.18:                                      # the selfie flash
        frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(230 * (1 - (t - SNAP) / 0.18)))))
    if t >= BREAK and t < DUR - 0.25:                               # a red tint on the break
        k = clamp((t - BREAK) / 0.12) * (0.6 + 0.4 * math.exp(-(t - BREAK) * 3))
        frame.alpha_composite(Image.new('RGBA', frame.size, (120, 0, 0, int(40 * k))))
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
            m.paste_center(frame, m.caption_layer(lines, 96, WHITE), W / 2, 290)
    if name in ('two', 'rewind'): chips(frame, t)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            col = SHARIT_SUB if SPEAKER[li] == 'sh' else WHITE
            m.paste_center(frame, sub_layer(lines, col), W / 2, 1560)
    if t < COLD_END or (T0 <= t < FF[0]) or name == 'frozen':
        frame.alpha_composite(PILL_EP, (40, 70))
        frame.alpha_composite(PILL_PART, (40 + PILL_EP.width + 10, 70))
        if not (t > DUR - 1.0 and int(t * 10) % 3 == 0): frame.alpha_composite(PILL_Q, (W - 40 - PILL_Q.width, 70))
    if t < DUR - 0.25:
        s, state, scr = clock_state(t)
        C.draw(frame, CLOCK_LABEL, s, state, t, scr)
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio (voices + SFX + street room tone; no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; voice = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(41)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for i0, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{i0:03d}.npy')).astype(np.float64)
        if SPEAKER[i0] == 'sh': y = m.phone_line(y) * 1.6                       # the chat voice through the phone
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
    def keys(t0, t1, g=0.05, step=0.09):
        tc = t0
        while tc < t1: add(sfx, m.highpass(nz(0.015), 3000) * np.exp(-tt_(0.015) * 200), tc, g); tc += step
    def car(t0, ln=2.2, g=0.03):                                                 # a distant car passing
        tt = tt_(ln); env = np.sin(np.pi * tt / ln) ** 2
        add(sfx, m.lowpass(nz(ln), 500) * env, t0, g)
    add(sfx, thud(0.7), 0.0)
    for k in range(5): pop(0.05 + 0.12 * k, 0.07)                               # confetti pops of the cold open
    rl = RW[1] - RW[0]; tr = tt_(rl)
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    add(sfx, m.lowpass(nz(DUR), 380) * 0.6, 0.0, 0.016)                         # street room tone
    for t_c in (3.0, 9.5, 15.0): car(t_c)
    add(sfx, m.bandpass(nz(0.4), 600, 5000) * np.linspace(0, 1, int(0.4 * SR)), FF[0] - 0.3, 0.06)
    keys(FF[0], FF[1], 0.07, 0.05)
    tap(L[2] - 0.1, 0.25); check(CHK1, 0.15)
    tap(SNAP - 0.05, 0.2)
    add(sfx, m.highpass(nz(0.06), 1800) * np.exp(-tt_(0.06) * 60), SNAP, 0.35)  # shutter
    add(sfx, m.highpass(nz(0.04), 2200) * np.exp(-tt_(0.04) * 80), SNAP + 0.07, 0.25)
    tc = UP[0]
    while tc < UP[1] - 0.1:                                                      # upload blips (+ the strip's warning buzz)
        add(sfx, m.tone(880, 0.04, harm=((1, 1),), decay=40), tc, 0.04); tc += 0.17
    check(CHK2, 0.16)
    tap(SEND[0], 0.25); whoosh(SEND[0] + 0.1, 0.07, 0.25)
    pop(CHAT, 0.18); keys(CHAT, L[4], 0.04, 0.17)
    check(CHK3, 0.2, True)
    for k in range(6): pop(GOLDT + 0.05 + 0.11 * k, 0.07)
    tap(MAIL, 0.3)
    tc = MAIL + 0.1
    while tc < BREAK - 0.05: add(sfx, m.tone(1200, 0.02, harm=((1, 1),), decay=60), tc, 0.02); tc += 0.25   # spinner ticks
    heartbeat(HOLD[0] + 0.04); heartbeat(HOLD[0] + 0.30, 0.5)
    add(sfx, thud(0.6), BREAK); whoosh(BREAK, 0.08, 0.2)
    for k, f in enumerate((392.0, 311.1)): add(sfx, m.tone(f, 0.28, harm=((1, 1), (2, 0.4)), decay=6), BREAK + 0.02 + 0.16 * k, 0.12)   # the bounce "bonk"
    pop(RESET, 0.12)
    add(sfx, m.tone(82.4, 1.2, harm=((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)), decay=2.2), L[105] + D[105] - 0.2, 0.14)
    out = voice + sfx
    out = out[:int(DUR * SR)]
    wl_ = 0.3; add(out, m.bandpass(nz(wl_), 500, 6000) * np.sin(np.pi * tt_(wl_) / wl_) ** 2 * 0.12, DUR - 0.28)
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
    ticks, prev = [], None                                                       # the clock: a soft tick every real second
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
        print('DUR', DUR, 'NF', NF, 'COLD_END', COLD_END, 'T0', round(T0, 2), 'FF', [round(x, 2) for x in FF])
        print('L', {k: round(v, 2) for k, v in L.items()})
        print('CHK', [round(x, 2) for x in (CHK1, CHK2, CHK3)], 'CAM', round(CAM, 2), 'SNAP', round(SNAP, 2), 'UP', [round(x, 2) for x in UP],
              'SEND', [round(x, 2) for x in SEND], 'MAIL', round(MAIL, 2), 'HOLD', [round(x, 2) for x in HOLD],
              'BREAK', round(BREAK, 2), 'RESET', round(RESET, 2), 'FREEZE', round(FREEZE, 2), 'tail', round(DUR - BREAK, 2))
        print('clock frame0', C.secs_left(story_t(0), ZERO), 'after rewind', C.secs_left(story_t(T0 + 0.01), ZERO))
        return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, os.environ.get('SHEET', 'ep41_contact.png'))); print('ok'); return
    if mode == 'frame':
        init_all(); tm = float(sys.argv[2]); draw_frame(int(round(tm * FPS))).save(os.path.join(OUTDIR, f'ep41_f{tm:.2f}.png')); print('ok'); return
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
