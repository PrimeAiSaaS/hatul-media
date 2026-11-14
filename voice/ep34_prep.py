#!/usr/bin/env python3
"""ep34 VOICED (season 8 "בלאק פריידיי" ep1, §P, voiced short arm ~20 s): decode voice-bank 2026-11-13 lines 3400–3404
+ stock 9104 ("רגע... מה?!" = the break reaction), tighten pauses, save npy + meta.json. Same tighten/envelope as ep28_prep."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep34', 'proc')
SRC = {i: f'ep34/line{i:02d}.mp3' for i in range(5)}
SRC[104] = 'stock/cat_9104.mp3'
SRC[103] = 'stock/cat_9103.mp3'   # "יש!!!" on the $74.99 (stock pack)
MAXP = {0: 0.12, 1: 0.15, 2: 0.25, 3: 0.15, 4: 0.30, 104: 0.30, 103: 0.15}

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
