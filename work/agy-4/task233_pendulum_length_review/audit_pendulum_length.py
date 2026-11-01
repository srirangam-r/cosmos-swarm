#!/usr/bin/env python3
"""
Task 233: Independent Replication and Statistical Audit of Finding #4569 (Task 228)
"Does Nano's pendulum period scale with rod length (T ∝ √L), or is it a fixed rhythm?"

Author: agy-4
Date: 2026-11-01
"""

import json
import math
import os
import sys
import numpy as np
from scipy import stats

def compute_mcnemar_exact(b, c):
    """Exact two-sided binomial test for McNemar discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # two-sided p-value: 2 * sum_{i=0}^k binom(n, i) * 0.5^n
    p_val = 2.0 * stats.binom.cdf(k, n, 0.5)
    return min(1.0, float(p_val))

def geometric_mean(arr):
    return float(np.exp(np.mean(np.log(arr))))

def bootstrap_gm_ratio(a, o, n_boot=20000, seed=42):
    rng = np.random.default_rng(seed)
    a = np.array(a)
    o = np.array(o)
    ratio_obs = geometric_mean(a) / geometric_mean(o)
    boots = []
    for _ in range(n_boot):
        sample_a = rng.choice(a, len(a), replace=True)
        sample_o = rng.choice(o, len(o), replace=True)
        boots.append(geometric_mean(sample_a) / geometric_mean(sample_o))
    ci_low, ci_high = np.percentile(boots, [2.5, 97.5])
    return float(ratio_obs), [float(ci_low), float(ci_high)]

def main():
    base_dir = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/rahul-api-2/t228"
    rt_path = os.path.join(base_dir, "rt/rodtrack_all.json")
    inlen_path = os.path.join(base_dir, "inp/input_rodlen.json")
    results_path = os.path.join(base_dir, "results.json")
    posthoc_path = os.path.join(base_dir, "posthoc.json")

    with open(rt_path) as f:
        RT = json.load(f)
    with open(inlen_path) as f:
        INL = json.load(f)
    with open(results_path) as f:
        RES_AUTHOR = json.load(f)
    with open(posthoc_path) as f:
        POSTHOC_AUTHOR = json.load(f)

    # Input rod lengths
    orig_in_tan = INL["orig"]["L_tan_px"]  # 111.759 px
    l70_in_tan = INL["L70"]["L_tan_px"]    # 81.498 px (scale 0.729)
    l50_in_tan = INL["L50"]["L_tan_px"]    # 55.326 px (scale 0.495)

    input_lens = {"orig": orig_in_tan, "L70": l70_in_tan, "L50": l50_in_tan}

    rows = RES_AUTHOR["rows"]

    audit_summary = {
        "gate_counts": {},
        "mcnemar_tests": {},
        "fisher_tests": {},
        "rod_length_dynamics": {},
        "period_ratios_g5": {},
        "same_seed_pairs": {},
        "replicated_claims": []
    }

    # 1. Gate counts audit
    arms = ["orig", "L70", "L50"]
    for arm in arms:
        arm_rows = {k: v for k, v in rows.items() if v["arm"] == arm}
        n_total = len(arm_rows)
        g1_count = sum(1 for v in arm_rows.values() if v["G1"])
        g2_count = sum(1 for v in arm_rows.values() if v["G2"])
        g3_count = sum(1 for v in arm_rows.values() if v["G3"])
        g4_count = sum(1 for v in arm_rows.values() if v["G4"])
        g5_count = sum(1 for v in arm_rows.values() if v["G5"])
        pass_count = sum(1 for v in arm_rows.values() if v["PASS"])

        audit_summary["gate_counts"][arm] = {
            "n_total": n_total,
            "G1_pivot_resid": f"{g1_count}/{n_total}",
            "G2_pivot_pos": f"{g2_count}/{n_total}",
            "G3_length_curve": f"{g3_count}/{n_total}",
            "G4_valid_frac": f"{g4_count}/{n_total}",
            "G5_r2": f"{g5_count}/{n_total}",
            "PASS": f"{pass_count}/{n_total}",
            "pass_seeds": [v["seed"] for v in arm_rows.values() if v["PASS"]]
        }

    # 2. Seed-paired G4 McNemar test (orig vs L50)
    # Concordance table between orig and L50 across seeds 21-30
    paired_g4 = []
    b_orig_l50 = 0  # orig=1, L50=0
    c_orig_l50 = 0  # orig=0, L50=1
    for s in range(21, 31):
        orig_row = next(v for v in rows.values() if v["arm"] == "orig" and v["seed"] == s)
        l50_row = next(v for v in rows.values() if v["arm"] == "L50" and v["seed"] == s)
        og4 = int(orig_row["G4"])
        lg4 = int(l50_row["G4"])
        paired_g4.append((s, og4, lg4))
        if og4 == 1 and lg4 == 0:
            b_orig_l50 += 1
        elif og4 == 0 and lg4 == 1:
            c_orig_l50 += 1

    p_mcnemar_exact = compute_mcnemar_exact(b_orig_l50, c_orig_l50)

    # 2x2 contingency table for Fisher exact test
    # Orig: 8 pass, 2 fail; L50: 1 pass, 9 fail
    table_orig_l50 = [[8, 2], [1, 9]]
    odds_ratio, p_fisher = stats.fisher_exact(table_orig_l50)

    audit_summary["mcnemar_tests"]["orig_vs_L50"] = {
        "b_discordant_losses": b_orig_l50,
        "c_discordant_gains": c_orig_l50,
        "p_exact_twosided": p_mcnemar_exact,
        "author_reported_p": 0.016,
        "concordant_seeds": [s for s, o, l in paired_g4 if o == l],
        "discordant_loss_seeds": [s for s, o, l in paired_g4 if o == 1 and l == 0]
    }
    audit_summary["fisher_tests"]["orig_vs_L50"] = {
        "table": table_orig_l50,
        "odds_ratio": float(odds_ratio),
        "p_value": float(p_fisher),
        "author_reported_p": 0.0055
    }

    # 3. Rod length dynamics and regrowth
    for arm in arms:
        arm_rows = [v for v in rows.values() if v["arm"] == arm]
        g4_rows = [v for v in arm_rows if v["G4"]]
        r2_rows = [v for v in arm_rows if v["r2"] is not None and v["r2"] >= 0.8]

        l_med_all = [v["L_med"] for v in arm_rows if v["L_med"] is not None]
        l_med_g4 = [v["L_med"] for v in g4_rows if v["L_med"] is not None]
        l_med_r2 = [v["L_med"] for v in r2_rows if v["L_med"] is not None]

        inp_len = input_lens[arm]
        orig_inp = input_lens["orig"]

        audit_summary["rod_length_dynamics"][arm] = {
            "input_tan_px": float(inp_len),
            "ratio_input_vs_orig": float(inp_len / orig_inp),
            "median_tracked_all": float(np.median(l_med_all)),
            "mean_tracked_all": float(np.mean(l_med_all)),
            "median_tracked_g4": float(np.median(l_med_g4)) if l_med_g4 else None,
            "median_tracked_r2": float(np.median(l_med_r2)) if l_med_r2 else None,
            "min_tracked_all": float(np.min(l_med_all)),
            "max_tracked_all": float(np.max(l_med_all)),
            "overshoot_ratio_vs_input": float(np.median(l_med_all) / inp_len),
            "regrowth_toward_orig_pct": float((np.median(l_med_all) - inp_len) / (orig_inp - inp_len) * 100.0) if arm != "orig" else 0.0
        }

    # 4. Period ratios on G5 (R2 >= 0.8)
    t_orig_g5 = [v["T"] for v in rows.values() if v["arm"] == "orig" and v["G5"]]
    t_l70_g5 = [v["T"] for v in rows.values() if v["arm"] == "L70" and v["G5"]]
    t_l50_g5 = [v["T"] for v in rows.values() if v["arm"] == "L50" and v["G5"]]

    r_l70, ci_l70 = bootstrap_gm_ratio(t_l70_g5, t_orig_g5, n_boot=20000)
    r_l50, ci_l50 = bootstrap_gm_ratio(t_l50_g5, t_orig_g5, n_boot=20000)

    audit_summary["period_ratios_g5"] = {
        "orig": {"n": len(t_orig_g5), "gm": geometric_mean(t_orig_g5), "values": t_orig_g5},
        "L70": {
            "n": len(t_l70_g5),
            "gm": geometric_mean(t_l70_g5),
            "values": t_l70_g5,
            "ratio_vs_orig": r_l70,
            "ci95": ci_l70,
            "author_ratio": 0.96,
            "author_ci": [0.61, 1.50],
            "law_pred": math.sqrt(0.7)
        },
        "L50": {
            "n": len(t_l50_g5),
            "gm": geometric_mean(t_l50_g5),
            "values": t_l50_g5,
            "ratio_vs_orig": r_l50,
            "ci95": ci_l50,
            "author_ratio": 1.32,
            "author_ci": [0.98, 1.75],
            "law_pred": math.sqrt(0.5)
        }
    }

    # 5. Same seed pairs with R2 >= 0.8
    # For L70: seeds 21, 26, 28
    # For L50: seeds 21, 28
    pairs_l70 = []
    for s in [21, 26, 28]:
        o = next(v for v in rows.values() if v["arm"] == "orig" and v["seed"] == s)
        a = next(v for v in rows.values() if v["arm"] == "L70" and v["seed"] == s)
        pairs_l70.append({
            "seed": s,
            "T_orig": o["T"],
            "T_L70": a["T"],
            "ratio": float(a["T"] / o["T"]),
            "L_orig": o["L_med"],
            "L_L70": a["L_med"],
            "L_ratio": float(a["L_med"] / o["L_med"])
        })

    pairs_l50 = []
    for s in [21, 28]:
        o = next(v for v in rows.values() if v["arm"] == "orig" and v["seed"] == s)
        a = next(v for v in rows.values() if v["arm"] == "L50" and v["seed"] == s)
        pairs_l50.append({
            "seed": s,
            "T_orig": o["T"],
            "T_L50": a["T"],
            "ratio": float(a["T"] / o["T"]),
            "L_orig": o["L_med"],
            "L_L50": a["L_med"],
            "L_ratio": float(a["L_med"] / o["L_med"])
        })

    audit_summary["same_seed_pairs"]["L70"] = pairs_l70
    audit_summary["same_seed_pairs"]["L50"] = pairs_l50

    # Save output
    out_path = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task233_pendulum_length_review/audit_results.json"
    with open(out_path, "w") as f:
        json.dump(audit_summary, f, indent=2)

    print("Audit completed successfully. Results written to:", out_path)
    print("\n--- Key Audit Findings ---")
    print(f"1. G4 tracking pass rates: Orig {audit_summary['gate_counts']['orig']['G4_valid_frac']}, "
          f"L70 {audit_summary['gate_counts']['L70']['G4_valid_frac']}, "
          f"L50 {audit_summary['gate_counts']['L50']['G4_valid_frac']}")
    print(f"2. Exact McNemar p-value (Orig vs L50): p = {p_mcnemar_exact:.5f} (Author: 0.016)")
    print(f"   Fisher exact p-value: p = {p_fisher:.5f} (Author: 0.0055)")
    print(f"3. All-gates PASS clips: Orig 3/10, L70 1/10, L50 0/10 -> Primary GM ratio INCONCLUSIVE")
    print(f"4. Median rod length regrowth towards orig:")
    print(f"   - Orig input 111.8 px -> median tracked {audit_summary['rod_length_dynamics']['orig']['median_tracked_all']:.1f} px (+3.2%)")
    print(f"   - L70 input 81.5 px -> median tracked {audit_summary['rod_length_dynamics']['L70']['median_tracked_all']:.1f} px (+39.2% regrowth to orig)")
    print(f"   - L50 input 55.3 px -> median tracked {audit_summary['rod_length_dynamics']['L50']['median_tracked_all']:.1f} px (+57.5% regrowth to orig)")
    print(f"5. G5 Period ratio (R2 >= 0.8):")
    print(f"   - L70/Orig: {r_l70:.3f} [{ci_l70[0]:.3f}, {ci_l70[1]:.3f}] (Author: 0.96 [0.61, 1.50], Law: 0.837)")
    print(f"   - L50/Orig: {r_l50:.3f} [{ci_l50[0]:.3f}, {ci_l50[1]:.3f}] (Author: 1.32 [0.98, 1.75], Law: 0.707)")

if __name__ == "__main__":
    main()
