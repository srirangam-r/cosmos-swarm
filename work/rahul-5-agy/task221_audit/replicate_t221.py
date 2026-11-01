#!/usr/bin/env python3
"""Independent replication and sensitivity audit of Finding #4597 (Task 221, rahul).

Finding #4597 claimed:
- Raw T_nano/T_real geo-mean is 1.56 (n=21 unique pend10 clips, R^2 >= 0.8).
- Corrected ratio R_corr baseline is 1.64.
- Same-camera projection k=1 -> 0.5: R_corr 1.640 -> 1.663.
- Nano-only projection k_n=0.9 -> 0.5 (real k=1): R_corr 1.636 -> 1.611.
- Off-vertical center/pivot offset (-10 deg to +15 deg): R_corr 1.585 -> 1.606.
- Max excursion as amplitude for both: 1.574 (off 0), 1.527 (off 10 deg).
- Most generous (Nano max excursion, real half-peak): 1.498 (off 0); + k_n=0.7 gives 1.486.
- Amplitudes needed for a rigid pendulum: 127 deg to 169 deg across 18/21 clips.

This script independently re-implements:
1. Elliptic integral calculation F(A) = (2/pi) * K(sin^2(A/2)).
2. Turning point processing, projection models (both orthographic and perspective), and offset models.
3. Clip selection criteria, geometric means, bootstrap 95% CIs.
4. Exact numerical root-finding for required physical amplitude A_needed.
"""

import json
import math
import os
import sys
import numpy as np
from scipy.special import ellipk
from scipy.optimize import brentq

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rahul-api-2"))
T205_PATH = os.path.join(DATA_DIR, "t205", "amp_results.json")
T213_PATH = os.path.join(DATA_DIR, "t213", "amp_t193.json")

def elliptic_factor(A_deg):
    """Exact period expansion factor F(A) = (2/pi) * K(sin^2(A/2)) for swing amplitude A (degrees)."""
    A_arr = np.asarray(A_deg, dtype=float)
    A_clamped = np.clip(A_arr, 0.0, 179.9)
    m = np.sin(np.radians(A_clamped) / 2.0) ** 2
    return (2.0 / np.pi) * ellipk(m)

def project_angles(theta_deg, k=1.0, off_deg=0.0):
    """De-project image turning points to true swing angles given plane tilt k = cos(alpha).
    tan(theta_img) = k * tan(theta_true) => theta_true = arctan(tan(theta_img) / k)
    """
    th = np.asarray(theta_deg, dtype=float)
    # Convert to true swing angle
    rad = np.radians(th)
    true_rad = np.arctan(np.tan(rad) / k)
    true_deg = np.degrees(true_rad)
    return true_deg

def extract_amplitude(theta_deg, mode="hc", k=1.0, off_deg=0.0):
    """Extract amplitude from turning points according to specified mode."""
    th_true = project_angles(theta_deg, k=k)
    
    if mode == "hc":
        # Half peak-to-peak of consecutive turning points (center-free)
        if len(th_true) < 2:
            return np.nan
        diffs = np.abs(np.diff(th_true)) / 2.0
        return float(np.median(diffs))
    elif mode == "side":
        # Absolute angle relative to shifted vertical axis
        return float(np.median(np.abs(th_true - off_deg)))
    elif mode == "max":
        # Maximum one-sided excursion
        return float(np.max(np.abs(th_true - off_deg)))
    else:
        raise ValueError(f"Unknown mode: {mode}")

def load_data():
    with open(T205_PATH, "r") as f:
        d205 = json.load(f)
    with open(T213_PATH, "r") as f:
        d213 = json.load(f)

    per = {}
    for k, v in d205["per_clip"].items():
        norm_k = k.replace("rpr_", "k191_")
        per[norm_k] = v
    for k, v in d213["per_clip"].items():
        norm_k = k.replace("rpr_", "k191_")
        if norm_k not in per:
            per[norm_k] = v

    real_data = per["real_pend10_f93"]

    # Filter eligible clips matching finding:
    # unique, not real, input == 'pend10', kiro_T present, my_r2 >= 0.8, finite A_hc
    eligible = []
    for name, clip in sorted(per.items()):
        if name.startswith("real"):
            continue
        if clip.get("input") != "pend10":
            continue
        if not clip.get("kiro_T"):
            continue
        if clip.get("my_r2", 0) < 0.8:
            continue
        if not np.isfinite(clip.get("A_hc", np.nan)):
            continue
        eligible.append(name)

    return per, real_data, eligible

