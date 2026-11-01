#!/usr/bin/env python3
"""
Generate publication-quality diagnostic figure for independent replication of Finding #4962 (Program N, E4).
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT_DIR = "/home/nail/swarm-work/agy-2/t249_e4_review"
DATA_FILE = os.path.join(OUT_DIR, "replicate_finding_4962_results.json")

def main():
    with open(DATA_FILE) as f:
        data = json.load(f)

    arms_data = data["metrics_per_arm"]
    arms = ["tlo", "thi", "slo", "shi", "reg"]
    labels = ["Temporal Low\n(|f|≤1/8, 29%)", "Temporal High\n(71%)", "Spatial Low\n(~6%)", "Spatial High\n(~94%)", "Region\n(Ball Path 10%)"]
    colors = ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Program N (E4): Initial Noise Component Decomposition on Cosmos3-Nano Dynamics\nIndependent Replication of Finding #4962 (n=9 seed clusters, seeds 401–412 on ball1_dd33)", fontsize=14, fontweight='bold', y=0.98)

    # Panel 1: Video Toward B
    ax1 = axes[0, 0]
    for i, arm in enumerate(arms):
        vals = arms_data[arm]["video_toward_B"]["values"]
        m = arms_data[arm]["video_toward_B"]["mean"]
        se = arms_data[arm]["video_toward_B"]["se"]
        x = np.random.normal(i, 0.04, size=len(vals))
        ax1.scatter(x, vals, color=colors[i], alpha=0.7, s=40, edgecolors='black', linewidth=0.5)
        ax1.errorbar(i, m, yerr=se, fmt='o', color='black', ecolor='black', elinewidth=2, capsize=5, markersize=8)

    ax1.axhline(0.5, color='gray', linestyle='--', alpha=0.5, label='Equal Mix (50%)')
    ax1.set_xticks(range(len(arms)))
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel("Toward B:  $d(mix, A) / [d(mix, A) + d(mix, B)]$", fontsize=10)
    ax1.set_title("A. Whole-Clip Pixel MAE Toward B (n=9)", fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.set_ylim(0.25, 0.75)

    # Panel 2: Motion Course Toward B
    ax2 = axes[0, 1]
    for i, arm in enumerate(arms):
        vals = arms_data[arm]["motion_course_toward_B"]["values"]
        m = arms_data[arm]["motion_course_toward_B"]["mean"]
        se = arms_data[arm]["motion_course_toward_B"]["se"]
        x = np.random.normal(i, 0.04, size=len(vals))
        ax2.scatter(x, vals, color=colors[i], alpha=0.7, s=40, edgecolors='black', linewidth=0.5)
        ax2.errorbar(i, m, yerr=se, fmt='o', color='black', ecolor='black', elinewidth=2, capsize=5, markersize=8)

    ax2.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
    ax2.set_xticks(range(len(arms)))
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel("Toward B:  $e_A / (e_A + e_B)$", fontsize=10)
    ax2.set_title("B. Motion Energy Course Correlation Toward B (n=9)", fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.set_ylim(0.25, 0.85)

    # Panel 3: Late Motion Toward B (n=5)
    ax3 = axes[1, 0]
    for i, arm in enumerate(arms):
        vals = arms_data[arm]["late_motion_toward_B"]["values"]
        m = arms_data[arm]["late_motion_toward_B"]["mean"]
        se = arms_data[arm]["late_motion_toward_B"]["se"]
        x = np.random.normal(i, 0.04, size=len(vals))
        ax3.scatter(x, vals, color=colors[i], alpha=0.7, s=45, edgecolors='black', linewidth=0.5)
        ax3.errorbar(i, m, yerr=se, fmt='o', color='black', ecolor='black', elinewidth=2, capsize=5, markersize=8)

    ax3.axhline(0.0, color='gray', linestyle='-', alpha=0.3)
    ax3.axhline(1.0, color='gray', linestyle='--', alpha=0.5, label='Complete Shift to B')
    ax3.set_xticks(range(len(arms)))
    ax3.set_xticklabels(labels, fontsize=9)
    ax3.set_ylabel("Toward B:  $(LM_X - LM_A) / (LM_B - LM_A)$", fontsize=10)
    ax3.set_title("C. Late-Motion Toward B (|ΔLM| > 0.3, n=5 pairs)", fontweight='bold')
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.set_ylim(-0.5, 1.6)

    # Panel 4: Paired Trajectory Shift (tlo vs thi & slo vs shi)
    ax4 = axes[1, 1]
    v_tlo = np.array(arms_data["tlo"]["video_toward_B"]["values"])
    v_thi = np.array(arms_data["thi"]["video_toward_B"]["values"])
    v_slo = np.array(arms_data["slo"]["video_toward_B"]["values"])
    v_shi = np.array(arms_data["shi"]["video_toward_B"]["values"])

    ax4.scatter(v_thi, v_tlo, color='#1f77b4', s=60, edgecolors='black', label='Temporal: Low vs High')
    ax4.scatter(v_shi, v_slo, color='#ff7f0e', s=60, marker='s', edgecolors='black', label='Spatial: Low vs High')

    lims = [0.25, 0.75]
    ax4.plot(lims, lims, 'k--', alpha=0.5, label='Equality line (Low = High)')
    ax4.set_xlim(lims)
    ax4.set_ylim(lims)
    ax4.set_xlabel("High-Frequency Toward B", fontsize=10)
    ax4.set_ylabel("Low-Frequency Toward B", fontsize=10)
    ax4.set_title("D. Low vs High Frequency Asymmetry per Seed Pair", fontweight='bold')
    ax4.legend(loc='lower right', frameon=True)
    ax4.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plot_path = os.path.join(OUT_DIR, "figure_e4_noise_component_replication.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"Saved plot to {plot_path}")

if __name__ == "__main__":
    main()
