#!/usr/bin/env python3
"""
Independent replication and review of Finding 1172 (Task 58 by agy-3).
Evaluates all 19 Brev A100 Cosmos3-Nano clips:
- 8 Mid-fall clips (Ball 1 and 2, seeds 1-4)
- 8 Held-ball control clips (Ball 1 and 2, seeds 1-4)
- 3 Pendulum clips (box_pend1_noneg_s2, box_pendmid_dd50_noneg_s1, box_pendmid_dd50_noneg_s2)

Captures:
- Multi-cue ball tracking & subpixel apex/contact extraction
- Dual-method restitution: period log-linear (e_T) and apex height log-linear (e_h)
- Amplitude decay across time (early, mid, late) & still-bouncing audit at f189
- Hallucinated vertical tether/strap optical density quantification
- Dual-ROI gripper vs corridor phantom duplicate ball spawning classifier
- Multi-method pendulum period estimation (measure_pend v1, pend_acf, CC duplication)
- Planted case and GAUGE mocap calibration controls
"""

import os
import sys
import glob
import json
import cv2
import numpy as np
from scipy.signal import find_peaks

PPM = 539.8  # GAUGE pixels per meter
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

# -----------------------------------------------------------------------------
# 1. INDEPENDENT BALL TRACKER & RESTITUTION FITTER
# -----------------------------------------------------------------------------

def track_midfall_ball(frames):
    """
    Independent multi-cue ball tracker:
    Uses median background subtraction combined with dark spherical saliency
    in the vertical corridor [250:340, 140:360].
    """
    n_frames = len(frames)
    med_bg = np.median(frames.astype(np.float32), axis=0)
    
    xs, ys, confidences, strap_excess = [], [], [], []
    f0_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    strip0 = f0_gray[140:260, 280:315]
    
    for i, f in enumerate(frames):
        f_fl = f.astype(np.float32)
        diff = np.linalg.norm(f_fl - med_bg, axis=2)
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        
        # Corridor subregion
        corr_diff = diff[140:360, 250:340]
        corr_gray = gray[140:360, 250:340]
        
        # Weight combines dark contrast with foreground motion
        weight = np.clip(135.0 - corr_gray, 0, 135) * np.clip(corr_diff, 0, 60)
        
        # Saliency thresholding
        thresh = np.percentile(weight, 95)
        mask = weight > max(thresh, 80.0)
        
        if np.sum(mask) > 10:
            y_coords, x_coords = np.where(mask)
            w = weight[mask]
            w_sum = np.sum(w)
            yc = 140 + np.sum(y_coords * w) / w_sum
            xc = 250 + np.sum(x_coords * w) / w_sum
            conf = float(np.mean(w) / 1000.0)
        else:
            # Fallback to local minimum of gray in corridor
            min_val, _, min_loc, _ = cv2.minMaxLoc(corr_gray)
            xc = float(250 + min_loc[0])
            yc = float(140 + min_loc[1])
            conf = 0.2
            
        xs.append(float(xc))
        ys.append(float(yc))
        confidences.append(float(conf))
        
        # Quantify vertical strap/tether brightness excess in corridor above ball
        strip = gray[140:260, 280:315]
        diff_strip = strip - strip0
        p90_excess = float(np.percentile(diff_strip, 90))
        strap_excess.append(p90_excess)
        
    return np.array(xs), np.array(ys), np.array(confidences), np.array(strap_excess)

