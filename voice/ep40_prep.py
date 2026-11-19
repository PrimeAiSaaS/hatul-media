#!/usr/bin/env python3
"""ep40 VOICED (season 9 "הקו פנוי" ep2, §P): decode voice-bank 2026-11-19 lines 4000–4005 + stock 9104 "רגע... מה?!" + 9103 "יש!!!" + 9000 "שנייה, מותק.", tighten pauses, save npy + meta.json (ep39_prep shape)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep40', 'proc')
SRC = {i: f'ep40/line{i:02d}.mp3' for i in range(6)}
SRC[104] = 'stock/cat_9104.mp3'; SRC[90] = 'stock/sharit_9000.mp3'
SRC[103] = 'stock/cat_9103.mp3'
MAXP = {0: 0.12, 1: 0.15, 2: 0.15, 3: 0.15, 4: 0.30, 5: 0.12, 90: 0.15, 103: 0.12, 104: 0.15}

def decode_tempo(p, k):
    import subprocess
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-af', f'atempo={k}', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)

def main():
    os.makedirs(OUT, exist_ok=True); meta = {}
    for i, f in SRC.items():
        x = decode_tempo(os.path.join(HERE, f), 1.12) if i == -1 else decode(os.path.join(HERE, f))   # the break line a touch faster
        y = tighten(x, MAXP[i]); y = y / (np.max(np.abs(y)) + 1e-9) * 0.95
        np.save(os.path.join(OUT, f'line{i:03d}.npy'), y.astype(np.float32))
        meta[i] = dict(dur=round(len(y) / SR, 3), orig=round(len(x) / SR, 3), env=envelope(y), src=f)
        print(i, meta[i]['orig'], '->', meta[i]['dur'])
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))

if __name__ == '__main__':
    main()
