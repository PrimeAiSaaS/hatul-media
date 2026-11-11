#!/usr/bin/env python3
"""ep33 VOICED (§P, ~18–22 s, the data agent's default voiced length 10.11): decode voice-bank lines 3300–3305 + 2703
("שרית?! גם פה?"), tighten pauses, save npy + meta.json (duration, 30 fps talk envelope). Same decode/tighten/envelope as ep28_prep.
3304 = Gabi's 9.11 pick on the pronunciation page (take C "אוּשַּׁר, מותק." = voice/review/20261109/3304_C.mp3, copied to ep33/line04.mp3).
3306 ("עמלה?! על הקצבה שלי?!") is not used: after the break §P allows only the frozen face."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep33', 'proc')
SRC = {0: 'ep33/line00.mp3', 1: 'ep33/line01.mp3', 2: 'ep33/line02.mp3', 3: 'ep33/line03.mp3', 4: 'ep33/line04.mp3',
       5: 'ep33/line05.mp3', 27: 'ep27/line03.mp3'}
MAXP = {0: 0.12, 1: 0.12, 2: 0.18, 3: 0.12, 4: 0.18, 5: 0.25, 27: 0.12}

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