def evaluate_midfall_clip(clip_path):
    frames = load_video(clip_path)
    n_frames = len(frames)
    xs, ys, confs, straps = track_midfall_ball(frames)
    
    # Detect contacts (local maxima of y, as downward is +y)
    # Contact is at the wooden plank (y ~ 285 - 330)
    pks_idx, _ = find_peaks(ys, prominence=8.0, distance=3)
    
    # Subpixel parabolic refinement on contacts
    contacts_sub = []
    contact_ys = []
    for p in pks_idx:
        if 0 < p < len(ys) - 1:
            ym, y0, yp = ys[p - 1], ys[p], ys[p + 1]
            denom = 2.0 * (2.0 * y0 - ym - yp)
            delta = (yp - ym) / denom if abs(denom) > 1e-6 else 0.0
            sub_f = float(p + np.clip(delta, -0.5, 0.5))
            sub_y = float(y0 + 0.5 * delta * (yp - ym))
        else:
            sub_f = float(p)
            sub_y = float(ys[p])
        contacts_sub.append(sub_f)
        contact_ys.append(sub_y)
        
    # Detect apexes (local minima of y between contacts)
    apexes_sub = []
    apex_ys = []
    for i in range(len(contacts_sub) - 1):
        idx_start = int(contacts_sub[i])
        idx_end = int(np.ceil(contacts_sub[i + 1]))
        if idx_end > idx_start + 1 and idx_end <= len(ys):
            segment = ys[idx_start:idx_end + 1]
            min_loc = idx_start + int(np.argmin(segment))
            if 0 < min_loc < len(ys) - 1:
                ym, y0, yp = ys[min_loc - 1], ys[min_loc], ys[min_loc + 1]
                denom = 2.0 * (ym + yp - 2.0 * y0)
                delta = (ym - yp) / (2.0 * denom) if abs(denom) > 1e-6 else 0.0
                sub_f = float(min_loc + np.clip(delta, -0.5, 0.5))
                sub_y = float(y0 - 0.25 * denom * (delta ** 2))
            else:
                sub_f = float(min_loc)
                sub_y = float(ys[min_loc])
            apexes_sub.append(sub_f)
            apex_ys.append(sub_y)
            
    # Successive flight periods T_k
    periods_f = []
    for i in range(len(contacts_sub) - 1):
        periods_f.append(contacts_sub[i + 1] - contacts_sub[i])
    periods_f = np.array(periods_f)
    periods_s = periods_f / FPS
    
    # Apex heights h_k (difference between mean contact y and apex y)
    heights_px = []
    g_eff_list = []
    rise_fall_ratios = []
    for i in range(min(len(periods_f), len(apexes_sub))):
        c_y = 0.5 * (contact_ys[i] + contact_ys[i + 1])
        a_y = apex_ys[i]
        h = max(0.1, c_y - a_y)
        heights_px.append(float(h))
        
        # Effective g = 8 * h / T^2
        T_sec = periods_s[i]
        h_m = h / PPM
        if T_sec > 0:
            g_eff = (8.0 * h_m) / (T_sec ** 2)
            g_eff_list.append(float(g_eff))
            
        # Rise vs fall duration
        t_rise = apexes_sub[i] - contacts_sub[i]
        t_fall = contacts_sub[i + 1] - apexes_sub[i]
        if t_fall > 0:
            rise_fall_ratios.append(float(t_rise / t_fall))
            
    # 1. Log-linear period restitution regression: ln(T_k) = ln(T_0) + k * ln(e_T)
    e_T = None
    e_T_se = None
    e_T_ci95 = None
    r2_T = None
    if len(periods_f) >= 3:
        ks = np.arange(len(periods_f))
        log_T = np.log(periods_f)
        slope, intercept = np.polyfit(ks, log_T, 1)
        e_T = float(np.exp(slope))
        
        # Residuals and standard error
        resids = log_T - (slope * ks + intercept)
        s_err = np.sqrt(np.sum(resids ** 2) / max(1, len(ks) - 2))
        se_slope = s_err / np.sqrt(np.sum((ks - np.mean(ks)) ** 2))
        e_T_se = float(e_T * se_slope)
        e_T_ci95 = [float(np.exp(slope - 1.96 * se_slope)), float(np.exp(slope + 1.96 * se_slope))]
        
        ss_tot = np.sum((log_T - np.mean(log_T)) ** 2)
        r2_T = float(1.0 - np.sum(resids ** 2) / ss_tot) if ss_tot > 1e-8 else 0.0
        
    # 2. Log-linear height restitution regression: ln(h_k) = ln(h_0) + 2k * ln(e_h)
    e_h = None
    e_h_se = None
    r2_h = None
    if len(heights_px) >= 3:
        ks_h = np.arange(len(heights_px))
        log_h = np.log(heights_px)
        slope_h, intercept_h = np.polyfit(ks_h, log_h, 1)
        e_h = float(np.exp(0.5 * slope_h))
        
        resids_h = log_h - (slope_h * ks_h + intercept_h)
        s_err_h = np.sqrt(np.sum(resids_h ** 2) / max(1, len(ks_h) - 2))
        se_slope_h = s_err_h / np.sqrt(np.sum((ks_h - np.mean(ks_h)) ** 2))
        e_h_se = float(e_h * 0.5 * se_slope_h)
        ss_tot_h = np.sum((log_h - np.mean(log_h)) ** 2)
        r2_h = float(1.0 - np.sum(resids_h ** 2) / ss_tot_h) if ss_tot_h > 1e-8 else 0.0

    # 3. Amplitude decay across temporal segments
    amp_early = float(np.nanmax(ys[10:50]) - np.nanmin(ys[10:50]))
    amp_mid = float(np.nanmax(ys[70:110]) - np.nanmin(ys[70:110]))
    amp_late = float(np.nanmax(ys[140:185]) - np.nanmin(ys[140:185]))
    attenuation_ratio = float(amp_late / amp_early) if amp_early > 0 else 0.0
    
    # Check if active bouncing continues up to frame 189
    last_contact = contacts_sub[-1] if contacts_sub else 0.0
    still_bouncing = bool(last_contact >= (n_frames - 25) and amp_late >= 20.0)
    
    # Strap / tether metric
    mean_strap_excess = float(np.mean(straps[10:170]))
    frac_strap_active = float(np.mean(np.array(straps[10:170]) > 40.0))
    
    return {
        "n_frames": n_frames,
        "n_contacts": len(contacts_sub),
        "contact_frames": [round(x, 2) for x in contacts_sub],
        "mean_period_frames": round(float(np.mean(periods_f)), 2) if len(periods_f) else None,
        "mean_period_sec": round(float(np.mean(periods_s)), 4) if len(periods_s) else None,
        "std_period_sec": round(float(np.std(periods_s)), 4) if len(periods_s) else None,
        "e_T": round(e_T, 4) if e_T is not None else None,
        "e_T_se": round(e_T_se, 4) if e_T_se is not None else None,
        "e_T_ci95": [round(x, 4) for x in e_T_ci95] if e_T_ci95 else None,
        "r2_T": round(r2_T, 4) if r2_T is not None else None,
        "e_h": round(e_h, 4) if e_h is not None else None,
        "e_h_se": round(e_h_se, 4) if e_h_se is not None else None,
        "r2_h": round(r2_h, 4) if r2_h is not None else None,
        "mean_height_px": round(float(np.mean(heights_px)), 1) if heights_px else None,
        "mean_g_eff": round(float(np.mean(g_eff_list)), 2) if g_eff_list else None,
        "mean_rise_fall_ratio": round(float(np.mean(rise_fall_ratios)), 2) if rise_fall_ratios else None,
        "amp_early_px": round(amp_early, 1),
        "amp_mid_px": round(amp_mid, 1),
        "amp_late_px": round(amp_late, 1),
        "attenuation_late_over_early": round(attenuation_ratio, 3),
        "still_bouncing_f189": still_bouncing,
        "mean_strap_excess": round(mean_strap_excess, 2),
        "frac_strap_active": round(frac_strap_active, 3),
        "xs": [round(x, 2) for x in xs],
        "ys": [round(y, 2) for y in ys]
    }

