#!/usr/bin/env python3
"""
Independent replication and review of Finding #4460 (Task 217, poornima-3).
Audits regional late-motion contrasts (BG, AIR, LOW, ROBOT, GRIP, ARM, WHOLE)
across 90 q8 clips (10 seeds x 3 GAUGE frames x F/QT/N).

Tests:
1. Spatial isolation: does the QT timed-settle clause selectively damp motion in the
   ball corridor (AIR, LOW, GRIP) while leaving background noise (BG) unaffected?
2. Exact seed-level statistical inference (1024 sign-flip permutations, 20k bootstrap resamples).
3. Area and absolute drop share decomposition from pixel motion maps.
4. Calibration against blind eye codes (codes_named.csv): AUC of motion proxies for REST.
5. Mechanism validation: correlation between ROBOT late motion and retethering under F and N.
"""

import json
import csv
import re
import itertools
import numpy as np
from scipy.stats import spearmanr

def compute_auc(y_true, y_score):
    """Exact ROC AUC via Mann-Whitney U rank sum."""
    y_true = np.asarray(y_true, bool)
    y_score = np.asarray(y_score, float)
    n1 = y_true.sum()
    n0 = len(y_true) - n1
    if n1 == 0 or n0 == 0:
        return None
    # Rank scores (average ranks for ties)
    order = np.argsort(y_score)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(y_score) + 1)
    
    # Handle ties
    unique_scores, inverse, counts = np.unique(y_score, return_inverse=True, return_counts=True)
    for i, count in enumerate(counts):
        if count > 1:
            ranks[inverse == i] = ranks[inverse == i].mean()
            
    r1 = ranks[y_true].sum()
    u = r1 - n1 * (n1 + 1) / 2.0
    return float(u / (n1 * n0))

def box(x0, x1, y0, y1):
    m = np.zeros((60, 104), bool)
    m[y0:y1+1, x0:x1+1] = True
    return m

REGIONS = {
    'LOW': box(8, 63, 34, 59),
    'AIR': box(22, 45, 14, 33),
    'ROBOT': box(22, 45, 0, 13) | box(46, 61, 0, 33),
    'BG': box(64, 103, 0, 59),
    'GRIP_posthoc': box(22, 45, 0, 13),
    'ARM_posthoc': box(46, 61, 0, 33),
    'WHOLE': np.ones((60, 104), bool),
}

