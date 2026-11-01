#!/usr/bin/env python3
import json, os
import numpy as np

WORK_DIR = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task72_score_review"
results_file = os.path.join(WORK_DIR, "firstfall_16_clips_results.json")

with open(results_file) as f:
    data = json.load(f)

print("=== BASELINE HELD-BALL CLIPS (box_ctrl) ===")
ctrl_releases = 0
ctrl_total = len(data["baseline_held"])
for k, v in data["baseline_held"].items():
    flag = v.get("flag", "error")
    g = v.get("g")
    fall_px = v.get("fall_px")
    fall_time = v.get("fall_time_s")
    if flag in ("ok", "weak") and g is not None:
        ctrl_releases += 1
        print(f"  {k:25s}: flag={flag:6s} g={g:6.2f} m/s² fall_px={fall_px:6.1f} t_fall={fall_time:5.3f}s")
    else:
        print(f"  {k:25s}: flag={flag:6s} (NO RELEASE / TRACK LOST)")

print(f"\nBaseline Release Rate: {ctrl_releases}/{ctrl_total} ({100*ctrl_releases/ctrl_total:.1f}%)")

print("\n=== RECIPE MID-FALL CLIPS (box_mid) ===")
mid_g_vals = []
mid_g_h_T = []
mid_fall_times = []
mid_fall_px = []
mid_flags = []

for k, v in data["recipe_midfall"].items():
    flag = v.get("flag", "error")
    g = v.get("g")
    g_hT = v.get("g_from_h_T")
    fall_px = v.get("fall_px")
    fall_time = v.get("fall_time_s")
    r2 = v.get("r2")
    mid_flags.append(flag)
    
    if g is not None:
        mid_g_vals.append(g)
    if g_hT is not None:
        mid_g_h_T.append(g_hT)
    if fall_time is not None:
        mid_fall_times.append(fall_time)
    if fall_px is not None:
        mid_fall_px.append(fall_px)
        
    g_str = f"{g:6.2f}" if g is not None else "  None"
    ghT_str = f"{g_hT:6.2f}" if g_hT is not None else "  None"
    r2_str = f"{r2:6.4f}" if r2 is not None else "  None"
    px_str = f"{fall_px:6.1f}" if fall_px is not None else "  None"
    t_str = f"{fall_time:5.3f}" if fall_time is not None else " None"
    print(f"  {k:25s}: flag={flag:6s} g={g_str} m/s² (g_hT={ghT_str}) r2={r2_str} fall_px={px_str} t_fall={t_str}s")

mean_g = float(np.mean(mid_g_vals))
se_g = float(np.std(mid_g_vals, ddof=1) / np.sqrt(len(mid_g_vals)))
ci95_g = [mean_g - 1.96 * se_g, mean_g + 1.96 * se_g]

mean_ghT = float(np.mean(mid_g_h_T))
se_ghT = float(np.std(mid_g_h_T, ddof=1) / np.sqrt(len(mid_g_h_T)))

print(f"\nRecipe Free-Fall g (Quadratic Fit):  {mean_g:.2f} ± {se_g:.2f} m/s² (95% CI: [{ci95_g[0]:.2f}, {ci95_g[1]:.2f}], n={len(mid_g_vals)})")
print(f"Recipe Free-Fall g (Kinematic 2h/T²): {mean_ghT:.2f} ± {se_ghT:.2f} m/s² (n={len(mid_g_h_T)})")
print(f"Flags: {dict((f, mid_flags.count(f)) for f in set(mid_flags))}")
