#!/usr/bin/env python3
"""
"חתול בהמתנה" — voiced specials #3 and #4 (Seedance 2.5 + Kling clips from Nano Banana Pro start frames).
  #3 "לא היית בבית"  — the courier note: home all day, note under the door, the branch, another note.
  #4 "אישור שצריך אישור" — window 3 sends him to window 4 which sends him to window 3 (same clerk).
Template: sp2.py (cold open → ◀◀ rewind → story → whip loop, snap-zoom per cut, subtitles by speaker, SFX only, no music).
  python3 spx.py 3|4 times | test t1 t2 ... | render
Sources: out/sp<N>/src/sp<N>_kNN.mp4 (clips), out/sp<N>/src/sp<N>_vNN.mp3 (voices).
"""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import make_video as m
from make_video import W, H, FPS, font, WHITE, ease_out, ease_in, ease_io, clamp, lerp
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice'))
import sp1_prep as VP

EPN = int(sys.argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'out', f'sp{EPN}', 'src')
OUT = m.OUTDIR
SR = m.SR
PINK = (255, 182, 210); BLUE = (176, 216, 255); YELLOW = (255, 221, 51); AMBER = (255, 184, 64)
COLOR = {'cat': WHITE, 'sh': PINK, 'ivr': BLUE}
MAXP = {'cat': 0.18, 'ivr': 0.22, 'sh': 0.3}

# ------------------------------------------------------------------ episode configs
if EPN == 3:
    NAME = 'sp3_not_home'
    VOICE = {0: ('cat', False), 1: ('ivr', True), 2: ('cat', False), 3: ('cat', False), 4: ('cat', False), 5: ('sh', False),
             6: ('cat', False), 7: ('sh', False), 8: ('cat', False), 9: ('sh', False), 10: ('cat', False)}
    SUBS = {0: ['הייתי בבית!!!', 'כל! היום!!!'], 1: [['החבילה שלך תגיע היום,'], ['בין 8 בבוקר ל-8 בערב.']],
            2: ['8 עד 8. מעולה.', 'אני לא זז מהדלת.'], 3: ['כל רעש... זה הוא.'], 4: ['"לא היית בבית"?!'],
            5: ['שנייה, מותק...'], 6: ['באתי לאסוף חבילה.', 'השליח רשם שלא הייתי בבית.'],
            7: ['החבילה עוד לא הגיעה לסניף, מותק.', 'תבוא מחר.'], 8: ['אז איפה היא?!'], 9: ['על הרכב, מותק.', 'מסתובבת.'],
            10: ['...כי הייתי אצלכם.']}
    TITLE = ['השליח:', '"לא היית בבית"']
    REWIND = '8 בבוקר'
    END = ['כל. פעם.']
    CTA = ['כמה פתקים כאלה קיבלתם?', 'כתבו בתגובות']
    BLUR_SRC = 'k02'
else:
    NAME = 'sp4_two_windows'
    VOICE = {0: ('cat', False), 1: ('cat', False), 2: ('sh', False), 3: ('cat', False), 4: ('sh', False), 5: ('cat', False),
             6: ('sh', False), 7: ('sh', False), 8: ('cat', False), 9: ('ivr', True), 10: ('cat', False)}
    SUBS = {0: ['אבל היא שלחה', 'אותי אלייך!!!'], 1: ['שלום, אני צריך', 'אישור תושב.'],
            2: [['בשמחה, מותק.'], ['רק תביא אישור ארנונה.', 'חלון 4.']], 3: ['שלום, אני צריך', 'אישור ארנונה.'],
            4: [['אין בעיה, מותק.'], ['רק תביא אישור תושב.', 'חלון 3.']], 5: ['רגע... את...', 'היית שם.'],
            6: ['שם זה חלון 3, מותק.', 'פה זה חלון 4.'], 7: ['מותק...', 'אפשר גם באתר.'], 8: ['באמת?!'],
            9: [['האתר בתחזוקה.'], ['נסו שוב בשעות', 'הפעילות של הסניף.']], 10: ['כל. פעם.']}
    TITLE = ['אישור', 'שצריך אישור']
    REWIND = 'שעה קודם'
    END = ['כל. פעם.']
    CTA = ['מה האישור הכי הזוי', 'שביקשו מכם? כתבו בתגובות']
    BLUR_SRC = 'k03'

