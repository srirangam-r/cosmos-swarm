#!/usr/bin/env python3
"""
Generate 4-panel publication figure for Task 233 review of Finding #4569.
Outputs: plots/figure_pendulum_length_audit.png
"""

import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def main():
    base_dir = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task233_pendulum_length_review"
    res_path = os.path.join(base_dir, "audit_results.json")
    author_res_path = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/rahul-api-2/t228/results.json"
    author_posthoc_path = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/rahul-api-2/t228/posthoc.json"

    with open(res_path) as f:
        AUDIT = json.load(f)
    with open(author_res_path) as f:
        RES = json.load(f)
    with open(author_posthoc_path) as f:
        POSTHOC = json.load(f)

    rows = RES["rows"]

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=200)

    # -------------------------------------------------------------
    # Panel A: Gate Pass Rates across Arms (Collapse of G4 Tracking in L50)
    # -------------------------------------------------------------
    ax_a = axes[0, 0]
    gates = ["G1 (Pivot Res)", "G2 (Pivot Pos)", "G3 (L Curve)", "G4 (Tracked >=60%)", "G5 (R2 >= 0.8)", "All PASS"]
    arms = ["orig", "L70", "L50"]
    colors = {"orig": "#2b5c8f", "L70": "#d95f02", "L50": "#7570b3"}
    arm_labels = {"orig": "Orig (L=1.0)", "L70": "L70 (L=0.7)", "L50": "L50 (L=0.5)"}

    x = np.arange(len(gates))
    width = 0.25

    for idx, arm in enumerate(arms):
        arm_rows = [v for v in rows.values() if v["arm"] == arm]
        n = len(arm_rows)
        counts = [
            sum(v["G1"] for v in arm_rows) / n * 100,
            sum(v["G2"] for v in arm_rows) / n * 100,
            sum(v["G3"] for v in arm_rows) / n * 100,
            sum(v["G4"] for v in arm_rows) / n * 100,
            sum(v["G5"] for v in arm_rows) / n * 100,
            sum(v["PASS"] for v in arm_rows) / n * 100,
        ]
        rects = ax_a.bar(x + (idx - 1) * width, counts, width, label=arm_labels[arm], color=colors[arm], alpha=0.85, edgecolor="black")
        for rect in rects:
            h = rect.get_height()
            if h > 0:
                ax_a.text(rect.get_x() + rect.get_width() / 2.0, h + 1.5, f"{int(round(h/10))}/10", ha="center", va="bottom", fontsize=8)

    ax_a.set_ylabel("Pass Rate (%)", fontsize=11, fontweight="bold")
    ax_a.set_title("A: Gate Survival & Tracking Breakdown\n(L50 G4 Tracking Collapse: 8/10 -> 1/10, McNemar p = 0.0156)", fontsize=11, fontweight="bold")
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(gates, rotation=20, ha="right", fontsize=9)
    ax_a.set_ylim(0, 115)
    ax_a.legend(loc="upper right", frameon=True)
    ax_a.grid(True, linestyle="--", alpha=0.6)

    # -------------------------------------------------------------
    # Panel B: Rod Length Dynamics (Input Target vs Median Tracked)
    # -------------------------------------------------------------
    ax_b = axes[0, 1]
    input_lens = [111.76, 81.50, 55.33]
    tracked_medians = [
        AUDIT["rod_length_dynamics"]["orig"]["median_tracked_all"],
        AUDIT["rod_length_dynamics"]["L70"]["median_tracked_all"],
        AUDIT["rod_length_dynamics"]["L50"]["median_tracked_all"],
    ]

    x_b = np.arange(3)
    bar_w = 0.35

    ax_b.bar(x_b - bar_w/2, input_lens, bar_w, label="Input Tan Rod (Target)", color="#666666", alpha=0.7, edgecolor="black")
    b2 = ax_b.bar(x_b + bar_w/2, tracked_medians, bar_w, label="Tracked Median Rod", color=[colors[a] for a in arms], alpha=0.85, edgecolor="black")

    for i, rect in enumerate(b2):
        h = rect.get_height()
        inp = input_lens[i]
        diff_pct = (h - inp) / inp * 100.0
        ax_b.text(rect.get_x() + rect.get_width() / 2.0, h + 2.5, f"{h:.1f} px\n({diff_pct:+.1f}%)", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax_b.axhline(111.76, color="#2b5c8f", linestyle=":", linewidth=1.5, label="Orig Canonical Target (111.8 px)")
    ax_b.set_ylabel("Rod Length (pixels)", fontsize=11, fontweight="bold")
    ax_b.set_title("B: Rod Length Dynamics & Canonical Regrowth\n(Model Rebuilds Shorter Rods Toward Original Prior)", fontsize=11, fontweight="bold")
    ax_b.set_xticks(x_b)
    ax_b.set_xticklabels(["Orig (1.0 L)", "L70 (0.7 L)", "L50 (0.5 L)"], fontsize=10)
    ax_b.set_ylim(0, 145)
    ax_b.legend(loc="upper left", frameon=True)
    ax_b.grid(True, linestyle="--", alpha=0.6)

    # -------------------------------------------------------------
    # Panel C: Measured Period vs Physical Law Prediction
    # -------------------------------------------------------------
    ax_c = axes[1, 0]
    fracs = [1.0, 0.7, 0.5]
    t_orig_gm = AUDIT["period_ratios_g5"]["orig"]["gm"]

    # Theoretical curve T(L) = T_orig * sqrt(f)
    f_dense = np.linspace(0.4, 1.1, 100)
    t_law_dense = t_orig_gm * np.sqrt(f_dense)
    ax_c.plot(f_dense, t_law_dense, color="black", linestyle="--", linewidth=2.0, label="Physics Law ($T \\propto \\sqrt{L}$)")
    ax_c.axhline(t_orig_gm, color="gray", linestyle=":", linewidth=1.5, label=f"Fixed Rhythm ($T \\approx {t_orig_gm:.2f}$ s)")

    # Plot empirical points
    for arm in arms:
        v_arm = [v for v in rows.values() if v["arm"] == arm and v["G5"]]
        t_vals = [v["T"] for v in v_arm]
        frac = 1.0 if arm == "orig" else (0.7 if arm == "L70" else 0.5)
        # Jitter x slightly
        x_jitter = np.random.default_rng(10).normal(frac, 0.012, size=len(t_vals))
        ax_c.scatter(x_jitter, t_vals, color=colors[arm], s=65, alpha=0.85, edgecolors="black", zorder=4, label=f"{arm_labels[arm]} (R2>=0.8, n={len(t_vals)})")

    # Add GM markers with bootstrap CIs
    for arm, frac in [("L70", 0.7), ("L50", 0.5)]:
        p_info = AUDIT["period_ratios_g5"][arm]
        gm_val = p_info["gm"]
        ci = [p_info["ratio_vs_orig"] * t_orig_gm for _ in [0]] # approx
        ax_c.scatter([frac], [gm_val], color=colors[arm], marker="D", s=110, edgecolor="black", zorder=5)

    ax_c.set_xlabel("Rod Length Fraction ($L / L_{orig}$)", fontsize=11, fontweight="bold")
    ax_c.set_ylabel("Measured Period $T$ (seconds)", fontsize=11, fontweight="bold")
    ax_c.set_title("C: Period Sensitivity on $R^2 \\geq 0.8$ Clips\n(L70 Ratio = 0.956 [0.61, 1.51]; L50 Ratio = 1.316 [0.98, 1.76])", fontsize=11, fontweight="bold")
    ax_c.set_xlim(0.4, 1.1)
    ax_c.set_ylim(0.8, 3.4)
    ax_c.legend(loc="upper left", frameon=True, fontsize=9)
    ax_c.grid(True, linestyle="--", alpha=0.6)

    # -------------------------------------------------------------
    # Panel D: Same-Seed Period Trajectories (Carryover Across Arms)
    # -------------------------------------------------------------
    ax_d = axes[1, 1]
    # Highlight seeds 21, 26, 28
    key_seeds = [21, 26, 28]
    seed_markers = {21: "o", 26: "s", 28: "^"}

    for s in key_seeds:
        s_rows = {v["arm"]: v for v in rows.values() if v["seed"] == s}
        # Check arms present with valid T
        pts_x = []
        pts_y = []
        for arm in ["orig", "L70", "L50"]:
            if arm in s_rows and s_rows[arm]["r2"] is not None and s_rows[arm]["r2"] >= 0.8:
                frac = 1.0 if arm == "orig" else (0.7 if arm == "L70" else 0.5)
                pts_x.append(frac)
                pts_y.append(s_rows[arm]["T"])

        if len(pts_x) >= 2:
            ax_d.plot(pts_x, pts_y, marker=seed_markers[s], markersize=9, linewidth=2.0, label=f"Seed {s} Trajectory", alpha=0.9)

    ax_d.set_xlabel("Rod Length Fraction ($L / L_{orig}$)", fontsize=11, fontweight="bold")
    ax_d.set_ylabel("Measured Period $T$ (seconds)", fontsize=11, fontweight="bold")
    ax_d.set_title("D: Same-Seed Period Persistence Across Lengths\n(Seeds 26 & 28 Hold Fixed Periods: 2.58s & 1.18s)", fontsize=11, fontweight="bold")
    ax_d.set_xlim(0.4, 1.1)
    ax_d.set_ylim(0.8, 3.4)
    ax_d.legend(loc="upper right", frameon=True)
    ax_d.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    plot_path = os.path.join(base_dir, "plots/figure_pendulum_length_audit.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Plot saved to: {plot_path}")

if __name__ == "__main__":
    main()
