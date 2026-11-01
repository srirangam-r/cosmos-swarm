#!/usr/bin/env python3
"""
summarize_results.py: Aggregates kinematics and NV scoreboard results
for Task 140 (Rule R on GAUGE dev scenes).
"""

import json
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
KIN_FILE = BASE_DIR / "kinematics_results.json"
SCORE_FILE = BASE_DIR / "nv_scores.json"

if not KIN_FILE.exists():
    print(f"Kinematics file {KIN_FILE} not found.")
    exit(0)

with open(KIN_FILE) as f:
    kin_data = json.load(f)

scores_data = {}
if SCORE_FILE.exists():
    with open(SCORE_FILE) as f:
        scores_data = json.load(f)

# Group by scene and arm
scenes = ["slope_wood", "slope_plastic", "pend_rest", "pend_mid"]
arms = ["base", "r", "n"]

summary = {}
for sc in scenes:
    summary[sc] = {}
    for arm in arms:
        matching = [v for k, v in kin_data.items() if v.get("scene") == sc and v.get("arm") == arm]
        if not matching:
            continue
        
        n = len(matching)
        if "slope" in sc:
            rest_rate = float(np.mean([1.0 if m.get("at_rest_at_f92") else 0.0 for m in matching]))
            v_peaks = [m.get("v_peak_mps", 0) for m in matching]
            v_lates = [m.get("v_late_mean_mps", 0) for m in matching]
            slide_ms = [m.get("slide_m", 0) for m in matching]
            summary[sc][arm] = {
                "n": n,
                "rest_rate_f92": round(rest_rate, 3),
                "v_peak_mean": round(float(np.mean(v_peaks)), 3),
                "v_late_mean": round(float(np.mean(v_lates)), 3),
                "slide_m_mean": round(float(np.mean(slide_ms)), 3)
            }
        elif sc == "pend_rest":
            rel_rate = float(np.mean([1.0 if m.get("released") else 0.0 for m in matching]))
            summary[sc][arm] = {
                "n": n,
                "release_rate": round(rel_rate, 3),
                "still_rest_rate": round(1.0 - rel_rate, 3),
                "early_energy_mean": round(float(np.mean([m.get("early_motion_energy", 0) for m in matching])), 3),
                "late_energy_mean": round(float(np.mean([m.get("late_motion_energy", 0) for m in matching])), 3)
            }
        else: # pend_mid
            rest_rate = float(np.mean([1.0 if m.get("at_rest_at_f92") else 0.0 for m in matching]))
            decay_ratios = [m.get("decay_ratio", 1.0) for m in matching]
            summary[sc][arm] = {
                "n": n,
                "rest_rate_f92": round(rest_rate, 3),
                "decay_ratio_mean": round(float(np.mean(decay_ratios)), 3),
                "early_energy_mean": round(float(np.mean([m.get("early_motion_energy", 0) for m in matching])), 3),
                "late_energy_mean": round(float(np.mean([m.get("late_motion_energy", 0) for m in matching])), 3)
            }

out_summary = BASE_DIR / "summary_contrasts.json"
with open(out_summary, "w") as f:
    json.dump(summary, f, indent=2)

print("Summary Contrasts:")
print(json.dumps(summary, indent=2))
