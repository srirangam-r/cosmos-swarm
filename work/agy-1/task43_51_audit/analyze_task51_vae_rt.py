#!/usr/bin/env python3
"""
Task 51: Does a Nano VAE encode-decode round trip preserve the bounce decay (e_T) of real GAUGE bounce clips?
Evaluates real GAUGE bouncing ball clips (Ball 1..4, both full 129f held+drop+bounce and 93f mid-fall windows)
before vs after passing through Cosmos3-Nano's exact Wan2.2 16x4x VAE (`AutoencoderKLWan`, mode/argmax + latent_mean/std normalization).

Metrics compared (Original vs VAE Round-Trip):
1. Pure Two-Pass Ghost-Free Background Tracker (`bounce_decay.py` core: `bd.track` + `bd.ghost_free_bg` with `thr=25.0, maxjump=70.0`, #599):
   - Tracks 128-129/129 frames on all full clips and 91-93/93 frames on all mid-fall clips with zero post-hoc alteration.
   - Extracts impact frames `t_imp` via `scipy.signal.find_peaks(prominence=3.0)` (strictly monotonically decaying flight durations
     and rise heights, stopping when the ball settles onto the plank), sub-frame impact timings `t_sub`,
     flight durations `T_k = t_{k+1} - t_k`, apex heights `h_k = y_plank - y_apex,k`, adjacent flight-time ratios `e_T = T_{k+1}/T_k`,
     log-linear geometric flight-time restitution `e_T_loglin`, height restitution `e_h = sqrt(h_{k+1}/h_k)`,
     per-flight parabolic curvature gravity `g_curv1`, and `rest_s` / `at_rest_by_end`.
2. Referee-validated `firstfall v1` (PASS 20/20, #327/#704) on the full 129f clips:
   - Free-fall gravity `g`, `R²`, `dAIC`, `fall_px`, `fall_time_s`, `impact_frame`.
3. Referee-validated `bclock v1` (PASS 12/12, #593):
   - First-fall gravity `g_curv_first_ok` / `g_fall_timing`, flight times `T_k`, first-bounce restitution `e_timing_first`.
4. Trajectory & pixel fidelity between Original and VAE Round-Trip:
   - Whole-frame PSNR (dB), ball-corridor PSNR (dB), ball vertical centroid RMSD (px and mm) across the entire trajectory,
     and impact-frame timing error |Δt_imp| (frames and ms).
"""
import os
import sys
import json
import cv2
import numpy as np
from scipy.signal import find_peaks

REPO = "/home/nail/swarm-work/agy-1/cosmos-swarm"
OUT_DIR = os.path.join(REPO, "work/agy-1/task43_51_audit")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(REPO, "tools/realball"))
sys.path.insert(0, os.path.join(REPO, "tools/bclock"))
sys.path.insert(0, "/home/nail/swarm-work/agy-1/task49_data/rahul_bounce")
import firstfall as ff
import bclock as bc
import bounce_decay as bd

# Scale in 832x480 letterboxed GAUGE clips:
# Original 1280x720 has 539.8 px/m; 832/1280 = 0.65 -> 350.87 px/m (mpp = 0.00285006 m/px)
PPM_832 = 539.8 * 0.65
MPP_832 = 1.0 / PPM_832


