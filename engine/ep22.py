#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 22: הבנק שלי: הפרטים דלפו — VOICED rebuild (14.11; Gabi 13.11: "לדובב הכל מדובב").
Same story, plant, break and shots as the silent v2 (ep22_v1.py, 13.05 s, FRAME0=1): this file re-times the v1 world onto
the real voice lines through a piecewise-linear time map (voiced t -> v1 time, like ep24.py), flaps the cat's mouth from
the talk envelope (Sharit talks while she speaks), drops the speech bubbles for speaker-coloured subtitles (cat white,
Sharit pink, y≈1450) and builds the audio on the voiced clock: voices + SFX + branch murmur, no music.
Voiced §P shape: cold open = 2205 "קוד? לא מוסרים!" (the loudest line of the climb; the plant bag "קוד: 4821" is in his
paw in that shot) → ◀◀ "רגע קודם" (the v1 clock literally runs backwards to frame 0) → 2200 want (the scam SMS slams on)
→ 2201 "ללחוץ כאן? מוחק." ✓ → 2202 he calls the real number → ring → 2203/2204 Sharit ✓ → 2205 ✓ gold → 2206
"לקוח זהיר! כל הכבוד, מותק." sticker + applause → 2207 "הקוד שלי? רק אני יודע." cheer → 2208 "סוף סוף... חשבון מוגן."
(peak, bag on the counter) → held 0.55 s (hush + heartbeat) → 2209 Sharit takes the bag and reads "ארבע, שמונה, שתיים,
אחת. תודה, מותק." → STAMP "אומת" on "תודה" → frozen face ≤0.5 s → whip into the cold open (loop).
9104 is not used: after the break only the frozen face (§P; experiment ending_on_sharit = the episode ends on her punch).

  python3 voice/ep22_prep.py            # once: voice/ep22/proc
  python3 ep22.py times | test t1 t2 ... | render   -> out/ep22_leak_v3.mp4
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep22_v1 as B
from make_video import W, H, K, FPS, S, lerp, clamp, ease_out, ease_in, ease_io, font, WHITE, INK

SH.bubble = lambda *a, **k: None          # no speech bubbles in the voiced cut (subtitles instead)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep22', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {i: META[i]['dur'] for i in META}
PINKSUB = (255, 182, 210)
OUTNAME = os.environ.get('OUTNAME', 'ep22_leak_v3')
SPEAKER = {0: 'cat', 1: 'cat', 2: 'cat', 3: 'sh', 4: 'sh', 5: 'cat', 6: 'sh', 7: 'cat', 8: 'cat', 9: 'sh'}

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
def seg_start(i, k):
    s = SEG[i]
    return s[k][0] if k < len(s) else D[i] * (k / max(1, len(s)))

