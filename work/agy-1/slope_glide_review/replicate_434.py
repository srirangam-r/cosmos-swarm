#!/usr/bin/env python3
"""Independent replication of Finding 434 (rahul-2):
Nano plastic-slope constant-velocity glide on seed-1 A/B clips (released vs corrected prompt).

Independent tracking methods:
1. Lab background-difference tracker (`lab_bgdiff`):
   - Background constructed by splicing late frames (t >= 70) over the upper plank and
     frame 0 over the lower plank, so the black plastic cube is completely absent from the
     reference background (no median-background ghost).
   - Per frame, compute CIE Lab Euclidean color distance from this clean background AND
     require dark luminance (L < 65 in OpenCV 0..255 Lab) inside the plank/table region.
   - Track the largest connected component; also record the number of substantial dark
     components (>= 800 px) to quantify cube splitting/fragmentation.
2. Normalized cross-correlation template tracker (`ncc_template`):
   - Extract the initial 44x44 cube patch around the frame-0 cube centroid.
   - Track via `cv2.matchTemplate(TM_CCOEFF_NORMED)` within a causal search window along the plank.

Independent scale & axis calibration:
- Compare the plank-length scale (0.50 m = 568 px, 0.880 mm/px) and the frame-0 cube bounding-box
  scale (0.05 m = 61.82 px, 0.809 mm/px).
- Compute the motion axis via total least squares (PCA) on the 2D trajectory centroids,
  and compare with the geometric plank axis.

Kinematic analysis:
- Project 2D positions onto the motion axis: s(t).
- Detect sustained onset (2 consecutive frames with displacement > 3 mm from frame 0) and also
  compare single-frame onset sensitivity.
- Fit linear (constant velocity v) and quadratic (s0 + v0*t + 0.5*a*t^2) models over:
  (a) the early window after onset (first 9 frames after onset, plus sensitivity across onset=4 vs 6),
  (b) the post-onset glide window (onset+9 to end of plank slide),
  (c) the whole on-plank slide (onset to end of plank slide).
- Compute R^2, RMSE, AIC difference (dAIC = AIC_linear - AIC_quad), and sliding-window velocity v(t).
"""
import json
import os
import cv2
import numpy as np


def load_video(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    return np.array(frames), float(fps)


def build_ghost_free_bg(frames):
    """Build a cube-free reference background by combining frame 0 (where cube is at top-right)
    and the median of frames 70..92 (where cube has already slid down to bottom-left)."""
    f0 = frames[0].copy()
    flate = np.median(frames[70:], axis=0).astype(np.uint8)
    bg = f0.copy()
    bg[:, 430:] = flate[:, 430:]
    return bg


def measure_scales(f0, bg):
    """Independently measure cube size in frame 0."""
    lab0 = cv2.cvtColor(f0, cv2.COLOR_BGR2Lab).astype(np.float32)
    lab_bg = cv2.cvtColor(bg, cv2.COLOR_BGR2Lab).astype(np.float32)
    diff0 = np.linalg.norm(lab0 - lab_bg, axis=2)
    mask0 = ((diff0 > 25.0) & (lab0[:, :, 0] < 70)).astype(np.uint8)
    mask0[300:, :] = 0
    mask0[:, :450] = 0
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask0)
    k = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    cube_cx0, cube_cy0 = centroids[k]
    cube_area0 = int(stats[k, cv2.CC_STAT_AREA])
    pts0 = np.argwhere(labels == k)[:, ::-1].astype(np.float32)
    rect = cv2.minAreaRect(pts0)
    cube_w, cube_h = rect[1]
    cube_side_px = float(np.mean([cube_w, cube_h]))

    return {
        "cube_init_centroid_px": [round(float(cube_cx0), 2), round(float(cube_cy0), 2)],
        "cube_init_area_px": cube_area0,
        "cube_init_rect_wh_px": [round(float(cube_w), 2), round(float(cube_h), 2)],
        "cube_side_px": round(cube_side_px, 2),
        "mpp_from_cube_50mm": round(0.05 / cube_side_px, 6),
        "mpp_from_plank_500mm": round(0.50 / 568.0, 6),
    }