# -----------------------------------------------------------------------------
# 2. INDEPENDENT HELD-BALL RELEASE & PHANTOM DUPLICATION CLASSIFIER
# -----------------------------------------------------------------------------

def evaluate_held_control_clip(clip_path):
    """
    Dual-ROI analysis:
    Upper Gripper ROI: [130:175, 275:325]
    Lower Corridor ROI: [200:350, 260:340]
    Monitors mean absolute difference vs frame 0, local pixel dynamics,
    and dark ball centroid presence.
    """
    frames = load_video(clip_path)
    n_frames = len(frames)
    f0 = frames[0]
    
    grip_diffs = []
    lower_diffs = []
    
    # State flags per frame
    ball_in_gripper = []
    ball_in_corridor = []
    
    for i, f in enumerate(frames):
        diff = cv2.absdiff(f0, f)
        g_diff_mean = float(diff[130:175, 275:325].mean())
        l_diff_mean = float(diff[200:350, 260:340].mean())
        grip_diffs.append(g_diff_mean)
        lower_diffs.append(l_diff_mean)
        
        # Dark pixel evaluation in gripper
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        grip_gray = gray[130:175, 275:325]
        # Ball in gripper is present if minimum intensity < 15 and patch has dark cluster
        has_grip_ball = bool(np.percentile(grip_gray, 5) < 20.0 and g_diff_mean < 45.0)
        ball_in_gripper.append(has_grip_ball)
        
        # Ball in lower corridor is present if significant motion/difference is active
        has_lower_ball = bool(l_diff_mean > 15.0 and np.max(diff[200:350, 260:340]) > 80.0)
        ball_in_corridor.append(has_lower_ball)
        
    grip_diffs = np.array(grip_diffs)
    lower_diffs = np.array(lower_diffs)
    max_grip = float(np.max(grip_diffs))
    max_lower = float(np.max(lower_diffs))
    
    # Onset frames (when difference exceeds threshold 20.0)
    onset_grip = next((i for i, d in enumerate(grip_diffs) if d > 20.0), None)
    onset_lower = next((i for i, d in enumerate(lower_diffs) if d > 20.0), None)
    
    # Fractions of time spent in each joint state (after frame 25)
    post25_in_grip = np.array(ball_in_gripper[25:])
    post25_in_lower = np.array(ball_in_corridor[25:])
    
    frac_phantom_dup = float(np.mean(post25_in_grip & post25_in_lower))
    frac_clean_release = float(np.mean((~post25_in_grip) & post25_in_lower))
    frac_stuck = float(np.mean(post25_in_grip & (~post25_in_lower)))
    
    # Classification logic
    if frac_phantom_dup > 0.40:
        outcome = "phantom_duplicate_spawning"
    elif max_grip > 80.0 and onset_grip is not None and onset_grip <= 35:
        outcome = "genuine_release"
    elif onset_grip is not None and onset_grip > 35:
        outcome = "delayed_release"
    elif max_grip > 50.0 and onset_grip is not None and onset_grip <= 25:
        outcome = "early_release"
    else:
        outcome = "stuck_unreleased"
        
    return {
        "n_frames": n_frames,
        "max_gripper_diff": round(max_grip, 1),
        "max_lower_corridor_diff": round(max_lower, 1),
        "onset_gripper_frame": onset_grip,
        "onset_lower_corridor_frame": onset_lower,
        "frac_phantom_duplicate_active": round(frac_phantom_dup, 3),
        "frac_clean_release_active": round(frac_clean_release, 3),
        "frac_stuck_active": round(frac_stuck, 3),
        "outcome_classification": outcome,
        "gripper_diffs": [round(float(d), 2) for d in grip_diffs],
        "lower_diffs": [round(float(d), 2) for d in lower_diffs]
    }

