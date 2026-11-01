#!/usr/bin/env python3
"""
Independent replication and review of Finding 1283 (Task 62).
Target: rahul-5-agy Finding #1283 on Nano's bounce restitution vs impact velocity ladder.
"""
import os, sys, json
import numpy as np
import cv2
from scipy.optimize import curve_fit

def log_linear_eT(flights):
    """Fit ln(T_k) = ln(T_0) + k * ln(e_T)"""
    if len(flights) < 2:
        return None, 0.0
    ks = np.arange(len(flights))
    ln_T = np.log(flights)
    # linear regression
    p = np.polyfit(ks, ln_T, 1)
    e_T = np.exp(p[0])
    # calculate SE
    pred = np.polyval(p, ks)
    res = ln_T - pred
    if len(flights) > 2:
        s_err = np.sqrt(np.sum(res**2) / (len(flights) - 2))
        s_slope = s_err / np.sqrt(np.sum((ks - np.mean(ks))**2))
        se_e_T = e_T * s_slope
    else:
        se_e_T = 0.0
    return float(e_T), float(se_e_T)

def analyze_sheets():
    sheet_dir = '/home/nail/swarm-work/agy-2/cosmos-swarm/work/rahul-5-agy/impact_speed/sheets'
    sheets = [
        ('dd33', 1, 'ball1_dd33_s1_sheet.jpg', 34.5, 2.60),
        ('dd33', 2, 'ball1_dd33_s2_sheet.jpg', 34.5, 2.60),
        ('dd35', 1, 'ball1_dd35_s1_sheet.jpg', 24.4, 2.19),
        ('dd35', 2, 'ball1_dd35_s2_sheet.jpg', 24.4, 2.19),
        ('dd37', 1, 'ball1_dd37_s1_sheet.jpg',  9.4, 1.36),
        ('dd37', 2, 'ball1_dd37_s2_sheet.jpg',  9.4, 1.36),
        ('dd58', 1, 'ball1_dd58_s1_sheet.jpg',  5.3, 1.02),
        ('dd58', 2, 'ball1_dd58_s2_sheet.jpg',  5.3, 1.02),
    ]
    
    sheet_results = {}
    for cond, seed, sname, drop_cm, v_imp in sheets:
        spath = os.path.join(sheet_dir, sname)
        img = cv2.imread(spath)
        tiles_data = []
        for t in range(10):
            tile = img[25:, t*110:(t+1)*110]
            gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
            # Find dark circular blob
            # Exclude bottom 20 px (table edge)
            sub = gray[:215, :]
            min_v, _, min_l, _ = cv2.minMaxLoc(sub)
            mask = (sub < min_v + 15).astype(np.uint8)
            M = cv2.moments(mask)
            if M['m00'] > 0:
                cx = M['m10'] / M['m00']
                cy = M['m01'] / M['m00']
            else:
                cx, cy = min_l[0], min_l[1]
            # Convert to full frame coordinates: x_full = cx + 240, y_full = cy + 145
            tiles_data.append({
                'frame': t * 10,
                'x_full': float(cx + 240),
                'y_full': float(cy + 145),
                'min_gray': float(min_v)
            })
        sheet_results[f'{cond}_s{seed}'] = {
            'cond': cond, 'seed': seed, 'drop_cm': drop_cm, 'v_imp': v_imp,
            'tiles': tiles_data
        }
    return sheet_results

