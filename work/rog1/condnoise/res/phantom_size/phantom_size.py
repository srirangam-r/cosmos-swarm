#!/usr/bin/env python3
"""Phantom-ball diameter (scout-1 #2519 test 1). For each clip: dark pixels at frame t (grey<TH_DARK) that were bright
in frame 0 (grey>TH_BRIGHT) -> connected components; keep round blobs (aspect 0.7-1.4, fill>0.55, area>60 px).
Report per frame the best blob's bbox w/h and equivalent diameter; writes a QC strip with the blob boxed.
Partial occlusion against the black curtain/table makes blobs SMALLER, so per-clip max over frames is the estimate.
Usage: phantom_size.py out.json qcdir clip.mp4 ..."""
import sys, json, os, cv2, numpy as np
out, qcd, clips = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(qcd, exist_ok=True)
TH_DARK, TH_BRIGHT = 70, 110
res = {}
for p in clips:
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    g0 = cv2.GaussianBlur(cv2.cvtColor(fr[0], cv2.COLOR_BGR2GRAY), (3, 3), 0)
    per = []
    for t in range(1, min(len(fr), 61)):
        g = cv2.GaussianBlur(cv2.cvtColor(fr[t], cv2.COLOR_BGR2GRAY), (3, 3), 0)
        m = ((g < TH_DARK) & (g0 > TH_BRIGHT)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        best = None
        for i in range(1, n):
            x, y, w, h, a = st[i]
            if a < 60 or not (0.7 <= w / h <= 1.4) or a / (w * h) < 0.55: continue
            if best is None or a > best[4]: best = (int(x), int(y), int(w), int(h), int(a))
        if best:
            per.append({"t": t, "x": best[0], "y": best[1], "w": best[2], "h": best[3], "area": best[4],
                        "d_eq": float(2 * np.sqrt(best[4] / np.pi))})
    name = os.path.basename(p)[:-4]
    if per:
        top = sorted(per, key=lambda r: -r["d_eq"])[:5]
        res[name] = {"n_frames_detected": len(per), "d_eq_max": top[0]["d_eq"], "d_eq_top5_median": float(np.median([r["d_eq"] for r in top])),
                     "first_t": per[0]["t"], "top": top}
        tiles = []
        for r in top[:4]:
            im = fr[r["t"]].copy(); cx, cy = r["x"] + r["w"] // 2, r["y"] + r["h"] // 2
            cv2.rectangle(im, (r["x"], r["y"]), (r["x"] + r["w"], r["y"] + r["h"]), (0, 0, 255), 1)
            x0, y0 = max(0, cx - 60), max(0, cy - 60)
            c = im[y0:y0 + 120, x0:x0 + 120]
            c = cv2.copyMakeBorder(c, 0, 120 - c.shape[0], 0, 120 - c.shape[1], cv2.BORDER_CONSTANT)
            c = cv2.resize(c, (240, 240), interpolation=cv2.INTER_NEAREST)
            cv2.putText(c, f"f{r['t']} d{r['d_eq']:.0f}", (4, 16), 0, 0.5, (0, 255, 255), 1); tiles.append(c)
        cv2.imwrite(os.path.join(qcd, name + "_qc.jpg"), np.hstack(tiles))
    else:
        res[name] = {"n_frames_detected": 0}
json.dump(res, open(out, "w"), indent=1)
for k, v in res.items():
    print(k, v.get("n_frames_detected"), round(v.get("d_eq_max", 0), 1), round(v.get("d_eq_top5_median", 0), 1), v.get("first_t"))