def track_cube_independent(frames, bg, init_xy):
    """Track cube with two independent trackers:
    1) Lab Clean-BG difference + luminance gate (connected components)
    2) Template matching (NCC) with causal neighborhood search
    Also counts substantial dark fragments (>= 800 px down to y < 395) to verify cube splitting."""
    lab_bg = cv2.cvtColor(bg, cv2.COLOR_BGR2Lab).astype(np.float32)
    H, W = frames.shape[1:3]

    yy, xx = np.mgrid[0:H, 0:W]
    p0 = np.array([672.0, 85.0])
    p1 = np.array([190.0, 385.0])
    v = p1 - p0
    L_line = np.linalg.norm(v)
    u = v / L_line
    rel_x = xx - p0[0]
    rel_y = yy - p0[1]
    along = rel_x * u[0] + rel_y * u[1]
    perp = (rel_x * (-u[1]) + rel_y * u[0])
    # Corridor along the plank for on-plank tracking (y < 302)
    corridor = (along >= -40) & (along <= L_line + 40) & (perp >= -25) & (perp <= 75) & (yy < 302) & (xx >= 140) & (xx <= 700)
    # Broader region including the lower plank and optical table (y < 395) to detect splitting
    split_roi = (yy < 395) & (xx >= 120) & (xx <= 700)

    cx0, cy0 = int(round(init_xy[0])), int(round(init_xy[1]))
    r_tmpl = 22
    tmpl = cv2.cvtColor(frames[0][cy0 - r_tmpl:cy0 + r_tmpl, cx0 - r_tmpl:cx0 + r_tmpl], cv2.COLOR_BGR2GRAY)
    ncc_cx, ncc_cy = float(cx0), float(cy0)

    records = []
    for idx, f in enumerate(frames):
        lab = cv2.cvtColor(f, cv2.COLOR_BGR2Lab).astype(np.float32)
        diff = np.linalg.norm(lab - lab_bg, axis=2)

        # On-plank foreground mask
        fg = ((diff > 22.0) & (lab[:, :, 0] < 65.0) & corridor).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, labels, stats, centroids = cv2.connectedComponentsWithStats(fg)
        plank_blobs = []
        for k in range(1, n):
            area = int(stats[k, cv2.CC_STAT_AREA])
            if area >= 250:
                plank_blobs.append((area, float(centroids[k][0]), float(centroids[k][1])))
        plank_blobs.sort(reverse=True)

        # Broader split-detection mask (down to y < 395)
        fg_split = ((diff > 20.0) & (lab[:, :, 0] < 65.0) & split_roi).astype(np.uint8)
        ns, ls, ss, cs = cv2.connectedComponentsWithStats(fg_split)
        split_blobs = sorted(
            [(int(ss[k, cv2.CC_STAT_AREA]), round(float(cs[k][0]), 1), round(float(cs[k][1]), 1))
             for k in range(1, ns) if ss[k, cv2.CC_STAT_AREA] >= 800],
            reverse=True,
        )

        # Template matching in causal window around previous NCC position
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        sx0 = max(140, int(round(ncc_cx)) - 45)
        sx1 = min(700, int(round(ncc_cx)) + 30)
        sy0 = max(30, int(round(ncc_cy)) - 25)
        sy1 = min(310, int(round(ncc_cy)) + 45)
        if sx1 - sx0 > 2 * r_tmpl and sy1 - sy0 > 2 * r_tmpl:
            roi = gray[sy0:sy1, sx0:sx1]
            res_ncc = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res_ncc)
            if max_val > 0.45:
                ncc_cx = float(sx0 + max_loc[0] + r_tmpl)
                ncc_cy = float(sy0 + max_loc[1] + r_tmpl)
        else:
            max_val = 0.0

        if plank_blobs and plank_blobs[0][0] >= 800:
            area1, bx1, by1 = plank_blobs[0]
            records.append({
                "frame": idx,
                "cx": bx1,
                "cy": by1,
                "area": area1,
                "ncc_cx": ncc_cx,
                "ncc_cy": ncc_cy,
                "ncc_score": round(float(max_val), 3),
                "split_blobs_ge800": split_blobs,
            })
        elif split_blobs:
            records.append({
                "frame": idx,
                "cx": None,
                "cy": None,
                "area": 0,
                "ncc_cx": ncc_cx,
                "ncc_cy": ncc_cy,
                "ncc_score": round(float(max_val), 3),
                "split_blobs_ge800": split_blobs,
            })
    return records


