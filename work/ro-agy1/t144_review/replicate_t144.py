#!/usr/bin/env python3
"""
Task 144 Independent Review & Replication:
Velocity cue (downward trail) test on GAUGE unsupported ball (G frame).
Replicates raj-api-3 Finding #3932 and verifies the unblinding key and statistical tests.
"""

import os
import sys
import json
import csv
import re
import hashlib
from collections import Counter
from scipy.stats import binomtest

SWARM_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
KEY_PATH = os.path.join(os.path.dirname(__file__), "key.json")
CODES_PATH = os.path.join(SWARM_ROOT, "work/raj-api-2/t144/codes.csv")
TARGET_KEY_HASH = "bc804e86c4e449662564d6216614d74467a5d10db4c252298556b85434cdc3f8"

def main():
    print("=== TASK 144 INDEPENDENT REPLICATION & AUDIT ===")
    
    # 1. Verify key integrity
    with open(KEY_PATH, "r") as f:
        key_content = f.read()
    key_hash = hashlib.sha256(key_content.encode()).hexdigest()
    print(f"Key SHA256:   {key_hash}")
    print(f"Target SHA256:{TARGET_KEY_HASH}")
    assert key_hash == TARGET_KEY_HASH, "Key hash mismatch!"
    print("[PASS] Key SHA256 matches pre-registered freeze.\n")
    
    key = json.loads(key_content)
    assert len(key) == 50, f"Expected 50 entries, got {len(key)}"

    # 2. Load blind codes
    with open(CODES_PATH, "r") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 50, f"Expected 50 coded rows, got {len(rows)}"

    d = {}
    for r in rows:
        hex_id = r["hex"]
        assert hex_id in key, f"Hex {hex_id} not in key!"
        clip_name = key[hex_id]
        m = re.match(r"t144_G1_(\w+)_s(\d+)", clip_name)
        assert m is not None, f"Could not parse clip name {clip_name}"
        arm = m.group(1)
        seed = int(m.group(2))
        d[(arm, seed)] = r

    def is_clean_fall(arm, seed, strict=False):
        r = d[(arm, seed)]
        val = r["clean_fall"] == "Y"
        if strict and "AMBIGUOUS" in r["note"]:
            val = False
        return val

    arms = ["A", "VD", "VU", "VI", "VB"]
    results = {
        "key_sha256": key_hash,
        "n_clips": len(rows),
        "primary": {},
        "strict": {},
        "secondary": {}
    }

    for strict, mode in [(False, "primary"), (True, "strict")]:
        print(f"--- {mode.upper()} READOUT ---")
        counts = {}
        for a in arms:
            c = sum(is_clean_fall(a, s, strict) for s in range(1, 11))
            counts[a] = f"{c}/10"
            print(f"Arm {a:2s}: {c}/10 clean falls")
        results[mode]["counts"] = counts

        contrasts = {}
        p_vals = {}
        for b in ["VU", "VI", "VB", "A"]:
            vd_only = sum(is_clean_fall("VD", s, strict) and not is_clean_fall(b, s, strict) for s in range(1, 11))
            b_only = sum(is_clean_fall(b, s, strict) and not is_clean_fall("VD", s, strict) for s in range(1, 11))
            ties = sum(is_clean_fall("VD", s, strict) == is_clean_fall(b, s, strict) for s in range(1, 11))
            n_discordant = vd_only + b_only
            p1 = binomtest(vd_only, n_discordant, 0.5, alternative="greater").pvalue if n_discordant > 0 else 1.0
            p_vals[b] = p1
            contrasts[f"VD_vs_{b}"] = {
                "vd_only": vd_only,
                f"{b.lower()}_only": b_only,
                "ties": ties,
                "p_one_sided": float(p1)
            }
            print(f"  VD vs {b:2s}: VD-only {vd_only}, {b:2s}-only {b_only}, ties {ties} -> exact 1-sided sign p = {p1:.4f}")
        
        # Holm adjustment across the two primary contrasts (VD > VU and VD > VI)
        sorted_prim = sorted([p_vals["VU"], p_vals["VI"]])
        holm_prim = {
            "VU": min(1.0, float(p_vals["VU"] * (2 if p_vals["VU"] == sorted_prim[0] else 1))),
            "VI": min(1.0, float(p_vals["VI"] * (2 if p_vals["VI"] == sorted_prim[0] else 1)))
        }
        contrasts["holm_adjustment_primary"] = holm_prim
        print(f"  Holm-adjusted primary p-values: {holm_prim}\n")
        results[mode]["contrasts"] = contrasts

    # 3. Secondary endpoints
    print("--- SECONDARY METRICS ---")
    for field in ["first_disp", "holder_redrawn", "clone"]:
        results["secondary"][field] = {}
        print(f"Metric: {field}")
        for a in arms:
            dist = dict(Counter(d[(a, s)][field] for s in range(1, 11)))
            results["secondary"][field][a] = dist
            print(f"  Arm {a:2s}: {dist}")
        print()

    # Save results
    out_json = os.path.join(os.path.dirname(__file__), "t144_replication_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[DONE] Wrote verified replication results to {out_json}")

if __name__ == "__main__":
    main()