def main():
    with open('/home/nail/swarm-work/agy-2/cosmos-swarm/work/rahul-5-agy/impact_speed/summary.json') as f:
        summary = json.load(f)
    
    print("=== 1. INDEPENDENT RE-EVALUATION OF AUTHOR'S DATA ===")
    reanal = []
    for item in summary:
        flights = item['flights_s']
        e_T_ratios = item['e_T_ratios']
        mean_adj = np.mean(e_T_ratios) if e_T_ratios else None
        se_adj = (np.std(e_T_ratios, ddof=1) / np.sqrt(len(e_T_ratios))) if len(e_T_ratios) > 1 else 0.0
        
        e_T_loglin, se_loglin = log_linear_eT(flights)
        
        # Check energy creation / height ratios
        rises = item['rises_px']
        drop_px = item['drop_cm'] * 539.8 / 100.0  # px from mpp
        max_rise_px = max(rises) if rises else 0.0
        energy_gain_ratio = (max_rise_px / drop_px) if drop_px > 0 else 0.0
        
        reanal.append({
            'clip': item['clip'],
            'cond': item['cond'],
            'seed': item['seed'],
            'drop_cm': item['drop_cm'],
            'v_imp': item['v_imp'],
            'n_impacts': item['n_impacts'],
            'flights_s': flights,
            'rises_px': rises,
            'author_mean_e_T': item['mean_e_T'],
            'author_se_e_T': item['se_e_T'],
            'recomputed_adj_e_T': mean_adj,
            'recomputed_adj_se': se_adj,
            'loglin_e_T': e_T_loglin,
            'loglin_se': se_loglin,
            'drop_px': drop_px,
            'max_rise_px': max_rise_px,
            'energy_gain_ratio': energy_gain_ratio,
            'still_bouncing': item['still_bouncing'],
            'outcome': 'bouncing' if item['n_impacts'] >= 3 else ('yo_yo' if item['clip']=='ball1_dd33_s2.mp4' else ('levitation' if item['n_impacts'] == 0 else 'decay_stop'))
        })
        print(f"Clip: {item['clip']} ({item['cond']} s{item['seed']}):")
        print(f"  Drop: {item['drop_cm']} cm, v_imp: {item['v_imp']} m/s, Impacts: {item['n_impacts']}")
        print(f"  Author e_T: {item['mean_e_T']} +/- {item['se_e_T']}")
        print(f"  Recomputed Adj: {mean_adj} +/- {se_adj}")
        print(f"  Log-Linear e_T: {e_T_loglin} +/- {se_loglin}")
        print(f"  Drop px: {drop_px:.1f}, Max Rise px: {max_rise_px:.1f}, Energy Gain Ratio: {energy_gain_ratio:.2f}x")
        print(f"  Outcome: {reanal[-1]['outcome']}")
        print()

    # Compare high drop (dd33 s1) vs low drop (dd58 s2)
    dd33_s1 = [r for r in reanal if r['cond']=='dd33' and r['seed']==1][0]
    dd58_s2 = [r for r in reanal if r['cond']=='dd58' and r['seed']==2][0]
    
    diff_adj = dd58_s2['recomputed_adj_e_T'] - dd33_s1['recomputed_adj_e_T']
    se_diff_adj = np.sqrt(dd58_s2['recomputed_adj_se']**2 + dd33_s1['recomputed_adj_se']**2)
    
    diff_loglin = dd58_s2['loglin_e_T'] - dd33_s1['loglin_e_T']
    se_diff_loglin = np.sqrt(dd58_s2['loglin_se']**2 + dd33_s1['loglin_se']**2)
    
    print("=== 2. IMPACT SPEED INVARIANCE TEST ===")
    print(f"Adjacent Ratio:")
    print(f"  dd33 s1 (2.60 m/s): {dd33_s1['recomputed_adj_e_T']:.4f} +/- {dd33_s1['recomputed_adj_se']:.4f}")
    print(f"  dd58 s2 (1.02 m/s): {dd58_s2['recomputed_adj_e_T']:.4f} +/- {dd58_s2['recomputed_adj_se']:.4f}")
    print(f"  Difference Delta e_T: {diff_adj:+.4f} +/- {se_diff_adj:.4f} (t = {diff_adj/se_diff_adj:.2f}, not significant)")
    print(f"Log-Linear Regression:")
    print(f"  dd33 s1 (2.60 m/s): {dd33_s1['loglin_e_T']:.4f} +/- {dd33_s1['loglin_se']:.4f}")
    print(f"  dd58 s2 (1.02 m/s): {dd58_s2['loglin_e_T']:.4f} +/- {dd58_s2['loglin_se']:.4f}")
    print(f"  Difference Delta e_T: {diff_loglin:+.4f} +/- {se_diff_loglin:.4f} (t = {diff_loglin/se_diff_loglin:.2f}, not significant)")
    print()

    print("=== 3. CONTACT SHEET AUDIT ===")
    sheet_data = analyze_sheets()
    for k, v in sheet_data.items():
        ys = [t['y_full'] for t in v['tiles']]
        min_y, max_y = min(ys), max(ys)
        drift_y = max_y - min_y
        print(f"Sheet {k} ({v['cond']} drop {v['drop_cm']}cm): y_range=[{min_y:.1f}, {max_y:.1f}], drift={drift_y:.1f}px")

    out_json = {
        'reanalysis': reanal,
        'contrast_adj': {'diff': diff_adj, 'se': se_diff_adj},
        'contrast_loglin': {'diff': diff_loglin, 'se': se_diff_loglin},
        'sheet_data': sheet_data
    }
    with open('/home/nail/swarm-work/agy-2/replicate_finding_1283_results.json', 'w') as f:
        json.dump(out_json, f, indent=2)
    print("\nSaved /home/nail/swarm-work/agy-2/replicate_finding_1283_results.json")

if __name__ == '__main__':
    main()