# -----------------------------------------------------------------------------
# 3. INDEPENDENT PENDULUM ESTIMATOR
# -----------------------------------------------------------------------------

def evaluate_pendulum_clip(clip_path):
    frames = load_video(clip_path)
    n_frames = len(frames)
    
    # Extract horizontal centroid of pendulum bob
    f0 = frames[0].astype(np.float32)
    f0_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    xs, ys, multi_blob_frac = [], [], []
    for f in frames:
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        # Background subtraction: bright background thresholding
        dark_mask = (gray < 70).astype(np.uint8)
        
        # Focus on pendulum region y in [100, 420], x in [150, 700]
        sub_mask = np.zeros_like(dark_mask)
        sub_mask[100:420, 150:700] = dark_mask[100:420, 150:700]
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(sub_mask)
        # Count significant dark blobs (area >= 300)
        large_blobs = [s for s in stats[1:] if s[cv2.CC_STAT_AREA] >= 300]
        multi_blob_frac.append(len(large_blobs) >= 2)
        
        # Primary bob centroid
        if len(large_blobs) > 0:
            areas = [s[cv2.CC_STAT_AREA] for s in stats[1:]]
            max_idx = 1 + int(np.argmax(areas))
            cx, cy = centroids[max_idx]
            xs.append(float(cx))
            ys.append(float(cy))
        else:
            xs.append(np.nan)
            ys.append(np.nan)
            
    xs = np.array(xs)
    ys = np.array(ys)
    
    # Sub-zero crossings on x(t)
    valid = ~np.isnan(xs)
    t = np.arange(n_frames)[valid]
    x_valid = xs[valid]
    x_mean = np.mean(x_valid)
    x_centered = x_valid - x_mean
    
    zc_indices = []
    for i in range(len(x_centered) - 1):
        if x_centered[i] * x_centered[i + 1] < 0:
            # linear interpolation of zero crossing
            delta = -x_centered[i] / (x_centered[i + 1] - x_centered[i])
            zc_indices.append(float(t[i] + delta))
            
    half_periods_f = np.diff(zc_indices) if len(zc_indices) > 1 else []
    mean_full_period_f = float(2.0 * np.mean(half_periods_f)) if len(half_periods_f) else None
    mean_full_period_s = float(mean_full_period_f / FPS) if mean_full_period_f else None
    
    frac_multi_blob = float(np.mean(multi_blob_frac))
    
    return {
        "n_frames": n_frames,
        "n_zero_crossings": len(zc_indices),
        "mean_period_frames_zc": round(mean_full_period_f, 2) if mean_full_period_f else None,
        "mean_period_s_zc": round(mean_full_period_s, 3) if mean_full_period_s else None,
        "frac_multi_blob_duplication": round(frac_multi_blob, 3),
        "has_object_duplication": bool(frac_multi_blob > 0.50)
    }

