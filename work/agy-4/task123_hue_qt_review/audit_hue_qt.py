#!/usr/bin/env python3
"""
work/agy-4/task123_hue_qt_review/audit_hue_qt.py:
Independent Statistical Replication and Ground-Truth Audit of Finding #2577

Audits raw model predictions from Qwen3-VL-2B (tools/hue_judge) on the prompt-timed
settle clause (QT vs base F, stillness control QS, and real GAUGE continuation video):
1. Independent JSON parsing and pairing across all 8 matched pairs and 3 QS controls.
2. Independent calculation of category means, SEs, paired deltas, analytical t-tests, and bootstrap CIs.
3. Ground-truth distance-to-real metric |judge(gen) - judge(real)| across all categories and 13 questions.
4. Exploratory question-exclusion sensitivity analysis (dropping Q1, Q2, Q5).
5. Comprehensive export to task123_review_results.json.
"""

import json
import os
import re
import sys
from pathlib import Path
import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPO_ROOT / "work" / "ro-1" / "hue_qt" / "res.json"
OUT_JSON = Path(__file__).resolve().parent / "task123_review_results.json"


def load_raw_predictions(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    with open(path) as f:
        data = json.load(f)
    return data["results"]


def parse_clip_name(stem):
    # e.g. ball_F_ball1_fps24_93f_s1 -> arm='F', ball='ball1', seed=1
    # or cause_QT_ball1_fps24_93f_s1
    # or cause5_F_ball1_fps24_93f_s3
    # or cause5_QS_ball1_fps24_93f_s3
    # or cause6_QT_ball2_fps24_93f_s1
    m = re.search(r"_(F|QT|QS)_(ball\d)_fps24_93f_s(\d)", stem)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    if "real_ball1_dd32_93f" in stem:
        return "real", "ball1", 0
    return None


def bootstrap_ci_paired(diffs, n_boot=10000, alpha=0.10, seed=42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    indices = rng.integers(0, n, size=(n_boot, n))
    boot_means = np.mean(diffs[indices], axis=1)
    lb = np.percentile(boot_means, (alpha / 2.0) * 100)
    ub = np.percentile(boot_means, (1.0 - alpha / 2.0) * 100)
    return float(lb), float(ub)


def run_audit():
    raw_results = load_raw_predictions(DATA_PATH)
    print(f"[audit] Loaded {len(raw_results)} evaluation rows from {DATA_PATH}")

    # Aggregate by clip stem across the 2 temporal offsets (0.0 and 0.5)
    by_clip = {}
    question_meta = {}

    for row in raw_results:
        stem = Path(row["clip"]).stem
        summary = dict(row["summary"])
        for q in row["rows"]:
            qid = q["id"]
            summary[f"Q{qid}"] = q["p_yes"]
            if qid not in question_meta:
                question_meta[qid] = {
                    "id": qid,
                    "category": q["category"],
                    "text": q["text"],
                }
        by_clip.setdefault(stem, []).append(summary)

    # Compute mean across offsets for each clip
    clip_means = {}
    for stem, summaries in by_clip.items():
        keys = summaries[0].keys()
        clip_means[stem] = {k: float(np.mean([s[k] for s in summaries])) for k in keys}

    print(f"[audit] Processed {len(clip_means)} unique clips (averaged across offsets)")

    # Group clips by arm, ball, seed
    clip_map = {}
    for stem in clip_means:
        parsed = parse_clip_name(stem)
        if parsed:
            clip_map[parsed] = stem

    # Identify paired sets
    # 1. QT vs F (n=8 pairs)
    qt_pairs = []
    for (arm, ball, seed), stem in clip_map.items():
        if arm == "QT" and ("F", ball, seed) in clip_map:
            qt_pairs.append((clip_map[("F", ball, seed)], stem, (ball, seed)))
    qt_pairs.sort(key=lambda x: x[2])

    # 2. QS vs F (n=3 pairs)
    qs_pairs = []
    for (arm, ball, seed), stem in clip_map.items():
        if arm == "QS" and ("F", ball, seed) in clip_map:
            qs_pairs.append((clip_map[("F", ball, seed)], stem, (ball, seed)))
    qs_pairs.sort(key=lambda x: x[2])

    real_stem = clip_map.get(("real", "ball1", 0))
    real_means = clip_means[real_stem] if real_stem else None

    print(f"[audit] Identified {len(qt_pairs)} matched QT-F pairs, {len(qs_pairs)} QS-F pairs, real_ref={real_stem is not None}")

    categories = [
        "overall",
        "Physical Laws",
        "Visual Integrity",
        "Geometric Reasoning",
        "Semantic Alignment",
    ]
    all_keys = categories + [f"Q{i}" for i in range(1, 14)]

    # Compute statistical contrasts
    results = {
        "metadata": {
            "source_file": str(DATA_PATH),
            "n_qt_f_pairs": len(qt_pairs),
            "n_qs_f_pairs": len(qs_pairs),
            "qt_pairs": [[p[0], p[1]] for p in qt_pairs],
            "qs_pairs": [[p[0], p[1]] for p in qs_pairs],
            "real_reference_clip": real_stem,
        },
        "category_contrasts": {},
        "question_contrasts": {},
        "distance_to_real": {},
        "exploratory_exclusion": {},
    }

    print("\n" + "=" * 80)
    print("INDEPENDENT REPLICATION OF FINDING #2577: CATEGORY CONTRASTS")
    print("=" * 80)
    print(f"{'Category':22s} {'Base F':8s} {'QT':8s} {'Real Ref':8s} {'Diff ± SE':18s} {'p-value':10s} {'90% CI':18s}")
    print("-" * 80)

    for cat in categories:
        f_vals = np.array([clip_means[f_stem][cat] for f_stem, _, _ in qt_pairs])
        qt_vals = np.array([clip_means[qt_stem][cat] for _, qt_stem, _ in qt_pairs])
        diffs = qt_vals - f_vals

        mean_f = float(np.mean(f_vals))
        mean_qt = float(np.mean(qt_vals))
        mean_diff = float(np.mean(diffs))
        se_diff = float(stats.sem(diffs))
        t_stat, p_val = stats.ttest_rel(qt_vals, f_vals)
        lb90, ub90 = bootstrap_ci_paired(diffs, alpha=0.10)
        lb95, ub95 = bootstrap_ci_paired(diffs, alpha=0.05)
        n_pos = int(np.sum(diffs > 0))

        real_val = float(real_means[cat]) if real_means else None

        results["category_contrasts"][cat] = {
            "F_mean": mean_f,
            "QT_mean": mean_qt,
            "Real_ref": real_val,
            "diff_mean": mean_diff,
            "se": se_diff,
            "t_stat": float(t_stat),
            "p_val": float(p_val),
            "ci90": [lb90, ub90],
            "ci95": [lb95, ub95],
            "n_pairs": len(diffs),
            "n_positive": n_pos,
        }

        real_str = f"{real_val:.3f}" if real_val is not None else "N/A"
        print(f"{cat:22s} {mean_f:.3f}    {mean_qt:.3f}    {real_str:8s} {mean_diff:+.3f} ± {se_diff:.3f}     {p_val:.4f}    [{lb90:+.3f}, {ub90:+.3f}]")

    print("\n" + "=" * 80)
    print("QUESTION-LEVEL EVALUATION & DISTANCE-TO-REAL DIVERGENCE")
    print("=" * 80)
    print(f"{'QID':4s} {'Cat':6s} {'Base F':8s} {'QT':8s} {'Real':8s} {'QT - F':14s} {'|F-Real|':9s} {'|QT-Real|':10s} {'Closer?':8s}")
    print("-" * 80)

    closer_count = 0
    total_q_count = 0

    for qid in range(1, 14):
        qkey = f"Q{qid}"
        f_vals = np.array([clip_means[f_stem][qkey] for f_stem, _, _ in qt_pairs])
        qt_vals = np.array([clip_means[qt_stem][qkey] for _, qt_stem, _ in qt_pairs])
        diffs = qt_vals - f_vals

        mean_f = float(np.mean(f_vals))
        mean_qt = float(np.mean(qt_vals))
        mean_diff = float(np.mean(diffs))
        se_diff = float(stats.sem(diffs))
        real_val = float(real_means[qkey]) if real_means else 0.0

        dist_f = abs(mean_f - real_val)
        dist_qt = abs(mean_qt - real_val)
        closer = dist_qt < dist_f
        ratio = (dist_f / dist_qt) if dist_qt > 1e-6 else float("inf")

        if closer:
            closer_count += 1
        total_q_count += 1

        meta = question_meta[qid]
        short_cat = meta["category"][:4]

        results["question_contrasts"][qkey] = {
            "id": qid,
            "category": meta["category"],
            "text": meta["text"],
            "F_mean": mean_f,
            "QT_mean": mean_qt,
            "Real_val": real_val,
            "diff_mean": mean_diff,
            "se": se_diff,
            "dist_F": dist_f,
            "dist_QT": dist_qt,
            "QT_closer": closer,
            "error_ratio_F_over_QT": ratio,
        }

        closer_str = "YES" if closer else "no"
        print(f"Q{qid:<3d} {short_cat:6s} {mean_f:.3f}    {mean_qt:.3f}    {real_val:.3f}    {mean_diff:+.3f} ± {se_diff:.3f}  {dist_f:.3f}     {dist_qt:.3f}      {closer_str:8s}")

    print(f"\n[summary] Prompt QT is closer to Real Reference in {closer_count}/{total_q_count} questions ({closer_count/total_q_count*100:.1f}%)")

    # Category-level distance-to-real
    print("\n" + "=" * 80)
    print("CATEGORY-LEVEL DISTANCE-TO-REAL ACCURACY (|Score(gen) - Score(real)|)")
    print("=" * 80)
    for cat in categories:
        mean_f = results["category_contrasts"][cat]["F_mean"]
        mean_qt = results["category_contrasts"][cat]["QT_mean"]
        real_val = results["category_contrasts"][cat]["Real_ref"]
        dist_f = abs(mean_f - real_val)
        dist_qt = abs(mean_qt - real_val)
        ratio = (dist_f / dist_qt) if dist_qt > 1e-6 else float("inf")
        results["distance_to_real"][cat] = {
            "dist_F": dist_f,
            "dist_QT": dist_qt,
            "error_ratio": ratio,
        }
        print(f"{cat:22s}: |F - Real| = {dist_f:.4f} vs |QT - Real| = {dist_qt:.4f} -> QT is {ratio:.1f}x closer to real")

    # Stillness Control (QS - F, n=3 pairs)
    print("\n" + "=" * 80)
    print("STILLNESS CONTROL AUDIT (QS vs Base F, n=3)")
    print("=" * 80)
    results["stillness_control_qs"] = {}
    for cat in categories:
        f_vals = np.array([clip_means[f_stem][cat] for f_stem, _, _ in qs_pairs])
        qs_vals = np.array([clip_means[qs_stem][cat] for _, qs_stem, _ in qs_pairs])
        diffs = qs_vals - f_vals
        mean_f = float(np.mean(f_vals))
        mean_qs = float(np.mean(qs_vals))
        mean_diff = float(np.mean(diffs))
        se_diff = float(stats.sem(diffs)) if len(diffs) > 1 else 0.0
        results["stillness_control_qs"][cat] = {
            "F_mean": mean_f,
            "QS_mean": mean_qs,
            "diff_mean": mean_diff,
            "se": se_diff,
            "n_pairs": len(diffs),
        }
        print(f"{cat:22s}: F={mean_f:.3f}, QS={mean_qs:.3f}, Diff = {mean_diff:+.3f} ± {se_diff:.3f}")

    # Exploratory Exclusion of Release Questions (Q1, Q2, Q5)
    # Questions that remain: Q3, Q4, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13 (n=10 questions)
    retained_qids = [3, 4, 6, 7, 8, 9, 10, 11, 12, 13]
    f_posthoc = []
    qt_posthoc = []
    real_posthoc = float(np.mean([real_means[f"Q{i}"] for i in retained_qids]))

    for f_stem, qt_stem, _ in qt_pairs:
        f_val = float(np.mean([clip_means[f_stem][f"Q{i}"] for i in retained_qids]))
        qt_val = float(np.mean([clip_means[qt_stem][f"Q{i}"] for i in retained_qids]))
        f_posthoc.append(f_val)
        qt_posthoc.append(qt_val)

    f_posthoc = np.array(f_posthoc)
    qt_posthoc = np.array(qt_posthoc)
    diffs_posthoc = qt_posthoc - f_posthoc

    mean_f_ph = float(np.mean(f_posthoc))
    mean_qt_ph = float(np.mean(qt_posthoc))
    diff_ph = float(np.mean(diffs_posthoc))
    se_ph = float(stats.sem(diffs_posthoc))
    t_ph, p_ph = stats.ttest_rel(qt_posthoc, f_posthoc)
    lb90_ph, ub90_ph = bootstrap_ci_paired(diffs_posthoc, alpha=0.10)

    results["exploratory_exclusion"] = {
        "excluded_questions": [1, 2, 5],
        "retained_questions": retained_qids,
        "F_mean": mean_f_ph,
        "QT_mean": mean_qt_ph,
        "Real_ref": real_posthoc,
        "diff_mean": diff_ph,
        "se": se_ph,
        "t_stat": float(t_ph),
        "p_val": float(p_ph),
        "ci90": [lb90_ph, ub90_ph],
        "passes_non_inferiority_delta_03": lb90_ph > -0.030,
    }

    print("\n" + "=" * 80)
    print("EXPLORATORY SENSITIVITY (DROPPING UNINFORMATIVE RELEASE Q1, Q2, Q5)")
    print("=" * 80)
    print(f"Retained Questions (n=10): Base F = {mean_f_ph:.3f}, QT = {mean_qt_ph:.3f}, Real = {real_posthoc:.3f}")
    print(f"Paired Difference: Δ = {diff_ph:+.4f} ± {se_ph:.4f} (p = {p_ph:.4f}), 90% CI = [{lb90_ph:+.4f}, {ub90_ph:+.4f}]")
    print(f"Non-Inferiority vs δ = 0.030: {'PASSES (LB > -0.030)' if lb90_ph > -0.030 else 'FAILS'}")

    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[audit] Results successfully saved to {OUT_JSON}")


if __name__ == "__main__":
    run_audit()
