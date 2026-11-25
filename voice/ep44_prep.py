#!/usr/bin/env python3
"""ep44 VOICED (Series 2 "שוקו והג׳ינג׳י" ep1, §P): decode voice-bank 2026-11-23 lines 4400–4408 (Gabi's picks 25.11: 4405 B), tighten pauses, save npy + meta.json."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep44', 'proc')
SRC = {i: f'ep44/line{i:02d}.mp3' for i in range(9)}

MAXP = {0: 0.12, 1: 0.15, 2: 0.25, 3: 0.25, 4: 0.12, 5: 0.25, 6: 0.2, 7: 0.3, 8: 0.25}

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
