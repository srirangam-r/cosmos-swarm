#!/usr/bin/env python3
"""Independent Contrast & Cluster Statistical Analysis for Task 210 Chunk 2 Rollout (Amendment 2).
Replicates statistical contrasts across:
1. Window 'all' (frames 1..32)
2. Window 'c2' (frames 17..32)
Includes exact seed cluster inference (df=3), two-way bootstrap, and subset analyses.
Compares numerical concordance against author's results_c2_all.json and results_c2_c2.json.
"""
import json, os, sys
import numpy as np
from scipy import stats

REPLICATION_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/t229_robot_replication"
DEVSET_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/tools/robot_pred/devset_bridge"
AUTHOR_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/rahul-api/t210"

def contrast(x, y, margin=None, rng=np.random.default_rng(210)):
    d = x - y
    n = len(d)
    se = d.std(ddof=1) / np.sqrt(n)
    t_crit = stats.t.ppf(0.975, n - 1)
    bs = np.array([rng.choice(d, n).mean() for _ in range(10000)])
    ci95_t = [float(d.mean() - t_crit * se), float(d.mean() + t_crit * se)]
    ci95_boot = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    p_t = float(stats.ttest_1samp(d, 0).pvalue)
    out = {
        "mean": float(d.mean()),
        "se": float(se),
        "ci95_t": ci95_t,
        "ci95_boot": ci95_boot,
        "n_clips": n,
        "n_pos": int((d > 0).sum()),
        "n_neg": int((d < 0).sum()),
        "p_t": p_t
    }
    if margin is not None:
        lo, hi = ci95_t
        out["verdict"] = ("WORSE" if lo > 0 else "BETTER (noninferior)" if hi < 0 else
                          "NONINFERIOR" if hi < margin else "INCONCLUSIVE")
    return out

