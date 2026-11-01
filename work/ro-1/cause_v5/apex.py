"""ro-1: unvalidated apex-sequence readout for the QT/F bounce clips (scout #2337 H-S test).
Ball = largest blob of |frame - temporal median| inside the corridor crop; y per frame (image px, down +).
Apexes = local minima of y between successive impacts (local maxima). Writes json + QC plot.
usage: python -I apex.py out_prefix clip1.mp4 [clip2.mp4 ...]
"""
import sys, json, os
import numpy as np, av
from scipy import ndimage
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

Y0, Y1, X0, X1 = 30, 400, 200, 400  # corridor (832x480 frame), wide enough for ball1/ball2 paths
BGP = float(os.environ.get("BGP", 90))  # background percentile: dark ball, so a bright percentile keeps a resting ball out of bg


def frames(p):
    c = av.open(p)
    out = [f.to_ndarray(format="gray").astype(np.float32) for f in c.decode(video=0)]
    c.close()
    return np.stack(out)


def track(v):
    roi = v[:, Y0:Y1, X0:X1]
    bg = np.percentile(roi, BGP, axis=0)
    ys, xs, ar = [], [], []
    for f in roi:
        d = ndimage.gaussian_filter(np.clip(bg - f, 0, None), 2)  # darker-than-bg only
        m = d > max(18.0, np.percentile(d, 99.5) * 0.5)
        lab, n = ndimage.label(m)
        if n == 0:
            ys.append(np.nan); xs.append(np.nan); ar.append(0); continue
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        k = int(np.argmax(sizes)) + 1
        cy, cx = ndimage.center_of_mass(m, lab, k)
        ys.append(cy + Y0); xs.append(cx + X0); ar.append(float(sizes[k - 1]))
    return np.array(ys), np.array(xs), np.array(ar)


def extrema(y, prom=8):
    yi = np.copy(y)
    ok = ~np.isnan(yi)
    yi[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), yi[ok]) if ok.sum() > 2 else 0
    imp, apx = [], []
    for i in range(1, len(yi) - 1):
        w = yi[max(0, i - 3): i + 4]
        if yi[i] == w.max() and yi[i] - w.min() > prom:
            imp.append(i)
    for a, b in zip(imp[:-1], imp[1:]):
        j = a + int(np.argmin(yi[a:b + 1]))
        apx.append(j)
    return yi, imp, apx


def main():
    pre = sys.argv[1]
    res = {}
    fig, axs = plt.subplots(len(sys.argv) - 2, 1, figsize=(9, 2.2 * (len(sys.argv) - 2)), squeeze=False)
    for ax, p in zip(axs[:, 0], sys.argv[2:]):
        v = frames(p)
        y, x, a = track(v)
        yi, imp, apx = extrema(y)
        floor = float(np.median(yi[imp])) if imp else float(np.nanmax(yi))
        h = [round(floor - yi[j], 1) for j in apx]
        name = os.path.basename(p)[:-4]
        res[name] = dict(impacts=imp, apex_frames=apx, apex_height_px=h,
                         ratios=[round(h[k + 1] / h[k], 2) for k in range(len(h) - 1) if h[k] > 0],
                         y=[None if np.isnan(q) else round(float(q), 1) for q in y])
        ax.plot(y, ".-", ms=3); ax.invert_yaxis()
        for j in imp: ax.axvline(j, color="r", lw=0.5)
        for j in apx: ax.plot(j, yi[j], "g^")
        ax.set_title(f"{name} apex h {h}", fontsize=7)
    fig.tight_layout(); fig.savefig(pre + ".png", dpi=90)
    json.dump(res, open(pre + ".json", "w"), indent=1)
    for k, r in res.items():
        print(k, "imp", r["impacts"], "h", r["apex_height_px"], "ratios", r["ratios"])


if __name__ == "__main__":
    main()
