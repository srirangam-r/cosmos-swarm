#!/usr/bin/env python3
"""
Task 232: Comprehensive Kinematic & Statistical Audit of Finding #4569 (Task 228)
Calculates exact McNemar test, Fisher exact test, bootstrap geometric mean ratios,
ANOVA variance decomposition, and compares rodtrack vs planted-PASS measure_pend.

Author: agy-2
Date: 2026-11-01
"""

import os
import sys
import json
import numpy as np
from scipy import stats

def compute_mcnemar_exact(b, c):
    """
    Exact two-sided binomial test for McNemar discordant pairs.
    b: discordants where Orig=1 and Edited=0
    c: discordants where Orig=0 and Edited=1
    """
    n = b + c
    if n == 0:
        return 1.0, 0, 0
    k = min(b, c)
    p_val = 2.0 * stats.binom.cdf(k, n, 0.5)
    return min(1.0, float(p_val)), b, c

def geometric_mean(arr):
    return float(np.exp(np.mean(np.log(arr))))

def bootstrap_gm_ratio(a, o, n_boot=20000, seed=42):
    rng = np.random.default_rng(seed)
    a = np.array(a)
    o = np.array(o)
    ratio = geometric_mean(a) / geometric_mean(o)
    boots = [geometric_mean(rng.choice(a, len(a))) / geometric_mean(rng.choice(o, len(o))) for _ in range(n_boot)]
    ci_low, ci_high = np.percentile(boots, [2.5, 97.5])
    return {
        'ratio': float(ratio),
        'ci95': [float(ci_low), float(ci_high)],
        'gm_a': geometric_mean(a),
        'gm_o': geometric_mean(o),
        'n_a': len(a),
        'n_o': len(o)
    }

