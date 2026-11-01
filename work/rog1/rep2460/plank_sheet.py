#!/usr/bin/env python3
"""Eye-coding sheet: native plank crop (x 60-700, y 200-440), frames from START every STEP, 4 columns, scale 0.7.
Usage: plank_sheet.py clip.mp4 out.jpg [start=0] [step=4]"""
import sys, cv2, numpy as np
p, o = sys.argv[1], sys.argv[2]
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
step = int(sys.argv[4]) if len(sys.argv) > 4 else 4
end = int(sys.argv[5]) if len(sys.argv) > 5 else 10**6
cap = cv2.VideoCapture(p); fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(f)
tiles = []
for t in range(start, min(len(fr), end + 1), step):
    c = cv2.resize(fr[t][200:440, 60:700], None, fx=0.7, fy=0.7, interpolation=cv2.INTER_AREA)
    cv2.putText(c, str(t), (4, 18), 0, 0.6, (0, 255, 255), 2); tiles.append(c)
tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % 4)
cv2.imwrite(o, np.vstack([np.hstack(tiles[r:r+4]) for r in range(0, len(tiles), 4)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
