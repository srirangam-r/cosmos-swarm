#!/usr/bin/env python3
"""Generate high-resolution publication-quality figure for NVIDIA scoreboard before/after comparison.
"""
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

WORK_DIR = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task68_nv_scoreboard"
JSON_PATH = os.path.join(WORK_DIR, "scoreboard_before_after.json")

def main():
    if not os.path.exists(JSON_PATH):
        print("JSON results not found yet.")
        return
        
    with open(JSON_PATH) as f:
        data = json.load(f)
        
    pairs = data["pairs_detail"]
    metrics = data["metrics"]
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=200)
    
    # 1. DOVER Fused Score: Baseline vs Recipe Fix across seeds
    ax = axes[0]
    seeds = [1, 2, 3, 4]
    
    # Extract values for Ball 1 and Ball 2
    b1_ctrl = [p["baseline"]["dover_fused"] for p in pairs if p["ball"] == 1]
    b1_mid = [p["recipe"]["dover_fused"] for p in pairs if p["ball"] == 1]
    b2_ctrl = [p["baseline"]["dover_fused"] for p in pairs if p["ball"] == 2]
    b2_mid = [p["recipe"]["dover_fused"] for p in pairs if p["ball"] == 2]
    
    x = np.arange(len(seeds))
    width = 0.35
    
    ax.bar(x - width/2, b1_ctrl, width, label='Held Baseline (B1)', color='#4A90E2', alpha=0.85)
    ax.bar(x + width/2, b1_mid, width, label='Recipe Mid-Fall (B1)', color='#50E3C2', alpha=0.85)
    
    ax.set_title("DOVER Fused Visual Realism (Ball 1)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Seed", fontsize=11)
    ax.set_ylabel("DOVER Score [0, 1]", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Seed {s}" for s in seeds])
    ax.set_ylim(0.4, 0.7)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(fontsize=9)
    
    # 2. Dynamic Degree (Normalized Flow)
    ax = axes[1]
    b1_dd_ctrl = [p["baseline"]["dd_norm"] for p in pairs if p["ball"] == 1]
    b1_dd_mid = [p["recipe"]["dd_norm"] for p in pairs if p["ball"] == 1]
    b2_dd_ctrl = [p["baseline"]["dd_norm"] for p in pairs if p["ball"] == 2]
    b2_dd_mid = [p["recipe"]["dd_norm"] for p in pairs if p["ball"] == 2]
    
    ax.bar(x - width/2, b1_dd_ctrl, width, label='Held Baseline (B1)', color='#E94E77', alpha=0.85)
    ax.bar(x + width/2, b1_dd_mid, width, label='Recipe Mid-Fall (B1)', color='#F5A623', alpha=0.85)
    ax.axhline(0.255, color='black', linestyle=':', linewidth=2, label='Real GAUGE Ref (0.255)')
    
    ax.set_title("VBench Dynamic Degree (Normalized Flow)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Seed", fontsize=11)
    ax.set_ylabel("Normalized Flow (dd_norm)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Seed {s}" for s in seeds])
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(fontsize=9)
    
    # 3. Paired Differences & 95% Confidence Intervals
    ax = axes[2]
    plot_metrics = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_norm"]
    labels = ["DOVER\nFused", "DOVER\nTechnical", "DOVER\nAesthetic", "Dynamic\nDegree (dd_norm)"]
    
    means = [metrics[m]["delta_mean"] for m in plot_metrics]
    errs_low = [means[i] - metrics[plot_metrics[i]]["bootstrap_ci95"][0] for i in range(len(plot_metrics))]
    errs_high = [metrics[plot_metrics[i]]["bootstrap_ci95"][1] - means[i] for i in range(len(plot_metrics))]
    
    y_pos = np.arange(len(plot_metrics))
    ax.errorbar(means, y_pos, xerr=[errs_low, errs_high], fmt='o', color='#2C3E50',
                ecolor='#3498DB', elinewidth=2.5, capsize=6, markersize=8)
    ax.axvline(0, color='red', linestyle='--', alpha=0.7)
    
    ax.set_title("Paired Difference (Recipe - Baseline, 95% CI)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Mean Paired Delta (Δ)", fontsize=11)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.4)
    
    plt.tight_layout()
    out_png = os.path.join(WORK_DIR, "figure_scoreboard_comparison.png")
    plt.savefig(out_png, dpi=200)
    print(f"Plot saved to {out_png}")

if __name__ == "__main__":
    main()