# ------------------------------------------------------------------ timeline (voiced t) and the map to v1 time
GAP = 0.08
L = {}; P = []
COLD_END = round(D[5] + 0.06, 2)                               # cold open: 2205 replayed
P += [(0.0, B.REFUSE[0]), (seg_start(5, 1), B.CHK3), (COLD_END - 0.02, 5.33)]
RW = (COLD_END, COLD_END + 0.28)                               # ◀◀ the v1 clock runs backwards to frame 0
T0 = RW[1]
P += [(RW[0], 5.3), (T0, 0.0)]
L[0] = T0 + 0.04                                               # "חשבונך ייחסם? הפעם לא עובדים עליי."
P += [(L[0] + 0.06, B.SLAM + 0.02), (L[0] + seg_start(0, 1), B.SUSP), (L[0] + D[0], 1.25)]
L[1] = L[0] + D[0] + GAP                                       # "ללחוץ כאן? מוחק."
P += [(L[1], 1.27), (L[1] + seg_start(1, 1), B.SWIPE), (L[1] + D[1], 1.9)]
L[2] = L[1] + D[1] + GAP                                       # "מתקשר לבנק בעצמי. למספר האמיתי."
P += [(L[2], 1.92), (L[2] + seg_start(2, 1) - 0.05, 2.30), (L[2] + D[2], 2.52)]
t_ring = L[2] + D[2]
L[3] = t_ring + 0.5                                            # ring, then "הבנק שלי, שרית."
P += [(L[3] - 0.02, B.PICK - 0.01), (L[3], B.PICK), (L[3] + D[3], 3.54)]
L[4] = L[3] + D[3] + GAP                                       # "מה הקוד שלך, מותק?"
P += [(L[4], 3.56), (L[4] + D[4], 4.08)]
L[5] = L[4] + D[4] + 0.14                                      # "קוד? לא מוסרים!"
P += [(L[5], B.REFUSE[0]), (L[5] + seg_start(5, 1), B.CHK3), (L[5] + D[5], 5.35)]
L[6] = L[5] + D[5] + 0.30                                      # applause, "לקוח זהיר! כל הכבוד, מותק."
P += [(L[5] + D[5] + 0.08, B.CLAP), (L[6], B.STICK - 0.05), (L[6] + D[6], 7.55)]
L[7] = L[6] + D[6] + GAP                                       # cheer: "הקוד שלי? רק אני יודע."
P += [(L[7], B.CHEER[0] + 0.02), (L[7] + D[7], 9.15)]
L[8] = L[7] + D[7] + 0.42                                      # bag down, "סוף סוף... חשבון מוגן." (peak line)
P += [(L[8] - 0.02, 9.62), (L[8] + D[8], 11.15)]
HOLD = (L[8] + D[8] + 0.03, L[8] + D[8] + 0.58)                # the peak held 0.55 s
P += [(HOLD[0], B.PEAK[0]), (HOLD[1], B.PEAK[1])]
L[9] = HOLD[1] + 0.32                                          # she takes the bag, reads the code
P += [(L[9] - 0.02, B.READ[0] - 0.01)]
BREAK_T = L[9] + seg_start(9, 4) - 0.02                        # "תודה, מותק." = STAMP "אומת"
P += [(BREAK_T, B.STAMP)]
FREEZE_T = L[9] + D[9]
DUR = round(FREEZE_T + 0.45, 2)
P += [(FREEZE_T, 12.62), (DUR, B.DUR - 0.02)]
NF = int(round((float(os.environ.get('LIMIT', '0')) or DUR) * FPS))
OCC = [(5, 0.0)] + [(k, L[k]) for k in range(10)]
NEXT = {}
for k_, (li, s0) in enumerate(OCC):
    NEXT[(li, s0)] = OCC[k_ + 1][1] if k_ + 1 < len(OCC) else DUR

def ts_of(t):
    if t <= P[0][0]: return P[0][1]
    for (a, x), (b, y) in zip(P, P[1:]):
        if a <= t < b: return x + (y - x) * (t - a) / (b - a) if b > a else y
    return P[-1][1]

def t_of(ts):
    """voiced time of a v1 time (after the rewind)"""
    for (a, x), (b, y) in zip(P, P[1:]):
        if a < T0: continue
        if x <= ts <= y and y > x: return a + (b - a) * (ts - x) / (y - x)
    return P[-1][0]

def speaking(t):
    for li, s0 in OCC:
        if s0 <= t < s0 + D[li]: return li, s0
    return None

def v_of(t, who):
    sp = speaking(t)
    if not sp or SPEAKER[sp[0]] != who: return 0.0, None
    li, s0 = sp; env = META[li]['env']; k = int((t - s0) * FPS)
    return (env[k] if k < len(env) else 0.0), li

# ------------------------------------------------------------------ mouths on the v1 characters
CUR = {'t': 0.0}
LOUD = {0: 'w', 1: 'w', 2: 'w', 5: 'w', 7: 'smile', 8: 'smile'}
def _cat_wrap(fn):
    def wrapped(ts, i):
        st, rot, dy = fn(ts, i)
        v, li = v_of(CUR['t'], 'cat')
        if li is not None:
            if v > 0.32: st['mouth'] = LOUD.get(li, 'w')
            elif v > 0.12: st['mouth'] = 'smile_small' if li in (7, 8) else 'w'
            dy += -10 * v; rot += 2.5 * v * math.sin(CUR['t'] * 7)
        return st, rot, dy
    return wrapped
