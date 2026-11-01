#!/usr/bin/env python3
"""Task 175: independent analysis of Rule R clips (kiro-1). Written without reusing task-140 code.

Per clip:
  move_frac[t] = fraction of pixels in a scene ROI whose gray level changed by > 12 between frames t-1 and t
                 (after 3x3 blur), i.e. how much of the scene is moving.
  early = mean move_frac over f1-30, late = mean over f62-92, late_tail = mean over f80-92.
  still_end = late_tail < STILL (0.002, i.e. <0.2% of ROI pixels changing per frame).
Pendulum only: x(t) = intensity-weighted centroid column of bright (rod) pixels in a band below the axle;
  amplitude early/late = (p95 - p5) of x(t) in f1-30 / f62-92; amp_ratio = late/early.
Contact sheet: frames 0, 23, 46, 69, 80, 92 for eye coding of where the object ends.
Nothing here is planted-validated.
"""
import json, sys, glob, os
import numpy as np, cv2

ROI = {  # x0, y0, x1, y1 in 832x480
    "slope_wood": (120, 0, 715, 480),
    "slope_plastic": (120, 0, 715, 480),
    "pend_mid": (200, 100, 420, 300),
}
BAND = (240, 380, 130, 220)  # pendulum rod band x0, x1, y0, y1
STILL = 0.002


def load(p):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    return np.array(fr)


def analyze(p):
    side = json.load(open(p[:-4] + ".json"))
    name = os.path.basename(p)[:-4]
    scene = next(s for s in ROI if s in name)
    arm = name.split(scene + "_")[1].split("_")[0]
    seed = int(name.rsplit("_s", 1)[1])
    g = load(p)
    x0, y0, x1, y1 = ROI[scene]
    r = np.stack([cv2.GaussianBlur(f, (3, 3), 0) for f in g[:, y0:y1, x0:x1]]).astype(np.int16)
    mf = np.r_[0, (np.abs(np.diff(r, axis=0)) > 12).mean(axis=(1, 2))]
    out = dict(name=name, scene=scene, arm=arm, seed=seed, n_frames=len(g),
               endpoint=side.get("endpoint") or side.get("server"),
               early=float(mf[1:31].mean()), late=float(mf[62:93].mean()), late_tail=float(mf[80:93].mean()))
    out["late_over_early"] = out["late"] / max(out["early"], 1e-6)
    out["still_end"] = bool(out["late_tail"] < STILL)
    if scene == "pend_mid":
        bx0, bx1, by0, by1 = BAND
        b = g[:, by0:by1, bx0:bx1].astype(float)
        w = np.clip(b - 120, 0, None)  # rod is light wood against dark curtain
        xs = np.arange(bx0, bx1)
        x = (w.sum(1) * xs).sum(1) / np.maximum(w.sum((1, 2)), 1)
        a_e = np.percentile(x[1:31], 95) - np.percentile(x[1:31], 5)
        a_l = np.percentile(x[62:93], 95) - np.percentile(x[62:93], 5)
        out.update(amp_early=float(a_e), amp_late=float(a_l), amp_ratio=float(a_l / max(a_e, 1e-6)),
                   x_trace=[round(float(v), 1) for v in x])
    idx = [0, 23, 46, 69, 80, len(g) - 1]
    cap = cv2.VideoCapture(p); col = []
    i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        if i in idx:
            f = cv2.resize(f, (416, 240)); cv2.putText(f, f"f{i}", (8, 24), 0, 0.7, (0, 255, 0), 2); col.append(f)
        i += 1
    os.makedirs("sheets", exist_ok=True)
    cv2.imwrite(f"sheets/{name}.jpg", np.vstack([np.hstack(col[:3]), np.hstack(col[3:6])]))
    return out


if __name__ == "__main__":
    res = [analyze(p) for p in sorted(glob.glob("clips/*.mp4"))]
    json.dump(res, open("per_clip.json", "w"), indent=1)
    for r in res:
        print(r["name"], r["endpoint"], f"early={r['early']:.4f} late={r['late']:.4f} tail={r['late_tail']:.4f} "
              f"L/E={r['late_over_early']:.2f} still={r['still_end']}",
              f"amp {r['amp_early']:.1f}->{r['amp_late']:.1f} ratio={r['amp_ratio']:.2f}" if "amp_ratio" in r else "")