# ------------------------------------------------------------------ voices
def load_voices():
    V = {}
    for i in VOICE:
        src = os.path.join(SRC, f'sp{EPN}_v{i:02d}.mp3')
        if VOICE[i][0] == 'ivr':
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-af', 'atempo=1.2', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                                 capture_output=True, check=True).stdout
            x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
        else:
            x = VP.decode(src)
        y = VP.tighten(x, MAXP[VOICE[i][0]])
        V[i] = y / (np.max(np.abs(y)) + 1e-9) * 0.95
    return V
VOX = load_voices()
VD = {i: len(VOX[i]) / SR for i in VOX}

# ------------------------------------------------------------------ edit decision list
SH = []
def shot(**k): SH.append(k)

if EPN == 3:
    shot(kind='clip', src='k01', ss=0.6, dur=VD[0] + 0.4, voice=[(0, 0.05)], tag='cold')
    shot(kind='rewind', src='k02', ss=0.0, dur=0.45)
    shot(kind='ui', ui='notify', dur=VD[1] + 0.35, voice=[(1, 0.15)])
    shot(kind='clip', src='k02', ss=0.6, dur=VD[2] + 0.4, voice=[(2, 0.1)])
    shot(kind='clip', src='k03', ss=0.0, dur=VD[3] + 0.5, voice=[(3, 0.15)])
    shot(kind='clip', src='k03', ss=1.2, speed=2.5, dur=1.4, ff=True, cap=['10 שעות אחר כך...'])
    shot(kind='clip', src='k04', ss=0.0, dur=2.6, cap=['18:00'], note=True)
    shot(kind='clip', src='k01', ss=1.8, dur=VD[4] + 0.45, voice=[(4, 0.08)], slam=0.05)
    shot(kind='clip', src='k05', ss=0.0, dur=VD[5] + 0.45, voice=[(5, 0.1)], cap=['למחרת, בסניף'])
    shot(kind='clip', src='k06', ss=0.3, dur=VD[6] + 0.3, voice=[(6, 0.05)])
    shot(kind='clip', src='k05', ss=1.6, dur=VD[7] + 0.3, voice=[(7, 0.05)])
    shot(kind='clip', src='k06', ss=2.4, dur=VD[8] + 0.35, voice=[(8, 0.05)], slam=0.1)
    shot(kind='clip', src='k05', ss=2.2, dur=VD[9] + 0.35, voice=[(9, 0.05)])
    shot(kind='clip', src='k07', ss=0.0, dur=1.5, cap=['בחזרה בבית...'])
    shot(kind='clip', src='k07', ss=1.5, dur=max(2.6, VD[10] + 0.9), voice=[(10, 0.2)], end=True)
else:
    shot(kind='clip', src='k01', ss=0.3, dur=VD[0] + 0.4, voice=[(0, 0.05)], tag='cold')
    shot(kind='rewind', src='k02', ss=0.0, dur=0.45)
    shot(kind='clip', src='k02', ss=0.2, dur=VD[1] + 0.3, voice=[(1, 0.08)], plate=('cat', '3'))
    shot(kind='clip', src='k03', ss=0.0, dur=VD[2] + 0.3, voice=[(2, 0.08)], plate=('sh', 'חלון 3'))
    shot(kind='clip', src='k02', ss=2.4, dur=VD[3] + 0.3, voice=[(3, 0.08)], plate=('cat', '4'), cap=['חלון 4'])
    shot(kind='clip', src='k03', ss=0.5, dur=VD[4] + 0.3, voice=[(4, 0.08)], plate=('sh', 'חלון 4'))
    shot(kind='clip', src='k05', ss=0.2, dur=VD[5] + 0.35, voice=[(5, 0.08)], plate=('cat', '4'))
    shot(kind='clip', src='k03', ss=1.2, dur=VD[6] + 0.3, voice=[(6, 0.05)], plate=('sh', 'חלון 4'))
    shot(kind='clip', src='k06', ss=0.0, speed=1.6, dur=2.4, ff=True, cap=['שעתיים אחר כך...'])
    shot(kind='clip', src='k07', ss=0.0, dur=VD[7] + 0.3, voice=[(7, 0.1)])
    shot(kind='clip', src='k07', ss=2.7, dur=VD[8] + 0.4, voice=[(8, 0.05)])
    shot(kind='ui', ui='site', dur=VD[9] + 0.4, voice=[(9, 0.15)])
    shot(kind='clip', src='k08', ss=0.4, dur=max(2.6, VD[10] + 1.0), voice=[(10, 0.3)], end=True)