B.cat_state_close = _cat_wrap(B.cat_state_close)
B.cat_state_two = _cat_wrap(B.cat_state_two)

_sh_state = B.sh_state
def sh_state(ts, i):
    st, rot = _sh_state(ts, i)
    v, li = v_of(CUR['t'], 'sh')
    if li is not None:
        st['mouth'] = 'talk' if v > 0.12 else ('munch' if li == 9 else 'lazy')
    elif st.get('mouth') == 'talk':
        st['mouth'] = 'grin' if ts >= B.CLAP else 'lazy'
    return st, rot
B.sh_state = sh_state

# ------------------------------------------------------------------ subtitles (plain text = the manifest text)
SUBS = {
    0: [['חשבונך ייחסם?'], ['הפעם לא עובדים עליי.']],
    1: [['ללחוץ כאן?'], ['מוחק.']],
    2: [['מתקשר לבנק בעצמי.'], ['למספר האמיתי.']],
    3: [['הבנק שלי, שרית.']],
    4: [['מה הקוד שלך, מותק?']],
    5: [['קוד?'], ['לא מוסרים!']],
    6: [['לקוח זהיר!'], ['כל הכבוד, מותק.']],
    7: [['הקוד שלי?'], ['רק אני יודע.']],
    8: [['סוף סוף...'], ['חשבון מוגן.']],
    9: [['ארבע, שמונה,'], ['שתיים, אחת.'], ['תודה, מותק.']],
}
SPLIT = {0: [0, 1], 1: [0, 1], 2: [0, 1], 5: [0, 1], 6: [0, 2], 7: [0, 1], 8: [0, 1], 9: [0, 2, 4]}
SUB_TIMES = []
for li, s0 in OCC:
    ch = SUBS[li]; ks = SPLIT.get(li, [0])
    starts = [0.0] + [seg_start(li, ks[k]) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.2)
        b = min(b, NEXT[(li, s0)] - 0.03)
        if s0 == 0.0: b = min(b, COLD_END)
        if li == 9 and k == len(ch) - 1: b = DUR - 0.25          # her punch stays up through the freeze
        SUB_TIMES.append((a, b, c, li))
SUB_Y = int(os.environ.get('SUBY', '1450'))
SUB_Y2 = int(os.environ.get('SUBY2', '1290'))   # two-shots: above the counter, the bag and the sticker
HOOK = ['הודעה מהבנק שלי', 'שהחשבון ייחסם?']
CAPS = [(0.0, COLD_END, HOOK), (T0, L[2] + seg_start(2, 1), HOOK)]

def sub_layer(lines, fill, size=64):
    f = font(size, 900); lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

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

