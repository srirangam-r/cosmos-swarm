#!/usr/bin/env python3
"""
Task 137: Unblinding and Statistical Analysis per PREREGISTRATION #3098
"""

import os
import sys
import json
import numpy as np
from scipy import stats

def wilson_interval(k, n, confidence=0.95):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return 0.0, (0.0, 0.0)
    p = k / n
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    spread = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, (max(0.0, centre - spread), min(1.0, centre + spread))

def paired_diff_ci(diffs, confidence=0.95):
    diffs = np.array(diffs, dtype=float)
    n = len(diffs)
    mean = float(np.mean(diffs))
    se = float(stats.sem(diffs)) if n > 1 else 0.0
    tcrit = stats.t.ppf(1 - (1 - confidence) / 2, df=n-1) if n > 1 else 0.0
    return mean, se, (mean - tcrit * se, mean + tcrit * se)

def run_unblinding(blind_eval_dir, eye_codes_file, out_file):
    key_file = os.path.join(blind_eval_dir, "KEY_LOCKED.json")
    metrics_file = os.path.join(blind_eval_dir, "automated_metrics_blind.json")
    
    with open(key_file) as f:
        key = json.load(f)
    with open(metrics_file) as f:
        auto_metrics = json.load(f)
    with open(eye_codes_file) as f:
        eye_codes = json.load(f)
        
    # Merge datasets
    merged = []
    for blind_id, kinfo in key.items():
        ecode = eye_codes.get(blind_id, {})
        ametric = auto_metrics.get(blind_id, {})
        
        row = {
            "blind_id": blind_id,
            "orig_base": kinfo["orig_base"],
            "arm": kinfo["arm"],
            "ball": kinfo["ball"],
            "seed": kinfo["seed"],
            "settled": 1 if ecode.get("settled_by_f92", "").upper() == "Y" else 0,
            "rest_frame": ecode.get("rest_frame"),
            "duplicate": ecode.get("duplicate_ball", 0),
            "morph": ecode.get("morph", 0),
            "exit": ecode.get("exit_frame", 0),
            "tether": ecode.get("tether_gripper", 0),
            "corridor_last20": ametric.get("corridor_last20", 0.0),
            "corridor_late": ametric.get("corridor_late", 0.0),
            "plank_late_chg_px": ametric.get("plank_late_chg_px", 0.0),
            "notes": ecode.get("notes", "")
        }
        merged.append(row)
        
    # Group by cell (ball, seed)
    # 6 cells: (ball1, 31), (ball1, 32), (ball1, 33), (ball2, 31), (ball2, 32), (ball2, 33)
    arms = ["F", "QT", "QTnc", "CO", "R"]
    arm_names = {
        "F": "Base Prompt (F)",
        "QT": "Full Timed-Settle (QT)",
        "QTnc": "QT No-Count (Persistence)",
        "CO": "Count-Only (CO)",
        "R": "Canonical Rule R (R)"
    }
    
    cells = {}
    for r in merged:
        c_id = (r["ball"], r["seed"])
        if c_id not in cells:
            cells[c_id] = {}
        cells[c_id][r["arm"]] = r
        
    print(f"Total evaluated cells: {len(cells)} (expected 6)")
    
    # Arm summaries
    arm_summary = {}
    for a in arms:
        a_rows = [r for r in merged if r["arm"] == a]
        n = len(a_rows)
        k_settled = sum(r["settled"] for r in a_rows)
        p, (ci_low, ci_high) = wilson_interval(k_settled, n)
        
        rest_frames = [r["rest_frame"] for r in a_rows if r["settled"] and r["rest_frame"] is not None]
        mean_rest = float(np.mean(rest_frames)) if rest_frames else None
        
        last20_vals = [r["corridor_last20"] for r in a_rows]
        mean_l20 = float(np.mean(last20_vals))
        se_l20 = float(stats.sem(last20_vals)) if n > 1 else 0.0
        
        art_count = sum(r["duplicate"] + r["morph"] + r["exit"] + r["tether"] for r in a_rows)
        
        arm_summary[a] = {
            "name": arm_names[a],
            "n": n,
            "settled_count": k_settled,
            "settle_rate": round(p, 4),
            "settle_wilson_95ci": [round(ci_low, 4), round(ci_high, 4)],
            "mean_rest_frame": round(mean_rest, 1) if mean_rest else None,
            "corridor_last20_mean": round(mean_l20, 4),
            "corridor_last20_se": round(se_l20, 4),
            "gross_artifact_count": art_count
        }
        
    # Paired contrasts vs Base F
    contrasts = {}
    for test_arm in ["QT", "QTnc", "CO", "R"]:
        settle_diffs = []
        l20_diffs = []
        paired_details = []
        
        for c_id in sorted(cells.keys()):
            f_row = cells[c_id].get("F")
            t_row = cells[c_id].get(test_arm)
            if f_row and t_row:
                s_diff = t_row["settled"] - f_row["settled"]
                l_diff = t_row["corridor_last20"] - f_row["corridor_last20"]
                settle_diffs.append(s_diff)
                l20_diffs.append(l_diff)
                paired_details.append({
                    "ball": c_id[0],
                    "seed": c_id[1],
                    "base_settled": f_row["settled"],
                    "test_settled": t_row["settled"],
                    "base_l20": f_row["corridor_last20"],
                    "test_l20": t_row["corridor_last20"],
                    "delta_settle": s_diff,
                    "delta_l20": round(l_diff, 4)
                })
                
        n_pairs = len(settle_diffs)
        k_settle_lift = sum(settle_diffs)
        mean_l20_diff, se_l20_diff, ci_l20 = paired_diff_ci(l20_diffs)
        
        # McNemar / sign test for settle count
        n_discordant_up = sum(1 for d in settle_diffs if d > 0)
        n_discordant_down = sum(1 for d in settle_diffs if d < 0)
        
        contrasts[f"{test_arm}_minus_F"] = {
            "test_arm": test_arm,
            "test_name": arm_names[test_arm],
            "n_pairs": n_pairs,
            "paired_settle_lift": k_settle_lift,
            "discordant_pairs": f"{n_discordant_up} up, {n_discordant_down} down",
            "delta_corridor_last20_mean": round(mean_l20_diff, 4),
            "delta_corridor_last20_se": round(se_l20_diff, 4),
            "delta_corridor_last20_95ci": [round(ci_l20[0], 4), round(ci_l20[1], 4)],
            "paired_details": paired_details
        }
        
    final_output = {
        "arms": arm_summary,
        "contrasts": contrasts,
        "raw_merged": merged
    }
    
    with open(out_file, "w") as out_f:
        json.dump(final_output, out_f, indent=2)
    print(f"Unblinded analysis complete! Results written to {out_file}")
    return final_output

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 analyze_and_unblind.py <blind_dir> <eye_codes.json> <out.json>")
        sys.exit(1)
    run_unblinding(sys.argv[1], sys.argv[2], sys.argv[3])
