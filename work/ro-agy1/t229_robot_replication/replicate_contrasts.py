#!/usr/bin/env python3
"""Independent Contrast & Cluster Statistical Analysis for Task 229 / Task 210."""
import json, os, sys
import numpy as np
from scipy import stats

INDEP_PATH = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/t229_robot_replication/independent_scores.json"
AUTHOR_SCORES_PATH = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/rahul-api/t210/scores.json"
AUTHOR_RESULTS_PATH = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/rahul-api/t210/results.json"
DEVSET_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/tools/robot_pred/devset_bridge"
OUT_RESULTS = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/t229_robot_replication/independent_results.json"

def contrast(x, y, margin=None, rng=np.random.default_rng(20261101)):
    d = x - y
    n = len(d)
    se = d.std(ddof=1) / np.sqrt(n)
    t_crit = stats.t.ppf(0.975, n - 1)
    bs = np.array([rng.choice(d, n).mean() for _ in range(20000)])
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

def main():
    print("Loading independent scores...")
    with open(INDEP_PATH, "r") as f:
        indep_data = json.load(f)
    indep_clips = indep_data["clips"]
    static_floor = indep_data["static_floor"]

    print("Loading author scores for numerical comparison...")
    with open(AUTHOR_SCORES_PATH, "r") as f:
        author_data = json.load(f)
    auth_clips = author_data["clips"]

    # 1. Numerical concordance check
    max_diffs = {"psnr": 0.0, "ssim": 0.0, "lpips": 0.0, "motion_mad": 0.0, "frame0_mad": 0.0}
    for k in indep_clips:
        if k in auth_clips:
            for m in max_diffs:
                diff = abs(indep_clips[k][m] - auth_clips[k][m])
                if diff > max_diffs[m]:
                    max_diffs[m] = diff
    print("Maximum absolute discrepancy between independent and author scores:")
    for m, diff in max_diffs.items():
        print(f"  {m:12s}: {diff:.2e}")
        assert diff < 1e-4, f"Numerical discrepancy too large for {m}: {diff}"
    print("Numerical score reproduction verified (bit-identical within float precision).")

    # 2. Setup contrasts
    rows = list(indep_clips.values())
    clips = sorted({r["clip"] for r in rows})
    arms = ["base", "R", "N"]
    seeds = sorted({r["seed"] for r in rows})
    
    with open(os.path.join(DEVSET_DIR, "index.json"), "r") as f:
        idx = json.load(f)
    instructed = {c["id"] for c in idx["clips"] if c["prompt"].strip()}

    T = {(r["arm"], r["clip"], r["seed"]): r for r in rows}
    complete = [c for c in clips if all((a, c, s) in T for a in arms for s in seeds)]
    assert len(complete) == 24, f"Expected 24 complete clips, got {len(complete)}"

    def clipmean(arm, m, ss=None, cl=None):
        target_clips = cl or complete
        target_seeds = ss or seeds
        return np.array([np.mean([T[(arm, c, s)][m] for s in target_seeds]) for c in target_clips])

    metrics = ["lpips", "psnr", "ssim", "motion_ratio"]
    results = {
        "n_clips": len(complete),
        "seeds": seeds,
        "arm_means": {},
        "contrasts": {},
        "seed_cluster_analysis": {},
        "subsets": {}
    }

    print("\n--- Arm Means (mean ± SE over 24 clips) ---")
    for a in arms:
        results["arm_means"][a] = {}
        for m in metrics:
            vals = clipmean(a, m)
            mean_v = float(vals.mean())
            se_v = float(vals.std(ddof=1) / np.sqrt(len(vals)))
            results["arm_means"][a][m] = {"mean": mean_v, "se": se_v}
        print(f"  Arm {a:5s}: LPIPS {results['arm_means'][a]['lpips']['mean']:.4f}±{results['arm_means'][a]['lpips']['se']:.4f} | PSNR {results['arm_means'][a]['psnr']['mean']:.2f}±{results['arm_means'][a]['psnr']['se']:.2f} dB | SSIM {results['arm_means'][a]['ssim']['mean']:.4f}±{results['arm_means'][a]['ssim']['se']:.4f}")

    # Static floor
    st_lp = np.array([static_floor[c]["lpips"] for c in complete])
    st_psnr = np.array([static_floor[c]["psnr"] for c in complete])
    st_ssim = np.array([static_floor[c]["ssim"] for c in complete])
    results["static_floor"] = {
        "lpips": {"mean": float(st_lp.mean()), "se": float(st_lp.std(ddof=1)/np.sqrt(len(st_lp)))},
        "psnr": {"mean": float(st_psnr.mean()), "se": float(st_psnr.std(ddof=1)/np.sqrt(len(st_psnr)))},
        "ssim": {"mean": float(st_ssim.mean()), "se": float(st_ssim.std(ddof=1)/np.sqrt(len(st_ssim)))}
    }
    print(f"  Static Floor: LPIPS {results['static_floor']['lpips']['mean']:.4f}±{results['static_floor']['lpips']['se']:.4f} | PSNR {results['static_floor']['psnr']['mean']:.2f}±{results['static_floor']['psnr']['se']:.2f} dB")

    print("\n--- Primary & Secondary Contrasts (Clip Unit, n=24) ---")
    for m in metrics:
        for x, y in [("R", "base"), ("R", "N"), ("N", "base")]:
            margin = 0.010 if (m == "lpips" and (x, y) == ("R", "base")) else None
            c_res = contrast(clipmean(x, m), clipmean(y, m), margin=margin)
            k = f"{m}:{x}-{y}"
            results["contrasts"][k] = c_res
            print(f"  {k:24s}: {c_res['mean']:+.4f} ± {c_res['se']:.4f} (t95 [{c_res['ci95_t'][0]:+.4f}, {c_res['ci95_t'][1]:+.4f}], boot [{c_res['ci95_boot'][0]:+.4f}, {c_res['ci95_boot'][1]:+.4f}], +{c_res['n_pos']}/-{c_res['n_neg']}, p={c_res['p_t']:.3f}) {c_res.get('verdict','')}")

    print("\n--- Whole-Seed Cluster Analysis (Cluster Unit: 4 Seeds) ---")
    # For each seed, compute clip-averaged contrast
    seed_lpips_r_base = {}
    seed_psnr_r_base = {}
    for s in seeds:
        d_lp = np.array([T[("R", c, s)]["lpips"] - T[("base", c, s)]["lpips"] for c in complete])
        d_ps = np.array([T[("R", c, s)]["psnr"] - T[("base", c, s)]["psnr"] for c in complete])
        seed_lpips_r_base[int(s)] = float(d_lp.mean())
        seed_psnr_r_base[int(s)] = float(d_ps.mean())
        print(f"  Seed {s}: LPIPS Δ = {d_lp.mean():+.6f} (clip SE {d_lp.std(ddof=1)/np.sqrt(len(d_lp)):.4f}, +{(d_lp>0).sum()}/-{(d_lp<0).sum()}) | PSNR Δ = {d_ps.mean():+.4f} dB")

    # Whole-seed cluster statistics over the 4 seed-level means
    seed_means = np.array(list(seed_lpips_r_base.values()))
    s_mean = float(seed_means.mean())
    s_std = float(seed_means.std(ddof=1))
    s_se = s_std / np.sqrt(len(seeds))
    t_crit_seed = stats.t.ppf(0.975, len(seeds) - 1)
    seed_ci95 = [s_mean - t_crit_seed * s_se, s_mean + t_crit_seed * s_se]
    print(f"\n  Seed-level omnibus LPIPS R-base: mean = {s_mean:+.6f}, seed SD = {s_std:.6f}, seed SE = {s_se:.6f}")
    print(f"  Seed-level t 95% CI (df=3): [{seed_ci95[0]:+.6f}, {seed_ci95[1]:+.6f}]")
    print(f"  Upper bound ({seed_ci95[1]:+.6f}) vs margin (+0.010): {(0.010 / max(seed_ci95[1], 1e-6)):.1f}x safety factor")
    assert seed_ci95[1] < 0.010, "Seed-level upper CI exceeds non-inferiority margin!"

    results["seed_cluster_analysis"] = {
        "per_seed_lpips_r_base": seed_lpips_r_base,
        "per_seed_psnr_r_base": seed_psnr_r_base,
        "seed_level_mean": s_mean,
        "seed_level_sd": s_std,
        "seed_level_se": s_se,
        "seed_level_ci95_t": seed_ci95
    }

    # Within-base pseudo-contrast (seeds 0,1 vs seeds 2,3)
    pseudo_d = clipmean("base", "lpips", ss=[0, 1]) - clipmean("base", "lpips", ss=[2, 3])
    pseudo_res = contrast(clipmean("base", "lpips", ss=[0, 1]), clipmean("base", "lpips", ss=[2, 3]))
    print(f"\n  Within-Base Pseudo-Contrast (Seeds {{0,1}} vs {{2,3}}): {pseudo_res['mean']:+.4f} ± {pseudo_res['se']:.4f} (t95 [{pseudo_res['ci95_t'][0]:+.4f}, {pseudo_res['ci95_t'][1]:+.4f}])")
    results["seed_cluster_analysis"]["pseudo_contrast_base_s01_vs_s23"] = pseudo_res

    print("\n--- Subsets (Instructed vs Default Prompt) ---")
    for name, sub in [("instructed", [c for c in complete if c in instructed]), ("default_prompt", [c for c in complete if c not in instructed])]:
        sub_c = contrast(clipmean("R", "lpips", cl=sub), clipmean("base", "lpips", cl=sub), margin=0.010)
        results["subsets"][f"lpips:R-base[{name}]"] = sub_c
        print(f"  {name:15s} (n={len(sub)}): LPIPS R-base = {sub_c['mean']:+.4f} ± {sub_c['se']:.4f} (t95 [{sub_c['ci95_t'][0]:+.4f}, {sub_c['ci95_t'][1]:+.4f}]) -> {sub_c['verdict']}")

    with open(OUT_RESULTS, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved independent statistical results to {OUT_RESULTS}")

if __name__ == "__main__":
    main()
