#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 31: כרטיס המועדון שלי עובר חברה — VOICED rebuild (7.11; Gabi 6.11: every episode from 29 voiced).
Same story, plant (the grey 4th line "דמי כרטיס · 1 ₪ · מהכרטיס הישן") and break (plant_payoff: SNIP → "חיוב נדחה") as the
silent v1 (ep31_v1.py, 12.25 s). Built like ep29 v2: a piecewise-linear time map voiced t -> v1 time, talk-envelope mouths,
subtitles instead of the speech bubbles (the experiment's on-screen send line "2 כרטיסים. 3 הוראות קבע." stays as a bubble),
cold open = 3100 "חשמל, סלולר, ארנונה. הכול עבר!" on the stamp moment, tight on his face with the ticked form (the grey plant
line in shot), ◀◀ "רגע קודם", no music, whip back into the cold open.
Voices: 3100 cold · 3101 want · 9103 "יש!!!" at the board · 2703 · 3102 · 3103 (stamp on "הועבר!") · 3104 · 3105 "ביי, כרטיס."
(peak lead-in) · break = SNIP + red phone, then 3106 "חיוב נדחה?! על שקל אחד?!" · freeze → whip.

  python3 voice/ep31_prep.py ; python3 ep31.py times | test t1 t2 ... | render
"""
import json, math, os, sys, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import make_video as m
import sharit as SH
import ep31_v1 as B
from make_video import W, H, K, FPS, S, lerp, clamp, ease_out, ease_in, font, WHITE

B.CAPTIONS = []                    # hook drawn here; the rest is spoken
_bubble = SH.bubble
def _only_send(img, text, *a, **k):          # keep the experiment's send line, drop the spoken bubbles
    if text.startswith('2 כרטיסים'): return _bubble(img, text, *a, **k)
SH.bubble = _only_send

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = m.OUTDIR
VDIR = os.path.join(HERE, 'voice', 'ep31', 'proc')
META = {int(k): v for k, v in json.load(open(os.path.join(VDIR, 'meta.json'))).items()}
D = {i: META[i]['dur'] for i in META}
PINKSUB = (255, 182, 210)
OUTNAME = os.environ.get('OUTNAME', 'ep31_club_v3')
LIMIT = float(os.environ.get('LIMIT', '0'))
SPEAKER = {0: 'cat', 1: 'cat', 2: 'sh', 3: 'sh', 4: 'sh', 5: 'cat', 6: 'cat', 27: 'cat', 103: 'cat'}
LOUD = {0: 'smile', 103: 'smile', 5: 'smile'}

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
def split_at(i, frac):
    """start of the voiced segment closest to frac of the line"""
    c = [s for s, _ in SEG[i] if s > 0.2]
    return min(c, key=lambda s: abs(s - D[i] * frac)) if c else D[i] * frac

# ------------------------------------------------------------------ timeline (voiced t) and the map to v1 time
L = {}; P = []                                   # line starts; (t, ts) map points
L['c0'] = 0.12; C_END = round(L['c0'] + D[0] + 0.1, 3)
COLD = [(0.0, 6.84), (0.12, B.STAMP), (C_END, 7.7)]
RW = (C_END, C_END + 0.35); T0 = RW[1]
L[1] = T0 + 0.18
sh_t = L[1] + split_at(1, 0.4) - 0.1           # "צריך להעביר..." = he flips the old card ("ישן")
tb = L[1] + D[1] + 0.12
P += [(T0, 0.0), (sh_t, B.SHAKE[0]), (sh_t + 0.6, B.SHAKE[1]), (tb - 0.02, 2.39)]
P += [(tb, 2.4), (tb + 0.96, B.LAND)]
L[103] = tb + 0.98
t2 = L[103] + D[103] + 0.15
P += [(t2 - 0.02, 3.99), (t2, 4.0)]
L[27] = t2 + 0.06
tF = L[27] + D[27] + 0.05
P += [(tF, 4.7), (tF + 0.05, B.FORMIN)]
L[2] = tF + 0.08
P += [(L[2] + D[2], 5.4)]
slap = L[2] + D[2] + 0.35                       # paw slap = signature, סלולר ✓
P += [(slap, B.PRINT), (slap + 0.3, B.CHK2 + 0.1)]
L[3] = slap + 0.4
tS = L[3] + split_at(3, 0.55)                   # STAMP on "הועבר!"
P += [(L[3], 6.0), (tS - 0.05, 6.85), (tS, B.STAMP), (L[3] + D[3] + 0.5, 7.7)]
L[4] = L[3] + D[3] + 0.55
tP = L[4] + D[4] + 0.12
P += [(L[4], 7.75), (tP - 0.02, 8.69), (tP, B.PHONEUP), (tP + 0.45, B.DIP[0])]
L[5] = tP + 0.47
P += [(L[5] + D[5] + 0.05, B.DIP[1])]
tpk = L[5] + D[5] + 1.0
P += [(tpk, B.PEAK[0]), (tpk + 0.55, B.PEAK[1]), (tpk + 0.57, B.SLIP[0]), (tpk + 0.71, B.SLIP[1]), (tpk + 0.79, B.BREAK)]
TB = tpk + 0.79
L[6] = TB + 0.1
FREEZE = L[6] + D[6]
DUR = round(FREEZE + 0.35, 2)
P += [(DUR, B.DUR - 0.01)]
NF = int(round((LIMIT or DUR) * FPS))
HOOK_END = tb
OCC = [(0, L['c0'])] + [(k, L[k]) for k in (1, 103, 27, 2, 3, 4, 5, 6)]

def ts_of(t):
    if t < C_END: pts = COLD
    elif t < T0:
        u = (t - RW[0]) / (RW[1] - RW[0]); return lerp(3.9, 0.3, ease_in(u))
    else: pts = P
    if t <= pts[0][0]: return pts[0][1]
    for (a, x), (b, y) in zip(pts, pts[1:]):
        if a <= t < b: return x + (y - x) * (t - a) / (b - a)
    return pts[-1][1]

def speaking(t):
    for li, s0 in OCC:
        if s0 <= t < s0 + D[li]: return li, s0
    return None

def v_of(t, who):
    sp = speaking(t)
    if not sp or SPEAKER[sp[0]] != who: return 0.0, None
    li, s0 = sp; env = META[li]['env']; k = int((t - s0) * FPS)
    return (env[k] if k < len(env) else 0.0), li

# ------------------------------------------------------------------ mouth overrides on the v1 state functions
CUR = {'t': 0.0}
EXPR2 = os.environ.get('EXPR2', '0') == '1'     # gate probe: a new big expression on every voiced phrase of the want lines
WANT_POSES = [dict(lid=0.0, pupil='tiny', brow='up', ear_dy=-26, look=(-22, 4), blush=0.0, sweat=1.0),
              dict(lid=0.0, pupil='big', brow='sad', ear_droop=0.6, look=(18, 18), blush=0.0),
              dict(lid=0.1, pupil='normal', brow='annoyed', ear_dy=-14, look=(-26, -6), blush=0.0),
              dict(lid=0.0, pupil='big', brow='up', ear_dy=-22, look=(-8, -10), blush=0.6)]
def want_pose(t):
    for li in (0, 1):
        if L[li] <= t < L[li] + D[li] + 0.1:
            segs = [s for s, _ in SEG[li]]
            k = sum(1 for s in segs if t - L[li] >= s - 0.05)
            return WANT_POSES[(k + 2 * li) % len(WANT_POSES)], t - L[li] - (segs[k - 1] if k else 0)
    return None, 0
def _cat_wrap(fn):
    def w(ts, i):
        st, rot, dy = fn(ts, i)
        if False and fn.__name__ == 'cat_state_close' and T0 <= CUR['t'] < tb and not (B.SHAKE[0] <= ts < B.SHAKE[1]):
            pose, u = want_pose(CUR['t'])
            if pose:
                st.update(pose); rot = 7 * math.exp(-u * 5) * math.sin(u * 20); dy = -18 * math.exp(-u * 7) * math.cos(u * 22)
        v, li = v_of(CUR['t'], 'cat')
        if li is not None:
            if v > 0.32: st['mouth'] = LOUD.get(li, 'w')
            if li == 6 and v <= 0.12: st['mouth'] = 'flat'
            elif v > 0.12: st['mouth'] = 'w' if li in (6, 27, 1) else 'smile_small'
            elif st.get('mouth') == 'munch': st['mouth'] = 'flat'
        return st, rot, dy
    return w
def _sh_wrap(fn):
    def w(ts, i):
        st, rot = fn(ts, i)
        v, li = v_of(CUR['t'], 'sh')
        if li is not None: st['mouth'] = 'talk' if v > 0.12 else ('grin' if li == 5 else 'lazy')
        elif st.get('mouth') == 'talk': st['mouth'] = 'grin'
        return st, rot
    return w
B.cat_state_close = _cat_wrap(B.cat_state_close)
B.cat_state_two = _cat_wrap(B.cat_state_two)
B.sh_state = _sh_wrap(B.sh_state)

# ------------------------------------------------------------------ subtitles
SUBS = {
    0: [['חשמל, סלולר, ארנונה.'], ['הכול עבר!']],
    1: [['הכרטיס עובר חברה.'], ['צריך להעביר את כל הוראות הקבע.']],
    103: [['יש!!!']],
    27: [['שרית?! גם פה?']],
    2: [['הוראות קבע?'], ['בבקשה, מותק.']],
    3: [['וארנונה...'], ['הועבר!']],
    4: [['עכשיו לגזור את הישן, מותק.']],
    5: [['ביי, כרטיס.']],
    6: [['חיוב נדחה?!'], ['על שקל אחד?!']],
}
def chunk_starts(i):
    ch = SUBS[i]
    if len(ch) == 1: return [0.0]
    tot = sum(len(' '.join(c)) for c in ch); acc = 0; out = [0.0]
    for c in ch[:-1]:
        acc += len(' '.join(c)); out.append(split_at(i, acc / tot))
    return out
SUB_TIMES = []
for li, s0 in OCC:
    cs = chunk_starts(li)
    for k, c in enumerate(SUBS[li]):
        a = s0 + max(0.0, cs[k] - 0.05); b = s0 + (cs[k + 1] - 0.05 if k + 1 < len(cs) else D[li] + 0.15)
        nxt = [s for _, s in OCC if s > s0 + 0.01]
        if nxt: b = min(b, nxt[0] - 0.03)
        if li == 0: b = min(b, C_END)
        SUB_TIMES.append((a, b, c, li))
SUB_Y = int(os.environ.get('SUBY', '1450')); SUB_TWO = 1265; SUB_CAT = 1530

def x64_badge(frame):
    """v1 badge moved down under the meter, right side (the hook sits at y 230-350 here)"""
    d = ImageDraw.Draw(frame)
    for y in range(0, H, 6): d.line([(0, y), (W, y)], fill=(0, 0, 0, 26), width=2)
    d.rounded_rectangle([920, 540, 1050, 610], radius=16, fill=(230, 40, 40), outline=(10, 10, 12), width=4)
    d.text((985, 576), 'x64', font=font(46, 900), fill=WHITE, anchor='mm', stroke_width=5, stroke_fill=(10, 10, 12))

def sub_layer(lines, fill, size=64):
    """same as ep26.sub_layer (copied: ep26 loads its own voice meta on import)"""
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
    d = ImageDraw.Draw(frame); rng = random.Random(int(t * 120))
    for _ in range(5):
        y = rng.uniform(300, 1700); h = rng.uniform(4, 14); d.rectangle([0, y, W, y + h], fill=(255, 255, 255, 70))
    for x0 in (300, 344):
        d.polygon([(x0 + 44, 900), (x0, 930), (x0 + 44, 960)], fill=WHITE, outline=(10, 10, 12), width=5)
    d.text((610, 930), 'רגע קודם', font=font(76, 900), fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(10, 10, 12))

def draw_frame(i):
    t = i / FPS; CUR['t'] = t
    ts = ts_of(t)
    name, a, b = B.shot(ts)
    img = {'two': B.scene_two, 'cat': B.scene_cat, 'board': B.scene_board}[name](ts, i)
    z, ccx, ccy = B.camera(ts)
    if t < C_END:                                                                # cold open: tight on him + the ticked form
        z, ccx, ccy = (1.62 - 0.05 * t, 760.0, 1060.0) if os.environ.get('FACEZ', '0') == '1' else (1.32 - 0.04 * t, 700.0, 1180.0)
    for cut in (T0, tb, t2, tP):                                                # snap-zoom on every cut
        if 0 <= t - cut < 0.2: z = max(z, 1.0 + 0.07 * (1 - ease_out((t - cut) / 0.2)))
    if 0 <= t - 0.12 < 0.3:
        rng = random.Random(i); sh_ = 14 * math.exp(-(t - 0.12) * 9); ccx += rng.uniform(-sh_, sh_); ccy += rng.uniform(-sh_, sh_)
    if z > 1.0005:
        cw, ch = W * K / z, H * K / z
        left = clamp(S(ccx) - cw / 2, 0, W * K - cw); top = clamp(S(ccy) - ch / 2, 0, H * K - ch)
        img = img.crop((int(left), int(top), int(left + cw), int(top + ch)))
    frame = img.resize((W, H), Image.LANCZOS)
    if B.TILT and ts < 2.4 and t >= T0:                      # v1's Dutch-angle want shot (snaps in from 11°)
        ang = 4.0 + 7.0 * math.exp(-(t - T0) * 9); zz = 1.09
        fr = frame.resize((int(W * zz), int(H * zz)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC)
        frame = fr.crop(((fr.width - W) // 2, (fr.height - H) // 2, (fr.width - W) // 2 + W, (fr.height - H) // 2 + H))
    frame.alpha_composite(m.VIG)
    if 2.4 <= ts < B.LAND and not (RW[0] <= t < RW[1]): B.x64_badge(frame, ts)
    if B.PEAK[0] <= ts < B.SLIP[1]:
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (ts - B.PEAK[0]) / 0.5)
        frame.alpha_composite(Image.new('RGBA', frame.size, (0, 0, 0, int(40 * k))))
    if 0.12 <= t < 0.18: frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, int(110 * (1 - (t - 0.28) / 0.06)))))
    if not (RW[0] <= t < RW[1]):
        for s_ in (B.SLAM, B.LAND, B.PRINT, B.STAMP, B.SLIP[1], B.BREAK):
            if t >= C_END and abs(ts - s_) < 0.03 and ts >= s_:
                frame.alpha_composite(Image.new('RGBA', frame.size, (255, 255, 255, 90)))
    if RW[0] <= t < RW[1]: rewind_overlay(frame, t)
    if t >= DUR - 0.22:                                                          # whip back into the cold open (loop)
        k_ = (t - (DUR - 0.22)) / 0.22
        moved = Image.new('RGBA', frame.size, (0, 0, 0, 255)); moved.paste(frame, (-int(700 * k_ * k_), 0))
        frame = moved.filter(ImageFilter.BoxBlur(int(2 + 26 * k_)))
    if not (RW[0] <= t < RW[1]): B.meter(frame, ts)
    if t < HOOK_END and not (RW[0] <= t < RW[1]):
        m.paste_center(frame, m.caption_layer(['כרטיס המועדון עובר חברה?', 'מה עם הוראות הקבע?'], 74, WHITE), W / 2, 290)
    for t0, t1, lines, li in SUB_TIMES:
        if t0 <= t < t1:
            cap = sub_layer(lines, PINKSUB if SPEAKER[li] == 'sh' else WHITE)
            m.paste_center(frame, cap, W / 2, 1000 if t < C_END else {'two': SUB_TWO, 'cat': SUB_CAT}.get(name, SUB_Y))
    if not (RW[0] <= t < RW[1]):
        frame.alpha_composite(B.PILL_EP, (40, 70))
        if not (t >= TB + 0.05 and int(t * 10) % 3 == 0):
            frame.alpha_composite(B.PILL_Q, (W - 40 - B.PILL_Q.width, 70))
    return frame.convert('RGB')

# ------------------------------------------------------------------ audio: voices + SFX (v1 events moved onto the voiced clock), no music
SR = m.SR
def t_of(ts):
    """inverse map (main timeline only)"""
    for (a, x), (b, y) in zip(P, P[1:]):
        if x <= ts <= y and y > x: return a + (b - a) * (ts - x) / (y - x)
    return P[-1][0]

def build_audio(path):
    n = int(DUR * SR) + SR; sfx = np.zeros(n); vox = np.zeros(n); add = m.add
    rng = np.random.default_rng(229)
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
    def rustle(t0, d_, g=0.12): add(sfx, m.highpass(nz(d_), 2500) * np.exp(-tt_(d_) * 6), t0, g)
    def crunch(t0, t1, g=0.12, step=0.13):
        tc = t0
        while tc < t1: add(sfx, m.bandpass(nz(0.07), 1500, 7000) * np.exp(-tt_(0.07) * 45), tc, g); tc += step
    # cold open: the stamp + cheer (flash-forward)
    thump(0.12, 0.85); add(sfx, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), 0.12, 0.45); check(0.17, 0.15, 659.3)
    applause(0.4, C_END - 0.05, 0.05); murmur(0.0, C_END, 0.06)
    tc = RW[0]                                                                   # ◀◀ tape scrub
    while tc < RW[1]:
        tt = tt_(0.04); add(sfx, np.sin(2 * np.pi * (2400 - 3000 * (tc - RW[0])) * tt) * np.exp(-tt * 30), tc, 0.05); tc += 0.035
    whoosh(RW[0], 0.35, 0.22)
    murmur(T0, tpk - 0.15, 0.07)
    thump(t_of(B.SLAM), 0.65); add(sfx, m.tone(196, 0.5, decay=4), t_of(B.SLAM), 0.18)
    rustle(sh_t, 0.4, 0.1); pop(sh_t + 0.2, 0.12)                                # the old card flips
    for tc in (tb, t2, tP): whoosh(tc - 0.08, 0.16, 0.1)
    for k_, (tj, _) in enumerate(B.JUMPS): add(sfx, m.tone(880 + 60 * k_, 0.06, harm=((1, 1),), decay=20), t_of(tj), 0.07)
    pop(t_of(B.SEND[0]), 0.18)
    ding(t_of(B.LAND), 0.24)
    thump(L[27], 0.3)
    whoosh(t_of(B.FORMIN) - 0.05, 0.2, 0.25)
    check(t_of(B.CHK1), 0.12, 523.3)
    thump(slap, 0.5); add(sfx, m.bandpass(nz(0.08), 300, 1800) * np.exp(-tt_(0.08) * 40), slap, 0.22); check(t_of(B.CHK2), 0.13, 587.3)
    thump(tS, 0.9); add(sfx, m.highpass(nz(0.05), 1200) * np.exp(-tt_(0.05) * 90), tS, 0.5); check(tS + 0.05, 0.16, 659.3)
    applause(tS + 0.5, L[4] - 0.05, 0.05)
    for k_ in range(6): pop(tS + 0.1 + 0.11 * k_, 0.07)
    whoosh(tP, 0.2, 0.2); pop(tP + 0.15, 0.15)
    pop(L[5] + D[5] - 0.1, 0.12)                                                 # the kiss
    add(sfx, m.highpass(nz(0.12), 3000) * np.exp(-tt_(0.12) * 20), tpk - 0.5, 0.1)  # scissors open (shhk)
    for hb in (tpk + 0.02, tpk + 0.5): thump(hb, 0.32); thump(hb + 0.16, 0.22)
    tsn = tpk + 0.68; add(sfx, m.highpass(nz(0.06), 2500) * np.exp(-tt_(0.06) * 60), tsn, 0.55)   # SNIP
    add(sfx, m.tone(2200, 0.05, harm=((1, 1),), decay=40), tsn, 0.12)
    thump(TB, 0.95); add(sfx, m.tone(110, 0.6, decay=3), TB, 0.3)
    tc = TB
    while tc < TB + 0.3:
        tt = tt_(0.05); add(sfx, np.sign(np.sin(2 * np.pi * 180 * tt)) * np.exp(-tt * 20), tc, 0.06); tc += 0.08
    murmur(TB + 0.05, DUR, 0.025)
    whoosh(DUR - 0.25, 0.25, 0.2)
    sfx += m.lowpass(nz(len(sfx) / SR), 300) * 0.006
    for li, s0 in OCC:
        y = np.load(os.path.join(VDIR, f'line{li:03d}.npy')).astype(np.float64); add(vox, y, s0, 1.0)
    sfx /= (np.max(np.abs(sfx)) + 1e-9) / 0.42
    vox /= (np.max(np.abs(vox)) + 1e-9) / 0.9
    out = (sfx + vox)[:int(DUR * SR)]
    out /= max(1.0, np.max(np.abs(out)) / 0.95)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())

PHONESM = os.environ.get('PHONESM', '0') == '1'   # gate probe: smaller phone in the want shot (the face dominates)
def init_all():
    B.init_all()
    if PHONESM:
        pass
def _init_worker(): init_all()
def _render(i): return draw_frame(i).tobytes()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'render'
    tag = os.environ.get('TAG', '')
    if mode == 'times':
        print('DUR', DUR, 'C_END', C_END, 'T0', T0, 'tb', round(tb, 2), 't2', round(t2, 2), 'tF', round(tF, 2), 'slap', round(slap, 2),
              'tS', round(tS, 2), 'tP', round(tP, 2), 'peak', round(tpk, 2), 'break', round(TB, 2))
        for k, v in L.items(): print(' line', k, round(v, 2), '-', round(v + D[0 if k == 'c0' else k], 2))
        return
    if mode == 'audio': build_audio(sys.argv[2]); print('ok'); return
    if mode == 'test':
        init_all()
        times = [float(x) for x in sys.argv[2:]]
        frames = [draw_frame(min(int(DUR * FPS) - 1, int(round(tm * FPS)))) for tm in times]
        tw, th = W // 3, H // 3; cols = min(6, len(frames)); rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (tw * cols, th * rows))
        for k, f in enumerate(frames): sheet.paste(f.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
        sheet.save(os.path.join(OUTDIR, f'ep31{tag}_contact.png')); print('ok'); return
    wav = os.path.join(OUTDIR, f'ep31{tag}_audio.wav'); build_audio(wav); print('audio ok')
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
