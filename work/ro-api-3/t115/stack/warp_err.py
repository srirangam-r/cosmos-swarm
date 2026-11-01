"""Temporal-consistency score for the pendulum crop: Farneback flow t->t+1, warp t+1 back to t,
mean |residual| (grey 0-255) inside the moving pixels, divided by mean |frame diff| there.
Low ratio = motion explained by smooth flow (rigid); high = blending/smearing/duplication.
Usage: warp_err.py out.json clip1.mp4 ..."""
import cv2, numpy as np, sys, json
Y0, Y1, X0, X1 = 0, 330, 170, 430   # pendulum region at 832x480 (same crop as zoomrow2.py)
def score(p):
    c = cv2.VideoCapture(p); fr = []
    while 1:
        ok, f = c.read()
        if not ok: break
        fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[Y0:Y1, X0:X1].astype(np.float32))
    h, w = fr[0].shape; gx, gy = np.meshgrid(np.arange(w), np.arange(h)); ratios = []; res = []
    for a, b in zip(fr[1:-1], fr[2:]):   # skip frame 0 (conditioning frame)
        fl = cv2.calcOpticalFlowFarneback(a.astype(np.uint8), b.astype(np.uint8), None, 0.5, 4, 15, 3, 5, 1.2, 0)
        wb = cv2.remap(b, (gx + fl[..., 0]).astype(np.float32), (gy + fl[..., 1]).astype(np.float32), cv2.INTER_LINEAR)
        d = np.abs(b - a); m = d > 12
        if m.sum() < 50: continue
        r = np.abs(wb - a)[m].mean(); ratios.append(r / d[m].mean()); res.append(r)
    return {"warp_ratio_mean": float(np.mean(ratios)), "warp_ratio_p90": float(np.percentile(ratios, 90)),
            "resid_mean": float(np.mean(res)), "n_pairs": len(ratios)}
out = {p.split('/')[-1][:-4]: score(p) for p in sys.argv[2:]}
json.dump(out, open(sys.argv[1], "w"), indent=1)
for k, v in out.items(): print(f"{k:32s} ratio {v['warp_ratio_mean']:.3f} p90 {v['warp_ratio_p90']:.3f} resid {v['resid_mean']:.2f} n {v['n_pairs']}")
