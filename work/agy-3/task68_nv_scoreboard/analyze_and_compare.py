#!/usr/bin/env python3
"""Analyze and compare official NVIDIA scoreboard metrics (DOVER + Dynamic Degree)
for Baseline (held frame 0) vs Recipe Fix (mid-fall released frame) across seeds 1-4.
"""
import json, os, sys
import numpy as np
from scipy import stats

WORK_DIR = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task68_nv_scoreboard"
REAL_REF_PATH = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/raj-4/nv_scoreboard_real/gauge_real_matched.json"

def bootstrap_ci(diffs, n_boot=10000, ci=0.95):
    diffs = np.array(diffs)
    boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return float(np.percentile(boot_means, 100 * alpha)), float(np.percentile(boot_means, 100 * (1.0 - alpha)))

def main():
    ctrl_path = os.path.join(WORK_DIR, "scores_baseline_held.json")
    mid_path = os.path.join(WORK_DIR, "scores_recipe_midfall.json")
    
    with open(ctrl_path) as f:
        ctrl_raw = json.load(f)
    with open(mid_path) as f:
        mid_raw = json.load(f)
        
    real_ref = {}
    if os.path.exists(REAL_REF_PATH):
        with open(REAL_REF_PATH) as f:
            real_ref = json.load(f)

    # Normalize keys (strip paths if present)
    ctrl = {os.path.basename(k): v for k, v in ctrl_raw.items()}
    mid = {os.path.basename(k): v for k, v in mid_raw.items()}

    pairs = []
    for b in (1, 2):
        for s in (1, 2, 3, 4):
            ckey = f"box_ctrl_b{b}_noneg_s{s}.mp4"
            mkey = f"box_mid_b{b}_noneg_s{s}.mp4"
            if ckey in ctrl and mkey in mid:
                pairs.append((b, s, ckey, mkey))

    print(f"Total matched pairs found: {len(pairs)} (Ball 1 & 2, Seeds 1-4)")
    
    metrics = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_norm", "dd_frac", "dd_binary"]
    
    results = {
        "n_pairs": len(pairs),
        "seeds": [1, 2, 3, 4],
        "balls": [1, 2],
        "pairs_detail": [],
        "metrics": {}
    }
    
    for b, s, ckey, mkey in pairs:
        c_entry = ctrl[ckey]
        m_entry = mid[mkey]
        p_res = {
            "ball": b,
            "seed": s,
            "ctrl_clip": ckey,
            "mid_clip": mkey,
            "baseline": {m: c_entry.get(m) for m in metrics},
            "recipe": {m: m_entry.get(m) for m in metrics},
            "delta": {m: float(m_entry.get(m, 0.0) - c_entry.get(m, 0.0)) for m in metrics}
        }
        results["pairs_detail"].append(p_res)
        
    for m in metrics:
        c_vals = np.array([p["baseline"][m] for p in results["pairs_detail"]])
        m_vals = np.array([p["recipe"][m] for p in results["pairs_detail"]])
        diffs = m_vals - c_vals
        
        # Means and SEs
        c_mean, c_se = float(np.mean(c_vals)), float(np.std(c_vals, ddof=1) / np.sqrt(len(c_vals)))
        m_mean, m_se = float(np.mean(m_vals)), float(np.std(m_vals, ddof=1) / np.sqrt(len(m_vals)))
        d_mean, d_se = float(np.mean(diffs)), float(np.std(diffs, ddof=1) / np.sqrt(len(diffs)))
        
        # Paired t-test
        t_stat, p_val = stats.ttest_rel(m_vals, c_vals)
        ci_low, ci_high = bootstrap_ci(diffs)
        
        # Within-group seed noise (pooled within each ball condition)
        # For baseline:
        b1_c = [c_entry[m] for k, c_entry in ctrl.items() if "_b1_" in k]
        b2_c = [c_entry[m] for k, c_entry in ctrl.items() if "_b2_" in k]
        c_seed_sd = float(np.sqrt(0.5 * (np.var(b1_c, ddof=1) + np.var(b2_c, ddof=1))))
        
        # For recipe:
        b1_m = [m_entry[m] for k, m_entry in mid.items() if "_b1_" in k]
        b2_m = [m_entry[m] for k, m_entry in mid.items() if "_b2_" in k]
        m_seed_sd = float(np.sqrt(0.5 * (np.var(b1_m, ddof=1) + np.var(b2_m, ddof=1))))
        
        results["metrics"][m] = {
            "baseline_mean": c_mean,
            "baseline_se": c_se,
            "recipe_mean": m_mean,
            "recipe_se": m_se,
            "delta_mean": d_mean,
            "delta_se": d_se,
            "paired_t": float(t_stat),
            "paired_p": float(p_val),
            "bootstrap_ci95": [ci_low, ci_high],
            "baseline_seed_noise_sd": c_seed_sd,
            "recipe_seed_noise_sd": m_seed_sd
        }

    # Save output
    out_json = os.path.join(WORK_DIR, "scoreboard_before_after.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out_json}")

    # Print summary table
    print("\n" + "="*85)
    print(f"{'Metric':<18} | {'Baseline (Held)':<18} | {'Recipe (Mid-Fall)':<18} | {'Delta (R - B)':<18} | {'95% CI':<16}")
    print("="*85)
    for m in metrics:
        r = results["metrics"][m]
        b_str = f"{r['baseline_mean']:.4f} +/- {r['baseline_se']:.4f}"
        m_str = f"{r['recipe_mean']:.4f} +/- {r['recipe_se']:.4f}"
        d_str = f"{r['delta_mean']:+.4f} +/- {r['delta_se']:.4f}"
        ci_str = f"[{r['bootstrap_ci95'][0]:+.4f}, {r['bootstrap_ci95'][1]:+.4f}]"
        print(f"{m:<18} | {b_str:<18} | {m_str:<18} | {d_str:<18} | {ci_str:<16}")
    print("="*85)

if __name__ == "__main__":
    main()
