#!/usr/bin/env python3
"""Program N Blind Coding Harness (rahul-5-agy)

Utility functions and CLI for:
1. Ingesting blinded contact sheets or clips.
2. Enforcing standardized coding vocabulary and validating codes.
3. Cryptographically freezing codes before unblinding.
4. Computing inter-rater reliability (Cohen's kappa, concordance) and planted-control accuracy.
"""

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from typing import Dict, List, Tuple, Optional, Any

VALID_END_STATES = {"REST", "MOVING", "HELD", "GONE", "UNCLEAR"}
VALID_TRINARY = {"Y", "N", "U"}
VALID_CONFIDENCE = {"H", "M", "L"}

VALID_MOTION_DIRECTIONS = {
    "DOWNWARD", "UPWARD", "STATIONARY",
    "SWINGING_NORMAL", "SWINGING_FAST", "FROZEN", "AMBIGUOUS"
}
VALID_COMPLIANCE = {"COMPLIANT", "NON_COMPLIANT", "UNCLEAR"}


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def freeze_file(filepath: str, out_hash_path: Optional[str] = None) -> str:
    """Calculate and write SHA-256 hash to a frozen checksum file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    sha = compute_sha256(filepath)
    if out_hash_path is None:
        out_hash_path = f"{filepath}.FROZEN.sha256"
    with open(out_hash_path, "w") as f:
        f.write(f"{sha}  {os.path.basename(filepath)}\n")
    return sha


def validate_contact_row(row: Dict[str, str], row_idx: int) -> List[str]:
    """Validate a contact event row against rubric vocabulary."""
    errors = []
    clip_id = row.get("id", "").strip()
    if not clip_id:
        errors.append(f"Row {row_idx}: Missing 'id'")

    end_state = row.get("end_state", "").strip().upper()
    if end_state not in VALID_END_STATES:
        errors.append(f"Row {row_idx} ({clip_id}): Invalid end_state '{end_state}', expected one of {VALID_END_STATES}")

    for field in ["clone", "retether", "growth"]:
        val = row.get(field, "").strip().upper()
        if val and val not in VALID_TRINARY:
            errors.append(f"Row {row_idx} ({clip_id}): Invalid {field} '{val}', expected one of {VALID_TRINARY}")

    conf = row.get("confidence", "").strip().upper()
    if conf and conf not in VALID_CONFIDENCE:
        errors.append(f"Row {row_idx} ({clip_id}): Invalid confidence '{conf}', expected one of {VALID_CONFIDENCE}")

    return errors


def validate_motion_row(row: Dict[str, str], row_idx: int) -> List[str]:
    """Validate a text control / motion row against rubric vocabulary."""
    errors = []
    clip_id = row.get("id", "").strip()
    if not clip_id:
        errors.append(f"Row {row_idx}: Missing 'id'")

    direction = row.get("motion_direction", "").strip().upper()
    if direction not in VALID_MOTION_DIRECTIONS:
        errors.append(f"Row {row_idx} ({clip_id}): Invalid motion_direction '{direction}', expected one of {VALID_MOTION_DIRECTIONS}")

    comp = row.get("text_compliance", "").strip().upper()
    if comp and comp not in VALID_COMPLIANCE:
        errors.append(f"Row {row_idx} ({clip_id}): Invalid text_compliance '{comp}', expected one of {VALID_COMPLIANCE}")

    return errors


def compute_cohen_kappa(rater1: List[str], rater2: List[str], labels: Optional[List[str]] = None) -> Dict[str, Any]:
    """Compute Cohen's kappa for two raters with categorical classifications."""
    if len(rater1) != len(rater2):
        raise ValueError(f"Rater lists must have same length: {len(rater1)} != {len(rater2)}")
    n = len(rater1)
    if n == 0:
        return {"n": 0, "observed_agreement": 0.0, "expected_agreement": 0.0, "kappa": 0.0}

    if labels is None:
        labels = sorted(list(set(rater1) | set(rater2)))

    label_to_idx = {l: i for i, l in enumerate(labels)}
    k = len(labels)
    matrix = [[0] * k for _ in range(k)]

    agreements = 0
    for r1, r2 in zip(rater1, rater2):
        if r1 == r2:
            agreements += 1
        i = label_to_idx[r1]
        j = label_to_idx[r2]
        matrix[i][j] += 1

    po = agreements / n

    # Expected agreement
    pe = 0.0
    for i in range(k):
        row_sum = sum(matrix[i])
        col_sum = sum(matrix[r][i] for r in range(k))
        pe += (row_sum * col_sum) / (n * n)

    if math.isclose(pe, 1.0):
        kappa = 1.0 if math.isclose(po, 1.0) else 0.0
    else:
        kappa = (po - pe) / (1.0 - pe)

    return {
        "n": n,
        "labels": labels,
        "confusion_matrix": matrix,
        "observed_agreement": po,
        "expected_agreement": pe,
        "kappa": kappa
    }


def evaluate_planted_controls(codes: List[Dict[str, str]], ground_truth: Dict[str, str], target_col: str = "end_state") -> Dict[str, Any]:
    """Score accuracy against planted known-answer controls."""
    matched = 0
    total = 0
    details = []

    for row in codes:
        cid = row.get("id")
        if cid in ground_truth:
            pred = row.get(target_col, "").strip().upper()
            actual = ground_truth[cid].strip().upper()
            is_correct = (pred == actual)
            if is_correct:
                matched += 1
            total += 1
            details.append({"id": cid, "predicted": pred, "ground_truth": actual, "correct": is_correct})

    acc = (matched / total) if total > 0 else 0.0
    return {
        "total_controls": total,
        "correct": matched,
        "accuracy": acc,
        "pass": acc >= 0.90 if total >= 5 else None,
        "details": details
    }


def load_kap_real_manifest(manifest_path: str) -> Dict[str, str]:
    """Load rog1's kap_real known-answer pack manifest and map labels to standardized rubric.

    Mappings:
      BOUNCING -> MOVING
      ROLLING  -> MOVING
      REST     -> REST
      AMBIG    -> UNCLEAR
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"kap_real manifest not found: {manifest_path}")
    with open(manifest_path, "r") as f:
        items = json.load(f)
    gt = {}
    for item in items:
        cid = item.get("cut_id")
        raw_label = str(item.get("label", "")).upper()
        if raw_label in ("BOUNCING", "ROLLING"):
            gt[cid] = "MOVING"
        elif raw_label == "REST":
            gt[cid] = "REST"
        elif "AMBIG" in raw_label:
            gt[cid] = "UNCLEAR"
        else:
            gt[cid] = raw_label
    return gt

