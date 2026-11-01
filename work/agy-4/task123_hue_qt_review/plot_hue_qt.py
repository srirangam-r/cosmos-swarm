#!/usr/bin/env python3
"""
work/agy-4/task123_hue_qt_review/plot_hue_qt.py:
Plot generation for Independent Replication of Finding #2577
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

DATA_JSON = Path(__file__).resolve().parent / "task123_review_results.json"
PLOTS_DIR = Path(__file__).resolve().parent / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def plot_category_contrasts(data):
    cats = [
        "overall",
        "Physical Laws",
        "Visual Integrity",
        "Geometric Reasoning",
        "Semantic Alignment",
    ]
    labels = ["Overall", "Physical", "Visual", "Geometric", "Semantic"]

    f_means = [data["category_contrasts"][c]["F_mean"] for c in cats]
    qt_means = [data["category_contrasts"][c]["QT_mean"] for c in cats]
    real_refs = [data["category_contrasts"][c]["Real_ref"] for c in cats]
    diffs = [data["category_contrasts"][c]["diff_mean"] for c in cats]
    ses = [data["category_contrasts"][c]["se"] for c in cats]

    x = np.arange(len(cats))
    width = 0.25

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1.4, 1.0]})

    # Panel 1: Absolute Scores
    b1 = ax1.bar(x - width, f_means, width, label="Base F (Unmodified)", color="#1f77b4", alpha=0.9, edgecolor="black")
    b2 = ax1.bar(x, qt_means, width, label="Prompt QT (Timed Settle)", color="#2ca02c", alpha=0.9, edgecolor="black")
    b3 = ax1.bar(x + width, real_refs, width, label="Real GAUGE Ref", color="#d62728", alpha=0.9, edgecolor="black")

    ax1.set_ylabel("HUE Judge Score (P(Yes))", fontsize=11, fontweight="bold")
    ax1.set_title("HUE Plausibility Scores: Base vs QT vs Real Video", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax1.set_ylim(0, 1.05)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", frameon=True)

    # Highlight Real matching QT on Overall and Physical
    ax1.annotate("Real ≈ QT\n(0.584 vs 0.585)", xy=(0, 0.585), xytext=(0, 0.72),
                 arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=6),
                 fontsize=9, ha="center", fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.6))

    # Panel 2: Ground-Truth Error (|Score - Score(Real)|)
    err_f = [data["distance_to_real"][c]["dist_F"] for c in cats]
    err_qt = [data["distance_to_real"][c]["dist_QT"] for c in cats]

    b_ef = ax2.bar(x - width/2, err_f, width, label="Base F Error (|F - Real|)", color="#aec7e8", edgecolor="black")
    b_eq = ax2.bar(x + width/2, err_qt, width, label="QT Error (|QT - Real|)", color="#98df8a", edgecolor="black")

    ax2.set_ylabel("Absolute Distance from Real Ground Truth", fontsize=11, fontweight="bold")
    ax2.set_title("Ground-Truth Accuracy: Closeness to Real Video", fontsize=12, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", frameon=True)

    # Annotate 76x and 5.7x
    ax2.annotate("76x Closer\nto Real", xy=(0 + width/2, err_qt[0]), xytext=(0 + width/2, 0.07),
                 arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=6),
                 fontsize=8.5, ha="center", fontweight="bold")
    ax2.annotate("5.7x Closer\nto Real", xy=(1 + width/2, err_qt[1]), xytext=(1 + width/2, 0.09),
                 arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=6),
                 fontsize=8.5, ha="center", fontweight="bold")

    plt.tight_layout()
    out_path = PLOTS_DIR / "figure_category_profiles.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[plot] Saved category profiles to {out_path}")


def plot_question_distance(data):
    q_data = data["question_contrasts"]
    qids = list(range(1, 14))

    labels = [f"Q{i}: {q_data[f'Q{i}']['category'][:4]} - {q_data[f'Q{i}']['text'][:35]}..." for i in qids]
    err_f = [q_data[f"Q{i}"]["dist_F"] for i in qids]
    err_qt = [q_data[f"Q{i}"]["dist_QT"] for i in qids]

    y = np.arange(len(qids))
    height = 0.35

    fig, ax = plt.subplots(figsize=(12, 7.5))

    ax.barh(y - height/2, err_f, height, label="Base F Distance to Real (|F - Real|)", color="#d62728", alpha=0.85, edgecolor="black")
    ax.barh(y + height/2, err_qt, height, label="Prompt QT Distance to Real (|QT - Real|)", color="#2ca02c", alpha=0.85, edgecolor="black")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()  # Q1 at top
    ax.set_xlabel("Absolute Error vs Real Ground-Truth Continuation Video (|Score - Score(Real)|)", fontsize=11, fontweight="bold")
    ax.set_title("Question-by-Question Divergence from Real Reality (10/13 Questions Closer in QT)", fontsize=12, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    ax.legend(loc="lower right", frameon=True, fontsize=10)

    # Annotate key questions
    for i, qid in enumerate(qids):
        ratio = q_data[f"Q{qid}"]["error_ratio_F_over_QT"]
        closer = q_data[f"Q{qid}"]["QT_closer"]
        if closer and ratio >= 2.0:
            ax.text(max(err_f[i], err_qt[i]) + 0.01, i, f"{ratio:.1f}x closer", va="center", fontsize=8.5, fontweight="bold", color="#1b7837")

    plt.tight_layout()
    out_path = PLOTS_DIR / "figure_question_distance_to_real.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[plot] Saved question distance-to-real to {out_path}")


def main():
    with open(DATA_JSON) as f:
        data = json.load(f)
    plot_category_contrasts(data)
    plot_question_distance(data)


if __name__ == "__main__":
    main()
