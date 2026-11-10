#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 24: הבנק שלי: נציג אנושי — VOICED rebuild (10.11; Gabi 9.11: "למה הפרקים הבאים בלי קול?" →
"להחליף ימים ולדבב"). Same story, plant, break and the same ONE continuous camera move (experiment one_take) as the
silent v2 (ep24_v1.py, 12.4 s, FRAME0=1): this file re-times the v1 world onto the real voice lines through a
piecewise-linear time map (voiced t -> v1 time), flaps the cat's mouth (and Sharit's on the call screen) from the talk
envelopes, nods his head with his own speech, swaps the speech bubbles for speaker-coloured subtitles (cat white,
Sharit pink, the IVR light blue, y≈1450) and drops the speakerphone hold music (no music in voiced episodes).
No ◀◀ rewind: a rewind would be a cut, and the experiment is one take. The cold open IS frame 0: the paw tapping
9, 9, 0# on "תשע, תשע, אפס, סולמית!" (the plant).
Voices (voice bank 2026-11-09, Gabi's picks 9.11): 2400 cold open · 2401 IVR "מעבירה לנציג." · 2402 want ·
2403 IVR 47 · 2404 battery stake · (x64 inside the move, nervous 9-taps = plant again) · 2405 IVR "אחת" · 9102
"יאללה!" · ring · 2406 Sharit (peak) · 2703 "שרית?! גם פה?" · peak held (inhale, heartbeat) · break: his paw taps 9
out of habit → BEEP → 2408 IVR "חזרת לתפריט הראשי." in the last 2.5 s · frozen face, the camera settles back on
frame 0 (loop).

  python3 voice/ep24_prep.py            # once: voice/ep24/proc
  python3 ep24.py times | test t1 t2 ... | render
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import ep24_v1 as B
from make_video import W, H, K, FPS, S, lerp, clamp, ease_out, ease_in, ease_io, font, WHITE, INK

B.TRANSFER_TXT = 'מעבירה לנציג...'   # the IVR voice is female (2401 'מעבירה לנציג.')
B.bubbles = lambda frame, t: None          # no speech bubbles in the voiced cut (subtitles instead)
B.CAPTIONS = [c for c in B.CAPTIONS if c[0] in (0.0, 5.65)]   # hook + the "12... 3... 2..." countdown (no voice there)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep24', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {i: META[i]['dur'] for i in META}
PINKSUB = (255, 182, 210); IVRSUB = (160, 214, 255)
OUTNAME = os.environ.get('OUTNAME', 'ep24_human_v3')
SPEAKER = {0: 'cat', 1: 'ivr', 2: 'cat', 3: 'ivr', 4: 'cat', 5: 'ivr', 102: 'cat', 6: 'sh', 27: 'cat', 8: 'ivr'}

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
L[0] = 0.0
w = [L[0] + seg_start(0, k) for k in range(4)]                 # תשע · תשע · אפס · סולמית
P += [(0.0, 0.0), (w[0], B.TAPS0[0]), (w[1], B.TAPS0[1]), (w[2], B.TAPS0[2]), (w[3], 0.95), (L[0] + D[0], 1.15)]
L[1] = L[0] + D[0] + 0.06
P += [(L[1] + 0.02, B.CHK1), (L[1] + D[1], 1.32)]
L[2] = L[1] + D[1] + GAP
P += [(L[2] + D[2], 1.97)]
L[3] = L[2] + D[2] + GAP
P += [(L[3] - 0.02, B.QSTART - 0.01), (L[3], B.QSTART), (L[3] + D[3], 2.9)]
L[4] = L[3] + D[3] + GAP
P += [(L[4] + D[4], 3.5)]
t_chk2 = L[4] + D[4] + 1.25                                    # x64 inside the move: 47 -> 12, nervous 9-taps (plant)
P += [(t_chk2, B.CHK2), (t_chk2 + 0.5, 6.2)]
L[5] = t_chk2 + 0.55
t_one = L[5] + seg_start(5, 1)                                 # "אחת" = the 1 tick
P += [(t_one, B.CHK3), (L[5] + D[5], 7.75)]
L[102] = L[5] + D[5] + GAP
P += [(L[102] + D[102], 8.1)]
t_ring = L[102] + D[102] + 0.85
P += [(t_ring, B.RING[0])]
L[6] = t_ring + 0.95
P += [(L[6] - 0.02, B.HELLO[0] - 0.01), (L[6], B.HELLO[0]), (L[6] + D[6], 10.75)]
L[27] = L[6] + D[6] + GAP
tpk = L[27] + D[27] + 0.05
P += [(tpk, B.PEAK[0])]
TAPB = tpk + 0.55                                              # the peak held 0.55 s (inhale + heartbeat)
TB = TAPB + 0.08
P += [(TAPB, B.TAPB), (TB, B.BEEP)]
L[8] = TB + 0.14
P += [(L[8] - 0.02, B.FREEZE[0])]
DUR = round(L[8] + D[8] + 0.42, 2)                             # freeze ≤ 0.5 s after the break line
P += [(DUR, B.DUR - 0.01)]
NF = int(round((float(os.environ.get('LIMIT', '0')) or DUR) * FPS))
OCC = [(k, L[k]) for k in (0, 1, 2, 3, 4, 5, 102, 6, 27, 8)]

def ts_of(t):
    if t <= P[0][0]: return P[0][1]
    for (a, x), (b, y) in zip(P, P[1:]):
        if a <= t < b: return x + (y - x) * (t - a) / (b - a)
    return P[-1][1]

def t_of(ts):
    for (a, x), (b, y) in zip(P, P[1:]):
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

# ------------------------------------------------------------------ mouth + speech nods on the v1 cat, Sharit's mouth on the call screen
CUR = {'t': 0.0}
EXPR = os.environ.get('EXPR', '0') == '1'
POSES = [dict(lid=0.0, pupil='tiny', brow='up', ear_dy=-26, look=(-22, 4), blush=0.0, sweat=1.0),
         dict(lid=0.0, pupil='big', brow='annoyed', ear_dy=-14, look=(-26, -6), blush=0.0),
         dict(lid=0.0, pupil='big', brow='up', ear_dy=-22, look=(-8, -10), blush=0.6),
         dict(lid=0.1, pupil='big', brow='sad', ear_droop=0.6, look=(18, 18), blush=0.0)]
LOUD = {0: 'w', 2: 'smile', 4: 'w', 102: 'smile', 27: 'w'}
_cat_state = B.cat_state
def cat_state(ts, i):
    st, rot, dy, puff = _cat_state(ts, i)
    t = CUR['t']
    v, li = v_of(t, 'cat')
    if li is not None:
        if v > 0.32: st['mouth'] = LOUD.get(li, 'w')
        elif v > 0.12: st['mouth'] = 'smile_small' if li in (2, 102) else 'w'
        else: st['mouth'] = 'flat' if li in (0, 4) else st.get('mouth', 'flat')
        dy += -10 * v; rot += 2.5 * v * math.sin(t * 7)
        if li == 4: st.update(brow='sad', pupil='big', sweat=1.0, look=(-28, 10))          # eyes on the battery
        if EXPR and li in (0, 2, 3, 4):                                                    # gate probe: a new big pose on every voiced phrase
            segs = [a for a, _ in SEG[li]]; s0 = dict(OCC)[li]
            k = sum(1 for a in segs if t - s0 >= a - 0.05)
            u = t - s0 - (segs[k - 1] if k else 0)
            st.update(POSES[(k + li) % len(POSES)])
            rot += 7 * math.exp(-u * 5) * math.sin(u * 20); dy += -18 * math.exp(-u * 7) * math.cos(u * 22)
        if li == 27: st.update(pupil='tiny', brow='up', ear_dy=-30, blush=0.0)            # "שרית?! גם פה?"
    if li is None and speaking(t) and SPEAKER[speaking(t)[0]] == 'ivr' and ts >= B.BEEP:
        pass                                                                               # frozen through the IVR line
    return st, rot, dy, puff
B.cat_state = cat_state

_phone_layer = B.phone_layer
def phone_layer(ts):
    lay = _phone_layer(ts)
    v, li = v_of(CUR['t'], 'sh')
    if li is not None and B.screen_mode(ts) == 'call' and v > 0.1:
        d = ImageDraw.Draw(lay); cx = B.PW / 2
        d.ellipse([S(cx - 14), S(268), S(cx + 14), S(268 + 6 + 18 * v)], fill=(110, 24, 40), outline=(206, 44, 72), width=m.iw(3))
    v2, li2 = v_of(CUR['t'], 'ivr')
    if li2 is not None and v2 > 0.1:                                                       # the IVR "speaks": the speaker grille pulses
        d = ImageDraw.Draw(lay)
        for k in range(3):
            r = 18 + 12 * k + 10 * v2
            d.arc([S(36 - r), S(64 - r), S(36 + r), S(64 + r)], -40, 40, fill=(220, 226, 240), width=m.iw(3))
    return lay
B.phone_layer = phone_layer

# ------------------------------------------------------------------ subtitles (plain text = the manifest text)
SUBS = {
    0: [['תשע, תשע,'], ['אפס, סולמית!']],
    1: [['מעבירה לנציג.']],
    2: [['הטריק עובד!'], ['בן אדם אמיתי, אני בא.']],
    3: [['מיקומך בתור:'], ['ארבעים ושבע.']],
    4: [['שלושה אחוז סוללה...'], ['תחזיקי מעמד.']],
    5: [['מיקומך בתור: אחת.']],
    102: [['יאללה!']],
    6: [['שלום, מדברת שרית...'], ['במה אפשר לעזור, מותק?']],
    27: [['שרית?! גם פה?']],
    8: [['חזרת לתפריט הראשי.']],
}
SPLIT = {0: [0, 2], 2: [0, 1], 3: [0, 1], 4: [0, 1], 6: [0, 1]}    # chunk k starts at voiced segment SPLIT[i][k]
SUB_TIMES = []
for li, s0 in OCC:
    ch = SUBS[li]; ks = SPLIT.get(li, [0])
    starts = [0.0] + [seg_start(li, ks[k]) for k in range(1, len(ch))]
    for k, c in enumerate(ch):
        a = s0 + max(0.0, starts[k] - 0.05); b = s0 + (starts[k + 1] - 0.05 if k + 1 < len(ch) else D[li] + 0.15)
        nxt = [s for _, s in OCC if s > s0 + 0.01]
        if nxt: b = min(b, nxt[0] - 0.03)
        SUB_TIMES.append((a, b, c, li))
SUB_Y = int(os.environ.get('SUBY', '1450'))

def sub_layer(lines, fill, size=64):
    f = font(size, 900); lh = size * 1.14
    h = int(lh * len(lines) + size * 0.6); im = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        s = size
        while d.textlength(ln, font=font(s, 900)) > W - 120 and s > 40: s -= 2
        d.text((W / 2, size * 0.3 + lh * (k + 0.5)), ln, font=font(s, 900), fill=fill, anchor='mm',
               stroke_width=max(6, int(s * 0.12)), stroke_fill=(10, 10, 12))
    return im

def draw_frame(i):
    t = i / FPS; CUR['t'] = t
    ts = ts_of(t)
    img = B.draw_world(ts, i)
    z, ccx, ccy = B.camera(ts)
    cw, ch = W * K / z, H * K / z
    left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
    img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    frame.alpha_composite(m.VIG)
    if B.FF[0] <= ts < B.FF[1]: B.ff_overlay(frame)
    if B.PEAK[0] <= ts < B.BEEP:
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - tpk) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(40 * k))))
    for s_ in (B.TAPS0[0], B.CHK1, B.CHK2, B.CHK3, B.BEEP):
        tv = t_of(s_)
        if tv <= t < tv + 0.06:
            frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(100 * (1 - (t - tv) / 0.06)))))
    for t0, t1, lines, size, yc, fill in B.CAPTIONS:
        if t0 <= ts < t1:
            u = t - t_of(t0); sc = 1 + 0.25 * math.exp(-u * 12) * math.cos(u * 20)
            if t0 == 0.0: sc = 1.0
            cap = m.caption_layer(lines, size, fill)
            if abs(sc - 1) > 0.004:
                cap = cap.resize((max(1, int(cap.width * sc)), max(1, int(cap.height * sc))), Image.BICUBIC)
            m.paste_center(frame, cap, W / 2, yc)
    B.meter(frame, ts)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            col = {'sh': PINKSUB, 'ivr': IVRSUB}.get(SPEAKER[li], WHITE)
            m.paste_center(frame, sub_layer(lines, col), W / 2, SUB_Y)
    if ts < 2.0:
        frame.alpha_composite(B.PILL_EP, (40, 70)); frame.alpha_composite(B.PILL_Q, (W - 40 - B.PILL_Q.width, 70))
    elif ts >= B.FREEZE[0] and int(t * 10) % 3 != 0:
        frame.alpha_composite(B.PILL_Q, (W - 40 - B.PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio: voices + SFX on the voiced clock (no music, no hold music)
SR = m.SR
def build_audio(path):
    n = int(DUR * SR) + SR; sfx = np.zeros(n); vox = np.zeros(n); add = m.add
    rng = np.random.default_rng(243)
    nz = lambda d_: rng.standard_normal(int(d_ * SR))
    tt_ = lambda d_: np.arange(int(d_ * SR)) / SR
    def thump(t0, g=0.8):
        tt = tt_(0.4); f = 150 * np.exp(-tt * 9) + 45; add(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9), t0, g)
    def pop(t0, g=0.22):
        tt = tt_(0.12); f = 300 + 900 * np.exp(-tt * 40); add(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30), t0, g)
    def dtmf(t0, lo=852, hi=1477, g=0.16, d_=0.11):
        tt = tt_(d_); env = np.minimum(1, np.minimum(tt / 0.005, (d_ - tt) / 0.01))
        add(sfx, (np.sin(2 * np.pi * lo * tt) + np.sin(2 * np.pi * hi * tt)) * 0.5 * env, t0, g)
    def murmur(t0, t1, g):
        d_ = t1 - t0; tt = tt_(d_)
        mod = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 1.7 * tt + 1))
        env = np.minimum(1, np.minimum(tt / 0.08, (d_ - tt) / 0.08)); add(sfx, m.bandpass(nz(d_), 250, 2200) * mod * env, t0, g)
    def check(t0, g=0.12, base=523.3):
        for k_, f_ in enumerate((base, base * 1.26, base * 1.5)): add(sfx, m.tone(f_, 0.22, harm=((1, 1), (2, 0.3)), decay=7), t0 + 0.07 * k_, g)
    def applause(t0, t1, g):
        tc = t0; r = random.Random(5)
        while tc < t1:
            add(sfx, m.bandpass(nz(0.03), 1200, 6000) * np.exp(-tt_(0.03) * 120), tc, g * r.uniform(0.5, 1.0)); tc += r.uniform(0.015, 0.045)
    def whoosh(t0, wl=0.3, g=0.25):
        wt = tt_(wl); add(sfx, m.bandpass(nz(wl), 700, 6000) * np.sin(np.pi * wt / wl) ** 2 * (wt / wl), t0, g)
    murmur(0.0, tpk - 0.1, 0.06)
    for k_, f_ in enumerate((659.3, 784.0, 987.8)):                  # soft menu chime under frame 0
        add(sfx, m.tone(f_, 0.2, harm=((1, 1),), decay=8), 0.02 + 0.1 * k_, 0.04)
    thump(w[0], 0.5)
    dtmf(w[0], 852, 1477); dtmf(w[1], 852, 1477); dtmf(w[2], 941, 1336); dtmf(w[3], 941, 1633, 0.12)   # 9 · 9 · 0 · #
    thump(t_of(B.CHK1), 0.4); check(t_of(B.CHK1), 0.13)
    pop(L[2] + 0.05, 0.14)
    add(sfx, m.bandpass(nz(0.5), 600, 5000) * np.linspace(0, 1, int(0.5 * SR)), t_of(B.FF[0]) - 0.25, 0.07)   # riser into x64
    tc = t_of(B.FF[0])                                                # x64: fast blips instead of the hold music
    while tc < t_of(B.FF[1]):
        add(sfx, m.tone(1200 + 200 * math.sin(tc * 9), 0.03, harm=((1, 1),), decay=40), tc, 0.025); tc += 0.07
    for x in B.TAPS_MID: dtmf(t_of(x), g=0.08, d_=0.06)               # nervous taps (plant)
    thump(t_of(B.CHK2), 0.45); check(t_of(B.CHK2), 0.13, 587.3)
    for k_, (tc_, _) in enumerate(B.TICKS): pop(t_of(tc_), 0.2 + 0.05 * k_); thump(t_of(tc_), 0.25 + 0.1 * k_)
    check(t_of(B.CHK3), 0.16, 659.3); applause(t_of(B.CHK3) + 0.05, t_ring - 0.1, 0.07)
    for k_ in range(6): pop(t_of(B.CHK3) + 0.05 + 0.11 * k_, 0.08)
    tc = t_ring
    while tc < L[6] - 0.1:                                            # ringback through the speaker
        L_ = min(0.32, L[6] - 0.1 - tc); tt = tt_(L_)
        add(sfx, m.phone_line((np.sin(2 * np.pi * 425 * tt)) * 0.7), tc, 0.12); tc += 0.5
    whoosh(t_ring - 0.1, 0.25, 0.12)
    pop(L[6], 0.18)
    add(sfx, m.bandpass(nz(0.35), 300, 3000) * np.linspace(0, 1, int(0.35 * SR)) ** 2, tpk, 0.06)   # the inhale
    for hb in (tpk + 0.02, tpk + 0.5): thump(hb, 0.32); thump(hb + 0.16, 0.22)
    dtmf(TAPB, g=0.22)                                                # the habit tap: 9
    thump(TB, 0.95); add(sfx, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), TB, 0.5)
    for k_, f_ in enumerate((987.8, 784.0, 523.3)):
        add(sfx, m.tone(f_, 0.14, harm=((1, 1),), decay=10), TB + 0.03 + 0.09 * k_, 0.12)
    murmur(TB + 0.05, DUR, 0.025)
    sfx += m.lowpass(nz(len(sfx) / SR), 300) * 0.006
    for li, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{li:03d}.npy')).astype(np.float64)
        if SPEAKER[li] in ('ivr', 'sh'): y = m.phone_line(y) * 1.6               # through the phone speaker
        add(vox, y, s0, 1.0)
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
    tag = os.environ.get('TAG', '')
    if mode == 'times':
        print('DUR', DUR, 'chk2', round(t_chk2, 2), 'one', round(t_one, 2), 'ring', round(t_ring, 2), 'peak', round(tpk, 2), 'break', round(TB, 2))
        for k, v in L.items(): print(' line', k, round(v, 2), '-', round(v + D[k], 2))
        return
    if mode == 'audio': build_audio(sys.argv[2]); print('ok'); return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(NF - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, f'ep24{tag}_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'ep24{tag}_audio.wav'); build_audio(wav); print('audio ok')
    mp4 = os.path.join(OUTDIR, f'{OUTNAME}{tag}.mp4')
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
