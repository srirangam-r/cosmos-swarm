#!/usr/bin/env python3
"""
Plot HUE judge window split and distance-to-real metrics.
"""
import json
import os
import matplotlib.pyplot as plt
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(D, "task118_review_results.json")) as f:
    data = json.load(f)

fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=150)

# Panel 1: Early vs Late Window Scores
ax = axes[0]
metrics = ["overall", "Physical", "Q1 (arm)", "Q5 (release)", "Q6 (rest)"]
m_keys = ["overall", "Physical Laws", "Q1", "Q5", "Q6"]

x = np.arange(len(metrics))
width = 0.25

f_early = [data["early"]["metrics"][k]["mean_F"] for k in m_keys]
qt_early = [data["early"]["metrics"][k]["mean_QT"] for k in m_keys]
real_early = [data["early"]["real_scores"][k] for k in m_keys]

f_late = [data["late"]["metrics"][k]["mean_F"] for k in m_keys]
qt_late = [data["late"]["metrics"][k]["mean_QT"] for k in m_keys]
real_late = [data["late"]["real_scores"][k] for k in m_keys]

ax.bar(x - width, f_late, width, label="F (Base Continuous)", color="#d95f02", alpha=0.85)
ax.bar(x, qt_late, width, label="QT (Prompt-Timed Settle)", color="#1b9e77", alpha=0.85)
ax.bar(x + width, real_late, width, label="Real GAUGE Continuation", color="#7570b3", alpha=0.85)

ax.set_ylabel("HUE Judge Score P(Yes)")
ax.set_title("Late Window (f46–92, Settled Tail): Scores vs Real Video")
ax.set_xticks(x)
ax.set_xticklabels(metrics, rotation=15, ha="right")
ax.legend(loc="upper right", frameon=True)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_ylim(0, 1.05)

# Panel 2: Distance to Real Reference |Score(Arm) - Score(Real)|
ax2 = axes[1]
dist_f_late = [data["late"]["distance_to_real"][k]["dist_F"] for k in m_keys]
dist_qt_late = [data["late"]["distance_to_real"][k]["dist_QT"] for k in m_keys]

width2 = 0.35
ax2.bar(x - width2/2, dist_f_late, width2, label="|F - Real|", color="#d95f02", alpha=0.85)
ax2.bar(x + width2/2, dist_qt_late, width2, label="|QT - Real| (Closer)", color="#1b9e77", alpha=0.85)

ax2.set_ylabel("Absolute Error from Real Ground Truth |Score - Real|")
ax2.set_title("Late Window Ground-Truth Error: QT is 3x–8x Closer to Real")
ax2.set_xticks(x)
ax2.set_xticklabels(metrics, rotation=15, ha="right")
ax2.legend(loc="upper right", frameon=True)
ax2.grid(axis="y", linestyle="--", alpha=0.5)
ax2.set_ylim(0, 0.65)

# Annotate ratios
for i in range(len(metrics)):
    k = m_keys[i]
    ratio = data["late"]["distance_to_real"][k]["ratio_F_over_QT"]
    if ratio > 1.2:
        ax2.annotate(f"{ratio:.1f}x closer",
                     xy=(x[i] + width2/2, dist_qt_late[i] + 0.02),
                     ha="center", fontsize=9, fontweight="bold", color="#1b9e77")

plt.tight_layout()
out_plot = os.path.join(D, "plots/figure_hue_window_audit.png")
plt.savefig(out_plot)
print(f"Plot saved to {out_plot}")
