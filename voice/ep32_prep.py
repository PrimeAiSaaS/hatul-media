#!/usr/bin/env python3
"""ep32 VOICED (§P, short arm target ~21 s): decode voice-bank lines 3200–3205 + 2703 ("שרית?! גם פה?") + stock 9103 ("יש!!!"),
tighten pauses, save npy + meta.json (duration, 30 fps talk envelope). Same decode/tighten/envelope as ep28_prep.
Short arm (voiced_length short_21): MAXP 0.12, 0.25 for the "..." lines. 3206 ("רגע! אני אחת!") is not used: after the break
§P allows only the frozen face."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep32', 'proc')
SRC = {0: 'ep32/line00.mp3', 1: 'ep32/line01.mp3', 2: 'ep32/line02.mp3', 3: 'ep32/line03.mp3', 4: 'ep32/line04.mp3',
       5: 'ep32/line05.mp3', 27: 'ep27/line03.mp3', 103: 'stock/cat_9103.mp3'}
MAXP = {0: 0.12, 1: 0.12, 2: 0.25, 3: 0.12, 4: 0.25, 5: 0.12, 27: 0.12, 103: 0.12}

def main():
    os.makedirs(OUT, exist_ok=True); meta = {}
    for i, f in SRC.items():
        x = decode(os.path.join(HERE, f)); y = tighten(x, MAXP[i]); y = y / (np.max(np.abs(y)) + 1e-9) * 0.95
        np.save(os.path.join(OUT, f'line{i:02d}.npy'), y.astype(np.float32))
        meta[i] = dict(dur=round(len(y) / SR, 3), orig=round(len(x) / SR, 3), env=envelope(y), src=f)
        print(i, meta[i]['orig'], '->', meta[i]['dur'])
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))

if __name__ == '__main__':
    main()
