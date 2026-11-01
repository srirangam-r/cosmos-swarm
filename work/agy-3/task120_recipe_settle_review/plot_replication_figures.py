#!/usr/bin/env python3
"""
Publication-quality figures for Task 120 / Finding #2720 independent replication:
4-panel comparison of Recipe prompt timed-settle clause (RECT vs REC).
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = "/home/nail/swarm-work/agy-3/cosmos-swarm"
TASK_DIR = os.path.join(REPO_ROOT, "work/agy-3/task120_recipe_settle_review")
RESULTS_PATH = os.path.join(TASK_DIR, "task120_replication_results.json")

with open(RESULTS_PATH) as f:
    res = json.load(f)

fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# Panel A: Late Corridor Motion (last20)
ax = axes[0, 0]
rec_last20 = res["last20"]["rec_vals"]
rect_last20 = res["last20"]["rect_vals"]
pairs_x = [1, 2]

for i in range(len(rec_last20)):
    ax.plot([1, 2], [rec_last20[i], rect_last20[i]], color="gray", alpha=0.7, linestyle="--", marker="o")

ax.errorbar([1], [res["last20"]["rec_mean"]], yerr=[res["last20"]["rec_se"]], fmt="s", color="darkred", 
            markersize=10, capsize=6, elinewidth=2.5, label=f"REC (Default): {res['last20']['rec_mean']:.2f} ± {res['last20']['rec_se']:.2f}")
ax.errorbar([2], [res["last20"]["rect_mean"]], yerr=[res["last20"]["rect_se"]], fmt="s", color="darkgreen", 
            markersize=10, capsize=6, elinewidth=2.5, label=f"RECT (+Timed Settle): {res['last20']['rect_mean']:.2f} ± {res['last20']['rect_se']:.2f}")

# Real reference line
ax.axhline(0.75, color="blue", linestyle=":", linewidth=2, label="Real GAUGE Continuation (0.75)")

ax.set_xticks([1, 2])
ax.set_xticklabels(["REC (Recipe Base)\n[Default Prompt]", "RECT (Recipe Fix)\n[+Timed Settle]"], fontsize=11, fontweight="bold")
ax.set_ylabel("Last 20 Frames Mean Pixel Diff", fontsize=11, fontweight="bold")
ax.set_title(f"A. Corridor Motion Collapse (f73-92)\nPaired Δ = {res['last20']['delta_mean']:+.2f} ± {res['last20']['delta_se']:.2f} (6/6 lower, p = {res['last20']['p_val']:.4f})", 
             fontsize=12, fontweight="bold")
ax.grid(True, linestyle=":", alpha=0.6)
ax.legend(fontsize=9, loc="upper right")

# Panel B: DOVER Fused Quality & Non-Inferiority
ax = axes[0, 1]
dover_delta = res["dover_fused"]["delta_mean"]
dover_se = res["dover_fused"]["delta_se"]
ci90 = res["dover_fused"]["ci90_t"]
ci95 = res["dover_fused"]["ci95_t"]

ax.axvline(0, color="black", linestyle="-", alpha=0.4)
ax.axvline(-0.020, color="red", linestyle="--", linewidth=2, label="Non-Inferiority Margin (-δ = -0.020)")
ax.axvline(-0.030, color="darkred", linestyle=":", linewidth=1.5, label="Exploratory Bound (-δ = -0.030)")

# Plot confidence intervals
ax.errorbar([dover_delta], [1], xerr=[[dover_delta - ci95[0]], [ci95[1] - dover_delta]], fmt="o", color="blue",
            capsize=6, elinewidth=2.5, label=f"Paired Δ: {dover_delta:+.4f} ± {dover_se:.4f}\n90% CI [{ci90[0]:+.3f}, {ci90[1]:+.3f}]\n95% CI [{ci95[0]:+.3f}, {ci95[1]:+.3f}]")

ax.set_yticks([1])
ax.set_yticklabels(["RECT − REC\n(n=6 pairs)"], fontsize=11, fontweight="bold")
ax.set_xlabel("Paired Difference in DOVER Fused Score", fontsize=11, fontweight="bold")
ax.set_xlim(-0.035, 0.025)
ax.set_title("B. DOVER Visual Quality Non-Inferiority\nZero Statistically Detectable Degradation (p = 0.6177)", fontsize=12, fontweight="bold")
ax.grid(True, linestyle=":", alpha=0.6)
ax.legend(fontsize=9, loc="lower left")

# Panel C: Optical Flow (RAFT) Temporal Profile
ax = axes[1, 0]
rec_flow = res["optical_flow"]["mean_rec_flow_profile"]
rect_flow = res["optical_flow"]["mean_rect_flow_profile"]
pairs_time = np.arange(1, 31) * 3 # ~ frames 3 to 90

ax.plot(pairs_time, rec_flow, color="darkred", linewidth=2.5, marker="o", label=f"REC Mean Flow (Late: {res['optical_flow']['late_rec_flow']:.2f})")
ax.plot(pairs_time, rect_flow, color="darkgreen", linewidth=2.5, marker="s", label=f"RECT Mean Flow (Late: {res['optical_flow']['late_rect_flow']:.2f})")
ax.axvline(45, color="gray", linestyle="--", label="Window Midpoint (f45)")

ax.set_xlabel("Video Frame Index", fontsize=11, fontweight="bold")
ax.set_ylabel("Optical Flow Magnitude (dd_maxrad, px)", fontsize=11, fontweight="bold")
ax.set_title("C. Optical Flow Trajectory Over Time\nRECT Flow Attenuates by 82.2% into Rest", fontsize=12, fontweight="bold")
ax.grid(True, linestyle=":", alpha=0.6)
ax.legend(fontsize=9, loc="upper right")

# Panel D: Physical Outcome & Artifact Taxonomy
ax = axes[1, 1]
categories = ["Settled at Rest\n(f92)", "Undamped Perpetual\nBounce", "Gross Visual\nArtifacts"]
rec_counts = [0, 6, 4] # out of 6
rect_counts = [5, 1, 0] # out of 6

x = np.arange(len(categories))
width = 0.35

rects1 = ax.bar(x - width/2, [c/6*100 for c in rec_counts], width, label="REC (Recipe Default)", color="#e74c3c", alpha=0.85, edgecolor="black")
rects2 = ax.bar(x + width/2, [c/6*100 for c in rect_counts], width, label="RECT (+Timed Settle)", color="#2ecc71", alpha=0.85, edgecolor="black")

# Add count labels
for rect in rects1:
    h = rect.get_height()
    ax.annotate(f"{int(h/100*6)}/6 ({h:.0f}%)", xy=(rect.get_x() + rect.get_width()/2, h),
                xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")

for rect in rects2:
    h = rect.get_height()
    ax.annotate(f"{int(h/100*6)}/6 ({h:.0f}%)", xy=(rect.get_x() + rect.get_width()/2, h),
                xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10, fontweight="bold")
ax.set_ylabel("Percentage of Clips (%)", fontsize=11, fontweight="bold")
ax.set_ylim(0, 115)
ax.set_title("D. Outcome & Artifact Taxonomy (n=6 Pairs)\n83.3% Rest & Complete Extinction of Gross Hallucinations", fontsize=12, fontweight="bold")
ax.grid(True, linestyle=":", alpha=0.6, axis="y")
ax.legend(fontsize=9, loc="upper right")

plt.suptitle("Finding #2720 Independent Replication: Recipe Timed-Settle Clause (RECT vs REC)", fontsize=15, fontweight="bold", y=0.99)
plt.tight_layout()

plot_path = os.path.join(TASK_DIR, "plots/figure_recipe_settle_replication.png")
plt.savefig(plot_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"Saved publication figure to {plot_path}")
