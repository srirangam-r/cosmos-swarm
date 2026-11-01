#!/usr/bin/env python3
"""ro-1: scout #2602 test 2 -- cut each F/QT clip (and the real ref) into EARLY f0-35 (1.5 s) and LATE f46-92 windows, re-encode (crf 18, 24 fps)."""
import av, sys, os, glob
SRC = sys.argv[1:]
os.makedirs('hue_trunc/clips', exist_ok=True)
for p in SRC:
    fr = [x.to_ndarray(format='rgb24') for x in av.open(p).decode(video=0)]
    b = os.path.basename(p)[:-4]
    for tag, sl in (('early', slice(0, 36)), ('late', slice(46, 93))):
        o = av.open(f'hue_trunc/clips/{tag}__{b}.mp4', 'w'); s = o.add_stream('libx264', rate=24)
        s.width, s.height, s.pix_fmt = fr[0].shape[1], fr[0].shape[0], 'yuv420p'; s.options = {'crf': '18'}
        for c in fr[sl]:
            for pk in s.encode(av.VideoFrame.from_ndarray(c, format='rgb24')): o.mux(pk)
        for pk in s.encode(): o.mux(pk)
        o.close()
    print(b, len(fr))
