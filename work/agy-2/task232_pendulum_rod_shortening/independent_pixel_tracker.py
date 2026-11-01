#!/usr/bin/env python3
"""
Task 232: Independent Pixel-Level Kinematic Tracker & Physical Rod Length Audit
Evaluates all 30 Cosmos3-Nano pendulum clips (Orig, L70, L50 across seeds 21-30).

Author: agy-2
Date: 2026-11-01
"""

import os
import sys
import glob
import json
import re
import cv2
import numpy as np
from scipy import stats
from scipy.optimize import least_squares

PIVOT_NOMINAL = np.array([326.0, 118.0])

def load_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def detect_pivot(f0):
    """Refine pivot center near (326, 118) using axle circle detection or gradient center."""
    gray = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    roi = gray[100:140, 310:345]
    # Center of minimal intensity or circle center
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(cv2.GaussianBlur(roi, (5, 5), 0))
    # Return nominal unless clear local minimum
    pivot_x = 310.0 + min_loc[0]
    pivot_y = 100.0 + min_loc[1]
    if np.hypot(pivot_x - PIVOT_NOMINAL[0], pivot_y - PIVOT_NOMINAL[1]) < 8.0:
        return np.array([pivot_x, pivot_y])
    return PIVOT_NOMINAL.copy()

def segment_rod_and_bob(frame, bg, pivot):
    """
    Independently segment tan wooden rod and dark metallic bob in frame.
    Returns:
      rod_mask, bob_mask, rod_length, bob_center, bob_area, bob_diam, secondary_bobs, branching_angle
    """
    H, W = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray, bg_gray)
    
    # 1. Tan wooden rod mask (HSV: H in [5, 28], S in [40, 255], V in [70, 255])
    # Restrict to plausible pendulum region: y in [100, 320], x in [150, 480]
    region_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.circle(region_mask, (int(pivot[0]), int(pivot[1])), 220, 255, -1)
    # Mask out above pivot
    region_mask[:int(pivot[1]) - 5, :] = 0
    # Mask out below table surface (y > 275)
    region_mask[275:, :] = 0

    tan_mask = (hsv[..., 0] >= 5) & (hsv[..., 0] <= 28) & (hsv[..., 1] >= 35) & (hsv[..., 2] >= 65)
    tan_mask = (tan_mask & (region_mask > 0)).astype(np.uint8) * 255
    # Morphological clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    tan_clean = cv2.morphologyEx(tan_mask, cv2.MORPH_OPEN, kernel)
    
    # Connected components for rod
    n_labels, labels, stats_cc, centroids = cv2.connectedComponentsWithStats(tan_clean)
    rod_pts = []
    rod_length = 0.0
    branching_angles = []
    
    # Find components connected to or aligned near pivot (within 35 px of pivot)
    main_rod_comp = None
    max_pts_near_pivot = 0
    for lbl in range(1, n_labels):
        area = stats_cc[lbl, cv2.CC_STAT_AREA]
        if area < 15:
            continue
        cx, cy = centroids[lbl]
        d_piv = np.hypot(cx - pivot[0], cy - pivot[1])
        if d_piv < 70.0:
            if area > max_pts_near_pivot:
                max_pts_near_pivot = area
                main_rod_comp = lbl

    if main_rod_comp is not None:
        ys, xs = np.nonzero(labels == main_rod_comp)
        pts = np.c_[xs, ys]
        dists = np.hypot(pts[:, 0] - pivot[0], pts[:, 1] - pivot[1])
        rod_length = float(np.max(dists)) if len(dists) > 0 else 0.0
        rod_pts = pts
        
        # Check for secondary branches
        for lbl in range(1, n_labels):
            if lbl == main_rod_comp:
                continue
            if stats_cc[lbl, cv2.CC_STAT_AREA] > 30:
                cx, cy = centroids[lbl]
                ang = np.degrees(np.arctan2(cx - pivot[0], cy - pivot[1]))
                main_ang = np.degrees(np.arctan2(np.median(xs) - pivot[0], np.median(ys) - pivot[1]))
                if abs(ang - main_ang) > 15.0 and np.hypot(cx - pivot[0], cy - pivot[1]) < 180:
                    branching_angles.append(float(ang - main_ang))

    # 2. Dark metallic bob segmentation (V < 90, difference > 15, or dark blob near rod tip)
    # Search region around pivot extending to 220 px
    dark_mask = (hsv[..., 2] < 95) & (region_mask > 0)
    # Require either motion diff or strong dark contrast
    bob_candidate_mask = (dark_mask & ((diff > 12) | (hsv[..., 2] < 70))).astype(np.uint8) * 255
    bob_clean = cv2.morphologyEx(bob_candidate_mask, cv2.MORPH_OPEN, kernel)
    
    n_bob_lbls, bob_labels, bob_stats, bob_centroids = cv2.connectedComponentsWithStats(bob_clean)
    bob_candidates = []
    for lbl in range(1, n_bob_lbls):
        area = bob_stats[lbl, cv2.CC_STAT_AREA]
        if area < 30 or area > 3500: # Bob is typically ~150-1000 px
            continue
        cx, cy = bob_centroids[lbl]
        d_piv = np.hypot(cx - pivot[0], cy - pivot[1])
        if d_piv > 30 and d_piv < 240:
            # Aspect ratio check
            w = bob_stats[lbl, cv2.CC_STAT_WIDTH]
            h = bob_stats[lbl, cv2.CC_STAT_HEIGHT]
            aspect = max(w, h) / max(1, min(w, h))
            if aspect < 3.5: # roughly spherical / elliptical
                bob_candidates.append({
                    'centroid': (float(cx), float(cy)),
                    'dist_pivot': float(d_piv),
                    'area': float(area),
                    'diam': float(2.0 * np.sqrt(area / np.pi)),
                    'aspect': float(aspect),
                    'angle_deg': float(np.degrees(np.arctan2(cx - pivot[0], cy - pivot[1])))
                })
                
    # Sort bob candidates by area descending
    bob_candidates.sort(key=lambda b: b['area'], reverse=True)
    
    primary_bob = bob_candidates[0] if len(bob_candidates) > 0 else None
    secondary_bobs = bob_candidates[1:] if len(bob_candidates) > 1 else []
    
    return {
        'rod_length': rod_length,
        'has_rod': bool(rod_length > 30.0),
        'primary_bob': primary_bob,
        'secondary_bobs': secondary_bobs,
        'n_bobs': len(bob_candidates),
        'branching_angles': branching_angles,
        'has_branching': len(branching_angles) > 0
    }

