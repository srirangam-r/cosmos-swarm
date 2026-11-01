#!/usr/bin/env python3
"""
Task 221 Independent Replication and Methodological Review:
Sensitivity of Pendulum Amplitude Correction to Projection and Off-Vertical Swing Centres.

Evaluates Finding #4597 (rahul) based on published turning-point datasets:
  - work/rahul-api-2/t205/amp_results.json
  - work/rahul-api-2/t213/amp_t193.json
"""

import json
import os
import sys
import numpy as np
from scipy.stats import pearsonr, spearmanr
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. Independent Arithmetic-Geometric Mean (AGM) Elliptic Integral
# ---------------------------------------------------------
def agm_ellipk(m):
    """
    Computes complete elliptic integral of the first kind K(m) via AGM.
    m = k^2 = sin^2(A / 2).
    """
    m = np.asarray(m, float)
    scalar = m.ndim == 0
    m = np.atleast_1d(m)
    out = np.zeros_like(m)
    for idx, val in enumerate(m):
        if val < 0.0 or val >= 1.0:
            out[idx] = np.nan
            continue
        a = 1.0
        b = np.sqrt(1.0 - val)
        while np.abs(a - b) > 1e-15:
            a, b = (a + b) / 2.0, np.sqrt(a * b)
        out[idx] = np.pi / (2.0 * a)
    return out[0] if scalar else out

def F_elliptic(A_deg):
    """
    Correction factor F(A) = (2 / pi) * K(sin^2(A / 2)).
    A_deg is amplitude in degrees.
    """
    A_deg = np.asarray(A_deg, float)
    A_clamped = np.clip(A_deg, 0.0, 179.5)
    m = np.sin(np.radians(A_clamped) / 2.0)**2
    return (2.0 / np.pi) * agm_ellipk(m)

# ---------------------------------------------------------
# 2. Angle Projection and Excursion Functions
# ---------------------------------------------------------
def project_angle(theta_deg, k=1.0):
    """
    Projection transform: tan(theta_img) = k * tan(theta_true)
    => theta_true = arctan(tan(theta_img) / k)
    k = cos(alpha) where alpha is out-of-plane inclination angle.
    """
    th_rad = np.radians(theta_deg)
    th_true_rad = np.arctan(np.tan(th_rad) / k)
    return np.degrees(th_true_rad)

def compute_amplitude(turning_points, mode='hc', k=1.0, off=0.0):
    """
    Computes angular amplitude from turning points under projection k and offset off:
      - 'hc': half peak-to-peak amplitude (median(|diff|)/2) - invariant to constant offset.
      - 'side': median(|theta - off|) - distance from offset equilibrium.
      - 'max': max(|theta - off|) - maximum excursion.
    """
    th = project_angle(np.array(turning_points, float), k=k)
    if mode == 'hc':
        diffs = np.abs(np.diff(th)) / 2.0
        return float(np.median(diffs)) if len(diffs) >= 1 else np.nan
    elif mode == 'side':
        return float(np.median(np.abs(th - off)))
    elif mode == 'max':
        return float(np.max(np.abs(th - off)))
    else:
        raise ValueError(f"Unknown mode {mode}")

# ---------------------------------------------------------
# 3. Data Loading and Filtering
# ---------------------------------------------------------
def load_and_filter_data(repo_root):
    f1 = os.path.join(repo_root, 'work/rahul-api-2/t205/amp_results.json')
    f2 = os.path.join(repo_root, 'work/rahul-api-2/t213/amp_t193.json')
    
    per = {}
    for path in [f1, f2]:
        with open(path, 'r') as fp:
            data = json.load(fp)
            for k, v in data['per_clip'].items():
                # Harmonize prefix: rpr_p10f93_base_s21..25 duplicate k191_p10f93_base_s21..25
                canonical_key = k.replace('rpr_', 'k191_')
                per[canonical_key] = v
                
    real_key = 'real_pend10_f93'
    if real_key not in per:
        raise KeyError(f"Real reference {real_key} not found in input data.")
    real_data = per[real_key]
    
    # Filter 21 eligible pend10 clips:
    # input == 'pend10', my_r2 >= 0.8, finite kiro_T and A_hc
    eligible_names = sorted([
        n for n, v in per.items()
        if not n.startswith('real')
        and v.get('input') == 'pend10'
        and v.get('kiro_T') is not None
        and v.get('my_r2', 0) >= 0.8
        and np.isfinite(v.get('A_hc', np.nan))
    ])
    
    return per, real_data, eligible_names

