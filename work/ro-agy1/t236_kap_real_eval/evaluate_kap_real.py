#!/usr/bin/env python3
"""
Evaluate Task 222 rest_candidate.py (ef3a6acb) against rog1's real GAUGE known-answer pack (kap_real).
Tests all 66 real cuts (20 BOUNCING, 22 ROLLING, 2 REST, 22 AMBIG) with objective mocap-grounded labels.
"""

import os
import sys
import json
import math
import numpy as np

# Ensure local rest_candidate is loaded
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from rest_candidate import classify_video

KAP_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../rog1/kap_real"))
MANIFEST_PATH = os.path.join(KAP_DIR, "manifest.json")
LABELS_PATH = os.path.join(KAP_DIR, "labels_final.json")
CUTS_DIR = os.path.join(KAP_DIR, "cuts")


def run_evaluation():
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    with open(LABELS_PATH, "r") as f:
        labels_final = json.load(f)

    print(f"Loaded {len(manifest)} cuts from manifest.")

    results = []
    
    # Category trackers
    cat_counts = {"BOUNCING": 0, "ROLLING": 0, "REST": 0, "AMBIG": 0}
    cat_classified = {"BOUNCING": 0, "ROLLING": 0, "REST": 0, "AMBIG": 0}
    cat_preds = {
        "BOUNCING": {"REST_CANDIDATE": 0, "MOVING_CANDIDATE": 0, "UNKNOWN": 0},
        "ROLLING": {"REST_CANDIDATE": 0, "MOVING_CANDIDATE": 0, "UNKNOWN": 0},
        "REST": {"REST_CANDIDATE": 0, "MOVING_CANDIDATE": 0, "UNKNOWN": 0},
        "AMBIG": {"REST_CANDIDATE": 0, "MOVING_CANDIDATE": 0, "UNKNOWN": 0},
    }

    unknown_reasons = {}

    for item in manifest:
        cut_id = item["cut_id"]
        true_label = item["label"]
        cat_counts[true_label] += 1

        video_path = os.path.join(CUTS_DIR, f"{cut_id}.mp4")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file missing: {video_path}")

        pred = classify_video(video_path)
        pred_state = pred["state"]
        cat_preds[true_label][pred_state] += 1

        is_classified = (pred_state != "UNKNOWN")
        if is_classified:
            cat_classified[true_label] += 1
        else:
            reason = pred.get("reason", "unknown")
            unknown_reasons[reason] = unknown_reasons.get(reason, 0) + 1

        max_shift = pred.get("max_shift_px")
        diameter = pred.get("median_box_diameter_px")
        shift_ratio = (max_shift / diameter) if (max_shift is not None and diameter) else None

        record = {
            "cut_id": cut_id,
            "clip": item["clip"],
            "true_label": true_label,
            "start_f": item["start_f"],
            "end_f": item["end_f"],
            "n_out_frames": item["n_out_frames"],
            "predicted_state": pred_state,
            "reason": pred.get("reason"),
            "max_shift_px": max_shift,
            "median_box_diameter_px": diameter,
            "shift_ratio": shift_ratio,
            "boxes": pred.get("boxes"),
            "edge_counts": pred.get("edge_counts"),
            "frame_indices": pred.get("frame_indices"),
        }
        results.append(record)

    total_cuts = len(results)
    total_classified = sum(cat_classified.values())
    total_coverage = total_classified / total_cuts

    # Analysis of rolling false rest rate
    rolling_total = cat_counts["ROLLING"]
    rolling_class = cat_classified["ROLLING"]
    rolling_rest = cat_preds["ROLLING"]["REST_CANDIDATE"]
    rolling_moving = cat_preds["ROLLING"]["MOVING_CANDIDATE"]
    rolling_unknown = cat_preds["ROLLING"]["UNKNOWN"]
    rolling_false_rest_rate = (rolling_rest / rolling_class) if rolling_class > 0 else 0.0

    # Analysis of bouncing
    bouncing_total = cat_counts["BOUNCING"]
    bouncing_class = cat_classified["BOUNCING"]
    bouncing_rest = cat_preds["BOUNCING"]["REST_CANDIDATE"]
    bouncing_moving = cat_preds["BOUNCING"]["MOVING_CANDIDATE"]

    # Analysis of rest (true ground truth rest)
    rest_total = cat_counts["REST"]
    rest_class = cat_classified["REST"]
    rest_correct = cat_preds["REST"]["REST_CANDIDATE"]

    # Analysis of ambig
    ambig_total = cat_counts["AMBIG"]
    ambig_class = cat_classified["AMBIG"]
    ambig_rest = cat_preds["AMBIG"]["REST_CANDIDATE"]
    ambig_moving = cat_preds["AMBIG"]["MOVING_CANDIDATE"]

    summary = {
        "dataset": "work/rog1/kap_real",
        "classifier_commit": "ef3a6acb",
        "total_cuts": total_cuts,
        "total_classified": total_classified,
        "total_coverage": total_coverage,
        "category_counts": cat_counts,
        "category_classified": cat_classified,
        "predictions_table": cat_preds,
        "unknown_reasons": unknown_reasons,
        "key_metrics": {
            "rolling_coverage": rolling_class / rolling_total,
            "rolling_false_rest_count": rolling_rest,
            "rolling_false_rest_rate_among_classified": rolling_false_rest_rate,
            "rolling_true_moving_count": rolling_moving,
            "rolling_unknown_count": rolling_unknown,
            "bouncing_coverage": bouncing_class / bouncing_total,
            "bouncing_false_rest_count": bouncing_rest,
            "bouncing_true_moving_count": bouncing_moving,
            "rest_coverage": rest_class / rest_total,
            "rest_true_positive_count": rest_correct,
            "ambig_coverage": ambig_class / ambig_total,
            "ambig_rest_count": ambig_rest,
            "ambig_moving_count": ambig_moving,
        }
    }

    print("\n" + "=" * 60)
    print("TASK 222 REST CLASSIFIER EVALUATION ON REAL GAUGE (kap_real)")
    print("=" * 60)
    print(f"Overall Coverage: {total_classified}/{total_cuts} ({total_coverage * 100:.1f}%)")
    print("\nConfusion Matrix by Ground-Truth Category:")
    print(f"{'Category':<12} | {'REST':<6} | {'MOVING':<6} | {'UNKNOWN':<8} | {'Total':<6} | {'Coverage':<8}")
    print("-" * 55)
    for cat in ["BOUNCING", "ROLLING", "REST", "AMBIG"]:
        p = cat_preds[cat]
        tot = cat_counts[cat]
        cov = cat_classified[cat] / tot * 100
        print(f"{cat:<12} | {p['REST_CANDIDATE']:<6} | {p['MOVING_CANDIDATE']:<6} | {p['UNKNOWN']:<8} | {tot:<6} | {cov:>5.1f}%")

    print("\nCRITICAL FAILURE MODE - ROLLING BALLS:")
    print(f"Active Rolling Balls (n={rolling_total}):")
    print(f"  - Classified: {rolling_class}/{rolling_total} ({rolling_class/rolling_total*100:.1f}%)")
    print(f"  - Classified as REST_CANDIDATE (FALSE REST): {rolling_rest}/{rolling_class} ({rolling_false_rest_rate*100:.1f}% of classified!)")
    print(f"  - Classified as MOVING_CANDIDATE: {rolling_moving}/{rolling_class}")

    print("\nTRUE REST BALLS (n=2):")
    print(f"  - Correctly identified as REST_CANDIDATE: {rest_correct}/{rest_total}")
    for r in results:
        if r["true_label"] == "REST":
            print(f"    {r['cut_id']}: state={r['predicted_state']}, shift={r['max_shift_px']}, diam={r['median_box_diameter_px']}")

    # Save outputs
    out_preds_path = os.path.join(SCRIPT_DIR, "predictions_kap_real.json")
    with open(out_preds_path, "w") as f:
        json.dump(results, f, indent=2)

    out_summary_path = os.path.join(SCRIPT_DIR, "results_summary.json")
    with open(out_summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSaved detailed predictions to {out_preds_path}")
    print(f"Saved summary metrics to {out_summary_path}")

    return results, summary


if __name__ == "__main__":
    run_evaluation()
