#!/usr/bin/env python3
"""Character sheet: the ginger cat + Shoko (שוקו), the new black cat. Same rig as make_video.draw_head,
recoloured through the module palette, plus Shoko's props (sunglasses on the head, toothpick)."""
import os, math
from PIL import Image, ImageDraw
import make_video as m

m.K = 2
K = m.K
W, H = 1080, 1420

GINGER = dict(FUR=m.FUR, FUR_D=m.FUR_D, OUT=m.OUT, CREAM=m.CREAM, PINK=m.PINK, IRIS=m.IRIS)
SHOKO = dict(FUR=(62, 62, 74), FUR_D=(38, 38, 48), OUT=(14, 14, 18), CREAM=(128, 128, 142),
             PINK=(178, 104, 124), IRIS=(206, 214, 58))

def palette(p):
    for k, v in p.items(): setattr(m, k, v)

def st(**kw):
    s = dict(lid=0.0, pupil='normal', mouth='flat', ear_dy=0.0, ear_droop=0.0, blush=0.0, sweat=0.0, twitch=False,
             eye_mode='open', brow='none', cobweb=0.0, look=(0, 0), red=0.0)
    s.update(kw); return s

def shades(d, ox, oy):
    """sunglasses pushed up on the forehead, drawn in head-layer units offset by (ox, oy)"""
    for cx in (205, 315):
        m.poly(d, [(ox + cx - 50, oy + 118), (ox + cx + 50, oy + 118), (ox + cx + 42, oy + 152), (ox + cx - 42, oy + 152)],
               fill=(20, 20, 26), outline=(0, 0, 0), width=5)
        m.line(d, [(ox + cx - 34, oy + 126), (ox + cx - 14, oy + 126)], (120, 160, 200), 4)
    m.line(d, [(ox + 255, oy + 128), (ox + 265, oy + 128)], (0, 0, 0), 7)

def toothpick(d, ox, oy):
    m.line(d, [(ox + 288, oy + 318), (ox + 352, oy + 296)], (222, 190, 130), 6)
    m.line(d, [(ox + 288, oy + 318), (ox + 352, oy + 296)], (150, 116, 70), 1)

def character(img, hx, hy, pal, state, scale=1.0, props=False, body=True):
    palette(pal)
    d = ImageDraw.Draw(img)
    ox, oy = hx - 260 * scale, hy - 245 * scale
    if body:
        m.E(d, hx, hy + 292 * scale, 205 * scale, 215 * scale, fill=m.FUR, outline=m.OUT, width=6)
        m.E(d, hx, hy + 330 * scale, 92 * scale, 145 * scale, fill=m.CREAM)
    L, _ = m.draw_head(state, 0)
    if scale != 1.0:
        L = L.resize((int(L.width * scale), int(L.height * scale)), Image.LANCZOS)
    if props:
        dl = ImageDraw.Draw(L)
        sk = m.K; m.K = K * scale
        shades(dl, 0, 0); toothpick(dl, 0, 0)
        m.K = sk
    img.alpha_composite(L, dest=(int(ox * K), int(oy * K)))

def label(img, x, y, text, size, fill=(30, 30, 36), weight=800):
    d = ImageDraw.Draw(img)
    f = m.font(size * K, weight)
    w = d.textlength(text, font=f, direction='rtl')
    d.text((x * K - w / 2, y * K), text, font=f, fill=fill, direction='rtl')

def main():
    img = Image.new('RGBA', (W * K, H * K), (246, 240, 226, 255))
    d = ImageDraw.Draw(img)
    m.poly(d, [(0, 0), (W, 0), (W, 120), (0, 120)], fill=(255, 210, 70))
    label(img, W / 2, 30, 'חתול בהמתנה · הצמד', 56)
    # the pair, full body
    character(img, 300, 390, GINGER, st(sweat=1.0, brow='sad', mouth='flat', look=(14, 2), pupil='big'), 0.82)
    character(img, 790, 390, SHOKO, st(lid=0.55, brow='annoyed', mouth='smile_small', look=(-10, 4)), 0.82, props=True)
    label(img, 300, 830, 'הג׳ינג׳י', 46)
    label(img, 300, 888, 'לפי הספר · מזיע · מפסיד', 30, (90, 70, 50), 600)
    label(img, 790, 830, 'שוקו', 46)
    label(img, 790, 888, 'שאנן · עוקף · מנצח', 30, (60, 60, 70), 600)
    # Shoko expressions row
    m.poly(d, [(0, 950), (W, 950), (W, 954), (0, 954)], fill=(200, 190, 170))
    label(img, W / 2, 970, 'שוקו: שלוש הבעות', 38)
    row = [(190, st(lid=0.55, mouth='smile_small', brow='annoyed', look=(-8, 4)), 'רגוע'),
           (540, st(lid=0.62, mouth='goofy', brow='none', look=(-14, 6)), 'מרוצה מעצמו'),
           (890, st(lid=0.0, pupil='tiny', mouth='flat', brow='up', sweat=1.0), 'נדיר: נלחץ')]
    for x, s_, t in row:
        character(img, x, 1150, SHOKO, s_, 0.62, props=True, body=False)
        label(img, x, 1345, t, 32, (60, 60, 70), 700)
    out = img.convert('RGB').resize((W, H), Image.LANCZOS)
    os.makedirs('out', exist_ok=True)
    out.save('out/shoko_sheet.png', optimize=True)
    print('out/shoko_sheet.png')

if __name__ == '__main__':
    main()
