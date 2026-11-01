#!/usr/bin/env python3
"""
evaluate_task69_blind.py
Independent blind evaluator for Task 24 GAUGE-ball eval clips (base, LoRA A, LoRA B, LoRA C).
Applies pre-registered metrics from task 24 msg 613:
1. Release rate: center drops > 1 ball diameter (22 px) below frame 0, with eye confirmation on contact sheet.
2. First-fall g (m/s²): quadratic parabolic fit and falling-time formula on released clips (539.8 px/m scale).
3. Bounce decay: restitution e1 = T1 / (2 t_fall), flight-time ratio T_{k+1}/T_k, apex height ratio e_h.
4. Time-to-rest: frame at which vertical motion < 2 px for 6+ frames after first impact (censored at frame 92).
5. Visual classification: genuine_release | held | phantom_duplicate | arm_plunge | substitute.
"""

import os
import sys
import glob
import json
import csv
import cv2
import numpy as np

PPM = 539.8           # pixels per meter (official GAUGE table plane)
FPS = 24.0            # frames per second
SEED_X = 281.0        # initial held-ball centre on GAUGE frame 0 (832x480)
SEED_Y = 119.0
BALL_RADIUS = 11.0    # ball radius in px (diameter = 22 px)
HALF_PATCH = 14       # template half-size
CORRIDOR_X = (180, 380)
CORRIDOR_Y = (80, 420)
PLANK_Y = 365.0       # typical plank contact level in px

