#!/usr/bin/env python3
"""ep30 VOICED (§P, target 30 s): decode voice-bank lines 3000–3010 (3003 = same text as 3000, not generated: the cold open
line is replayed in context) + 2703 ("שרית?! גם פה?"), tighten pauses, save npy + meta.json (duration, 30 fps talk envelope).
Same decode/tighten/envelope as ep28_prep. MAXP 0.18 normal, 0.35 for Sharit's "..." lines and the cat's "סוף סוף...".""" 
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep30', 'proc')
SRC = {0: 'ep30/line00.mp3', 1: 'ep30/line01.mp3', 2: 'ep30/line02.mp3', 4: 'ep30/line04.mp3', 5: 'ep30/line05.mp3',
       6: 'ep30/line06.mp3', 7: 'ep30/line07.mp3', 8: 'ep30/line08.mp3', 9: 'ep30/line09.mp3', 10: 'ep30/line10.mp3',
       27: 'ep27/line03.mp3'}
MAXP = {0: 0.18, 1: 0.18, 2: 0.18, 4: 0.35, 5: 0.18, 6: 0.35, 7: 0.35, 8: 0.35, 9: 0.18, 10: 0.18, 27: 0.18}

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
