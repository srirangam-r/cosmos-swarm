#!/usr/bin/env python3
"""
Task 118: Independent Replication and Review of Finding 2668
Audit of HUE Plausibility Judge Window Split (Early f0-35 vs Late f46-92)
Author: agy-4
"""

import json
import os
import re
import numpy as np
import scipy.stats as stats

def bootstrap_ci(diffs, n_boot=100000, alpha=0.05, seed=42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot_means = rng.choice(diffs, size=(n_boot, n), replace=True).mean(axis=1)
    lower = np.percentile(boot_means, 100 * (alpha / 2))
    upper = np.percentile(boot_means, 100 * (1 - alpha / 2))
    return float(lower), float(upper)

def run_audit():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    trunc_dir = os.path.join(repo_root, "work/ro-1/hue_trunc")
    full_dir = os.path.join(repo_root, "work/ro-1/hue_qt")
    
    trunc_res_path = os.path.join(trunc_dir, "res.json")
    full_pair_path = os.path.join(full_dir, "pair.json")
    
    with open(trunc_res_path) as f:
        trunc_raw = json.load(f)["results"]
        
    with open(full_pair_path) as f:
        full_pair = json.load(f)
        
    # Aggregate raw predictions by clip stem
    by_clip = {}
    for r in trunc_raw:
        clip_name = os.path.basename(r["clip"])
        stem = re.sub(r"\.mp4$", "", clip_name)
        entry = dict(r["summary"])
        for row in r["rows"]:
            entry[f"Q{row['id']}"] = row["p_yes"]
        by_clip.setdefault(stem, []).append(entry)
        
    # Average across offsets (0.0 and 0.5)
    mean_by_clip = {
        stem: {k: float(np.mean([x[k] for x in entries])) for k in entries[0]}
        for stem, entries in by_clip.items()
    }
    
    # 8 matched pairs
    pairs_def = [
        ("ball_F_ball1_fps24_93f_s1", "cause_QT_ball1_fps24_93f_s1"),
        ("ball_F_ball1_fps24_93f_s2", "cause_QT_ball1_fps24_93f_s2"),
        ("cause5_F_ball1_fps24_93f_s3", "cause5_QT_ball1_fps24_93f_s3"),
        ("cause5_F_ball1_fps24_93f_s4", "cause5_QT_ball1_fps24_93f_s4"),
        ("cause5_F_ball1_fps24_93f_s5", "cause5_QT_ball1_fps24_93f_s5"),
        ("ball_F_ball2_fps24_93f_s1", "cause6_QT_ball2_fps24_93f_s1"),
        ("ball_F_ball2_fps24_93f_s2", "cause6_QT_ball2_fps24_93f_s2"),
        ("cause6_F_ball2_fps24_93f_s3", "cause6_QT_ball2_fps24_93f_s3"),
    ]
    
    metrics_to_audit = ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment", "Q1", "Q2", "Q4", "Q5", "Q6", "Q12"]
    
    audit_results = {}
    
    for window in ["early", "late"]:
        w_real_key = f"{window}__real_ball1_dd32_93f"
        real_vals = mean_by_clip[w_real_key]
        
        w_res = {
            "window": window,
            "n": len(pairs_def),
            "real_scores": {k: real_vals.get(k, None) for k in metrics_to_audit if k in real_vals},
            "metrics": {},
            "distance_to_real": {}
        }
        
        for k in metrics_to_audit:
            if k not in real_vals:
                continue
            f_vals = np.array([mean_by_clip[f"{window}__{p[0]}"][k] for p in pairs_def])
            qt_vals = np.array([mean_by_clip[f"{window}__{p[1]}"][k] for p in pairs_def])
            diffs = qt_vals - f_vals
            
            mean_f = float(np.mean(f_vals))
            mean_qt = float(np.mean(qt_vals))
            real_val = float(real_vals[k])
            
            mean_diff = float(np.mean(diffs))
            se_diff = float(stats.sem(diffs))
            sd_diff = float(np.std(diffs, ddof=1))
            
            t_stat, p_val = stats.ttest_1samp(diffs, 0.0)
            ci95_low, ci95_high = bootstrap_ci(diffs)
            
            # Distance to real
            dist_f = float(np.abs(mean_f - real_val))
            dist_qt = float(np.abs(mean_qt - real_val))
            dist_ratio = float(dist_f / dist_qt) if dist_qt > 1e-6 else 999.0
            
            # Per-pair distance to real
            pair_dist_f = np.abs(f_vals - real_val)
            pair_dist_qt = np.abs(qt_vals - real_val)
            dist_diffs = pair_dist_qt - pair_dist_f # negative means QT is closer
            mean_dist_diff = float(np.mean(dist_diffs))
            se_dist_diff = float(stats.sem(dist_diffs))
            n_closer = int(np.sum(dist_diffs < 0))
            
            w_res["metrics"][k] = {
                "mean_F": mean_f,
                "mean_QT": mean_qt,
                "mean_diff": mean_diff,
                "se_diff": se_diff,
                "sd_diff": sd_diff,
                "t_stat": float(t_stat),
                "p_val": float(p_val),
                "ci95_bootstrap": [ci95_low, ci95_high],
                "n_pos": int(np.sum(diffs > 0)),
            }
            
            w_res["distance_to_real"][k] = {
                "dist_F": dist_f,
                "dist_QT": dist_qt,
                "ratio_F_over_QT": dist_ratio,
                "mean_paired_dist_diff": mean_dist_diff,
                "se_paired_dist_diff": se_dist_diff,
                "n_closer_to_real": n_closer,
            }
            
        audit_results[window] = w_res
        
    # Also replicate full-clip metrics
    full_metrics = {}
    full_real = full_pair["real_ref"]
    for k in ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment", "Q4", "Q6", "Q12"]:
        data_k = full_pair["QT-F"][k]
        dist_f = abs(data_k["F"] - full_real[k])
        dist_qt = abs(data_k["QT"] - full_real[k])
        full_metrics[k] = {
            "mean_F": data_k["F"],
            "mean_QT": data_k["QT"],
            "mean_diff": data_k["diff"],
            "se_diff": data_k["se"],
            "real": full_real[k],
            "dist_F": dist_f,
            "dist_QT": dist_qt,
        }
    audit_results["full_clip"] = full_metrics
    
    out_json = os.path.join(os.path.dirname(__file__), "task118_review_results.json")
    with open(out_json, "w") as f:
        json.dump(audit_results, f, indent=2)
        
    print(f"Audit results written to {out_json}")
    
    # Print summary table
    print("\n=== TASK 118 REPLICATION SUMMARY ===")
    print("Early Window (f0-35, while bouncing):")
    for k in ["overall", "Physical Laws", "Q1", "Q2", "Q5", "Q6"]:
        m = audit_results["early"]["metrics"][k]
        d = audit_results["early"]["distance_to_real"][k]
        r = audit_results["early"]["real_scores"][k]
        print(f"  {k:15s} | F: {m['mean_F']:.3f} | QT: {m['mean_QT']:.3f} | Real: {r:.3f} | Diff: {m['mean_diff']:+.3f} ± {m['se_diff']:.3f} (p={m['p_val']:.3f}) | |QT-real|: {d['dist_QT']:.3f} vs |F-real|: {d['dist_F']:.3f}")
        
    print("\nLate Window (f46-92, while settled):")
    for k in ["overall", "Physical Laws", "Q1", "Q2", "Q5", "Q6"]:
        m = audit_results["late"]["metrics"][k]
        d = audit_results["late"]["distance_to_real"][k]
        r = audit_results["late"]["real_scores"][k]
        print(f"  {k:15s} | F: {m['mean_F']:.3f} | QT: {m['mean_QT']:.3f} | Real: {r:.3f} | Diff: {m['mean_diff']:+.3f} ± {m['se_diff']:.3f} (p={m['p_val']:.3f}) | |QT-real|: {d['dist_QT']:.3f} vs |F-real|: {d['dist_F']:.3f} (Ratio: {d['ratio_F_over_QT']:.1f}x closer)")

if __name__ == "__main__":
    run_audit()
