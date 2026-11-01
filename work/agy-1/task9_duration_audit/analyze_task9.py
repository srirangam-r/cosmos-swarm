#!/usr/bin/env python3
"""
Task 9 Duration Sweep Audit & Gripper-Lowering Artifact Analysis (agy-1, Shift 3).

Evaluates the matched GAUGE-protocol bouncing-ball clips across clip durations:
  - 61 frames (2.54 s @ 24 fps): raj2_dur_ball1_nf61_s1.mp4
  - 93 frames (3.88 s @ 24 fps): ball1_nf93_s1.mp4, ball2_nf93_s1.mp4
  - 189 frames (7.88 s @ 24 fps): gauge_ball1_noneg_s1.mp4, gauge_ball2_noneg_s1.mp4
  - Control (189f with boilerplate neg prompt): gauge_ball1_neg_s1.mp4

Runs:
  1. Referee-validated firstfall v1 (tools/realball/firstfall.py, PASS 20/20)
  2. Referee-validated bclock / gauge_blind v1.1 (tools/gauge_blind/gauge_blind.py, PASS 12/12)
  3. Referee-validated measure_ball v5 (tools/trk_ballfall/measure_ball.py, PASS 20/20)
  4. Independent dual-patch NCC tracker measuring:
     - Franka gripper housing vertical trajectory y_gripper(t) (patch around (282, 68))
     - Held ball vertical trajectory y_ball(t) (patch around (282, 117))
     - Separation delta_y(t) = (y_ball(t) - y_gripper(t)) - (y_ball(0) - y_gripper(0))
     - Correlation r(y_gripper, y_ball) across the clip
     - Spawned/substitute ball trajectory in the lower flight zone (y in [145, 360])
"""

from __future__ import annotations
import json
import math
import os
import subprocess
import sys
from pathlib import Path
import cv2
import numpy as np

REPO_ROOT = Path("/home/nail/swarm-work/agy-1/cosmos-swarm")
OUT_DIR = REPO_ROOT / "work" / "agy-1" / "task9_duration_audit"
WORK_DIR = Path("/home/nail/swarm-work/agy-1/task9_work")

sys.path.insert(0, str(REPO_ROOT / "tools" / "realball"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "bclock"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "gauge_blind"))

import firstfall
import gauge_blind


CLIPS = [
    {
        "id": "ball1_nf61_s1",
        "scene": "ball1",
        "num_frames": 61,
        "duration_s": 61 / 24.0,
        "seed": 1,
        "neg_prompt": None,
        "path": REPO_ROOT / "work/raj-2/task9_duration/first_clip/raj2_dur_ball1_nf61_s1.mp4",
    },
    {
        "id": "ball1_nf93_s1",
        "scene": "ball1",
        "num_frames": 93,
        "duration_s": 93 / 24.0,
        "seed": 1,
        "neg_prompt": None,
        "path": WORK_DIR / "20261101T040652_0013_rog2-negmeta.mp4",
    },
    {
        "id": "ball2_nf93_s1",
        "scene": "ball2",
        "num_frames": 93,
        "duration_s": 93 / 24.0,
        "seed": 1,
        "neg_prompt": None,
        "path": WORK_DIR / "20261101T042507_0018_rog2-negmeta.mp4",
    },
    {
        "id": "ball1_nf189_s1",
        "scene": "ball1",
        "num_frames": 189,
        "duration_s": 189 / 24.0,
        "seed": 1,
        "neg_prompt": None,
        "path": REPO_ROOT / "work/raj-1/gauge_ball/gauge_ball1_noneg_s1.mp4",
    },
    {
        "id": "ball2_nf189_s1",
        "scene": "ball2",
        "num_frames": 189,
        "duration_s": 189 / 24.0,
        "seed": 1,
        "neg_prompt": None,
        "path": REPO_ROOT / "work/raj-1/gauge_ball/gauge_ball2_noneg_s1.mp4",
    },
    {
        "id": "ball1_nf189_neg_s1",
        "scene": "ball1",
        "num_frames": 189,
        "duration_s": 189 / 24.0,
        "seed": 1,
        "neg_prompt": "boilerplate",
        "path": REPO_ROOT / "work/raj-1/gauge_ball/gauge_ball1_neg_s1.mp4",
    },
]