def draw_frame(i):
    t = i / FPS; CUR['t'] = t
    ts = ts_of(t)
    name, a, b = B.shot(ts)
    img = {'two': B.scene_two, 'cat': B.scene_cat}[name](ts, i)
    z, ccx, ccy = B.camera(ts)
    if t < 0.3: z = max(z, 1.18 - 0.18 * ease_out(t / 0.3))          # frame 0: snap pull-back, already moving
    if t < 0.45:                                                       # cold-open impact shake
        r_ = random.Random(i); sh_ = 22 * math.exp(-t * 6); ccx += r_.uniform(-sh_, sh_); ccy += r_.uniform(-sh_, sh_); z = max(z, 1.03)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if HOLD[0] <= t < L[9]:                                   # the held beat: hush, heartbeat pulse
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - HOLD[0]) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(36 + 30 * k))))
    for s_ in (t_of(B.SLAM), t_of(B.CHK1), t_of(B.PICK), t_of(B.CHK3), t_of(B.STICK), BREAK_T):
        if s_ <= t < s_ + 0.06:
            frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - s_) / 0.06)))))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if t >= DUR - 0.25:                                       # whip out -> loops into the cold open
        k_ = (t - (DUR - 0.25)) / 0.25
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    for t0, t1, lines in CAPS:
        if t0 <= t < t1:
            m.paste_center(frame, m.caption_layer(lines, 96, WHITE), W / 2, 290)
    if not (B.GRAB <= ts < B.STAMP):
        B.meter(frame, ts)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            m.paste_center(frame, sub_layer(lines, PINKSUB if SPEAKER[li] == 'sh' else WHITE), W / 2, SUB_Y if name == 'cat' else SUB_Y2)
    if t < L[2]:
        frame.alpha_composite(B.PILL_EP, (40, 70)); frame.alpha_composite(B.PILL_Q, (W - 40 - B.PILL_Q.width, 70))
    elif t >= FREEZE_T and int(t * 10) % 3 != 0:
        frame.alpha_composite(B.PILL_Q, (W - 40 - B.PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio: voices + SFX on the voiced clock (no music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; sfx = np.zeros(n); vox = np.zeros(n); add = m.add
    rng = np.random.default_rng(222)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    def thump(t0, g=0.8):
        tt = tt_(0.4); f = 150 * np.exp(-tt * 9) + 45; add(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9), t0, g)
    def pop(t0, g=0.22):
        tt = tt_(0.12); f = 300 + 900 * np.exp(-tt * 40); add(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30), t0, g)
    def whoosh(t0, wl=0.3, g=0.25):
        wt = tt_(wl); add(sfx, m.bandpass(nz(wl), 700, 6000) * np.sin(np.pi * wt / wl) ** 2 * (wt / wl), t0, g)
    def murmur(t0, t1, g):
        d_ = t1 - t0; tt = tt_(d_)
        mod = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 1.7 * tt + 1))
        env = np.minimum(1, np.minimum(tt / 0.08, (d_ - tt) / 0.08)); add(sfx, m.bandpass(nz(d_), 250, 2200) * mod * env, t0, g)
    def ding(t0, g=0.2):
        for k_, f_ in enumerate((1318.5, 1760.0)): add(sfx, m.tone(f_, 0.35, harm=((1, 1), (2, 0.2)), decay=7), t0 + 0.09 * k_, g)
    def check(t0, g=0.12, base=523.3):
        for k_, f_ in enumerate((base, base * 1.26, base * 1.5)): add(sfx, m.tone(f_, 0.22, harm=((1, 1), (2, 0.3)), decay=7), t0 + 0.07 * k_, g)
    def applause(t0, t1, g):
        tc = t0; r = random.Random(5)
        while tc < t1:
            add(sfx, m.bandpass(nz(0.03), 1200, 6000) * np.exp(-tt_(0.03) * 120), tc, g * r.uniform(0.5, 1.0)); tc += r.uniform(0.015, 0.045)
    thump(0.0, 0.9); add(sfx, m.highpass(nz(0.06), 1500) * np.exp(-tt_(0.06) * 60), 0.0, 0.4)      # cold open: impact
    check(seg_start(5, 1), 0.10, 659.3)
    rl = RW[1] - RW[0]; tr = tt_(rl)                                                                # rewind tape
    fr_ = 300 + 1600 * (tr / rl) + 260 * np.sign(np.sin(2 * np.pi * 11 * tr))
    add(sfx, m.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(fr_) / SR)) * 0.6 + 0.4 * nz(rl), 400, 6000) * np.sin(np.pi * tr / rl), RW[0], 0.16)
    murmur(0.0, HOLD[0] - 0.1, 0.06)
    ts_slam = t_of(B.SLAM); thump(ts_slam, 0.6); ding(ts_slam, 0.2)
    whoosh(t_of(B.SWIPE) - 0.05, 0.22, 0.3); thump(t_of(B.CHK1), 0.35); check(t_of(B.CHK1), 0.12)
    for tc in (2.3, 4.1, 5.4, 7.6, 9.2): whoosh(t_of(tc) - 0.08, 0.16, 0.08)
    td = t_of(B.DIAL)
    for k_ in range(3): add(sfx, m.tone(697 + 120 * k_, 0.07, harm=((1, 1), (1.7, 0.6)), decay=1), td + 0.06 + 0.07 * k_, 0.08)
    tc = t_ring + 0.02
    while tc < L[3] - 0.04:
        tt = tt_(0.04); add(sfx, np.sin(2 * np.pi * 950 * tt) * np.sign(np.sin(2 * np.pi * 25 * tt)) * 0.6, tc, 0.12); tc += 0.05
    pop(L[3] - 0.02, 0.22); check(t_of(B.CHK2), 0.12, 587.3)
    thump(t_of(B.CHK3), 0.4); check(t_of(B.CHK3), 0.15, 659.3)
    applause(t_of(B.CLAP), L[7] - 0.1, 0.05)
    thump(t_of(B.STICK), 0.5); check(t_of(B.STICK) + 0.05, 0.14, 784.0)
    applause(L[7], L[7] + D[7], 0.07)
    for k_ in range(6): pop(L[7] + 0.05 + 0.11 * k_, 0.07)
    tb = t_of(B.BAGDOWN); thump(tb, 0.35); add(sfx, m.highpass(nz(0.12), 2500) * np.exp(-tt_(0.12) * 20), tb, 0.1)
    for hb in (HOLD[0] + 0.02, HOLD[0] + 0.3): thump(hb, 0.32); thump(hb + 0.14, 0.22)
    tg = t_of(B.GRAB + 0.2); add(sfx, m.highpass(nz(0.12), 2500) * np.exp(-tt_(0.12) * 20), tg, 0.12)
    tc = tg + 0.15
    while tc < BREAK_T - 0.05:                                                                       # munch under her reading
        add(sfx, m.bandpass(nz(0.07), 1500, 7000) * np.exp(-tt_(0.07) * 45), tc, 0.08); tc += 0.26
    thump(BREAK_T, 0.95); add(sfx, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), BREAK_T, 0.6)   # THUNK "אומת"
    add(sfx, m.tone(82.4, 1.0, harm=((1, 1), (2, 0.6), (3, 0.4)), decay=2.4), BREAK_T + 0.02, 0.22)
    murmur(L[9], DUR, 0.025)
    whoosh(DUR - 0.28, 0.3, 0.12)
    sfx += m.lowpass(nz(len(sfx) / SR), 300) * 0.006
    for li, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{li:03d}.npy')).astype(np.float64)
        add(vox, y, s0, 0.95 if SPEAKER[li] == 'cat' else 0.9)
    sfx /= (np.max(np.abs(sfx)) + 1e-9) / 0.42
    vox /= (np.max(np.abs(vox)) + 1e-9) / 0.9
    out = (sfx + vox)[:int(DUR * SR)]
    out /= max(1.0, np.max(np.abs(out)) / 0.95)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())

