"""dk2 independent re-measure of dk1 #5566/#5666 (task 255 E3/E3b, action-contrast guidance) on the committed SEED-1 clips.
Independent code: cv2 decode, own RMSE, SSIM with cv2 11x11 Gaussian window (Wang 2004), motion amount DE (same definition,
mean |V_k - V_0| over frames 1-16) PLUS an independent motion readout: Farneback optical-flow magnitude between consecutive
frames, ratio to the real clip. No LPIPS (not installed here). Frames 1..16 of 17 vs real.mp4 frames 0..16 (dk1 convention).
Usage: python3 -I remeasure.py <repo_root> <out.json>"""
import json, os, sys
import cv2, numpy as np
root, outp = sys.argv[1], sys.argv[2]
SETS = {"E3": ("work/dk1/t255_e3/clips_s1", "tools/robot_pred/devset_bridge", "work/dk1/t255_e3/results/e3.json"),
        "E3b": ("work/dk1/t255_e3b/clips_s1", "work/dk1/t255_e3b/devset_bridge_ho", "work/dk1/t255_e3b/results/e3b.json")}
def load(p, n=17):
    c = cv2.VideoCapture(p); fr = []
    while len(fr) < n:
        ok, f = c.read()
        if not ok: break
        fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float64) / 255.0)
    return np.stack(fr)
def rmse(a, b): return float(np.sqrt(((a[1:17] - b[1:17]) ** 2).mean()))
def ssim1(x, y):
    C1, C2 = 0.01 ** 2, 0.03 ** 2; g = lambda z: cv2.GaussianBlur(z, (11, 11), 1.5)
    mx, my = g(x), g(y); sxx, syy, sxy = g(x * x) - mx ** 2, g(y * y) - my ** 2, g(x * y) - mx * my
    return float((((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (sxx + syy + C2)))[5:-5, 5:-5].mean())
def dssim(a, b):
    w = np.array([0.299, 0.587, 0.114]); return float(np.mean([1 - ssim1(x @ w, y @ w) for x, y in zip(a[1:17], b[1:17])]))
def de(v): return float(np.abs(v[1:17] - v[0:1]).mean())
def flow(v):
    g = [(f @ np.array([0.299, 0.587, 0.114]) * 255).astype(np.uint8) for f in v[:17]]
    return float(np.mean([np.linalg.norm(cv2.calcOpticalFlowFarneback(g[i], g[i + 1], None, 0.5, 3, 15, 3, 5, 1.2, 0), axis=2).mean() for i in range(16)]))
def boot_med(x, n=20000, seed=0):
    r = np.random.default_rng(seed); x = np.asarray(x); m = np.median(x[r.integers(0, len(x), (n, len(x)))], 1)
    return [float(np.percentile(m, 1.67 / 2 * 1)), float(np.percentile(m, 100 - 1.67 / 2))]
res = {"per_clip": {}, "summary": {}}
for S, (cd, dv, dkj) in SETS.items():
    dk = json.load(open(os.path.join(root, dkj)))["per_clip"]
    arms = sorted({f.split("_")[-2] if not f.endswith("swap_neg3_s1.mp4") else "swap_neg3" for f in os.listdir(os.path.join(root, cd))})
    arms = [a for a in arms if a != "neg3"] + ["neg3"]; arms = [a for a in arms if a in ("plain", "neg3", "zero1")]
    for cid in sorted(dk):
        R = load(os.path.join(root, dv, cid, "real.mp4"))
        r = {"set": S, "DE_real": de(R), "FL_real": flow(R)}
        for a in arms:
            X = load(os.path.join(root, cd, f"t255e3_{cid}_{a}_s1.mp4"))
            r[a] = dict(RMSE=rmse(X, R), DSSIM=dssim(X, R), DE=de(X), FL=flow(X),
                        dk1_RMSE_s1=dk[cid][f"RMSE_{a}"][0], dk1_DSSIM_s1=dk[cid][f"DSSIM_{a}"][0])
        res["per_clip"][f"{S}:{cid}"] = r
C = list(res["per_clip"].values())
for S in ("E3", "E3b", "pooled"):
    CC = [c for c in C if S == "pooled" or c["set"] == S]
    for a in ("neg3", "zero1"):
        CA = [c for c in CC if a in c]
        if not CA: continue
        d = {}
        for m in ("RMSE", "DSSIM"):
            x = [c[a][m] - c["plain"][m] for c in CA]
            d[f"d{m}"] = dict(median=float(np.median(x)), ci9833=boot_med(x), n_worse=int(sum(v > 0 for v in x)), n=len(x))
        for m, ref in (("DE", "DE_real"), ("FL", "FL_real")):
            d[f"{m}_over_real_median"] = {a: float(np.median([c[a][m] / c[ref] for c in CA])), "plain": float(np.median([c["plain"][m] / c[ref] for c in CA]))}
            x = [np.log(c[a][m] / c["plain"][m]) for c in CA]
            d[f"{m}_ratio_vs_plain"] = dict(median=float(np.exp(np.median(x))), n_more=int(sum(v > 0 for v in x)))
        res["summary"][f"{S}:{a}"] = d
    # agreement of my metric with dk1's seed-1 numbers
    for m in ("RMSE", "DSSIM"):
        mine = [c[a][m] for c in CC for a in ("plain", "neg3", "zero1") if a in c]
        his = [c[a][f"dk1_{m}_s1"] for c in CC for a in ("plain", "neg3", "zero1") if a in c]
        res["summary"][f"{S}:agree_{m}"] = dict(pearson=float(np.corrcoef(mine, his)[0, 1]), median_ratio=float(np.median(np.array(mine) / np.array(his))), n=len(mine))
json.dump(res, open(outp, "w"), indent=1)
print(json.dumps(res["summary"], indent=1))
