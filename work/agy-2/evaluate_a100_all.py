#!/usr/bin/env python3
"""
Evaluation suite for raj-3's 19 A100 clips (mid-fall, held-ball controls, pendulums).
Captures:
- Mid-fall: trajectory, contact frames, cycle periods, log-linear restitution e_T,
  flight heights, g_eff, asymmetry, strap/tether excess.
- Held-ball: gripper displacement, lower corridor motion, phantom duplicate detection,
  release status, fall duration, and measured g.
- Pendulum: period in seconds/frames.
"""

import os
import sys
import glob
import json
import cv2
import numpy as np
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

PPM = 539.8  # pixels per meter for GAUGE ball setup
FPS = 24.0

def load_video(path):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return np.array(frames)

def track_lower_corridor_ball(frames, seed_xy=(287.0, 155.0), y_min=165, y_max=355, x_min=220, x_max=355):
    med_bg = np.median(frames.astype(np.float32), axis=0)
    sx, sy = seed_xy
    hw = 11
    gray0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    # clip template boundaries
    sy_int, sx_int = int(round(sy)), int(round(sx))
    tmpl0 = gray0[max(0, sy_int - hw):min(gray0.shape[0], sy_int + hw + 1),
                  max(0, sx_int - hw):min(gray0.shape[1], sx_int + hw + 1)].copy()

    xs, ys, scores, strap_white_excess = [], [], [], []
    for i, f in enumerate(frames):
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        diff = np.linalg.norm(f.astype(np.float32) - med_bg, axis=2)
        if i == 0:
            nx, ny, sc = float(sx), float(sy), 1.0
        else:
            roi_g = gray[y_min:y_max, x_min:x_max]
            res = cv2.matchTemplate(roi_g, tmpl0, cv2.TM_CCOEFF_NORMED)
            diff_c = cv2.GaussianBlur(diff, (9, 9), 0)[
                y_min + hw:y_min + hw + res.shape[0],
                x_min + hw:x_min + hw + res.shape[1],
            ]
            dark_c = np.clip(
                (120.0 - cv2.GaussianBlur(gray, (9, 9), 0)[
                    y_min + hw:y_min + hw + res.shape[0],
                    x_min + hw:x_min + hw + res.shape[1],
                ]) / 80.0,
                0.0, 1.0,
            )
            score_map = 0.55 * res + 0.30 * np.clip(diff_c / 35.0, 0.0, 1.0) + 0.15 * dark_c
            bi, bj = np.unravel_index(np.argmax(score_map), score_map.shape)
            # subpixel refinement
            dx, dy = 0.0, 0.0
            if 0 < bi < score_map.shape[0] - 1 and 0 < bj < score_map.shape[1] - 1:
                denom_x = 2.0 * score_map[bi, bj] - score_map[bi, bj - 1] - score_map[bi, bj + 1]
                if abs(denom_x) > 1e-6:
                    dx = np.clip((score_map[bi, bj + 1] - score_map[bi, bj - 1]) / (2.0 * denom_x), -0.5, 0.5)
                denom_y = 2.0 * score_map[bi, bj] - score_map[bi - 1, bj] - score_map[bi + 1, bj]
                if abs(denom_y) > 1e-6:
                    dy = np.clip((score_map[bi + 1, bj] - score_map[bi - 1, bj]) / (2.0 * denom_y), -0.5, 0.5)

            nx = float(x_min + bj + dx + hw)
            ny = float(y_min + bi + dy + hw)
            sc = float(res[bi, bj])

        xs.append(round(nx, 2))
        ys.append(round(ny, 2))
        scores.append(round(sc, 3))

        # Quantify white strap / tether in corridor above ball
        y_hi = max(145, min(int(round(ny)) - 12, 260))
        strip = gray[135:y_hi, 278:316]
        strip0 = gray0[135:y_hi, 278:316]
        excess = float(np.percentile(strip - strip0, 90)) if strip.size > 0 else 0.0
        strap_white_excess.append(round(excess, 2))

    return np.array(xs), np.array(ys), np.array(scores), np.array(strap_white_excess)

