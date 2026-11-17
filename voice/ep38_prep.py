#!/usr/bin/env python3
"""ep38 VOICED (season 8 "בלאק פריידיי" finale, §P, voiced short arm ~21 s): decode voice-bank 2026-11-13 lines 3800–3804
+ 2703 "שרית?! גם פה?" + 2509 "חופשי. סוף סוף... חופשי." (the peak, reuse)
+ stock 9000 "שנייה, מותק." + 9103 "יש!!!", tighten pauses, save npy + meta.json (ep37_prep shape)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep38', 'proc')
SRC = {i: f'ep38/line{i:02d}.mp3' for i in range(5)}
SRC[27] = 'ep27/line03.mp3'
SRC[25] = 'ep25/line09.mp3'
SRC[90] = 'stock/sharit_9000.mp3'
SRC[103] = 'stock/cat_9103.mp3'
MAXP = {0: 0.15, 1: 0.12, 2: 0.15, 3: 0.12, 4: 0.12, 27: 0.12, 25: 0.30, 90: 0.15, 103: 0.15}

def decode_tempo(p, k):
    import subprocess
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-af', f'atempo={k}', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)

def main():
    os.makedirs(OUT, exist_ok=True); meta = {}
    for i, f in SRC.items():
        x = decode(os.path.join(HERE, f))
        if i == 4: x = decode_tempo(os.path.join(HERE, f), 1.12)   # the app line a touch faster: the break stays in the last ~2.5 s
        y = tighten(x, MAXP[i]); y = y / (np.max(np.abs(y)) + 1e-9) * 0.95
        np.save(os.path.join(OUT, f'line{i:03d}.npy'), y.astype(np.float32))
        meta[i] = dict(dur=round(len(y) / SR, 3), orig=round(len(x) / SR, 3), env=envelope(y), src=f)
        print(i, meta[i]['orig'], '->', meta[i]['dur'])
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))

if __name__ == '__main__':
    main()
