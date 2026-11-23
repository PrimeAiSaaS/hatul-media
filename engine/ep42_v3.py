#!/usr/bin/env python3
"""
"חתול בהמתנה" — פרק 42 v3 (polish 23.11: ice cream cup + scoops + spoon melting with the clock, big puddle on the break, bent shorter arm; base = ep42p.py):\n הפסקת חשמל + שעון אמיתי (Gabi 22.11, lesson 20261122-1600-claude-real-clock, rebuild_clock).
Same voices, plant (the "ראשי" switch), climb and break as ep42.py; the only addition is a red LED countdown
"הגלידה נמסה בעוד 00:SS" that counts real seconds from frame 0 and hits 00:00 a beat before he flips "ראשי" (the ice
cream is a puddle the moment the light comes back). Soft tick on every second, louder in the last 5, a buzz on 00:00.

  python3 ep42_v2.py times | test t1 t2 ... | render   -> out/ep42_hashmal_v2.mp4
"""
import os, sys
os.environ.setdefault('OUTNAME', 'ep42_hashmal_v3')
import ep42p as E
import clock_overlay as C

LABEL = ['הגלידה', 'נמסה בעוד']
ZERO = E.FLIP - 0.05                       # 00:00 just before the paw flips "ראשי"

def clock_state(t):
    name = E.shot(t)[0]
    st = E.story_t(t)
    s = C.secs_left(st, ZERO)
    if name == 'rewind': return s, 'run', True
    if s == 0: return 0, 'zero', False
    return s, ('hot' if s <= 5 else 'run'), False

_draw = E.draw_frame
def draw_frame(i):
    t = i / E.FPS
    fr = _draw(i)
    if t >= E.DUR - 0.25: return fr        # the whip: the clock rides the blur out, frame 0 brings it back
    fr = fr.convert('RGBA')
    s, state, scr = clock_state(t)
    C.draw(fr, LABEL, s, state, t, scr)
    return fr.convert('RGB')
E.draw_frame = draw_frame

_audio = E.build_audio
def build_audio(path):
    _audio(path)
    ticks, prev = [], None
    for i in range(int(E.DUR * E.FPS)):
        t = i / E.FPS; s, state, scr = clock_state(t)
        if scr: prev = None; continue
        if prev is not None and s != prev and s > 0: ticks.append(t)
        prev = s
    C.add_ticks(path, ticks, loud_from=ZERO - 5.0, final=ZERO)
E.build_audio = build_audio

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'times':
        print('ZERO', round(ZERO, 2), 'frame0', C.secs_left(E.story_t(0), ZERO), 'T0', C.secs_left(E.story_t(E.T0 + 0.01), ZERO))
    E.main()
