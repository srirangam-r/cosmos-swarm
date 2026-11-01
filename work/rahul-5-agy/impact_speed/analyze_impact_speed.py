#!/usr/bin/env python3
"""Task 52: Does Nano's bounce decay (e_T) depend on impact speed?
Evaluates 8 clips across a 4-condition drop height ladder (34.5cm, 24.4cm, 9.4cm, 5.3cm;
impact speeds 2.60 m/s down to 1.02 m/s) generated from real GAUGE ball 1 first frames.
"""
import os, sys, json
import cv2, numpy as np
from scipy.signal import find_peaks

def analyze_clip(clip_path, seed_xy, fps=24.0):
    cap = cv2.VideoCapture(clip_path)
    ret, f0 = cap.read()
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sx, sy = seed_xy
    hw = 12
    gray0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    tmpl = gray0[max(0, sy-hw):min(f0.shape[0], sy+hw+1), max(0, sx-hw):min(f0.shape[1], sx+hw+1)]
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    traj = []
    cur_x, cur_y = sx, sy
    for i in range(n_frames):
        ret, fr = cap.read()
        if not ret: break
        gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        x_min = max(220, int(cur_x - 35))
        x_max = min(360, int(cur_x + 35))
        y_min = max(130, int(cur_y - 60))
        y_max = min(365, int(cur_y + 60))
        search = gray[y_min:y_max, x_min:x_max]
        res = cv2.matchTemplate(search, tmpl, cv2.TM_CCOEFF_NORMED)
        min_v, max_v, min_l, max_l = cv2.minMaxLoc(res)
        bx = max_l[0] + x_min + hw
        by = max_l[1] + y_min + hw
        traj.append((i, bx, by, max_v))
        if max_v > 0.4:
            cur_x, cur_y = bx, by
    cap.release()
    return traj

def main():
    clips = [
        ('dd33', 1, 'ball1_dd33_s1.mp4', (285, 150), 34.5, 2.60),
        ('dd33', 2, 'ball1_dd33_s2.mp4', (285, 150), 34.5, 2.60),
        ('dd35', 1, 'ball1_dd35_s1.mp4', (289, 204), 24.4, 2.19),
        ('dd35', 2, 'ball1_dd35_s2.mp4', (289, 204), 24.4, 2.19),
        ('dd37', 1, 'ball1_dd37_s1.mp4', (288, 285),  9.4, 1.36),
        ('dd37', 2, 'ball1_dd37_s2.mp4', (288, 285),  9.4, 1.36),
        ('dd58', 1, 'ball1_dd58_s1.mp4', (307, 307),  5.3, 1.02),
        ('dd58', 2, 'ball1_dd58_s2.mp4', (307, 307),  5.3, 1.02),
    ]
    summary = []
    for cond, seed, clip, seed_xy, drop_cm, v_imp in clips:
        clip_path = f'/home/sha/swarm-work/rahul-5-agy/impact_speed_sweep/out/{clip}'
        if not os.path.exists(clip_path):
            continue
        traj = analyze_clip(clip_path, seed_xy)
        ys = np.array([p[2] for p in traj])
        pks, _ = find_peaks(ys, prominence=15, distance=4)
        plank_pks = [p for p in pks if ys[p] > 300]
        first_imp = plank_pks[0] if len(plank_pks) > 0 else None
        
        flights = []
        rises = []
        for i in range(len(plank_pks) - 1):
            p1 = plank_pks[i]
            p2 = plank_pks[i+1]
            T_fr = p2 - p1
            apex_fr = p1 + np.argmin(ys[p1:p2+1])
            rise_px = max(ys[p1], ys[p2]) - ys[apex_fr]
            flights.append(T_fr / 24.0)
            rises.append(rise_px)
        
        e_T_ratios = [flights[i+1] / flights[i] for i in range(len(flights)-1)] if len(flights) >= 2 else []
        mean_e_T = np.mean(e_T_ratios) if e_T_ratios else None
        se_e_T = (np.std(e_T_ratios) / np.sqrt(len(e_T_ratios))) if len(e_T_ratios) > 1 else 0.0
        still_bouncing = (len(plank_pks) >= 3 and plank_pks[-1] > 70)
        
        summary.append({
            'clip': clip, 'cond': cond, 'seed': seed, 'drop_cm': drop_cm, 'v_imp': v_imp,
            'first_imp': int(first_imp) if first_imp else None,
            'n_impacts': len(plank_pks),
            'plank_pks': [int(p) for p in plank_pks],
            'flights_s': [float(f) for f in flights],
            'rises_px': [float(r) for r in rises],
            'e_T_ratios': [float(r) for r in e_T_ratios],
            'mean_e_T': float(mean_e_T) if mean_e_T is not None else None,
            'se_e_T': float(se_e_T),
            'still_bouncing': bool(still_bouncing)
        })
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