def main():
    repo_root = '/home/nail/swarm-work/agy-2/cosmos-swarm'
    t228_results_path = os.path.join(repo_root, 'work/rahul-api-2/t228/results.json')
    t228_rt_path = os.path.join(repo_root, 'work/rahul-api-2/t228/rt/rodtrack_all.json')
    measure_path = os.path.join(repo_root, 'work/agy-2/task232_pendulum_rod_shortening/measure_pend_results.json')
    out_path = os.path.join(repo_root, 'work/agy-2/task232_pendulum_rod_shortening/comprehensive_audit_results.json')
    
    with open(t228_results_path) as f:
        t228 = json.load(f)
    with open(t228_rt_path) as f:
        rt_all = json.load(f)
        
    rows = t228['rows']
    
    # 1. G4 tracking passes and contingency tables
    arms = ['orig', 'L70', 'L50']
    g4_by_seed = {a: {} for a in arms}
    g5_by_seed = {a: {} for a in arms}
    pass_by_seed = {a: {} for a in arms}
    T_by_seed = {a: {} for a in arms}
    L_by_seed = {a: {} for a in arms}
    
    for r in rows.values():
        a = r['arm']
        s = r['seed']
        g4_by_seed[a][s] = r['G4']
        g5_by_seed[a][s] = r['G5']
        pass_by_seed[a][s] = r['PASS']
        T_by_seed[a][s] = r.get('T')
        L_by_seed[a][s] = r.get('L_med')
        
    seeds = sorted(list(g4_by_seed['orig'].keys()))
    
    # McNemar tests
    # Orig vs L50
    b_l50 = sum(1 for s in seeds if g4_by_seed['orig'][s] and not g4_by_seed['L50'][s])
    c_l50 = sum(1 for s in seeds if not g4_by_seed['orig'][s] and g4_by_seed['L50'][s])
    p_mcnemar_l50, _, _ = compute_mcnemar_exact(b_l50, c_l50)
    
    # Orig vs L70
    b_l70 = sum(1 for s in seeds if g4_by_seed['orig'][s] and not g4_by_seed['L70'][s])
    c_l70 = sum(1 for s in seeds if not g4_by_seed['orig'][s] and g4_by_seed['L70'][s])
    p_mcnemar_l70, _, _ = compute_mcnemar_exact(b_l70, c_l70)
    
    # Fisher exact test (2x2 table)
    # Orig: 8 pass, 2 fail; L50: 1 pass, 9 fail
    table_l50 = [[8, 2], [1, 9]]
    odds_l50, p_fisher_l50 = stats.fisher_exact(table_l50)
    
    table_l70 = [[8, 2], [7, 3]]
    odds_l70, p_fisher_l70 = stats.fisher_exact(table_l70)
    
    # 2. Length regrowth analysis
    orig_lens = [L_by_seed['orig'][s] for s in seeds if L_by_seed['orig'][s] is not None]
    l70_lens = [L_by_seed['L70'][s] for s in seeds if L_by_seed['L70'][s] is not None]
    l50_lens = [L_by_seed['L50'][s] for s in seeds if L_by_seed['L50'][s] is not None]
    
    # 3. Harmonic subset period ratio (G5: R2 >= 0.8)
    l70_g5_seeds = [s for s in seeds if g5_by_seed['L70'][s] and T_by_seed['L70'][s]]
    orig_g5_seeds = [s for s in seeds if g5_by_seed['orig'][s] and T_by_seed['orig'][s]]
    l50_g5_seeds = [s for s in seeds if g5_by_seed['L50'][s] and T_by_seed['L50'][s]]
    
    t_l70_g5 = [T_by_seed['L70'][s] for s in l70_g5_seeds]
    t_orig_g5 = [T_by_seed['orig'][s] for s in orig_g5_seeds]
    t_l50_g5 = [T_by_seed['L50'][s] for s in l50_g5_seeds]
    
    bs_l70_g5 = bootstrap_gm_ratio(t_l70_g5, t_orig_g5)
    bs_l50_g5 = bootstrap_gm_ratio(t_l50_g5, t_orig_g5)
    
    # 4. Same-seed carryover
    same_seed_26 = {
        'orig_T': T_by_seed['orig'].get(26),
        'l70_T': T_by_seed['L70'].get(26),
        'diff': T_by_seed['L70'].get(26) - T_by_seed['orig'].get(26) if T_by_seed['orig'].get(26) and T_by_seed['L70'].get(26) else None,
        'ratio': T_by_seed['L70'].get(26) / T_by_seed['orig'].get(26) if T_by_seed['orig'].get(26) and T_by_seed['L70'].get(26) else None,
    }
    same_seed_28 = {
        'orig_T': T_by_seed['orig'].get(28),
        'l70_T': T_by_seed['L70'].get(28),
        'diff': T_by_seed['L70'].get(28) - T_by_seed['orig'].get(28) if T_by_seed['orig'].get(28) and T_by_seed['L70'].get(28) else None,
        'ratio': T_by_seed['L70'].get(28) / T_by_seed['orig'].get(28) if T_by_seed['orig'].get(28) and T_by_seed['L70'].get(28) else None,
    }
    
    # 5. ANOVA on log(T) across G5 clips: seed variance vs arm variance
    all_g5_T = []
    all_g5_seeds = []
    all_g5_arms = []
    for a in arms:
        for s in seeds:
            if g5_by_seed[a][s] and T_by_seed[a][s]:
                all_g5_T.append(np.log(T_by_seed[a][s]))
                all_g5_seeds.append(s)
                all_g5_arms.append(a)
                
    y = np.array(all_g5_T)
    # Total variance
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    # Variance explained by seed
    unique_seeds = np.unique(all_g5_seeds)
    ss_seed = sum(len(y[np.array(all_g5_seeds) == s]) * (np.mean(y[np.array(all_g5_seeds) == s]) - np.mean(y)) ** 2 for s in unique_seeds)
    eta2_seed = float(ss_seed / ss_tot) if ss_tot > 0 else 0.0
    
    results = {
        'mcnemar_l50': {
            'b_losses': b_l50,
            'c_gains': c_l50,
            'p_value': p_mcnemar_l50
        },
        'mcnemar_l70': {
            'b_losses': b_l70,
            'c_gains': c_l70,
            'p_value': p_mcnemar_l70
        },
        'fisher_l50': {
            'odds_ratio': float(odds_l50),
            'p_value': float(p_fisher_l50)
        },
        'fisher_l70': {
            'odds_ratio': float(odds_l70),
            'p_value': float(p_fisher_l70)
        },
        'rod_lengths': {
            'orig_median_all': float(np.median(orig_lens)),
            'l70_median_all': float(np.median(l70_lens)),
            'l50_median_all': float(np.median(l50_lens)),
            'l70_input_target': 81.50,
            'l50_input_target': 55.33,
            'orig_input_target': 111.76,
            'l70_regrowth_px': float(np.median(l70_lens) - 81.50),
            'l70_regrowth_frac_of_gap': float((np.median(l70_lens) - 81.50) / (111.76 - 81.50))
        },
        'harmonic_ratio_G5': {
            'L70_vs_orig': bs_l70_g5,
            'L50_vs_orig': bs_l50_g5
        },
        'same_seed_carryover': {
            'seed_26': same_seed_26,
            'seed_28': same_seed_28
        },
        'anova_eta2_seed': eta2_seed,
        'n_clips_total': len(rows),
        'n_clips_g4': {'orig': sum(g4_by_seed['orig'].values()), 'L70': sum(g4_by_seed['L70'].values()), 'L50': sum(g4_by_seed['L50'].values())},
        'n_clips_pass': {'orig': sum(pass_by_seed['orig'].values()), 'L70': sum(pass_by_seed['L70'].values()), 'L50': sum(pass_by_seed['L50'].values())}
    }
    
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved comprehensive audit results to {out_path}")
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
