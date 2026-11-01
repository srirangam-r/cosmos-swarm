"""POST HOC (after seeing review_result.json): why is 1-SSIM worse than the static floor?
Per clip, seed-mean over own s1-3: dssim(gen_t, real_t) and dssim(real_0, real_t) for t = 0..16 (t=0: the
conditioning frame as Nano re-renders it vs the real frame 0 = encode/decode loss)."""
import importlib.util, json, os, sys
import numpy as np
spec = importlib.util.spec_from_file_location("rv", os.path.join(os.path.dirname(__file__), "review.py"))
src = open(spec.origin).read().split("selftest()\nMETRICS")[0]
ns = {}; exec(compile(src, "review_head", "exec"), ns)
dev, cdir, outp = sys.argv[1:4]
ids = [c["id"] for c in json.load(open(os.path.join(dev, "index.json")))["clips"]]
G, F = [], []
for cid in ids:
    real = ns["load"](os.path.join(dev, cid, "real.mp4"))[:17]
    g = np.mean([[1 - ns["ssim_map"](a, b).mean() for a, b in zip(ns["load"](os.path.join(cdir, f"t255_{cid}_own_s{s}.mp4")), real)] for s in (1, 2, 3)], 0)
    f = [1 - ns["ssim_map"](real[0], b).mean() for b in real]
    G.append(g); F.append(f)
G, F = np.array(G), np.array(F)
out = dict(gen_vs_real_t=G.mean(0).tolist(), floor_t=F.mean(0).tolist(),
           gen_t0=float(G[:, 0].mean()), gen_t0_range=[float(G[:, 0].min()), float(G[:, 0].max())])
json.dump(out, open(outp, "w"), indent=1)
print("t   gen   floor"); [print(t, round(a, 3), round(b, 3)) for t, (a, b) in enumerate(zip(out["gen_vs_real_t"], out["floor_t"]))]

# POST HOC 2: VAE-matched floor = Nano's OWN re-rendered frame 0 repeated (removes encode/decode loss from the comparison)
import itertools
rows = []
for cid in ids:
    realall = ns["load"](os.path.join(dev, cid, "real.mp4"))
    real = realall[1:17]; m = ns["motion_mask"](realall[:17])
    for s in (1, 2, 3):
        g = ns["load"](os.path.join(cdir, f"t255_{cid}_own_s{s}.mp4"))
        g0 = np.repeat(g[:1], 16, 0)
        a, b = ns["dist"](g[1:17], real, m), ns["dist"](g0, real, m)
        rows.append([a["dssim"], b["dssim"], a["rmse"], b["rmse"], a["rmse_mask"], b["rmse_mask"], cid])
R = np.array([r[:6] for r in rows]); cl = np.array([r[6] for r in rows])
per = np.array([R[cl == c].mean(0) for c in ids])  # clip means over seeds
gain = per[:, [1, 3, 5]] - per[:, [0, 2, 4]]  # genfloor - gen (positive = Nano beats its own static frame)
out2 = {k: dict(gen=float(per[:, 2 * i].mean()), genfloor=float(per[:, 2 * i + 1].mean()), gain=float(gain[:, i].mean()),
                se=float(gain[:, i].std(ddof=1) / np.sqrt(len(gain))), pos=int((gain[:, i] > 0).sum()))
        for i, k in enumerate(["dssim", "rmse", "rmse_mask"])}
out["vae_matched_floor"] = out2
json.dump(out, open(outp, "w"), indent=1)
print(json.dumps(out2, indent=1))
