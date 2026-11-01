#!/usr/bin/env python3
"""Task 210 analysis per PREREG.md. Input: scores.json from score_t210.py. Output: results.json + printed table."""
import json, sys
import numpy as np
from scipy import stats
sc = json.load(open(sys.argv[1])); outp = sys.argv[2]
rows = list(sc["clips"].values())
clips = sorted({r["clip"] for r in rows}); arms = ["base", "R", "N"]; seeds = sorted({r["seed"] for r in rows})
idx = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else None
instructed = {c["id"] for c in idx["clips"] if c["prompt"].strip()} if idx else set(clips)
M = ["lpips", "psnr", "ssim", "motion_ratio"]
for r in rows:
    r["motion_ratio"] = r["motion_mad"] / max(r["motion_mad_real"], 1e-6)
T = {(r["arm"], r["clip"], r["seed"]): r for r in rows}
complete = [c for c in clips if all((a, c, s) in T for a in arms for s in seeds)]

def clipmean(arm, m, ss=None, cl=None):
    return np.array([np.mean([T[(arm, c, s)][m] for s in (ss or seeds)]) for c in (cl or complete)])

def contrast(x, y, margin=None, rng=np.random.default_rng(210)):
    d = x - y; n = len(d); se = d.std(ddof=1) / np.sqrt(n); t = stats.t.ppf(0.975, n - 1)
    bs = np.array([rng.choice(d, n).mean() for _ in range(10000)])
    out = {"mean": float(d.mean()), "se": float(se), "ci95_t": [float(d.mean() - t * se), float(d.mean() + t * se)],
           "ci95_boot": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "n_clips": n,
           "n_pos": int((d > 0).sum()), "n_neg": int((d < 0).sum()), "p_t": float(stats.ttest_1samp(d, 0).pvalue)}
    if margin is not None:
        lo, hi = out["ci95_t"]
        out["verdict"] = ("WORSE" if lo > 0 else "BETTER (noninferior)" if hi < 0 else
                          "NONINFERIOR" if hi < margin else "INCONCLUSIVE")
    return out

res = {"n_complete_clips": len(complete), "seeds": seeds, "arm_means": {}, "contrasts": {}, "seed_noise": {}}
for a in arms:
    res["arm_means"][a] = {m: {"mean": float(clipmean(a, m).mean()), "se": float(clipmean(a, m).std(ddof=1) / np.sqrt(len(complete)))} for m in M}
st = np.array([sc["static"][c]["lpips"] for c in complete])
res["static_floor_lpips"] = {"mean": float(st.mean()), "se": float(st.std(ddof=1) / np.sqrt(len(st)))}
for m in M:
    for x, y in [("R", "base"), ("R", "N"), ("N", "base")]:
        res["contrasts"][f"{m}:{x}-{y}"] = contrast(clipmean(x, m), clipmean(y, m), 0.010 if (m == "lpips" and (x, y) == ("R", "base")) else None)
    # seed-noise pseudo-contrast within base: seeds {0,1} vs {2,3}
    if len(seeds) >= 4:
        res["seed_noise"][f"{m}:base{seeds[:2]}-base{seeds[2:4]}"] = contrast(clipmean("base", m, seeds[:2]), clipmean("base", m, seeds[2:4]))
    sd = np.array([np.std([T[("base", c, s)][m] for s in seeds], ddof=1) for c in complete])
    res["seed_noise"][f"{m}:base_within_clip_seed_sd"] = float(np.sqrt((sd ** 2).mean()))
# per-seed R-base lpips sign
res["per_seed_lpips_R-base"] = {int(s): float(np.mean([T[("R", c, s)]["lpips"] - T[("base", c, s)]["lpips"] for c in complete])) for s in seeds}
# instructed vs default-prompt subsets
for name, sub in [("instructed", [c for c in complete if c in instructed]), ("default_prompt", [c for c in complete if c not in instructed])]:
    if len(sub) >= 3:
        res["contrasts"][f"lpips:R-base[{name}]"] = contrast(clipmean("R", "lpips", cl=sub), clipmean("base", "lpips", cl=sub))
json.dump(res, open(outp, "w"), indent=1)
print("complete clips", len(complete), "seeds", seeds)
for a, v in res["arm_means"].items():
    print(a, {m: f"{v[m]['mean']:.4f}±{v[m]['se']:.4f}" for m in M})
print("static floor lpips", res["static_floor_lpips"])
for k, v in res["contrasts"].items():
    print(f"{k:28s} {v['mean']:+.4f} ± {v['se']:.4f}  t95 [{v['ci95_t'][0]:+.4f},{v['ci95_t'][1]:+.4f}]  boot [{v['ci95_boot'][0]:+.4f},{v['ci95_boot'][1]:+.4f}]  +{v['n_pos']}/-{v['n_neg']}  p={v['p_t']:.3f} {v.get('verdict','')}")
for k, v in res["seed_noise"].items():
    print("SEEDNOISE", k, v if isinstance(v, float) else f"{v['mean']:+.4f} t95 [{v['ci95_t'][0]:+.4f},{v['ci95_t'][1]:+.4f}]")
print("per-seed R-base lpips", res["per_seed_lpips_R-base"])