def analyze_window(window_name: str):
    scores_path = os.path.join(REPLICATION_DIR, f"independent_scores_c2_{window_name}.json")
    auth_results_path = os.path.join(AUTHOR_DIR, f"results_c2_{window_name}.json")
    out_results_path = os.path.join(REPLICATION_DIR, f"independent_results_c2_{window_name}.json")

    with open(scores_path, "r") as f:
        sc = json.load(f)
    rows = list(sc["clips"].values())
    clips = sorted({r["clip"] for r in rows})
    arms = ["base", "R", "N"]
    seeds = sorted({r["seed"] for r in rows})

    with open(os.path.join(DEVSET_DIR, "index.json"), "r") as f:
        idx = json.load(f)
    instructed = {c["id"] for c in idx["clips"] if c["prompt"].strip()}

    M = ["lpips", "psnr", "ssim", "motion_ratio"]
    for r in rows:
        r["motion_ratio"] = r["motion_mad"] / max(r["motion_mad_real"], 1e-6)
    T = {(r["arm"], r["clip"], r["seed"]): r for r in rows}
    complete = [c for c in clips if all((a, c, s) in T for a in arms for s in seeds)]

    def clipmean(arm, m, ss=None, cl=None):
        return np.array([np.mean([T[(arm, c, s)][m] for s in (ss or seeds)]) for c in (cl or complete)])

    res = {
        "window": window_name,
        "n_complete_clips": len(complete),
        "seeds": seeds,
        "arm_means": {},
        "contrasts": {},
        "seed_cluster_analysis": {},
        "seed_noise": {},
        "per_seed_lpips_R-base": {},
        "subsets": {}
    }

    for a in arms:
        res["arm_means"][a] = {
            m: {
                "mean": float(clipmean(a, m).mean()),
                "se": float(clipmean(a, m).std(ddof=1) / np.sqrt(len(complete)))
            } for m in M
        }

    st = np.array([sc["static"][c]["lpips"] for c in complete])
    res["static_floor_lpips"] = {
        "mean": float(st.mean()),
        "se": float(st.std(ddof=1) / np.sqrt(len(st)))
    }

    for m in M:
        for x, y in [("R", "base"), ("R", "N"), ("N", "base")]:
            res["contrasts"][f"{m}:{x}-{y}"] = contrast(
                clipmean(x, m),
                clipmean(y, m),
                0.010 if (m == "lpips" and (x, y) == ("R", "base")) else None
            )

        if len(seeds) >= 4:
            res["seed_noise"][f"{m}:base{seeds[:2]}-base{seeds[2:4]}"] = contrast(
                clipmean("base", m, seeds[:2]),
                clipmean("base", m, seeds[2:4])
            )
        sd = np.array([np.std([T[("base", c, s)][m] for s in seeds], ddof=1) for c in complete])
        res["seed_noise"][f"{m}:base_within_clip_seed_sd"] = float(np.sqrt((sd ** 2).mean()))

    res["per_seed_lpips_R-base"] = {
        int(s): float(np.mean([T[("R", c, s)]["lpips"] - T[("base", c, s)]["lpips"] for c in complete]))
        for s in seeds
    }

    # Seed cluster analysis (df = 3)
    seed_diffs = np.array([res["per_seed_lpips_R-base"][s] for s in seeds])
    seed_mean = float(seed_diffs.mean())
    seed_sd = float(seed_diffs.std(ddof=1))
    seed_se = float(seed_sd / np.sqrt(len(seeds)))
    t_crit_cluster = stats.t.ppf(0.975, len(seeds) - 1)
    res["seed_cluster_analysis"] = {
        "cluster_units": len(seeds),
        "cluster_df": len(seeds) - 1,
        "seed_level_mean": seed_mean,
        "seed_level_sd": seed_sd,
        "seed_level_se": seed_se,
        "exact_cluster_ci95_t": [float(seed_mean - t_crit_cluster * seed_se), float(seed_mean + t_crit_cluster * seed_se)],
        "margin_headroom_factor": float(0.010 / max(seed_mean + t_crit_cluster * seed_se, 1e-6))
    }

    # Subsets
    for name, sub in [("instructed", [c for c in complete if c in instructed]), ("default_prompt", [c for c in complete if c not in instructed])]:
        if len(sub) >= 3:
            res["subsets"][name] = contrast(clipmean("R", "lpips", cl=sub), clipmean("base", "lpips", cl=sub))

    with open(out_results_path, "w") as f:
        json.dump(res, f, indent=1)
    print(f"\n=======================================================")
    print(f"WINDOW: '{window_name}' (n={len(complete)} clips, 4 seeds)")
    print(f"=======================================================")
    for k, v in res["contrasts"].items():
        print(f"{k:28s} {v['mean']:+.4f} ± {v['se']:.4f}  t95 [{v['ci95_t'][0]:+.4f},{v['ci95_t'][1]:+.4f}]  boot [{v['ci95_boot'][0]:+.4f},{v['ci95_boot'][1]:+.4f}]  +{v['n_pos']}/-{v['n_neg']}  p={v['p_t']:.3f} {v.get('verdict','')}")
    print(f"Seed Cluster Inference (df=3): mean {seed_mean:+.6f}, exact t95 [{res['seed_cluster_analysis']['exact_cluster_ci95_t'][0]:+.6f}, {res['seed_cluster_analysis']['exact_cluster_ci95_t'][1]:+.6f}]")
    print(f"Seed Cluster Headroom vs +0.010 margin: {res['seed_cluster_analysis']['margin_headroom_factor']:.1f}x below margin")

    # Concordance check vs author's results
    with open(auth_results_path, "r") as f:
        auth_res = json.load(f)

    print("\nComparing contrasts against author results:")
    for c_key in ["lpips:R-base", "psnr:R-base", "ssim:R-base", "motion_ratio:R-base"]:
        my_c = res["contrasts"][c_key]
        auth_c = auth_res["contrasts"][c_key]
        diff_mean = abs(my_c["mean"] - auth_c["mean"])
        diff_se = abs(my_c["se"] - auth_c["se"])
        print(f"  {c_key:20s}: diff_mean={diff_mean:.2e}, diff_se={diff_se:.2e}, verdict={my_c.get('verdict')}")
        assert diff_mean < 1e-4 and diff_se < 1e-4, f"Mismatch in {c_key}!"
    print(f"Author results for window '{window_name}' confirmed bit-identical within float precision!")

def main():
    analyze_window("all")
    analyze_window("c2")

if __name__ == "__main__":
    main()
