#!/usr/bin/env python3
"""ep47 VOICED (Series 2 "שוקו והג׳ינג׳י" ep4, §P): decode voice-bank 2026-11-23 lines 4700–4707 (Gabi's picks 25.11: 4700 D + B takes from abd4dd4/d666ffd, as in the repo), tighten pauses, save npy + meta.json."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep47', 'proc')
SRC = {i: f'ep47/line{i:02d}.mp3' for i in range(8)}

MAXP = {0: 0.2, 1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.35, 6: 0.25, 7: 0.2}

def main():
    os.makedirs(OUT, exist_ok=True); meta = {}
    for i, f in SRC.items():
        x = decode(os.path.join(HERE, f))
        y = tighten(x, MAXP[i]); y = y / (np.max(np.abs(y)) + 1e-9) * 0.95
        np.save(os.path.join(OUT, f'line{i:03d}.npy'), y.astype(np.float32))
        meta[i] = dict(dur=round(len(y) / SR, 3), orig=round(len(x) / SR, 3), env=envelope(y), src=f)
        print(i, meta[i]['orig'], '->', meta[i]['dur'])
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))

if __name__ == '__main__':
    main()
