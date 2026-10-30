#!/usr/bin/env python3
"""Reel covers (1080x1920) per episode: a key frame + episode badge + title, inside the 3:4 grid-safe area."""
import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFilter
import make_video as m

OUT = os.path.join(m.OUTDIR, 'covers'); os.makedirs(OUT, exist_ok=True)
BRAND = (255, 204, 64)
EPISODES = [  # file, frame time (no on-screen caption there), episode number, title
    ('cat_on_hold.mp4', 9.8, 1, 'ביטוח לאומי'),
    ('ep2_bank_sms.mp4', 9.8, 2, 'קוד ה-SMS'),
    ('ep3_branch.mp4', 8.8, 3, 'הסניף'),
    ('ep4_fax.mp4', 9.7, 4, 'הפקס'),
    ('ep5_finale.mp4', 6.2, 5, 'סוף עונה'),
    ('ep6_voter.mp4', 7.0, 6, 'ההודעה לבוחר'),
    ('ep7_payment.mp4', 5.3, 7, 'הקצבה של ה-12'),
    ('ep8_arnona.mp4', 9.05, 8, 'ארנונה'),
    ('ep9_address.mp4', 4.3, 9, 'שינוי כתובת'),
    ('ep10_election.mp4', 9.7, 10, 'יום הבחירות'),
    ('arc1_pilot.mp4', 11.0, 'arc1', 'אתם מחליטים'),   # arc episodes: n = doc key, badge 'החלטה N'
    ('ep11_outage.mp4', 3.3, 11, 'תקלה אזורית'),
    ('ep12_sms.mp4', 6.3, 12, 'קוד ה-SMS'),
    ('ep13.mp4', 8.23, 13, 'משרד הפנים בלי תור'),
    ('ep14_80s.mp4', 5.2, 14, 'ביטוח לאומי, שנות ה-80'),
    ('ep15_norm.mp4', 7.12, 15, 'הטכנאי מגיע'),
    ('arc2_final.mp4', 9.0, 'arc2', 'ספח לקלפי?'),
    ('ep16_norm.mp4', 3.3, 16, 'טסט לרכב'),
    ('ep17_norm.mp4', 9.15, 17, 'ביטוח רכב'),
    ('ep18_v2_norm.mp4', 3.65, 18, 'דוח חניה'),   # v2 (§P, 28.10): two-shot, the stamp in the air, no caption
    ('ep19.mp4', 6.4, 19, 'התמונה לרישיון'),   # two-shot before the punchline (no caption there)   # built from ep18.draw_frame(210) with CAPTIONS=[] (every cat frame has a caption)
    ('ep20_v2_norm.mp4', 11.0, 20, 'הגרר'),   # v2 (§P, 29.10): peak in the car, eyes closed, the clock at 15:59 (no caption 9.8–)
    ('ep21_v2_norm.mp4', 10.95, 21, 'החשבון הוקפא'),   # v2 (§P, 30.10): peak, card over the terminal (no caption 10.65–)
    ('ep22_norm.mp4', 11.4, 22, 'הפרטים דלפו'),
    ('ep23_norm.mp4', 11.5, 23, 'קוד ה-SMS'),   # §P peak: paw over "כניסה", 23:59:57 (no caption 11.05–)   # §P peak: eyes closed, the bag with the code on the counter (no caption 11.15–12.0)   # two-shot before "וואלה." (no caption 7.8–8.15)   # Eilat, the new notice just slapped on (no caption 10.3–11.2)
]

def grab(mp4, t):
    png = os.path.join(OUT, f'_frame_{os.path.basename(mp4)}.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', os.path.join(m.OUTDIR, mp4), '-frames:v', '1', png], check=True)
    return Image.open(png).convert('RGBA')

def shade(img):
    """darken the top band so the title pops, keep the cat bright"""
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for y in range(0, 760, 4):
        a = int(150 * (1 - y / 760) ** 1.4)
        d.rectangle([0, y, W, y + 4], fill=(10, 10, 14, a))
    img.alpha_composite(ov)

def cover(mp4, t, n, title):
    img = grab(mp4, t); shade(img); d = ImageDraw.Draw(img)
    W = img.width
    # title plate (solid, so the busy set behind never fights the text)
    size = 138
    while d.textlength(title, font=m.font(size, 900)) > W - 220: size -= 4
    tw = int(d.textlength(title, font=m.font(size, 900))) + 110
    d.rounded_rectangle([W / 2 - tw / 2, 400, W / 2 + tw / 2, 590], radius=36, fill=(16, 16, 20))
    d.text((W / 2, 498), title, font=m.font(size, 900), fill=(255, 255, 255), anchor='mm')
    # episode badge, overlapping the plate's top edge
    bf = m.font(54, 900); label = f'החלטה {str(n)[3:]}' if str(n).startswith('arc') else f'פרק {n}'
    bw = int(d.textlength(label, font=bf)) + 70
    d.rounded_rectangle([W / 2 - bw / 2, 340, W / 2 + bw / 2, 430], radius=45, fill=BRAND, outline=(16, 16, 20), width=6)
    d.text((W / 2, 385), label, font=bf, fill=(20, 18, 14), anchor='mm')
    # series name at the bottom of the safe area
    sf = m.font(52, 800); s = 'חתול בהמתנה'
    sw = int(d.textlength(s, font=sf)) + 60
    d.rounded_rectangle([W / 2 - sw / 2, 1548, W / 2 + sw / 2, 1626], radius=39, fill=(10, 10, 14, 230))
    d.text((W / 2, 1587), s, font=sf, fill=BRAND, anchor='mm')
    path = os.path.join(OUT, f'cover_{n}.png' if str(n).startswith('arc') else f'cover_ep{n}.png')
    img.convert('RGB').save(path, optimize=True)
    return path

def grid_preview(paths):
    """how the covers sit in the profile grid (3:4 crop of the 9:16 frame)"""
    tw, th = 300, 400
    sheet = Image.new('RGB', (tw * 3 + 8, th), (255, 255, 255))
    for k, p in enumerate(paths):
        im = Image.open(p); cw, ch = 1080, 1440
        im = im.crop((0, (1920 - ch) // 2, cw, (1920 + ch) // 2)).resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (k * (tw + 4), 0))
    p = os.path.join(OUT, 'grid_preview.png'); sheet.save(p); return p

if __name__ == '__main__':
    only = sys.argv[1:]
    ps = [cover(*e) for e in EPISODES if not only or str(e[2]) in only]
    for p in ps: print(p)
    print(grid_preview(ps[::-1]))
    for f in os.listdir(OUT):
        if f.startswith('_frame_'): os.remove(os.path.join(OUT, f))
