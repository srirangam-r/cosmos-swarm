#!/usr/bin/env python3
import json, os
import numpy as np

WORK_DIR = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task72_score_review"
out_f0 = os.path.join(WORK_DIR, "scores_real_f0.json")
out_mid = os.path.join(WORK_DIR, "scores_real_midfall.json")

with open(out_f0) as f:
    d_f0 = json.load(f)
with open(out_mid) as f:
    d_mid = json.load(f)

ball_configs = [
    (1, 33),
    (2, 35),
    (3, 34),
    (4, 34),
]

metrics = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_norm", "dd_binary"]
comparison = {"per_ball": {}, "summary": {}}

for b, mid_f in ball_configs:
    name_f0 = f"real_ball_{b}_f0_93f.mp4"
    name_mid = f"real_ball_{b}_midfall_dd{mid_f}_93f_orig.mp4"
    
    s_f0 = d_f0[name_f0]
    s_mid = d_mid[name_mid]
    
    ball_diff = {}
    for m in metrics:
        ball_diff[m] = {
            "f0": s_f0[m],
            "mid": s_mid[m],
            "diff": s_mid[m] - s_f0[m]
        }
    comparison["per_ball"][f"ball_{b}"] = ball_diff

for m in metrics:
    diffs = [comparison["per_ball"][f"ball_{b}"][m]["diff"] for b, _ in ball_configs]
    mean_diff = float(np.mean(diffs))
    se_diff = float(np.std(diffs, ddof=1) / np.sqrt(len(diffs)))
    comparison["summary"][m] = {
        "mean_diff": mean_diff,
        "se_diff": se_diff,
        "ci95": [mean_diff - 1.96 * se_diff, mean_diff + 1.96 * se_diff],
        "values": diffs
    }

out_comp = os.path.join(WORK_DIR, "real_video_control_comparison.json")
with open(out_comp, "w") as f:
    json.dump(comparison, f, indent=2)

print("\n=== REAL VIDEO INPUT CONTROL SUMMARY (Midfall - f0, n=4 Real GAUGE Drops) ===")
for m in metrics:
    s = comparison["summary"][m]
    vals = [f"{v:+.4f}" for v in s['values']]
    print(f"{m:18s}: Δ = {s['mean_diff']:+.5f} ± {s['se_diff']:.5f} (95% CI: [{s['ci95'][0]:+.5f}, {s['ci95'][1]:+.5f}]) | per-ball: {vals}")
