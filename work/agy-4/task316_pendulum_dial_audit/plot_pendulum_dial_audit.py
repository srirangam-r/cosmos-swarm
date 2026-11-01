#!/usr/bin/env python3
"""
Plotting script for Task 316: Pendulum Speed Dial Audit
Generates publication-ready figure: figure_pendulum_dial_audit.png
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plot_audit(audit_json_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with open(audit_json_path, 'r') as f:
        data = json.load(f)

    rows = data["rows"]
    fits = data["fits"]
    acf_fit = fits["acf_all_20"]
    mp_sel_fit = fits["mp_selected_17"]
    mp_all_fit = fits["mp_all_20"]

    targets = np.array([r["target_s"] for r in rows])
    acf_s = np.array([r["acf_s"] for r in rows])
    mp_s = np.array([r["mp_s"] for r in rows])
    mp_flags = np.array([r["mp_flag"] for r in rows])
    flickers = np.array([r["flicker"] for r in rows])
    gaps = np.array([r["tool_gap"] for r in rows])

    # Plot setup
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 15,
    })

    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=300)
    fig.suptitle("Independent Audit of Cosmos3-Nano Pendulum Speed Dial (Finding #6274)", fontweight='bold')

    # Panel A: Linear Calibration
    ax = axes[0, 0]
    p_grid = np.linspace(0.5, 2.1, 100)
    ax.plot(p_grid, p_grid, 'k--', alpha=0.5, label='Commanded Unity (y = x)')

    # ACF All 20
    ax.scatter(targets, acf_s, color='#0284c7', s=55, alpha=0.85, label=f"ACF (All 20): Slope {acf_fit['slope']:.3f}, R²={acf_fit['r2']:.4f}")
    ax.plot(p_grid, acf_fit['slope'] * p_grid + acf_fit['intercept'], color='#0284c7', lw=1.8)

    # MP Selected 17 (ok) vs 3 flagged
    ok_mask = (mp_flags == 'ok')
    ax.scatter(targets[ok_mask], mp_s[ok_mask], color='#16a34a', marker='s', s=45, alpha=0.85, 
               label=f"MP (17 ok): Slope {mp_sel_fit['slope']:.3f}, R²={mp_sel_fit['r2']:.4f}")
    ax.plot(p_grid, mp_sel_fit['slope'] * p_grid + mp_sel_fit['intercept'], color='#16a34a', lw=1.8, linestyle='-.')

    # Flagged MP
    bad_mask = ~ok_mask
    ax.scatter(targets[bad_mask], mp_s[bad_mask], color='#dc2626', marker='X', s=90, zorder=5, label='MP (3 Flagged: 1 harmonic, 2 low-cycle)')
    
    # Annotate the harmonic clip pend11_P600_s2
    for r in rows:
        if r["clip"] == "dial_pend11_P600_s2" or (r["target_s"] == 0.6 and r["mp_flag"] != "ok"):
            ax.annotate("Harmonic 1/2 lock\n(MP=0.293s, ACF=0.599s)", 
                        xy=(r["target_s"], r["mp_s"]), 
                        xytext=(r["target_s"] + 0.15, r["mp_s"] + 0.15),
                        arrowprops=dict(arrowstyle="->", color='#dc2626', lw=1.5),
                        fontsize=9, fontweight='semibold', color='#dc2626',
                        bbox=dict(boxstyle="round,pad=0.3", fc="#fee2e2", ec="#dc2626", lw=1))

    ax.set_xlabel("Commanded Proxy Period P (s)")
    ax.set_ylabel("Measured Period T (s)")
    ax.set_title("A. Commanded vs. Measured Period Across 20 Clips")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0.5, 2.1)
    ax.set_ylim(0.2, 2.2)

    # Panel B: Relative Error vs Command
    ax = axes[0, 1]
    rel_err_acf = np.abs(acf_s - targets) / targets * 100.0
    rel_err_mp = np.abs(mp_s - targets) / targets * 100.0

    ax.plot(targets, rel_err_acf, 'o', color='#0284c7', label=f"ACF Relative Error (Max {np.max(rel_err_acf):.2f}%)")
    ax.plot(targets[ok_mask], rel_err_mp[ok_mask], 's', color='#16a34a', label=f"MP (17 ok) Error (Max {np.max(rel_err_mp[ok_mask]):.2f}%)")
    ax.plot(targets[bad_mask], rel_err_mp[bad_mask], 'X', color='#dc2626', markersize=9, label=f"MP (3 flagged) Error (Max {np.max(rel_err_mp):.2f}%)")

    ax.axhline(5.0, color='gray', linestyle=':', label='5% Error Threshold')
    ax.axhline(10.0, color='red', linestyle='--', label='10% Error Threshold')

    ax.set_xlabel("Commanded Proxy Period P (s)")
    ax.set_ylabel("Absolute Relative Error (%)")
    ax.set_title("B. Command Relative Error by Period")
    ax.set_yscale('log')
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3, which='both')

    # Panel C: Inter-Reader Tool Gap
    ax = axes[1, 0]
    ax.plot(targets, gaps * 100.0, 'D', color='#7c3aed', markersize=7, alpha=0.85, label='Tool Gap 2|ACF-MP|/(ACF+MP)')
    ax.axhline(10.0, color='red', linestyle='--', lw=1.5, label='Task 290/301 Gate (10% max gap)')

    for r in rows:
        if r["tool_gap"] > 0.10:
            ax.annotate(f"{r['clip']}\nGap: {r['tool_gap']*100:.1f}%", 
                        xy=(r["target_s"], r["tool_gap"] * 100), 
                        xytext=(r["target_s"] + 0.1, r["tool_gap"] * 100 - 15),
                        arrowprops=dict(arrowstyle="->", color='#7c3aed', lw=1.5),
                        fontsize=9, fontweight='semibold', color='#7c3aed',
                        bbox=dict(boxstyle="round,pad=0.3", fc="#f3e8ff", ec="#7c3aed", lw=1))

    ax.set_xlabel("Commanded Proxy Period P (s)")
    ax.set_ylabel("Inter-Reader Relative Gap (%)")
    ax.set_title("C. Inter-Reader Concordance (19/20 < 1.0%, 1 Flagged)")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-2, 80)

    # Panel D: Optical Flicker
    ax = axes[1, 1]
    ax.scatter(targets, flickers, color='#d97706', s=60, alpha=0.85, label=f"Flicker (Median {data['flicker_summary']['median']:.4f})")
    ax.axhline(0.08, color='red', linestyle='--', lw=1.5, label='Flicker Gate Threshold (0.08)')
    ax.axhspan(0.0, 0.01, color='green', alpha=0.1, label='Clean / Zero Flicker Band (<0.01)')

    ax.set_xlabel("Commanded Proxy Period P (s)")
    ax.set_ylabel("Optical Flicker (mean abs frame diff)")
    ax.set_title("D. Optical Flicker Distribution Across the Dial")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0.0, 0.09)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plot_path = os.path.join(output_dir, "figure_pendulum_dial_audit.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Plot saved to {plot_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: plot_pendulum_dial_audit.py <audit_results.json> <output_dir>")
        sys.exit(1)
    plot_audit(sys.argv[1], sys.argv[2])