def read_video(path):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def analyze_clip(path, out_sheets_dir):
    clip_name = os.path.basename(path)
    clip_id = clip_name.replace('.mp4', '')
    frames = read_video(path)
    n_frames = len(frames)
    if n_frames == 0:
        return None

    H, W = frames[0].shape[:2]

    # Convert frames to grayscale
    gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]

    # Frame 0 template around held ball
    x0, y0 = int(round(SEED_X)), int(round(SEED_Y))
    tpl_y1 = max(0, y0 - HALF_PATCH)
    tpl_y2 = min(H, y0 + HALF_PATCH + 1)
    tpl_x1 = max(0, x0 - HALF_PATCH)
    tpl_x2 = min(W, x0 + HALF_PATCH + 1)
    ball_tpl = gray_frames[0][tpl_y1:tpl_y2, tpl_x1:tpl_x2]

    # Background frame estimate (median across frames)
    # Using temporal median across frames can highlight moving objects
    sample_idx = np.linspace(0, n_frames - 1, min(15, n_frames), dtype=int)
    med_bg = np.median([gray_frames[i] for i in sample_idx], axis=0).astype(np.uint8)

    # Tracking arrays
    track_x = []
    track_y = []
    track_score = []
    gripper_ncc = []
    lower_corridor_mass = []
    arm_motion_mag = []

    # Gripper monitoring ROI: around seed position
    grip_box = (max(0, x0 - 25), max(0, y0 - 20), min(W, x0 + 25), min(H, y0 + 20))
    grip_tpl = gray_frames[0][y0 - HALF_PATCH:y0 + HALF_PATCH + 1, x0 - HALF_PATCH:x0 + HALF_PATCH + 1]

    curr_x, curr_y = SEED_X, SEED_Y

    for t in range(n_frames):
        g = gray_frames[t]

        # 1. Gripper retention score (NCC within gripper box)
        gx1, gy1, gx2, gy2 = grip_box
        grip_roi = g[gy1:gy2, gx1:gx2]
        if grip_roi.shape[0] >= grip_tpl.shape[0] and grip_roi.shape[1] >= grip_tpl.shape[1]:
            res_grip = cv2.matchTemplate(grip_roi, grip_tpl, cv2.TM_CCOEFF_NORMED)
            g_ncc = float(np.max(res_grip))
        else:
            g_ncc = 0.0
        gripper_ncc.append(g_ncc)

        # 2. Lower corridor mass (detecting phantom duplicate below y=180)
        corr_diff = cv2.absdiff(g[180:390, 240:320], gray_frames[0][180:390, 240:320])
        lower_corridor_mass.append(float(np.mean(corr_diff)))

        # 3. Track ball position
        # Search window around previous position or along vertical drop corridor
        search_half_x = 40
        search_half_y = 60
        sx1 = max(0, int(curr_x - search_half_x))
        sx2 = min(W, int(curr_x + search_half_x + 1))
        sy1 = max(0, int(curr_y - 20))  # allow mostly downward search
        sy2 = min(H, int(curr_y + search_half_y + 1))

        search_roi = g[sy1:sy2, sx1:sx2]
        best_score = -1.0
        best_pt = (curr_x, curr_y)

        if search_roi.shape[0] >= ball_tpl.shape[0] and search_roi.shape[1] >= ball_tpl.shape[1]:
            res = cv2.matchTemplate(search_roi, ball_tpl, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            best_score = float(max_val)
            best_pt = (sx1 + max_loc[0] + HALF_PATCH, sy1 + max_loc[1] + HALF_PATCH)

        track_x.append(best_pt[0])
        track_y.append(best_pt[1])
        track_score.append(best_score)

        # Update search center if confident
        if best_score > 0.40:
            curr_x = 0.8 * curr_x + 0.2 * best_pt[0]
            curr_y = best_pt[1]

    track_y = np.array(track_y)
    track_x = np.array(track_x)
    track_score = np.array(track_score)
    gripper_ncc = np.array(gripper_ncc)
    lower_corridor_mass = np.array(lower_corridor_mass)

    # Metric 1: Release detection
    y_drop = track_y - SEED_Y
    drop_threshold = 22.0 # 1 ball diameter
    exceed_indices = np.where((y_drop > drop_threshold) & (track_score > 0.35))[0]

    auto_release = False
    release_frame = None
    if len(exceed_indices) > 0:
        first_exceed = exceed_indices[0]
        # Trace backwards to find release onset
        pre = np.where(y_drop[:first_exceed] < 5.0)[0]
        release_frame = int(pre[-1]) if len(pre) > 0 else 0
        auto_release = True

    # Kinematics if released
    impact_frames = []
    apex_frames = []
    g_parabolic = None
    g_parabolic_r2 = None
    g_timing = None
    e1 = None
    e_ratios = []
    time_to_rest_frame = None
    at_rest_by_end = 0

    if auto_release and release_frame is not None:
        # Find turning points (impacts) where track_y reaches local maxima near plank (y > 300)
        # Smooth track_y slightly for turning point analysis
        kernel_size = 3
        y_smooth = np.convolve(track_y, np.ones(kernel_size)/kernel_size, mode='same')

        for t in range(release_frame + 2, n_frames - 2):
            if y_smooth[t] > 280.0:
                if y_smooth[t] >= y_smooth[t-1] and y_smooth[t] >= y_smooth[t+1]:
                    if y_smooth[t] >= y_smooth[t-2] and y_smooth[t] >= y_smooth[t+2]:
                        if len(impact_frames) == 0 or (t - impact_frames[-1]) >= 4:
                            impact_frames.append(t)

        # Detect apexes (local minima between impacts)
        if len(impact_frames) >= 1:
            for k in range(len(impact_frames) - 1):
                t_start = impact_frames[k]
                t_end = impact_frames[k+1]
                sub_y = y_smooth[t_start:t_end]
                apex_t = t_start + int(np.argmin(sub_y))
                apex_frames.append(apex_t)

        # First fall analysis
        if len(impact_frames) >= 1:
            t_imp1 = impact_frames[0]
            dt_frames = t_imp1 - release_frame
            if dt_frames >= 3:
                fit_t = np.arange(release_frame, t_imp1 + 1)
                fit_y = track_y[fit_t]
                t_sec = (fit_t - release_frame) / FPS
                # Parabolic fit: y(t) = y0 + v0*t + 0.5*g*t^2
                try:
                    p = np.polyfit(t_sec, fit_y, 2)
                    y_pred = np.polyval(p, t_sec)
                    ss_res = np.sum((fit_y - y_pred)**2)
                    ss_tot = np.sum((fit_y - np.mean(fit_y))**2)
                    r2 = 1.0 - (ss_res / (ss_tot + 1e-8))

                    # p[0] is 0.5 * g_px
                    g_parabolic = float(2.0 * p[0] / PPM)
                    g_parabolic_r2 = float(r2)
                except Exception:
                    pass

                dy_meters = (track_y[t_imp1] - track_y[release_frame]) / PPM
                t_fall_sec = dt_frames / FPS
                g_timing = float(2.0 * dy_meters / (t_fall_sec**2))

            # Restitution e1 and successive flight ratios
            if len(impact_frames) >= 2:
                T1_frames = impact_frames[1] - impact_frames[0]
                t_fall_frames = impact_frames[0] - release_frame
                if t_fall_frames > 0:
                    e1 = float(T1_frames / (2.0 * t_fall_frames))

                for k in range(len(impact_frames) - 2):
                    Tk = impact_frames[k+1] - impact_frames[k]
                    Tk1 = impact_frames[k+2] - impact_frames[k+1]
                    if Tk > 0:
                        e_ratios.append(float(Tk1 / Tk))

            # Time to rest: after first impact, motion < 2 px for 6 frames
            for t in range(impact_frames[0], n_frames - 6):
                window = track_y[t:t+6]
                if np.max(np.abs(window - window[0])) < 2.0:
                    time_to_rest_frame = t
                    at_rest_by_end = 1
                    break

    if time_to_rest_frame is None:
        time_to_rest_frame = n_frames - 1
        at_rest_by_end = 0

    # Eye classification heuristics (to be confirmed on contact sheet)
    # Check if ball remains in gripper across whole clip
    held_fraction = float(np.mean(gripper_ncc > 0.65))
    held_at_end = float(gripper_ncc[-1])
    max_drop = float(np.max(y_drop))
    max_lower_corridor = float(np.max(lower_corridor_mass))

    if held_fraction > 0.85 and max_drop < 15.0:
        if max_lower_corridor > 20.0:
            tentative_category = "phantom_duplicate"
        else:
            tentative_category = "held"
    elif held_fraction > 0.70 and max_drop > 30.0:
        tentative_category = "phantom_duplicate"
    elif auto_release:
        if max_drop > 200.0:
            tentative_category = "genuine_release"
        else:
            tentative_category = "ambiguous_drop"
    else:
        tentative_category = "held"

    # Generate 24-frame contact sheet (every 4th frame: 0, 4, 8, ... 92)
    sample_frames = list(range(0, n_frames, 4))
    if sample_frames[-1] != n_frames - 1:
        sample_frames.append(n_frames - 1)

    tiles = []
    for f_idx in sample_frames:
        frame_copy = frames[f_idx].copy()
        # Crop interaction corridor: x in [180, 380], y in [80, 420]
        crop = frame_copy[CORRIDOR_Y[0]:CORRIDOR_Y[1], CORRIDOR_X[0]:CORRIDOR_X[1]].copy()

        # Circle tracked position relative to crop
        bx = int(track_x[f_idx] - CORRIDOR_X[0])
        by = int(track_y[f_idx] - CORRIDOR_Y[0])
        conf = track_score[f_idx]
        color = (0, 255, 0) if conf > 0.40 else (0, 0, 255)
        if 0 <= bx < crop.shape[1] and 0 <= by < crop.shape[0]:
            cv2.circle(crop, (bx, by), int(BALL_RADIUS + 3), color, 2)

        # Annotate frame number, y position, and gripper NCC
        cv2.putText(crop, f"f:{f_idx:02d}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(crop, f"y:{track_y[f_idx]:.0f}", (6, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(crop, f"g:{gripper_ncc[f_idx]:.2f}", (6, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)

        # Resize for sheet
        tile_resized = cv2.resize(crop, (150, 255))
        tiles.append(tile_resized)

    # Grid tiles into rows of 6
    while len(tiles) % 6 != 0:
        tiles.append(np.zeros_like(tiles[0]))

    rows = []
    for r in range(0, len(tiles), 6):
        rows.append(np.hstack(tiles[r:r+6]))
    sheet = np.vstack(rows)

    sheet_path = os.path.join(out_sheets_dir, f"{clip_id}_sheet.jpg")
    cv2.imwrite(sheet_path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])

    result = {
        "clip_id": clip_id,
        "clip_name": clip_name,
        "n_frames": n_frames,
        "auto_release": int(auto_release),
        "release_frame": release_frame,
        "tentative_category": tentative_category,
        "max_drop_px": round(max_drop, 1),
        "held_fraction": round(held_fraction, 3),
        "held_at_end_ncc": round(held_at_end, 3),
        "max_lower_corridor_diff": round(max_lower_corridor, 2),
        "g_parabolic": round(g_parabolic, 3) if g_parabolic is not None else None,
        "g_parabolic_r2": round(g_parabolic_r2, 4) if g_parabolic_r2 is not None else None,
        "g_timing": round(g_timing, 3) if g_timing is not None else None,
        "n_impacts": len(impact_frames),
        "impact_frames": impact_frames,
        "apex_frames": apex_frames,
        "e1": round(e1, 3) if e1 is not None else None,
        "e_ratio_med": round(float(np.median(e_ratios)), 3) if len(e_ratios) > 0 else None,
        "time_to_rest_frame": time_to_rest_frame,
        "at_rest_by_end": at_rest_by_end,
        "sheet_path": sheet_path
    }
    return result

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 evaluate_task69_blind.py <CLIPS_DIR> <OUT_DIR>")
        sys.exit(1)

    clips_dir = sys.argv[1]
    out_dir = sys.argv[2]
    sheets_dir = os.path.join(out_dir, "sheets")
    os.makedirs(sheets_dir, exist_ok=True)

    mp4_files = sorted(glob.glob(os.path.join(clips_dir, "*.mp4")))
    print(f"Found {len(mp4_files)} clips in {clips_dir}")

    results = []
    for idx, f in enumerate(mp4_files):
        print(f"[{idx+1}/{len(mp4_files)}] Processing {os.path.basename(f)}...")
        res = analyze_clip(f, sheets_dir)
        if res:
            results.append(res)

    # Save detailed JSON
    json_path = os.path.join(out_dir, "task69_blind_results.json")
    with open(json_path, 'w') as jf:
        json.dump(results, jf, indent=2)

    # Save CSV
    csv_path = os.path.join(out_dir, "task69_blind_scores.csv")
    fieldnames = [
        "clip_id", "auto_release", "tentative_category", "release_frame",
        "max_drop_px", "held_fraction", "held_at_end_ncc", "max_lower_corridor_diff",
        "g_parabolic", "g_parabolic_r2", "g_timing", "n_impacts",
        "e1", "e_ratio_med", "time_to_rest_frame", "at_rest_by_end"
    ]
    with open(csv_path, 'w', newline='') as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"\nDone! Processed {len(results)} clips.")
    print(f"JSON saved to {json_path}")
    print(f"CSV saved to {csv_path}")

if __name__ == "__main__":
    main()