def fit_kinematics(records, fps=24.0, mpp=0.50 / 568.0):
    """Compute PCA motion axis, project positions, and compare linear vs quadratic fits."""
    valid = [r for r in records if r["area"] > 2000]
    frames = np.array([r["frame"] for r in valid])
    pts = np.array([[r["cx"], r["cy"]] for r in valid], dtype=np.float64)
    ncc_pts = np.array([[r["ncc_cx"], r["ncc_cy"]] for r in valid], dtype=np.float64)

    geom_ax = np.array([190.0 - 672.0, 385.0 - 85.0])
    geom_ax /= np.linalg.norm(geom_ax)

    pts_mean = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - pts_mean, full_matrices=False)
    pca_ax = vt[0]
    if pca_ax @ geom_ax < 0:
        pca_ax = -pca_ax

    axis_angle_diff_deg = float(np.degrees(np.arccos(np.clip(pca_ax @ geom_ax, -1.0, 1.0))))

    s_geom = ((pts - np.array([672.0, 85.0])) @ geom_ax) * mpp
    s_pca = ((pts - pts[0]) @ pca_ax) * mpp
    s_ncc = ((ncc_pts - ncc_pts[0]) @ geom_ax) * mpp

    keep = (s_geom < 0.45) & np.r_[True, np.diff(s_geom) > -0.01]
    idx = frames[keep]
    s = s_geom[keep]
    s_p = s_pca[keep]
    s_n = s_ncc[keep]

    # Single-frame threshold (>3 mm) vs sustained 2-frame threshold (>3 mm)
    above = s > s[0] + 0.003
    on_single = int(idx[int(np.argmax(above))])
    sustained = above[:-1] & above[1:]
    on_sustained = int(idx[int(np.argmax(sustained))])
    t = idx / fps

    def fit_window(mask):
        tw = t[mask] - t[mask][0]
        sw = s[mask]
        n_pts = len(tw)
        p1 = np.polyfit(tw, sw, 1)
        p2 = np.polyfit(tw, sw, 2)
        res1 = sw - np.polyval(p1, tw)
        res2 = sw - np.polyval(p2, tw)
        ss_tot = float(np.sum((sw - sw.mean()) ** 2))
        ss_res1 = float(np.sum(res1 ** 2))
        ss_res2 = float(np.sum(res2 ** 2))
        r2_lin = 1.0 - ss_res1 / ss_tot if ss_tot > 0 else 0.0
        r2_quad = 1.0 - ss_res2 / ss_tot if ss_tot > 0 else 0.0
        aic_lin = n_pts * np.log(max(ss_res1 / n_pts, 1e-18)) + 2 * 2
        aic_quad = n_pts * np.log(max(ss_res2 / n_pts, 1e-18)) + 2 * 3
        rng = np.random.default_rng(42)
        bs_v, bs_a = [], []
        for _ in range(1000):
            b = rng.integers(0, n_pts, size=n_pts)
            if len(np.unique(tw[b])) >= 3:
                bs_v.append(np.polyfit(tw[b], sw[b], 1)[0])
                bs_a.append(2.0 * np.polyfit(tw[b], sw[b], 2)[0])
        return {
            "n_frames": int(n_pts),
            "frame_range": [int(idx[mask][0]), int(idx[mask][-1])],
            "v_lin_mps": round(float(p1[0]), 4),
            "v_lin_se": round(float(np.std(bs_v, ddof=1)), 4),
            "a_quad_mps2": round(float(2.0 * p2[0]), 4),
            "a_quad_se": round(float(np.std(bs_a, ddof=1)), 4),
            "r2_lin": round(r2_lin, 5),
            "r2_quad": round(r2_quad, 5),
            "rmse_lin_mm": round(float(np.sqrt(ss_res1 / n_pts) * 1000.0), 3),
            "rmse_quad_mm": round(float(np.sqrt(ss_res2 / n_pts) * 1000.0), 3),
            "dAIC_lin_minus_quad": round(float(aic_lin - aic_quad), 2),
        }

    on = on_sustained
    early_mask = (idx >= on - 1) & (idx <= on + 8)
    late_mask = idx >= on + 9
    whole_mask = idx >= on

    # Also compute early window using single-frame onset if it differs from sustained onset
    early_single_mask = (idx >= on_single - 1) & (idx <= on_single + 8)
    late_single_mask = idx >= on_single + 9
    whole_single_mask = idx >= on_single

    v_late_pca = float(np.polyfit(t[late_mask], s_p[late_mask], 1)[0])
    a_late_pca = float(2.0 * np.polyfit(t[late_mask], s_p[late_mask], 2)[0])
    v_late_ncc = float(np.polyfit(t[late_mask], s_n[late_mask], 1)[0])

    sliding_v = []
    idx_whole = idx[whole_mask]
    t_whole = t[whole_mask]
    s_whole = s[whole_mask]
    for k in range(0, len(t_whole) - 8, 4):
        vk = float(np.polyfit(t_whole[k:k + 9], s_whole[k:k + 9], 1)[0])
        sliding_v.append({"frames": f"{int(idx_whole[k])}-{int(idx_whole[k+8])}", "v_mps": round(vk, 3)})

    split_events = [
        {"frame": r["frame"], "blobs_ge800_area_cx_cy": r["split_blobs_ge800"]}
        for r in records if len(r["split_blobs_ge800"]) >= 2
    ]

    return {
        "onset_frame_sustained": on_sustained,
        "onset_frame_single": on_single,
        "last_plank_frame": int(idx[-1]),
        "slide_distance_m": round(float(s[-1] - s[0]), 4),
        "pca_vs_geom_axis_deg": round(axis_angle_diff_deg, 2),
        "early_window_fit_sustained": fit_window(early_mask),
        "early_window_fit_single": fit_window(early_single_mask),
        "late_glide_fit_sustained": fit_window(late_mask),
        "late_glide_fit_single": fit_window(late_single_mask),
        "whole_slide_fit_sustained": fit_window(whole_mask),
        "whole_slide_fit_single": fit_window(whole_single_mask),
        "late_glide_pca_axis": {
            "v_lin_mps": round(v_late_pca, 4),
            "a_quad_mps2": round(a_late_pca, 4),
        },
        "late_glide_ncc_tracker": {
            "v_lin_mps": round(v_late_ncc, 4),
        },
        "sliding_9f_velocities": sliding_v,
        "cube_splitting_events_ge800px": split_events,
    }