def init_all(): B.init_all()
def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if mode == 'times':
        print('DUR', DUR, 'COLD_END', COLD_END, 'T0', T0, 'HOLD', [round(x, 2) for x in HOLD], 'BREAK', round(BREAK_T, 2), 'FREEZE', round(FREEZE_T, 2))
        for k, v in L.items(): print(' line', k, round(v, 2), '-', round(v + D[k], 2))
        for x in ('SLAM', 'CHK1', 'PICK', 'CHK2', 'CHK3', 'STICK', 'BAGDOWN', 'GRAB'): print(' ', x, round(t_of(getattr(B, x)), 2))
        return
    if mode == 'audio': build_audio(sys.argv[2]); print('ok'); return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, os.environ.get('SHEET', 'ep22_contact.png'))); print('ok'); return
    wav = os.path.join(OUTDIR, f'{OUTNAME}_audio.wav'); build_audio(wav); print('audio ok')
    mp4 = os.path.join(OUTDIR, f'{OUTNAME}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=_init_worker) as pool:
        for k, buf in enumerate(pool.imap(_render, range(NF), chunksize=4)):
            proc.stdin.write(buf)
            if k % 90 == 0: print('frame', k, '/', NF, flush=True)
    proc.stdin.close(); proc.wait(); print('done', mp4, DUR)

if __name__ == '__main__':
    main()