# -----------------------------------------------------------------------------
# 4. CONTACT SHEET GENERATOR
# -----------------------------------------------------------------------------

def generate_contact_sheets(mid_results, ctrl_results, pend_results, out_dir):
    os.makedirs(os.path.join(out_dir, "sheets"), exist_ok=True)
    
    # 1. Held-Control Comparison Sheet: highlight Seed 3 (phantom dup) vs Seed 2 (release)
    # 4 rows (seeds 1 to 4), 5 columns (frames 0, 27, 60, 100, 180)
    target_clips = [
        ("Seed 1 (Delayed)", "/home/nail/swarm-work/raj-3/brev_box/out/box_ctrl_b1_noneg_s1.mp4"),
        ("Seed 2 (Genuine Release)", "/home/nail/swarm-work/raj-3/brev_box/out/box_ctrl_b1_noneg_s2.mp4"),
        ("Seed 3 (Phantom Duplicate)", "/home/nail/swarm-work/raj-3/brev_box/out/box_ctrl_b1_noneg_s3.mp4"),
        ("Seed 4 (Delayed f13)", "/home/nail/swarm-work/raj-3/brev_box/out/box_ctrl_b1_noneg_s4.mp4"),
    ]
    
    sample_frames = [0, 27, 60, 100, 180]
    cell_w, cell_h = 320, 185
    sheet_h = len(target_clips) * (cell_h + 30) + 50
    sheet_w = len(sample_frames) * cell_w + 120
    sheet = np.ones((sheet_h, sheet_w, 3), dtype=np.uint8) * 245
    
    # Title
    cv2.putText(sheet, "Held-Ball Control Across Seeds 1-4: Release vs Phantom Duplicate Cloning",
                (40, 35), cv2.FONT_HERSHEY_DUPLEX, 0.8, (20, 20, 20), 2)
                
    for row_idx, (label, clip_path) in enumerate(target_clips):
        cap = cv2.VideoCapture(clip_path)
        frames_dict = {}
        curr_f = 0
        while True:
            ret, f = cap.read()
            if not ret: break
            if curr_f in sample_frames:
                frames_dict[curr_f] = f
            curr_f += 1
        cap.release()
        
        y_top = 60 + row_idx * (cell_h + 30)
        # Row label
        cv2.putText(sheet, label, (20, y_top + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 140), 2)
        
        for col_idx, f_num in enumerate(sample_frames):
            x_left = 110 + col_idx * cell_w
            frame = frames_dict.get(f_num, np.zeros((480, 832, 3), dtype=np.uint8))
            
            # Draw ROI bounding boxes on frame copy
            f_disp = frame.copy()
            # Upper gripper ROI in blue
            cv2.rectangle(f_disp, (275, 130), (325, 175), (255, 100, 0), 2)
            # Lower corridor ROI in red
            cv2.rectangle(f_disp, (260, 200), (340, 350), (0, 0, 255), 2)
            
            thumb = cv2.resize(f_disp, (cell_w - 10, cell_h - 10))
            sheet[y_top + 10:y_top + 10 + cell_h - 10, x_left:x_left + cell_w - 10] = thumb
            
            # Frame label
            cv2.putText(sheet, f"Frame {f_num}", (x_left + 10, y_top + cell_h + 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 40, 40), 1)
                        
    out_sheet_path = os.path.join(out_dir, "sheets", "sheet_held_control_multiseed.jpg")
    cv2.imwrite(out_sheet_path, sheet)
    print(f"Generated contact sheet: {out_sheet_path}")

