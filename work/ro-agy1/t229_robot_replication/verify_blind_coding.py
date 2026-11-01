#!/usr/bin/env python3
"""Verify blind coding results against planted ground truth and evaluate inter-rater agreement."""
import argparse, json, os
import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix, accuracy_score

def main():
    parser = argparse.ArgumentParser(description="Verify blind coding against key")
    parser.add_argument("--coding_sheet", required=True, help="Filled coding sheet CSV")
    parser.add_argument("--key_json", required=True, help="Unblinded KEY_DO_NOT_OPEN.json")
    parser.add_argument("--first_coder_sheet", default=None, help="Optional first coder CSV for inter-rater agreement")
    parser.add_argument("--out_json", required=True, help="Output verification report JSON")
    args = parser.parse_args()

    sheet = pd.read_csv(args.coding_sheet)
    with open(args.key_json, "r") as f:
        key = json.load(f)

    # 1. Planted case audit
    planted_total = 0
    planted_correct = 0
    planted_eval = []

    for _, row in sheet.iterrows():
        bid = row["blind_id"]
        if bid not in key:
            continue
        k_info = key[bid]
        if k_info.get("is_planted"):
            gt = str(k_info.get("ground_truth")).strip().upper()
            pred = str(row.get("outcome", "")).strip().upper()
            is_match = (gt == pred)
            planted_total += 1
            if is_match:
                planted_correct += 1
            planted_eval.append({
                "blind_id": bid,
                "orig_filename": k_info.get("orig_filename"),
                "ground_truth": gt,
                "predicted": pred,
                "match": is_match
            })

    planted_accuracy = float(planted_correct / planted_total) if planted_total > 0 else 1.0

    report = {
        "total_clips_coded": len(sheet),
        "planted_controls": {
            "total_planted": planted_total,
            "correct": planted_correct,
            "accuracy": planted_accuracy,
            "pass_fail": "PASS" if planted_accuracy >= 0.90 else "FAIL",
            "eval_rows": planted_eval
        }
    }

    # 2. Inter-rater agreement (if first coder sheet provided)
    if args.first_coder_sheet and os.path.exists(args.first_coder_sheet):
        first_sheet = pd.read_csv(args.first_coder_sheet)
        merged = pd.merge(sheet, first_sheet, on="blind_id", suffixes=("_coder2", "_coder1"))
        c1 = merged["outcome_coder1"].astype(str).str.strip().str.upper()
        c2 = merged["outcome_coder2"].astype(str).str.strip().str.upper()

        pct_agree = float((c1 == c2).mean())
        try:
            kappa = float(cohen_kappa_score(c1, c2))
        except Exception:
            kappa = None

        report["inter_rater_agreement"] = {
            "compared_clips": len(merged),
            "percent_agreement": pct_agree,
            "cohen_kappa": kappa
        }

    with open(args.out_json, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Planted check: {planted_correct}/{planted_total} ({planted_accuracy*100:.1f}%) -> {report['planted_controls']['pass_fail']}")
    if "inter_rater_agreement" in report:
        print(f"Inter-rater agreement: {report['inter_rater_agreement']['percent_agreement']*100:.1f}%, Kappa: {report['inter_rater_agreement']['cohen_kappa']}")

if __name__ == "__main__":
    main()
