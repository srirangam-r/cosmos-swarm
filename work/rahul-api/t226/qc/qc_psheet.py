#!/usr/bin/env python3
"""Eye-QC sheet for P (not a coding instrument; the analyst is not a coder, Amendment 5): one image per arm, rows = seeds,
columns = pendulum ROI crops at frames 0,6,...,90. usage: qc_psheet.py clip_dir out_dir"""
import sys, os, glob
import numpy as np, cv2
cd, od = sys.argv[1], sys.argv[2]; os.makedirs(od, exist_ok=True)
x0, y0, x1, y1 = 180, 95, 460, 300; FR = list(range(0, 93, 6))
for arm in ('base', 'neutral', 'still', 'fast'):
    rows = []
    for s in range(101, 107):
        p = os.path.join(cd, f't226_P_{arm}_s{s}.mp4')
        if not os.path.exists(p): continue
        c = cv2.VideoCapture(p); F = []
        while True:
            ok, f = c.read()
            if not ok: break
            F.append(cv2.resize(f, (832, 480)) if f.shape[:2] != (480, 832) else f)
        tl = []
        for k in FR:
            t = cv2.resize(F[min(k, len(F) - 1)][y0:y1, x0:x1], (112, 82)); cv2.putText(t, str(k), (1, 10), 0, 0.33, (0, 255, 255), 1); tl.append(t)
        lab = np.zeros((82, 40, 3), np.uint8); cv2.putText(lab, f's{s}', (2, 45), 0, 0.4, (255, 255, 255), 1)
        rows.append(np.hstack([lab] + tl))
    if rows:
        hdr = np.zeros((18, rows[0].shape[1], 3), np.uint8); cv2.putText(hdr, f'P {arm}', (4, 13), 0, 0.45, (255, 255, 255), 1)
        cv2.imwrite(os.path.join(od, f'P_{arm}.jpg'), np.vstack([hdr] + rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
print('ok')
