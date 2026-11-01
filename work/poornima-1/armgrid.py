# rows = seeds, cols = frames; tiny tiles for eye QC of one arm
import cv2, sys, glob, numpy as np
arm, out = sys.argv[1], sys.argv[2]; fr = [0, 24, 48, 66, 80, 92]
rows = []
for p in sorted(glob.glob(f"clips_h100/arm{arm}_*_s*.mp4"), key=lambda s: int(s.split('_s')[-1][:-4])):
    c = cv2.VideoCapture(p); t = []
    for i in fr:
        c.set(1, i); ok, f = c.read(); f = cv2.resize(f, (277, 160))
        cv2.putText(f, f"s{p.split('_s')[-1][:-4]} f{i}", (3, 15), 0, 0.5, (0, 0, 255), 1); t.append(f)
    rows.append(np.hstack(t))
cv2.imwrite(out, np.vstack(rows))