def main():
    clip_dir = "/home/nail/swarm-work/agy-1/slope_clips"
    out_dir = "/home/nail/swarm-work/agy-1/cosmos-swarm/work/agy-1/slope_glide_review"
    os.makedirs(out_dir, exist_ok=True)

    results = {}
    for name in ["plastic_released_nf93_s1", "plastic_corrected_nf93_s1"]:
        path = os.path.join(clip_dir, f"{name}.mp4")
        frames, fps = load_video(path)
        bg = build_ghost_free_bg(frames)
        calib = measure_scales(frames[0], bg)
        records = track_cube_independent(frames, bg, calib["cube_init_centroid_px"])
        kin_plank = fit_kinematics(records, fps=fps, mpp=calib["mpp_from_plank_500mm"])
        kin_cube = fit_kinematics(records, fps=fps, mpp=calib["mpp_from_cube_50mm"])
        results[name] = {
            "calibration": calib,
            "kinematics_plank_scale_0.88mm_px": kin_plank,
            "kinematics_cube_scale_0.81mm_px": {
                "steady_v_mps": kin_cube["late_glide_fit_sustained"]["v_lin_mps"],
                "early_a_sustained_mps2": kin_cube["early_window_fit_sustained"]["a_quad_mps2"],
                "early_a_single_mps2": kin_cube["early_window_fit_single"]["a_quad_mps2"],
                "late_a_mps2": kin_cube["late_glide_fit_sustained"]["a_quad_mps2"],
                "whole_a_mps2": kin_cube["whole_slide_fit_sustained"]["a_quad_mps2"],
            },
        }
        print(f"=== {name} ===")
        print(json.dumps(results[name], indent=2))

    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