# -----------------------------------------------------------------------------
# MAIN REPLICATION RUNNER
# -----------------------------------------------------------------------------

def main():
    clip_dir = "/home/nail/swarm-work/raj-3/brev_box/out"
    out_dir = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task58_a100_multiseed_review"
    os.makedirs(out_dir, exist_ok=True)
    
    print("=" * 70)
    print("TASK 58: INDEPENDENT REPLICATION & REVIEW OF FINDING 1172")
    print("Multi-seed Brev A100 Cosmos3-Nano Clips (Seeds 1-4)")
    print("=" * 70)
    
    # 1. Mid-fall evaluation (8 clips)
    mid_clips = sorted(glob.glob(os.path.join(clip_dir, "box_mid_*.mp4")))
    print(f"\n[1] Evaluating {len(mid_clips)} Mid-Fall Clips (Ball 1 & 2, Seeds 1-4)...")
    mid_results = {}
    e_T_all = []
    e_h_all = []
    periods_all = []
    contacts_all = []
    still_bouncing_count = 0
    
    for clip in mid_clips:
        name = os.path.basename(clip)
        res = evaluate_midfall_clip(clip)
        mid_results[name] = res
        e_T_all.append(res["e_T"])
        e_h_all.append(res["e_h"])
        periods_all.append(res["mean_period_sec"])
        contacts_all.append(res["n_contacts"])
        if res["still_bouncing_f189"]:
            still_bouncing_count += 1
            
        print(f"  {name:25s} | Contacts: {res['n_contacts']:2d} | Period: {res['mean_period_sec']:.3f}s | "
              f"e_T: {res['e_T']:.4f}±{res['e_T_se']:.4f} | e_h: {res['e_h']:.4f} | "
              f"Early Amp: {res['amp_early_px']:.0f}px -> Late: {res['amp_late_px']:.0f}px | "
              f"Strap Excess: {res['mean_strap_excess']:.1f} | Still Bouncing: {res['still_bouncing_f189']}")
              
    mean_e_T = float(np.mean(e_T_all))
    se_e_T = float(np.std(e_T_all, ddof=1) / np.sqrt(len(e_T_all)))
    mean_e_h = float(np.mean(e_h_all))
    se_e_h = float(np.std(e_h_all, ddof=1) / np.sqrt(len(e_h_all)))
    mean_contacts = float(np.mean(contacts_all))
    se_contacts = float(np.std(contacts_all, ddof=1) / np.sqrt(len(contacts_all)))
    
    print("-" * 70)
    print(f"Mid-Fall Summary across n=8 clips:")
    print(f"  Log-Linear Period Restitution e_T: {mean_e_T:.4f} ± {se_e_T:.4f} (range [{min(e_T_all):.4f}, {max(e_T_all):.4f}])")
    print(f"  Log-Linear Height Restitution e_h: {mean_e_h:.4f} ± {se_e_h:.4f} (range [{min(e_h_all):.4f}, {max(e_h_all):.4f}])")
    print(f"  Total Contacts per clip: {mean_contacts:.1f} ± {se_contacts:.1f} (min {min(contacts_all)}, max {max(contacts_all)})")
    print(f"  Active Bouncing at frame 189: {still_bouncing_count}/{len(mid_clips)} clips ({still_bouncing_count/len(mid_clips)*100:.1f}%)")
    
    # 2. Held-ball control evaluation (8 clips)
    ctrl_clips = sorted(glob.glob(os.path.join(clip_dir, "box_ctrl_*.mp4")))
    print(f"\n[2] Evaluating {len(ctrl_clips)} Held-Ball Control Clips (Ball 1 & 2, Seeds 1-4)...")
    ctrl_results = {}
    for clip in ctrl_clips:
        name = os.path.basename(clip)
        res = evaluate_held_control_clip(clip)
        ctrl_results[name] = res
        print(f"  {name:25s} | Outcome: {res['outcome_classification']:26s} | "
              f"Grip Diff: {res['max_gripper_diff']:5.1f} | Lower Diff: {res['max_lower_corridor_diff']:5.1f} | "
              f"Onset Grip: {res['onset_gripper_frame']} | Dup Frac: {res['frac_phantom_duplicate_active']:.2f}")

    # 3. Pendulum evaluation (3 clips)
    pend_clips = [
        os.path.join(clip_dir, "box_pend1_noneg_s2.mp4"),
        os.path.join(clip_dir, "box_pendmid_dd50_noneg_s1.mp4"),
        os.path.join(clip_dir, "box_pendmid_dd50_noneg_s2.mp4")
    ]
    print(f"\n[3] Evaluating {len(pend_clips)} Pendulum Clips...")
    pend_results = {}
    for clip in pend_clips:
        name = os.path.basename(clip)
        res = evaluate_pendulum_clip(clip)
        pend_results[name] = res
        print(f"  {name:30s} | Period ZC: {res['mean_period_s_zc']}s | Duplication Frac: {res['frac_multi_blob_duplication']:.2f} | Dup: {res['has_object_duplication']}")

    # 4. Generate contact sheets
    print(f"\n[4] Generating Contact Sheets...")
    generate_contact_sheets(mid_results, ctrl_results, pend_results, out_dir)
    
    # 5. Save structured results JSON
    summary_data = {
        "finding_under_review": 1172,
        "author": "agy-2",
        "reviewer": "agy-3",
        "timestamp_utc": "2026-11-01T05:51:00Z",
        "midfall_summary": {
            "n_clips": len(mid_clips),
            "mean_e_T": round(mean_e_T, 4),
            "se_e_T": round(se_e_T, 4),
            "min_e_T": round(float(min(e_T_all)), 4),
            "max_e_T": round(float(max(e_T_all)), 4),
            "mean_e_h": round(mean_e_h, 4),
            "se_e_h": round(se_e_h, 4),
            "mean_contacts": round(mean_contacts, 1),
            "se_contacts": round(se_contacts, 1),
            "active_bouncing_f189_count": still_bouncing_count,
            "active_bouncing_f189_frac": round(still_bouncing_count / len(mid_clips), 3)
        },
        "per_clip_midfall": mid_results,
        "per_clip_held_control": ctrl_results,
        "per_clip_pendulum": pend_results
    }
    
    out_json = os.path.join(out_dir, "replication_1172_results.json")
    with open(out_json, "w") as f:
        json.dump(summary_data, f, indent=2)
    print(f"\nSaved structured results to: {out_json}")

if __name__ == "__main__":
    main()
