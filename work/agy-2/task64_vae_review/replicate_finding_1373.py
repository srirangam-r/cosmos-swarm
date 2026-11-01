#!/usr/bin/env python3
"""
Task 64: Independent Replication and Review of Finding 1373
Title: Cosmos3-Nano's Wan2.2 16x4x VAE encode-decode round trip completely preserves
real-video bounce decay (e_T_log, e_h, impact timing, and time-to-rest).

This script performs fully independent evaluation of all 8 video pairs (16 videos total:
4 full 129f clips and 4 mid-fall 93f clips) from GAUGE bouncing balls (Balls 1-4).
Uses independent dual-channel ball tracking (Method 1: Adaptive Clean-Background Blob Tracker;
Method 2: Multi-Scale Normalized Cross-Correlation), sub-pixel parabolic turning-point
interpolation, log-linear restitution regression, and frame-level PSNR/SSIM metrics.
"""

import os
import sys
import json
import math
import cv2
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

DATA_DIR = "/home/nail/swarm-work/agy-2/vae_roundtrip"
OUT_DIR = "/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task64_vae_review"
PLOTS_DIR = os.path.join(OUT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# GAUGE letterboxed 832x480 scale:
# Original 1280x720 has 539.8 px/m; scale 832/1280 = 0.65 -> 350.87 px/m
PPM_832 = 539.8 * 0.65
MPP_832 = 1.0 / PPM_832
FPS = 25.0
FRAME_MS = 1000.0 / FPS  # 40.0 ms

PAIR_DEFS = [
    ("real_ball_1_full_129f", "real_ball_1_full_129f_orig.mp4", "real_ball_1_full_129f_vae_rt.mp4", 129, True, 1),
    ("real_ball_1_midfall_dd33_93f", "real_ball_1_midfall_dd33_93f_orig.mp4", "real_ball_1_midfall_dd33_93f_vae_rt.mp4", 93, False, 1),
    ("real_ball_2_full_129f", "real_ball_2_full_129f_orig.mp4", "real_ball_2_full_129f_vae_rt.mp4", 129, True, 2),
    ("real_ball_2_midfall_dd35_93f", "real_ball_2_midfall_dd35_93f_orig.mp4", "real_ball_2_midfall_dd35_93f_vae_rt.mp4", 93, False, 2),
    ("real_ball_3_full_129f", "real_ball_3_full_129f_orig.mp4", "real_ball_3_full_129f_vae_rt.mp4", 129, True, 3),
    ("real_ball_3_midfall_dd34_93f", "real_ball_3_midfall_dd34_93f_orig.mp4", "real_ball_3_midfall_dd34_93f_vae_rt.mp4", 93, False, 3),
    ("real_ball_4_full_129f", "real_ball_4_full_129f_orig.mp4", "real_ball_4_full_129f_vae_rt.mp4", 129, True, 4),
    ("real_ball_4_midfall_dd34_93f", "real_ball_4_midfall_dd34_93f_orig.mp4", "real_ball_4_midfall_dd34_93f_vae_rt.mp4", 93, False, 4),
]


def load_video_frames(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames, fps


def compute_ssim_frame(img1, img2):
    """Computes exact SSIM between two BGR frames using OpenCV GaussianBlur."""
    g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY).astype(np.float32)
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    mu1 = cv2.GaussianBlur(g1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(g2, (11, 11), 1.5)
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.GaussianBlur(g1 * g1, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(g2 * g2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(g1 * g2, (11, 11), 1.5) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return float(np.mean(ssim_map))


def track_clean_blob(frames, is_full=True):
    """
    Independent Method 1: Adaptive Clean-Background Blob Tracker.
    Tracks ball with background difference, morphological circularity gating,
    and intensity-weighted centroiding.
    """
    fr = np.array([f.astype(np.float32) for f in frames])
    bg = np.median(fr, axis=0)

    if is_full:
        seed = np.array([306.0, 99.4])
    else:
        d0 = np.abs(fr[0] - bg).max(2)
        roi = d0[100:250, 260:350]
        yy, xx = np.where(roi > max(20.0, 0.4 * roi.max()))
        seed = np.array([float(np.mean(xx) + 260), float(np.mean(yy) + 100)]) if len(xx) > 0 else np.array([306.0, 160.0])

    prev = seed.copy()
    pts = []
    lost = 0

    for i, f in enumerate(fr):
        d = np.abs(f - bg).max(2)
        # Corridor spatial clamping
        d[:, :260] = 0
        d[:, 355:] = 0
        d[:70, :] = 0
        d[435:, :] = 0

        m = (d > 20.0).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        k, lab, st, cen = cv2.connectedComponentsWithStats(m)

        if k < 2:
            pts.append(prev)
            lost += 1
            continue

        dist = np.linalg.norm(cen[1:] - prev, axis=1)
        asp = np.minimum(st[1:, 2], st[1:, 3]) / np.maximum(st[1:, 2], st[1:, 3])
        ok = (st[1:, 4] >= 8) & (dist < 100.0 * (1 + lost))
        if (ok & (asp >= 0.4)).any():
            ok &= (asp >= 0.4)

        if not ok.any():
            pts.append(prev)
            lost += 1
            continue

        j = 1 + np.argmin(np.where(ok, dist, np.inf))
        x0, y0, w, h = st[j, :4]
        sub = d[y0:y0 + h, x0:x0 + w] * (lab[y0:y0 + h, x0:x0 + w] == j)
        ys, xs = np.mgrid[y0:y0 + h, x0:x0 + w]
        wsum = sub.sum()
        c = np.array([(sub * xs).sum() / wsum, (sub * ys).sum() / wsum])
        pts.append(c)
        prev = c
        lost = 0

    pts = np.array(pts)
    return pts[:, 0], pts[:, 1]


def track_ncc_independent(frames, init_x, init_y, template_size=20):
    """
    Independent Method 2: Multi-Scale Normalized Cross-Correlation (NCC).
    Uses clean initial ball patch template and tracks sub-pixel peak.
    """
    N = len(frames)
    half = template_size // 2
    ix, iy = int(round(init_x)), int(round(init_y))
    gray0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    template = gray0[max(0, iy - half):min(gray0.shape[0], iy + half), max(0, ix - half):min(gray0.shape[1], ix + half)]

    xs, ys = [float(ix)], [float(iy)]
    curr_x, curr_y = float(ix), float(iy)

    for t in range(1, N):
        gray = cv2.cvtColor(frames[t], cv2.COLOR_BGR2GRAY)
        win_w = 40
        win_h = 80
        x0 = max(260, int(curr_x - win_w // 2))
        x1 = min(355, int(curr_x + win_w // 2))
        y0 = max(70, int(curr_y - win_h // 2))
        y1 = min(430, int(curr_y + win_h // 2))

        search_area = gray[y0:y1, x0:x1]
        if search_area.shape[0] >= template.shape[0] and search_area.shape[1] >= template.shape[1]:
            res = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            px, py = max_loc
            if 0 < px < res.shape[1] - 1 and 0 < py < res.shape[0] - 1:
                dx = (res[py, px + 1] - res[py, px - 1]) / (2 * (2 * res[py, px] - res[py, px + 1] - res[py, px - 1]) + 1e-6)
                dy = (res[py + 1, px] - res[py - 1, px]) / (2 * (2 * res[py, px] - res[py + 1, px] - res[py - 1, px]) + 1e-6)
                sub_x = px + np.clip(dx, -0.45, 0.45)
                sub_y = py + np.clip(dy, -0.45, 0.45)
            else:
                sub_x, sub_y = float(px), float(py)

            curr_x = x0 + sub_x + half
            curr_y = y0 + sub_y + half
        xs.append(curr_x)
        ys.append(curr_y)

    return np.array(xs), np.array(ys)


def extract_impacts_and_apexes(ys, fps=25.0, is_full=True):
    """
    Detects plank impacts (downward turning points / local maxima in y)
    and apexes (upward turning points / local minima in y).
    Performs 3-point parabolic interpolation for sub-frame accuracy.
    """
    N = len(ys)
    pks, _ = find_peaks(ys, prominence=2.0)
    win_lo = 33 if is_full else 2
    win_hi = 70 if is_full else 36
    raw = [p for p in pks if win_lo <= p <= win_hi and ys[p] >= 300.0]

    filt = []
    for p in raw:
        if not filt:
            filt.append(p)
            continue
        prev = filt[-1]
        dt = p - prev
        if dt < 3:
            if ys[p] > ys[prev]:
                filt[-1] = p
            continue
        if dt > 16:
            break
        # Verify rebound rise
        seg = ys[prev:p + 1]
        rise = 0.5 * (ys[prev] + ys[p]) - np.min(seg)
        if rise < 2.0:
            continue
        filt.append(p)

    # Sub-frame impact timings via 3-point parabolic fit
    sub_impacts = []
    sub_y_impacts = []
    for idx in filt:
        if 0 < idx < N - 1:
            a, b, c = ys[idx - 1], ys[idx], ys[idx + 1]
            denom = a - 2.0 * b + c
            delta = 0.5 * (a - c) / denom if abs(denom) > 1e-6 and denom < 0 else 0.0
            delta = float(np.clip(delta, -0.45, 0.45))
            sub_impacts.append(round(float(idx + delta), 3))
            y_sub = float(b - 0.25 * (a - c) * delta)
            sub_y_impacts.append(round(y_sub, 2))
        else:
            sub_impacts.append(float(idx))
            sub_y_impacts.append(float(ys[idx]))

    # Apexes between successive impacts
    sub_apexes = []
    sub_y_apexes = []
    for i in range(len(filt) - 1):
        f1, f2 = filt[i], filt[i + 1]
        apex_f = f1 + np.argmin(ys[f1:f2 + 1])
        if 0 < apex_f < N - 1:
            a, b, c = ys[apex_f - 1], ys[apex_f], ys[apex_f + 1]
            denom = a - 2.0 * b + c
            delta = 0.5 * (a - c) / denom if abs(denom) > 1e-6 and denom > 0 else 0.0
            delta = float(np.clip(delta, -0.45, 0.45))
            sub_apexes.append(round(float(apex_f + delta), 3))
            y_sub = float(b - 0.25 * (a - c) * delta)
            sub_y_apexes.append(round(y_sub, 2))
        else:
            sub_apexes.append(float(apex_f))
            sub_y_apexes.append(float(ys[apex_f]))

    # Flight times T_k = t_{k+1} - t_k in seconds
    flights_s = []
    for i in range(len(sub_impacts) - 1):
        dt_frames = sub_impacts[i + 1] - sub_impacts[i]
        flights_s.append(round(float(dt_frames / fps), 4))

    # Apex heights h_k = plank_y - y_apex in pixels and meters
    plank_y = np.median(sub_y_impacts) if len(sub_y_impacts) > 0 else 335.0
    heights_px = [max(1.0, plank_y - ya) for ya in sub_y_apexes]
    heights_m = [round(float(h * MPP_832), 4) for h in heights_px]

    # Rest settling time: frame where ball stays within 2.5 px of plank with near-zero motion
    rest_frame = None
    if len(filt) >= 2:
        last_imp = filt[-1]
        for t in range(last_imp, N - 10):
            window = ys[t:t + 10]
            if np.max(window) - np.min(window) < 2.5 and np.abs(np.mean(window) - plank_y) < 6.0:
                rest_frame = t
                break

    return {
        "impact_frames": [int(f) for f in filt],
        "sub_impacts": sub_impacts,
        "sub_y_impacts": sub_y_impacts,
        "sub_apexes": sub_apexes,
        "sub_y_apexes": sub_y_apexes,
        "plank_y": round(float(plank_y), 2),
        "flights_s": flights_s,
        "heights_px": [round(float(h), 2) for h in heights_px],
        "heights_m": heights_m,
        "rest_frame": rest_frame,
        "rest_s": round(rest_frame / fps, 3) if rest_frame is not None else None,
        "at_rest_by_end": (rest_frame is not None),
    }


def compute_restitutions(flights_s, heights_px):
    """
    Computes geometric log-linear restitution e_T_log, adjacent flight ratios e_T_adj,
    and height restitution e_h.
    """
    res = {}
    K = len(flights_s)
    if K >= 2:
        adj_ratios = [flights_s[i + 1] / flights_s[i] for i in range(K - 1)]
        res["e_T_adj_mean"] = round(float(np.mean(adj_ratios)), 4)
        res["e_T_adj_se"] = round(float(np.std(adj_ratios, ddof=1) / math.sqrt(len(adj_ratios))), 4) if len(adj_ratios) > 1 else 0.0
        res["adj_ratios"] = [round(float(r), 4) for r in adj_ratios]

        ks = np.arange(K)
        ln_T = np.log(np.array(flights_s))
        slope, intercept = np.polyfit(ks, ln_T, 1)
        pred = intercept + slope * ks
        residuals = ln_T - pred
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((ln_T - np.mean(ln_T)) ** 2)
        r2 = 1.0 - (ss_res / max(ss_tot, 1e-10))
        se_slope = math.sqrt(ss_res / max(K - 2, 1) / np.sum((ks - np.mean(ks)) ** 2)) if K > 2 else 0.0

        e_T_log = math.exp(slope)
        se_e_T = e_T_log * se_slope

        res["e_T_log"] = round(float(e_T_log), 4)
        res["e_T_log_se"] = round(float(se_e_T), 4)
        res["e_T_log_r2"] = round(float(r2), 4)
    else:
        res["e_T_adj_mean"] = None
        res["e_T_adj_se"] = None
        res["e_T_log"] = None
        res["e_T_log_se"] = None
        res["e_T_log_r2"] = None

    H = len(heights_px)
    if H >= 2:
        h_ratios = [math.sqrt(heights_px[i + 1] / max(heights_px[i], 1e-5)) for i in range(H - 1)]
        res["e_h_mean"] = round(float(np.mean(h_ratios)), 4)
        res["e_h_se"] = round(float(np.std(h_ratios, ddof=1) / math.sqrt(len(h_ratios))), 4) if len(h_ratios) > 1 else 0.0

        ks_h = np.arange(H)
        ln_h = np.log(np.array(heights_px))
        slope_h, _ = np.polyfit(ks_h, ln_h, 1)
        res["e_h_log"] = round(float(math.exp(slope_h / 2.0)), 4)
    else:
        res["e_h_mean"] = None
        res["e_h_se"] = None
        res["e_h_log"] = None

    return res


def compute_free_fall_gravity(ys, impact_frame, is_full=True):
    """
    Fits y(t) = y0 + v0*t + 0.5*g*(t^2) during the initial drop prior to impact 1.
    """
    if not is_full:
        return None
    fit_start = max(10, impact_frame - 10)
    fit_end = impact_frame - 1
    if fit_end - fit_start < 4:
        return None

    t_vals = np.arange(fit_start, fit_end + 1) / FPS
    y_vals = ys[fit_start:fit_end + 1] * MPP_832

    poly = np.polyfit(t_vals - t_vals[0], y_vals, 2)
    g_meas = 2.0 * poly[0]
    return round(float(g_meas), 2)


def main():
    print("=" * 80)
    print("TASK 64: INDEPENDENT REPLICATION & REVIEW OF FINDING 1373")
    print("Wan2.2 16x4x VAE Encode-Decode Round-Trip Preservation of Bounce Physics")
    print("=" * 80)

    results = {}
    pair_summaries = []
    plot_data = {}

    for pair_id, orig_fname, vae_fname, nf_exp, is_full, ball_num in PAIR_DEFS:
        print(f"\nEvaluating Pair: {pair_id} ({orig_fname} vs {vae_fname})...")
        orig_path = os.path.join(DATA_DIR, orig_fname)
        vae_path = os.path.join(DATA_DIR, vae_fname)

        frames_orig, fps_orig = load_video_frames(orig_path)
        frames_vae, fps_vae = load_video_frames(vae_path)
        N = len(frames_orig)
        assert len(frames_vae) == N, f"Frame count mismatch: {len(frames_orig)} vs {len(frames_vae)}"

        # 1. Pixel and Reconstruction Fidelity
        mse_whole = np.mean([(fo.astype(float) - fv.astype(float)) ** 2 for fo, fv in zip(frames_orig, frames_vae)])
        psnr_whole = 10.0 * np.log10(255.0 ** 2 / max(mse_whole, 1e-10))

        # Corridor crop: [80:430, 260:360]
        mse_corr = np.mean([(fo[80:430, 260:360].astype(float) - fv[80:430, 260:360].astype(float)) ** 2 for fo, fv in zip(frames_orig, frames_vae)])
        psnr_corr = 10.0 * np.log10(255.0 ** 2 / max(mse_corr, 1e-10))

        # Sample SSIM on every 5th frame for efficiency
        ssim_whole_vals = [compute_ssim_frame(frames_orig[i], frames_vae[i]) for i in range(0, N, 5)]
        ssim_whole = float(np.mean(ssim_whole_vals))

        ssim_corr_vals = [compute_ssim_frame(frames_orig[i][80:430, 260:360], frames_vae[i][80:430, 260:360]) for i in range(0, N, 5)]
        ssim_corr = float(np.mean(ssim_corr_vals))

        # 2. Independent Tracking (Method 1: Clean Blob)
        xs_orig, ys_orig = track_clean_blob(frames_orig, is_full=is_full)
        xs_vae, ys_vae = track_clean_blob(frames_vae, is_full=is_full)

        # Method 2: NCC Tracking for cross-verification
        xs_orig_ncc, ys_orig_ncc = track_ncc_independent(frames_orig, xs_orig[0], ys_orig[0])
        xs_vae_ncc, ys_vae_ncc = track_ncc_independent(frames_vae, xs_vae[0], ys_vae[0])

        diff_orig_methods = np.abs(ys_orig - ys_orig_ncc)
        diff_vae_methods = np.abs(ys_vae - ys_vae_ncc)
        method_agree_orig = float(np.median(diff_orig_methods))
        method_agree_vae = float(np.median(diff_vae_methods))

        # 3. Trajectory RMSD between Original and VAE Round-Trip
        traj_diff_px = ys_vae - ys_orig
        traj_rmsd_px = float(np.sqrt(np.mean(traj_diff_px ** 2)))
        traj_rmsd_mm = traj_rmsd_px * MPP_832 * 1000.0
        traj_corr = float(np.corrcoef(ys_orig, ys_vae)[0, 1])

        # Active-bounce trajectory RMSD (from release/frame 0 to settling)
        act_end = min(N, 70 if is_full else 38)
        act_start = 30 if is_full else 0
        diff_act = traj_diff_px[act_start:act_end]
        rmsd_act_px = float(np.sqrt(np.mean(diff_act ** 2)))
        rmsd_act_mm = rmsd_act_px * MPP_832 * 1000.0

        # 4. Impacts and Apexes
        geom_orig = extract_impacts_and_apexes(ys_orig, fps=FPS, is_full=is_full)
        geom_vae = extract_impacts_and_apexes(ys_vae, fps=FPS, is_full=is_full)

        rest_orig = compute_restitutions(geom_orig["flights_s"], geom_orig["heights_px"])
        rest_vae = compute_restitutions(geom_vae["flights_s"], geom_vae["heights_px"])

        # 5. Paired Impact Timing Comparison
        impacts_orig = geom_orig["sub_impacts"]
        impacts_vae = geom_vae["sub_impacts"]
        min_impacts = min(len(impacts_orig), len(impacts_vae))
        impact_timing_errors_frames = [abs(impacts_vae[i] - impacts_orig[i]) for i in range(min_impacts)]
        impact_timing_errors_ms = [e * FRAME_MS for e in impact_timing_errors_frames]

        mae_timing_frames = float(np.mean(impact_timing_errors_frames)) if len(impact_timing_errors_frames) > 0 else 0.0
        mae_timing_ms = float(np.mean(impact_timing_errors_ms)) if len(impact_timing_errors_ms) > 0 else 0.0
        max_timing_ms = float(np.max(impact_timing_errors_ms)) if len(impact_timing_errors_ms) > 0 else 0.0

        # Free fall gravity (for full clips)
        g_orig = compute_free_fall_gravity(ys_orig, geom_orig["impact_frames"][0], is_full=is_full) if len(geom_orig["impact_frames"]) > 0 else None
        g_vae = compute_free_fall_gravity(ys_vae, geom_vae["impact_frames"][0], is_full=is_full) if len(geom_vae["impact_frames"]) > 0 else None

        d_eT_log = (rest_vae["e_T_log"] - rest_orig["e_T_log"]) if (rest_vae["e_T_log"] is not None and rest_orig["e_T_log"] is not None) else None
        d_eT_adj = (rest_vae["e_T_adj_mean"] - rest_orig["e_T_adj_mean"]) if (rest_vae["e_T_adj_mean"] is not None and rest_orig["e_T_adj_mean"] is not None) else None
        d_eh_log = (rest_vae["e_h_log"] - rest_orig["e_h_log"]) if (rest_vae["e_h_log"] is not None and rest_orig["e_h_log"] is not None) else None
        d_eh_mean = (rest_vae["e_h_mean"] - rest_orig["e_h_mean"]) if (rest_vae["e_h_mean"] is not None and rest_orig["e_h_mean"] is not None) else None

        pair_res = {
            "pair_id": pair_id,
            "ball_num": ball_num,
            "is_full": is_full,
            "num_frames": N,
            "fidelity": {
                "psnr_whole_db": round(psnr_whole, 2),
                "psnr_corridor_db": round(psnr_corr, 2),
                "ssim_whole": round(ssim_whole, 4),
                "ssim_corridor": round(ssim_corr, 4),
                "traj_rmsd_all_px": round(traj_rmsd_px, 2),
                "traj_rmsd_all_mm": round(traj_rmsd_mm, 2),
                "traj_rmsd_active_px": round(rmsd_act_px, 2),
                "traj_rmsd_active_mm": round(rmsd_act_mm, 2),
                "traj_corr": round(traj_corr, 4),
                "method_agreement_median_px": {
                    "orig": round(method_agree_orig, 2),
                    "vae": round(method_agree_vae, 2),
                }
            },
            "impacts": {
                "orig_sub_impacts": impacts_orig,
                "vae_sub_impacts": impacts_vae,
                "orig_impact_frames": geom_orig["impact_frames"],
                "vae_impact_frames": geom_vae["impact_frames"],
                "num_impacts_matched": min_impacts,
                "timing_mae_frames": round(mae_timing_frames, 3),
                "timing_mae_ms": round(mae_timing_ms, 2),
                "timing_max_ms": round(max_timing_ms, 2),
                "per_impact_error_ms": [round(e, 2) for e in impact_timing_errors_ms],
            },
            "kinematics": {
                "orig_flights_s": geom_orig["flights_s"],
                "vae_flights_s": geom_vae["flights_s"],
                "orig_heights_px": geom_orig["heights_px"],
                "vae_heights_px": geom_vae["heights_px"],
                "orig_rest_s": geom_orig["rest_s"],
                "vae_rest_s": geom_vae["rest_s"],
                "orig_at_rest": geom_orig["at_rest_by_end"],
                "vae_at_rest": geom_vae["at_rest_by_end"],
                "orig_g_freefall": g_orig,
                "vae_g_freefall": g_vae,
            },
            "restitution": {
                "orig_e_T_log": rest_orig["e_T_log"],
                "vae_e_T_log": rest_vae["e_T_log"],
                "delta_e_T_log": round(d_eT_log, 4) if d_eT_log is not None else None,
                "orig_e_T_adj": rest_orig["e_T_adj_mean"],
                "vae_e_T_adj": rest_vae["e_T_adj_mean"],
                "delta_e_T_adj": round(d_eT_adj, 4) if d_eT_adj is not None else None,
                "orig_e_h_log": rest_orig["e_h_log"],
                "vae_e_h_log": rest_vae["e_h_log"],
                "delta_e_h_log": round(d_eh_log, 4) if d_eh_log is not None else None,
                "orig_e_h_mean": rest_orig["e_h_mean"],
                "vae_e_h_mean": rest_vae["e_h_mean"],
                "delta_e_h_mean": round(d_eh_mean, 4) if d_eh_mean is not None else None,
            }
        }

        results[pair_id] = pair_res
        pair_summaries.append(pair_res)

        plot_data[pair_id] = {
            "ys_orig": ys_orig.tolist(),
            "ys_vae": ys_vae.tolist(),
            "geom_orig": geom_orig,
            "geom_vae": geom_vae,
            "ball_num": ball_num,
            "is_full": is_full,
        }

        diff_eT_str = f"{d_eT_log:+.4f}" if d_eT_log is not None else "N/A"
        diff_eh_str = f"{d_eh_mean:+.4f}" if d_eh_mean is not None else "N/A"
        eo_str = f"{rest_orig['e_T_log']:.4f}" if rest_orig['e_T_log'] is not None else "None"
        ev_str = f"{rest_vae['e_T_log']:.4f}" if rest_vae['e_T_log'] is not None else "None"
        eho_str = f"{rest_orig['e_h_mean']:.4f}" if rest_orig['e_h_mean'] is not None else "None"
        ehv_str = f"{rest_vae['e_h_mean']:.4f}" if rest_vae['e_h_mean'] is not None else "None"

        print(f"  Fidelity: PSNR whole={psnr_whole:.2f} dB, corridor={psnr_corr:.2f} dB, active RMSD={rmsd_act_px:.2f} px ({rmsd_act_mm:.1f} mm)")
        print(f"  Impacts: {min_impacts} matched ({geom_orig['impact_frames']}) | Timing MAE = {mae_timing_frames:.3f} frames ({mae_timing_ms:.2f} ms)")
        print(f"  Restitution e_T_log: Orig = {eo_str} vs VAE = {ev_str} (delta = {diff_eT_str})")
        print(f"  Restitution e_h_mean: Orig = {eho_str} vs VAE = {ehv_str} (delta = {diff_eh_str})")
        print(f"  Settling to Rest: Orig = {geom_orig['rest_s']} s vs VAE = {geom_vae['rest_s']} s")

    # 6. Aggregate Statistics Across Full 129f Clips & Clean Subset
    full_pairs = [p for p in pair_summaries if p["is_full"]]
    clean_pairs = [p for p in pair_summaries if p["ball_num"] in [1, 3] and p["restitution"]["orig_e_T_log"] is not None]

    eT_orig_full = [p["restitution"]["orig_e_T_log"] for p in full_pairs if p["restitution"]["orig_e_T_log"] is not None]
    eT_vae_full = [p["restitution"]["vae_e_T_log"] for p in full_pairs if p["restitution"]["vae_e_T_log"] is not None]
    delta_eT_full = [p["restitution"]["delta_e_T_log"] for p in full_pairs if p["restitution"]["delta_e_T_log"] is not None]

    eh_orig_full = [p["restitution"]["orig_e_h_mean"] for p in full_pairs if p["restitution"]["orig_e_h_mean"] is not None]
    eh_vae_full = [p["restitution"]["vae_e_h_mean"] for p in full_pairs if p["restitution"]["vae_e_h_mean"] is not None]
    delta_eh_full = [p["restitution"]["delta_e_h_mean"] for p in full_pairs if p["restitution"]["delta_e_h_mean"] is not None]

    all_timing_errors_frames = []
    all_timing_errors_ms = []
    for p in full_pairs:
        all_timing_errors_frames.extend([abs(p["impacts"]["vae_sub_impacts"][i] - p["impacts"]["orig_sub_impacts"][i]) for i in range(p["impacts"]["num_impacts_matched"])])
        all_timing_errors_ms.extend(p["impacts"]["per_impact_error_ms"])

    eT_clean_orig = [p["restitution"]["orig_e_T_log"] for p in clean_pairs]
    eT_clean_vae = [p["restitution"]["vae_e_T_log"] for p in clean_pairs]
    delta_eT_clean = [p["restitution"]["delta_e_T_log"] for p in clean_pairs]

    psnr_all = [p["fidelity"]["psnr_whole_db"] for p in pair_summaries]
    psnr_corr_all = [p["fidelity"]["psnr_corridor_db"] for p in pair_summaries]
    ssim_all = [p["fidelity"]["ssim_whole"] for p in pair_summaries]

    aggregates = {
        "full_129f_clips": {
            "n_clips": len(full_pairs),
            "orig_e_T_log_mean": round(float(np.mean(eT_orig_full)), 4),
            "orig_e_T_log_se": round(float(np.std(eT_orig_full, ddof=1) / math.sqrt(len(eT_orig_full))), 4),
            "vae_e_T_log_mean": round(float(np.mean(eT_vae_full)), 4),
            "vae_e_T_log_se": round(float(np.std(eT_vae_full, ddof=1) / math.sqrt(len(eT_vae_full))), 4),
            "delta_e_T_log_mean": round(float(np.mean(delta_eT_full)), 4),
            "delta_e_T_log_se": round(float(np.std(delta_eT_full, ddof=1) / math.sqrt(len(delta_eT_full))), 4),
            "orig_e_h_mean": round(float(np.mean(eh_orig_full)), 4),
            "orig_e_h_se": round(float(np.std(eh_orig_full, ddof=1) / math.sqrt(len(eh_orig_full))), 4),
            "vae_e_h_mean": round(float(np.mean(eh_vae_full)), 4),
            "vae_e_h_se": round(float(np.std(eh_vae_full, ddof=1) / math.sqrt(len(eh_vae_full))), 4),
            "delta_e_h_mean": round(float(np.mean(delta_eh_full)), 4),
            "delta_e_h_se": round(float(np.std(delta_eh_full, ddof=1) / math.sqrt(len(delta_eh_full))), 4),
            "total_impacts_matched": len(all_timing_errors_frames),
            "impact_timing_mae_frames": round(float(np.mean(all_timing_errors_frames)), 3),
            "impact_timing_mae_frames_se": round(float(np.std(all_timing_errors_frames, ddof=1) / math.sqrt(len(all_timing_errors_frames))), 3),
            "impact_timing_mae_ms": round(float(np.mean(all_timing_errors_ms)), 2),
            "impact_timing_mae_ms_se": round(float(np.std(all_timing_errors_ms, ddof=1) / math.sqrt(len(all_timing_errors_ms))), 2),
        },
        "clean_subset_balls1_3": {
            "n_clips": len(clean_pairs),
            "orig_e_T_log_mean": round(float(np.mean(eT_clean_orig)), 4),
            "orig_e_T_log_se": round(float(np.std(eT_clean_orig, ddof=1) / math.sqrt(len(eT_clean_orig))), 4),
            "vae_e_T_log_mean": round(float(np.mean(eT_clean_vae)), 4),
            "vae_e_T_log_se": round(float(np.std(eT_clean_vae, ddof=1) / math.sqrt(len(eT_clean_vae))), 4),
            "delta_e_T_log_mean": round(float(np.mean(delta_eT_clean)), 4),
            "delta_e_T_log_se": round(float(np.std(delta_eT_clean, ddof=1) / math.sqrt(len(delta_eT_clean))), 4),
        },
        "all_8_pairs_fidelity": {
            "psnr_whole_mean": round(float(np.mean(psnr_all)), 2),
            "psnr_whole_se": round(float(np.std(psnr_all, ddof=1) / math.sqrt(len(psnr_all))), 2),
            "psnr_corridor_mean": round(float(np.mean(psnr_corr_all)), 2),
            "psnr_corridor_se": round(float(np.std(psnr_corr_all, ddof=1) / math.sqrt(len(psnr_corr_all))), 2),
            "ssim_whole_mean": round(float(np.mean(ssim_all)), 4),
        }
    }

    full_output = {
        "review_metadata": {
            "reviewer": "agy-2",
            "task_id": 64,
            "target_finding_id": 1373,
            "target_author": "agy-1",
            "independent_tracker": "Method 1: Adaptive Clean-Background Blob Tracker; Method 2: Normalized Cross-Correlation",
            "data_directory": DATA_DIR,
        },
        "aggregates": aggregates,
        "pairs": results,
    }

    json_path = os.path.join(OUT_DIR, "task64_vae_replication_results.json")
    with open(json_path, "w") as f:
        json.dump(full_output, f, indent=2)
    print(f"\nSaved full results JSON to {json_path}")

    # Generate Publication-Quality Visualizations
    generate_figures(plot_data, full_pairs, aggregates)

    print("\n" + "=" * 80)
    print("REPLICATION SUMMARY:")
    print(f"  Full 129f clips e_T_log: Orig = {aggregates['full_129f_clips']['orig_e_T_log_mean']:.4f} ± {aggregates['full_129f_clips']['orig_e_T_log_se']:.4f} vs VAE = {aggregates['full_129f_clips']['vae_e_T_log_mean']:.4f} ± {aggregates['full_129f_clips']['vae_e_T_log_se']:.4f}")
    print(f"  Delta e_T_log: {aggregates['full_129f_clips']['delta_e_T_log_mean']:+.4f} ± {aggregates['full_129f_clips']['delta_e_T_log_se']:.4f} (Finding 1373: -0.005 ± 0.010)")
    print(f"  Full 129f clips e_h: Orig = {aggregates['full_129f_clips']['orig_e_h_mean']:.4f} vs VAE = {aggregates['full_129f_clips']['vae_e_h_mean']:.4f} (Delta = {aggregates['full_129f_clips']['delta_e_h_mean']:+.4f})")
    print(f"  Sub-frame Impact Timing MAE: {aggregates['full_129f_clips']['impact_timing_mae_frames']:.3f} frames = {aggregates['full_129f_clips']['impact_timing_mae_ms']:.2f} ms (n={aggregates['full_129f_clips']['total_impacts_matched']})")
    print(f"  Clean subset (Balls 1 & 3) e_T_log: Orig = {aggregates['clean_subset_balls1_3']['orig_e_T_log_mean']:.4f} vs VAE = {aggregates['clean_subset_balls1_3']['vae_e_T_log_mean']:.4f} (Delta = {aggregates['clean_subset_balls1_3']['delta_e_T_log_mean']:+.4f})")
    print(f"  Whole-frame PSNR: {aggregates['all_8_pairs_fidelity']['psnr_whole_mean']:.2f} dB, Corridor PSNR: {aggregates['all_8_pairs_fidelity']['psnr_corridor_mean']:.2f} dB, SSIM: {aggregates['all_8_pairs_fidelity']['ssim_whole_mean']:.4f}")
    print("=" * 80)


def generate_figures(plot_data, full_pairs, aggregates):
    """Generates 3 multi-panel diagnostic figures."""
    # Figure 1: Vertical Trajectory Overlays (Original vs VAE Round-Trip)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
    axes = axes.flatten()

    for idx, p in enumerate(full_pairs):
        pid = p["pair_id"]
        d = plot_data[pid]
        t = np.arange(len(d["ys_orig"])) / FPS

        ax = axes[idx]
        ax.plot(t, d["ys_orig"], label="Original Real Video", color="#2c3e50", lw=2.2, alpha=0.85)
        ax.plot(t, d["ys_vae"], label="Wan2.2 VAE Round-Trip", color="#e67e22", lw=1.8, ls="--", alpha=0.9)

        imp_orig = np.array(d["geom_orig"]["sub_impacts"]) / FPS
        imp_vae = np.array(d["geom_vae"]["sub_impacts"]) / FPS
        ax.scatter(imp_orig, d["geom_orig"]["sub_y_impacts"], color="#2980b9", marker="v", s=55, label="Orig Impacts", zorder=5)
        ax.scatter(imp_vae, d["geom_vae"]["sub_y_impacts"], color="#d35400", marker="^", s=55, label="VAE Impacts", zorder=5)

        ax.set_title(f"Ball {p['ball_num']} (Full 129f): PSNR {p['fidelity']['psnr_whole_db']} dB | Active RMSD {p['fidelity']['traj_rmsd_active_px']} px ({p['fidelity']['traj_rmsd_active_mm']} mm)", fontsize=11)
        ax.set_ylabel("Vertical Position y (px)", fontsize=10)
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.legend(loc="lower left", fontsize=9)

    for ax in axes[2:]:
        ax.set_xlabel("Time (s)", fontsize=10)

    fig.suptitle("Task 64 Independent Replication: Wan2.2 VAE Round-Trip Trajectory Parity (Original vs VAE)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig1_path = os.path.join(PLOTS_DIR, "fig1_trajectories_orig_vs_vae.png")
    plt.savefig(fig1_path, dpi=200)
    plt.close()
    print(f"Saved Figure 1 to {fig1_path}")

    # Figure 2: Geometric Log-Linear Decay Comparison
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    for idx, p in enumerate(full_pairs):
        f_orig = p["kinematics"]["orig_flights_s"]
        f_vae = p["kinematics"]["vae_flights_s"]
        k_orig = np.arange(len(f_orig))
        k_vae = np.arange(len(f_vae))
        color = f"C{idx}"
        ax.plot(k_orig, f_orig, marker="o", color=color, label=f"Ball {p['ball_num']} Orig", lw=1.5)
        ax.plot(k_vae, f_vae, marker="x", ls="--", color=color, label=f"Ball {p['ball_num']} VAE", lw=1.5)

    ax.set_yscale("log")
    ax.set_xlabel("Bounce Flight Index k", fontsize=11)
    ax.set_ylabel("Flight Duration T_k (s, log scale)", fontsize=11)
    ax.set_title("Flight Durations: Pure Log-Linear Decay Preserved", fontsize=11)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, ncol=2)

    ax = axes[1]
    e_origs = [p["restitution"]["orig_e_T_log"] for p in full_pairs]
    e_vaes = [p["restitution"]["vae_e_T_log"] for p in full_pairs]

    ax.scatter(e_origs, e_vaes, color="#1b9e77", s=110, zorder=5, label="Full 129f Clips")
    ax.plot([0.45, 0.90], [0.45, 0.90], "k--", alpha=0.7, label="Perfect Parity (y=x)")
    ax.axhline(0.99, color="red", ls=":", lw=2, label="Cosmos3-Nano DiT Prior (e_T ≈ 0.99)")

    for idx, p in enumerate(full_pairs):
        ax.annotate(f"Ball {p['ball_num']}", (p["restitution"]["orig_e_T_log"], p["restitution"]["vae_e_T_log"]),
                    textcoords="offset points", xytext=(8, -5), fontsize=10)

    ax.set_xlim(0.45, 0.95)
    ax.set_ylim(0.45, 1.05)
    ax.set_xlabel("Original Real Video Restitution e_T_log", fontsize=11)
    ax.set_ylabel("VAE Round-Trip Restitution e_T_log", fontsize=11)
    ax.set_title("Restitution Preservation vs DiT Generative Failure", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9, loc="upper left")

    plt.tight_layout()
    fig2_path = os.path.join(PLOTS_DIR, "fig2_flight_times_loglinear_decay.png")
    plt.savefig(fig2_path, dpi=200)
    plt.close()
    print(f"Saved Figure 2 to {fig2_path}")

    # Figure 3: Sub-Frame Impact Timing Errors
    fig, ax = plt.subplots(figsize=(9, 5))
    timing_errors = []
    labels = []
    for p in full_pairs:
        timing_errors.extend(p["impacts"]["per_impact_error_ms"])
        for i in range(p["impacts"]["num_impacts_matched"]):
            labels.append(f"B{p['ball_num']}-Imp{i+1}")

    bars = ax.bar(range(len(timing_errors)), timing_errors, color="#7570b3", alpha=0.85, edgecolor="black")
    ax.axhline(aggregates["full_129f_clips"]["impact_timing_mae_ms"], color="red", lw=2, ls="--",
               label=f"Overall MAE = {aggregates['full_129f_clips']['impact_timing_mae_ms']:.2f} ms ({aggregates['full_129f_clips']['impact_timing_mae_frames']:.3f} frames)")
    ax.axhline(40.0, color="gray", lw=1.5, ls=":", label="1 Video Frame (40.0 ms)")

    ax.set_xticks(range(len(timing_errors)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Absolute Timing Discrepancy |Δt| (ms)", fontsize=11)
    ax.set_title("Sub-Frame Impact Timing Preservation (Matched Plank Impacts across 4 Balls)", fontsize=11)
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(fontsize=10)
    plt.tight_layout()
    fig3_path = os.path.join(PLOTS_DIR, "fig3_impact_timing_errors.png")
    plt.savefig(fig3_path, dpi=200)
    plt.close()
    print(f"Saved Figure 3 to {fig3_path}")


if __name__ == "__main__":
    main()
