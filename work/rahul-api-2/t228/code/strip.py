"""Contact strip of the pendulum crop (x 200-460, y 60-300) every 6th native frame, one row per clip.
usage: strip.py out.png clip1.mp4 [clip2.mp4 ...]"""
import sys

import cv2
import numpy as np

out = sys.argv[1]
rows = []
for p in sys.argv[2:]:
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok:
            break
        F.append(f)
    tiles = []
    for i in range(0, len(F), 6):
        t = F[i][60:300, 200:460].copy()
        cv2.putText(t, str(i), (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        tiles.append(cv2.resize(t, (130, 120), interpolation=cv2.INTER_AREA))
    row = np.hstack(tiles)
    lab = np.zeros((18, row.shape[1], 3), np.uint8)
    cv2.putText(lab, p.split('/')[-1], (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    rows.append(np.vstack([lab, row]))
w = max(r.shape[1] for r in rows)
rows = [np.pad(r, ((0, 0), (0, w - r.shape[1]), (0, 0))) for r in rows]
cv2.imwrite(out, np.vstack(rows))
