#!/usr/bin/env python3
"""ep22 VOICED rebuild (Gabi 13.11: "לדובב הכל מדובב"): decode voice-bank 2026-11-13 lines 2200–2209 + stock 9104
("רגע... מה?!"), tighten pauses, save npy + meta.json (duration, 30 fps talk envelope). Same tighten/envelope as ep28_prep.
MAXP 0.18 normal, 0.35 for the "..." lines (2208 "סוף סוף... חשבון מוגן.", 9104) and Sharit's slow digit read (2209)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep22', 'proc')
SRC = {i: f'ep22/line{i:02d}.mp3' for i in range(10)}
SRC[104] = 'stock/cat_9104.mp3'
MAXP = {i: 0.18 for i in range(10)}
MAXP.update({8: 0.35, 9: 0.30, 104: 0.35})

def main():
    os.makedirs(OUT, exist_ok=True); meta = {}
    for i, f in SRC.items():
        x = decode(os.path.join(HERE, f)); y = tighten(x, MAXP[i]); y = y / (np.max(np.abs(y)) + 1e-9) * 0.95
        np.save(os.path.join(OUT, f'line{i:03d}.npy'), y.astype(np.float32))
        meta[i] = dict(dur=round(len(y) / SR, 3), orig=round(len(x) / SR, 3), env=envelope(y), src=f)
        print(i, meta[i]['orig'], '->', meta[i]['dur'])
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))

if __name__ == '__main__':
    main()
