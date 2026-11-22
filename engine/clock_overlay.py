#!/usr/bin/env python3
"""Real-seconds countdown (lesson 20261122-1600-claude-real-clock, Gabi 22.11): a red LED box in the free top band
between the serial pills, visible from frame 0 to the break. One displayed second = one real second of video.
The cold open is an in-context replay, so the clock there shows the story time it replays (like ep35); the ◀◀ rewind
scrambles the digits. Used by ep42_v2.py and ep43_v2.py (wrappers over the built episodes; voices, plant, climb and
break untouched)."""
import math, random, wave
import numpy as np
from PIL import Image, ImageDraw
import make_video as m
from make_video import font, W

BOX = (452, 58, 872, 166)          # x0, y0, x1, y1 in frame px (between the left pills and the queue pill, above the hook)

def secs_left(story_t, zero):
    return max(0, math.ceil(zero - story_t - 1e-6))

def draw(frame, label_lines, secs, state='run', t=0.0, scramble=False):
    """state: 'run' (red), 'hot' (last 5 s, blinking), 'zero' (00:00 flashing), 'done' (green, stopped)."""
    d = ImageDraw.Draw(frame)
    x0, y0, x1, y1 = BOX
    sh = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 4, y0 + 8, x1 + 4, y1 + 8], radius=18, fill=(0, 0, 0, 110))
    frame.alpha_composite(sh)
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=(22, 10, 12, 245), outline=(90, 90, 98), width=5)
    # label on the right (RTL), digits on the left
    lx = x1 - 22; ly = (y0 + y1) / 2
    lf = font(28, 800)
    for k, ln in enumerate(label_lines):
        d.text((lx, ly + (k - (len(label_lines) - 1) / 2) * 34), ln, font=lf, fill=(236, 236, 240), anchor='rm')
    if scramble:
        r = random.Random(int(t * 60)); txt = f'00:{r.randint(0, 59):02d}'
    else:
        txt = f'{secs // 60:02d}:{secs % 60:02d}'
    col = (255, 58, 48)
    if state == 'hot' and int(t * 4) % 2 == 1: col = (255, 170, 140)
    if state == 'zero': col = (255, 58, 48) if int(t * 6) % 2 == 0 else (120, 24, 20)
    if state == 'done': col = (70, 220, 110)
    dx = x0 + 20 + 105
    d.text((dx, ly + 3), txt, font=font(72, 900), fill=col, anchor='mm')
    return frame

def add_ticks(wav_path, tick_times, loud_from=None, g=0.05, g_loud=0.09, final=None):
    """mix a soft clock tick into an existing 16-bit stereo wav at the given times (seconds)."""
    with wave.open(wav_path, 'rb') as wv:
        sr = wv.getframerate(); n = wv.getnframes(); raw = wv.readframes(n)
    a = np.frombuffer(raw, dtype=np.int16).reshape(-1, 2).astype(np.float64) / 32767
    mono = np.zeros(len(a))
    tick = m.tone(1500, 0.03, harm=((1, 1), (2, 0.3)), decay=60)
    for tc in tick_times:
        gg = g_loud if (loud_from is not None and tc >= loud_from) else g
        s0 = int(tc * sr)
        if 0 <= s0 < len(mono): seg = tick[:len(mono) - s0]; mono[s0:s0 + len(seg)] += seg * gg
    if final is not None:   # the 00:00 / stop buzz
        tt = np.arange(int(0.22 * sr)) / sr
        bz = np.sign(np.sin(2 * np.pi * 880 * tt)) * np.exp(-tt * 9) * 0.5
        s0 = int(final * sr); seg = bz[:max(0, len(mono) - s0)]; mono[s0:s0 + len(seg)] += seg * 0.08
    a = a + mono[:, None]
    a /= max(1.0, np.max(np.abs(a)) / 0.97)
    with wave.open(wav_path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(sr); wv.writeframes((a * 32767).astype(np.int16).tobytes())
