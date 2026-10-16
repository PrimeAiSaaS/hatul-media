#!/usr/bin/env python3
"""Hook B for the Instagram Trial Reel: the same episode with a different opening.

The regular reel (hook A) goes to followers; the Trial Reel goes only to non-followers, so every
episode becomes a test of two openings. Exactly one thing changes between A and B: the opening.

Modes
  text      Cover the episode's opening caption with a paper-note card carrying hook B for the first
            --secs seconds (default 2.2), then fade it out so the original caption takes over.
            Same picture, same length, same loop; only the opening line differs.
  coldopen  Prepend --dur seconds (default 1.2) taken from --from (the payoff moment) with hook B on
            the card, then play the whole episode. Tests "payoff first" against the normal setup.

Usage
  python3 tools/hook_variant.py text     <in.mp4> <out.mp4> "<hook B>" [--secs 2.2] [--top 80] [--bottom 430]
  python3 tools/hook_variant.py coldopen <in.mp4> <out.mp4> "<hook B>" --from 6.5 [--dur 1.2]
  python3 tools/hook_variant.py sheet    <a.mp4> <b.mp4> <out.png>     # side-by-side check of the first 3 s

--top/--bottom: the band (in 1080x1920 pixels) that holds the opening caption. The default covers the
caption position used by the series engine (two lines, centred, under the top UI margin).
Hook B: up to ~6 words per line, at most 2 lines, must contain the topic keyword (Growth playbook §A).
"""
import os, subprocess, sys, tempfile, argparse
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONTS = ['/home/claude/cat_video/fonts/Rubik[wght].ttf', '/home/claude/cat_engine/engine/fonts/Rubik[wght].ttf',
         os.path.join(os.path.dirname(__file__), 'fonts', 'Rubik[wght].ttf')]
FONT = os.environ.get('FONT') or next((f for f in FONTS if os.path.exists(f)), FONTS[0])
PAPER, INK, RED, TAPE = (251, 244, 226, 255), (24, 22, 26, 255), (196, 48, 52, 255), (236, 222, 170, 210)


def font(size, weight=900):
    f = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f


def wrap(text, f, maxw, d):
    if '\n' in text: return [t.strip() for t in text.split('\n') if t.strip()]
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def card(text, top, bottom):
    """Full-frame RGBA layer: a slightly tilted paper note (series look: the 'נא להמתין' sign) with hook B."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    bw, bh = 980, bottom - top
    note = Image.new('RGBA', (bw + 40, bh + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(note)
    d.rounded_rectangle([24, 26, bw + 24, bh + 26], radius=22, fill=(0, 0, 0, 70))          # shadow
    d.rounded_rectangle([14, 14, bw + 14, bh + 14], radius=22, fill=PAPER, outline=(214, 200, 168, 255), width=3)
    d.rectangle([bw // 2 - 70, 0, bw // 2 + 110, 34], fill=TAPE)                              # tape strip
    size = 104
    while True:
        f = font(size); lines = wrap(text, f, bw - 90, d)
        lh = int(size * 1.18)
        if (len(lines) <= 2 and lh * len(lines) <= bh - 50) or size <= 56: break
        size -= 4
    y = 14 + (bh - lh * len(lines)) / 2 + lh / 2
    for i, ln in enumerate(lines):
        d.text((14 + bw / 2, y), ln, font=f, fill=RED if (i == 0 and len(lines) > 1) else INK, anchor='mm', direction='rtl')
        y += lh
    note = note.rotate(-1.6, resample=Image.BICUBIC, expand=False)
    layer.alpha_composite(note, ((W - note.width) // 2, top - 20))
    return layer


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True, check=True).stdout)


def has_audio(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', p],
                         capture_output=True, text=True).stdout
    return bool(out.strip())


ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30',
       '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart']


def mode_text(src, out, hook, secs, top, bottom):
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, 'card.png'); card(hook, top, bottom).save(png)
        fo = max(0.15, min(0.3, secs / 8))
        fc = (f"[1:v]format=rgba,fade=t=out:st={secs - fo:.2f}:d={fo:.2f}:alpha=1[c];"
              f"[0:v]scale={W}:{H},setsar=1[b];[b][c]overlay=0:0:enable='lte(t,{secs:.2f})'[v]")
        amap = ['-map', '0:a'] if has_audio(src) else []
        run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-loop', '1', '-t', f'{secs:.2f}', '-i', png,
             '-filter_complex', fc, '-map', '[v]', *amap, *ENC, out])


def mode_coldopen(src, out, hook, t0, dur, top, bottom):
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, 'card.png'); card(hook, top, bottom).save(png)
        aud = has_audio(src)
        a_pre = f"[0:a]atrim=start={t0:.2f}:duration={dur:.2f},asetpts=PTS-STARTPTS,afade=t=out:st={dur - 0.15:.2f}:d=0.15[ap];" if aud else ''
        fc = (f"[0:v]scale={W}:{H},setsar=1,split[v0][v1];"
              f"[v0]trim=start={t0:.2f}:duration={dur:.2f},setpts=PTS-STARTPTS[pre0];[pre0][1:v]overlay=0:0[pre];"
              f"[v1]setpts=PTS-STARTPTS[main];" + a_pre +
              (f"[pre][ap][main][0:a]concat=n=2:v=1:a=1[v][a]" if aud else f"[pre][main]concat=n=2:v=1:a=0[v]"))
        maps = ['-map', '[v]'] + (['-map', '[a]'] if aud else [])
        run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-loop', '1', '-t', f'{dur:.2f}', '-i', png,
             '-filter_complex', fc, *maps, *ENC, out])


def sheet(a, b, out):
    with tempfile.TemporaryDirectory() as td:
        rows = []
        for p in (a, b):
            ims = []
            for t in (0.1, 0.9, 1.8, 2.8):
                f = os.path.join(td, f'{len(rows)}_{t}.png')
                run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', p, '-frames:v', '1', '-vf', 'scale=270:-1', f])
                ims.append(Image.open(f).convert('RGB'))
            rows.append(ims)
        w, h = rows[0][0].size; c = Image.new('RGB', (w * 4, h * 2), 'white')
        for r, ims in enumerate(rows):
            for i, im in enumerate(ims): c.paste(im, (i * w, r * h))
        c.save(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['text', 'coldopen', 'sheet'])
    ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('hook')
    ap.add_argument('--secs', type=float, default=2.2)
    ap.add_argument('--from', dest='t0', type=float, default=None)
    ap.add_argument('--dur', type=float, default=1.2)
    ap.add_argument('--top', type=int, default=80)
    ap.add_argument('--bottom', type=int, default=430)
    a = ap.parse_args()
    if a.mode == 'sheet':
        sheet(a.src, a.out, a.hook); print(a.hook); sys.exit(0)
    if a.mode == 'text':
        mode_text(a.src, a.out, a.hook, a.secs, a.top, a.bottom)
    else:
        if a.t0 is None: sys.exit('coldopen needs --from <seconds> (the payoff moment)')
        mode_coldopen(a.src, a.out, a.hook, a.t0, a.dur, a.top, a.bottom)
    if os.path.getsize(a.out) > 19_000_000:   # jsDelivr serves files up to 20 MB
        tmp = a.out + '.small.mp4'
        run(['ffmpeg', '-v', 'error', '-y', '-i', a.out, '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-maxrate', '2800k',
             '-bufsize', '5600k', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', tmp])
        os.replace(tmp, a.out)
    print(f'{a.out}  {duration(a.src):.2f}s -> {duration(a.out):.2f}s  {os.path.getsize(a.out) / 1e6:.1f} MB')
