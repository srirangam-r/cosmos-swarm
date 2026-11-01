#!/usr/bin/env python3
"""Evaluate all 16 choices of 3-of-4 seeds for Ball 1 & 2 in Motion Fidelity (Cosmos 3 tech report eqs. 10-11).
Tests robustness of MF before/after across seed subsets and ddof conventions.
"""
import json, itertools
import numpy as np

# Ground truth binary dynamic degree from task 68 scores:
# Base held ball:
# Ball 1 seeds 1-4: [0, 1, 1, 1]
# Ball 2 seeds 1-4: [1, 1, 1, 1]
# Recipe midfall:
# Ball 1 seeds 1-4: [0, 1, 0, 0]
# Ball 2 seeds 1-4: [0, 1, 0, 1]

dd_base = {
    1: [0, 1, 1, 1],
    2: [1, 1, 1, 1]
}
dd_recipe = {
    1: [0, 1, 0, 0],
    2: [0, 1, 0, 1]
}

# Real GAUGE optical flow reference dd_ref = 0.0 (gauge_real_matched.json)
dd_ref = 0.0

def calc_prompt(dd_triplet, ddof=0):
    avg = float(np.mean(dd_triplet))
    var = float(sum((x - avg)**2 for x in dd_triplet) / (3 - ddof))
    denom = var + avg**2
    mc = var / denom if denom > 0 else 0.0
    return avg, var, mc

def calc_mf(dd_dict, triplet_b1, triplet_b2, ddof=0):
    dd_b1 = [dd_dict[1][s-1] for s in triplet_b1]
    dd_b2 = [dd_dict[2][s-1] for s in triplet_b2]
    
    avg1, var1, mc1 = calc_prompt(dd_b1, ddof)
    avg2, var2, mc2 = calc_prompt(dd_b2, ddof)
    
    dd_gen = (avg1 + avg2) / 2.0
    mc = (mc1 + mc2) / 2.0
    mf = (1.0 - abs(dd_gen - dd_ref)) * (1.0 - mc)
    return dd_gen, mc, mf

triplets = list(itertools.combinations([1, 2, 3, 4], 3))

results = []

for t1 in triplets:
    for t2 in triplets:
        dd_g_base, mc_base, mf_base = calc_mf(dd_base, t1, t2, ddof=0)
        dd_g_rec, mc_rec, mf_rec = calc_mf(dd_recipe, t1, t2, ddof=0)
        d_mf = mf_rec - mf_base
        results.append({
            "t_b1": t1, "t_b2": t2,
            "base": {"dd": dd_g_base, "mc": mc_base, "mf": mf_base},
            "recipe": {"dd": dd_g_rec, "mc": mc_rec, "mf": mf_rec},
            "delta_mf": d_mf
        })

delta_mfs = [r["delta_mf"] for r in results]
mf_bases = [r["base"]["mf"] for r in results]
mf_recs = [r["recipe"]["mf"] for r in results]
mc_bases = [r["base"]["mc"] for r in results]
mc_recs = [r["recipe"]["mc"] for r in results]

print(f"=== MOTION FIDELITY ALL 16 SEED COMBINATIONS (ddof=0) ===")
print(f"Δ(MF): min={min(delta_mfs):+.4f}, max={max(delta_mfs):+.4f}, mean={np.mean(delta_mfs):+.4f} ± {np.std(delta_mfs):.4f}")
print(f"16/16 combinations Δ(MF) > 0: {all(d > 0 for d in delta_mfs)}")
print(f"Baseline MF: {np.mean(mf_bases):.4f} (range [{min(mf_bases):.4f}, {max(mf_bases):.4f}])")
print(f"Recipe MF:   {np.mean(mf_recs):.4f} (range [{min(mf_recs):.4f}, {max(mf_recs):.4f}])")
print(f"Baseline MC (variance penalty): {np.mean(mc_bases):.4f} (range [{min(mc_bases):.4f}, {max(mc_bases):.4f}])")
print(f"Recipe MC (variance penalty):   {np.mean(mc_recs):.4f} (range [{min(mc_recs):.4f}, {max(mc_recs):.4f}])")
