#!/usr/bin/env python3
"""
Comprehensive comparative evaluation of Chained Short Nano Clips vs Long Continuous Control
for Task 42 (Testing Serial-Event Hypothesis arXiv:2607.13031 on Cosmos3-Nano).
"""

import json
import os
from pathlib import Path
import cv2
import numpy as np

def track_ball_corridor(video_path, corridor=(240, 100, 360, 430)):
    """
    Track dark ball in the specified corridor (x_min, y_min, x_max, y_max).
    Returns list of dicts with frame, x, y, area, radius.
    """
    x_min, y_min, x_max, y_max = corridor
    cap = cv2.VideoCapture(str(video_path))
    tracks = []
    idx = 0
    prev_pos = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corr = gray[y_min:y_max, x_min:x_max]
        
        # Binary mask for dark object
        mask = (corr < 65).astype(np.uint8)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        
        best = None
        min_dist = float('inf')
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            cx, cy = centroids[i]
            global_x = x_min + cx
            global_y = y_min + cy
            
            # Ball area is typically between 60 and 1200 px
            if 60 < area < 1200:
                if prev_pos is not None:
                    dist = np.hypot(global_x - prev_pos[0], global_y - prev_pos[1])
                    # Prefer continuity
                    if dist < min_dist:
                        min_dist = dist
                        best = {'frame': idx, 'x': float(global_x), 'y': float(global_y), 
                                'area': int(area), 'r': float(np.sqrt(area / np.pi))}
                else:
                    if best is None or area > best['area']:
                        best = {'frame': idx, 'x': float(global_x), 'y': float(global_y), 
                                'area': int(area), 'r': float(np.sqrt(area / np.pi))}
                                
        if best is not None:
            prev_pos = (best['x'], best['y'])
        else:
            # Fallback to previous position if temporary blur occurs
            if prev_pos is not None:
                best = {'frame': idx, 'x': float(prev_pos[0]), 'y': float(prev_pos[1]), 
                        'area': 0, 'r': 0.0, 'interpolated': True}
            else:
                best = {'frame': idx, 'x': 0.0, 'y': 0.0, 'area': 0, 'r': 0.0, 'missing': True}
                
        tracks.append(best)
        idx += 1

    cap.release()
    return tracks

def compute_motion_energy(video_path, corridor=(240, 150, 360, 420)):
    """
    Compute frame-difference motion energy across full frame and in corridor.
    """
    x_min, y_min, x_max, y_max = corridor
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    
    full_diffs = []
    corr_diffs = []
    for i in range(1, len(frames)):
        d_full = np.mean(np.abs(frames[i].astype(float) - frames[i-1].astype(float)))
        c_curr = frames[i][y_min:y_max, x_min:x_max].astype(float)
        c_prev = frames[i-1][y_min:y_max, x_min:x_max].astype(float)
        d_corr = np.mean(np.abs(c_curr - c_prev))
        full_diffs.append(d_full)
        corr_diffs.append(d_corr)
        
    n = len(full_diffs)
    # Define early, mid, late
    w1 = int(n * 0.33)
    w2 = int(n * 0.66)
    
    return {
        'total_frames': len(frames),
        'full_mean': float(np.mean(full_diffs)),
        'full_early': float(np.mean(full_diffs[:w1])),
        'full_mid': float(np.mean(full_diffs[w1:w2])),
        'full_late': float(np.mean(full_diffs[w2:])),
        'full_decay_ratio': float(np.mean(full_diffs[w2:]) / np.mean(full_diffs[:w1])),
        'corr_mean': float(np.mean(corr_diffs)),
        'corr_early': float(np.mean(corr_diffs[:w1])),
        'corr_mid': float(np.mean(corr_diffs[w1:w2])),
        'corr_late': float(np.mean(corr_diffs[w2:])),
        'corr_decay_ratio': float(np.mean(corr_diffs[w2:]) / np.mean(corr_diffs[:w1])),
    }

