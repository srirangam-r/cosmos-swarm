#!/usr/bin/env python3
"""
replicate_550_621.py
Independent Replication and Review of Finding 550 & Finding 621 (ro-3).
Agent: agy-3 (Task 54)

Finding 550:
Turning off diffusers' duration template ("The video is 7.9 seconds long and is of 24 FPS.")
does not change Nano's pendulum period (189f seed 1). Reported: 107.4 f [107.0, 107.8] vs 107.1 f [106.7, 107.5], Delta = +0.3 f (0.3%).

Finding 621:
"P_frames ~ 0.55 * num_frames" hypothesis does NOT hold up across clip lengths and seeds.
On 61f seed 1, period is ~80-88 f (P/N ~ 1.3-1.4, <1 cycle).
On 189f seed 2, object duplication invalidates pendulum physics (repeats every ~54 f).
Across 4 clips at 24 fps, period runs 2.1-4.5 s (2.0-4.2x real 1.06 s). Seed noise is ~2x on its own.
"""

import os
import sys
import json
import subprocess
import numpy as np
import cv2
from scipy.optimize import curve_fit

REPO = "/home/nail/swarm-work/agy-3/cosmos-swarm"
WORK_DIR = os.path.join(REPO, "work/agy-3/task54_pendulum_review")
PLANTED_DIR = "/home/nail/swarm-work/agy-1/planted"
CLIPS189_DIR = os.path.join(REPO, "work/ro-3/task25_fps_pendulum/clips189")
CLIPSMORE_DIR = os.path.join(REPO, "work/ro-3/task25_fps_pendulum/clips_more")
FPS_SWEEP_DIR = os.path.join(REPO, "work/ro-1/fps_sweep")

os.makedirs(WORK_DIR, exist_ok=True)

def load_frames(path, skip=0):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames[skip:]

def parab_peak(y, i):
    if i <= 0 or i >= len(y) - 1:
        return float(i)
    a, b, c = float(y[i - 1]), float(y[i]), float(y[i + 1])
    den = a - 2.0 * b + c
    off = 0.5 * (a - c) / den if abs(den) > 1e-12 else 0.0
    return float(i + np.clip(off, -0.5, 0.5))

def first_min_curve(lags, D, depth=0.30):
    rng = float(D.max() - D.min())
    if rng <= 0:
        return None
    for i in range(3, len(D) - 1):
        if D[i] <= D[i - 1] and D[i] <= D[i + 1]:
            left_max = float(D[:i].max())
            j = i + 1
            while j < len(D) and D[j] >= D[j - 1]:
                j += 1
            right_max = float(D[i:j].max()) if j > i + 1 else float(D[i])
            prom = min(left_max, right_max if j < len(D) else left_max) - float(D[i])
            if prom < depth * rng:
                continue
            L = lags[i]
            h = int(np.argmin(np.abs(lags - L / 2.0)))
            if lags[h] >= lags[0] + 1 and D[h] < D[i]:
                continue
            return float(lags[0] + parab_peak(-D, i)), float(prom / rng)
    return None

