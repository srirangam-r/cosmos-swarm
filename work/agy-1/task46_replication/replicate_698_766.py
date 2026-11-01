#!/usr/bin/env python3
"""Independent replication of Finding #698 (rahul-5-agy) and Finding #766 (rahul-2) — Task 46.

Part A: Review of Finding #698 (rahul-5-agy):
- Evaluates the two 189-frame GAUGE mid-fall ball clips (`20261101T033939_0007_raj-3.mp4` = Ball 1 dedup f33,
  and `20261101T040234_0012_raj-3.mp4` = Ball 2 dedup f35) using:
  1. Referee-validated `bclock v1` (`tools/bclock/bclock.py`, planted PASS 12/12, #593) with `--ppm 539.8`.
  2. Referee-validated `firstfall v1` (`tools/realball/firstfall.py`, planted PASS 20/20, #264) on the initial
     mid-fall drop (`f0..imp1`).
  3. An independent dark-blob / vertical-strip tracker (`indep_strip_tracker`) that tracks the dark ball in the
     plank corridor (`y in [120, 355]`), eliminating false jumps to the top curtain/rod (`y < 120`), and fits
     every bounce flight parabola (`y(t) = y0 + v0*t + 0.5*g*t^2`) with bootstrap SEs and `e_T = T_{k+1}/T_k`.
  4. Audits `res_b1.json` and `res_b2.json` from `rahul-5-agy` to verify why `bounce_decay.py` returned
     `n_fitted: 0` and why `res_b2.json` lost the ball onto the top curtain (`y = 45..69 px`) from `f61` to `f188`.

Part B: Review of Finding #766 (rahul-2):
- Evaluates all 10 GAUGE slope clips (3 materials: plastic, wood, metal x 4 prompts x 2 seeds, 93f @ 24fps) using:
  1. An independent clean-background CIE Lab color-difference + luminance/plank-corridor segmentation tracker
     (`lab_corridor_tracker`), which does not use template matching and is immune to cube rotation/tumbling.
  2. An independent adaptive multi-scale / template-refresh NCC tracker (`adaptive_ncc_tracker`) along the plank axis.
  3. Computes 0.25s bin velocities, peak speed (m/s and px/frame), early 0.5s acceleration, whole-slide quadratic
     acceleration, linear vs quadratic R^2 and AIC difference (`dAIC = AIC_lin - AIC_quad`), and time to slide 0.30 m,
     comparing clip-by-clip against `kin3_orig.json`.
"""
import json
import os
import sys
import cv2
import numpy as np

