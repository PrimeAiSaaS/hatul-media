#!/usr/bin/env python3
"""
"חתול בהמתנה" — החתול מגיב #1 v2: 4 הודעות (~11.2 s, no voice, no music, SFX only).
v2 (12.10, Gabi: "ארוך ומשעמם באמצע, ההודעות לא מצחיקות, הסוף והפתיחה"):
  - 4 escalating messages instead of 8, every card is a self-contained contradiction joke
  - cold open = the payoff (crying cat) with the hook "ההודעה הרביעית שברה אותו", the last beat is the same cry → seamless loop
  - cat 1.35x bigger than v1, anchored to a low floor line, tighter key (no white fringe)
  python3 react1_v2.py test 0.1 0.5 1.2 3.5 6 8.5 10.5 11.1   -> out/react1_v2_contact.png
  python3 react1_v2.py render                                -> out/react1_v2.mp4
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import make_video as m
from make_video import W, H, FPS, font, WHITE, ease_out, clamp, lerp

HERE = os.path.dirname(os.path.abspath(__file__))
RDIR = os.path.join(HERE, 'out', 'react')
OUT = m.OUTDIR

# (clip, clip_start_s, length_s, app, app_color, line1, line2, red_line, sfx)
BEATS = [
    ('06_cry',      3.50, 0.70, '',            None,           '',                       '',                    False, 'coldopen'),
    ('09_sideeye',  0.50, 2.30, 'הבנק שלי',    (28, 104, 226), 'זוהתה פעילות חריגה:',    'נכנסת לאפליקציה.',     True,  'sus'),
    ('07_furious',  1.00, 2.60, 'מוקד שירות',  (90, 90, 104),  'הנציג סיים את השיחה.',   'נשמח שתדרג אותו!',     True, 'kettle'),
    ('03_facepalm', 0.55, 2.40, 'משרד הפנים',  (28, 70, 150),  'לקביעת תור יש להציג',    'אישור על קביעת תור.',  True,  'slap'),
    ('06_cry',      1.95, 3.20, 'משרד הפנים',  (28, 70, 150),  'בקשתך אושרה!',         'התור הקרוב: מרץ 2027', True,  'wahwah'),
]
T = [0.0]
for b in BEATS: T.append(T[-1] + b[2])
DUR = round(T[-1], 2)
NF = int(round(DUR * FPS))
N_MSG = sum(1 for b in BEATS if b[3])

CAT_SCALE = 2.0                 # clip 720x1280 → 1440x2560 (v1 was 1.5)
FLOOR_Y = 1700                  # where the cat's shadow sits
CLIP_FLOOR = 985                # shadow y inside the 720x1280 clip
CAT_DX = (W - int(720 * CAT_SCALE)) // 2
CAT_DY = FLOOR_Y - int(CLIP_FLOOR * CAT_SCALE)

# ------------------------------------------------------------------ background
def build_bg():
    img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img)
    top, bot = (198, 210, 230), (234, 238, 246)
    for y in range(FLOOR_Y):
        u = y / FLOOR_Y; d.line([(0, y), (W, y)], fill=tuple(int(lerp(a, b, u)) for a, b in zip(top, bot)))
    d.rectangle([0, FLOOR_Y, W, H], fill=(176, 180, 190))
    d.rectangle([0, FLOOR_Y - 4, W, FLOOR_Y + 6], fill=(132, 138, 152))
    return img.convert('RGBA')

# ------------------------------------------------------------------ chroma key (tighter than v1: no light fringe)
def key(frame):
    a = frame.astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gr = g - np.maximum(r, b)
    alpha = np.clip(1 - (gr - 10) / 30.0, 0, 1)
    g2 = np.minimum(g, np.maximum(r, b))                       # full despill
    out = np.dstack([r, g2, b, (alpha * 255).astype(np.int16)]).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(out, 'RGBA')
    al = im.split()[3].filter(ImageFilter.MinFilter(3))        # erode 1 px → kills the halo
    im.putalpha(al)
    return im

def read_frames(name, start, length):
    path = os.path.join(RDIR, f'hatul_react_{name}.mp4')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{start:.3f}', '-t', f'{length + 0.2:.3f}', '-i', path,
                          '-vf', f'fps={FPS}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 1280, 720, 3)

# ------------------------------------------------------------------ notification card
def card(app, col, l1, l2, red, u):
    cw, ch = 960, 300
    lay = Image.new('RGBA', (W, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0 = (W - cw) / 2; y0 = 30
    d.rounded_rectangle([x0 + 6, y0 + 12, x0 + cw + 6, y0 + ch + 12], radius=48, fill=(0, 0, 0, 70))
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=48, fill=(250, 250, 252, 255), outline=(200, 204, 214, 255), width=3)
    d.rounded_rectangle([x0 + cw - 120, y0 + 30, x0 + cw - 40, y0 + 110], radius=20, fill=col + (255,))
    d.text((x0 + cw - 80, y0 + 70), app[0], font=font(48, 900), fill=WHITE, anchor='mm')
    d.text((x0 + cw - 146, y0 + 70), app, font=font(40, 800), fill=(70, 70, 80), anchor='rm')
    d.text((x0 + 44, y0 + 70), 'עכשיו', font=font(32, 600), fill=(140, 140, 150), anchor='lm')
    d.text((x0 + cw - 44, y0 + 162), l1, font=font(60, 900), fill=(26, 26, 32), anchor='rm')
    d.text((x0 + cw - 44, y0 + 240), l2, font=font(60, 900), fill=(214, 36, 44) if red else (26, 26, 32), anchor='rm')
    if 'אושרה' in l1:
        d.ellipse([x0 + 40, y0 + 120, x0 + 120, y0 + 200], fill=(40, 170, 80))
        d.line([(x0 + 60, y0 + 160), (x0 + 76, y0 + 178), (x0 + 102, y0 + 140)], fill=WHITE, width=10, joint='curve')
    if u >= 1: return lay
    out = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    off = int(lerp(-240, 0, ease_out(u)))
    out.alpha_composite(lay.crop((0, max(0, -off), W, 400)), dest=(0, max(0, off)))
    out.putalpha(out.split()[3].point(lambda v: int(v * clamp(u * 2.5))))
    return out

# ------------------------------------------------------------------ frame
BG = None
CAPS = {}
def caps():
    CAPS['cold'] = m.caption_layer(['ההודעה הרביעית', 'שברה אותו'], 100, WHITE)
    CAPS['small'] = m.caption_layer(['הודעות שכל ישראלי מכיר'], 58, WHITE)
    CAPS['end'] = m.caption_layer(['כל. פעם. מחדש.'], 92, (255, 221, 51))
    CAPS['cta'] = m.caption_layer(['איזו הודעה הכי שברה אתכם?'], 54, (255, 221, 51))

def place_cat(img, cat_rgba, t, beat):
    big = cat_rgba.resize((int(720 * CAT_SCALE), int(1280 * CAT_SCALE)), Image.BILINEAR)
    u = t - T[beat]
    z = 1.0 + (0.10 if beat > 0 else 0.0) * math.exp(-u * 10)   # snap punch-in on every new message
    if beat == 0: z = 1.18 - 0.10 * ease_out(clamp(u / BEATS[0][2]))   # cold open: snap pull-back (motion from frame 1)
    shake = (int(14 * math.sin(t * 90)), int(10 * math.cos(t * 77))) if beat == 0 else (0, 0)
    if z > 1.001:
        nw, nh = int(big.width * z), int(big.height * z)
        big = big.resize((nw, nh), Image.BILINEAR)
        fx = W / 2 - CAT_DX; fy = (FLOOR_Y - 380) - CAT_DY        # zoom around the cat's face
        dx = int(CAT_DX - fx * (z - 1)) + shake[0]; dy = int(CAT_DY - fy * (z - 1)) + shake[1]
    else:
        dx, dy = CAT_DX, CAT_DY
    img.alpha_composite(big, dest=(dx, dy)) if dx >= 0 and dy >= 0 else img.alpha_composite(
        big.crop((max(0, -dx), max(0, -dy), max(0, -dx) + W, max(0, -dy) + H)), dest=(max(0, dx), max(0, dy)))

def compose(t, cat_rgba, beat):
    img = BG.copy()
    place_cat(img, cat_rgba, t, beat)
    app, col, l1, l2, red = BEATS[beat][3:8]
    u = t - T[beat]
    if app:
        img.alpha_composite(card(app, col, l1, l2, red, clamp(u / 0.2)), dest=(0, 300))
        d = ImageDraw.Draw(img)
        k = sum(1 for b in BEATS[:beat + 1] if b[3])
        d.rounded_rectangle([40, 272, 160, 320], radius=24, fill=(16, 16, 20, 220))
        d.text((100, 296), f'{k}/{N_MSG}', font=font(32, 800), fill=WHITE, anchor='mm')
    last = len(BEATS) - 1
    end_on = beat == last and u > 1.1
    if beat == 0:
        m.paste_center(img, CAPS['cold'], W / 2, 170)
    elif end_on:
        m.paste_center(img, CAPS['end'], W / 2, 180)          # the closing gag replaces the small top caption, over the action
        m.paste_center(img, CAPS['cta'], W / 2, 1740)
    else:
        m.paste_center(img, CAPS['small'], W / 2, 190)
    # quick flash cut out of the cold open, and a whip at the very end that lands on the cold open
    if beat == 1 and u < 0.08:
        img = Image.blend(img, Image.new('RGBA', img.size, (255, 255, 255, 255)), 0.7 * (1 - u / 0.08))
    if t >= DUR - 0.18:
        k = (t - (DUR - 0.18)) / 0.18
        moved = Image.new('RGBA', img.size, (0, 0, 0, 255)); moved.paste(img, (-int(500 * k * k), 0))
        img = moved.filter(ImageFilter.BoxBlur(int(2 + 20 * k)))
    return img.convert('RGB')

# ------------------------------------------------------------------ audio
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; out = np.zeros(n); add = m.add
    rng = np.random.default_rng(5)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    def ding(t0):
        add(out, m.tone(1318.5, 0.5, harm=((1, 1), (2.76, 0.2)), decay=7), t0, 0.22)
        add(out, m.tone(1760.0, 0.6, harm=((1, 1), (2.76, 0.2)), decay=7), t0 + 0.09, 0.2)
    def buzz(t0):
        for k in range(2):
            tt = tt_(0.12); add(out, m.lowpass(np.sign(np.sin(2 * np.pi * 150 * tt)), 400) * np.sin(np.pi * tt / 0.12), t0 + k * 0.15, 0.22)
    def wah(t0, notes, last=1.0, g=0.13):
        for k, fq in enumerate(notes):
            L_ = 0.34 if k < len(notes) - 1 else last; tt = tt_(L_)
            sig = np.sign(np.sin(2 * np.pi * fq * (1 + 0.01 * np.sin(2 * np.pi * 5 * tt)) * tt)) * 0.5 + np.sin(2 * np.pi * fq * tt)
            add(out, m.lowpass(sig, 1200) * np.minimum(1, tt / 0.03) * np.exp(-tt * (2 if k < len(notes) - 1 else 1.2)), t0 + k * 0.34, g)
    for i, b in enumerate(BEATS):
        t0 = T[i]; kind = b[8]
        if b[3]: ding(t0 + 0.02); buzz(t0)
        r = t0 + 0.3
        if kind == 'coldopen':                                   # hit on frame 1 + the sob
            tt = tt_(0.4); add(out, np.sin(2 * np.pi * np.cumsum(140 * np.exp(-tt * 7) + 45) / SR) * np.exp(-tt * 8), 0.0, 0.9)
            wah(0.05, (207.7, 196.0), last=0.5, g=0.12)
        elif kind == 'sus':                                      # suspicious "hmmm" + squeak
            tt = tt_(0.9); f = 220 + 25 * np.sin(2 * np.pi * 3 * tt)
            add(out, m.lowpass(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 900) * np.sin(np.pi * tt / 0.9) ** 2, r + 0.2, 0.12)
            tt = tt_(0.25); add(out, np.sin(2 * np.pi * np.cumsum(900 + 1400 * tt / 0.25) / SR) * np.sin(np.pi * tt / 0.25), t0 + 1.5, 0.12)
        elif kind == 'kettle':
            tt = tt_(0.3); add(out, np.sin(2 * np.pi * np.cumsum(160 * np.exp(-tt * 6) + 50) / SR) * np.exp(-tt * 9), t0 + 0.25, 0.7)
            L_ = 2.0; tt = tt_(L_); f = 2400 + 300 * np.minimum(1, tt / 0.4) + 60 * np.sin(2 * np.pi * 7 * tt)
            env = np.minimum(1, tt / 0.2) * np.minimum(1, (L_ - tt) / 0.2)
            add(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * env, r, 0.12)
            add(out, m.bandpass(nz(L_), 2000, 6000) * env, r, 0.05)
        elif kind == 'slap':
            add(out, m.highpass(nz(0.08), 1200) * np.exp(-tt_(0.08) * 60), t0 + 0.55, 0.7)
            tt = tt_(0.3); add(out, np.sin(2 * np.pi * np.cumsum(120 * np.exp(-tt * 5) + 50) / SR) * np.exp(-tt * 12), t0 + 0.55, 0.55)
            L_ = 1.0; tt = tt_(L_); add(out, m.bandpass(nz(L_), 400, 1800) * np.sin(np.pi * tt / L_) ** 2, t0 + 1.1, 0.2)
        elif kind == 'wahwah':
            wah(r + 0.1, (233.1, 220.0, 207.7, 196.0), last=1.3)
        if i > 0: add(out, m.bandpass(nz(0.12), 600, 5000) * np.sin(np.pi * tt_(0.12) / 0.12) ** 2, t0 - 0.06, 0.06)
    add(out, m.bandpass(nz(0.2), 500, 6000) * np.sin(np.pi * tt_(0.2) / 0.2) ** 2, DUR - 0.2, 0.1)
    out = out[:int(DUR * SR)]
    out /= np.max(np.abs(out)) / 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())

# ------------------------------------------------------------------ main
def beat_of(t):
    for i in range(len(BEATS)):
        if T[i] <= t < T[i + 1]: return i
    return len(BEATS) - 1

def main():
    global BG
    m.init_static(); BG = build_bg(); caps()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    cache = {}
    def cat_at(t):
        i = beat_of(t)
        if i not in cache:
            cache.clear(); b = BEATS[i]; cache[i] = read_frames(b[0], b[1], b[2])
        fr = cache[i]; k = min(len(fr) - 1, int((t - T[i]) * FPS))
        return key(fr[k]), i
    if mode == 'test':
        times = [float(x) for x in sys.argv[2:]]
        frames = []
        for tm in times:
            c, i = cat_at(tm); frames.append(compose(tm, c, i))
        tw, th = W // 3, H // 3; cols = min(4, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th)), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUT, 'react1_v2_contact.png')); print('ok', DUR); return
    wav = os.path.join(OUT, 'react1_v2_audio.wav'); build_audio(wav)
    mp4 = os.path.join(OUT, 'react1_v2.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(NF):
        t = k / FPS; c, i = cat_at(t)
        proc.stdin.write(compose(t, c, i).tobytes())
        if k % 90 == 0: print('frame', k, '/', NF, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
