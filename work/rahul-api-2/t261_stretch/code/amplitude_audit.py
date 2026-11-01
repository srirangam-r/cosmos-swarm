"""
Amplitude Audit & Nonlinear Period Elongation Evaluation for Task 261 / Finding #5561
Evaluates complete elliptic integral factors K(theta_0) across the 10 eligible Primary clips
and compares against the real mocap reference (real_pend10_f93).
"""

import json
from pathlib import Path
import numpy as np
from scipy.special import ellipk
from scipy.stats import spearmanr, pearsonr

REPO_ROOT = Path(__file__).resolve().parents[4]
RESULTS_JSON = REPO_ROOT / "work/rahul-api-2/t261_stretch/results.json"
ANGLES_JSON = REPO_ROOT / "work/rahul-api-2/t261_stretch/angles_primary10.json"
REAL_JSON = REPO_ROOT / "work/kiro-1/t191/real.json"

def ellip_factor(amp_deg):
    amp_rad = np.radians(amp_deg)
    m = np.sin(amp_rad / 2.0) ** 2
    if m >= 1.0:
        return np.nan
    return (2.0 / np.pi) * ellipk(m)

def main():
    with open(RESULTS_JSON) as f:
        res = json.load(f)
    
    with open(ANGLES_JSON) as f:
        angles_data = json.load(f)

    with open(REAL_JSON) as f:
        real_data = json.load(f)

    real_th = np.array(real_data["real_pend10_f93"]["series"]["theta"])
    real_amp_ptp = 0.5 * (np.nanmax(real_th) - np.nanmin(real_th))
    K_real = ellip_factor(real_amp_ptp)
    T_real = 1.1735501872474754

    print(f"Real pend10 baseline:")
    print(f"  PTP/2 amplitude: {real_amp_ptp:.2f} deg")
    print(f"  K(theta_0) factor: {K_real:.4f} (+{(K_real - 1.0)*100:.2f}% elongation over T0)")
    print(f"  Mocap period T_real: {T_real:.4f} s\n")

    all_rows = {r["clip"]: r for r in res["all_rows"]}
    prim_clips = [c["clip"] for c in res["PRIMARY"]["clips"]]

    print(f"{'Clip':<20} {'T_mp':<8} {'S':<8} {'theta_0':<10} {'K_ratio':<10} {'ratio_geom':<12} {'ratio_all':<12}")
    print("-" * 84)

    records = []
    for cname in prim_clips:
        r = all_rows[cname]
        th = np.array(angles_data[cname]["series_theta"])
        amp = 0.5 * (np.nanmax(th) - np.nanmin(th))
        k_nano = ellip_factor(amp)
        k_ratio = k_nano / K_real

        T_mp = r["T_mp"]
        S = r["S"]
        rg = T_mp / (T_real * np.sqrt(1.0 + S))
        ra = rg / k_ratio

        records.append({
            "clip": cname,
            "T_mp": T_mp,
            "S": S,
            "theta_0_deg": amp,
            "k_nano": k_nano,
            "k_ratio": k_ratio,
            "ratio_geom": rg,
            "ratio_all": ra,
            "is_e3": cname.startswith("N_E3")
        })

        print(f"{cname:<20} {T_mp:<8.3f} {S:<+8.3f} {amp:<10.2f} {k_ratio:<10.4f} {rg:<12.4f} {ra:<12.4f}")

    print("\nSummary Statistics:")
    pooled_r_all = [rec["ratio_all"] for rec in records]
    e3_r_all = [rec["ratio_all"] for rec in records if rec["is_e3"]]

    print(f"  Pooled Median Residual (n={len(records)}): {np.median(pooled_r_all):.4f}x (+{(np.median(pooled_r_all)-1.0)*100:.1f}%)")
    print(f"  E3-only Median Residual (n={len(e3_r_all)}): {np.median(e3_r_all):.4f}x (+{(np.median(e3_r_all)-1.0)*100:.1f}%)")
    
    k_rats = [rec["k_ratio"] for rec in records]
    r_geoms = [rec["ratio_geom"] for rec in records]
    sp = spearmanr(k_rats, r_geoms)
    print(f"  Spearman rho(K_ratio, ratio_geom): {sp.statistic:.3f} (p={sp.pvalue:.3f})")

if __name__ == "__main__":
    main()