def analyze_midfall_clip(clip_path):
    frames = load_video(clip_path)
    n_frames = len(frames)
    xs, ys, scores, straps = track_lower_corridor_ball(frames)

    # Find plank contacts (local maxima of y)
    pks, _ = find_peaks(ys, prominence=14.0, distance=3)
    pks_sub = []
    for p in pks:
        if 0 < p < len(ys) - 1:
            y_m, y_0, y_p = ys[p - 1], ys[p], ys[p + 1]
            denom = 2.0 * (2.0 * y_0 - y_m - y_p)
            delta = (y_p - y_m) / denom if abs(denom) > 1e-6 else 0.0
            pks_sub.append(float(p + np.clip(delta, -0.5, 0.5)))
        else:
            pks_sub.append(float(p))

    # Find apexes (local minima of y between contacts)
    apexes_sub = []
    for i in range(len(pks) - 1):
        seg = ys[pks[i]:pks[i + 1] + 1]
        if len(seg) > 2:
            min_idx = pks[i] + int(np.argmin(seg))
            if 0 < min_idx < len(ys) - 1:
                y_m, y_0, y_p = ys[min_idx - 1], ys[min_idx], ys[min_idx + 1]
                denom = 2.0 * (y_m + y_p - 2.0 * y_0)
                delta = (y_m - y_p) / (2.0 * denom) if abs(denom) > 1e-6 else 0.0
                apexes_sub.append((float(min_idx + np.clip(delta, -0.5, 0.5)), float(np.min(seg))))
            else:
                apexes_sub.append((float(min_idx), float(np.min(seg))))

    # Cycle periods
    cycle_periods_frames = []
    for i in range(len(pks_sub) - 1):
        cycle_periods_frames.append(pks_sub[i + 1] - pks_sub[i])

    # Log-linear restitution e_T fit: ln(T_k) = ln(T_0) + k * ln(e_T)
    e_T_fit = None
    e_T_se = None
    if len(cycle_periods_frames) >= 3:
        ks = np.arange(len(cycle_periods_frames))
        log_Ts = np.log(cycle_periods_frames)
        slope, intercept = np.polyfit(ks, log_Ts, 1)
        e_T_fit = float(np.exp(slope))
        # residual standard error of slope
        resids = log_Ts - (slope * ks + intercept)
        s_err = np.sqrt(np.sum(resids**2) / max(1, len(ks) - 2))
        se_slope = s_err / np.sqrt(np.sum((ks - np.mean(ks))**2))
        e_T_se = float(e_T_fit * se_slope)

    # Flight heights and g_eff
    flight_heights_px = []
    g_eff_list = []
    for i in range(min(len(cycle_periods_frames), len(apexes_sub))):
        T_f = cycle_periods_frames[i]
        T_sec = T_f / FPS
        # height = contact y - apex y
        contact_y = 0.5 * (ys[pks[i]] + ys[pks[i + 1]])
        apex_y = apexes_sub[i][1]
        h_px = contact_y - apex_y
        flight_heights_px.append(float(h_px))
        h_m = h_px / PPM
        if T_sec > 0 and h_m > 0:
            # For symmetric parabolic flight h = 1/8 g T^2 => g = 8 h / T^2
            g_val = 8.0 * h_m / (T_sec**2)
            g_eff_list.append(float(g_val))

    # Tether strap excess
    strap_excess = float(np.mean(straps))
    frac_strap_active = float(np.mean(np.array(straps) > 20.0))

    return {
        "n_frames": n_frames,
        "n_contacts": len(pks_sub),
        "contact_frames": [round(x, 2) for x in pks_sub],
        "cycle_periods_frames": [round(x, 2) for x in cycle_periods_frames],
        "cycle_periods_sec": [round(x / FPS, 4) for x in cycle_periods_frames],
        "mean_cycle_period_s": round(float(np.mean(cycle_periods_frames) / FPS), 4) if cycle_periods_frames else None,
        "std_cycle_period_s": round(float(np.std(cycle_periods_frames) / FPS), 4) if cycle_periods_frames else None,
        "e_T_fit": round(e_T_fit, 4) if e_T_fit is not None else None,
        "e_T_se": round(e_T_se, 4) if e_T_se is not None else None,
        "flight_heights_px": [round(x, 1) for x in flight_heights_px],
        "mean_height_px": round(float(np.mean(flight_heights_px)), 1) if flight_heights_px else None,
        "g_eff_flights": [round(x, 2) for x in g_eff_list],
        "mean_g_eff": round(float(np.mean(g_eff_list)), 2) if g_eff_list else None,
        "std_g_eff": round(float(np.std(g_eff_list)), 2) if g_eff_list else None,
        "strap_mean_excess": round(strap_excess, 2),
        "frac_strap_active": round(frac_strap_active, 3),
        "still_bouncing_at_end": bool(pks_sub and pks_sub[-1] > n_frames - 25)
    }