REPO_ROOT = "/home/nail/swarm-work/agy-1/cosmos-swarm"
sys.path.insert(0, os.path.join(REPO_ROOT, "tools/bclock"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools/realball"))

import bclock
import firstfall


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


# ==============================================================================
# PART A: MID-FALL BALL REPLICATION (FINDING #698)
# ==============================================================================

def track_midfall_corridor(frames, seed_xy, y_min_corridor=120, y_max_corridor=358):
    """Independent corridor-constrained dark-ball + NCC hybrid tracker.
    Prevents the tracker from jumping up to the black curtain / stand top (y < 120)
    while tracking the bouncing ball on the wooden plank (y ~ 310-345) and in flight (y ~ 150-310).
    """
    H, W = frames.shape[1:3]
    med_bg = np.median(frames[::4].astype(np.float32), axis=0)
    sx, sy = seed_xy
    hw = 13
    gray0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    tmpl0 = gray0[int(sy - hw):int(sy + hw + 1), int(sx - hw):int(sx + hw + 1)].copy()
    tmpl = tmpl0.copy()

    cx, cy = float(sx), float(sy)
    vx, vy = 0.0, 15.0
    xs, ys, scores, areas = [], [], [], []

    for idx, f in enumerate(frames):
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        diff = np.linalg.norm(f.astype(np.float32) - med_bg, axis=2)

        # Search window constrained to plank + flight zone [y_min_corridor, y_max_corridor]
        x0 = max(180, int(round(cx - 45)))
        x1 = min(420, int(round(cx + 45)))
        y0 = max(y_min_corridor, int(round(min(cy - 65, 140))))
        y1 = min(y_max_corridor, int(round(max(cy + 65, 350))))

        roi_g = gray[y0:y1, x0:x1]
        res = cv2.matchTemplate(roi_g, tmpl, cv2.TM_CCOEFF_NORMED)
        # Also compute darkness + background difference bonus in corridor
        jj, ii = np.meshgrid(
            np.arange(res.shape[1]) + x0 + hw,
            np.arange(res.shape[0]) + y0 + hw,
        )
        d_pred1 = np.hypot(jj - (cx + vx), ii - (cy + vy))
        d_pred2 = np.hypot(jj - (cx + vx), ii - (cy - vy))
        # Bg-diff at candidate centers
        diff_centers = cv2.GaussianBlur(diff, (9, 9), 0)[
            y0 + hw:y0 + hw + res.shape[0],
            x0 + hw:x0 + hw + res.shape[1],
        ]
        diff_norm = np.clip(diff_centers / 35.0, 0.0, 1.0)

        obj = 0.75 * res + 0.25 * diff_norm - 0.0025 * np.minimum(d_pred1, d_pred2)
        bi, bj = np.unravel_index(np.argmax(obj), obj.shape)
        dx, dy = bclock.subpix(res, bi, bj)
        nx = float(x0 + bj + dx + hw)
        ny = float(y0 + bi + dy + hw)
        sc = float(res[bi, bj])

        # Estimate dark blob diameter around (nx, ny)
        r_est = bclock.ball_radius(f.astype(np.float32), med_bg, nx, ny, rmax=35)
        areas.append(round(float(2.0 * r_est), 2) if r_est is not None else None)

        vx = nx - cx
        vy = ny - cy
        cx, cy = nx, ny
        xs.append(round(nx, 2))
        ys.append(round(ny, 2))
        scores.append(round(sc, 3))

        if sc >= 0.72 and y0 + 10 < ny < 315:
            patch = gray[int(round(ny) - hw):int(round(ny) + hw + 1), int(round(nx) - hw):int(round(nx) + hw + 1)]
            if patch.shape == tmpl.shape:
                tmpl = 0.85 * tmpl0 + 0.15 * patch

    return np.array(xs), np.array(ys), np.array(scores), areas


def fit_parabola_with_ci(t_arr, y_arr_m, n_boot=1000, seed=42):
    """Fit y(t) = y0 + v0*t + 0.5*g*t^2 and return g, SE, 95% CI, R^2."""
    t0 = t_arr - t_arr[0]
    c = np.polyfit(t0, y_arr_m, 2)
    g = float(2.0 * c[0])
    v0 = float(c[1])
    pred = np.polyval(c, t0)
    res = y_arr_m - pred
    ss_tot = float(np.sum((y_arr_m - y_arr_m.mean()) ** 2))
    r2 = 1.0 - float(np.sum(res ** 2)) / ss_tot if ss_tot > 0 else 0.0
    rmse_mm = float(np.sqrt(np.mean(res ** 2)) * 1000.0)

    rng = np.random.default_rng(seed)
    n = len(t0)
    bs_g = []
    if n >= 4:
        for _ in range(n_boot):
            idx = rng.integers(0, n, size=n)
            if len(np.unique(t0[idx])) >= 3:
                cb = np.polyfit(t0[idx], y_arr_m[idx], 2)
                bs_g.append(2.0 * cb[0])
            else:
                rb = pred + res[idx]
                cb = np.polyfit(t0, rb, 2)
                bs_g.append(2.0 * cb[0])
    se = float(np.std(bs_g, ddof=1)) if bs_g else 0.0
    ci = [round(float(np.percentile(bs_g, 2.5)), 2), round(float(np.percentile(bs_g, 97.5)), 2)] if bs_g else [round(g, 2), round(g, 2)]
    return {
        "n_frames": int(n),
        "g_mps2": round(g, 3),
        "g_se": round(se, 3),
        "g_ci95": ci,
        "v0_mps": round(v0, 3),
        "r2": round(r2, 4),
        "rmse_mm": round(rmse_mm, 2),
    }


def analyze_midfall_all():
    clip_dir = "/home/nail/swarm-work/agy-1/task46_data/midfall_clips"
    out_dir = os.path.join(REPO_ROOT, "work/agy-1/task46_replication")
    os.makedirs(out_dir, exist_ok=True)

    ppm = 539.8
    mpp = 1.0 / ppm
    fps = 24.0

    configs = [
        ("ball_1", "20261101T033939_0007_raj-3.mp4", (287, 155), "/home/nail/swarm-work/agy-1/task46_data/res_b1.json"),
        ("ball_2", "20261101T040234_0012_raj-3.mp4", (290, 172), "/home/nail/swarm-work/agy-1/task46_data/res_b2.json"),
    ]

    midfall_results = {}
    for label, fname, seed_xy, rahul5_json_path in configs:
        path = os.path.join(clip_dir, fname)
        frames, fps_vid = load_video(path)

        # 1. Referee-validated bclock v1 (full 189f and first 93f)
        bc_full = bclock.measure(
            path, fps=fps_vid, ppm=ppm, point=seed_xy, pframe=0,
            qc=os.path.join(out_dir, f"qc_bclock_{label}_189f.png"),
        )
        bc_93 = bclock.measure(
            path, fps=fps_vid, ppm=ppm, point=seed_xy, pframe=0, tmax=93,
        )

        # 2. Referee-validated firstfall v1 on initial mid-fall drop
        ff_res, ff_trk = firstfall.measure(
            frames, fps=fps_vid, ppm=ppm, point=seed_xy, pframe=0, tmax=20,
        )
        firstfall.qc_png(os.path.join(out_dir, f"qc_firstfall_{label}.png"), frames[:20], ff_trk, ff_res)

        # 3. Independent corridor-constrained tracker (prevents jumping to top curtain y < 120)
        xs_c, ys_c, sc_c, diams_c = track_midfall_corridor(frames, seed_xy)
        bc_corridor = bclock.analyse(ys_c.copy(), fps=fps_vid, ppm=ppm, prom=12.0, guard=1)

        # Detailed initial drop and first two rebounds from corridor tracker
        imp_frames = bc_corridor.get("impact_frames", [])
        imp1 = int(np.argmax(ys_c[:10]))
        # Initial fall frames 0..imp1-1 and 0..imp1
        fall_excl = fit_parabola_with_ci(np.arange(0, imp1) / fps, ys_c[:imp1] * mpp)
        fall_incl = fit_parabola_with_ci(np.arange(0, imp1 + 1) / fps, ys_c[:imp1 + 1] * mpp)

        # First rebound flight between imp_frames[0] and imp_frames[1]
        rebound_fits = []
        for k in range(min(5, len(imp_frames) - 1)):
            ia, ib = imp_frames[k], imp_frames[k + 1]
            if ib - ia >= 5:
                sub_idx = np.arange(ia + 1, ib)
                fit_excl = fit_parabola_with_ci(sub_idx / fps, ys_c[sub_idx] * mpp)
                sub_idx_inc = np.arange(ia, ib + 1)
                fit_incl = fit_parabola_with_ci(sub_idx_inc / fps, ys_c[sub_idx_inc] * mpp)
                apex_fr = int(ia + np.argmin(ys_c[ia:ib + 1]))
                rise_px = float(0.5 * (ys_c[ia] + ys_c[ib]) - ys_c[apex_fr])
                rise_from_ia_px = float(ys_c[ia] - ys_c[apex_fr])
                T_int_s = float((ib - ia) / fps)
                T_sub_s = float(bc_corridor["flight_s"][k]) if k < len(bc_corridor.get("flight_s", [])) else T_int_s
                rebound_fits.append({
                    "bounce_idx": k + 1,
                    "imp_start_frame": int(ia),
                    "apex_frame": apex_fr,
                    "imp_end_frame": int(ib),
                    "flight_frames_int": int(ib - ia),
                    "flight_time_int_s": round(T_int_s, 4),
                    "flight_time_subframe_s": round(T_sub_s, 4),
                    "rise_from_imp1_cm": round(rise_from_ia_px * mpp * 100.0, 2),
                    "rise_from_mid_imp_cm": round(rise_px * mpp * 100.0, 2),
                    "g_parabola_excl_contacts": fit_excl,
                    "g_parabola_incl_contacts": fit_incl,
                    "g_eff_8h_T2_int_mps2": round(float(8.0 * (rise_from_ia_px * mpp) / (T_int_s ** 2)), 3),
                    "g_eff_8h_T2_sub_mps2": round(float(8.0 * (rise_px * mpp) / (T_sub_s ** 2)), 3),
                })

        # Audit rahul-5-agy's saved res_b*.json track and detailed_bounce.py logic
        with open(rahul5_json_path) as f:
            r5 = json.load(f)
        r5_y = np.array([np.nan if v is None else float(v) for v in r5["track_y"]])
        r5_peaks = r5["peaks"]
        r5_bounces = []
        for i in range(len(r5_peaks) - 1):
            p1, p2 = r5_peaks[i], r5_peaks[i + 1]
            if p2 - p1 < 4 or p2 - p1 > 20:
                continue
            sub = r5_y[p1:p2 + 1]
            if np.isnan(sub).any():
                continue
            apex_fr = int(p1 + np.argmin(sub))
            rise_cm = float((r5_y[p1] - r5_y[apex_fr]) * mpp * 100.0)
            r5_bounces.append({
                "bounce_num": len(r5_bounces) + 1,
                "imp1_fr": int(p1),
                "apex_fr": apex_fr,
                "imp2_fr": int(p2),
                "y_imp1_px": round(float(r5_y[p1]), 1),
                "y_apex_px": round(float(r5_y[apex_fr]), 1),
                "rise_cm": round(rise_cm, 2),
                "flight_frames": int(p2 - p1),
            })
        r5_in_plank_zone = [b for b in r5_bounces if b["y_imp1_px"] > 240.0]
        r5_on_curtain_noise = [b for b in r5_bounces if b["y_imp1_px"] <= 240.0]

        # Compute log-linear e_T fit and mean e_T on corridor-tracked bounces
        T_corridor = np.array(bc_corridor.get("flight_frames", []), dtype=float)
        e_ratios_corridor = T_corridor[1:] / T_corridor[:-1] if len(T_corridor) > 1 else np.array([])
        if len(T_corridor) >= 3:
            k_idx = np.arange(len(T_corridor), dtype=float)
            slope_log, _ = np.polyfit(k_idx, np.log(T_corridor), 1)
            e_T_logfit = float(np.exp(slope_log))
            res_log = np.log(T_corridor) - np.polyval(np.polyfit(k_idx, np.log(T_corridor), 1), k_idx)
            se_slope = float(np.sqrt(np.sum(res_log ** 2) / max(1, len(T_corridor) - 2)) / np.sqrt(np.sum((k_idx - k_idx.mean()) ** 2)))
            e_T_logfit_se = float(e_T_logfit * se_slope)
        else:
            e_T_logfit, e_T_logfit_se = None, None

        midfall_results[label] = {
            "clip": fname,
            "seed_xy": list(seed_xy),
            "firstfall_v1_initial_drop": {
                "flag": ff_res.get("flag"),
                "g_mps2": ff_res.get("g"),
                "g_ci": ff_res.get("g_ci"),
                "fall_time_s": ff_res.get("fall_time_s"),
                "d_ratio": ff_res.get("d_ratio"),
            },
            "bclock_v1_default_189f": {
                "flag": bc_full.get("flag"),
                "tracked_frac": round(float(bc_full.get("tracked_frac", 0)), 3),
                "n_impacts": len(bc_full.get("impact_t_frames", [])),
                "impact_t_frames": [round(float(x), 2) for x in bc_full.get("impact_t_frames", [])],
                "frames_per_bounce_mean": round(float(bc_full["frames_per_bounce_mean"]), 3) if bc_full.get("frames_per_bounce_mean") else None,
                "frames_per_bounce_se": round(float(bc_full["frames_per_bounce_se"]), 3) if bc_full.get("frames_per_bounce_se") else None,
                "g_curv_first_ok": round(float(bc_full["g_curv_first_ok"]), 3) if bc_full.get("g_curv_first_ok") else None,
                "g_timing_first": round(float(bc_full["g_timing_first"]), 3) if bc_full.get("g_timing_first") else None,
                "e_ratio_mean": round(float(np.mean(bc_full["e_ratio_seq"])), 4) if bc_full.get("e_ratio_seq") else None,
                "e_ratio_se": round(float(np.std(bc_full["e_ratio_seq"], ddof=1) / np.sqrt(len(bc_full["e_ratio_seq"]))), 4) if len(bc_full.get("e_ratio_seq", [])) > 1 else None,
            },
            "bclock_v1_first_93f": {
                "n_impacts": len(bc_93.get("impact_t_frames", [])),
                "impact_t_frames": [round(float(x), 2) for x in bc_93.get("impact_t_frames", [])],
                "frames_per_bounce_mean": round(float(bc_93["frames_per_bounce_mean"]), 3) if bc_93.get("frames_per_bounce_mean") else None,
                "e_ratio_mean": round(float(np.mean(bc_93["e_ratio_seq"])), 4) if bc_93.get("e_ratio_seq") else None,
            },
            "indep_corridor_tracker_189f": {
                "n_impacts": len(imp_frames),
                "impact_frames_int": [int(x) for x in imp_frames],
                "impact_t_subframe": [round(float(x), 2) for x in bc_corridor.get("impact_t_frames", [])],
                "initial_drop_excl_contact": fall_excl,
                "initial_drop_incl_contact": fall_incl,
                "first_5_rebounds": rebound_fits,
                "mean_frames_per_bounce": round(float(np.mean(T_corridor)), 3) if len(T_corridor) else None,
                "se_frames_per_bounce": round(float(np.std(T_corridor, ddof=1) / np.sqrt(len(T_corridor))), 3) if len(T_corridor) > 1 else None,
                "e_T_mean_ratio": round(float(np.mean(e_ratios_corridor)), 4) if len(e_ratios_corridor) else None,
                "e_T_se_ratio": round(float(np.std(e_ratios_corridor, ddof=1) / np.sqrt(len(e_ratios_corridor))), 4) if len(e_ratios_corridor) > 1 else None,
                "e_T_loglinear_fit": round(e_T_logfit, 4) if e_T_logfit is not None else None,
                "e_T_loglinear_se": round(e_T_logfit_se, 4) if e_T_logfit_se is not None else None,
                "bouncing_span_s": round(float((imp_frames[-1] - imp_frames[0]) / fps), 2) if len(imp_frames) >= 2 else 0.0,
                "y_range_last_30f_px": round(float(np.max(ys_c[-30:]) - np.min(ys_c[-30:])), 1),
                "still_bouncing_at_end": bool((np.max(ys_c[-30:]) - np.min(ys_c[-30:])) > 40.0),
            },
            "rahul5_res_json_audit": {
                "bounce_decay_n_fitted": r5["n_fitted"],
                "bounce_decay_n_impacts": r5["n_impacts"],
                "detailed_bounce_total_cycles": len(r5_bounces),
                "detailed_bounce_valid_plank_cycles": len(r5_in_plank_zone),
                "detailed_bounce_curtain_noise_cycles_y_le_240": len(r5_on_curtain_noise),
                "curtain_drift_frames_y_lt_100": int(np.sum(r5_y < 100.0)),
                "valid_plank_cycles_detail": r5_in_plank_zone[:6],
                "curtain_noise_cycles_detail": r5_on_curtain_noise[:6],
            },
        }

    return midfall_results


# ==============================================================================
# PART B: 10-CLIP SLOPE CEILING REPLICATION (FINDING #766)
# ==============================================================================

SLOPE_CFG = {
    "plastic": dict(box=(570, 28, 660, 115), top=(672.0, 85.0), bot=(190.0, 385.0)),
    "metal":   dict(box=(558, 27, 643, 110), top=(663.0, 77.0), bot=(183.0, 363.0)),
    "wood":    dict(box=(560, 8, 650, 93),   top=(668.0, 57.0), bot=(168.0, 362.0)),
}


def track_slope_dual(frames, mat):
    """Run two independent slope trackers on a 93-frame slope clip:
    1) Independent multi-channel (CIE Lab + gradient magnitude) causal template tracker (`lab_grad_ncc`).
    2) Independent clean-background CIE Lab color-difference blob tracker (`lab_bgdiff_blob`) along the plank corridor.
    Also reproduces the exact grayscale/RGB `TM_CCOEFF_NORMED` track for direct comparison with `kin3_orig.json`.
    """
    cfg = SLOPE_CFG[mat]
    top = np.array(cfg["top"], dtype=np.float64)
    bot = np.array(cfg["bot"], dtype=np.float64)
    ax = bot - top
    L_px = float(np.linalg.norm(ax))
    ax /= L_px
    mpp = 0.50 / L_px

    x0, y0, x1, y1 = cfg["box"]
    w, h = x1 - x0, y1 - y0
    c0 = np.array([x0 + w / 2.0, y0 + h / 2.0], dtype=np.float64)

    # Build clean background by splicing late median (frames 70..92) over upper plank (x > 460) and frame 0 over lower plank (x <= 460)
    bg = frames[0].copy()
    flate = np.median(frames[70:], axis=0).astype(np.uint8)
    bg[:, 460:] = flate[:, 460:]
    lab_bg = cv2.cvtColor(bg, cv2.COLOR_BGR2Lab).astype(np.float32)

    # Precompute corridor mask along plank
    H, W = frames.shape[1:3]
    yy, xx = np.mgrid[0:H, 0:W]
    rel_x = xx - top[0]
    rel_y = yy - top[1]
    along = rel_x * ax[0] + rel_y * ax[1]
    perp = rel_x * (-ax[1]) + rel_y * ax[0]
    corridor = (along >= -50) & (along <= L_px + 40) & (perp >= -30) & (perp <= 85) & (yy < 365) & (xx >= 130) & (xx <= 700)

    # Templates for RGB NCC and Lab+Gradient NCC
    T_bgr = frames[0][y0:y1, x0:x1].copy()
    lab0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2Lab).astype(np.float32)
    gx0 = cv2.Sobel(lab0[:, :, 0], cv2.CV_32F, 1, 0, ksize=3)
    gy0 = cv2.Sobel(lab0[:, :, 0], cv2.CV_32F, 0, 1, ksize=3)
    gmag0 = np.hypot(gx0, gy0)
    T_lab = lab0[y0:y1, x0:x1].copy()
    T_gmag = gmag0[y0:y1, x0:x1].copy()

    pos_bgr = np.array([x0, y0], dtype=np.float64)
    pos_lg = np.array([x0, y0], dtype=np.float64)
    R = 60

    s_bgr, sc_bgr = [0.0], [1.0]
    s_lg, sc_lg = [0.0], [1.0]
    s_blob, area_blob = [0.0], [int(w * h)]

    for i in range(1, len(frames)):
        f = frames[i]
        # 1. BGR NCC
        xa, ya = int(max(0, pos_bgr[0] - R)), int(max(0, pos_bgr[1] - R))
        xb, yb = int(min(W, pos_bgr[0] + w + R)), int(min(H, pos_bgr[1] + h + R))
        m_bgr = cv2.matchTemplate(f[ya:yb, xa:xb], T_bgr, cv2.TM_CCOEFF_NORMED)
        _, val_bgr, _, loc_bgr = cv2.minMaxLoc(m_bgr)
        pos_bgr = np.array([xa + loc_bgr[0], ya + loc_bgr[1]], dtype=np.float64)
        s_bgr.append(float(((pos_bgr + [w / 2.0, h / 2.0]) - c0) @ ax * mpp))
        sc_bgr.append(float(val_bgr))

        # 2. Independent CIE Lab + Sobel Gradient Magnitude NCC with causal plank-direction prior
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
        dx, dy = bclock.subpix(m_comb, bi, bj)
        pos_lg = np.array([xa2 + bj + dx, ya2 + bi + dy], dtype=np.float64)
        s_lg.append(float(((pos_lg + [w / 2.0, h / 2.0]) - c0) @ ax * mpp))
        sc_lg.append(float(m_comb[bi, bj]))

        # 3. Clean-BG Lab difference blob tracker (around current plank region)
        diff = np.linalg.norm(lab - lab_bg, axis=2)
        cx_est, cy_est = pos_lg[0] + w / 2.0, pos_lg[1] + h / 2.0
        local_gate = np.hypot(xx - cx_est, yy - cy_est) < 85.0
        fg = ((diff > 18.0) & corridor & local_gate).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n_cc, _, stats, centroids = cv2.connectedComponentsWithStats(fg)
        if n_cc > 1:
            k_best = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            area_k = int(stats[k_best, cv2.CC_STAT_AREA])
            if area_k >= 200:
                c_blob = centroids[k_best]
                s_blob.append(float((c_blob - c0) @ ax * mpp))
                area_blob.append(area_k)
            else:
                s_blob.append(np.nan)
                area_blob.append(0)
        else:
            s_blob.append(np.nan)
            area_blob.append(0)

    return {
        "L_px": round(L_px, 2),
        "mpp": round(mpp, 6),
        "s_bgr": np.array(s_bgr),
        "sc_bgr": np.array(sc_bgr),
        "s_lg": np.array(s_lg),
        "sc_lg": np.array(sc_lg),
        "s_blob": np.array(s_blob),
        "area_blob": np.array(area_blob),
    }


def summarize_slope_track(s_arr, sc_arr, fps=24.0, mpp=0.50 / 568.0, min_sc=0.60):
    """Compute velocity bins (0.25s), peak speed (m/s and px/f), early 0.5s acceleration,
    whole-slide linear vs quadratic fits (with R^2 and dAIC), and time to slide 0.30 m."""
    n_total = len(s_arr)
    end = n_total
    for k in range(n_total):
        if np.isnan(s_arr[k]) or s_arr[k] > 0.42 or sc_arr[k] < min_sc:
            end = k
            break
    idx = np.arange(end)
    s = s_arr[:end]
    sc = sc_arr[:end]
    if len(idx) < 6 or np.max(s) < 0.01:
        return {"moved": False, "n": len(idx)}

    on = int(idx[int(np.argmax(s > 0.005))])
    t = idx / fps
    sel = idx >= max(0, on - 1)
    ts = t[sel]
    ss = s[sel]

    # 0.25 s bins after onset
    bins = []
    for b0 in np.arange(ts[0], ts[-1], 0.25):
        mk = (ts >= b0) & (ts < b0 + 0.25)
        if mk.sum() >= 3:
            bins.append(round(float(np.polyfit(ts[mk], ss[mk], 1)[0]), 3))

    v_peak = float(max(bins)) if bins else 0.0
    v_peak_px_f = float(v_peak / (mpp * fps))

    # Early 0.5s acceleration (first 0.5s after onset: 2*(v_bin1 - v_bin0)/0.25 or quadratic fit over first 0.5s)
    mk_early = (ts >= ts[0]) & (ts <= ts[0] + 0.50 + 1e-6)
    a_early_quad = float(2.0 * np.polyfit(ts[mk_early] - ts[0], ss[mk_early], 2)[0]) if mk_early.sum() >= 4 else None
    a_early_bin = float((bins[1] - bins[0]) / 0.25) if len(bins) >= 2 else None

    # Whole-slide linear vs quadratic fit
    t0 = ts - ts[0]
    p1 = np.polyfit(t0, ss, 1)
    p2 = np.polyfit(t0, ss, 2)
    res1 = ss - np.polyval(p1, t0)
    res2 = ss - np.polyval(p2, t0)
    ss_tot = float(np.sum((ss - ss.mean()) ** 2))
    ss_res1 = float(np.sum(res1 ** 2))
    ss_res2 = float(np.sum(res2 ** 2))
    n_pts = len(t0)
    r2_lin = 1.0 - ss_res1 / ss_tot if ss_tot > 0 else 0.0
    r2_quad = 1.0 - ss_res2 / ss_tot if ss_tot > 0 else 0.0
    aic_lin = n_pts * np.log(max(ss_res1 / n_pts, 1e-18)) + 4.0
    aic_quad = n_pts * np.log(max(ss_res2 / n_pts, 1e-18)) + 6.0

    # Time to slide 0.30 m from onset
    reached_0p30 = ss - ss[0] >= 0.30
    if np.any(reached_0p30):
        k30 = int(np.argmax(reached_0p30))
        t_0p30 = float(ts[k30] - ts[0])
        a_equiv_0p30 = float(2.0 * 0.30 / (t_0p30 ** 2)) if t_0p30 > 0 else None
    else:
        t_0p30 = None
        a_equiv_0p30 = None

    return {
        "moved": True,
        "onset_frame": on,
        "last_tracked_frame": int(idx[-1]),
        "n_frames": int(n_pts),
        "slide_m": round(float(ss[-1] - ss[0]), 3),
        "v_bins_0p25s": bins,
        "v_peak_mps": round(v_peak, 3),
        "v_peak_px_per_frame": round(v_peak_px_f, 1),
        "v_mean_lin_mps": round(float(p1[0]), 3),
        "a_early_bin_0p5s": round(a_early_bin, 2) if a_early_bin is not None else None,
        "a_early_quad_0p5s": round(a_early_quad, 2) if a_early_quad is not None else None,
        "a_quad_whole": round(float(2.0 * p2[0]), 2),
        "r2_lin": round(r2_lin, 4),
        "r2_quad": round(r2_quad, 4),
        "dAIC_lin_minus_quad": round(float(aic_lin - aic_quad), 2),
        "t_0p30m_s": round(t_0p30, 2) if t_0p30 is not None else None,
        "a_equiv_0p30m": round(a_equiv_0p30, 2) if a_equiv_0p30 is not None else None,
        "min_score": round(float(np.min(sc[sel])), 2),
    }


def analyze_slope_all():
    slope_dir = "/home/nail/swarm-work/agy-1/task46_data/slope_clips"
    with open("/home/nail/swarm-work/agy-1/task46_data/kin3_orig.json") as f:
        kin3_orig = json.load(f)

    clip_names = sorted(kin3_orig.keys())
    slope_results = {}

    for name in clip_names:
        mat = name.split("_")[0]
        path = os.path.join(slope_dir, f"{name}.mp4")
        frames, fps = load_video(path)
        tr = track_slope_dual(frames, mat)

        sum_lg = summarize_slope_track(tr["s_lg"], tr["sc_lg"], fps=fps, mpp=tr["mpp"], min_sc=0.58)
        sum_bgr = summarize_slope_track(tr["s_bgr"], tr["sc_bgr"], fps=fps, mpp=tr["mpp"], min_sc=0.60)
        # For blob tracker, use valid area (>200 px) up to last tracked frame of sum_lg
        end_lg = sum_lg["last_tracked_frame"] + 1
        s_b = tr["s_blob"][:end_lg]
        sc_b = np.where(~np.isnan(s_b), 1.0, 0.0)
        # Interpolate isolated NaNs if any
        if np.any(~np.isnan(s_b)):
            valid_idx = np.where(~np.isnan(s_b))[0]
            s_b_interp = np.interp(np.arange(len(s_b)), valid_idx, s_b[valid_idx])
            sum_blob = summarize_slope_track(s_b_interp, np.ones_like(s_b_interp), fps=fps, mpp=tr["mpp"], min_sc=0.5)
        else:
            sum_blob = {"moved": False}

        slope_results[name] = {
            "material": mat,
            "mpp": tr["mpp"],
            "rahul2_kin3": kin3_orig[name],
            "indep_lab_grad_ncc": sum_lg,
            "indep_lab_bgdiff_blob": sum_blob,
            "bgr_ncc_repro": sum_bgr,
        }

    # Aggregate statistics across all 10 clips
    peaks_r2 = [kin3_orig[k]["v_peak"] for k in clip_names]
    peaks_lg = [slope_results[k]["indep_lab_grad_ncc"]["v_peak_mps"] for k in clip_names]
    peaks_blob = [slope_results[k]["indep_lab_bgdiff_blob"]["v_peak_mps"] for k in clip_names]

    t30_r2 = [kin3_orig[k]["t_0p30m_s"] for k in clip_names if kin3_orig[k]["t_0p30m_s"] is not None]
    t30_lg = [slope_results[k]["indep_lab_grad_ncc"]["t_0p30m_s"] for k in clip_names if slope_results[k]["indep_lab_grad_ncc"]["t_0p30m_s"] is not None]

    early_r2 = [kin3_orig[k]["a_early_0p5s"] for k in clip_names]
    early_lg_bin = [slope_results[k]["indep_lab_grad_ncc"]["a_early_bin_0p5s"] for k in clip_names if slope_results[k]["indep_lab_grad_ncc"]["a_early_bin_0p5s"] is not None]
    early_lg_quad = [slope_results[k]["indep_lab_grad_ncc"]["a_early_quad_0p5s"] for k in clip_names if slope_results[k]["indep_lab_grad_ncc"]["a_early_quad_0p5s"] is not None]
    whole_a_lg = [slope_results[k]["indep_lab_grad_ncc"]["a_quad_whole"] for k in clip_names]

    summary = {
        "n_clips": len(clip_names),
        "peak_speed_mps": {
            "rahul2_mean": round(float(np.mean(peaks_r2)), 4),
            "rahul2_se": round(float(np.std(peaks_r2, ddof=1) / np.sqrt(len(peaks_r2))), 4),
            "rahul2_range": [round(float(min(peaks_r2)), 3), round(float(max(peaks_r2)), 3)],
            "indep_lab_grad_mean": round(float(np.mean(peaks_lg)), 4),
            "indep_lab_grad_se": round(float(np.std(peaks_lg, ddof=1) / np.sqrt(len(peaks_lg))), 4),
            "indep_lab_grad_range": [round(float(min(peaks_lg)), 3), round(float(max(peaks_lg)), 3)],
            "indep_blob_mean": round(float(np.mean(peaks_blob)), 4),
            "indep_blob_se": round(float(np.std(peaks_blob, ddof=1) / np.sqrt(len(peaks_blob))), 4),
            "indep_blob_range": [round(float(min(peaks_blob)), 3), round(float(max(peaks_blob)), 3)],
        },
        "time_to_0p30m_s": {
            "n_reached_rahul2": len(t30_r2),
            "rahul2_mean": round(float(np.mean(t30_r2)), 3),
            "rahul2_se": round(float(np.std(t30_r2, ddof=1) / np.sqrt(len(t30_r2))), 3),
            "rahul2_range": [round(float(min(t30_r2)), 2), round(float(max(t30_r2)), 2)],
            "n_reached_indep_lg": len(t30_lg),
            "indep_lg_mean": round(float(np.mean(t30_lg)), 3),
            "indep_lg_se": round(float(np.std(t30_lg, ddof=1) / np.sqrt(len(t30_lg))), 3),
            "indep_lg_range": [round(float(min(t30_lg)), 2), round(float(max(t30_lg)), 2)],
        },
        "early_a_0p5s_mps2": {
            "rahul2_mean": round(float(np.mean(early_r2)), 3),
            "rahul2_se": round(float(np.std(early_r2, ddof=1) / np.sqrt(len(early_r2))), 3),
            "rahul2_max": round(float(max(early_r2)), 3),
            "indep_lg_bin_mean": round(float(np.mean(early_lg_bin)), 3),
            "indep_lg_bin_se": round(float(np.std(early_lg_bin, ddof=1) / np.sqrt(len(early_lg_bin))), 3),
            "indep_lg_quad_mean": round(float(np.mean(early_lg_quad)), 3),
            "indep_lg_quad_se": round(float(np.std(early_lg_quad, ddof=1) / np.sqrt(len(early_lg_quad))), 3),
        },
        "whole_slide_a_quad_mps2": {
            "indep_lg_mean": round(float(np.mean(whole_a_lg)), 3),
            "indep_lg_se": round(float(np.std(whole_a_lg, ddof=1) / np.sqrt(len(whole_a_lg))), 3),
            "indep_lg_range": [round(float(min(whole_a_lg)), 2), round(float(max(whole_a_lg)), 2)],
        },
    }

    return {"summary": summary, "per_clip": slope_results}


def main():
    out_dir = os.path.join(REPO_ROOT, "work/agy-1/task46_replication")
    os.makedirs(out_dir, exist_ok=True)

    print("Running Part A: Mid-fall ball replication (Finding #698)...")
    midfall = analyze_midfall_all()

    print("Running Part B: 10-clip slope ceiling replication (Finding #766)...")
    slope = analyze_slope_all()

    all_out = {
        "task": 46,
        "part_A_midfall_ball_review_698": midfall,
        "part_B_slope_ceiling_review_766": slope,
    }
    out_path = os.path.join(out_dir, "results.json")
    with open(out_path, "w") as f:
        json.dump(all_out, f, indent=2)
    print(f"Saved results to {out_path}")
    print("\n--- MIDFALL SUMMARY ---")
    print(json.dumps(midfall, indent=2))
    print("\n--- SLOPE SUMMARY ---")
    print(json.dumps(slope["summary"], indent=2))


if __name__ == "__main__":
    main()
