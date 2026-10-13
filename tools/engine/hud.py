#!/usr/bin/env python3
"""
"אתם מחליטים" overlays (Series Bible §N) — a fixed game HUD, a viewer-comment card and the vote card.

  from hud import hud, comment_card, vote_card, rules_card
  hud(frame, 'פרק 1', followers=212, queue=500, pop=None)      # draws in place on an RGBA 1080x1920 frame
  layer = comment_card('someone', 'שילך לבנק', 12, example=True, glow=0.0)   # RGBA layer, paste with make_video.paste_center
  layer = vote_card()                                          # end card: "מה החתול עושה מחר?"
  python3 hud.py demo                                          # → out/hud_demo.png

All sizes are 1080x1920 units. Pills sit at y 70–150, out of the hook caption's way (y≈250) and the platform UI.
No emoji glyphs (the fonts have none): the icons are drawn.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter
import make_video as m
from make_video import W, H, font, WHITE

INK = (20, 20, 26)
YELLOW = (255, 214, 64)
PINK = (255, 92, 120)
CARD = (24, 26, 34)
CARD_LINE = (60, 64, 80)
MUTED = (160, 166, 184)
ORANGE = (255, 140, 40)
PILL_H = 76
PILL_Y = 74


def _pill(label, icon=None, fill=(255, 255, 255), ink=INK, scale=1.0):
    """One rounded pill as an RGBA image. icon: 'person' | 'ticket' | None."""
    f = font(int(40 * scale), 800)
    tw = int(ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(label, font=f))
    pad = int(26 * scale); ic = int(44 * scale) if icon else 0; gap = int(12 * scale) if icon else 0
    w, h = tw + 2 * pad + ic + gap, int(PILL_H * scale)
    im = Image.new('RGBA', (w + 12, h + 14), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([6, 10, w + 6, h + 10], radius=h // 2, fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w, h], radius=h // 2, fill=fill, outline=(0, 0, 0), width=max(3, int(4 * scale)))
    # RTL: icon on the right, text to its left
    x_icon = w - pad - ic
    cy = h // 2
    if icon == 'person':
        r = ic * 0.22
        d.ellipse([x_icon + ic / 2 - r, cy - ic * 0.42, x_icon + ic / 2 + r, cy - ic * 0.42 + 2 * r], fill=ink)
        d.pieslice([x_icon + ic * 0.12, cy - ic * 0.02, x_icon + ic * 0.88, cy + ic * 0.72], 180, 360, fill=ink)
    elif icon == 'ticket':
        x0, y0, x1, y1 = x_icon, cy - ic * 0.32, x_icon + ic, cy + ic * 0.32
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(6 * scale), fill=ORANGE, outline=ink, width=max(2, int(3 * scale)))
        for yy in (y0, y1):
            d.ellipse([x0 + ic / 2 - 6 * scale, yy - 6 * scale, x0 + ic / 2 + 6 * scale, yy + 6 * scale], fill=fill)
        d.line([x0 + ic / 2, y0 + 7 * scale, x0 + ic / 2, y1 - 7 * scale], fill=ink, width=max(2, int(3 * scale)))
    d.text((pad + tw / 2, cy + 1), label, font=f, fill=ink, anchor='mm')
    return im


def hud(frame, ep_label, followers=None, queue=None, pop=None, scale=1.0):
    """Draw the HUD on an RGBA frame in place.
    pop = None (all visible) or a dict {'ep': k, 'followers': k, 'queue': k} with 0..1 drop-in progress per pill."""
    def k_of(key):
        if pop is None: return 1.0
        return max(0.0, min(1.0, pop.get(key, 1.0)))
    items = [('ep', _pill(ep_label, None, fill=YELLOW, scale=scale), 'left')]
    if followers is not None: items.append(('followers', _pill(f'{int(followers):,}', 'person', scale=scale), 'right'))
    if queue is not None: items.append(('queue', _pill(f'{int(queue)}', 'ticket', scale=scale), 'right'))
    x_left, x_right = 40, W - 40
    for key, im, side in items:
        k = k_of(key)
        if k <= 0: continue
        e = 1 - (1 - k) ** 3
        bounce = 1 + 0.18 * math.sin(math.pi * min(1, k * 1.3)) * (1 - k)
        im2 = im if abs(bounce - 1) < 1e-3 else im.resize((int(im.width * bounce), int(im.height * bounce)), Image.BICUBIC)
        y = int(PILL_Y - (1 - e) * 140)
        if side == 'left':
            x = x_left; x_left += im.width + 14
        else:
            x = x_right - im2.width; x_right -= im.width + 14
        if k < 1:
            a = im2.split()[3].point(lambda v: int(v * min(1, k * 2)))
            im2 = im2.copy(); im2.putalpha(a)
        frame.alpha_composite(im2, (x, y))
    return frame


def _wrap(text, f, width, d):
    words, lines, cur = text.split(), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=f) <= width or not cur: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines


def comment_card(username, text, likes, example=False, glow=0.0, width=900):
    """A viewer comment as an Instagram-like dark card. glow 0..1 = the winner highlight."""
    words = text.split()
    if len(words) > 12: text = ' '.join(words[:12]) + '…'
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    ft, fu, fl = font(46, 700), font(34, 700), font(34, 800)
    lines = _wrap(text, ft, width - 190, d0)
    h = 120 + 58 * len(lines) + 24
    pad = 30
    im = Image.new('RGBA', (width + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if glow > 0:
        g = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle([pad - 10, pad - 10, pad + width + 10, pad + h + 10], radius=44, fill=YELLOW + (int(200 * glow),))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([pad + 6, pad + 14, pad + width + 6, pad + h + 14], radius=36, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = pad, pad, pad + width, pad + h
    d.rounded_rectangle([x0, y0, x1, y1], radius=36, fill=CARD, outline=YELLOW if glow > 0.5 else CARD_LINE, width=5 if glow > 0.5 else 3)
    # avatar (right side, RTL)
    ax = x1 - 40 - 76; ay = y0 + 34
    d.ellipse([ax, ay, ax + 76, ay + 76], fill=(255, 150, 60))
    d.text((ax + 38, ay + 40), (username[:1] or '?').upper(), font=font(40, 900), fill=WHITE, anchor='mm')
    # username (LTR handle, right-aligned next to the avatar)
    d.text((ax - 20, ay + 22), '@' + username, font=fu, fill=WHITE, anchor='rm')
    # heart + likes (top-left, on the username row)
    hx, hy = x0 + 62, ay + 22
    s_ = 15
    d.ellipse([hx - 2 * s_, hy - s_, hx, hy + s_ // 2], fill=PINK); d.ellipse([hx, hy - s_, hx + 2 * s_, hy + s_ // 2], fill=PINK)
    d.polygon([(hx - 2 * s_ + 1, hy + 2), (hx + 2 * s_ - 1, hy + 2), (hx, hy + 2 * s_ + 4)], fill=PINK)
    lw = d.textlength(f'{int(likes):,}', font=fl)
    d.text((hx + 2 * s_ + 14, hy + 4), f'{int(likes):,}', font=fl, fill=WHITE, anchor='lm')
    if example:
        tag = 'לדוגמה'; tw = d.textlength(tag, font=font(28, 800)); tx = hx + 2 * s_ + 14 + lw + 24
        d.rounded_rectangle([tx, hy - 22, tx + tw + 28, hy + 22], radius=22, fill=(70, 74, 92))
        d.text((tx + 14 + tw / 2, hy), tag, font=font(28, 800), fill=WHITE, anchor='mm')
    yy = ay + 74
    for ln in lines:
        d.text((ax - 20, yy + 26), ln, font=ft, fill=WHITE, anchor='rm'); yy += 58
    return im


def _plain_card(lines_big, lines_small, accent=YELLOW, width=940):
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    fb, fs = font(76, 900), font(44, 800)
    h = 70 + 92 * len(lines_big) + 70 * len(lines_small) + 50
    pad = 30
    im = Image.new('RGBA', (width + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([pad + 6, pad + 16, pad + width + 6, pad + h + 16], radius=44, fill=(0, 0, 0, 130))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad, pad, pad + width, pad + h], radius=44, fill=(255, 255, 255), outline=(0, 0, 0), width=6)
    y = pad + 70
    for ln in lines_big:
        s = 76
        while d0.textlength(ln, font=font(s, 900)) > width - 80 and s > 40: s -= 2
        d.text((pad + width / 2, y + 30), ln, font=font(s, 900), fill=INK, anchor='mm'); y += 92
    for ln in lines_small:
        tw = d0.textlength(ln, font=fs)
        d.rounded_rectangle([pad + width / 2 - tw / 2 - 26, y - 4, pad + width / 2 + tw / 2 + 26, y + 58], radius=29, fill=accent)
        d.text((pad + width / 2, y + 27), ln, font=fs, fill=INK, anchor='mm'); y += 70
    return im


def vote_card():
    """End card for every arc episode (§N rule 1)."""
    return _plain_card(['מה החתול עושה מחר?'], ['התגובה עם הכי הרבה לייקים קובעת', 'כל עוקב חדש = מקום אחד קדימה בתור'])


def rules_card(which):
    """Pilot explainer cards. which = 'vote' | 'follow'."""
    if which == 'vote':
        return _plain_card(['אתם מחליטים.'], ['התגובה עם הכי הרבה לייקים קובעת'])
    return _plain_card(['כל עוקב חדש'], ['= מקום אחד קדימה בתור'])


def queue_of(arc, followers_now):
    """§N rule 2: queue_start − (followers_now − followers_base), never below 1."""
    if followers_now is None or arc.get('followers_base') is None: return None
    return max(1, int(arc.get('queue_start', 500)) - (int(followers_now) - int(arc['followers_base'])))


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'demo':
    m.init_static()
    src = sys.argv[2] if len(sys.argv) > 2 else None
    if src and os.path.exists(src):
        bg = Image.open(src).convert('RGB').resize((W, H)).convert('RGBA')
    else:
        bg = Image.new('RGBA', (W, H), (200, 214, 232, 255))
    a = bg.copy(); hud(a, 'פרק 1', 212, 500)
    m.paste_center(a, comment_card('noa.example', 'שילך סוף סוף לסדר את הארנונה', 108, glow=1.0), W / 2, 760)
    m.paste_center(a, comment_card('dudi.example', 'שיתקשר לבנק ויבקש לדבר עם מנהל', 57, example=True), W / 2, 1100)
    b = bg.copy(); hud(b, 'פרק 1', 212, 499)
    m.paste_center(b, vote_card(), W / 2, 980)
    sheet = Image.new('RGB', (W, H // 2))
    sheet.paste(a.convert('RGB').resize((W // 2, H // 2)), (0, 0)); sheet.paste(b.convert('RGB').resize((W // 2, H // 2)), (W // 2, 0))
    out = os.path.join(m.OUTDIR, 'hud_demo.png'); sheet.save(out); print(out)
