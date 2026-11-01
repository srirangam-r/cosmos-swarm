#!/usr/bin/env python3
"""
Generate publication-quality figures for Task 48:
Denoising-loss Arrow-of-Time probe in Cosmos3-Nano.
"""
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def generate_plots():
    results_path = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task48_arrow_of_time/task48_analysis_results.json"
    with open(results_path) as fp:
        res = json.load(fp)

    out_dir = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task48_arrow_of_time/plots"
    os.makedirs(out_dir, exist_ok=True)

    # 1. Figure 1: Arm Comparisons (Real vs Cosmos Undamped vs Cosmos Settling)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=300)

    # Panel A: Mean Paired Delta (Reverse - Forward)
    arms = ["Real GAUGE\n(Damped, n=6)", "Cosmos Base F\n(Undamped, n=4)", "Cosmos Timed\n(QT/RECT, n=2)"]
    means = [
        res["real_damped"]["mean_delta_rev_minus_fwd"],
        res["cosmos_undamped"]["mean_delta_rev_minus_fwd"],
        res["cosmos_settling"]["mean_delta_rev_minus_fwd"]
    ]
    errors = [
        res["real_damped"]["se_delta"],
        res["cosmos_undamped"]["se_delta"],
        res["cosmos_settling"]["se_delta"]
    ]
    colors = ["#2b5c8f", "#d95f02", "#7570b3"]

    bars = axes[0].bar(arms, means, yerr=errors, capsize=5, color=colors, alpha=0.85, edgecolor='black', linewidth=1.2)
    axes[0].axhline(0, color='gray', linestyle='--', linewidth=1)
    axes[0].set_ylabel(r"Paired RF Loss Delta ($\Delta_{\mathrm{rev} - \mathrm{fwd}}$)", fontsize=11, fontweight='bold')
    axes[0].set_title("(a) Arrow-of-Time Preference\n(Loss(Reverse) - Loss(Forward))", fontsize=12, fontweight='bold')
    axes[0].grid(axis='y', linestyle=':', alpha=0.6)

    # Add text labels on bars
    for bar in bars:
        h = bar.get_height()
        va = 'bottom' if h >= 0 else 'top'
        axes[0].annotate(f"{h:+.4f}",
                         xy=(bar.get_x() + bar.get_width() / 2, h),
                         xytext=(0, 3 if h >= 0 else -12),
                         textcoords="offset points",
                         ha='center', va=va, fontsize=10, fontweight='bold')

    # Panel B: Delta by Noise Level (sigma)
    sigmas = [0.1, 0.3, 0.5, 0.7, 0.9]
    real_by_sigma = [res["real_damped"]["by_sigma_delta"][str(s)] for s in sigmas]
    cosmos_by_sigma = [res["cosmos_undamped"]["by_sigma_delta"][str(s)] for s in sigmas]
    settle_by_sigma = [res["cosmos_settling"]["by_sigma_delta"][str(s)] for s in sigmas]

    axes[1].plot(sigmas, real_by_sigma, 'o-', color="#2b5c8f", label="Real GAUGE Drops (Damped)", linewidth=2.5, markersize=7)
    axes[1].plot(sigmas, cosmos_by_sigma, 's--', color="#d95f02", label="Cosmos Base F (Undamped)", linewidth=2.5, markersize=7)
    axes[1].plot(sigmas, settle_by_sigma, '^:', color="#7570b3", label="Cosmos Timed (QT/RECT)", linewidth=2.5, markersize=7)
    axes[1].axhline(0, color='gray', linestyle='--', linewidth=1)
    axes[1].set_xlabel(r"Diffusion Noise Scale $\sigma$", fontsize=11, fontweight='bold')
    axes[1].set_ylabel(r"$\Delta_{\mathrm{rev} - \mathrm{fwd}}$ by Noise Level", fontsize=11, fontweight='bold')
    axes[1].set_title("(b) Arrow-of-Time Asymmetry vs. Noise $\sigma$", fontsize=12, fontweight='bold')
    axes[1].legend(frameon=True, fontsize=9)
    axes[1].grid(True, linestyle=':', alpha=0.6)

    # Panel C: The Static Attractor Basin (Freeze First vs Forward)
    freeze_means = [
        res["real_damped"]["freeze_minus_fwd_delta"],
        res["cosmos_undamped"]["freeze_minus_fwd_delta"],
        res["cosmos_settling"]["freeze_minus_fwd_delta"]
    ]
    bars_frz = axes[2].bar(arms, freeze_means, color=["#1b9e77", "#d95f02", "#7570b3"], alpha=0.85, edgecolor='black', linewidth=1.2)
    axes[2].set_ylabel(r"$\Delta_{\mathrm{freeze} - \mathrm{fwd}}$ (Loss Difference)", fontsize=11, fontweight='bold')
    axes[2].set_title("(c) Static Attractor Basin\n(Loss(Freeze) - Loss(Forward))", fontsize=12, fontweight='bold')
    axes[2].grid(axis='y', linestyle=':', alpha=0.6)

    for bar in bars_frz:
        h = bar.get_height()
        axes[2].annotate(f"{h:+.3f}\n(-{abs(h)/0.25*100:.0f}%)",
                         xy=(bar.get_x() + bar.get_width() / 2, h),
                         xytext=(0, -22),
                         textcoords="offset points",
                         ha='center', va='top', fontsize=9, fontweight='bold')

    plt.tight_layout()
    fig_path = os.path.join(out_dir, "figure_task48_arrow_of_time.png")
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved {fig_path}")

    # 2. Figure 2: Latent Temporal Progression (Impact-Localized Asymmetry)
    real_b1 = json.load(open("/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task48_arrow_of_time/out/probe_real_ball1.json"))
    base_s3 = json.load(open("/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task48_arrow_of_time/out/probe_cosmos_baseF_b1_s3.json"))

    pfd_real = real_b1["paired"]["reverse_minus_forward"]["mean_delta_per_frame"]
    pfd_base = base_s3["paired"]["reverse_minus_forward"]["mean_delta_per_frame"]

    frames = np.arange(len(pfd_real))

    fig2, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(frames, pfd_real, 'o-', color="#2b5c8f", label="Real GAUGE Ball 1 (Damped Physics)", linewidth=2.5, markersize=6)
    ax.plot(frames, pfd_base, 's--', color="#d95f02", label="Cosmos Base F Ball 1 s3 (Undamped)", linewidth=2.5, markersize=6)
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax.set_xlabel("Latent Frame Index (Temporal Progression, 0 to 22)", fontsize=11, fontweight='bold')
    ax.set_ylabel(r"$\Delta_{\mathrm{rev} - \mathrm{fwd}}$ (Latent Frame Delta)", fontsize=11, fontweight='bold')
    ax.set_title("Impact-Localized Dissipation: Reversal Loss Asymmetry Across Latent Frames", fontsize=12, fontweight='bold')

    # Annotate impact points on real video
    ax.annotate("Bounce Impacts\n(Entropy Spikes)", xy=(9, 0.0661), xytext=(6, 0.085),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                fontweight='bold', fontsize=9)

    ax.legend(frameon=True, fontsize=10, loc="upper left")
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    fig2_path = os.path.join(out_dir, "figure_task48_latent_temporal.png")
    plt.savefig(fig2_path)
    plt.close()
    print(f"Saved {fig2_path}")

if __name__ == "__main__":
    generate_plots()
