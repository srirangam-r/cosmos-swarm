#!/usr/bin/env python3
"""
analyze_clips.py: Quantitative Kinematics, Rest Evaluation, and Filmstrips
for Task 140 (Rule R on GAUGE Slope and Pendulum dev scenes).
Incorporates agy-2 / rahul-2 causal multi-channel NCC slope tracking.
"""

import os
import sys
import glob
import json
from pathlib import Path
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
CLIPS_DIR = BASE_DIR / "clips"
STRIPS_DIR = BASE_DIR / "strips"
STRIPS_DIR.mkdir(parents=True, exist_ok=True)

SLOPE_CFG = {
    "slope_plastic": dict(box=(570, 28, 660, 115), top=(672.0, 85.0), bot=(190.0, 385.0)),
    "slope_wood":    dict(box=(560, 8, 650, 93),   top=(668.0, 57.0), bot=(168.0, 362.0)),
}


def load_video(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    return np.array(frames), float(fps)


def subpix(r, i, j):
    def p(a, b, c):
        den = a - 2 * b + c
        return 0.0 if abs(den) < 1e-9 else 0.5 * (a - c) / den
    dy = p(r[i - 1, j], r[i, j], r[i + 1, j]) if 0 < i < r.shape[0] - 1 else 0.0
    dx = p(r[i, j - 1], r[i, j], r[i, j + 1]) if 0 < j < r.shape[1] - 1 else 0.0
    return dx, dy


def make_contact_strip(frames, out_path, step=8):
    """Save an unblinded contact sheet showing progression across clip."""
    indices = list(range(0, len(frames), step))
    if indices[-1] != len(frames) - 1:
        indices.append(len(frames) - 1)
    
    strip_frames = []
    for idx in indices:
        f = frames[idx].copy()
        cv2.putText(f, f"f{idx}", (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        strip_frames.append(cv2.resize(f, (208, 120)))
    
    mid = (len(strip_frames) + 1) // 2
    row1_imgs = strip_frames[:mid]
    row2_imgs = strip_frames[mid:]
    
    row1 = np.hstack(row1_imgs)
    row2 = np.hstack(row2_imgs)
    
    if row1.shape[1] > row2.shape[1]:
        pad = np.zeros((row2.shape[0], row1.shape[1] - row2.shape[1], 3), dtype=np.uint8)
        row2 = np.hstack([row2, pad])
    elif row2.shape[1] > row1.shape[1]:
        pad = np.zeros((row1.shape[0], row2.shape[1] - row1.shape[1], 3), dtype=np.uint8)
        row1 = np.hstack([row1, pad])
        
    grid = np.vstack([row1, row2])
    cv2.imwrite(str(out_path), grid)


def track_slope_dual(frames, scene_type):
    mat_key = scene_type
    cfg = SLOPE_CFG[mat_key]
    top = np.array(cfg["top"], dtype=np.float64)
    bot = np.array(cfg["bot"], dtype=np.float64)
    ax = bot - top
    L_px = float(np.linalg.norm(ax))
    ax /= L_px
    mpp = 0.50 / L_px

    x0, y0, x1, y1 = cfg["box"]
    w, h = x1 - x0, y1 - y0
    c0 = np.array([x0 + w / 2.0, y0 + h / 2.0], dtype=np.float64)

    lab0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2Lab).astype(np.float32)
    gx0 = cv2.Sobel(lab0[:, :, 0], cv2.CV_32F, 1, 0, ksize=3)
    gy0 = cv2.Sobel(lab0[:, :, 0], cv2.CV_32F, 0, 1, ksize=3)
    gmag0 = np.hypot(gx0, gy0)
    T_lab = lab0[y0:y1, x0:x1].copy()
    T_gmag = gmag0[y0:y1, x0:x1].copy()

    H, W = frames.shape[1:3]
    pos_lg = np.array([x0, y0], dtype=np.float64)
    R = 60

    s_lg, sc_lg = [0.0], [1.0]

    for i in range(1, len(frames)):
        f = frames[i]
        lab = cv2.cvtColor(f, cv2.COLOR_BGR2Lab).astype(np.float32)
        gx = cv2.Sobel(lab[:, :, 0], cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(lab[:, :, 0], cv2.CV_32F, 0, 1, ksize=3)
        gmag = np.hypot(gx, gy)

        xa2, ya2 = int(max(0, pos_lg[0] - R)), int(max(0, pos_lg[1] - R))
        xb2, yb2 = int(min(W, pos_lg[0] + w + R)), int(min(H, pos_lg[1] + h + R))
        m_lab = cv2.matchTemplate(lab[ya2:yb2, xa2:xb2], T_lab, cv2.TM_CCOEFF_NORMED)
        m_gmag = cv2.matchTemplate(gmag[ya2:yb2, xa2:xb2], T_gmag, cv2.TM_CCOEFF_NORMED)
        m_comb = 0.65 * m_lab + 0.35 * m_gmag
        bi, bj = np.unravel_index(np.argmax(m_comb), m_comb.shape)
        dx, dy = subpix(m_comb, bi, bj)
        pos_lg = np.array([xa2 + bj + dx, ya2 + bi + dy], dtype=np.float64)
        s_lg.append(float(((pos_lg + [w / 2.0, h / 2.0]) - c0) @ ax * mpp))
        sc_lg.append(float(m_comb[bi, bj]))

    s = np.array(s_lg)
    fps = 24.0
    dt = 1.0 / fps
    vel = np.gradient(s, dt)
    
    # Check motion onset
    onset_idx = int(np.where(s > 0.005)[0][0]) if np.any(s > 0.005) else -1
    v_peak = float(np.max(vel)) if len(vel) else 0.0
    v_early_mean = float(np.mean(vel[onset_idx:min(onset_idx + 24, len(vel))])) if onset_idx >= 0 else 0.0
    v_late_mean = float(np.mean(vel[60:93])) if len(vel) >= 93 else float(np.mean(vel[-20:]))
    late_pos_spread = float(np.std(s[70:93])) if len(s) >= 93 else float(np.std(s[-20:]))
    
    # Rest condition: late velocity < 0.05 m/s AND late position std < 0.008 m (8 mm)
    at_rest = bool(abs(v_late_mean) < 0.05 and late_pos_spread < 0.008)
    ran_off = bool(s[-1] > 0.40)

    return {
        "scene": scene_type,
        "onset_frame": onset_idx,
        "slide_m": round(float(s[-1] - s[0]), 3),
        "v_peak_mps": round(v_peak, 3),
        "v_early_mean_mps": round(v_early_mean, 3),
        "v_late_mean_mps": round(v_late_mean, 3),
        "late_pos_std_m": round(late_pos_spread, 4),
        "final_pos_m": round(float(s[-1]), 3),
        "at_rest_at_f92": at_rest,
        "ran_off_plank": ran_off
    }


def track_pendulum(frames, scene_type):
    gray_f = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    
    motion_energy = []
    for i in range(1, len(gray_f)):
        diff = cv2.absdiff(gray_f[i], gray_f[i-1])
        motion_energy.append(float(np.mean(diff)))
    motion_energy = np.array(motion_energy)

    early_energy = float(np.mean(motion_energy[:24]))
    late_energy = float(np.mean(motion_energy[60:92])) if len(motion_energy) >= 92 else float(np.mean(motion_energy[-20:]))

    if scene_type == "pend_rest":
        diff0 = [float(np.mean(cv2.absdiff(gray_f[i], gray_f[0]))) for i in range(len(gray_f))]
        max_diff0 = float(np.max(diff0))
        released = bool(max_diff0 > 3.5)
        at_rest = not released
        return {
            "scene": scene_type,
            "released": released,
            "max_diff_f0": round(max_diff0, 2),
            "early_motion_energy": round(early_energy, 2),
            "late_motion_energy": round(late_energy, 2),
            "at_rest_at_f92": at_rest
        }
    else: # pend_mid
        decay_ratio = float(late_energy / max(early_energy, 1e-4))
        at_rest = bool(decay_ratio < 0.30 or late_energy < 0.60)
        return {
            "scene": scene_type,
            "early_motion_energy": round(early_energy, 2),
            "late_motion_energy": round(late_energy, 2),
            "decay_ratio": round(decay_ratio, 3),
            "at_rest_at_f92": at_rest
        }


def main():
    clips = sorted(glob.glob(str(CLIPS_DIR / "t140_*.mp4")))
    print(f"Found {len(clips)} t140 clips in {CLIPS_DIR}")
    if not clips:
        print("No t140 clips found yet.")
        return

    results = {}
    for clip_path in clips:
        name = Path(clip_path).stem
        parts = name.split("_")
        scene = "_".join(parts[1:-2])
        arm = parts[-2]
        seed = int(parts[-1].replace("s", ""))

        frames, fps = load_video(clip_path)
        strip_path = STRIPS_DIR / f"{name}_strip.jpg"
        make_contact_strip(frames, strip_path)

        if "slope" in scene:
            kin = track_slope_dual(frames, scene)
        else:
            kin = track_pendulum(frames, scene)

        kin.update({
            "name": name,
            "scene": scene,
            "arm": arm,
            "seed": seed,
            "n_frames": len(frames),
            "fps": fps
        })
        results[name] = kin

    out_json = BASE_DIR / "kinematics_results.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote kinematics for {len(results)} clips to {out_json}")


if __name__ == "__main__":
    main()
