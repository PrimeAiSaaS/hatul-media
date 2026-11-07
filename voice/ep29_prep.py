#!/usr/bin/env python3
"""ep29 VOICED rebuild (6.11 Gabi: every episode from 29 voiced): decode voice-bank lines 2900–2906 + 2703 ("שרית?! גם פה?")
+ stock 9104 ("רגע... מה?!"), tighten pauses, save npy + meta.json (duration, 30 fps talk envelope). Same tighten/envelope as ep28_prep."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep29', 'proc')
SRC = {0: 'ep29/line00.mp3', 1: 'ep29/line01.mp3', 2: 'ep29/line02.mp3', 3: 'ep29/line03.mp3', 4: 'ep29/line04.mp3',
       5: 'ep29/line05.mp3', 6: 'ep29/line06.mp3', 27: 'ep27/line03.mp3', 900: 'stock/sharit_9000.mp3', 104: 'stock/cat_9104.mp3'}
MAXP = {0: 0.18, 1: 0.18, 2: 0.18, 3: 0.35, 4: 0.18, 5: 0.35, 6: 0.35, 27: 0.18, 900: 0.35, 104: 0.35}

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
