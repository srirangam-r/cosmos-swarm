#!/usr/bin/env python3
"""
Analyze ball GROWTH within each clip (end diameter / f0 diameter).
This avoids the cross-resolution calibration issue.
"""
import json
import numpy as np
from pathlib import Path
from scipy import stats

def main():
    work_dir = Path(__file__).parent
    results_dir = work_dir / 'results'
    
    # Load tracking summary
    with open(results_dir / 'all_tracks_summary.json') as f:
        tracks = json.load(f)
    
    print("=== Ball Diameter Growth Analysis ===\n")
    
    # Compute growth ratio (d_end / d_f0) for each clip
    growth_by_arm = {'F': [], 'QT': [], 'N': []}
    
    for clip_name, data in tracks.items():
        arm = data['arm']
        d_f0 = data['d_f0']
        d_end = data['d_end']
        
        if d_f0 and d_end and d_f0 > 0:
            growth = d_end / d_f0
            growth_by_arm[arm].append({
                'clip': clip_name,
                'scene': data['scene'],
                'seed': data['seed'],
                'd_f0': d_f0,
                'd_end': d_end,
                'growth': growth
            })
    
    # Statistics per arm
    for arm in ['F', 'QT', 'N']:
        data_list = growth_by_arm[arm]
        if not data_list:
            continue
        
        growth_ratios = np.array([d['growth'] for d in data_list])
        d_f0_values = np.array([d['d_f0'] for d in data_list])
        d_end_values = np.array([d['d_end'] for d in data_list])
        
        print(f"Arm {arm} (n={len(data_list)} clips):")
        print(f"  f0 diameter:  {d_f0_values.mean():.1f} ± {d_f0_values.std():.1f} px (range {d_f0_values.min():.0f}-{d_f0_values.max():.0f})")
        print(f"  end diameter: {d_end_values.mean():.1f} ± {d_end_values.std():.1f} px (range {d_end_values.min():.0f}-{d_end_values.max():.0f})")
        print(f"  growth ratio: {growth_ratios.mean():.2f} ± {growth_ratios.std():.2f} (range {growth_ratios.min():.2f}-{growth_ratios.max():.2f})")
        
        # Bootstrap CI
        n_boot = 1000
        boot_means = []
        for _ in range(n_boot):
            boot_sample = np.random.choice(growth_ratios, size=len(growth_ratios), replace=True)
            boot_means.append(np.mean(boot_sample))
        
        ci_low = np.percentile(boot_means, 2.5)
        ci_high = np.percentile(boot_means, 97.5)
        print(f"  95% CI: [{ci_low:.2f}, {ci_high:.2f}]")
        print()
    
    # Test if growth differs between arms
    f_growth = np.array([d['growth'] for d in growth_by_arm['F']])
    qt_growth = np.array([d['growth'] for d in growth_by_arm['QT']])
    n_growth = np.array([d['growth'] for d in growth_by_arm['N']])
    
    print("=== Statistical Tests ===")
    
    # F vs QT
    t_stat, p_val = stats.ttest_ind(f_growth, qt_growth)
    print(f"F vs QT: t={t_stat:.2f}, p={p_val:.4f}")
    
    # F vs N
    t_stat, p_val = stats.ttest_ind(f_growth, n_growth)
    print(f"F vs N:  t={t_stat:.2f}, p={p_val:.4f}")
    
    # QT vs N
    t_stat, p_val = stats.ttest_ind(qt_growth, n_growth)
    print(f"QT vs N: t={t_stat:.2f}, p={p_val:.4f}")
    
    # Save results
    output = {
        'F': {
            'n': len(growth_by_arm['F']),
            'mean_growth': float(f_growth.mean()),
            'std_growth': float(f_growth.std()),
            'ci_95': [float(np.percentile(f_growth, 2.5)), float(np.percentile(f_growth, 97.5))],
            'mean_d_f0': float(np.mean([d['d_f0'] for d in growth_by_arm['F']])),
            'mean_d_end': float(np.mean([d['d_end'] for d in growth_by_arm['F']]))
        },
        'QT': {
            'n': len(growth_by_arm['QT']),
            'mean_growth': float(qt_growth.mean()),
            'std_growth': float(qt_growth.std()),
            'ci_95': [float(np.percentile(qt_growth, 2.5)), float(np.percentile(qt_growth, 97.5))],
            'mean_d_f0': float(np.mean([d['d_f0'] for d in growth_by_arm['QT']])),
            'mean_d_end': float(np.mean([d['d_end'] for d in growth_by_arm['QT']]))
        },
        'N': {
            'n': len(growth_by_arm['N']),
            'mean_growth': float(n_growth.mean()),
            'std_growth': float(n_growth.std()),
            'ci_95': [float(np.percentile(n_growth, 2.5)), float(np.percentile(n_growth, 97.5))],
            'mean_d_f0': float(np.mean([d['d_f0'] for d in growth_by_arm['N']])),
            'mean_d_end': float(np.mean([d['d_end'] for d in growth_by_arm['N']]))
        }
    }
    
    with open(results_dir / 'growth_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to {results_dir}/growth_analysis.json")

if __name__ == '__main__':
    main()
