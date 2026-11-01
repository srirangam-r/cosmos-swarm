"""Find the source frame of pend10_mid_f93.png in GAUGE pendulum video 10 and
build a background plate for the pendulum region from nearby frames (median
over frames where the rod/bob is away from the region). usage: plate.py in.png 10.mp4 outdir"""
import sys, json
import cv2, numpy as np
inp, vid, out = sys.argv[1:4]
ref = cv2.imread(inp).astype(np.float32)
cap = cv2.VideoCapture(vid)
F = []
for i in range(400):
    ok, f = cap.read()
    if not ok: break
    L = np.zeros((480, 832, 3), np.uint8); L[6:474] = cv2.resize(f, (832, 468), interpolation=cv2.INTER_AREA)
    F.append(L)
F = np.array(F)
err = np.array([np.abs(x.astype(np.float32) - ref).mean() for x in F])
k = int(err.argmin())
print('best frame', k, 'err', err[k], 'next best', np.sort(err)[:5])
# region of interest around the lower rod and bob
y0, y1, x0, x1 = 140, 300, 250, 380
roi = F[:, y0:y1, x0:x1].astype(np.float32)
med = np.median(roi[max(0, k-120):k+120], axis=0)
dev = np.abs(roi - med).mean(axis=(1, 2, 3))
print('robot-region change vs frame k (x 380-560):', [round(float(np.abs(F[j, 0:300, 380:560].astype(np.float32) - F[k, 0:300, 380:560].astype(np.float32)).mean()), 2) for j in range(max(0, k-120), min(len(F), k+120), 20)])
cv2.imwrite(f'{out}/plate_roi_median.png', med.astype(np.uint8))
np.save(f'{out}/frames_near.npy', F[max(0, k-120):k+120])
json.dump(dict(best_frame=k, err=float(err[k]), win=[max(0, k-120), min(len(F), k+120)]), open(f'{out}/plate_meta.json', 'w'))