T = [0.0]
for s in SH: T.append(T[-1] + s['dur'])
DUR = round(T[-1], 2)
NF = int(round(DUR * FPS))
CUES = []
for k, s in enumerate(SH):
    for ln, off in s.get('voice', []): CUES.append((T[k] + off, ln))

def shot_at(t):
    for k in range(len(SH)):
        if T[k] <= t < T[k + 1]: return k
    return len(SH) - 1

# ------------------------------------------------------------------ media
_cache = {}
def clip_frames(k):
    if k in _cache: return _cache[k]
    _cache.clear()
    s = SH[k]; sp = s.get('speed', 1.0)
    path = os.path.join(SRC, f"sp{EPN}_{s['src']}.mp4")
    # crop to exact 9:16, then scale
    vf = f"setpts={1 / sp:.4f}*PTS,fps={FPS},crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale={W}:{H}:flags=lanczos"
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f"{s['ss']:.3f}", '-t', f"{s['dur'] * sp + 0.3:.3f}", '-i', path,
                          '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    _cache[k] = fr
    return fr

BLUR = None
def ui_bg():
    global BLUR
    if BLUR is None:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '0.5', '-i', os.path.join(SRC, f'sp{EPN}_{BLUR_SRC}.mp4'), '-frames:v', '1',
                              '-vf', f"crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale={W}:{H}", '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, check=True).stdout
        im = Image.fromarray(np.frombuffer(raw, np.uint8).reshape(H, W, 3), 'RGB').resize((W // 4, H // 4))
        im = im.filter(ImageFilter.GaussianBlur(8)).resize((W, H))
        BLUR = Image.eval(im, lambda v: int(v * 0.45)).convert('RGBA')
    return BLUR.copy()

def phone_panel(img, u, draw_body):
    pw, ph = 640, 1120
    p = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=70, fill=(18, 18, 22))
    d.rounded_rectangle([16, 16, pw - 16, ph - 16], radius=58, fill=(34, 40, 64))
    d.rounded_rectangle([pw / 2 - 70, 34, pw / 2 + 70, 64], radius=15, fill=(10, 10, 12))
    draw_body(d, pw, ph)
    p = p.rotate(-2 + 0.8 * math.sin(u * 2), resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', p.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 120), mask=p.split()[3]); sh = sh.filter(ImageFilter.GaussianBlur(16))
    img.alpha_composite(sh, (int(W / 2 - p.width / 2 + 18), int(980 - p.height / 2 + 24)))
    img.alpha_composite(p, (int(W / 2 - p.width / 2), int(980 - p.height / 2)))

def ui_notify(t, u):
    img = ui_bg()
    def body(d, pw, ph):
        d.text((pw / 2, 140), '08:00', font=font(96, 800), fill=WHITE, anchor='mm')
        d.text((pw / 2, 220), 'יום שלישי', font=font(36, 600), fill=(190, 196, 220), anchor='mm')
        k = ease_out(clamp(u / 0.35)); y0 = 300 + (1 - k) * -60
        d.rounded_rectangle([40, y0, pw - 40, y0 + 250], radius=34, fill=(246, 246, 250))
        d.rounded_rectangle([pw - 130, y0 + 26, pw - 70, y0 + 86], radius=14, fill=(230, 120, 30))
        d.text((pw - 100, y0 + 56), '📦' if False else 'ש', font=font(40, 900), fill=WHITE, anchor='mm')
        d.text((pw - 150, y0 + 56), 'משלוחים', font=font(34, 800), fill=(30, 30, 36), anchor='rm')
        d.text((pw - 70, y0 + 130), 'החבילה שלך תגיע היום!', font=font(38, 800), fill=(20, 20, 26), anchor='rm')
        d.text((pw - 70, y0 + 190), 'בין 08:00 ל-20:00', font=font(38, 700), fill=(60, 60, 70), anchor='rm')
    phone_panel(img, u, body)
    return img

def ui_site(t, u):
    img = ui_bg()
    def body(d, pw, ph):
        d.rounded_rectangle([30, 90, pw - 30, 150], radius=30, fill=(60, 66, 92))
        d.text((pw / 2, 120), 'אזור אישי · בקשות', font=font(28, 600), fill=(200, 206, 230), anchor='mm')
        d.rounded_rectangle([40, 200, pw - 40, 900], radius=36, fill=(250, 250, 252))
        cx, cy = pw / 2, 420
        ang = u * 260
        for k in range(10):   # spinning gear-ish loader
            a = math.radians(ang + k * 36); al = int(60 + 190 * (k / 9))
            d.ellipse([cx + 90 * math.cos(a) - 12, cy + 90 * math.sin(a) - 12, cx + 90 * math.cos(a) + 12, cy + 90 * math.sin(a) + 12], fill=(230, 120, 30, al))
        d.text((pw / 2, 600), 'האתר בתחזוקה', font=font(52, 900), fill=(26, 26, 32), anchor='mm')
        d.text((pw / 2, 680), 'נסו שוב בשעות', font=font(36, 700), fill=(80, 80, 90), anchor='mm')
        d.text((pw / 2, 730), 'הפעילות של הסניף', font=font(36, 700), fill=(80, 80, 90), anchor='mm')
        d.rounded_rectangle([140, 790, pw - 140, 860], radius=35, fill=(200, 200, 210))
        d.text((pw / 2, 825), 'קבע תור', font=font(32, 800), fill=(120, 120, 130), anchor='mm')
    phone_panel(img, u, body)
    return img

UIS = {'notify': ui_notify, 'site': ui_site}

# ------------------------------------------------------------------ overlays
def sub_layer(lines, fill, size=62):
    f = font(size, 900); lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 110 and s > 38: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm', stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

def subs_at(t):
    for t0, ln in CUES:
        d = VD[ln]
        if t0 - 0.05 <= t < t0 + d + 0.2:
            s = SUBS[ln]; who = VOICE[ln][0]
            if isinstance(s[0], list):
                tot = sum(len(' '.join(c)) for c in s); acc = 0
                for c in s:
                    a = t0 + d * acc / tot; acc += len(' '.join(c)); b = t0 + d * acc / tot
                    if a - 0.05 <= t < b + 0.1: return c, who
                return s[-1], who
            return s, who
    return None, None

def rewind_overlay(frame, t):
    frame.alpha_composite(m.SCAN)
    d = ImageDraw.Draw(frame); rng = random.Random(int(t * 120))
    for _ in range(5):
        y = rng.uniform(300, 1700); h = rng.uniform(4, 14); d.rectangle([0, y, W, y + h], fill=(255, 255, 255, 70))
    for x0 in (230, 274):
        d.polygon([(x0 + 44, 900), (x0, 930), (x0 + 44, 960)], fill=WHITE, outline=(10, 10, 12), width=5)
    d.text((600, 930), REWIND, font=font(76, 900), fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(10, 10, 12))

def ff_overlay(frame, t):
    frame.alpha_composite(m.SCAN)
    d = ImageDraw.Draw(frame)
    if int(t * 4) % 2 == 0:
        for x0 in (790, 834):
            d.polygon([(x0, 330), (x0 + 44, 360), (x0, 390)], fill=WHITE, outline=(10, 10, 12), width=4)
        d.text((950, 360), 'x64', font=font(52, 900), fill=WHITE, anchor='mm', stroke_width=6, stroke_fill=(10, 10, 12))

PLATE = {'sh': (416, 413, 628, 515), 'cat': (470, 430, 610, 525)}
def plate_overlay(frame, who, label):
    x0, y0, x1, y1 = PLATE[who]
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=AMBER, outline=(140, 90, 20), width=5)
    s = 58
    while d.textlength(label, font=font(s, 900)) > (x1 - x0) - 30 and s > 24: s -= 2
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 2), label, font=font(s, 900), fill=(32, 26, 16), anchor='mm')

