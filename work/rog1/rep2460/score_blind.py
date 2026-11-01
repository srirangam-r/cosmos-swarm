#!/usr/bin/env python3
"""v2 (shift 70): adds late_chg_px = mean over the last 24 frame pairs of #pixels with |grey diff|>20 in the plank crop
(x 60-700, y 200-440, 3x3 blur). The p99 metric below is too coarse: a small ball is <1% of the region (see eye codes).
Blind scorer for the #2460 replication (rog1). Independent of ro-1's analyze.py.
For each clip: (1) moving fraction = share of the last 24 frames (1 s) whose 99th-percentile
abs grey diff to the previous frame, inside the lower scene (y>=120, whole width), is above 5 (codec noise floor 2-4 on the #2460 example clips);
(2) 'still since' = first frame t such that every later frame-pair stays below that threshold.
Also writes a gripper/plank contact sheet (every 4 frames) per clip for the eye codes.
Usage: python3 score_blind.py clipdir out.json"""
import sys, json, glob, os, cv2, numpy as np
d, out = sys.argv[1], sys.argv[2]
res = {}
for p in sorted(glob.glob(os.path.join(d, "r60_*.mp4"))):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (3, 3), 0)[120:].astype(np.int16))
    pc = [f[80:320, 60:700] for f in fr]  # plank crop (y 200-440 of full frame, since fr starts at y=120)
    chg = [int((np.abs(pc[i] - pc[i-1]) > 20).sum()) for i in range(1, len(pc))]
    q = [float(np.percentile(np.abs(fr[i] - fr[i-1]), 99)) for i in range(1, len(fr))]
    mov = [x > 5 for x in q]
    still = len(fr)
    for t in range(len(mov) - 1, -1, -1):
        if mov[t]: break
        still = t + 1
    n = os.path.basename(p)[:-4]
    res[n] = {"frames": len(fr), "moving_frac_last24": float(np.mean(mov[-24:])), "still_since": still,
              "p99diff_last24_mean": float(np.mean(q[-24:])),
              "late_chg_px": float(np.mean(chg[-24:])), "chg_series": chg}
    cap = cv2.VideoCapture(p); raw = []
    while True:
        ok, f = cap.read()
        if not ok: break
        raw.append(f)
    tiles = [cv2.putText(cv2.resize(raw[t], (320, 185)).copy(), str(t), (4, 16), 0, 0.5, (0, 255, 255), 1)
             for t in range(0, len(raw), 4)]
    tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % 6)
    cv2.imwrite(os.path.join(d, n + "_sheet.jpg"),
                np.vstack([np.hstack(tiles[r:r+6]) for r in range(0, len(tiles), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res, indent=1))
