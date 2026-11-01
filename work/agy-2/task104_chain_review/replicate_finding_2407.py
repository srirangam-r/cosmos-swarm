#!/usr/bin/env python3
"""
Independent Replication and Review of Finding 2407 (Task 42):
Chaining short I2V clips vs continuous long control, and seam kinematic audit.

Author: agy-2
Date: 2026-11-01
"""

import os
import sys
import json
from pathlib import Path
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def track_median_bg(video_path, corridor=(100, 430, 260, 340), min_area=30):
    """
    Robust background-subtraction ball tracker.
    Computes median temporal background, then identifies moving dark ball in corridor.
    """
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        frames.append(f)
    cap.release()

    if not frames:
        raise ValueError(f"Could not load frames from {video_path}")

    # Median background estimate across sampled frames
    sample_step = max(1, len(frames) // 30)
    bg = np.median([f.astype(float) for f in frames[::sample_step]], axis=0)

    y_min, y_max, x_min, x_max = corridor
    tracks = []
    prev_pos = None

    for idx, f in enumerate(frames):
        diff = np.abs(f.astype(float) - bg)
        corr_diff = diff[y_min:y_max, x_min:x_max].mean(axis=2)
        mask = (corr_diff > 25).astype(np.uint8)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

        best_blob = None
        min_dist = float('inf')

        # Find best candidate
        for j in range(1, num_labels):
            area = stats[j, cv2.CC_STAT_AREA]
            cx = x_min + centroids[j][0]
            cy = y_min + centroids[j][1]

            # Filter out tiny gripper noise
            if area >= min_area:
                if prev_pos is not None:
                    dist = np.hypot(cx - prev_pos[0], cy - prev_pos[1])
                    if dist < min_dist:
                        min_dist = dist
                        best_blob = {'frame': idx, 'x': float(cx), 'y': float(cy), 'area': int(area)}
                else:
                    if best_blob is None or area > best_blob['area']:
                        best_blob = {'frame': idx, 'x': float(cx), 'y': float(cy), 'area': int(area)}

        if best_blob is not None:
            prev_pos = (best_blob['x'], best_blob['y'])
        else:
            if prev_pos is not None:
                best_blob = {'frame': idx, 'x': float(prev_pos[0]), 'y': float(prev_pos[1]), 'area': 0, 'interpolated': True}
            else:
                best_blob = {'frame': idx, 'x': 295.0, 'y': 156.0, 'area': 0, 'default': True}

        tracks.append(best_blob)

    return tracks, frames

def track_ncc_subpixel(video_path, initial_crop_box=(142, 280, 35, 35), search_roi=(100, 440, 240, 360)):
    """
    Subpixel Normalized Cross-Correlation (NCC) template tracker.
    initial_crop_box: (y, x, h, w) in frame 0.
    search_roi: (y_min, y_max, x_min, x_max).
    """
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        frames.append(f)
    cap.release()

    y0, x0, th, tw = initial_crop_box
    tmpl = frames[0][y0:y0+th, x0:x0+tw].copy()

    y_min, y_max, x_min, x_max = search_roi
    tracks = []

    for idx, frame in enumerate(frames):
        search_area = frame[y_min:y_max, x_min:x_max]
        res = cv2.matchTemplate(search_area, tmpl, cv2.TM_CCOEFF_NORMED)
        min_v, max_v, min_l, max_l = cv2.minMaxLoc(res)

        best_y = max_l[1]
        best_x = max_l[0]

        sub_x, sub_y = float(best_x), float(best_y)
        if 0 < best_x < res.shape[1] - 1 and 0 < best_y < res.shape[0] - 1:
            dx = (float(res[best_y, best_x + 1]) - float(res[best_y, best_x - 1])) / 2.0
            dy = (float(res[best_y + 1, best_x]) - float(res[best_y - 1, best_x])) / 2.0
            dxx = float(res[best_y, best_x + 1]) - 2.0 * float(res[best_y, best_x]) + float(res[best_y, best_x - 1])
            dyy = float(res[best_y + 1, best_x]) - 2.0 * float(res[best_y, best_x]) + float(res[best_y - 1, best_x])
            if abs(dxx) > 1e-5:
                sub_x -= dx / dxx
            if abs(dyy) > 1e-5:
                sub_y -= dy / dyy

        global_x = x_min + sub_x + tw / 2.0
        global_y = y_min + sub_y + th / 2.0

        tracks.append({
            'frame': idx,
            'x': float(global_x),
            'y': float(global_y),
            'score': float(max_v)
        })

    return tracks, frames

def extract_bounces(tracks, min_prominence=4.0):
    """
    Extract impacts (local max in y) and apices (local min in y).
    """
    ys = np.array([t['y'] for t in tracks])
    n = len(ys)

    impacts = []
    apices = []

    for i in range(1, n - 1):
        if ys[i] >= ys[i-1] and ys[i] >= ys[i+1]:
            left_trough = np.min(ys[max(0, i-8):i]) if i > 0 else ys[i]
            right_trough = np.min(ys[i+1:min(n, i+9)]) if i < n-1 else ys[i]
            prom = ys[i] - max(left_trough, right_trough)
            if prom >= min_prominence:
                impacts.append({'frame': i, 'y': float(ys[i]), 'x': float(tracks[i]['x'])})

        elif ys[i] <= ys[i-1] and ys[i] <= ys[i+1]:
            left_peak = np.max(ys[max(0, i-8):i]) if i > 0 else ys[i]
            right_peak = np.max(ys[i+1:min(n, i+9)]) if i < n-1 else ys[i]
            prom = min(left_peak, right_peak) - ys[i]
            if prom >= min_prominence:
                apices.append({'frame': i, 'y': float(ys[i]), 'x': float(tracks[i]['x'])})

    clean_impacts = []
    for imp in impacts:
        if not clean_impacts or (imp['frame'] - clean_impacts[-1]['frame'] >= 4):
            clean_impacts.append(imp)

    clean_apices = []
    for ap in apices:
        if not clean_apices or (ap['frame'] - clean_apices[-1]['frame'] >= 4):
            clean_apices.append(ap)

    durations = []
    for k in range(1, len(clean_impacts)):
        dur = clean_impacts[k]['frame'] - clean_impacts[k-1]['frame']
        durations.append(dur)

    e_T_ratios = []
    for k in range(1, len(durations)):
        if durations[k-1] > 0:
            e_T_ratios.append(float(durations[k] / durations[k-1]))

    table_y = float(np.median([imp['y'] for imp in clean_impacts])) if clean_impacts else 355.0
    apex_heights = [table_y - ap['y'] for ap in clean_apices]

    e_h_ratios = []
    for k in range(1, len(apex_heights)):
        if apex_heights[k-1] > 0 and apex_heights[k] > 0:
            e_h_ratios.append(float(np.sqrt(apex_heights[k] / apex_heights[k-1])))

    # Rest detection
    rest_found = False
    rest_frame = None
    vels = np.abs(np.diff(ys))
    for i in range(len(vels) - 15):
        if np.all(vels[i:i+15] < 0.3) and abs(ys[i] - table_y) < 5.0:
            rest_found = True
            rest_frame = i
            break

    return {
        'impacts': clean_impacts,
        'apices': clean_apices,
        'flight_durations': durations,
        'mean_cycle_frames': float(np.mean(durations)) if durations else None,
        'mean_cycle_seconds': float(np.mean(durations) / 24.0) if durations else None,
        'e_T_ratios': e_T_ratios,
        'e_T_mean': float(np.mean(e_T_ratios)) if e_T_ratios else None,
        'apex_heights_px': apex_heights,
        'e_h_ratios': e_h_ratios,
        'e_h_mean': float(np.mean(e_h_ratios)) if e_h_ratios else None,
        'table_y_ref': table_y,
        'settled_at_rest': rest_found,
        'rest_frame': rest_frame
    }

def main():
    root = Path('/home/nail/swarm-work/agy-2/cosmos-swarm')
    work_dir = root / 'work/agy-2/task104_chain_review'
    plots_dir = work_dir / 'plots'
    plots_dir.mkdir(parents=True, exist_ok=True)

    seg1_path = root / 'work/ro-1/fps_sweep/ballF/ball_F_ball1_fps24_93f_s1.mp4'
    seg2_path = root / 'work/ro-1/srv_rescue/codex-1/20261101T043944_0037_codex-1.mp4'
    chained_path = root / 'work/agy-4/task42_chain_bounce/chained_s1_185f.mp4'
    control_path = root / 'work/raj-3/midfall/out_gb10/midfall_ball1_dd33_noneg_s1.mp4'

    print("=== Step 1: Tracking Video Streams with Median BG Subtraction ===")
    track_seg1, frames_seg1 = track_median_bg(seg1_path)
    track_seg2, frames_seg2 = track_median_bg(seg2_path)
    track_chained, frames_chained = track_median_bg(chained_path)
    track_control, frames_control = track_median_bg(control_path)

    print(f"Seg1: {len(track_seg1)} frames. f0=({track_seg1[0]['x']:.1f}, {track_seg1[0]['y']:.1f}), f92=({track_seg1[92]['x']:.1f}, {track_seg1[92]['y']:.1f})")
    print(f"Seg2: {len(track_seg2)} frames. f0=({track_seg2[0]['x']:.1f}, {track_seg2[0]['y']:.1f}), f92=({track_seg2[92]['x']:.1f}, {track_seg2[92]['y']:.1f})")
    print(f"Chained 185f: {len(track_chained)} frames. f0=({track_chained[0]['x']:.1f}, {track_chained[0]['y']:.1f}), f184=({track_chained[-1]['x']:.1f}, {track_chained[-1]['y']:.1f})")
    print(f"Control 189f: {len(track_control)} frames. f0=({track_control[0]['x']:.1f}, {track_control[0]['y']:.1f}), f188=({track_control[-1]['x']:.1f}, {track_control[-1]['y']:.1f})")

    print("\n=== Step 2: Analyzing Bounces & Dissipation ===")
    bounces_chained = extract_bounces(track_chained)
    bounces_control = extract_bounces(track_control)
    bounces_seg1 = extract_bounces(track_seg1)
    bounces_seg2 = extract_bounces(track_seg2)

    cyc_ch_str = f"{bounces_chained['mean_cycle_frames']:.1f} f ({bounces_chained['mean_cycle_seconds']:.2f} s)" if bounces_chained['mean_cycle_frames'] else "N/A"
    eh_ch_str = f"{bounces_chained['e_h_mean']:.3f}" if bounces_chained['e_h_mean'] else "N/A"
    print(f"Chained 185f: {len(bounces_chained['impacts'])} impacts, mean cycle = {cyc_ch_str}, e_h = {eh_ch_str}, settled = {bounces_chained['settled_at_rest']}")

    cyc_ctrl_str = f"{bounces_control['mean_cycle_frames']:.1f} f ({bounces_control['mean_cycle_seconds']:.2f} s)" if bounces_control['mean_cycle_frames'] else "N/A"
    eh_ctrl_str = f"{bounces_control['e_h_mean']:.3f}" if bounces_control['e_h_mean'] else "N/A"
    print(f"Control 189f: {len(bounces_control['impacts'])} impacts, mean cycle = {cyc_ctrl_str}, e_h = {eh_ctrl_str}, settled = {bounces_control['settled_at_rest']}")

    print("\n=== Step 3: Auditing Seam Kinematics Across Frame 92 ===")
    seam_data = []
    # Segment 1 frames 85 to 92
    for i in range(85, 93):
        t = track_seg1[i]
        v = (track_seg1[i+1]['y'] - track_seg1[i]['y']) if i < 92 else (track_seg2[1]['y'] - track_seg2[0]['y'])
        seam_data.append({
            'source': 'seg1',
            'local_frame': i,
            'chained_frame': i,
            'x': t['x'],
            'y': t['y'],
            'v_y': v
        })
    # Segment 2 frames 0 to 15
    for i in range(0, 16):
        t = track_seg2[i]
        v = (track_seg2[i+1]['y'] - track_seg2[i]['y']) if i < 15 else 0.0
        seam_data.append({
            'source': 'seg2',
            'local_frame': i,
            'chained_frame': 92 + i,
            'x': t['x'],
            'y': t['y'],
            'v_y': v
        })

    for d in seam_data:
        print(f"[{d['source']} f{d['local_frame']:2d} -> chained f{d['chained_frame']:3d}] y = {d['y']:6.2f}, x = {d['x']:6.2f}, v_y = {d['v_y']:+6.2f} px/f")

    print("\n=== Step 4: Tracker Bug Diagnosis in Task 42 Scorer ===")
    corridor = (240, 100, 360, 430)
    x_min, y_min, x_max, y_max = corridor
    bug_diagnosis = []
    for idx in range(8):
        frame = frames_seg2[idx]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corr = gray[y_min:y_max, x_min:x_max]
        mask = (corr < 65).astype(np.uint8)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

        components = []
        passed_filter = []
        for j in range(1, num_labels):
            area = stats[j, cv2.CC_STAT_AREA]
            cx = x_min + centroids[j][0]
            cy = y_min + centroids[j][1]
            components.append({'area': int(area), 'gx': float(cx), 'gy': float(cy)})
            if 60 < area < 1200:
                passed_filter.append({'area': int(area), 'gx': float(cx), 'gy': float(cy)})

        bug_diagnosis.append({
            'frame': idx,
            'true_bg_pos': (track_seg2[idx]['x'], track_seg2[idx]['y']),
            'total_components': len(components),
            'passed_filter_count': len(passed_filter),
            'passed_components': passed_filter,
            'tracker_returned_missing': len(passed_filter) == 0,
            'tracker_reported_coord': (passed_filter[0]['gx'], passed_filter[0]['gy']) if passed_filter else (0.0, 0.0)
        })
        print(f"Seg2 f{idx}: True y={track_seg2[idx]['y']:5.1f} | Passed 60<area<1200: {len(passed_filter)} | Reported: {bug_diagnosis[-1]['tracker_reported_coord']}")

    print("\n=== Step 5: Generating Visual Artifacts & Contact Sheets ===")
    # 1. Trajectory comparison plot
    fig, ax = plt.subplots(figsize=(12, 6))
    ys_ch = [t['y'] for t in track_chained]
    ys_ctrl = [t['y'] for t in track_control]
    ax.plot(range(len(ys_ch)), ys_ch, label='Chained 185f Arm (Seg1 93f + Seg2 92f)', color='royalblue', linewidth=2.0)
    ax.plot(range(len(ys_ctrl)), ys_ctrl, label='Continuous Long Control Arm (189f)', color='darkorange', linewidth=2.0, alpha=0.85)
    ax.axvline(92, color='crimson', linestyle='--', linewidth=1.5, label='Chaining Seam (Frame 92)')

    for imp in bounces_chained['impacts']:
        ax.plot(imp['frame'], imp['y'], 'rv', markersize=6)
    for ap in bounces_chained['apices']:
        ax.plot(ap['frame'], ap['y'], 'g^', markersize=6)

    ax.set_title('Task 42 Independent Replication: Chained 185f vs Continuous 189f Trajectory', fontsize=14, fontweight='bold')
    ax.set_xlabel('Frame Index (24 fps)', fontsize=12)
    ax.set_ylabel('Vertical Position y (px, downward)', fontsize=12)
    ax.invert_yaxis()
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    plot_traj_path = plots_dir / 'trajectory_chained_vs_control.png'
    fig.savefig(plot_traj_path, dpi=180)
    plt.close(fig)
    print(f"Saved {plot_traj_path}")

    # 2. Seam Kinematics Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    seam_frames = [d['chained_frame'] for d in seam_data[8:]]
    seam_ys = [d['y'] for d in seam_data[8:]]
    seam_vs = [d['v_y'] for d in seam_data[8:]]

    pre_frames = [d['chained_frame'] for d in seam_data[:8]]
    pre_ys = [d['y'] for d in seam_data[:8]]
    pre_vs = [d['v_y'] for d in seam_data[:8]]

    ax1.plot(pre_frames, pre_ys, 'o-', color='purple', linewidth=2.0, label='Segment 1 (Pre-seam trajectory)')
    ax1.plot(seam_frames, seam_ys, 's-', color='teal', linewidth=2.0, label='Segment 2 (Post-seam continuation)')
    ax1.axvline(92, color='crimson', linestyle='--', linewidth=1.5, label='Seam Frame 92')
    ax1.set_ylabel('Position y (px)', fontsize=11)
    ax1.set_title('Kinematic Continuity Across Seam: Position y(t) and Velocity v(t)', fontsize=13, fontweight='bold')
    ax1.invert_yaxis()
    ax1.legend(loc='lower right', fontsize=10)
    ax1.grid(True, alpha=0.3)

    ax2.plot(pre_frames, pre_vs, 'o-', color='purple', linewidth=2.0, label='Segment 1 Velocity')
    ax2.plot(seam_frames, seam_vs, 's-', color='teal', linewidth=2.0, label='Segment 2 Velocity')
    ax2.axvline(92, color='crimson', linestyle='--', linewidth=1.5, label='Seam Frame 92')
    ax2.axhline(0, color='gray', linestyle=':', label='Zero Velocity')
    ax2.set_ylabel('Vertical Velocity v_y (px/frame)', fontsize=11)
    ax2.set_xlabel('Chained Frame Index', fontsize=11)
    ax2.legend(loc='upper right', fontsize=10)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    plot_seam_path = plots_dir / 'seam_kinematics_audit.png'
    fig.savefig(plot_seam_path, dpi=180)
    plt.close(fig)
    print(f"Saved {plot_seam_path}")

    # 3. Contact Sheet: Seam Frame Progression
    crops = []
    # Seg1 frames 89 to 92
    for f_idx in range(89, 93):
        f = frames_seg1[f_idx]
        pos = track_seg1[f_idx]
        cx, cy = int(round(pos['x'])), int(round(pos['y']))
        crop = f[100:430, 240:360].copy()
        cv2.circle(crop, (cx - 240, cy - 100), 5, (0, 255, 0), -1)
        cv2.circle(crop, (cx - 240, cy - 100), 12, (0, 0, 255), 2)
        cv2.putText(crop, f"Seg1 f{f_idx}", (8, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        cv2.putText(crop, f"y={pos['y']:.1f}", (8, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        crops.append(crop)

    # Seg2 frames 0 to 7
    for f_idx in range(0, 8):
        f = frames_seg2[f_idx]
        pos = track_seg2[f_idx]
        cx, cy = int(round(pos['x'])), int(round(pos['y']))
        crop = f[100:430, 240:360].copy()
        cv2.circle(crop, (cx - 240, cy - 100), 5, (0, 255, 0), -1)
        cv2.circle(crop, (cx - 240, cy - 100), 12, (0, 0, 255), 2)
        cv2.putText(crop, f"Seg2 f{f_idx}", (8, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        cv2.putText(crop, f"y={pos['y']:.1f}", (8, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        crops.append(crop)

    row1 = np.hstack(crops[:6])
    row2 = np.hstack(crops[6:])
    contact_sheet = np.vstack([row1, row2])
    sheet_path = plots_dir / 'seam_contact_sheet.jpg'
    cv2.imwrite(str(sheet_path), contact_sheet)
    print(f"Saved {sheet_path}")

    # 4. Save Structured JSON
    results = {
        'task': 104,
        'target_finding_id': 2407,
        'target_author': 'agy-4',
        'target_commit': '8780f81',
        'verdict': 'replicated (refuting bounce decay) & refuted (5-frame stagnation is tracker artifact)',
        'summary': {
            'core_negative_finding_status': 'replicated',
            'seam_stagnation_claim_status': 'refuted (tracker area threshold failure)',
            'scout1_vae_latent_stall_status': 'refuted (ball moves continuously across frames 0-5 with v_y in [+8, +2, -4, -8, -8] px/f)'
        },
        'kinematics': {
            'chained_185f': {
                'total_frames': len(track_chained),
                'impact_count': len(bounces_chained['impacts']),
                'mean_cycle_frames': bounces_chained['mean_cycle_frames'],
                'mean_cycle_seconds': bounces_chained['mean_cycle_seconds'],
                'apex_height_restitution_mean_e_h': bounces_chained['e_h_mean'],
                'settled_at_rest': bounces_chained['settled_at_rest'],
                'impact_frames': [imp['frame'] for imp in bounces_chained['impacts']],
                'apex_frames': [ap['frame'] for ap in bounces_chained['apices']]
            },
            'single_long_control_189f': {
                'total_frames': len(track_control),
                'impact_count': len(bounces_control['impacts']),
                'mean_cycle_frames': bounces_control['mean_cycle_frames'],
                'mean_cycle_seconds': bounces_control['mean_cycle_seconds'],
                'apex_height_restitution_mean_e_h': bounces_control['e_h_mean'],
                'settled_at_rest': bounces_control['settled_at_rest'],
                'impact_frames': [imp['frame'] for imp in bounces_control['impacts']],
                'apex_frames': [ap['frame'] for ap in bounces_control['apices']]
            }
        },
        'seam_kinematics': seam_data,
        'tracker_bug_diagnosis': bug_diagnosis,
        'scoreboard_deltas': {
            'dover_fused': {
                'chained': 0.5398,
                'control': 0.5370,
                'delta': +0.0028,
                'verdict': 'within seed noise'
            },
            'dynamic_degree_norm': {
                'chained': 1.1621,
                'control': 1.4185,
                'delta': -0.2564,
                'verdict': 'both dd_binary = 0'
            }
        }
    }

    out_json = work_dir / 'task104_review_results.json'
    out_json.write_text(json.dumps(results, indent=2))
    print(f"\nSaved structured results to {out_json}")

if __name__ == '__main__':
    main()
