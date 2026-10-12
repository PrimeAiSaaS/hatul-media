#!/usr/bin/env python3
"""Story kit for one episode: two 1080x1920 assets for Instagram/Facebook Stories.
  story_teaser.mp4 — the first 8 s of the episode, scaled to fit inside the story safe zone,
                     with a yellow tag "פרק חדש עולה היום בערב" on top (Stories cover the top ~250 px
                     and the bottom ~340 px with UI, so nothing important goes there).
  story_poll.png   — a darkened key frame + the hook question; the middle is left empty for the
                     poll / question sticker that Gabi adds in the app (stickers can't be added by API).
Usage: python3 story_kit.py <episode.mp4> <out_dir> "<question>" ["<tag text>"]
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = os.environ.get('FONT', '/home/claude/cat_video/fonts/Rubik[wght].ttf')
W, H = 1080, 1920

def font(size, weight=900):
    f = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f

def pill(text, size=54, fg=(20, 18, 22), bg=(255, 204, 64)):
    f = font(size); d0 = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    tw = int(d0.textlength(text, font=f)); h = int(size * 1.7); w = tw + int(size * 1.4)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=bg)
    d.text((w / 2, h / 2), text, font=f, fill=fg, anchor='mm', direction='rtl')
    return im

def wrap(text, f, maxw, d):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def main(src, out, question, tag='פרק חדש עולה היום בערב'):
    os.makedirs(out, exist_ok=True)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
    tag_png = os.path.join(out, '_tag.png'); pill(tag).save(tag_png)
    # teaser: video scaled to 82% and centred a bit low, blurred copy behind it, tag on top
    t = min(8.0, dur)
    fc = ('[0:v]split[a][b];[a]scale=1080:1920,boxblur=30:5,eq=brightness=-0.12[bg];'
          '[b]scale=886:-2[fg];[bg][fg]overlay=(W-w)/2:330[v];[v][1:v]overlay=(W-w)/2:200,format=yuv420p')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-t', f'{t:.2f}', '-i', src, '-i', tag_png, '-filter_complex', fc,
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '4500k', '-bufsize', '9000k',
                    '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-movflags', '+faststart', os.path.join(out, 'story_teaser.mp4')], check=True)
    # poll frame: key frame at 40%, blurred + darkened, question near the top, empty middle for the sticker
    fr = os.path.join(out, '_frame.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{dur * 0.4:.2f}', '-i', src, '-frames:v', '1', '-vf', 'scale=1080:1920', fr], check=True)
    bg = Image.open(fr).convert('RGB').filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new('RGB', bg.size, (12, 10, 14)), 0.45).convert('RGBA')
    d = ImageDraw.Draw(bg); f = font(84)
    lines = wrap(question, f, W - 160, d); y = 330
    for ln in lines:
        d.text((W / 2, y), ln, font=f, fill=(255, 255, 255), anchor='mm', direction='rtl', stroke_width=6, stroke_fill=(12, 12, 14)); y += 110
    p = pill('הסקר כאן למטה', 46); bg.alpha_composite(p, ((W - p.width) // 2, y + 40))
    d.text((W / 2, 1520), '@hatul.bahamtana', font=font(40, 700), fill=(255, 255, 255, 200), anchor='mm')
    bg.convert('RGB').save(os.path.join(out, 'story_poll.png'))
    for x in (tag_png, fr): os.remove(x)
    print(out)

if __name__ == '__main__':
    main(*sys.argv[1:])
