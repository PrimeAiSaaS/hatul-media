#!/usr/bin/env python3
"""ep27 (voiced, §P, short_21 arm): decode the voice-bank lines 2700–2710, tighten pauses, save wav + json (duration, 30 fps talk envelope)."""
import json, os, subprocess, sys
import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'ep27')
OUT = os.path.join(HERE, 'ep27', 'proc')
# max pause kept inside a line (s): normal lines tight, Sharit's "שנייה, מותק..." and the chill lines keep more air
MAXP = {0: 0.12, 1: 0.12, 2: 0.12, 3: 0.12, 4: 0.12, 5: 0.12, 6: 0.25, 7: 0.25, 8: 0.12, 9: 0.25, 10: 0.25}   # short_21 arm: 0.12, Sharit's '...' lines (and the cat's 'שרית...') 0.25

def decode(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)

def tighten(x, maxp):
    win = int(0.02 * SR)
    n = len(x) // win
    rms = np.sqrt(np.mean(x[:n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    loud = db > (db.max() - 38)
    idx = np.where(loud)[0]
    a, b = max(0, idx[0] - 2), min(n, idx[-1] + 4)          # trim lead/tail
    keep = []
    k = a; run = 0
    maxw = int(maxp / 0.02)
    for k in range(a, b):
        if loud[k]: run = 0; keep.append(k)
        else:
            run += 1
            if run <= maxw: keep.append(k)
    y = np.concatenate([x[k * win:(k + 1) * win] for k in keep])
    # tiny fades at the cut points are inside silence, so no clicks; fade edges
    f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y

def envelope(y, fps=30):
    hop = SR // fps
    n = int(np.ceil(len(y) / hop))
    e = np.array([np.sqrt(np.mean(y[k * hop:(k + 1) * hop] ** 2) + 1e-12) for k in range(n)])
    return (e / (e.max() + 1e-9)).round(3).tolist()

def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for i in range(11):
        x = decode(os.path.join(SRC, f'line{i:02d}.mp3'))
        y = tighten(x, MAXP[i])
        y = y / (np.max(np.abs(y)) + 1e-9) * 0.95
        np.save(os.path.join(OUT, f'line{i:02d}.npy'), y.astype(np.float32))
        meta[i] = dict(dur=round(len(y) / SR, 3), orig=round(len(x) / SR, 3), env=envelope(y))
        print(i, meta[i]['orig'], '->', meta[i]['dur'])
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))

if __name__ == '__main__':
    main()