CAP_CACHE = {}
def cap(lines, size, fill=WHITE):
    key = (tuple(lines), size, fill)
    if key not in CAP_CACHE: CAP_CACHE[key] = m.caption_layer(lines, size, fill)
    return CAP_CACHE[key]

def draw_frame(i):
    t = i / FPS; k = shot_at(t); s = SH[k]; u = t - T[k]
    kind = s['kind']
    if kind == 'ui':
        img = UIS[s['ui']](t, u)
    else:
        fr = clip_frames(k)
        if kind == 'rewind':
            idx = int((1 - u / s['dur']) * min(len(fr) - 1, 40))
        else:
            idx = min(len(fr) - 1, int(u * FPS))
        img = Image.fromarray(fr[idx], 'RGB').convert('RGBA')
        if s.get('plate'): plate_overlay(img, *s['plate'])
    z, cx, cy = 1.0 + 0.03 * u / max(0.5, s['dur']), 540.0, 1000.0
    if kind != 'rewind' and u < 0.22: z += 0.07 * (1 - ease_out(u / 0.22))
    if s.get('tag') == 'cold':
        z += 0.10 * (1 - ease_out(clamp(u / 0.35))); cx += 14 * math.sin(t * 61) * math.exp(-u * 2.5); cy += 10 * math.cos(t * 53) * math.exp(-u * 2.5)
    if s.get('slam') is not None and u >= s['slam']:
        q = u - s['slam']; cx += 12 * math.sin(t * 70) * math.exp(-q * 6); cy += 8 * math.cos(t * 57) * math.exp(-q * 6)
    if s.get('note'):   # slow push toward the door gap
        e = ease_io(clamp(u / s['dur'])); z = lerp(z, 1.35, e); cx = lerp(cx, 680, e); cy = lerp(cy, 1250, e)
    if z > 1.001:
        cw, ch = W / z, H / z
        l = clamp(cx - cw / 2, 0, W - cw); tp = clamp(cy - ch / 2, 0, H - ch)
        img = img.crop((int(l), int(tp), int(l + cw), int(tp + ch))).resize((W, H), Image.BILINEAR)
    frame = img
    frame.alpha_composite(m.VIG)
    if kind == 'rewind': rewind_overlay(frame, t)
    if s.get('ff'): ff_overlay(frame, t)
    if k == 0:
        m.paste_center(frame, cap(TITLE, 104), W / 2, 240)
    if s.get('cap'):
        m.paste_center(frame, cap(s['cap'], 86), W / 2, 250)
    if s.get('end') and u > 0.5:
        m.paste_center(frame, cap(END, 104), W / 2, 260)
        m.paste_center(frame, cap(CTA, 54, YELLOW), W / 2, 1712)
    lines, who = subs_at(t)
    if lines and s.get('end') and u > 0.5 and list(lines) == list(END): lines = None
    if lines:
        m.paste_center(frame, sub_layer(lines, COLOR[who]), W / 2, 1460 if len(lines) == 1 else 1430)
    if t >= DUR - 0.22:
        q = (t - (DUR - 0.22)) / 0.22
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(650 * q * q), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * q)))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio
def phone_fx(x):
    y = m.bandpass(x, 320, 3200)
    y = np.tanh(y * 2.2) / np.tanh(2.2)
    return y * 0.9

