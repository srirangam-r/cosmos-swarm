# one row per clip: pendulum crop every 4 frames f0..f88 (23 tiles); rows labelled
import cv2, numpy as np, sys
out = sys.argv[1]; rows = []
for p in sys.argv[2:]:
    c = cv2.VideoCapture(p); fr = []
    while 1:
        ok, f = c.read()
        if not ok: break
        fr.append(f)
    t = [cv2.resize(fr[i][0:330, 170:430], (78, 99)) for i in range(0, 92, 4)]
    lab = np.zeros((99, 150, 3), np.uint8); cv2.putText(lab, p.split('/')[-1][3:-4], (2, 50), 0, 0.4, (255, 255, 255), 1)
    rows.append(np.hstack([lab] + t))
cv2.imwrite(out, np.vstack(rows))
