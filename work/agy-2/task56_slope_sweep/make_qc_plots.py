#!/usr/bin/env python3
"""Generate publication-quality QC plots for slope sweep replication."""
import json
import matplotlib.pyplot as plt
import numpy as np

with open("summary_slope_sweep.json") as f:
    summary = json.load(f)

with open("results_slope_sweep.json") as f:
    results = json.load(f)

# 1. Bar chart comparing Peak Velocities across arms
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

arms_order = ["base", "cfg1", "cfg3", "fps12", "nf189"]
arm_labels = ["Base (CFG 6)", "CFG 1.0", "CFG 3.0", "FPS 12", "NF 189 (7.9s)"]

# Plastic
p_means = [summary[f"plastic_{a}"]["peak_v_lg_mean"] for a in arms_order]
p_ses = [summary[f"plastic_{a}"]["peak_v_lg_se"] for a in arms_order]
p_seeds = [summary[f"plastic_{a}"]["peaks_lg_per_seed"] for a in arms_order]

x = np.arange(len(arms_order))
ax1.bar(x, p_means, yerr=p_ses, capsize=5, color="#3498db", alpha=0.7, edgecolor="#2980b9", label="Plastic (LG NCC Mean $\\pm$ SE)")
for i, seeds in enumerate(p_seeds):
    ax1.scatter([x[i]] * len(seeds), seeds, color="#e74c3c", zorder=5, alpha=0.8, s=40)

ax1.axhline(1.47, color="black", linestyle="--", linewidth=1.5, label="Physical Mocap (1.47 m/s)")
ax1.axhline(0.40, color="gray", linestyle=":", linewidth=1.2, label="Plastic Ceiling (~0.40 m/s)")
ax1.set_xticks(x)
ax1.set_xticklabels(arm_labels, rotation=25, ha="right")
ax1.set_ylabel("Peak Slide Velocity (m/s)", fontsize=11)
ax1.set_title("Plastic Slope: Slide Speed across Arms", fontsize=12, fontweight="bold")
ax1.set_ylim(-0.05, 1.6)
ax1.grid(axis="y", linestyle="--", alpha=0.5)
ax1.legend(loc="upper right", fontsize=9)

# Wood
w_means = [summary[f"wood_{a}"]["peak_v_lg_mean"] for a in arms_order]
w_ses = [summary[f"wood_{a}"]["peak_v_lg_se"] for a in arms_order]
w_seeds = [summary[f"wood_{a}"]["peaks_lg_per_seed"] for a in arms_order]

ax2.bar(x, w_means, yerr=w_ses, capsize=5, color="#2ecc71", alpha=0.7, edgecolor="#27ae60", label="Wood (LG NCC Mean $\\pm$ SE)")
for i, seeds in enumerate(w_seeds):
    ax2.scatter([x[i]] * len(seeds), seeds, color="#e74c3c", zorder=5, alpha=0.8, s=40)

ax2.axhline(1.47, color="black", linestyle="--", linewidth=1.5, label="Physical Mocap (1.47 m/s)")
ax2.set_xticks(x)
ax2.set_xticklabels(arm_labels, rotation=25, ha="right")
ax2.set_title("Wood Slope: Slide Speed across Arms", fontsize=12, fontweight="bold")
ax2.grid(axis="y", linestyle="--", alpha=0.5)
ax2.legend(loc="upper right", fontsize=9)

plt.tight_layout()
plt.savefig("qc_slope_sweep_velocities.png", dpi=150)
plt.close()

# 2. Velocity Bins Comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Plot representative seed 1 velocity bins across arms
for a, col in zip(["base", "cfg1", "cfg3", "fps12", "nf189"], ["#2c3e50", "#e74c3c", "#f39c12", "#3498db", "#9b59b6"]):
    key = f"plastic_{a}_s1"
    bins = results[key]["indep_lab_grad_ncc"].get("v_bins_0p25s", [])
    tb = np.arange(len(bins)) * 0.25
    ax1.plot(tb, bins, marker="o", label=f"plastic {a}", color=col, linewidth=1.8)

ax1.set_xlabel("Time from Onset (s)", fontsize=11)
ax1.set_ylabel("Velocity in 0.25s Bin (m/s)", fontsize=11)
ax1.set_title("Plastic (Seed 1): Velocity vs Time", fontsize=12, fontweight="bold")
ax1.set_ylim(-0.02, 0.55)
ax1.grid(True, linestyle="--", alpha=0.5)
ax1.legend(loc="upper right", fontsize=9)

for a, col in zip(["base", "cfg1", "cfg3", "fps12", "nf189"], ["#2c3e50", "#e74c3c", "#f39c12", "#3498db", "#9b59b6"]):
    key = f"wood_{a}_s1"
    bins = results[key]["indep_lab_grad_ncc"].get("v_bins_0p25s", [])
    tb = np.arange(len(bins)) * 0.25
    ax2.plot(tb, bins, marker="s", label=f"wood {a}", color=col, linewidth=1.8)

ax2.set_xlabel("Time from Onset (s)", fontsize=11)
ax2.set_ylabel("Velocity in 0.25s Bin (m/s)", fontsize=11)
ax2.set_title("Wood (Seed 1): Velocity vs Time", fontsize=12, fontweight="bold")
ax2.set_ylim(-0.02, 0.85)
ax2.grid(True, linestyle="--", alpha=0.5)
ax2.legend(loc="upper right", fontsize=9)

plt.tight_layout()
plt.savefig("qc_slope_sweep_bins.png", dpi=150)
plt.close()

print("Plots successfully saved: qc_slope_sweep_velocities.png, qc_slope_sweep_bins.png")
