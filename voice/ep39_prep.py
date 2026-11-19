#!/usr/bin/env python3
"""ep39 VOICED (season 9 "הקו פנוי" ep1, §P, ~25 s): decode voice-bank 2026-11-19 lines 3900–3906 (Gabi's 19.11 picks
already applied to voice/ep39/lineNN.mp3) + 2703 "שרית?! גם פה?" + stock 9101 "סבבה." (his own voice on the recording)
+ 9103 "יש!!!", tighten pauses, save npy + meta.json (ep38_prep shape)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ep28_prep import decode, tighten, envelope, SR
OUT = os.path.join(HERE, 'ep39', 'proc')
SRC = {i: f'ep39/line{i:02d}.mp3' for i in range(7)}
SRC[27] = 'ep27/line03.mp3'
SRC[101] = 'stock/cat_9101.mp3'
SRC[103] = 'stock/cat_9103.mp3'
MAXP = {0: 0.12, 1: 0.15, 2: 0.15, 3: 0.12, 4: 0.15, 5: 0.15, 6: 0.15, 27: 0.12, 101: 0.12, 103: 0.12}

def decode_tempo(p, k):
    import subprocess
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-af', f'atempo={k}', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)

def main():
    os.makedirs(OUT, exist_ok=True); meta = {}
    for i, f in SRC.items():
        x = decode_tempo(os.path.join(HERE, f), 1.12) if i == 6 else decode(os.path.join(HERE, f))   # the break line a touch faster
        y = tighten(x, MAXP[i]); y = y / (np.max(np.abs(y)) + 1e-9) * 0.95
        np.save(os.path.join(OUT, f'line{i:03d}.npy'), y.astype(np.float32))
        meta[i] = dict(dur=round(len(y) / SR, 3), orig=round(len(x) / SR, 3), env=envelope(y), src=f)
        print(i, meta[i]['orig'], '->', meta[i]['dur'])
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))

if __name__ == '__main__':
    main()
