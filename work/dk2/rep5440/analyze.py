"""FROZEN before any rep5440 clip exists. Independent analysis (opencv/numpy/av; no code from work/dk1).
Inputs: clips dir with rep5440_<cid>_<arm>_s<seed>.mp4 (arms own/zero, seeds 11-13); devset dir for real.mp4.
Per clip (cid, arm, seed), frames V_0..V_16 (gray float, 256x256):
  PD  = mean_k mean|V_k - V_0| over k=1..16 (pixel drift vs the clip's OWN generated frame 0; cancels VAE re-render)
  FM  = mean_k mean ||Farneback flow(V_{k-1} -> V_k)|| (px/frame), an independent motion family
Per clip cid: rho_PD = median_seed PD(zero) / median_seed PD(own); rho_FM likewise.
Seed spread S_arm = mean over the 3 seed pairs of RMSE(V^a, V^b) over frames 1..16; ratio = S_zero / S_own.
PRIMARY (replicates #5440 if all hold): median rho_PD < 0.5, its 95% clip-bootstrap upper bound < 0.5,
  and >= 20/24 clips with rho_PD < 0.5.
SECONDARY: same for rho_FM; median S_zero/S_own < 0.5 with >= 20/24 clips < 1; real-video PD/FM for scale
  (own/real ratio, reported only). Known answers: PD = FM = 0 on a frozen copy of frame 0 (asserted).
Bootstrap: 10000 resamples over clips, seed 0.
Usage: python3 analyze.py <clips_dir> <devset_dir> > result.json
"""
import json, sys, itertools
from pathlib import Path
import numpy as np, cv2, av

clips, dev = Path(sys.argv[1]), Path(sys.argv[2])
SEEDS, ARMS = (11, 12, 13), ("own", "zero")

def frames(p, n=17):
    with av.open(str(p)) as c:
        fr = [f.to_ndarray(format="gray").astype(np.float32) for f in c.decode(video=0)]
    fr = [cv2.resize(f, (256, 256), interpolation=cv2.INTER_AREA) if f.shape != (256, 256) else f for f in fr]
    return np.stack(fr[:n])

def pd(v): return float(np.mean([np.abs(v[k] - v[0]).mean() for k in range(1, len(v))]))
def fm(v):
    u8 = np.clip(v, 0, 255).astype(np.uint8); out = []
    for k in range(1, len(v)):
        f = cv2.calcOpticalFlowFarneback(u8[k-1], u8[k], None, 0.5, 3, 15, 3, 5, 1.2, 0)
        out.append(np.linalg.norm(f, axis=2).mean())
    return float(np.mean(out))

still = np.repeat(np.full((1, 256, 256), 128, np.float32) + np.random.default_rng(0).uniform(0, 50, (1, 256, 256)).astype(np.float32), 17, 0)
assert pd(still) == 0 and fm(still) < 1e-3  # Farneback numerical floor ~3e-4 px

def boot(x, rng=np.random.default_rng(0), B=10000):
    x = np.asarray(x); i = rng.integers(0, len(x), (B, len(x)))
    m = np.median(x[i], axis=1); return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]

cids = [c["id"] for c in json.loads((dev / "index.json").read_text())["clips"]]
per = {}
for cid in cids:
    V = {(a, s): frames(clips / f"rep5440_{cid}_{a}_s{s}.mp4") for a in ARMS for s in SEEDS}
    real = frames(dev / cid / "real.mp4")
    r = {"PD": {a: [pd(V[a, s]) for s in SEEDS] for a in ARMS}, "FM": {a: [fm(V[a, s]) for s in SEEDS] for a in ARMS},
         "PD_real": pd(real), "FM_real": fm(real)}
    r["S"] = {a: float(np.mean([np.sqrt(((V[a, x][1:] - V[a, y][1:]) ** 2).mean()) for x, y in itertools.combinations(SEEDS, 2)])) for a in ARMS}
    r["rho_PD"] = float(np.median(r["PD"]["zero"]) / np.median(r["PD"]["own"]))
    r["rho_FM"] = float(np.median(r["FM"]["zero"]) / np.median(r["FM"]["own"]))
    r["S_ratio"] = r["S"]["zero"] / r["S"]["own"]
    r["own_over_real_PD"] = float(np.median(r["PD"]["own"]) / r["PD_real"])
    per[cid] = r

def summ(key, thr):
    x = [per[c][key] for c in cids]
    return {"median": float(np.median(x)), "ci95": boot(x), "n_below": int(sum(v < thr for v in x)), "n": len(x), "thr": thr}

res = {"rho_PD": summ("rho_PD", 0.5), "rho_FM": summ("rho_FM", 0.5), "S_ratio": summ("S_ratio", 1.0),
       "S_ratio_below_half": int(sum(per[c]["S_ratio"] < 0.5 for c in cids)),
       "own_over_real_PD": summ("own_over_real_PD", 1.0)}
p = res["rho_PD"]
res["PRIMARY_replicated"] = bool(p["median"] < 0.5 and p["ci95"][1] < 0.5 and p["n_below"] >= 20)
res["per_clip"] = per
print(json.dumps(res, indent=1))
