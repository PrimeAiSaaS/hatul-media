#!/usr/bin/env python3
"""ep41 VOICED (season 9 "הקו פנוי" ep3, §P): decode voice-bank 2026-11-19 lines 4100–4105 (Gabi's picks: 4100 B,
4102 C, 4104 D, rest old) + stock 9105 "לא. לא. לא...", tighten pauses, save npy + meta.json (ep43_prep shape)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep41', 'proc')
SRC = {i: f'ep41/line{i:02d}.mp3' for i in range(6)}
SRC[105] = 'stock/cat_9105.mp3'
MAXP = {0: 0.12, 1: 0.15, 2: 0.18, 3: 0.18, 4: 0.30, 5: 0.35, 105: 0.30}

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