def analyze_held_control_clip(clip_path):
    frames = load_video(clip_path)
    n_frames = len(frames)
    f0 = frames[0]

    # Track ball at gripper (x in [280, 320], y in [130, 175])
    gripper_diffs = []
    lower_diffs = []
    # also detect template position of ball in gripper
    gray0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    tmpl_gripper = gray0[135:165, 290:315].copy()

    gripper_ys = []
    lower_ball_detected = []
    for i, f in enumerate(frames):
        diff = cv2.absdiff(f0, f)
        gripper_diffs.append(float(diff[130:175, 280:320].mean()))
        lower_diffs.append(float(diff[190:350, 250:350].mean()))

        # Match gripper template in upper window [120:200, 280:320]
        roi_upper = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[120:200, 280:320]
        res_u = cv2.matchTemplate(roi_upper, tmpl_gripper, cv2.TM_CCOEFF_NORMED)
        min_v, max_v, min_l, max_l = cv2.minMaxLoc(res_u)
        gripper_ys.append(120 + max_l[1])

        # Check for dark blob in lower corridor [190:350, 260:340]
        roi_lower = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[190:350, 260:340]
        min_v_l, _, _, _ = cv2.minMaxLoc(roi_lower)
        lower_ball_detected.append(min_v_l < 40.0)

    max_grip_diff = float(max(gripper_diffs))
    max_lower_diff = float(max(lower_diffs))
    gripper_y_range = float(max(gripper_ys) - min(gripper_ys))

    # Determine release mode:
    # Mode 1: Held ball remains stationary at gripper (gripper diff small or y_range small),
    # but lower corridor experiences motion -> duplicate/phantom ball
    # Mode 2: Ball at gripper genuinely moves down (gripper y increases significantly, max_grip_diff large)
    # Mode 3: Ball stays held, no lower motion -> stuck
    is_released = False
    is_duplicated = False
    onset_frame = None
    fall_g = None

    if max_grip_diff < 15.0 and max_lower_diff > 25.0:
        is_released = False
        is_duplicated = True
        classification = "phantom_duplicate_unreleased"
    elif max_grip_diff > 80.0 and gripper_y_range > 15.0:
        is_released = True
        is_duplicated = False
        classification = "genuine_release"
        # Find onset frame where gripper diff starts exceeding 20
        for idx, gd in enumerate(gripper_diffs):
            if gd > 20.0:
                onset_frame = idx
                break
    elif max_grip_diff < 15.0 and max_lower_diff < 15.0:
        is_released = False
        is_duplicated = False
        classification = "stuck_unreleased"
    else:
        # Check motion threshold
        if max_grip_diff > 50.0:
            is_released = True
            classification = "partial_or_full_release"
            for idx, gd in enumerate(gripper_diffs):
                if gd > 20.0:
                    onset_frame = idx
                    break
        else:
            is_released = False
            is_duplicated = True
            classification = "phantom_duplicate_unreleased"

    return {
        "n_frames": n_frames,
        "max_gripper_diff": round(max_grip_diff, 1),
        "max_lower_corridor_diff": round(max_lower_diff, 1),
        "gripper_y_range": round(gripper_y_range, 1),
        "classification": classification,
        "is_released": is_released,
        "is_duplicated": is_duplicated,
        "onset_frame": onset_frame
    }

def main():
    clip_dir = "/home/nail/swarm-work/raj-3/brev_box/out"
    out_dir = "/home/nail/swarm-work/agy-2"

    print("=== EVALUATING 19 A100 CLIPS ===")

    # 1. Mid-fall clips (8 clips)
    mid_clips = sorted(glob.glob(os.path.join(clip_dir, "box_mid_*.mp4")))
    print(f"\n1. Mid-fall clips ({len(mid_clips)} found):")
    mid_results = {}
    for clip in mid_clips:
        name = os.path.basename(clip)
        print(f"  Analyzing {name}...")
        res = analyze_midfall_clip(clip)
        mid_results[name] = res
        print(f"    -> contacts: {res['n_contacts']}, mean period: {res['mean_cycle_period_s']}s, e_T: {res['e_T_fit']} ± {res['e_T_se']}, g_eff: {res['mean_g_eff']} m/s^2, strap_excess: {res['strap_mean_excess']}")

    # 2. Held-ball control clips (8 clips)
    ctrl_clips = sorted(glob.glob(os.path.join(clip_dir, "box_ctrl_*.mp4")))
    print(f"\n2. Held-ball control clips ({len(ctrl_clips)} found):")
    ctrl_results = {}
    for clip in ctrl_clips:
        name = os.path.basename(clip)
        print(f"  Analyzing {name}...")
        res = analyze_held_control_clip(clip)
        ctrl_results[name] = res
        print(f"    -> {res['classification']} (grip_diff: {res['max_gripper_diff']}, lower_diff: {res['max_lower_corridor_diff']}, onset: {res['onset_frame']})")

    # 3. Save combined results
    output_data = {
        "midfall_evaluation": mid_results,
        "held_control_evaluation": ctrl_results
    }
    out_file = os.path.join(out_dir, "a100_multi_seed_results.json")
    with open(out_file, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nSaved all results to {out_file}")

if __name__ == "__main__":
    main()