def run_measure_pend_cli(path, fps):
    cmd = ["python3", "-I", f"{REPO}/tools/trk_ballfall/measure_pend.py", path, "--fps", str(fps)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        # Find json in stdout
        out = res.stdout.strip()
        idx = out.find("{")
        if idx >= 0:
            return json.loads(out[idx:])
    except Exception as e:
        pass
    return {"error": res.stderr}

def run_pend_acf_cli(path, fps, skip=12):
    cmd = ["python3", "-I", f"{REPO}/tools/pend_acf/pend_acf.py", path, "--fps", str(fps), "--skip", str(skip)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(res.stdout)
    except Exception:
        return {"error": res.stderr}

def independent_self_similarity(frames, fps):
    n = len(frames)
    G_full = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames])
    G = np.array([
        cv2.GaussianBlur(
            cv2.resize(g, (g.shape[1] // 8, g.shape[0] // 8), interpolation=cv2.INTER_AREA),
            (3, 3), 0
        )
        for g in G_full
    ])
    sd = G.std(axis=0)
    mask = sd >= np.percentile(sd, 90)
    Xm = G[:, mask]
    if Xm.shape[1] == 0 or n < 10:
        return None, None, None

    max_lag = int(n / 1.3)
    if max_lag < 4:
        return None, None, None
    lags = np.arange(1, max_lag + 1)

    # 1. L1 distance
    D_l1 = np.array([np.abs(Xm[:-L] - Xm[L:]).mean() for L in lags])
    m_l1 = first_min_curve(lags, D_l1)

    # 2. Median L2 distance
    D_l2_med = np.array([np.median(np.sqrt(np.mean((Xm[:-L] - Xm[L:]) ** 2, axis=1))) for L in lags])
    m_l2 = first_min_curve(lags, D_l2_med)

    # 3. Temporal-median Cosine distance on mean-centered pixels
    Xc = Xm - Xm.mean(axis=0, keepdims=True)
    norms = np.linalg.norm(Xc, axis=1) + 1e-8
    D_cos_med = np.array([
        np.median(1.0 - np.sum(Xc[:-L] * Xc[L:], axis=1) / (norms[:-L] * norms[L:]))
        for L in lags
    ])
    m_cos = first_min_curve(lags, D_cos_med)

    return m_l1, m_l2, m_cos

def independent_dark_bob_kinematics(frames, fps, pivot=(415.0, 135.0)):
    n = len(frames)
    G_full = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames])
    h, w = G_full.shape[1], G_full.shape[2]

    # Background model from 80th percentile of bright intensities
    bg_bright = np.percentile(G_full, 80, axis=0)
    dark_diff = np.clip(bg_bright - G_full, 0, 255)

    # Crop out edge artifacts, ceiling, and optical table border
    dark_diff[:, :int(0.10 * h), :] = 0
    dark_diff[:, int(0.85 * h):, :] = 0
    dark_diff[:, :, :int(0.20 * w)] = 0
    dark_diff[:, :, int(0.80 * w):] = 0

    cx_list = []
    cy_list = []
    area_list = []
    angle_list = []
    multi_blob_counts = []

    for t in range(n):
        mb = (dark_diff[t] > 32).astype(np.uint8)
        mb = cv2.morphologyEx(mb, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n_cc, _, st, cen = cv2.connectedComponentsWithStats(mb)
        
        # Count moving blobs >= 350 px
        large_blobs = [k for k in range(1, n_cc) if st[k, 4] >= 350]
        multi_blob_counts.append(len(large_blobs))

        if n_cc > 1:
            idx = 1 + int(np.argmax(st[1:, 4]))
            cx, cy, area = float(cen[idx][0]), float(cen[idx][1]), int(st[idx, 4])
        else:
            cx = cx_list[-1] if cx_list else w / 2.0
            cy = cy_list[-1] if cy_list else h / 2.0
            area = 0
        cx_list.append(cx)
        cy_list.append(cy)
        area_list.append(area)

        # Angle from pivot
        px, py = pivot
        ang = np.degrees(np.arctan2(cx - px, max(20.0, cy - py)))
        angle_list.append(float(ang))

    cx_arr = np.array(cx_list)
    cy_arr = np.array(cy_list)
    ang_arr = np.array(angle_list)
    t_sec = np.arange(n) / float(fps)

    # Zero crossings of x - median(x)
    x_sig = cx_arr - np.median(cx_arr)
    sg = np.sign(x_sig)
    zc_intervals = []
    for up in (True, False):
        idx = np.where((sg[:-1] < 0) & (sg[1:] >= 0))[0] if up else np.where((sg[:-1] > 0) & (sg[1:] <= 0))[0]
        tc = idx - x_sig[idx] / (x_sig[idx + 1] - x_sig[idx] + 1e-12)
        if len(tc) > 1:
            zc_intervals.extend(np.diff(tc).tolist())
    P_zc_f = float(np.median(zc_intervals)) if zc_intervals else None

    # Turning points (local extrema of angle)
    right_turning = []
    left_turning = []
    for t in range(1, n - 1):
        if ang_arr[t] >= ang_arr[t - 1] and ang_arr[t] >= ang_arr[t + 1] and ang_arr[t] > 8.0:
            # sub-frame peak
            p_off = parab_peak(ang_arr, t)
            right_turning.append(float(p_off))
        elif ang_arr[t] <= ang_arr[t - 1] and ang_arr[t] <= ang_arr[t + 1] and ang_arr[t] < -8.0:
            p_off = parab_peak(-ang_arr, t)
            left_turning.append(float(p_off))

    # Extrema intervals
    all_ext = sorted([(t, 1) for t in right_turning] + [(t, -1) for t in left_turning])
    ext_periods = []
    for k in range(len(all_ext) - 2):
        if all_ext[k][1] == all_ext[k + 2][1]:
            ext_periods.append(all_ext[k + 2][0] - all_ext[k][0])
    P_ext_f = float(np.median(ext_periods)) if ext_periods else None

    # Harmonic curve fit
    def damped_sin(t, x0, A, beta, omega, phi):
        return x0 + A * np.exp(-beta * t) * np.cos(omega * t + phi)

    # Initial guess
    P_init = P_zc_f or P_ext_f or (n / 2.0)
    omega0 = 2.0 * np.pi / (P_init / float(fps))
    A0 = 0.5 * (cx_arr.max() - cx_arr.min())
    x0_init = np.median(cx_arr)
    fit_res = {}
    try:
        popt, pcov = curve_fit(
            damped_sin,
            t_sec,
            cx_arr,
            p0=[x0_init, A0, 0.05, omega0, 0.0],
            bounds=([0, 10, -0.5, 0.1, -np.pi], [w, w, 1.0, 20.0, np.pi]),
            maxfev=5000
        )
        omega_fit = popt[3]
        P_fit_s = 2.0 * np.pi / omega_fit
        P_fit_f = P_fit_s * fps
        residuals = cx_arr - damped_sin(t_sec, *popt)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((cx_arr - np.mean(cx_arr)) ** 2)
        r2 = 1.0 - (ss_res / (ss_tot + 1e-12))
        fit_res = {
            "period_fit_frames": float(P_fit_f),
            "period_fit_s": float(P_fit_s),
            "amplitude_px": float(popt[1]),
            "damping_beta": float(popt[2]),
            "r2": float(r2),
            "fit_success": True
        }
    except Exception as e:
        fit_res = {
            "period_fit_frames": None,
            "period_fit_s": None,
            "amplitude_px": None,
            "damping_beta": None,
            "r2": None,
            "fit_success": False,
            "fit_error": str(e)
        }

    # Object duplication metric
    frac_multi_blob = float(np.mean(np.array(multi_blob_counts) >= 2))
    duplication_flag = bool(frac_multi_blob > 0.30)

    return {
        "period_zc_frames": P_zc_f,
        "period_zc_s": (P_zc_f / fps) if P_zc_f else None,
        "period_ext_frames": P_ext_f,
        "period_ext_s": (P_ext_f / fps) if P_ext_f else None,
        "zc_intervals_frames": [round(float(x), 3) for x in zc_intervals],
        "ext_periods_frames": [round(float(x), 3) for x in ext_periods],
        "right_turning_frames": [round(float(x), 3) for x in right_turning],
        "left_turning_frames": [round(float(x), 3) for x in left_turning],
        "angle_min": float(ang_arr.min()),
        "angle_max": float(ang_arr.max()),
        "angle_range": float(ang_arr.max() - ang_arr.min()),
        "duplication_flag": duplication_flag,
        "frac_multi_blob": frac_multi_blob,
        "curve_fit": fit_res
    }

def create_contact_sheet(frames, out_path, num_samples=12):
    n = len(frames)
    indices = np.linspace(0, n - 1, num_samples).astype(int)
    sampled = []
    for idx in indices:
        f = frames[idx].copy()
        cv2.putText(f, f"f{idx}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        f_thumb = cv2.resize(f, (277, 160))
        sampled.append(f_thumb)
    
    # 2 rows of 6
    row1 = np.hstack(sampled[:6])
    row2 = np.hstack(sampled[6:12])
    grid = np.vstack([row1, row2])
    cv2.imwrite(out_path, grid)

def evaluate_clip(name, path, fps, skip=12):
    print(f"\n==========================================")
    print(f"Evaluating: {name} (fps={fps}, skip={skip})")
    print(f"Path: {path}")
    if not os.path.exists(path):
        print(f"ERROR: file does not exist: {path}")
        return {"error": "file_not_found", "path": path}

    frames = load_frames(path, skip=skip)
    n_frames = len(frames)
    print(f"Loaded {n_frames} frames (after skip={skip})")

    # Generate contact sheet
    sheet_name = f"sheet_{name}.jpg"
    sheet_path = os.path.join(WORK_DIR, sheet_name)
    create_contact_sheet(load_frames(path, skip=0), sheet_path)

    # 1. Referee-validated measure_pend CLI
    mp_res = run_measure_pend_cli(path, fps)
    print(f"measure_pend v1: period_s = {mp_res.get('period_s')}, flag = {mp_res.get('flag')}, r2 = {mp_res.get('r2')}")

    # 2. ro-3 pend_acf CLI
    p_acf = run_pend_acf_cli(path, fps, skip=skip)
    print(f"pend_acf CLI: period_frames = {p_acf.get('period_frames')}, flag = {p_acf.get('flag')}")

    # 3. Independent self-similarity
    m_l1, m_l2, m_cos = independent_self_similarity(frames, fps)
    s_l1 = f"{m_l1[0]:.2f}f" if m_l1 else "None"
    s_l2 = f"{m_l2[0]:.2f}f" if m_l2 else "None"
    s_cos = f"{m_cos[0]:.2f}f" if m_cos else "None"
    print(f"Independent Self-Sim: L1={s_l1}, L2_med={s_l2}, Cos_med={s_cos}")

    # 4. Independent dark bob kinematics & duplication audit
    kin = independent_dark_bob_kinematics(frames, fps)
    p_zc_str = f"{kin['period_zc_frames']:.2f}f" if kin['period_zc_frames'] is not None else "None"
    p_ext_str = f"{kin['period_ext_frames']:.2f}f" if kin['period_ext_frames'] is not None else "None"
    print(f"Dark-Bob Kinematics: P_zc={p_zc_str}, P_ext={p_ext_str}, Duplication={kin['duplication_flag']} (frac={kin['frac_multi_blob']:.2f})")
    if kin['curve_fit']['fit_success']:
        p_fit_f = kin['curve_fit']['period_fit_frames']
        p_fit_s = kin['curve_fit']['period_fit_s']
        r2 = kin['curve_fit']['r2']
        p_fit_str = f"{p_fit_f:.2f}f ({p_fit_s:.3f}s)" if p_fit_f is not None else "None"
        r2_str = f"{r2:.4f}" if r2 is not None else "None"
        print(f"Harmonic Fit: P_fit = {p_fit_str}, R2 = {r2_str}")

    return {
        "name": name,
        "path": path,
        "fps": fps,
        "skip": skip,
        "n_frames_evaluated": n_frames,
        "measure_pend_v1": {
            "period_s": mp_res.get("period_s"),
            "period_frames": (mp_res.get("period_s") * fps) if mp_res.get("period_s") else None,
            "period_ci95_s": mp_res.get("period_ci95"),
            "zc_periods_s": mp_res.get("zc_periods"),
            "r2": mp_res.get("r2"),
            "beta": mp_res.get("beta"),
            "flag": mp_res.get("flag")
        },
        "pend_acf_cli": {
            "period_frames": p_acf.get("period_frames"),
            "period_s": p_acf.get("period_s"),
            "ci95_frames": p_acf.get("ci95_frames"),
            "flag": p_acf.get("flag"),
            "window_spread": p_acf.get("window_spread")
        },
        "indep_self_similarity": {
            "l1_acf_frames": m_l1[0] if m_l1 else None,
            "l2_med_acf_frames": m_l2[0] if m_l2 else None,
            "cos_med_acf_frames": m_cos[0] if m_cos else None,
            "l1_acf_s": (m_l1[0] / fps) if m_l1 else None,
            "l2_med_acf_s": (m_l2[0] / fps) if m_l2 else None,
            "cos_med_acf_s": (m_cos[0] / fps) if m_cos else None,
        },
        "dark_bob_kinematics": kin
    }

def main():
    results = {}

    # 1. Referee Planted Control Clips
    planted_clips = [
        ("planted-00", os.path.join(PLANTED_DIR, "planted-00.mp4"), 24.0, 0),
        ("planted-07", os.path.join(PLANTED_DIR, "planted-07.mp4"), 24.0, 0),
        ("planted-11", os.path.join(PLANTED_DIR, "planted-11.mp4"), 24.0, 0),
        ("planted-13", os.path.join(PLANTED_DIR, "planted-13.mp4"), 24.0, 0),
    ]
    planted_res = {}
    for name, p, fps, sk in planted_clips:
        if os.path.exists(p):
            planted_res[name] = evaluate_clip(name, p, fps, skip=sk)
    results["planted_controls"] = planted_res

    # 2. Finding 550 Target Pair (Duration Template Ablation, 189f s1)
    f550_clips = [
        ("pend_fps24_s1_189f_dur_on", os.path.join(CLIPS189_DIR, "pend_fps24_s1_189f_crf20.mp4"), 24.0, 12),
        ("pend_fps24_nodur_s1_189f_dur_off", os.path.join(CLIPS189_DIR, "pend_fps24_nodur_s1_189f_crf20.mp4"), 24.0, 12),
    ]
    f550_res = {}
    for name, p, fps, sk in f550_clips:
        f550_res[name] = evaluate_clip(name, p, fps, skip=sk)
    results["finding_550_duration_ablation"] = f550_res

    # 3. Finding 621 Target Set (Clip-Length and Seed Noise at 24 fps)
    f621_clips = [
        ("pend_fps24_61f_s1", os.path.join(CLIPSMORE_DIR, "pend_fps24_61f_s1.mp4"), 24.0, 0),
        ("pend_A_fps24_93f_s1", os.path.join(FPS_SWEEP_DIR, "pend_A_fps24_93f_s1.mp4"), 24.0, 12),
        ("pend_fps24_s1_189f", os.path.join(CLIPS189_DIR, "pend_fps24_s1_189f_crf20.mp4"), 24.0, 12),
        ("pend_fps24_s2_189f", os.path.join(CLIPSMORE_DIR, "pend_fps24_s2.mp4"), 24.0, 12),
    ]
    f621_res = {}
    for name, p, fps, sk in f621_clips:
        f621_res[name] = evaluate_clip(name, p, fps, skip=sk)
    results["finding_621_clip_length_and_seeds"] = f621_res

    # 4. Cross-FPS Extensions
    fps_ext_clips = [
        ("pend_fps48_s1_189f", os.path.join(CLIPS189_DIR, "pend_fps48_s1_189f_crf20.mp4"), 48.0, 24),
        ("pend_fps12_s1_189f", os.path.join(CLIPS189_DIR, "pend_fps12_s1_189f_crf20.mp4"), 12.0, 6),
        ("pend_B_fps12_93f_s1", os.path.join(FPS_SWEEP_DIR, "pend_B_fps12_93f_s1.mp4"), 12.0, 6),
    ]
    fps_res = {}
    for name, p, fps, sk in fps_ext_clips:
        fps_res[name] = evaluate_clip(name, p, fps, skip=sk)
    results["cross_fps_extensions"] = fps_res

    # Save to JSON
    out_json = os.path.join(WORK_DIR, "results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll evaluations saved to: {out_json}")

if __name__ == "__main__":
    main()