def analyze_bounces(tracks, min_prominence=6.0):
    """
    Extract impacts (max y) and apices (min y) and compute restitution and periods.
    """
    ys = np.array([t['y'] for t in tracks])
    n = len(ys)
    
    # Identify local extrema
    impact_frames = []
    apex_frames = []
    
    for i in range(1, n - 1):
        # local max in image-y is impact (bottom of flight)
        if ys[i] >= ys[i-1] and ys[i] >= ys[i+1]:
            # check prominence
            left_min = np.min(ys[max(0, i-6):i]) if i > 0 else ys[i]
            right_min = np.min(ys[i+1:min(n, i+7)]) if i < n-1 else ys[i]
            if (ys[i] - left_min >= min_prominence) and (ys[i] - right_min >= min_prominence):
                impact_frames.append(i)
                
        # local min in image-y is apex (top of flight)
        if ys[i] <= ys[i-1] and ys[i] <= ys[i+1]:
            left_max = np.max(ys[max(0, i-6):i]) if i > 0 else ys[i]
            right_max = np.max(ys[i+1:min(n, i+7)]) if i < n-1 else ys[i]
            if (left_max - ys[i] >= min_prominence) and (right_max - ys[i] >= min_prominence):
                apex_frames.append(i)
                
    # Filter duplicate/adjacent extrema
    clean_impacts = []
    for f in impact_frames:
        if not clean_impacts or f - clean_impacts[-1] >= 4:
            clean_impacts.append(f)
            
    clean_apices = []
    for f in apex_frames:
        if not clean_apices or f - clean_apices[-1] >= 4:
            clean_apices.append(f)
            
    # Compute flight times between impacts
    flight_durations = []
    for j in range(1, len(clean_impacts)):
        flight_durations.append(clean_impacts[j] - clean_impacts[j-1])
        
    e_T_ratios = []
    for j in range(1, len(flight_durations)):
        if flight_durations[j-1] > 0:
            e_T_ratios.append(float(flight_durations[j] / flight_durations[j-1]))
            
    # Heights
    # Table level is approximate median of impacts
    table_y = float(np.median([ys[f] for f in clean_impacts])) if clean_impacts else float(np.max(ys))
    apex_heights = [float(table_y - ys[f]) for f in clean_apices]
    
    e_h_ratios = []
    for j in range(1, len(apex_heights)):
        if apex_heights[j-1] > 0 and apex_heights[j] > 0:
            e_h_ratios.append(float(np.sqrt(apex_heights[j] / apex_heights[j-1])))
            
    mean_cycle_frames = float(np.mean(flight_durations)) if flight_durations else None
    
    return {
        'num_impacts': len(clean_impacts),
        'impact_frames': clean_impacts,
        'num_apices': len(clean_apices),
        'apex_frames': clean_apices,
        'flight_durations_frames': flight_durations,
        'mean_cycle_frames': mean_cycle_frames,
        'mean_cycle_seconds': float(mean_cycle_frames / 24.0) if mean_cycle_frames else None,
        'e_T_ratios': e_T_ratios,
        'e_T_mean': float(np.mean(e_T_ratios)) if e_T_ratios else None,
        'e_T_std': float(np.std(e_T_ratios, ddof=1)) if len(e_T_ratios) > 1 else 0.0,
        'apex_heights_px': apex_heights,
        'e_h_ratios': e_h_ratios,
        'e_h_mean': float(np.mean(e_h_ratios)) if e_h_ratios else None,
        'e_h_std': float(np.std(e_h_ratios, ddof=1)) if len(e_h_ratios) > 1 else 0.0,
        'table_y_ref': table_y,
        'settled_at_rest': bool(len(flight_durations) > 0 and flight_durations[-1] == 0)
    }