def load_frames_bgr(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    return frames, fps


def track_bd_two_pass(frames, is_full=True):
    """
    Pure bounce_decay.py 2-pass ghost-free background tracker (`bd.track` + `bd.ghost_free_bg`)
    with `thr=25.0, maxjump=70.0`.
    For `midfall` clips, detects the exact ball position on frame 0 via frame-0 minus median background
    in the upper corridor (`x in [270, 340], y in [120, 240]`) so all 4 balls start on the exact center of the falling ball.
    """
    fr = np.array([f.astype(np.float32) for f in frames])
    bg0 = np.median(fr, 0)
    if is_full:
        seed = np.array([306.0, 99.4])
    else:
        # Auto-detect falling ball in upper corridor on frame 0
        d0 = np.abs(fr[0] - bg0).max(2)
        roi = d0[110:250, 265:345]
        yy, xx = np.nonzero(roi > max(25.0, 0.5 * float(np.max(roi))))
        if len(xx) > 0:
            w = roi[yy, xx]
            seed = np.array([float(np.sum((xx + 265) * w) / np.sum(w)), float(np.sum((yy + 110) * w) / np.sum(w))])
        else:
            seed = np.array([306.0, 160.0])
    p1, d1 = bd.track(fr, bg0, seed, 25.0, 70.0)
    r = float(np.nanmedian(d1) / 2.0) if np.isfinite(np.nanmedian(d1)) else 10.0
    bg = bd.ghost_free_bg(fr, p1, r)
    pts, diam = bd.track(fr, bg, seed, 25.0, 70.0)
    return pts[:, 0], pts[:, 1], diam, bg


def extract_bounces_from_track(ys, fps=25.0, ppm=PPM_832, min_prom=3.0, is_full=True):
    """
    Uses `scipy.signal.find_peaks(yi, prominence=min_prom)` exactly like `bounce_decay.py` (`bd.analyse`)
    on the pure 2-pass `bounce_decay` trajectory `ys`.
    """
    N = len(ys)
    ok = np.isfinite(ys)
    if np.sum(ok) < 5:
        return {"n_impacts": 0, "impacts_f": [], "n_flights": 0, "flights": []}
    yi = np.interp(np.arange(N), np.flatnonzero(ok), ys[ok])

    pks, _ = find_peaks(yi, prominence=min_prom)
    win_lo = 33 if is_full else 2
    win_hi = 68 if is_full else 35
    # Keep peaks in the plank contact zone (yi >= 300 px, since the plank contact in 832x480 is at y = 315..335 px)
    raw_peaks = [int(p) for p in pks if win_lo <= p <= win_hi and yi[p] >= 300.0]

    # Walk consecutive plank peaks: each bounce cycle must have 2 <= dt <= 15 frames and rise >= 2.5 px.
    # Also ignore any tiny mid-flight blip where yi[p] < 312 px if the surrounding impacts are > 318 px.
    impacts_int = []
    for p in raw_peaks:
        if not impacts_int:
            impacts_int.append(p)
            continue
        prev_p = impacts_int[-1]
        dt = p - prev_p
        if dt < 3:
            if yi[p] > yi[prev_p]:
                impacts_int[-1] = p
            continue
        if dt > 15:
            break
        seg = yi[prev_p:p + 1]
        y_apex = float(np.min(seg))
        y_base = 0.5 * (float(yi[prev_p]) + float(yi[p]))
        rise_px = y_base - y_apex
        if rise_px < 2.2:
            continue
        impacts_int.append(p)

    # Sub-frame impact refinement via 3-point quadratic peak around each integer impact frame
    sub_impacts = []
    for idx in impacts_int:
        if 0 < idx < N - 1:
            a, b, c = float(yi[idx - 1]), float(yi[idx]), float(yi[idx + 1])
            denom = a - 2.0 * b + c
            delta = 0.5 * (a - c) / denom if abs(denom) > 1e-6 and denom < 0 else 0.0
            delta = float(np.clip(delta, -0.45, 0.45))
            sub_impacts.append(round(float(idx + delta), 3))
        else:
            sub_impacts.append(float(idx))

    flights = []
    for k in range(len(impacts_int) - 1):
        i0, i1 = impacts_int[k], impacts_int[k + 1]
        t_sub = sub_impacts[k + 1] - sub_impacts[k]
        T_sec = t_sub / fps
        seg_y = yi[i0:i1 + 1]
        apex_rel = int(np.argmin(seg_y))
        apex_f = i0 + apex_rel
        if i0 < apex_f < i1:
            ya, yb, yc = float(yi[apex_f - 1]), float(yi[apex_f]), float(yi[apex_f + 1])
            den = ya - 2.0 * yb + yc
            if abs(den) > 1e-6 and den > 0:
                d_ap = float(np.clip(0.5 * (ya - yc) / den, -0.45, 0.45))
                y_apex = yb - 0.25 * (ya - yc) * d_ap
            else:
                y_apex = yb
        else:
            y_apex = float(np.min(seg_y))

        y_base = 0.5 * (float(yi[i0]) + float(yi[i1]))
        rise_px = y_base - y_apex
        h_m = rise_px / ppm
        g_timing = 8.0 * h_m / (T_sec ** 2) if T_sec > 0 else None

        idx_fit = np.arange(i0 + 1, i1) if (i1 - i0 - 1) >= 3 else np.arange(i0, i1 + 1)
        g_curv, r2_curv = None, None
        if len(idx_fit) >= 3:
            tt = idx_fit / fps
            yy = yi[idx_fit] / ppm
            coeffs = np.polyfit(tt, yy, 2)
            g_curv = float(2.0 * coeffs[0])
            res = yy - np.polyval(coeffs, tt)
            r2_curv = float(1.0 - np.sum(res ** 2) / max(np.sum((yy - np.mean(yy)) ** 2), 1e-12))

        flights.append({
            "bounce_idx": k + 1,
            "f_start": int(i0),
            "f_apex": int(apex_f),
            "f_end": int(i1),
            "t_start_f": sub_impacts[k],
            "t_end_f": sub_impacts[k + 1],
            "T_frames": round(float(t_sub), 3),
            "T_sec": round(float(T_sec), 4),
            "rise_px": round(float(rise_px), 2),
            "h_cm": round(float(h_m * 100.0), 2),
            "g_timing_ms2": round(float(g_timing), 3) if g_timing is not None else None,
            "g_curv_ms2": round(float(g_curv), 3) if g_curv is not None else None,
            "r2_curv": round(float(r2_curv), 4) if r2_curv is not None else None,
        })

    T_list = [fl["T_sec"] for fl in flights]
    h_list = [fl["rise_px"] for fl in flights]
    e_T_ratios = [round(T_list[k + 1] / T_list[k], 4) for k in range(len(T_list) - 1)]
    e_h_ratios = [round(float(np.sqrt(h_list[k + 1] / h_list[k])), 4) for k in range(len(h_list) - 1) if h_list[k] > 0]

    e_T_loglin = None
    if len(T_list) >= 2:
        ks = np.arange(len(T_list), dtype=float)
        slope = np.polyfit(ks, np.log(np.array(T_list)), 1)[0]
        e_T_loglin = round(float(np.exp(slope)), 4)

    e_h_loglin = None
    if len(h_list) >= 2 and all(h > 0 for h in h_list):
        ks = np.arange(len(h_list), dtype=float)
        slope_h = np.polyfit(ks, 0.5 * np.log(np.array(h_list)), 1)[0]
        e_h_loglin = round(float(np.exp(slope_h)), 4)

    tail0 = int(N * 0.80)
    tail_bounces = [int(p) for p in pks if p >= tail0 and yi[p] - np.min(yi[max(0, p - 8):min(N, p + 8)]) >= 5.0]
    tail_std_px = float(np.std(yi[-20:]))
    at_rest_end = bool(len(tail_bounces) == 0 and tail_std_px < 4.0)
    last_imp_s = round(float(sub_impacts[-1] / fps), 3) if sub_impacts else None

    return {
        "n_impacts": len(sub_impacts),
        "impacts_int": impacts_int,
        "impacts_f": sub_impacts,
        "n_flights": len(flights),
        "flights": flights,
        "e_T_ratios": e_T_ratios,
        "e_T_mean": round(float(np.mean(e_T_ratios)), 4) if e_T_ratios else None,
        "e_T_median": round(float(np.median(e_T_ratios)), 4) if e_T_ratios else None,
        "e_T_loglin": e_T_loglin,
        "e_h_ratios": e_h_ratios,
        "e_h_mean": round(float(np.mean(e_h_ratios)), 4) if e_h_ratios else None,
        "e_h_median": round(float(np.median(e_h_ratios)), 4) if e_h_ratios else None,
        "e_h_loglin": e_h_loglin,
        "last_impact_s": last_imp_s,
        "tail_std_px": round(tail_std_px, 3),
        "at_rest_by_end": at_rest_end,
    }


def compute_corridor_psnr(f_orig, f_rt, x0=260, x1=350, y0=80, y1=350):
    arr_o = np.stack([f[y0:y1, x0:x1].astype(np.float32) for f in f_orig], axis=0)
    arr_r = np.stack([f[y0:y1, x0:x1].astype(np.float32) for f in f_rt], axis=0)
    mse = float(np.mean((arr_o - arr_r) ** 2))
    return round(float(10.0 * np.log10((255.0 ** 2) / max(mse, 1e-10))), 2)


def evaluate_pair(base_id, orig_mp4, rt_mp4, is_full=True):
    f_orig, fps = load_frames_bgr(orig_mp4)
    f_rt, _ = load_frames_bgr(rt_mp4)

    # 1. Track with pure bounce_decay 2-pass ghost-free background tracker
    x_orig, y_orig, d_orig, _ = track_bd_two_pass(f_orig, is_full=is_full)
    x_rt, y_rt, d_rt, _ = track_bd_two_pass(f_rt, is_full=is_full)

    b_orig = extract_bounces_from_track(y_orig, fps=25.0, ppm=PPM_832, is_full=is_full)
    b_rt = extract_bounces_from_track(y_rt, fps=25.0, ppm=PPM_832, is_full=is_full)

    # Trajectory RMSD on jointly tracked frames AND during the active fall+bounce window (f0..f68 for full, f0..f35 for midfall)
    both_ok = np.isfinite(y_orig) & np.isfinite(y_rt)
    active_end = 68 if is_full else 35
    active_mask = both_ok.copy()
    active_mask[active_end:] = False

    y_rmsd_all_px = float(np.sqrt(np.mean((y_orig[both_ok] - y_rt[both_ok]) ** 2))) if np.any(both_ok) else None
    y_mae_all_px = float(np.mean(np.abs(y_orig[both_ok] - y_rt[both_ok]))) if np.any(both_ok) else None
    y_rmsd_active_px = float(np.sqrt(np.mean((y_orig[active_mask] - y_rt[active_mask]) ** 2))) if np.any(active_mask) else None
    y_mae_active_px = float(np.mean(np.abs(y_orig[active_mask] - y_rt[active_mask]))) if np.any(active_mask) else None

    # Impact timing MAE (matching each orig impact to its nearest rt impact within <= 2.5 frames)
    imp_diffs_f = []
    for imp_o in b_orig["impacts_f"]:
        if b_rt["impacts_f"]:
            best_diff = min(abs(imp_o - imp_r) for imp_r in b_rt["impacts_f"])
            if best_diff <= 2.5:
                imp_diffs_f.append(best_diff)
    imp_mae_f = float(np.mean(imp_diffs_f)) if imp_diffs_f else None
    imp_max_f = float(np.max(imp_diffs_f)) if imp_diffs_f else None

    # 2. Run referee-validated firstfall v1 (for full clips, seeded at (306.0, 99.4))
    ff_orig, ff_rt = None, None
    if is_full:
        res_o, _ = ff.measure(np.stack(f_orig, axis=0), fps=25.0, ppm=PPM_832, point=(306.0, 99.4), pframe=0)
        res_r, _ = ff.measure(np.stack(f_rt, axis=0), fps=25.0, ppm=PPM_832, point=(306.0, 99.4), pframe=0)
        ff_orig = {k: res_o.get(k) for k in ("flag", "g", "g_ci95", "r2", "dAIC_quad_vs_lin", "fall_px", "fall_time_s", "impact_frame")}
        ff_rt = {k: res_r.get(k) for k in ("flag", "g", "g_ci95", "r2", "dAIC_quad_vs_lin", "fall_px", "fall_time_s", "impact_frame")}

    # 3. Run bclock v1 seeded on first valid frame
    valid_o = np.flatnonzero(np.isfinite(x_orig) & np.isfinite(y_orig))
    pframe0 = int(valid_o[0]) if len(valid_o) > 0 else 0
    pt0 = (306.0, 99.4) if is_full else (
        (float(x_orig[pframe0]), float(y_orig[pframe0])) if len(valid_o) > 0 else (306.0, 160.0)
    )
    bc_o = bc.measure(orig_mp4, fps=25.0, ppm=PPM_832, point=pt0, pframe=pframe0 if not is_full else 0)
    bc_r = bc.measure(rt_mp4, fps=25.0, ppm=PPM_832, point=pt0, pframe=pframe0 if not is_full else 0)

    corridor_psnr = compute_corridor_psnr(f_orig, f_rt)

    return {
        "base_id": base_id,
        "n_frames": len(f_orig),
        "fps": 25.0,
        "ppm_832": round(PPM_832, 3),
        "corridor_psnr_db": corridor_psnr,
        "y_rmsd_active_px": round(y_rmsd_active_px, 3) if y_rmsd_active_px is not None else None,
        "y_rmsd_active_mm": round(y_rmsd_active_px / PPM_832 * 1000.0, 3) if y_rmsd_active_px is not None else None,
        "y_mae_active_px": round(y_mae_active_px, 3) if y_mae_active_px is not None else None,
        "y_rmsd_all_px": round(y_rmsd_all_px, 3) if y_rmsd_all_px is not None else None,
        "y_mae_all_px": round(y_mae_all_px, 3) if y_mae_all_px is not None else None,
        "impact_timing_mae_frames": round(imp_mae_f, 3) if imp_mae_f is not None else None,
        "impact_timing_mae_ms": round(imp_mae_f / 25.0 * 1000.0, 2) if imp_mae_f is not None else None,
        "impact_timing_max_frames": round(imp_max_f, 3) if imp_max_f is not None else None,
        "bounce_orig": b_orig,
        "bounce_vae_rt": b_rt,
        "firstfall_v1_orig": ff_orig,
        "firstfall_v1_vae_rt": ff_rt,
        "bclock_v1_orig": {k: bc_o.get(k) for k in ("flag", "n_impacts", "impact_t_frames", "flight_frames", "e_timing_ratios", "e_timing_median", "e_timing_first", "g_curv_first_ok", "g_fall_timing")},
        "bclock_v1_vae_rt": {k: bc_r.get(k) for k in ("flag", "n_impacts", "impact_t_frames", "flight_frames", "e_timing_ratios", "e_timing_median", "e_timing_first", "g_curv_first_ok", "g_fall_timing")},
        "track_y_orig": [None if np.isnan(v) else round(float(v), 2) for v in y_orig],
        "track_y_vae_rt": [None if np.isnan(v) else round(float(v), 2) for v in y_rt],
    }


def make_qc_plot(results, rt_dir, out_jpg):
    W, H = 1600, 920
    canvas = np.full((H, W, 3), 250, dtype=np.uint8)
    cv2.putText(canvas, "Task 51: Cosmos3-Nano Wan2.2 VAE (16x4x) Round-Trip on Real GAUGE Bouncing Ball Clips (832x480 @ 25fps)",
                (25, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (20, 20, 20), 2, cv2.LINE_AA)

    full_keys = [f"real_ball_{i}_full_129f" for i in range(1, 5)]
    for idx, key in enumerate(full_keys):
        if key not in results:
            continue
        r = results[key]
        col = idx % 2
        row = idx // 2
        x0 = 40 + col * 780
        y0 = 55 + row * 280
        pw, ph = 720, 230
        cv2.rectangle(canvas, (x0, y0), (x0 + pw, y0 + ph), (255, 255, 255), -1)
        cv2.rectangle(canvas, (x0, y0), (x0 + pw, y0 + ph), (180, 180, 180), 1)

        yo = np.array([np.nan if v is None else v for v in r["track_y_orig"]])
        yr = np.array([np.nan if v is None else v for v in r["track_y_vae_rt"]])
        bo = r["bounce_orig"]
        br = r["bounce_vae_rt"]
        psnr = r.get("vae_meta", {}).get("psnr_db", 0.0)
        ff_o = r["firstfall_v1_orig"]["g"] if r.get("firstfall_v1_orig") and r["firstfall_v1_orig"].get("g") else 0.0
        ff_r = r["firstfall_v1_vae_rt"]["g"] if r.get("firstfall_v1_vae_rt") and r["firstfall_v1_vae_rt"].get("g") else 0.0
        imp_mae = r["impact_timing_mae_frames"] if r["impact_timing_mae_frames"] is not None else 0.0

        title = (f"Ball {idx+1} (129f->33 latents): PSNR={psnr:.2f}dB, y_RMSD={r['y_rmsd_active_px']:.2f}px ({r['y_rmsd_active_mm']:.1f}mm), "
                 f"imp_MAE={imp_mae:.2f}f")
        cv2.putText(canvas, title, (x0 + 8, y0 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1, cv2.LINE_AA)
        sub = (f"ORIG: imps={bo['impacts_int']} e_T={bo['e_T_loglin']} (mean={bo['e_T_mean']}), e_h={bo['e_h_mean']}, g={ff_o:.2f} | "
               f"VAE: imps={br['impacts_int']} e_T={br['e_T_loglin']} (mean={br['e_T_mean']}), e_h={br['e_h_mean']}, g={ff_r:.2f}")
        cv2.putText(canvas, sub, (x0 + 8, y0 + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.39, (40, 60, 120), 1, cv2.LINE_AA)

        f_min, f_max = 20, 95
        y_min_px, y_max_px = 85.0, 345.0

        def to_pt(f_idx, y_val):
            px = int(x0 + 35 + (f_idx - f_min) / (f_max - f_min) * (pw - 50))
            py = int(y0 + 48 + (y_val - y_min_px) / (y_max_px - y_min_px) * (ph - 65))
            return px, py

        for y_grid in [100, 200, 300, 330]:
            _, gy = to_pt(f_min, y_grid)
            cv2.line(canvas, (x0 + 35, gy), (x0 + pw - 15, gy), (230, 230, 230), 1)
            cv2.putText(canvas, f"{y_grid}", (x0 + 4, gy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)

        pts_o = [to_pt(t, yo[t]) for t in range(f_min, min(f_max, len(yo))) if np.isfinite(yo[t])]
        for k in range(len(pts_o) - 1):
            cv2.line(canvas, pts_o[k], pts_o[k + 1], (200, 70, 20), 2, cv2.LINE_AA)

        pts_r = [to_pt(t, yr[t]) for t in range(f_min, min(f_max, len(yr))) if np.isfinite(yr[t])]
        for k in range(len(pts_r) - 1):
            cv2.line(canvas, pts_r[k], pts_r[k + 1], (20, 110, 230), 1, cv2.LINE_AA)
        for pt in pts_r[::2]:
            cv2.circle(canvas, pt, 2, (20, 110, 230), -1)

        for imp_f in bo["impacts_int"]:
            if f_min <= imp_f < f_max and np.isfinite(yo[imp_f]):
                ix, iy = to_pt(imp_f, yo[imp_f])
                cv2.circle(canvas, (ix, iy), 4, (180, 40, 20), 1, cv2.LINE_AA)
                cv2.putText(canvas, f"f{imp_f}", (ix - 10, iy + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (140, 30, 20), 1)

    fo, _ = load_frames_bgr(os.path.join(rt_dir, "real_ball_1_full_129f_orig.mp4"))
    fr, _ = load_frames_bgr(os.path.join(rt_dir, "real_ball_1_full_129f_vae_rt.mp4"))
    key_frames = [(34, "f34 Fall"), (37, "f37 Imp1"), (43, "f43 Apex1"), (49, "f49 Imp2"),
                  (52, "f52 Apex2"), (55, "f55 Imp3"), (58, "f58 Apex3"), (61, "f61 Imp4"), (80, "f80 Rest")]
    y_strip = 625
    cv2.putText(canvas, "Ball 1 Corridor Crops (x=250..360, y=170..355) — Top: Original | Bottom: Wan2.2 VAE Round-Trip (4x temporal compression)",
                (40, y_strip - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (30, 30, 30), 1, cv2.LINE_AA)
    for k, (f_idx, label) in enumerate(key_frames):
        cx0 = 40 + k * 170
        crop_o = fo[f_idx][170:355, 250:360]
        crop_r = fr[f_idx][170:355, 250:360]
        crop_o_res = cv2.resize(crop_o, (155, 125))
        crop_r_res = cv2.resize(crop_r, (155, 125))
        canvas[y_strip:y_strip + 125, cx0:cx0 + 155] = crop_o_res
        canvas[y_strip + 132:y_strip + 257, cx0:cx0 + 155] = crop_r_res
        cv2.putText(canvas, f"ORIG {label}", (cx0 + 4, y_strip + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"VAE  {label}", (cx0 + 4, y_strip + 146), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 235, 255), 1, cv2.LINE_AA)

    cv2.imwrite(out_jpg, canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print("Wrote QC plot:", out_jpg)


def main():
    rt_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/nail/swarm-work/agy-1/vae_rt_gb10"
    meta_path = os.path.join(rt_dir, "vae_rt_meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}

    results = {}
    for f in sorted(os.listdir(rt_dir)):
        if not f.endswith("_orig.mp4"):
            continue
        base_id = f[:-9]
        orig_p = os.path.join(rt_dir, f"{base_id}_orig.mp4")
        rt_p = os.path.join(rt_dir, f"{base_id}_vae_rt.mp4")
        if not os.path.exists(rt_p):
            continue
        is_full = "full" in base_id
        res = evaluate_pair(base_id, orig_p, rt_p, is_full=is_full)
        if base_id in meta:
            res["vae_meta"] = meta[base_id]
        results[base_id] = res
        bo = res["bounce_orig"]
        br = res["bounce_vae_rt"]
        print(f"[{base_id:32s}] PSNR={res.get('vae_meta',{}).get('psnr_db')}dB (corr={res['corridor_psnr_db']}dB), "
              f"y_RMSD_act={res['y_rmsd_active_px']}px ({res['y_rmsd_active_mm']}mm), imp_MAE={res['impact_timing_mae_frames']}f | "
              f"ORIG: n_imp={bo['n_impacts']}, imps={bo['impacts_int']}, e_T_log={bo['e_T_loglin']} (mean={bo['e_T_mean']}), e_h={bo['e_h_mean']}, rest={bo['at_rest_by_end']} | "
              f"VAE_RT: n_imp={br['n_impacts']}, imps={br['impacts_int']}, e_T_log={br['e_T_loglin']} (mean={br['e_T_mean']}), e_h={br['e_h_mean']}, rest={br['at_rest_by_end']}")

    out_json = os.path.join(OUT_DIR, "task51_vae_roundtrip_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print("Wrote", out_json)

    make_qc_plot(results, rt_dir, os.path.join(OUT_DIR, "qc_task51_vae_roundtrip.jpg"))


if __name__ == "__main__":
    main()