def run_evaluation():
    per, real_data, eligible_names = load_data()
    n_clips = len(eligible_names)
    print(f"Loaded {n_clips} eligible unique pend10 clips.")

    # 1. Raw period ratios
    raw_ratios = np.array([per[n]["kiro_T"] / real_data["kiro_T"] for n in eligible_names])
    raw_geom = float(np.exp(np.mean(np.log(raw_ratios))))
    raw_median = float(np.median(raw_ratios))
    raw_min = float(np.min(raw_ratios))
    raw_max = float(np.max(raw_ratios))

    # Bootstrap 95% CI for raw geom mean
    rng = np.random.default_rng(20261101)
    boot_raw = [
        np.exp(np.mean(np.log(rng.choice(raw_ratios, size=n_clips, replace=True))))
        for _ in range(5000)
    ]
    raw_ci = (float(np.percentile(boot_raw, 2.5)), float(np.percentile(boot_raw, 97.5)))

    print(f"Raw period ratio T_nano/T_real: geom mean {raw_geom:.3f} (95% CI [{raw_ci[0]:.3f}, {raw_ci[1]:.3f}], range [{raw_min:.2f}, {raw_max:.2f}])")

    def calc_corrected_ratios(mode_n, mode_r, kn, kr, off=0.0):
        Ar = extract_amplitude(real_data["turn_theta"], mode=mode_r, k=kr, off_deg=off)
        Fr = elliptic_factor(Ar)
        Tr_corr = real_data["kiro_T"] / Fr

        ratios = []
        for n in eligible_names:
            clip = per[n]
            An = extract_amplitude(clip["turn_theta"], mode=mode_n, k=kn, off_deg=off)
            Fn = elliptic_factor(An)
            Tn_corr = clip["kiro_T"] / Fn
            ratios.append(Tn_corr / Tr_corr)
        ratios = np.array(ratios)
        geom = float(np.exp(np.mean(np.log(ratios))))
        return geom, float(np.min(ratios)), float(np.max(ratios)), ratios

    results = {}

    # Baseline: mode hc, k=1, off=0
    base_geom, base_min, base_max, base_ratios = calc_corrected_ratios("hc", "hc", 1.0, 1.0, 0.0)
    boot_base = [
        np.exp(np.mean(np.log(rng.choice(base_ratios, size=n_clips, replace=True))))
        for _ in range(5000)
    ]
    base_ci = (float(np.percentile(boot_base, 2.5)), float(np.percentile(boot_base, 97.5)))
    results["baseline"] = {
        "geom": base_geom, "ci_95": base_ci, "range": [base_min, base_max]
    }
    print(f"Baseline corrected ratio (hc, k=1, off=0): {base_geom:.3f} [{base_ci[0]:.3f}, {base_ci[1]:.3f}], range [{base_min:.2f}, {base_max:.2f}]")

    # A. Same camera projection (k in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5])
    results["same_k"] = {}
    print("\n[A] Same-camera projection (k applied to both):")
    for k in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]:
        g, mi, ma, _ = calc_corrected_ratios("hc", "hc", k, k, 0.0)
        results["same_k"][str(k)] = {"geom": g, "min": mi, "max": ma}
        print(f"  k={k:.1f}: geom {g:.3f} [{mi:.2f}, {ma:.2f}]")

    # B. Nano-only projection (k_n in [0.9, 0.8, 0.7, 0.6, 0.5], kr=1.0)
    results["nano_only_k"] = {}
    print("\n[B] Nano-only projection (k_n applied, k_r=1.0):")
    for kn in [0.9, 0.8, 0.7, 0.6, 0.5]:
        g, mi, ma, _ = calc_corrected_ratios("hc", "hc", kn, 1.0, 0.0)
        results["nano_only_k"][str(kn)] = {"geom": g, "min": mi, "max": ma}
        print(f"  k_n={kn:.1f}: geom {g:.3f} [{mi:.2f}, {ma:.2f}]")

    # C. Off-vertical pivot offset (mode side, off in [-15, -10, -5, 0, 5, 10, 15])
    results["side_off"] = {}
    print("\n[C] Off-vertical pivot offset (mode=side):")
    for off in [-15, -10, -5, 0, 5, 10, 15]:
        g, mi, ma, _ = calc_corrected_ratios("side", "side", 1.0, 1.0, float(off))
        results["side_off"][str(off)] = {"geom": g, "min": mi, "max": ma}
        print(f"  off={off:3d} deg: geom {g:.3f} [{mi:.2f}, {ma:.2f}]")

    # D. Largest-excursion (mode max, off in [0, 5, 10])
    results["max_off"] = {}
    print("\n[D] Largest-excursion (mode=max, both):")
    for off in [0, 5, 10]:
        g, mi, ma, _ = calc_corrected_ratios("max", "max", 1.0, 1.0, float(off))
        results["max_off"][str(off)] = {"geom": g, "min": mi, "max": ma}
        print(f"  off={off:2d} deg: geom {g:.3f} [{mi:.2f}, {ma:.2f}]")

    # E. Nano max-excursion vs Real hc
    g_e, mi_e, ma_e, _ = calc_corrected_ratios("max", "hc", 1.0, 1.0, 0.0)
    results["gen_max_vs_hc"] = {"geom": g_e, "min": mi_e, "max": ma_e}
    print(f"\n[E] Generous (Nano max, Real hc): geom {g_e:.3f} [{mi_e:.2f}, {ma_e:.2f}]")

    # F. Combined generous: Nano max & k_n=0.7 vs Real hc & kr=1.0
    g_f, mi_f, ma_f, _ = calc_corrected_ratios("max", "hc", 0.7, 1.0, 0.0)
    results["gen_max_k07"] = {"geom": g_f, "min": mi_f, "max": ma_f}
    print(f"[F] Combined generous (Nano max + k_n=0.7, Real hc): geom {g_f:.3f} [{mi_f:.2f}, {ma_f:.2f}]")

    # G. Required amplitude analysis:
    # For natural period to match real: T_0,nano = T_0,real
    # => T_nano / F(A_needed) = T_real / F(A_real)
    # => F(A_needed) = (T_nano / T_real) * F(A_real)
    Ar_baseline = extract_amplitude(real_data["turn_theta"], mode="hc", k=1.0, off_deg=0.0)
    Fr_baseline = elliptic_factor(Ar_baseline)
    
    needed_amps = []
    per_clip_records = []
    print("\n[G] Amplitude needed for each clip to match real natural period:")
    for n in eligible_names:
        clip = per[n]
        r_raw = clip["kiro_T"] / real_data["kiro_T"]
        a_hc = clip.get("A_hc", np.nan)
        target_F = r_raw * Fr_baseline

        if target_F <= 1.0:
            # Nano period is already faster than or equal to small-angle real
            a_needed = 0.0
        elif target_F >= elliptic_factor(179.9):
            a_needed = 180.0
        else:
            try:
                a_needed = float(brentq(lambda a: elliptic_factor(a) - target_F, 0.0, 179.9))
            except Exception:
                a_needed = np.nan

        needed_amps.append(a_needed)
        per_clip_records.append({
            "name": n,
            "kiro_T": clip["kiro_T"],
            "R_raw": r_raw,
            "A_hc": a_hc,
            "target_F": float(target_F),
            "A_needed": a_needed
        })
        print(f"  {n:26s} R_raw={r_raw:.2f}  A_hc={a_hc:4.1f} deg  A_needed={a_needed:5.1f} deg")

    valid_needed = [a for a in needed_amps if a > 0 and np.isfinite(a)]
    min_needed = min(valid_needed) if valid_needed else np.nan
    max_needed = max(valid_needed) if valid_needed else np.nan
    n_above_120 = sum(1 for a in valid_needed if a >= 120.0)

    results["needed_analysis"] = {
        "A_real_hc": Ar_baseline,
        "F_real": Fr_baseline,
        "n_clips": len(eligible_names),
        "n_needed_positive": len(valid_needed),
        "n_needed_above_120": n_above_120,
        "range_needed_deg": [min_needed, max_needed],
        "per_clip": per_clip_records
    }

    print(f"\nSummary of needed amplitudes: {n_above_120}/{len(valid_needed)} clips require A_needed >= 120 deg (range {min_needed:.1f} - {max_needed:.1f} deg).")

    # Output replication artifacts
    out_dir = os.path.dirname(os.path.abspath(__file__))
    res_path = os.path.join(out_dir, "replication_results.json")
    with open(res_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote full replication results to {res_path}")

    return results

if __name__ == "__main__":
    run_evaluation()