# ---------------------------------------------------------
# 4. Statistical Estimation and Bootstrap
# ---------------------------------------------------------
def geo_mean(arr):
    arr = np.asarray(arr, float)
    return float(np.exp(np.mean(np.log(arr))))

def bootstrap_ci(arr, n_boot=10000, ci=0.95, seed=42):
    rng = np.random.default_rng(seed)
    arr = np.asarray(arr, float)
    boot_means = []
    n = len(arr)
    for _ in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means.append(np.exp(np.mean(np.log(sample))))
    alpha = (1.0 - ci) / 2.0
    return float(np.percentile(boot_means, alpha * 100)), float(np.percentile(boot_means, (1.0 - alpha) * 100))

# ---------------------------------------------------------
# Main Analysis Pipeline
# ---------------------------------------------------------
def main():
    repo_root = '/home/nail/swarm-work/agy-2/cosmos-swarm'
    output_dir = os.path.join(repo_root, 'work/agy-2/task221_pendulum_amplitude_review')
    plots_dir = os.path.join(output_dir, 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    per, real_data, names = load_and_filter_data(repo_root)
    n_clips = len(names)
    print(f"Loaded {n_clips} eligible clips for Task 221 replication.")
    assert n_clips == 21, f"Expected 21 clips, got {n_clips}"
    
    # Real reference parameters
    T_real = float(real_data['kiro_T']) # 1.17 s
    turns_real = real_data['turn_theta']
    A_real_hc = compute_amplitude(turns_real, 'hc', k=1.0)
    F_real_hc = F_elliptic(A_real_hc)
    
    print(f"Real GAUGE reference: T = {T_real:.3f} s, A_hc = {A_real_hc:.2f}°, F(A) = {F_real_hc:.4f}")
    
    # Raw period ratios
    raw_ratios = np.array([per[n]['kiro_T'] / T_real for n in names])
    raw_geo = geo_mean(raw_ratios)
    raw_ci = bootstrap_ci(raw_ratios)
    print(f"Raw Nano/Real ratio: geo-mean = {raw_geo:.4f}, 95% CI [{raw_ci[0]:.3f}, {raw_ci[1]:.3f}], range [{raw_ratios.min():.3f}, {raw_ratios.max():.3f}]")
    
    # Amplitude correlation with period
    amps_hc = np.array([per[n]['A_hc'] for n in names])
    periods = np.array([per[n]['kiro_T'] for n in names])
    r_pearson, p_pearson = pearsonr(amps_hc, periods)
    rho_spearman, p_spearman = spearmanr(amps_hc, periods)
    print(f"Correlation (A_hc vs T): Pearson r = {r_pearson:.4f} (p={p_pearson:.4f}), Spearman rho = {rho_spearman:.4f} (p={p_spearman:.4f})")
    
    def eval_contrast(mode_n, mode_r, kn, kr, off=0.0):
        Ar = compute_amplitude(turns_real, mode=mode_r, k=kr, off=off)
        Fr = F_elliptic(Ar)
        ratios = []
        for n in names:
            v = per[n]
            An = compute_amplitude(v['turn_theta'], mode=mode_n, k=kn, off=off)
            Fn = F_elliptic(An)
            T0_nano = v['kiro_T'] / Fn
            T0_real = T_real / Fr
            ratios.append(T0_nano / T0_real)
        ratios = np.array(ratios)
        gm = geo_mean(ratios)
        ci = bootstrap_ci(ratios)
        return {
            'geo_mean': float(gm),
            'min': float(ratios.min()),
            'max': float(ratios.max()),
            'ci95': [float(ci[0]), float(ci[1])],
            'per_clip': [float(x) for x in ratios]
        }
        
    results = {
        'n_clips': n_clips,
        'raw_ratio': {
            'geo_mean': float(raw_geo),
            'min': float(raw_ratios.min()),
            'max': float(raw_ratios.max()),
            'ci95': [float(raw_ci[0]), float(raw_ci[1])]
        },
        'correlation_A_vs_T': {
            'pearson_r': float(r_pearson),
            'pearson_p': float(p_pearson),
            'spearman_rho': float(rho_spearman),
            'spearman_p': float(p_spearman)
        },
        'scenarios': {}
    }
    
    # Baseline replication (hc, k=1, off=0)
    baseline = eval_contrast('hc', 'hc', 1.0, 1.0, 0.0)
    results['scenarios']['baseline_k1'] = baseline
    print(f"Baseline (hc, k=1): geo-mean = {baseline['geo_mean']:.4f}, range [{baseline['min']:.2f}, {baseline['max']:.2f}]")
    
    # [A] Same-camera projection sweep k in [0.4, 1.0]
    k_vals = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4]
    same_k_res = {}
    for k in k_vals:
        res = eval_contrast('hc', 'hc', k, k, 0.0)
        same_k_res[f"k_{k:.2f}"] = res
        print(f"  Shared k={k:.2f}: geo-mean = {res['geo_mean']:.4f} [{res['min']:.2f}, {res['max']:.2f}]")
    results['scenarios']['same_camera_projection'] = same_k_res
    
    # [B] Nano-only projection sweep (kn in [0.4, 1.0], kr = 1.0)
    nano_k_res = {}
    for kn in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]:
        res = eval_contrast('hc', 'hc', kn, 1.0, 0.0)
        nano_k_res[f"kn_{kn:.2f}"] = res
        print(f"  Nano-only kn={kn:.2f}: geo-mean = {res['geo_mean']:.4f} [{res['min']:.2f}, {res['max']:.2f}]")
    results['scenarios']['nano_only_projection'] = nano_k_res
    
    # [C] Off-vertical centre offset (-20° to +20°)
    off_vals = list(range(-20, 21, 5))
    off_res = {}
    for off in off_vals:
        res = eval_contrast('side', 'side', 1.0, 1.0, float(off))
        off_res[f"off_{off:+03d}"] = res
        print(f"  Offset off={off:+03d}°: geo-mean = {res['geo_mean']:.4f}")
    results['scenarios']['off_vertical_centre'] = off_res
    
    # [D] Largest excursion ('max')
    max_res = {}
    for off in [0, 5, 10, 15]:
        res = eval_contrast('max', 'max', 1.0, 1.0, float(off))
        max_res[f"max_off_{off:+03d}"] = res
        print(f"  Max-excursion off={off:+03d}°: geo-mean = {res['geo_mean']:.4f}")
    results['scenarios']['max_excursion_both'] = max_res
    
    # [E] Generous: Nano max vs Real hc
    gen_max = eval_contrast('max', 'hc', 1.0, 1.0, 0.0)
    results['scenarios']['generous_max_vs_hc'] = gen_max
    print(f"  Generous (Nano max, Real hc): geo-mean = {gen_max['geo_mean']:.4f} [{gen_max['min']:.2f}, {gen_max['max']:.2f}]")
    
    # [F] Combined generous: Nano max & kn=0.7 vs Real hc & kr=1.0
    gen_comb = eval_contrast('max', 'hc', 0.7, 1.0, 0.0)
    results['scenarios']['generous_combined_kn0.7'] = gen_comb
    print(f"  Combined Generous (Nano max kn=0.7, Real hc kr=1.0): geo-mean = {gen_comb['geo_mean']:.4f}")
    
    # [G] Theoretical Inversion: Required Amplitude A_needed
    per_clip_table = []
    a_needed_list = []
    for n in names:
        v = per[n]
        Rr = v['kiro_T'] / T_real
        Fn_need = Rr * F_real_hc
        try:
            A_need = brentq(lambda a: F_elliptic(a) - Fn_need, 1.0, 179.4)
        except Exception:
            A_need = np.nan
        per_clip_table.append({
            'clip_name': n,
            'T_raw': float(v['kiro_T']),
            'R_raw': float(Rr),
            'A_hc': float(v['A_hc']),
            'A_needed': float(A_need) if np.isfinite(A_need) else None
        })
        if np.isfinite(A_need):
            a_needed_list.append(A_need)
            
    a_needed_arr = np.array(a_needed_list)
    results['inversion_amplitude_needed'] = {
        'n_clips_total': n_clips,
        'n_clips_finite_needed': len(a_needed_arr),
        'n_clips_needed_ge_120': int(np.sum(a_needed_arr >= 120.0)),
        'n_clips_needed_ge_140': int(np.sum(a_needed_arr >= 140.0)),
        'median_needed': float(np.median(a_needed_arr)),
        'mean_needed': float(np.mean(a_needed_arr)),
        'min_needed': float(np.min(a_needed_arr)),
        'max_needed': float(np.max(a_needed_arr)),
        'per_clip': per_clip_table
    }
    print(f"Required Amplitude: median = {np.median(a_needed_arr):.1f}°, range [{np.min(a_needed_arr):.1f}°, {np.max(a_needed_arr):.1f}°]")
    print(f"  Clips needing A >= 120°: {np.sum(a_needed_arr >= 120.0)} / {len(a_needed_arr)}")
    
    # Save structured results
    results_path = os.path.join(output_dir, 'independent_sensitivity_results.json')
    with open(results_path, 'w') as fp:
        json.dump(results, fp, indent=2)
    print(f"Saved results to {results_path}")
    
    # ---------------------------------------------------------
    # 5. Publication Plots
    # ---------------------------------------------------------
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # Plot 1: Amplitude vs Period Scatter
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    ax.scatter(amps_hc, periods, color='#1f77b4', s=60, edgecolors='black', alpha=0.85, label='Cosmos3-Nano Clips (n=21)', zorder=4)
    ax.scatter([A_real_hc], [T_real], color='#d62728', s=120, marker='*', edgecolors='black', label='Real GAUGE pend10 (1.17 s, 67.9°)', zorder=5)
    
    # Theoretical physical curve T(theta) = T0 * F(theta) for T0 = 1.06 s (mocap baseline)
    theta_grid = np.linspace(5, 85, 100)
    T0_real_est = T_real / F_real_hc
    ax.plot(theta_grid, T0_real_est * F_elliptic(theta_grid), '--', color='#2ca02c', lw=2, label=f'Physical Harmonic Law: T = {T0_real_est:.2f} s · F(θ)')
    
    ax.set_xlabel('Angular Amplitude A (Half Peak-to-Peak, deg)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Oscillation Period T (s)', fontsize=11, fontweight='bold')
    ax.set_title('Period vs. Swing Amplitude in Cosmos3-Nano\nNull Correlation (r = +0.04, p = 0.86) Refutes Amplitude Dependence', fontsize=12, fontweight='bold')
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plot1_path = os.path.join(plots_dir, 'figure_amplitude_vs_period.png')
    plt.savefig(plot1_path)
    plt.close()
    
    # Plot 2: Projection & Offset Sensitivity Curves
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), dpi=300)
    
    # Subplot A: Projection k
    k_plot = np.array(k_vals)
    same_geo = [same_k_res[f"k_{k:.2f}"]['geo_mean'] for k in k_plot]
    same_ci_lo = [same_k_res[f"k_{k:.2f}"]['ci95'][0] for k in k_plot]
    same_ci_hi = [same_k_res[f"k_{k:.2f}"]['ci95'][1] for k in k_plot]
    
    ax1.plot(k_plot, same_geo, 'o-', color='#1f77b4', lw=2, label='Same-Camera (Real & Nano)')
    ax1.fill_between(k_plot, same_ci_lo, same_ci_hi, color='#1f77b4', alpha=0.15)
    
    kn_plot = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4])
    nano_geo = [nano_k_res[f"kn_{kn:.2f}"]['geo_mean'] for kn in kn_plot]
    ax1.plot(kn_plot, nano_geo, 's--', color='#ff7f0e', lw=2, label='Asymmetric (Nano-only, Real k=1)')
    
    ax1.axhline(raw_geo, color='gray', linestyle=':', label=f'Raw Uncorrected Ratio ({raw_geo:.2f}x)')
    ax1.axhline(1.0, color='red', linestyle='-', lw=1.5, label='Physical Parity (1.00x)')
    ax1.set_xlabel('Projection Factor k = cos(α) [1.0 = Frontal, 0.5 = 60° Tilt]', fontsize=10.5, fontweight='bold')
    ax1.set_ylabel('Corrected Ratio T_0(Nano) / T_0(Real)', fontsize=10.5, fontweight='bold')
    ax1.set_title('Sensitivity to Out-of-Plane Tilt (k)', fontsize=11, fontweight='bold')
    ax1.set_ylim(0.8, 2.0)
    ax1.legend(fontsize=9, frameon=True)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Subplot B: Centre Offset
    off_plot = np.array(off_vals)
    off_geo = [off_res[f"off_{off:+03d}"]['geo_mean'] for off in off_plot]
    off_ci_lo = [off_res[f"off_{off:+03d}"]['ci95'][0] for off in off_plot]
    off_ci_hi = [off_res[f"off_{off:+03d}"]['ci95'][1] for off in off_plot]
    
    ax2.plot(off_plot, off_geo, 'd-', color='#2ca02c', lw=2, label='Offset Equilibrium (|θ - θ_off|)')
    ax2.fill_between(off_plot, off_ci_lo, off_ci_hi, color='#2ca02c', alpha=0.15)
    ax2.axhline(baseline['geo_mean'], color='blue', linestyle='--', label=f'Baseline (k=1, off=0°: {baseline["geo_mean"]:.2f}x)')
    ax2.axhline(1.0, color='red', linestyle='-', lw=1.5, label='Physical Parity (1.00x)')
    ax2.set_xlabel('Equilibrium Angular Offset θ_off (deg)', fontsize=10.5, fontweight='bold')
    ax2.set_ylabel('Corrected Ratio T_0(Nano) / T_0(Real)', fontsize=10.5, fontweight='bold')
    ax2.set_title('Sensitivity to Equilibrium Centre Offset', fontsize=11, fontweight='bold')
    ax2.set_ylim(0.8, 2.0)
    ax2.legend(fontsize=9, frameon=True)
    ax2.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plot2_path = os.path.join(plots_dir, 'figure_projection_offset_sensitivity.png')
    plt.savefig(plot2_path)
    plt.close()
    
    # Plot 3: Observed vs Needed Amplitude
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    indices = np.arange(len(per_clip_table))
    obs_amps = [x['A_hc'] for x in per_clip_table]
    req_amps = [x['A_needed'] if x['A_needed'] is not None else 180.0 for x in per_clip_table]
    
    width = 0.35
    ax.bar(indices - width/2, obs_amps, width, label='Observed Amplitude A_hc (Mean 55.1°)', color='#1f77b4', alpha=0.85, edgecolor='black')
    ax.bar(indices + width/2, req_amps, width, label='Required Physical Amplitude A_needed (Median 151.0°)', color='#d62728', alpha=0.75, edgecolor='black')
    
    ax.axhline(90.0, color='black', linestyle=':', label='Horizontal Threshold (90°)')
    ax.set_ylabel('Amplitude (degrees)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Clip Index (n=21 Eligible Cosmos3-Nano Clips)', fontsize=11, fontweight='bold')
    ax.set_title('Physical Impossibility: Observed vs. Required Amplitude\nExplaining Nano Period Slowdown Requires Impossible Excursions (127°–169°)', fontsize=11.5, fontweight='bold')
    ax.set_xticks(indices)
    ax.set_xticklabels([f"C{i+1}" for i in range(len(indices))], fontsize=8.5)
    ax.set_ylim(0, 195)
    ax.legend(frameon=True, fontsize=9.5, loc='upper left')
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plot3_path = os.path.join(plots_dir, 'figure_observed_vs_needed_amplitude.png')
    plt.savefig(plot3_path)
    plt.close()
    
    print(f"Generated 3 publication plots in {plots_dir}")

if __name__ == '__main__':
    main()
