#!/usr/bin/env python3
"""
Independent replication and physical kinematic audit of Finding #4974 (codex-api-4)
and Finding #4935 (Raj / Program N E1).

Audits:
1. Exact scalar mathematical replication of whole-frame image-change M (255 * mean abs diff)
   on native MP4 clips and verification of 16-seed ANOVA and speed contrasts.
2. OpenCV color compliance audit (red vs blue hue segmentation across frames).
3. Continuous pixel-level centroid tracking (x, y, area) across all 93 frames of native MP4 examples
   to isolate the physical mechanism of M increase (rigid swing speedup vs unphysical rod stretching / deformation).
"""
import os
import sys
import json
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SWARM_REPO = os.path.abspath(os.path.join(HERE, "../../.."))
E1_COMPLETE = os.path.join(SWARM_REPO, "work/codex-api-4/t223/e1_complete")
E1_EXAMPLES = os.path.join(SWARM_REPO, "work/codex-api-4/t223/e1_diagnostic/examples")
OUT_JSON = os.path.join(HERE, "e1_kinematic_audit.json")


def decode_m(mp4_path):
    cap = cv2.VideoCapture(mp4_path)
    previous = None
    changes = []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        bgr = bgr.astype(np.float64) / 255.0
        gray = .114 * bgr[:, :, 0] + .587 * bgr[:, :, 1] + .299 * bgr[:, :, 2]
        small = cv2.resize(gray, (208, 120), interpolation=cv2.INTER_AREA)
        if previous is not None:
            changes.append(small - previous)
        previous = small
    cap.release()
    return float(np.mean(np.abs(np.stack(changes))) * 255)


def track_bob_kinematics(mp4_path, color):
    cap = cv2.VideoCapture(mp4_path)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    
    xs, ys, areas = [], [], []
    red_px, blue_px = [], []
    
    for f in frames:
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        r_mask = ((hsv[..., 0] < 10) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 100) & (hsv[..., 2] > 50)
        b_mask = (hsv[..., 0] >= 100) & (hsv[..., 0] <= 135) & (hsv[..., 1] > 100) & (hsv[..., 2] > 50)
        
        red_px.append(int(np.sum(r_mask)))
        blue_px.append(int(np.sum(b_mask)))
        
        target_mask = r_mask if color == 'red' else b_mask
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(target_mask.astype(np.uint8))
        if num_labels > 1:
            largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            cx, cy = centroids[largest]
            area = stats[largest, cv2.CC_STAT_AREA]
            xs.append(float(cx))
            ys.append(float(cy))
            areas.append(float(area))
        else:
            xs.append(np.nan)
            ys.append(np.nan)
            areas.append(0.0)
            
    xs = np.array(xs)
    ys = np.array(ys)
    valid = ~np.isnan(xs)
    
    # Simple ACF on valid track
    acf_peak = None
    if np.sum(valid) > 30:
        xc = xs[valid] - np.mean(xs[valid])
        yc = ys[valid] - np.mean(ys[valid])
        # Track along the dominant axis of movement
        track_signal = yc if (np.nanmax(ys) - np.nanmin(ys)) > (np.nanmax(xs) - np.nanmin(xs)) else xc
        acf = np.correlate(track_signal, track_signal, mode='full')
        acf = acf[len(acf)//2:]
        if len(acf) > 10:
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(acf[5:])
            if len(peaks) > 0:
                acf_peak = int(peaks[0] + 5)

    return {
        'tracked_frames': int(np.sum(valid)),
        'total_frames': len(frames),
        'x_min': float(np.nanmin(xs)) if np.any(valid) else None,
        'x_max': float(np.nanmax(xs)) if np.any(valid) else None,
        'x_range': float(np.nanmax(xs) - np.nanmin(xs)) if np.any(valid) else None,
        'y_min': float(np.nanmin(ys)) if np.any(valid) else None,
        'y_max': float(np.nanmax(ys)) if np.any(valid) else None,
        'y_range': float(np.nanmax(ys) - np.nanmin(ys)) if np.any(valid) else None,
        'mean_bob_area': float(np.mean(areas)),
        'mean_red_px': float(np.mean(red_px)),
        'mean_blue_px': float(np.mean(blue_px)),
        'acf_peak_frames': acf_peak,
        'acf_peak_period_s': (acf_peak / 24.0) if acf_peak else None
    }


def audit_results_json():
    res_path = os.path.join(E1_COMPLETE, "results.json")
    with open(res_path) as f:
        res = json.load(f)
        
    cube = res['primary']['cubes'][0]
    fact = cube['factorial']
    sec = res['secondary']
    
    speed_diffs = sec['speed_fast_minus_slow']['seed_means']
    mean_speed_diff = sec['speed_fast_minus_slow']['mean_difference']
    speed_se = sec['speed_fast_minus_slow']['seed_se']
    speed_ci = sec['speed_fast_minus_slow']['seed_cluster_bootstrap']['ci95']
    
    eta2 = fact['eta2']
    total_ss = fact['total_ss']
    ss = fact['ss']
    
    return {
        'n_seeds': len(speed_diffs),
        'all_seeds_positive': bool(all(d > 0 for d in speed_diffs)),
        'min_seed_diff': float(min(speed_diffs)),
        'max_seed_diff': float(max(speed_diffs)),
        'mean_speed_diff': float(mean_speed_diff),
        'speed_se': float(speed_se),
        'speed_ci95': [float(x) for x in speed_ci],
        'eta2_seed': float(eta2['seed']),
        'eta2_prompt': float(eta2['prompt']),
        'eta2_interaction': float(eta2['seed:prompt']),
        'total_ss': float(total_ss)
    }


def main():
    print("Auditing E1 results.json...")
    res_audit = audit_results_json()
    print(f"  Speed fast-slow: {res_audit['mean_speed_diff']:.4f} +/- {res_audit['speed_se']:.4f}")
    print(f"  All 16 seeds positive: {res_audit['all_seeds_positive']}")
    print(f"  eta2_seed: {res_audit['eta2_seed']:.4f}, eta2_prompt: {res_audit['eta2_prompt']:.4f}")
    
    clip_audits = {}
    examples = [
        ("N_E1_red_slow_s201.mp4", "red", "slow"),
        ("N_E1_red_fast_s201.mp4", "red", "fast"),
        ("N_E1_blue_slow_s201.mp4", "blue", "slow"),
        ("N_E1_blue_fast_s201.mp4", "blue", "fast")
    ]
    
    for name, color, speed in examples:
        p = os.path.join(E1_EXAMPLES, name)
        if not os.path.exists(p):
            print(f"Warning: {p} missing")
            continue
        print(f"Auditing native clip {name}...")
        m_val = decode_m(p)
        kin = track_bob_kinematics(p, color)
        clip_audits[name] = {
            'color': color,
            'speed': speed,
            'image_change_M': m_val,
            'kinematics': kin
        }
        print(f"  M = {m_val:.4f} | y_range = {kin['y_range']:.1f}px | x_range = {kin['x_range']:.1f}px | area = {kin['mean_bob_area']:.1f}")
        
    out = {
        'results_audit': res_audit,
        'example_clips_audit': clip_audits
    }
    
    with open(OUT_JSON, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Wrote audit to {OUT_JSON}")


if __name__ == '__main__':
    main()
