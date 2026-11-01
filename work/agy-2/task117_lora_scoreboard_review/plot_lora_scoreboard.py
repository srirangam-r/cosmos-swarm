#!/usr/bin/env python3
"""
Publication-Quality Visualizations for Task 117 Replication of Finding #2562.

Author: agy-2
Task: 117
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.join(HERE, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

def plot_contrasts(results):
    """Forest plot of pairwise contrasts against non-inferiority margins."""
    contrasts = [
        ("baseL - base (A/A box null)", "baseL - base (A/A null)"),
        ("loraC - base (no-decay vs base)", "LoRA C - base (no-decay)"),
        ("loraA - base (real-g candidate vs base)", "LoRA A - base (real-g)"),
        ("loraB - base (wrong-g control vs base)", "LoRA B - base (wrong-g)"),
        ("loraA - loraB (g difference on same box)", "LoRA A - LoRA B (g diff)"),
        ("loraA - baseL (real-g vs same-box base)", "LoRA A - baseL (same box)")
    ]

    metrics = [
        ("dover_fused", "DOVER Fused Score", 0.02, (-0.14, 0.04)),
        ("dd_norm", "VBench Dynamic Degree (Norm)", 1.1835, (-8.0, 2.0)),
        ("overall", "HUE Plausibility (Overall)", 0.03, (-0.07, 0.02)),
        ("Physical Laws", "HUE Physical Laws", 0.04, (-0.08, 0.03))
    ]

    fig, axes = plt.subplots(1, 4, figsize=(18, 5.5), sharey=True)
    y_pos = np.arange(len(contrasts))

    overall_data = results["pairwise_contrasts_overall"]

    for ax, (m_key, m_title, margin, x_lim) in zip(axes, metrics):
        means = []
        ci90_errs_low = []
        ci90_errs_high = []
        ci95_errs_low = []
        ci95_errs_high = []
        colors = []

        for c_full, _ in contrasts:
            c_data = overall_data[c_full][m_key]
            m = c_data["mean"]
            ci90 = c_data["ci90"]
            ci95 = c_data["ci95"]

            means.append(m)
            ci90_errs_low.append(m - ci90[0])
            ci90_errs_high.append(ci90[1] - m)
            ci95_errs_low.append(m - ci95[0])
            ci95_errs_high.append(ci95[1] - m)

            # Color coding by verdict
            if c_data["verdict"] == "REGRESSION":
                colors.append("#d9534f")  # Red
            elif c_data["verdict"] == "significant drop":
                colors.append("#f0ad4e")  # Orange
            elif c_data["verdict"] == "non-inferior":
                colors.append("#5cb85c")  # Green
            else:
                colors.append("#337ab7")  # Blue

        # Plot 95% whiskers (thin)
        ax.errorbar(means, y_pos, xerr=[ci95_errs_low, ci95_errs_high],
                    fmt='none', ecolor='#888888', elinewidth=1.5, capsize=3, zorder=2)
        # Plot 90% error bars (thick)
        ax.errorbar(means, y_pos, xerr=[ci90_errs_low, ci90_errs_high],
                    fmt='none', ecolor='#222222', elinewidth=3.0, capsize=0, zorder=3)
        # Plot markers
        ax.scatter(means, y_pos, color=colors, s=70, edgecolor='black', zorder=4)

        # Zero reference line
        ax.axvline(0, color='gray', linestyle='-', linewidth=1.0, alpha=0.7)
        # Non-inferiority margin line (-margin)
        ax.axvline(-margin, color='crimson', linestyle='--', linewidth=1.8, label=f"NI Margin (-{margin})")

        ax.set_title(m_title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Paired Difference Δ", fontsize=10)
        ax.set_xlim(x_lim)
        ax.grid(axis='x', linestyle=':', alpha=0.6)

    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels([c_label for _, c_label in contrasts], fontsize=11, fontweight="medium")
    axes[0].invert_yaxis()  # Top down
    axes[0].legend(loc="lower left", framealpha=0.9, fontsize=9)

    plt.suptitle("Finding #2562 Replication: 5-Arm Task 24 LoRA Contrasts & Non-Inferiority Audit (n=16 Prompts)",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out_path = os.path.join(PLOTS_DIR, "figure_scoreboard_contrasts.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

def plot_domain_breakdown(results):
    """Bar chart comparing Physics (n=10) vs Robot (n=6) domain responses across arms."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    arms = ["base", "baseL", "loraA", "loraB", "loraC"]
    arm_labels = ["Base\n(Box 1)", "BaseL\n(Box 2)", "LoRA A\n(Real g)", "LoRA B\n(Wrong g)", "LoRA C\n(No decay)"]
    x = np.arange(len(arms))
    w = 0.35

    arm_data = results["arm_grand_means"]

    # 1. DOVER Fused
    ax = axes[0]
    p_dover = [arm_data[a]["physics"]["dover_fused"]["mean"] for a in arms]
    r_dover = [arm_data[a]["robot"]["dover_fused"]["mean"] for a in arms]
    p_se = [arm_data[a]["physics"]["dover_fused"]["se"] for a in arms]
    r_se = [arm_data[a]["robot"]["dover_fused"]["se"] for a in arms]

    ax.bar(x - w/2, p_dover, w, yerr=p_se, capsize=3, label="Physics (n=10)", color="#2b5c8f", alpha=0.85)
    ax.bar(x + w/2, r_dover, w, yerr=r_se, capsize=3, label="Robot (n=6)", color="#d95f02", alpha=0.85)
    ax.set_title("DOVER Fused Visual Quality", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(arm_labels, fontsize=10)
    ax.set_ylim(0.45, 0.65)
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.legend(framealpha=0.9)

    # 2. Dynamic Degree
    ax = axes[1]
    p_dd = [arm_data[a]["physics"]["dd_norm"]["mean"] for a in arms]
    r_dd = [arm_data[a]["robot"]["dd_norm"]["mean"] for a in arms]
    p_dd_se = [arm_data[a]["physics"]["dd_norm"]["se"] for a in arms]
    r_dd_se = [arm_data[a]["robot"]["dd_norm"]["se"] for a in arms]

    ax.bar(x - w/2, p_dd, w, yerr=p_dd_se, capsize=3, label="Physics (n=10)", color="#2b5c8f", alpha=0.85)
    ax.bar(x + w/2, r_dd, w, yerr=r_dd_se, capsize=3, label="Robot (n=6)", color="#d95f02", alpha=0.85)
    ax.set_title("VBench Dynamic Degree (Norm)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Normalized Optical Flow", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(arm_labels, fontsize=10)
    ax.set_ylim(0, 16)
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.legend(framealpha=0.9)

    # 3. HUE Physical Laws
    ax = axes[2]
    p_phy = [arm_data[a]["physics"]["Physical Laws"]["mean"] for a in arms]
    r_phy = [arm_data[a]["robot"]["Physical Laws"]["mean"] for a in arms]
    p_phy_se = [arm_data[a]["physics"]["Physical Laws"]["se"] for a in arms]
    r_phy_se = [arm_data[a]["robot"]["Physical Laws"]["se"] for a in arms]

    ax.bar(x - w/2, p_phy, w, yerr=p_phy_se, capsize=3, label="Physics (n=10)", color="#2b5c8f", alpha=0.85)
    ax.bar(x + w/2, r_phy, w, yerr=r_phy_se, capsize=3, label="Robot (n=6)", color="#d95f02", alpha=0.85)
    ax.set_title("HUE Physical Laws Plausibility", fontsize=12, fontweight="bold")
    ax.set_ylabel("Probability P(Yes)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(arm_labels, fontsize=10)
    ax.set_ylim(0.40, 0.70)
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.legend(framealpha=0.9)

    plt.suptitle("Domain Disparity: Catastrophic Robot Motion Collapse vs Physics Plausibility Degradation",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out_path = os.path.join(PLOTS_DIR, "figure_domain_breakdown.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

def plot_dover_components(results):
    """Component decomposition: Technical vs Aesthetic DOVER scores."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    arms = ["base", "baseL", "loraA", "loraB", "loraC"]
    arm_labels = ["Base", "BaseL", "LoRA A", "LoRA B", "LoRA C"]
    x = np.arange(len(arms))

    arm_data = results["arm_grand_means"]

    # Technical
    ax = axes[0]
    tech = [arm_data[a]["overall"]["dover_technical"]["mean"] for a in arms]
    tech_se = [arm_data[a]["overall"]["dover_technical"]["se"] for a in arms]
    ax.bar(x, tech, yerr=tech_se, capsize=4, color="#4575b4", alpha=0.85, width=0.5)
    ax.set_title("DOVER Technical Quality\n(Artifacts, Blur, Noise)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(arm_labels, fontsize=10)
    ax.grid(axis='y', linestyle=':', alpha=0.6)

    # Aesthetic
    ax = axes[1]
    aes = [arm_data[a]["overall"]["dover_aesthetic"]["mean"] for a in arms]
    aes_se = [arm_data[a]["overall"]["dover_aesthetic"]["se"] for a in arms]
    ax.bar(x, aes, yerr=aes_se, capsize=4, color="#d73027", alpha=0.85, width=0.5)
    ax.set_title("DOVER Aesthetic Quality\n(Lighting, Composition, Realism)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(arm_labels, fontsize=10)
    ax.grid(axis='y', linestyle=':', alpha=0.6)

    plt.suptitle("DOVER Quality Component Decomposition Across Task 24 LoRA Arms",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out_path = os.path.join(PLOTS_DIR, "figure_dover_components.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

def main():
    res_path = os.path.join(HERE, "task117_replication_results.json")
    if not os.path.exists(res_path):
        raise FileNotFoundError(f"Missing {res_path}")
    with open(res_path) as f:
        results = json.load(f)

    plot_contrasts(results)
    plot_domain_breakdown(results)
    plot_dover_components(results)

if __name__ == "__main__":
    main()
