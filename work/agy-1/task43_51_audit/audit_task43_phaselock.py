#!/usr/bin/env python3
"""
Task 43 & Review of Finding #1052:
Independent evaluation of Task 44's PhaseLock step/CFG sweep on GAUGE Ball 1 Frame 0
using:
1. Preregistered Decision Gate #802:
   - Same-endpoint/stack, same-seed CFG 6 2-step vs 35-step comparison (seeds 1 and 2).
   - Referee-validated firstfall v1 (PASS 20/20).
   - Referee-validated bclock v1 / gauge_blind v1.1 (PASS 12/12).
   - Independent Dual-Patch NCC Tracker (simultaneously tracking the white Franka gripper housing at (282, 68)
     and the held ball at (282, 117)) to separate true ball release from robot-arm descent and gripper-finger motion.
   - Plank-tilt & Multi-Blob Hallucination Detector (measuring the wooden plank right-end displacement and counting
     simultaneous dark ball blobs on the plank/gripper).
"""
import os
import sys
import json
import hashlib
import subprocess
import cv2
import numpy as np

REPO = "/home/nail/swarm-work/agy-1/cosmos-swarm"
PHASELOCK_DIR = os.path.join(REPO, "work/rahul-5-agy/phaselock")
OUT_DIR = os.path.join(REPO, "work/agy-1/task43_51_audit")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(REPO, "tools/realball"))
sys.path.insert(0, os.path.join(REPO, "tools/bclock"))
import firstfall as ff
import bclock as bc


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_frames_bgr(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    return frames, fps


def track_patch_ncc(frames, cx0, cy0, half_w=18, half_h=14, search_x=(210, 360), search_y=(20, 355)):
    """Sub-pixel parabolic-peak NCC template tracker anchored on Frame 0."""
    f0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    H, W = f0.shape
    x0 = max(0, int(round(cx0 - half_w)))
    x1 = min(W, int(round(cx0 + half_w + 1)))
    y0 = max(0, int(round(cy0 - half_h)))
    y1 = min(H, int(round(cy0 + half_h + 1)))
    tmpl = f0[y0:y1, x0:x1]
    th, tw = tmpl.shape

    sx0, sx1 = max(0, search_x[0]), min(W, search_x[1])
    sy0, sy1 = max(0, search_y[0]), min(H, search_y[1])

    xs, ys, scores = [], [], []
    for f in frames:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        roi = g[sy0:sy1, sx0:sx1]
        res = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        mx, my = max_loc
        # Sub-pixel parabolic refinement
        sub_x, sub_y = float(mx), float(my)
        if 0 < mx < res.shape[1] - 1:
            denom = 2.0 * (res[my, mx - 1] - 2.0 * res[my, mx] + res[my, mx + 1])
            if abs(denom) > 1e-6:
                sub_x += float((res[my, mx - 1] - res[my, mx + 1]) / denom)
        if 0 < my < res.shape[0] - 1:
            denom = 2.0 * (res[my - 1, mx] - 2.0 * res[my, mx] + res[my + 1, mx])
            if abs(denom) > 1e-6:
                sub_y += float((res[my - 1, mx] - res[my + 1, mx]) / denom)
        cx = sx0 + sub_x + tw / 2.0
        cy = sy0 + sub_y + th / 2.0
        xs.append(round(cx, 3))
        ys.append(round(cy, 3))
        scores.append(round(float(max_val), 4))
    return np.array(xs), np.array(ys), np.array(scores)


def analyze_mp4_dual_patch_and_physics(mp4_path):
    frames, fps = load_frames_bgr(mp4_path)
    # 1. Track white gripper housing at (282, 68)
    gx, gy, g_ncc = track_patch_ncc(frames, 282, 68, half_w=24, half_h=16, search_x=(220, 350), search_y=(15, 290))
    # 2. Track initial ball + finger patch at (282, 117)
    bx, by, b_ncc = track_patch_ncc(frames, 282, 117, half_w=11, half_h=11, search_x=(220, 350), search_y=(45, 360))

    dy0 = float(by[0] - gy[0])
    sep = (by - gy) - dy0

    # 3. Also run firstfall v1 directly on the video
    ff_F = np.stack(frames, axis=0)
    ff_res, (ff_x, ff_y, ff_area) = ff.measure(ff_F, fps=24.0, ppm=539.8, point=(282.0, 117.0), pframe=0)

    # Compare firstfall's fit_frames (e.g. f3..f7 or f0..f14) against gripper housing motion!
    f_start, f_end = ff_res.get("fit_frames", [0, 10])
    grip_drop_fit = float(gy[min(f_end, len(gy)-1)] - gy[max(0, f_start)])
    ff_drop_fit = float(ff_y[min(f_end, len(ff_y)-1)] - ff_y[max(0, f_start)]) if not np.isnan(ff_y[min(f_end, len(ff_y)-1)]) else None

    # Check gripper descent across frames 0..22 (where the robot arm bends down to crush the plank in s2!)
    grip_max_drop_f0_25 = float(np.max(gy[:26]) - gy[0])
    grip_max_drop_frame = int(np.argmax(gy[:26]))

    # Check wooden plank right-end lift/levitation (around x=340..410, y=230..315)
    # In Frame 0, plank sits quietly on the black mat. In s2_steps35, the plank tilts up like a seesaw (f18..f46)!
    f0_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    plank_diff_f18_46 = []
    for idx in range(18, min(48, len(frames))):
        fg = cv2.cvtColor(frames[idx], cv2.COLOR_BGR2GRAY).astype(np.float32)
        # ROI over upper plank/air above right half of plank (x=310..420, y=220..295)
        roi_diff = np.mean(np.abs(fg[220:295, 310:420] - f0_gray[220:295, 310:420]))
        plank_diff_f18_46.append(float(roi_diff))

    # Count distinct dark ball-like blobs in the plank/table zone (x=220..420, y=240..360) across frames 6..18 and 50..85
    # Using background difference from clean median or intensity threshold
    multi_ball_counts = []
    for idx in [6, 8, 10, 12, 54, 62, 70, 80, 90]:
        if idx >= len(frames):
            continue
        fg = cv2.cvtColor(frames[idx], cv2.COLOR_BGR2GRAY)
        # Look at difference from f0 in table/plank region (x=200..410, y=245..365)
        diff = f0_gray[245:365, 200:410] - fg[245:365, 200:410].astype(np.float32)
        mask = (diff > 28).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        blobs = []
        for lbl in range(1, num_labels):
            area = int(stats[lbl, cv2.CC_STAT_AREA])
            if 25 <= area <= 1200:
                blobs.append({
                    "area": area,
                    "cx": round(float(centroids[lbl][0] + 200), 1),
                    "cy": round(float(centroids[lbl][1] + 245), 1),
                })
        multi_ball_counts.append({"frame": idx, "n_blobs": len(blobs), "blobs": blobs})

    # Run bclock v1 as well
    bc_res = bc.measure(mp4_path, fps=24.0, ppm=539.8, point=(282.0, 117.0), pframe=0)

    return {
        "sha256": sha256_file(mp4_path),
        "n_frames": len(frames),
        "fps": fps,
        "gripper_y_f0": float(gy[0]),
        "gripper_y_f3_f9": [round(float(v), 2) for v in gy[3:10]],
        "gripper_max_drop_f0_14_px": round(float(np.max(gy[:15]) - gy[0]), 2),
        "gripper_max_drop_f0_25_px": round(grip_max_drop_f0_25, 2),
        "gripper_max_drop_frame": grip_max_drop_frame,
        "ball_patch_max_drop_f0_14_px": round(float(np.max(by[:15]) - by[0]), 2),
        "max_sep_f0_14_px": round(float(np.max(sep[:15])), 2),
        "corr_gripper_ball_f0_25": round(float(np.corrcoef(gy[:26], by[:26])[0, 1]), 4) if np.std(gy[:26]) > 0.5 and np.std(by[:26]) > 0.5 else 0.0,
        "firstfall_v1": {
            "flag": ff_res.get("flag"),
            "g": round(float(ff_res["g"]), 4) if ff_res.get("g") is not None else None,
            "g_ci95": [round(float(x), 4) for x in ff_res.get("g_ci95", [None, None])] if ff_res.get("g_ci95") and ff_res["g_ci95"][0] is not None else None,
            "r2": round(float(ff_res["r2"]), 4) if ff_res.get("r2") is not None else None,
            "dAIC": round(float(ff_res["dAIC_quad_vs_lin"]), 3) if ff_res.get("dAIC_quad_vs_lin") is not None else None,
            "fall_px": round(float(ff_res["fall_px"]), 2) if ff_res.get("fall_px") is not None else None,
            "fall_time_s": round(float(ff_res["fall_time_s"]), 4) if ff_res.get("fall_time_s") is not None else None,
            "motion_frame": ff_res.get("motion_frame"),
            "impact_frame": ff_res.get("impact_frame"),
            "fit_frames": ff_res.get("fit_frames"),
            "y_f0_to_f12": [round(float(v), 2) if not np.isnan(v) else None for v in ff_y[:13]],
            "y_f13_to_f45_min_max": [round(float(np.nanmin(ff_y[13:46])), 2), round(float(np.nanmax(ff_y[13:46])), 2)],
            "gripper_drop_during_fit_px": round(grip_drop_fit, 2),
            "ff_drop_during_fit_px": round(ff_drop_fit, 2) if ff_drop_fit is not None else None,
        },
        "bclock_v1": {
            "flag": bc_res.get("flag"),
            "first_fall_g_ms2": bc_res.get("first_fall_g_ms2"),
            "first_fall_r2": bc_res.get("first_fall_r2"),
            "n_impacts": bc_res.get("n_impacts"),
        },
        "plank_levitation_mean_diff_f18_46": round(float(np.mean(plank_diff_f18_46)), 2),
        "plank_levitation_max_diff_f18_46": round(float(np.max(plank_diff_f18_46)), 2),
        "table_dark_blobs_by_frame": multi_ball_counts,
    }


def main():
    summary_path = os.path.join(PHASELOCK_DIR, "summary.json")
    summary_rows = json.load(open(summary_path))

    # 1. Verify all 10 firstfall JSONs against summary.json
    json_audit = []
    for row in summary_rows:
        name = row["name"]
        ff_json_path = os.path.join(PHASELOCK_DIR, f"{name}_firstfall.json")
        ff_data = json.load(open(ff_json_path))
        sidecar_path = os.path.join(PHASELOCK_DIR, f"{name}.json")
        sidecar = json.load(open(sidecar_path))
        json_audit.append({
            "name": name,
            "steps": row["steps"],
            "guidance": row["guidance"],
            "seed": row["seed"],
            "flag": ff_data["flag"],
            "fall_px": round(float(ff_data["fall_px"]), 2),
            "fall_time_s": round(float(ff_data["fall_time_s"]), 4),
            "g": round(float(ff_data["g"]), 4) if ff_data["g"] is not None else None,
            "r2": round(float(ff_data["r2"]), 4) if ff_data["r2"] is not None else None,
            "dAIC": round(float(ff_data["dAIC_quad_vs_lin"]), 3) if ff_data["dAIC_quad_vs_lin"] is not None else None,
            "motion_frame": ff_data.get("motion_frame"),
            "impact_frame": ff_data.get("impact_frame"),
            "fit_frames": ff_data.get("fit_frames"),
            "d_ratio": round(float(ff_data.get("d_ratio", 0.0)), 3) if ff_data.get("d_ratio") is not None else None,
            "server_clip": sidecar.get("server_clip"),
            "elapsed_s": sidecar.get("elapsed_s"),
        })

    # 2. Deep audit of the 4 MP4 clips (the matched CFG=6, seed 1 & 2, 2-step vs 35-step quartet for Task 43)
    mp4_names = [
        "ball1_steps2_cfg6_s1",
        "ball1_steps2_cfg6_s2",
        "ball1_steps35_cfg6_s1",
        "ball1_steps35_cfg6_s2",
    ]
    mp4_audit = {}
    for name in mp4_names:
        p = os.path.join(PHASELOCK_DIR, f"{name}.mp4")
        if os.path.exists(p):
            mp4_audit[name] = analyze_mp4_dual_patch_and_physics(p)

    out_data = {
        "task44_all_10_runs": json_audit,
        "task43_matched_mp4_quartet": mp4_audit,
    }
    out_file = os.path.join(OUT_DIR, "task43_phaselock_audit.json")
    with open(out_file, "w") as f:
        json.dump(out_data, f, indent=2)
    print("Wrote", out_file)
    for k, v in mp4_audit.items():
        print(k, "-> flag:", v["firstfall_v1"]["flag"], "g:", v["firstfall_v1"]["g"],
              "grip_drop_f0_25:", v["gripper_max_drop_f0_25_px"],
              "plank_lev_max:", v["plank_levitation_max_diff_f18_46"],
              "blobs_f10:", [b for b in v["table_dark_blobs_by_frame"] if b["frame"] in (8, 10, 70)])

if __name__ == "__main__":
    main()
