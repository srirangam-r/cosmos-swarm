#!/usr/bin/env python3
import json
import numpy as np

with open("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/replication_results.json") as f:
    d = json.load(f)

print("=== PIXEL COMPARISON ===")
for k, v in d["pairs"].items():
    f0 = v['f0_mad']
    m = v['mad_10_92']
    p_roi = v['pend_roi_mad']
    bg_roi = v['bg_roi_mad']
    print(f"{k}: f0_mad={f0:.4f}, mad_10_92={m:.3f}, pend_roi={p_roi:.3f}, bg_roi={bg_roi:.3f}")

mads = [v["mad_10_92"] for v in d["pairs"].values()]
print(f"\nMean MAD (10-92): {np.mean(mads):.3f} +/- {np.std(mads)/np.sqrt(len(mads)):.3f}, range [{np.min(mads):.3f}, {np.max(mads):.3f}]")
print(f"Between-seed MAD: {d['pixel_summary']['between_seed_mad_mean']:.3f} (range {d['pixel_summary']['between_seed_mad_range']})")

print("\n=== PERIOD COMPARISON ===")
print(f"{'Pair':12} | {'nv mp_T':>8} | {'kar mp_T':>8} | {'Delta mp_T':>10} | {'nv acf_T':>8} | {'kar acf_T':>8} | {'Delta acf_T':>11} | {'Flags':>10}")
print("-" * 85)
for k, v in d["pairs"].items():
    nv_mp = f"{v['nv_mp_T']:.3f}" if v['nv_mp_T'] is not None else "None"
    kar_mp = f"{v['kar_mp_T']:.3f}" if v['kar_mp_T'] is not None else "None"
    d_mp = f"{v['delta_mp']:+.3f}" if v['delta_mp'] is not None else "None"
    nv_acf = f"{v['nv_acf_T']:.3f}" if v['nv_acf_T'] is not None else "None"
    kar_acf = f"{v['kar_acf_T']:.3f}" if v['kar_acf_T'] is not None else "None"
    d_acf = f"{v['delta_acf']:+.3f}" if v['delta_acf'] is not None else "None"
    flg = f"{v['nv_flag']}/{v['kar_flag']}"
    print(f"{k:12} | {nv_mp:>8} | {kar_mp:>8} | {d_mp:>10} | {nv_acf:>8} | {kar_acf:>8} | {d_acf:>11} | {flg:>10}")

# Author comparisons:
# Author stated:
# acf/measure_pend periods (s) nv vs kar:
# pend10 s1-3: 0.84/0.74/0.23 vs 0.91/0.79/0.25
# pend11 s1-3: 0.83/0.53/1.65 vs 0.83/0.26/1.66
# Excluding pend11 s2, |Delta| = 0.07, 0.05, 0.02, 0.00, 0.01 s (n=5 pairs)
print("\n=== AUTHOR COMPARISON CHECK (ACF periods) ===")
for k in ["pend10_s1", "pend10_s2", "pend10_s3", "pend11_s1", "pend11_s2", "pend11_s3"]:
    v = d["pairs"][k]
    nv_a = v['nv_acf_T']
    kar_a = v['kar_acf_T']
    diff_a = abs(nv_a - kar_a) if nv_a and kar_a else None
    print(f"{k}: nv_acf={nv_a:.2f}, kar_acf={kar_a:.2f}, |Delta|={diff_a:.2f} s" if diff_a is not None else f"{k}: None")

valid_keys = [k for k in ["pend10_s1", "pend10_s2", "pend10_s3", "pend11_s1", "pend11_s3"]]
deltas_acf_5 = [abs(d["pairs"][k]['nv_acf_T'] - d["pairs"][k]['kar_acf_T']) for k in valid_keys]
print(f"\nAcross the 5 consistent pairs: |Delta_acf| values = {[round(x, 2) for x in deltas_acf_5]}")
print(f"Max |Delta_acf| = {np.max(deltas_acf_5):.2f} s, Mean |Delta_acf| = {np.mean(deltas_acf_5):.3f} s")

# Distance to real physical period (1.17 s for pend10, 1.18 s for pend11)
print("\n=== PHYSICAL PERIOD RECOVERY CHECK ===")
for k, v in d["pairs"].items():
    real = v["real_T"]
    nv_err = abs(v['nv_acf_T'] - real)
    kar_err = abs(v['kar_acf_T'] - real)
    print(f"{k} (real {real} s): |nv - real| = {nv_err:.3f} s, |kar - real| = {kar_err:.3f} s")
