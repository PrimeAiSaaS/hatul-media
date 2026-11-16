#!/usr/bin/env python3
"""ep36 VOICED (season 8 "בלאק פריידיי" ep3, §P, voiced short arm ~21 s): decode voice-bank 2026-11-13 lines 3600–3605
+ 2703 "שרית?! גם פה?" + stock 9000 "שנייה, מותק.", 9102 "יאללה!", 9103 "יש!!!" (9104 kept for probes), tighten pauses, save npy + meta.json (ep35_prep shape)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep36', 'proc')
SRC = {i: f'ep36/line{i:02d}.mp3' for i in range(6)}
SRC[104] = 'stock/cat_9104.mp3'
SRC[103] = 'stock/cat_9103.mp3'
SRC[102] = 'stock/cat_9102.mp3'   # "יאללה!" when the dot reaches the pin
SRC[27] = 'ep27/line03.mp3'      # 2703 "שרית?! גם פה?" (Sharit = the courier dispatcher)
SRC[900] = 'stock/sharit_9000.mp3'  # 9000 "שנייה, מותק."
MAXP = {0: 0.12, 1: 0.15, 2: 0.15, 3: 0.12, 4: 0.30, 5: 0.12, 104: 0.30, 103: 0.15, 102: 0.12, 27: 0.12, 900: 0.18}   # the peak '...' keeps air

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