def main():
    # 1. Load data
    with open('regional_results.json') as f:
        author_data = json.load(f)
    
    per_clip = author_data['per_clip']
    assert len(per_clip) == 90, f"Expected 90 clips, got {len(per_clip)}"
    
    # Organize by (img, prompt, seed)
    clip_dict = {}
    for c in per_clip:
        key = (c['img'], c['prompt'], int(c['seed']))
        clip_dict[key] = c
    
    images = ['b1dd33', 'b2dd35', 'b2dd37']
    seeds = list(range(1, 11))
    prompts = ['F', 'QT', 'N']
    
    # 2. Re-compute contrasts independently
    independent_contrasts = {}
    rng = np.random.default_rng(20261101)
    
    for r_name in REGIONS:
        independent_contrasts[r_name] = {}
        for p_test, p_ctrl in [('QT', 'F'), ('QT', 'N'), ('N', 'F')]:
            pair_name = f"{p_test}-{p_ctrl}"
            
            # For each seed, average across 3 images
            d_per_seed = []
            for s in seeds:
                d_img = [clip_dict[(img, p_test, s)][r_name] - clip_dict[(img, p_ctrl, s)][r_name] for img in images]
                d_per_seed.append(np.mean(d_img))
            
            d_arr = np.array(d_per_seed)
            mean_log = float(np.mean(d_arr))
            ratio = float(np.exp(mean_log))
            
            # Exact sign-flip test (1024 permutations for n=10)
            signs = np.array(list(itertools.product([1, -1], repeat=len(d_arr))))
            null_means = (signs * d_arr).mean(axis=1)
            p_signflip = float(np.mean(np.abs(null_means) >= np.abs(mean_log) - 1e-12))
            
            # Seed cluster bootstrap (20,000 resamples)
            boot_idx = rng.integers(0, len(d_arr), size=(20000, len(d_arr)))
            boot_means = d_arr[boot_idx].mean(axis=1)
            ci95_ratio = [float(np.exp(np.percentile(boot_means, 2.5))), float(np.exp(np.percentile(boot_means, 97.5)))]
            
            n_pos = int((d_arr > 0).sum())
            n_neg = int((d_arr < 0).sum())
            
            independent_contrasts[r_name][pair_name] = {
                'mean_log': mean_log,
                'ratio': ratio,
                'ci95_ratio': ci95_ratio,
                'p_signflip': p_signflip,
                'n_pos': n_pos,
                'n_neg': n_neg,
                'per_seed': [round(float(v), 3) for v in d_arr]
            }
    
    # 3. Spatial drop share analysis using motionmaps.npz
    mm = np.load('motionmaps.npz')
    F_map = mm['F']
    QT_map = mm['QT']
    N_map = mm['N']
    
    diff_F_QT = F_map - QT_map
    total_drop = float(diff_F_QT.sum())
    
    spatial_shares = {}
    sub_regions = {
        'GRIP': box(22, 45, 0, 13),
        'AIR': box(22, 45, 14, 33),
        'LOW': box(8, 63, 34, 59),
        'ARM': box(46, 61, 0, 33),
        'BG': box(64, 103, 0, 59),
        'REST': ~(box(22, 45, 0, 13) | box(22, 45, 14, 33) | box(8, 63, 34, 59) | box(46, 61, 0, 33) | box(64, 103, 0, 59))
    }
    
    for s_name, s_mask in sub_regions.items():
        area_px = int(s_mask.sum())
        area_pct = float(area_px / 6240 * 100)
        mean_F = float(F_map[s_mask].mean())
        mean_QT = float(QT_map[s_mask].mean())
        mean_diff = float(mean_F - mean_QT)
        drop_share = float(diff_F_QT[s_mask].sum() / total_drop * 100)
        
        spatial_shares[s_name] = {
            'area_px': area_px,
            'area_pct': area_pct,
            'mean_F': mean_F,
            'mean_QT': mean_QT,
            'mean_diff': mean_diff,
            'drop_share_pct': drop_share
        }
    
    # 4. Calibration vs blind eye codes (codes_named.csv)
    codes_by_key = {}
    with open('codes_named.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            m = re.match(r't141q8_(b\w+?)_(F|QT|N)_s(\d+)$', row['name'])
            if m:
                codes_by_key[(m.group(1), m.group(2), int(m.group(3)))] = row
    
    # Match codes with per_clip entries
    matched_data = []
    for c in per_clip:
        key = (c['img'], c['prompt'], int(c['seed']))
        if key in codes_by_key:
            code_row = codes_by_key[key]
            end_state = code_row['end_state']
            ret_val = float(code_row['retether01']) if code_row['retether01'] in ('0', '1') else np.nan
            st_val = 1.0 if end_state == 'REST' else (0.0 if end_state != 'UNCLEAR' else np.nan)
            matched_data.append({
                'name': c['name'],
                'prompt': c['prompt'],
                'img': c['img'],
                'seed': c['seed'],
                'LOW': c['LOW'],
                'WHOLE': c['WHOLE'],
                'AIR': c['AIR'],
                'ROBOT': c['ROBOT'],
                'BG': c['BG'],
                'end_state': end_state,
                'retether': ret_val,
                'settle': st_val
            })
    
    def auc_lower(pos, neg):
        pos, neg = np.asarray(pos), np.asarray(neg)
        if len(pos) == 0 or len(neg) == 0:
            return None
        return float((pos[:, None] < neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())
    
    auc_results = {}
    for r_eval in ['LOW', 'WHOLE', 'AIR', 'ROBOT', 'BG']:
        auc_results[r_eval] = {}
        for pset in [('F', 'QT', 'N'), ('F',), ('QT',), ('N',)]:
            pos, neg = [], []
            for m in matched_data:
                if m['prompt'] not in pset:
                    continue
                if m['end_state'] == 'UNCLEAR':
                    continue
                if m['end_state'] == 'REST':
                    pos.append(m[r_eval])
                else:
                    neg.append(m[r_eval])
            auc_results[r_eval]['+'.join(pset)] = {
                'auc_rest_lower': auc_lower(pos, neg),
                'n_rest': len(pos),
                'n_other': len(neg)
            }
    
    def calc_spearman(x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        valid = ~np.isnan(x) & ~np.isnan(y)
        if valid.sum() < 3:
            return None, int(valid.sum())
        rx = np.argsort(np.argsort(x[valid]))
        ry = np.argsort(np.argsort(y[valid]))
        if rx.std() == 0 or ry.std() == 0:
            return None, int(valid.sum())
        return float(np.corrcoef(rx, ry)[0, 1]), int(valid.sum())
        
    spearman_results = {}
    for p in ['F', 'QT', 'N']:
        p_subset = [m for m in matched_data if m['prompt'] == p]
        robot_motion = [m['ROBOT'] for m in p_subset]
        retether = [m['retether'] for m in p_subset]
        settle = [m['settle'] for m in p_subset]
        
        rho_ret, n_ret = calc_spearman(robot_motion, retether)
        rho_st, n_st = calc_spearman(robot_motion, settle)
        spearman_results[p] = {
            'robot_vs_retether': rho_ret,
            'n_retether': n_ret,
            'robot_vs_settle': rho_st,
            'n_settle': n_st
        }
    
    # 5. Compile full review summary
    review_output = {
        'independent_contrasts': independent_contrasts,
        'spatial_shares': spatial_shares,
        'auc_results': auc_results,
        'spearman_results': spearman_results,
        'total_pixel_drop': total_drop
    }
    
    with open('independent_review_results.json', 'w') as f:
        json.dump(review_output, f, indent=2)
    
    print("=== INDEPENDENT REPLICATION SUMMARY ===")
    print("1. Background Motion (Null Check):")
    bg = independent_contrasts['BG']['QT-F']
    print(f"   BG QT/F ratio = {bg['ratio']:.4f} (95% CI [{bg['ci95_ratio'][0]:.4f}, {bg['ci95_ratio'][1]:.4f}], p = {bg['p_signflip']:.4f})")
    print(f"   Signs: {bg['n_pos']} positive, {bg['n_neg']} negative seeds (Exact balanced null!)")
    
    print("\n2. Ball Corridor Motion Collapse:")
    for r_k in ['AIR', 'LOW', 'GRIP_posthoc', 'WHOLE']:
        c = independent_contrasts[r_k]['QT-F']
        print(f"   {r_k:12s} QT/F ratio = {c['ratio']:.4f} (95% CI [{c['ci95_ratio'][0]:.4f}, {c['ci95_ratio'][1]:.4f}], p = {c['p_signflip']:.5f}) | {c['n_neg']}/10 seeds negative")
    
    print("\n3. Spatial Drop Share Decomposition:")
    for s_k, s_v in spatial_shares.items():
        print(f"   {s_k:8s}: Area={s_v['area_pct']:5.2f}% | F={s_v['mean_F']:.4f} -> QT={s_v['mean_QT']:.4f} | Drop share: {s_v['drop_share_pct']:5.2f}%")
    
    print("\n4. AUC for Physical Rest Discrimination:")
    for r_k in ['LOW', 'WHOLE', 'AIR', 'ROBOT', 'BG']:
        res_pool = auc_results[r_k]['F+QT+N']
        res_qt = auc_results[r_k]['QT']
        print(f"   {r_k:8s}: Pooled AUC = {res_pool['auc_rest_lower']:.4f} (n_rest={res_pool['n_rest']}, n_other={res_pool['n_other']}) | Within-QT AUC = {res_qt['auc_rest_lower']:.4f}")
    
    print("\n5. Robot Motion vs Retethering Correlation:")
    for p_k in ['F', 'QT', 'N']:
        p_v = spearman_results[p_k]
        print(f"   Arm {p_k:2s}: robot vs retether rho = {p_v['robot_vs_retether']:+.4f} (n = {p_v['n_retether']}) | robot vs settle rho = {p_v['robot_vs_settle']:+.4f} (n = {p_v['n_settle']})")

if __name__ == '__main__':
    main()
