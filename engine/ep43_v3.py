#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 43 v3 (polish 23.11: frame 0 blurs+darkens the set behind the hook; the chips row moved under the clock and fits right of the "438 חלון 3" board; base = ep43p.py):\n תור אונליין: אפריל + שעון אמיתי (Gabi 22.11, lesson 20261122-1600-claude-real-clock, rebuild_clock).
Same voices, plant (Sharit's "בחופשה מ-2.12 עד 4.12"), climb and break as ep43.py; the only addition is a red LED
countdown "ניתוק מהאתר בעוד 00:SS" (the gov-site session timeout) that counts real seconds from frame 0; he books
"מחר" with 00:01 left — the clock stops green — and the cut to the next morning (the break) takes it away.
Soft tick on every second, louder in the last 5, a stop chime-buzz on the booking.

  python3 ep43_v2.py times | test t1 t2 ... | render   -> out/ep43_april_v2.mp4
"""
import os, sys
os.environ.setdefault('OUTNAME', 'ep43_april_v3')
import ep43p as E
import clock_overlay as C

LABEL = ['ניתוק', 'מהאתר בעוד']
ZERO = E.BOOK + 0.6                        # he books with 00:01 left; the clock stops there

def clock_state(t):
    name = E.shot(t)[0]
    st = E.story_t(t)
    s = C.secs_left(st, ZERO)
    if name == 'rewind': return s, 'run', True
    if name in ('morning', 'frozen'): return None, None, False   # next morning: no clock
    if t >= E.BOOK: return C.secs_left(E.BOOK, ZERO), 'done', False
    return s, ('hot' if s <= 5 else 'run'), False

_draw = E.draw_frame
def draw_frame(i):
    t = i / E.FPS
    fr = _draw(i)
    if t >= E.DUR - 0.25: return fr        # the whip: the clock rides the blur out, frame 0 brings it back
    fr = fr.convert('RGBA')
    s, state, scr = clock_state(t)
    if s is None: return fr.convert('RGB')
    C.draw(fr, LABEL, s, state, t, scr)
    return fr.convert('RGB')
E.draw_frame = draw_frame

_audio = E.build_audio
def build_audio(path):
    _audio(path)
    ticks, prev = [], None
    for i in range(int(E.DUR * E.FPS)):
        t = i / E.FPS; s, state, scr = clock_state(t)
        if scr or s is None or state == 'done': prev = None; continue
        if prev is not None and s != prev and s > 0: ticks.append(t)
        prev = s
    C.add_ticks(path, ticks, loud_from=ZERO - 5.0, final=None)
E.build_audio = build_audio

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'times':
        print('ZERO', round(ZERO, 2), 'frame0', C.secs_left(E.story_t(0), ZERO), 'T0', C.secs_left(E.story_t(E.T0 + 0.01), ZERO))
    E.main()