def load_gray_frames(video_path: Path) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    cap.release()
    return frames


def track_patch_ncc(
    frames: list[np.ndarray],
    x0: int,
    y0: int,
    half_w: int = 18,
    half_h: int = 16,
    step_radius: int = 24,
    x_bounds: tuple[int, int] = (210, 360),
    y_bounds: tuple[int, int] = (20, 360),
) -> dict:
    """Track a template anchored at (x0, y0) in frame 0 using anchored + step-constrained NCC."""
    h, w = frames[0].shape
    t_x0 = max(0, x0 - half_w)
    t_x1 = min(w, x0 + half_w + 1)
    t_y0 = max(0, y0 - half_h)
    t_y1 = min(h, y0 + half_h + 1)
    tmpl0 = frames[0][t_y0:t_y1, t_x0:t_x1].astype(np.float32)
    th, tw = tmpl0.shape

    xs, ys, nccs = [float(x0)], [float(y0)], [1.0]
    cx, cy = float(x0), float(y0)

    for idx in range(1, len(frames)):
        img = frames[idx].astype(np.float32)
        sx0 = max(x_bounds[0], int(round(cx)) - step_radius - tw // 2)
        sx1 = min(x_bounds[1], int(round(cx)) + step_radius + tw // 2)
        sy0 = max(y_bounds[0], int(round(cy)) - step_radius - th // 2)
        sy1 = min(y_bounds[1], int(round(cy)) + step_radius + th // 2)

        roi = img[sy0:sy1, sx0:sx1]
        if roi.shape[0] < th or roi.shape[1] < tw:
            xs.append(cx)
            ys.append(cy)
            nccs.append(0.0)
            continue

        res = cv2.matchTemplate(roi, tmpl0, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        best_x = sx0 + max_loc[0] + tw // 2
        best_y = sy0 + max_loc[1] + th // 2
        cx, cy = float(best_x), float(best_y)
        xs.append(cx)
        ys.append(cy)
        nccs.append(float(max_val))

    return {
        "x": xs,
        "y": ys,
        "ncc": nccs,
    }


def detect_spawned_plank_ball(frames: list[np.ndarray]) -> dict:
    """Detect whether a dark circular ball appears on/above the plank (y in [160, 355], x in [220, 420])
    while comparing against frame 0 background."""
    f0 = frames[0].astype(np.float32)
    plank_presence_frames = []
    dark_blob_ys = []
    dark_blob_areas = []

    for idx, f in enumerate(frames):
        roi_diff = f0[160:355, 220:420] - f[160:355, 220:420].astype(np.float32)
        # Positive roi_diff means frame idx is darker than frame 0 (a dark object appeared)
        mask = ((roi_diff > 35.0) & (f[160:355, 220:420] < 75)).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        best_area = 0
        best_cy = None
        for lbl in range(1, num_labels):
            area = int(stats[lbl, cv2.CC_STAT_AREA])
            if area > best_area and area >= 120:
                best_area = area
                best_cy = float(centroids[lbl][1] + 160.0)
        if best_cy is not None:
            plank_presence_frames.append(idx)
            dark_blob_ys.append(best_cy)
            dark_blob_areas.append(best_area)

    return {
        "n_frames_with_dark_object_in_flight_or_plank": len(plank_presence_frames),
        "first_frame_detected": plank_presence_frames[0] if plank_presence_frames else None,
        "last_frame_detected": plank_presence_frames[-1] if plank_presence_frames else None,
        "median_area_px": float(np.median(dark_blob_areas)) if dark_blob_areas else 0.0,
        "equiv_diameter_px": float(2.0 * math.sqrt(np.median(dark_blob_areas) / math.pi)) if dark_blob_areas else 0.0,
        "median_y_px": float(np.median(dark_blob_ys)) if dark_blob_ys else None,
    }


def analyze_dual_patch(video_path: Path) -> dict:
    frames = load_gray_frames(video_path)
    # 1. Track white gripper housing directly above the held ball: (282, 68)
    gripper_trk = track_patch_ncc(
        frames, x0=282, y0=68, half_w=24, half_h=18, step_radius=20,
        x_bounds=(200, 360), y_bounds=(15, 260)
    )
    # 2. Track held ball in gripper: (282, 117)
    ball_trk = track_patch_ncc(
        frames, x0=282, y0=117, half_w=16, half_h=16, step_radius=24,
        x_bounds=(200, 360), y_bounds=(30, 355)
    )

    yg = np.array(gripper_trk["y"], dtype=np.float64)
    yb = np.array(ball_trk["y"], dtype=np.float64)
    dy0 = yb[0] - yg[0]
    sep = (yb - yg) - dy0  # positive if ball moves down relative to gripper

    # Check first 14 frames (0.58s, where real release/first-fall occurs) AND first 42 frames (1.75s, where gripper-lowering occurs)
    n_release = min(14, len(frames))
    n_early = min(42, len(frames))
    max_gripper_drop_release_win = float(np.max(yg[:n_release] - yg[0]))
    max_ball_drop_release_win = float(np.max(yb[:n_release] - yb[0]))
    max_rel_sep_release_win = float(np.max(sep[:n_release]))

    max_gripper_drop_early = float(np.max(yg[:n_early] - yg[0]))
    max_ball_drop_early = float(np.max(yb[:n_early] - yb[0]))
    max_rel_separation_early = float(np.max(sep[:n_early]))
    median_abs_sep_early = float(np.median(np.abs(sep[:n_early])))

    if np.std(yg[:n_early]) > 1.0 and np.std(yb[:n_early]) > 1.0:
        corr_early = float(np.corrcoef(yg[:n_early], yb[:n_early])[0, 1])
    else:
        corr_early = 0.0

    spawn_info = detect_spawned_plank_ball(frames)

    # Classify physical regime objectively:
    if max_rel_sep_release_win > 60.0 and max_gripper_drop_release_win < 15.0:
        regime = "true_release_from_stationary_gripper"
    elif max_gripper_drop_early > 80.0 and median_abs_sep_early < 25.0 and corr_early > 0.90:
        regime = "gripper_lowers_with_held_ball_plus_spawned_plank_ball"
    elif max_ball_drop_early < 25.0 and spawn_info["n_frames_with_dark_object_in_flight_or_plank"] > 20:
        regime = "held_stationary_plus_spawned_substitute_ball"
    else:
        regime = "other"

    return {
        "n_frames": len(frames),
        "max_gripper_drop_f0_14_px": round(max_gripper_drop_release_win, 2),
        "max_ball_drop_f0_14_px": round(max_ball_drop_release_win, 2),
        "max_ball_minus_gripper_sep_f0_14_px": round(max_rel_sep_release_win, 2),
        "max_gripper_drop_f0_42_px": round(max_gripper_drop_early, 2),
        "max_ball_drop_f0_42_px": round(max_ball_drop_early, 2),
        "max_ball_minus_gripper_separation_f0_42_px": round(max_rel_separation_early, 2),
        "median_abs_ball_gripper_sep_f0_42_px": round(median_abs_sep_early, 2),
        "gripper_ball_y_corr_f0_42": round(corr_early, 4),
        "gripper_y_f0_f12_f20_f38": [
            round(float(yg[0]), 1),
            round(float(yg[min(12, len(yg) - 1)]), 1),
            round(float(yg[min(20, len(yg) - 1)]), 1),
            round(float(yg[min(38, len(yg) - 1)]), 1),
        ],
        "ball_y_f0_f12_f20_f38": [
            round(float(yb[0]), 1),
            round(float(yb[min(12, len(yb) - 1)]), 1),
            round(float(yb[min(20, len(yb) - 1)]), 1),
            round(float(yb[min(38, len(yb) - 1)]), 1),
        ],
        "spawned_plank_ball": spawn_info,
        "physical_regime": regime,
    }


def run_measure_ball_v5(video_path: Path) -> dict:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "tools/trk_ballfall/measure_ball.py"),
        str(video_path),
        "--fps",
        "24",
        "--ppm",
        "539.8",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()}
    try:
        data = json.loads(proc.stdout)
        return {
            "g_ms2": data.get("g_ms2"),
            "g_ci95_ms2": data.get("g_ci95_ms2"),
            "r2": data.get("r2"),
            "fit_frames": data.get("fit_frames"),
            "track_source": data.get("track_source"),
            "Quality_flag": data.get("Quality_flag"),
        }
    except Exception as exc:
        return {"error": str(exc)}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet_dir = OUT_DIR / "sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for item in CLIPS:
        vpath = item["path"]
        print(f"Analyzing {item['id']} ({vpath})...")
        # 1. firstfall v1
        F_ff = firstfall.trk.load(str(vpath))
        ff_res, ff_trk = firstfall.measure(
            F_ff,
            fps=24.0,
            ppm=539.8,
        )
        ff_seeded_res, _ = firstfall.measure(
            F_ff,
            fps=24.0,
            ppm=539.8,
            point=[282.0, 117.0],
        )
        firstfall.qc_png(str(OUT_DIR / f"{item['id']}_firstfall_qc.png"), F_ff, ff_trk, ff_res)
        # 2. gauge_blind v1.1 (bclock)
        gb_row, gb_full = gauge_blind.score(
            str(vpath),
            fps=24.0,
            sheetdir=str(sheet_dir),
        )
        # 3. measure_ball v5
        mb_res = run_measure_ball_v5(vpath)
        # 4. Dual-patch gripper vs ball + spawned ball detector
        dp_res = analyze_dual_patch(vpath)

        # Scaling prediction if g_61 = 3.390 m/s^2 scaled as (61/N)^2:
        g_pred_n2 = 3.390 * ((61.0 / item["num_frames"]) ** 2)

        results.append({
            "id": item["id"],
            "scene": item["scene"],
            "num_frames": item["num_frames"],
            "duration_s": round(item["duration_s"], 3),
            "seed": item["seed"],
            "neg_prompt": item["neg_prompt"],
            "g_pred_if_N_minus_2_scaling_ms2": round(g_pred_n2, 3),
            "firstfall_v1": {
                "flag": ff_res.get("flag"),
                "g_ms2": ff_res.get("g"),
                "g_ci95_ms2": ff_res.get("g_ci95"),
                "g_from_h_T_ms2": ff_res.get("g_from_h_T"),
                "r2": ff_res.get("r2"),
                "dAIC_quad_vs_lin": ff_res.get("dAIC_quad_vs_lin"),
                "fit_frames": ff_res.get("fit_frames"),
                "fall_px": ff_res.get("fall_px"),
                "fall_time_s": ff_res.get("fall_time_s"),
                "seeded_282_117_flag": ff_seeded_res.get("flag"),
                "seeded_282_117_g_ms2": ff_seeded_res.get("g"),
            },
            "gauge_blind_v1_1": {
                "release": gb_row.get("release"),
                "bclock_flag": gb_row.get("bclock_flag"),
                "g_ms2": gb_row.get("g"),
                "g_src": gb_row.get("g_src"),
                "first_fall_r2": gb_row.get("first_fall_r2"),
                "max_drop_px": gb_row.get("max_drop_px"),
                "rest_minus_impact_px": gb_row.get("rest_minus_impact_px"),
                "held_at_end_ncc": gb_row.get("held_at_end_ncc"),
                "n_impacts": gb_row.get("n_impacts"),
            },
            "measure_ball_v5": mb_res,
            "dual_patch_gripper_vs_ball": dp_res,
        })

    summary_path = OUT_DIR / "task9_duration_results.json"
    summary_path.write_text(json.dumps(results, indent=2))
    print(f"Saved results to {summary_path}")


if __name__ == "__main__":
    main()