def build_audio(path):
    n = int(DUR * SR) + SR; vox = np.zeros(n); sfx = np.zeros(n); add = m.add
    rng = np.random.default_rng(11)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    for t0, ln in CUES:
        y = VOX[ln]
        if VOICE[ln][1]: y = phone_fx(y)
        add(vox, y, t0, 0.95)
    def thud(t0, g=0.8):
        tt = tt_(0.4); f = 140 * np.exp(-tt * 6) + 45
        add(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 10) + m.lowpass(nz(0.4), 500) * np.exp(-tt * 30) * 0.6, t0, g)
        add(sfx, m.highpass(nz(0.05), 1500) * np.exp(-tt_(0.05) * 60), t0, 0.4)
    def whoosh(t0, g=0.06): add(sfx, m.bandpass(nz(0.16), 600, 5000) * np.sin(np.pi * tt_(0.16) / 0.16) ** 2, t0 - 0.08, g)
    def ding(t0):
        add(sfx, m.tone(1318.5, 0.5, harm=((1, 1), (2.76, 0.2)), decay=7), t0, 0.2); add(sfx, m.tone(1760, 0.6, harm=((1, 1), (2.76, 0.2)), decay=7), t0 + 0.09, 0.18)
    def knock(t0, n_=3):
        for r in range(n_): add(sfx, m.lowpass(nz(0.06), 900) * np.exp(-tt_(0.06) * 70), t0 + r * 0.16, 0.5)
    def paper(t0, L_=0.7): add(sfx, m.bandpass(nz(L_), 2000, 9000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 9 * tt_(L_)))) * np.sin(np.pi * tt_(L_) / L_), t0, 0.08)
    def snore(t0, L_=1.2):
        tt = tt_(L_); add(sfx, m.lowpass(nz(L_), 300) * np.sin(np.pi * tt / L_) ** 2, t0, 0.18)
    thud(0.02, 0.9)
    for k, s in enumerate(SH):
        t0 = T[k]
        if k > 0 and s['kind'] != 'rewind': whoosh(t0)
        if s['kind'] == 'rewind':
            rl = s['dur']; tr = tt_(rl); fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
            add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), t0, 0.15)
        if s.get('slam') is not None: thud(t0 + s['slam'], 0.7)
        if s['kind'] == 'ui': ding(t0 + 0.2)
        if s.get('note'):
            snore(t0 + 0.1); paper(t0 + 0.5); snore(t0 + 1.4)
        if s.get('ff'):
            L_ = s['dur']; tt = tt_(L_); f = 900 + 500 * np.sin(2 * np.pi * 7 * tt)
            add(sfx, m.bandpass(np.sin(2 * np.pi * np.cumsum(f) / SR), 400, 4000) * 0.4, t0, 0.08)
        if EPN == 3 and s.get('src') == 'k03' and not s.get('ff'): knock(t0 + 1.0, 2)
        if s.get('end'): add(sfx, m.highpass(nz(0.08), 1200) * np.exp(-tt_(0.08) * 60), t0 + 1.6, 0.4)
    add(sfx, m.bandpass(nz(0.25), 500, 6000) * np.sin(np.pi * tt_(0.25) / 0.25) ** 2, DUR - 0.24, 0.1)
    env = np.convolve(np.abs(vox), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode='same')
    out = vox + sfx * (1 - 0.45 * np.clip(env * 8, 0, 1))
    out = out[:int(DUR * SR)]
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())

def main():
    m.init_static()
    mode = sys.argv[2] if len(sys.argv) > 2 else 'render'
    if mode == 'times':
        print('DUR', DUR)
        for k, s in enumerate(SH): print(round(T[k], 2), s.get('kind'), s.get('src', s.get('ui')), round(s['dur'], 2), s.get('voice', ''))
        return
    if mode == 'test':
        times = sorted(float(x) for x in sys.argv[3:])
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(5, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for q, f in enumerate(frames): sheet.paste(f.resize((tw, th)), ((q % cols) * tw, (q // cols) * th))
        sheet.save(os.path.join(OUT, f'sp{EPN}_contact.png')); print('ok'); return
    wav = os.path.join(OUT, f'sp{EPN}_audio.wav'); build_audio(wav); print('audio ok', DUR)
    if mode == 'audio': return
    mp4 = os.path.join(OUT, f'{NAME}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(NF):
        proc.stdin.write(draw_frame(i).tobytes())
        if i % 150 == 0: print('frame', i, '/', NF, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