def fit_harmonic_oscillation(times, angles):
    """
    Fit damped sinusoidal oscillation:
    theta(t) = theta_0 + e^{-beta t} [ A cos(omega t) + B sin(omega t) ]
    Returns dict of fitted parameters.
    """
    valid = np.isfinite(angles)
    t = times[valid]
    y = angles[valid]
    if len(y) < 15:
        return {'r2': 0.0, 'T': None, 'beta': 0.0, 'valid': False}
    
    dur = t[-1] - t[0]
    # Zero crossing estimation
    y_center = y - np.median(y)
    zc_up = np.where((y_center[:-1] < 0) & (y_center[1:] >= 0))[0]
    zc_dn = np.where((y_center[:-1] > 0) & (y_center[1:] <= 0))[0]
    all_zc = np.sort(np.concatenate([zc_up, zc_dn]))
    
    T_zc = None
    if len(all_zc) >= 3:
        zc_times = t[all_zc]
        half_periods = np.diff(zc_times)
        if len(half_periods) >= 2:
            T_zc = float(2.0 * np.median(half_periods))
            
    # Grid search for best T
    T_grid = np.linspace(0.4, min(4.0, dur * 1.5), 35)
    if T_zc is not None and 0.3 < T_zc < 5.0:
        T_grid = np.unique(np.concatenate([T_grid, [T_zc]]))
        
    best_res = None
    best_cost = 1e12
    for T_cand in T_grid:
        w0 = 2 * np.pi / T_cand
        # Model: p[0]=T, p[1]=beta, p[2]=theta_0, p[3]=A, p[4]=B
        def residual(p):
            w = 2 * np.pi / p[0]
            decay = np.exp(-p[1] * t)
            pred = p[2] + decay * (p[3] * np.cos(w * t) + p[4] * np.sin(w * t))
            return pred - y
        
        p0 = [T_cand, 0.0, np.median(y), y[0] - np.median(y), 0.0]
        bounds = ([0.2, -1.0, -90.0, -90.0, -90.0], [6.0, 1.0, 90.0, 90.0, 90.0])
        try:
            res = least_squares(residual, p0, bounds=bounds, ftol=1e-4, max_nfev=50)
            if res.cost < best_cost:
                best_cost = res.cost
                best_res = res
        except Exception:
            continue
            
    if best_res is not None:
        p = best_res.x
        res_fun = best_res.fun
        ss_res = np.sum(res_fun ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 1e-6 else 0.0
        return {
            'T': float(p[0]),
            'beta': float(p[1]),
            'theta_0': float(p[2]),
            'amp': float(np.hypot(p[3], p[4])),
            'r2': float(r2),
            'T_zc': T_zc,
            'valid': bool(r2 >= 0.5)
        }
    return {'r2': 0.0, 'T': None, 'beta': 0.0, 'valid': False}

def analyze_clip(clip_path):
    fn = os.path.basename(clip_path)
    # Determine arm and seed
    if 'base' in fn or fn.startswith('rpr_'):
        arm = 'orig'
        m = re.search(r's(\d+)', fn)
        seed = int(m.group(1)) if m else None
    elif 'L70' in fn:
        arm = 'L70'
        m = re.search(r's(\d+)', fn)
        seed = int(m.group(1)) if m else None
    elif 'L50' in fn:
        arm = 'L50'
        m = re.search(r's(\d+)', fn)
        seed = int(m.group(1)) if m else None
    else:
        arm = 'unknown'
        seed = None

    frames = load_frames(clip_path)
    n_frames = len(frames)
    if n_frames == 0:
        return {'file': fn, 'error': 'empty_clip'}

    # Compute temporal median background (subsampling 10 frames)
    step = max(1, n_frames // 10)
    bg_sub = np.median([frames[i] for i in range(0, n_frames, step)], axis=0).astype(np.uint8)
    
    pivot = detect_pivot(frames[0])
    
    # Analyze frame 0 reference
    f0_info = segment_rod_and_bob(frames[0], bg_sub, pivot)
    f0_rod_len = f0_info['rod_length']
    f0_bob_diam = f0_info['primary_bob']['diam'] if f0_info['primary_bob'] else 0.0
    f0_bob_dist = f0_info['primary_bob']['dist_pivot'] if f0_info['primary_bob'] else 0.0
    f0_bob_area = f0_info['primary_bob']['area'] if f0_info['primary_bob'] else 0.0

    # Per-frame extraction
    rod_lens = []
    bob_dists = []
    bob_diams = []
    bob_areas = []
    thetas = []
    valid_frames = 0
    duplicate_bob_frames = 0
    giant_bob_frames = 0
    branching_frames = 0
    regrown_rod_frames = 0 # Rod length >= 0.9 * 111.8 = 100.6 px
    dissolution_frames = 0 # No bob or rod tracked

    times = np.arange(n_frames) / 24.0
    
    for f_idx, frame in enumerate(frames):
        info = segment_rod_and_bob(frame, bg_sub, pivot)
        rl = info['rod_length']
        pb = info['primary_bob']
        
        rod_lens.append(rl)
        if rl >= 100.0 and arm != 'orig':
            regrown_rod_frames += 1
            
        if info['has_branching']:
            branching_frames += 1
            
        if info['n_bobs'] >= 2:
            duplicate_bob_frames += 1
            
        if pb is not None:
            bd = pb['dist_pivot']
            diam = pb['diam']
            area = pb['area']
            ang = pb['angle_deg']
            bob_dists.append(bd)
            bob_diams.append(diam)
            bob_areas.append(area)
            thetas.append(ang)
            valid_frames += 1
            
            # Giant bob check (area > 1.6 * f0_bob_area or diam > 1.3 * f0_bob_diam)
            if (f0_bob_diam > 0 and diam > 1.35 * f0_bob_diam) or (f0_bob_area > 0 and area > 1.8 * f0_bob_area):
                giant_bob_frames += 1
        else:
            bob_dists.append(np.nan)
            bob_diams.append(np.nan)
            bob_areas.append(np.nan)
            thetas.append(np.nan)
            dissolution_frames += 1

    # Aggregate kinematic metrics
    valid_frac = valid_frames / float(n_frames)
    med_rod_len = float(np.nanmedian(rod_lens)) if len(rod_lens) > 0 else 0.0
    med_bob_dist = float(np.nanmedian(bob_dists)) if valid_frames > 0 else 0.0
    med_bob_diam = float(np.nanmedian(bob_diams)) if valid_frames > 0 else 0.0
    
    # Fit harmonic motion on angular trajectory
    harmonic = fit_harmonic_oscillation(times, np.array(thetas))
    
    # Gate definitions (similar to kiro-1 G1-G5, but independently calculated from pixel tracker)
    # G1: pivot residue < 5 px (our pivot is fixed at detected axle)
    # G2: pivot within 15 px of (326, 118)
    # G3: length deviation < 0.25 of input reference
    # G4: valid tracked fraction >= 0.60
    # G5: harmonic fit R2 >= 0.80
    
    target_len = {'orig': 111.8, 'L70': 81.5, 'L50': 55.3}.get(arm, 111.8)
    len_dev = abs(med_rod_len - target_len) / target_len if target_len > 0 else 9.0
    
    g_pivot = bool(np.hypot(pivot[0] - PIVOT_NOMINAL[0], pivot[1] - PIVOT_NOMINAL[1]) < 15.0)
    g_length = bool(len_dev < 0.25)
    g_tracked = bool(valid_frac >= 0.60)
    g_harmonic = bool(harmonic['r2'] >= 0.80)
    all_pass = bool(g_pivot and g_length and g_tracked and g_harmonic)

    return {
        'file': fn,
        'arm': arm,
        'seed': seed,
        'n_frames': n_frames,
        'pivot': pivot.tolist(),
        'f0_rod_len': float(f0_rod_len),
        'f0_bob_diam': float(f0_bob_diam),
        'f0_bob_dist': float(f0_bob_dist),
        'f0_bob_area': float(f0_bob_area),
        'valid_frac': float(valid_frac),
        'med_rod_len': float(med_rod_len),
        'med_bob_dist': float(med_bob_dist),
        'med_bob_diam': float(med_bob_diam),
        'bob_growth_ratio': float(med_bob_diam / f0_bob_diam) if f0_bob_diam > 0 else 1.0,
        'rod_regrowth_ratio': float(med_rod_len / target_len) if target_len > 0 else 1.0,
        'rod_to_orig_ratio': float(med_rod_len / 111.76),
        'duplicate_bob_rate': float(duplicate_bob_frames / float(n_frames)),
        'giant_bob_rate': float(giant_bob_frames / float(n_frames)),
        'branching_rate': float(branching_frames / float(n_frames)),
        'regrown_rod_rate': float(regrown_rod_frames / float(n_frames)),
        'dissolution_rate': float(dissolution_frames / float(n_frames)),
        'T_fit': harmonic.get('T'),
        'r2': harmonic.get('r2'),
        'T_zc': harmonic.get('T_zc'),
        'beta': harmonic.get('beta'),
        'amp_deg': harmonic.get('amp'),
        'gates': {
            'G_pivot': g_pivot,
            'G_length': g_length,
            'G4_tracked': g_tracked,
            'G5_harmonic': g_harmonic,
            'ALL_PASS': all_pass
        },
        'thetas': [float(t) if np.isfinite(t) else None for t in thetas],
        'rod_lens': [float(r) for r in rod_lens],
        'bob_dists': [float(b) if np.isfinite(b) else None for b in bob_dists]
    }

def main():
    clips_dir = '/home/nail/swarm-work/agy-2/t232_pendulum_data/clips'
    all_clips = sorted(glob.glob(os.path.join(clips_dir, '*.mp4')))
    print(f"Found {len(all_clips)} clips in {clips_dir}")
    
    results = {}
    for clip in all_clips:
        fn = os.path.basename(clip)
        print(f"Analyzing {fn}...")
        res = analyze_clip(clip)
        results[fn] = res
        print(f"  -> Arm: {res['arm']}, Seed: {res['seed']}, ValidFrac: {res['valid_frac']:.2f}, "
              f"RodLen: {res['med_rod_len']:.1f}px, BobDist: {res['med_bob_dist']:.1f}px, "
              f"R2: {res['r2']:.3f}, T: {res['T_fit']}, ALL_PASS: {res['gates']['ALL_PASS']}")
        
    out_path = '/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task232_pendulum_rod_shortening/independent_tracking_results.json'
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_path}")

if __name__ == '__main__':
    main()