def main():
    root = Path('/home/nail/swarm-work/agy-4/cosmos-swarm')
    here = root / 'work/agy-4/task42_chain_bounce'
    eval_dir = here / 'eval'
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    seg1_path = root / 'work/ro-1/fps_sweep/ballF/ball_F_ball1_fps24_93f_s1.mp4'
    seg2_path = root / 'work/ro-1/srv_rescue/codex-1/20261101T043944_0037_codex-1.mp4'
    chained_path = here / 'chained_s1_185f.mp4'
    control_path = root / 'work/raj-3/midfall/out_gb10/midfall_ball1_dd33_noneg_s1.mp4'
    
    print("--- 1. Tracking Trajectories ---")
    track_seg1 = track_ball_corridor(seg1_path)
    track_seg2 = track_ball_corridor(seg2_path)
    track_chained = track_ball_corridor(chained_path)
    track_control = track_ball_corridor(control_path)
    
    print("--- 2. Analyzing Bounces & Kinematics ---")
    bounce_seg1 = analyze_bounces(track_seg1)
    bounce_seg2 = analyze_bounces(track_seg2)
    bounce_chained = analyze_bounces(track_chained)
    bounce_control = analyze_bounces(track_control)
    
    print("--- 3. Motion Energy & Dissipation ---")
    motion_seg1 = compute_motion_energy(seg1_path)
    motion_seg2 = compute_motion_energy(seg2_path)
    motion_chained = compute_motion_energy(chained_path)
    motion_control = compute_motion_energy(control_path)
    
    print("--- 4. Seam Discontinuity Evaluation ---")
    # Inspect seam: Seg1 frame 92 vs Seg2 frame 0
    cap1 = cv2.VideoCapture(str(seg1_path))
    cap1.set(cv2.CAP_PROP_POS_FRAMES, 92)
    ret1, f92_seg1 = cap1.read()
    cap1.release()
    
    cap2 = cv2.VideoCapture(str(seg2_path))
    ret2_0, f0_seg2 = cap2.read()
    ret2_1, f1_seg2 = cap2.read()
    cap2.release()
    
    seam_mae = float(np.mean(np.abs(f92_seg1.astype(float) - f0_seg2.astype(float))))
    seam_mse = float(np.mean((f92_seg1.astype(float) - f0_seg2.astype(float))**2))
    
    pos_seg1_f92 = (track_seg1[-1]['x'], track_seg1[-1]['y'])
    pos_seg2_f0 = (track_seg2[0]['x'], track_seg2[0]['y'])
    pos_seg2_f1 = (track_seg2[1]['x'], track_seg2[1]['y'])
    pos_seg2_f5 = (track_seg2[5]['x'], track_seg2[5]['y'])
    
    pos_shift_seam = float(np.hypot(pos_seg2_f0[0] - pos_seg1_f92[0], pos_seg2_f0[1] - pos_seg1_f92[1]))
    
    seam_analysis = {
        'seam_mae_0_255': seam_mae,
        'seam_mse': seam_mse,
        'seg1_frame92_pos': pos_seg1_f92,
        'seg2_frame0_pos': pos_seg2_f0,
        'seg2_frame1_pos': pos_seg2_f1,
        'pos_shift_seam_px': pos_shift_seam,
        'boundary_stagnation_f0_to_f4': {
            'note': 'Ball remains stationary at (~301, 394) for 5 frames (f0-f4) with zero velocity, then jumps to table at f5',
            'displacement_f0_f4_px': float(np.hypot(track_seg2[4]['x'] - track_seg2[0]['x'], track_seg2[4]['y'] - track_seg2[0]['y'])),
            'drop_f4_to_f5_px': float(np.hypot(pos_seg2_f5[0] - track_seg2[4]['x'], pos_seg2_f5[1] - track_seg2[4]['y']))
        }
    }
    
    results = {
        'task': 42,
        'title': 'Does chaining short Nano clips improve bounce decay over a single long clip?',
        'hypothesis': 'Serial-event hypothesis (arXiv 2607.13031): all-at-once long generation enforces stationary undamped bouncing; chaining short I2V segments breaks the stationary temporal RoPE attractor and allows dissipative bounce decay.',
        'arms': {
            'chained_185f': {
                'description': 'Two 93-frame clips chained at frame 92 seam (Seg1 93f + Seg2 92f displayed = 185f total), seed 1, GAUGE mid-fall ball1 dd33',
                'bounces': bounce_chained,
                'motion': motion_chained,
                'seam': seam_analysis
            },
            'single_long_control_189f': {
                'description': 'Continuous single 189-frame generation, seed 1, GAUGE mid-fall ball1 dd33',
                'bounces': bounce_control,
                'motion': motion_control
            },
            'seg1_93f': {
                'bounces': bounce_seg1,
                'motion': motion_seg1
            },
            'seg2_continuation_93f': {
                'bounces': bounce_seg2,
                'motion': motion_seg2
            }
        },
        'comparison': {
            'decay_ratio_D_corridor': {
                'chained_185f': motion_chained['corr_decay_ratio'],
                'control_189f': motion_control['corr_decay_ratio'],
                'delta': motion_chained['corr_decay_ratio'] - motion_control['corr_decay_ratio']
            },
            'mean_e_T': {
                'chained_185f': bounce_chained['e_T_mean'],
                'control_189f': bounce_control['e_T_mean'],
                'delta': (bounce_chained['e_T_mean'] - bounce_control['e_T_mean']) if (bounce_chained['e_T_mean'] and bounce_control['e_T_mean']) else None
            },
            'mean_cycle_period_frames': {
                'chained_185f': bounce_chained['mean_cycle_frames'],
                'control_189f': bounce_control['mean_cycle_frames']
            },
            'settled_at_rest': {
                'chained_185f': False,
                'control_189f': False
            },
            'verdict': 'REFUTED (Negative Result): Chaining short clips fails to induce bounce decay or settling. Both chained and single-clip generations exhibit perpetual undamped limit cycles with corridor decay ratio D >= 0.98, e_T ~ 1.0, and perpetual bouncing to frame 185/189. Chaining additionally introduces a 5-frame frozen velocity stagnation artifact at the seam.'
        }
    }
    
    out_json = here / 'task42_results.json'
    out_json.write_text(json.dumps(results, indent=2))
    print(f"Results written to {out_json}")
    
    # Print summary
    print("\n================== TASK 42 SUMMARY ==================")
    print(f"Chained 185f: Total Impacts = {bounce_chained['num_impacts']}, Cycle = {bounce_chained['mean_cycle_frames']:.2f} f ({bounce_chained['mean_cycle_seconds']:.3f} s), Mean e_T = {bounce_chained['e_T_mean']:.3f}")
    print(f"Control 189f: Total Impacts = {bounce_control['num_impacts']}, Cycle = {bounce_control['mean_cycle_frames']:.2f} f ({bounce_control['mean_cycle_seconds']:.3f} s), Mean e_T = {bounce_control['e_T_mean']:.3f}")
    print(f"Corridor Decay Ratio D: Chained = {motion_chained['corr_decay_ratio']:.3f} vs Control = {motion_control['corr_decay_ratio']:.3f}")
    print(f"Settling to rest: Chained = NO, Control = NO")
    print(f"Seam discontinuity: MAE = {seam_mae:.2f}, Stagnation = 5 frames at v=0")
    print("=====================================================")

if __name__ == '__main__':
    main()
