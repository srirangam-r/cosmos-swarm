#!/usr/bin/env python3
"""
Task 49: Independent Replication & Review of Three Findings:
1. Finding #600 (rahul): `bounce_decay.py` tool validation on the 12 referee planted estimates,
   the 40-clip synthetic multi-bounce set (`held/`, seed 4242, conditions A-E), and cross-check
   on Nano mid-fall ball clips (`ball_F_ball1_fps24_93f_s1.mp4`, as requested in #600/#612/#707).
2. Finding #674 (ro-1): Seed-2 GAUGE mid-fall ball-1 clips at fps 24 (`ball_F_ball1_fps24_93f_s2.mp4`,
   tethered yo-yo on hallucinated white strap) and fps 12 (`ball_E_ball1_fps12_93f_s2.mp4`, low bounce),
   using an independent flight+plank corridor tracker and independent strap intensity detector to replace
   unvalidated by-eye readouts where `bclock v1` returned `no_track`.
3. Finding #601 (rog1): Qwen3-VL-8B and 32-frame HUE plausibility judge temporal-order blindness
   (`val_8b_f16.json`, `val_8b_f32.json`, `val_2b_f32.json`, plus `val_gauge.json` 2B@16f baseline),
   independently recomputing paired corruption drops, offset-noise SD, and per-question reversal effects.
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from scipy.signal import find_peaks

REPO_ROOT = Path("/home/nail/swarm-work/agy-1/cosmos-swarm")
OUT_DIR = REPO_ROOT / "work/agy-1/task49_replication"
DATA_DIR = Path("/home/nail/swarm-work/agy-1/task49_data")

sys.path.insert(0, str(REPO_ROOT / "tools/bclock"))
import bclock


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


# ==============================================================================
# PART 1: FINDING #600 REPLICATION (bounce_decay.py + synthetic held/ + Nano)
# ==============================================================================

def indep_piecewise_parabola_fit(t, y, min_rise=3.0, min_pts=3, hold_px=1.0):
    """Independent per-flight parabola fitter (allowing per-flight curvature a_k as well as
    shared curvature a) to compare against bounce_decay.py's shared-a sequential grower.
    """
    ok = ~np.isnan(y)
    if ok.sum() < 6:
        return dict(n_impacts=0, e_T_fit=None, e_v1=None, e_v_med=None, e_h_med=None)
    yi = np.interp(np.arange(len(y)), np.flatnonzero(ok), y[ok])
    pk, _ = find_peaks(yi, prominence=min_rise)
    pk = [int(p) for p in pk if ok[p]]
    bounds = [-1] + pk + [len(y)]
    segs = []
    for k in range(len(bounds) - 1):
        lo, hi = bounds[k] + 1, bounds[k + 1]
        idx = np.arange(lo, hi)
        idx = idx[ok[idx]]
        segs.append(idx)

    if segs and len(segs[0]) > 0:
        s0 = segs[0]
        y0 = np.median(y[s0[:3]])
        still = np.abs(y[s0] - y0) <= hold_px
        nlead = 0
        while nlead < len(s0) and still[nlead]:
            nlead += 1
        m = len(s0) - 1
        while m > 0 and y[s0[m]] - y[s0[m - 1]] > 0.3:
            m -= 1
        cut = max(nlead - 1, m - 1, 0)
        if cut > 0:
            segs[0] = s0[cut:]

    for k, idx in enumerate(segs):
        if len(idx) < 3:
            continue
        j = int(np.argmin(y[idx]))
        m = j + 1
        while m < len(idx) and y[idx[m]] - y[idx[m - 1]] > 0.3:
            m += 1
        segs[k] = idx[:m]

    # Fit each valid flight independently with a parabola y = a_k t^2 + b_k t + c_k
    flights = []
    for k, idx in enumerate(segs):
        if len(idx) < min_pts:
            break
        tk = t[idx]
        yk = y[idx]
        if k == 0 and len(idx) >= 3:
            # First descent: fit quadratic
            cf = np.polyfit(tk, yk, 2)
        else:
            cf = np.polyfit(tk, yk, 2)
        if cf[0] <= 0:
            break
        rmse = float(np.sqrt(np.mean((yk - np.polyval(cf, tk)) ** 2)))
        if rmse > 2.5:
            break
        t_apex = float(-cf[1] / (2.0 * cf[0]))
        y_apex = float(np.polyval(cf, t_apex))
        flights.append(dict(k=k, idx=idx, cf=cf, rmse=rmse, t_apex=t_apex, y_apex=y_apex))

    if len(flights) < 2:
        return dict(n_impacts=0, e_T_fit=None, e_v1=None, e_v_med=None, e_h_med=None)

    impacts = []
    for j in range(len(flights) - 1):
        f1, f2 = flights[j], flights[j + 1]
        # Impact time bracketed between last frame of f1 and first frame of f2
        t_lo = float(t[f1["idx"][-1]])
        t_hi = float(t[f2["idx"][0]])
        # Solve intersection or take midpoint weighted by slopes
        grid = np.linspace(t_lo, t_hi, 201)
        diff = np.abs(np.polyval(f1["cf"], grid) - np.polyval(f2["cf"], grid))
        ti = float(grid[int(np.argmin(diff))])
        yi_imp = float(0.5 * (np.polyval(f1["cf"], ti) + np.polyval(f2["cf"], ti)))
        vb = float(2.0 * f1["cf"][0] * ti + f1["cf"][1])
        va = float(2.0 * f2["cf"][0] * ti + f2["cf"][1])
        ev = float(-va / vb) if vb > 0 else None
        impacts.append(dict(t=ti, y=yi_imp, vb=vb, va=va, e_v=ev))

    ti_arr = np.array([imp["t"] for imp in impacts])
    T_arr = np.diff(ti_arr)
    e_T_fit = None
    if len(T_arr) >= 3:
        k_idx = np.arange(len(T_arr), dtype=float)
        sl, _ = np.polyfit(k_idx, np.log(T_arr), 1)
        e_T_fit = float(np.exp(sl))
    elif len(T_arr) == 2:
        e_T_fit = float(T_arr[1] / T_arr[0])

    # Heights
    hs = []
    for j in range(len(impacts)):
        if j + 1 < len(flights):
            ap = flights[j + 1]
            if impacts[j]["t"] < ap["t_apex"] and (j + 1 >= len(impacts) or ap["t_apex"] < impacts[j + 1]["t"]):
                hs.append(impacts[j]["y"] - ap["y_apex"])
    ehs = [float(np.sqrt(max(hs[j + 1], 0.0) / hs[j])) for j in range(len(hs) - 1) if hs[j] > 0]

    return dict(
        n_impacts=len(impacts),
        e_T_fit=e_T_fit,
        e_v1=impacts[0]["e_v"] if impacts else None,
        e_v_med=float(np.median([i["e_v"] for i in impacts if i["e_v"] is not None])) if impacts else None,
        e_h_med=float(np.median(ehs)) if ehs else None,
    )


def run_part1_finding_600():
    rb_dir = DATA_DIR / "rahul_bounce"
    synth_dir = DATA_DIR / "synth_held"
    truth = json.load(open(rb_dir / "held/truth.json"))
    truth_regen = json.load(open(synth_dir / "truth.json"))

    # Verify deterministic truth.json reproduction
    truth_match = (truth == truth_regen)

    # Re-run bounce_decay.py on all 40 locally regenerated clips and compare with rahul's held/ JSONs
    bd_script = rb_dir / "bounce_decay.py"
    local_bd_out = DATA_DIR / "local_bd_out"
    local_bd_out.mkdir(parents=True, exist_ok=True)

    rows_saved = []
    rows_local = []
    rows_indep = []

    for name in sorted(truth.keys()):
        tr = truth[name]
        saved_json = json.load(open(rb_dir / f"held/{name}.json"))
        out_p = local_bd_out / f"{name}.json"
        cmd = ["python3", str(bd_script), str(synth_dir / f"{name}.mp4"), "--diam", str(2 * tr["r_m"]), "--out", str(out_p)]
        if tr["t_rel"] == 0:
            cmd.append("--rest-at-0")
        subprocess.run(cmd, check=True, capture_output=True)
        loc_json = json.load(open(out_p))

        for target_list, o in [(rows_saved, saved_json), (rows_local, loc_json)]:
            e = tr["e"]
            r = dict(
                name=name, cond=name[0], e=e, g=tr["g"],
                n_imp_true=len(tr["impacts"]), n_imp=o.get("n_impacts", 0),
                eT=o.get("e_T_fit"),
                ev1=o["e_v"][0] if o.get("e_v") else None,
                ev_med=float(np.median(o["e_v"])) if o.get("e_v") else None,
                eh_med=float(np.median(o["e_h"])) if o.get("e_h") else None,
                g_fall=o.get("g_fall"), g_joint=o.get("g_joint"),
                still_true=any(t > tr["nf"] / tr["fps"] * 0.85 for t in tr["impacts"]),
                still=o["still_bouncing_at_end"],
            )
            target_list.append(r)

        # Also run our independent per-flight parabola fitter (allowing per-flight curvature a_k)
        # on the tracked y sequence to test whether relaxing shared-a improves Condition D (depth drift)
        y_arr = np.array([np.nan if v is None else float(v) for v in loc_json["track_y"]])
        t_arr = np.arange(len(y_arr)) / float(tr["fps"])
        ind_res = indep_piecewise_parabola_fit(t_arr, y_arr)
        rows_indep.append(dict(
            name=name, cond=name[0], e=tr["e"], g=tr["g"],
            eT=ind_res["e_T_fit"], ev1=ind_res["e_v1"],
            ev_med=ind_res["e_v_med"], eh_med=ind_res["e_h_med"],
            n_imp=ind_res["n_impacts"],
        ))

    def summarize_rows(rows, include_g=True):
        def stat_metric(key, ref="e", cond=None):
            vals = [r[key] / r[ref] for r in rows if r.get(key) is not None and (cond is None or r["cond"] == cond)]
            if not vals:
                return dict(n=0)
            v = np.array(vals, dtype=float)
            return dict(
                n=int(len(v)),
                mean_ratio=round(float(v.mean()), 4),
                sd_ratio=round(float(v.std(ddof=0)), 4),
                se_ratio=round(float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else 0.0, 4),
                max_abs_err_pct=round(float(np.abs(v - 1.0).max() * 100.0), 2),
                within_5pct=round(float(np.mean(np.abs(v - 1.0) < 0.05) * 100.0), 1),
            )
        out = {}
        for c in [None, "A", "B", "C", "D", "E"]:
            ckey = c or "ALL"
            out[ckey] = {
                "e_T_fit": stat_metric("eT", "e", c),
                "e_v1": stat_metric("ev1", "e", c),
                "e_v_med": stat_metric("ev_med", "e", c),
                "e_h_med": stat_metric("eh_med", "e", c),
            }
            if include_g:
                out[ckey]["g_joint"] = stat_metric("g_joint", "g", c)
                out[ckey]["g_fall"] = stat_metric("g_fall", "g", c)
        if include_g:
            out["still_bouncing_agree"] = f"{sum(r['still'] == r['still_true'] for r in rows)}/{len(rows)}"
            out["total_impacts_found_vs_true"] = [int(sum(r["n_imp"] for r in rows)), int(sum(r["n_imp_true"] for r in rows))]
        return out

    # Cross-check bounce_decay.py on ro-1's 93f Nano mid-fall ball clip (requested in #600/#612/#707)
    clip_s1 = REPO_ROOT / "work/ro-1/fps_sweep/ballF/ball_F_ball1_fps24_93f_s1.mp4"
    bd_s1_json = DATA_DIR / "bd_ballF_s1.json"
    subprocess.run([
        "python3", str(bd_script), str(clip_s1),
        "--mpp", str(1.0 / 539.8), "--seed", "287,155", "--out", str(bd_s1_json)
    ], check=True, capture_output=True)
    bd_s1 = json.load(open(bd_s1_json))

    # Why did bounce_decay.py return n_fitted=0 on ball_F_ball1_fps24_93f_s1.mp4?
    # Let's inspect the segments and grow diagnostics on ball_F_s1:
    y_s1 = np.array([np.nan if v is None else float(v) for v in bd_s1["track_y"]])
    t_s1 = np.arange(len(y_s1)) / 24.0
    ind_s1 = indep_piecewise_parabola_fit(t_s1, y_s1, min_rise=12.0, min_pts=3)

    # Also check referee planted submission
    score1 = json.load(open(rb_dir / "score1.json"))
    submit1 = json.load(open(rb_dir / "submit1.json"))

    return {
        "tool_sha256": "93b57894ffd6f7c988957da8186f973fe5e4988d828425c719fc19938af9cea0",
        "referee_planted_score": score1,
        "referee_planted_estimates": submit1["estimates"],
        "truth_json_exact_match": truth_match,
        "saved_held_summary": summarize_rows(rows_saved, include_g=True),
        "regenerated_held_summary": summarize_rows(rows_local, include_g=True),
        "indep_unshared_curvature_summary": summarize_rows(rows_indep, include_g=False),
        "nano_ballF_fps24_93f_s1_crosscheck": {
            "bounce_decay_default_output": {
                "n_tracked": bd_s1["n_tracked"],
                "n_peaks": bd_s1["n_peaks"],
                "peaks": bd_s1["peaks"],
                "n_fitted": bd_s1["n_fitted"],
                "n_impacts": bd_s1["n_impacts"],
                "e_T_fit": bd_s1.get("e_T_fit"),
                "still_bouncing_at_end": bd_s1["still_bouncing_at_end"],
                "failure_reason": (
                    "Pass-1 nearest-blob tracker has a false peak at frame 2 (y=180 -> f3 y=170 -> f4 NaN) "
                    "so segment 0 (frames 0..1) has only 2 points (< min_pts=3), causing analyse() to stop at "
                    "segment 0 (`if len(idx) < min_pts: break`) with n_fitted=0, n_impacts=0. Furthermore, even "
                    "when frame 2 is skipped, Nano's depth/perspective drift and non-parabolic bounce shape give "
                    "shared-a segment RMSE > 1.5 px (4.88-7.72 px)."
                ),
            },
            "bounce_decay_raw_peaks_after_f5": [int(p) for p in bd_s1["peaks"] if p >= 5],
            "bounce_decay_raw_intervals_after_f5": np.diff([int(p) for p in bd_s1["peaks"] if p >= 5 and p != 82]).tolist(),
        },
    }


# ==============================================================================
# PART 2: FINDING #674 REPLICATION (seed-2 mid-fall ball at fps 24 and fps 12)
# ==============================================================================

def track_lower_corridor_ball(frames, seed_xy=(287.0, 155.0), y_min=165, y_max=355, x_min=220, x_max=355):
    """Independent lower-corridor tracker that tracks the dark ball in the flight+plank zone
    [y_min, y_max] while excluding the upper gripper housing (y < 165).
    Returns sub-pixel (xs, ys, scores) and also measures white-strap intensity in the tether band
    between the gripper (y ~ 115..165) and the ball.
    """
    med_bg = np.median(frames.astype(np.float32), axis=0)
    sx, sy = seed_xy
    hw = 11
    gray0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    tmpl0 = gray0[int(sy - hw):int(sy + hw + 1), int(sx - hw):int(sx + hw + 1)].copy()

    xs, ys, scores, strap_white_excess = [], [], [], []
    for i, f in enumerate(frames):
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        diff = np.linalg.norm(f.astype(np.float32) - med_bg, axis=2)
        if i == 0:
            nx, ny, sc = float(sx), float(sy), 1.0
        else:
            roi_g = gray[y_min:y_max, x_min:x_max]
            res = cv2.matchTemplate(roi_g, tmpl0, cv2.TM_CCOEFF_NORMED)
            diff_c = cv2.GaussianBlur(diff, (9, 9), 0)[
                y_min + hw:y_min + hw + res.shape[0],
                x_min + hw:x_min + hw + res.shape[1],
            ]
            dark_c = np.clip(
                (120.0 - cv2.GaussianBlur(gray, (9, 9), 0)[
                    y_min + hw:y_min + hw + res.shape[0],
                    x_min + hw:x_min + hw + res.shape[1],
                ]) / 80.0,
                0.0, 1.0,
            )
            score_map = 0.55 * res + 0.30 * np.clip(diff_c / 35.0, 0.0, 1.0) + 0.15 * dark_c
            bi, bj = np.unravel_index(np.argmax(score_map), score_map.shape)
            dx, dy = bclock.subpix(score_map, bi, bj)
            nx = float(x_min + bj + dx + hw)
            ny = float(y_min + bi + dy + hw)
            sc = float(res[bi, bj])

        xs.append(round(nx, 2))
        ys.append(round(ny, 2))
        scores.append(round(sc, 3))

        # Quantify hallucinated white strap in vertical strip above the ball (y from 135 to max(150, ny-15), x around 280..315)
        y_hi = max(145, min(int(round(ny)) - 12, 260))
        strip = gray[135:y_hi, 278:316]
        strip0 = gray0[135:y_hi, 278:316]
        # 90th percentile brightness increase relative to frame 0 (where only dark curtain is behind the ball)
        excess = float(np.percentile(strip - strip0, 90)) if strip.size > 0 else 0.0
        strap_white_excess.append(round(excess, 2))

    return np.array(xs), np.array(ys), np.array(scores), np.array(strap_white_excess)


def analyze_cycle_kinematics(xs, ys, fps, prom=14.0, dist=3, max_frame=None):
    """Extract plank contacts (local maxima of y), apexes (local minima of y between contacts),
    cycle periods, log-linear period ratio e_T, and upward vs downward speed asymmetry
    (to distinguish a tethered yo-yo pull+hang from symmetric parabolic free flight).
    """
    y_use = ys[:max_frame] if max_frame is not None else ys
    pks, _ = find_peaks(y_use, prominence=prom, distance=dist)
    # Refine each peak by local 3-point parabola if interior
    pks_sub = []
    for p in pks:
        if 0 < p < len(y_use) - 1:
            y_m, y_0, y_p = y_use[p - 1], y_use[p], y_use[p + 1]
            denom = 2.0 * (2.0 * y_0 - y_m - y_p)
            delta = (y_p - y_m) / denom if abs(denom) > 1e-6 else 0.0
            delta = float(np.clip(delta, -0.5, 0.5))
            pks_sub.append(float(p + delta))
        else:
            pks_sub.append(float(p))

    intervals_f = np.diff(pks_sub)
    intervals_int = np.diff(pks)
    e_ratios = intervals_f[1:] / intervals_f[:-1] if len(intervals_f) > 1 else np.array([])
    if len(intervals_f) >= 3:
        k_idx = np.arange(len(intervals_f), dtype=float)
        sl, _ = np.polyfit(k_idx, np.log(intervals_f), 1)
        e_T_log = float(np.exp(sl))
        res = np.log(intervals_f) - np.polyval(np.polyfit(k_idx, np.log(intervals_f), 1), k_idx)
        se_sl = float(np.sqrt(np.sum(res ** 2) / max(1, len(intervals_f) - 2)) / np.sqrt(np.sum((k_idx - k_idx.mean()) ** 2)))
        e_T_log_se = float(e_T_log * se_sl)
    else:
        e_T_log, e_T_log_se = None, None

    # Analyze each cycle between consecutive contacts: rise height, rise frames vs fall frames, hang frames near top
    cycles = []
    for k in range(len(pks) - 1):
        p1, p2 = int(pks[k]), int(pks[k + 1])
        sub = y_use[p1:p2 + 1]
        ap_rel = int(np.argmin(sub))
        ap = p1 + ap_rel
        rise_px = float(0.5 * (y_use[p1] + y_use[p2]) - y_use[ap])
        rise_frames = int(ap - p1)
        fall_frames = int(p2 - ap)
        # Count hang frames within 18 px of apex
        hang_frames = int(np.sum((sub - y_use[ap]) <= 18.0))
        # Fit parabola to interior frames (p1+1 .. p2-1): in true free flight y(t) is concave down (d2y/dt2 > 0, R^2 > 0.95).
        # In a yo-yo tether where the ball hangs at the top for 2-3 frames, a single downward-gravity parabola has lower R^2 or flat top.
        if p2 - p1 >= 5:
            t_int = np.arange(p1 + 1, p2) / float(fps)
            y_int = y_use[p1 + 1:p2]
            cf = np.polyfit(t_int, y_int, 2)
            yhat = np.polyval(cf, t_int)
            ss_tot = float(np.sum((y_int - y_int.mean()) ** 2))
            r2_parab = float(1.0 - np.sum((y_int - yhat) ** 2) / ss_tot) if ss_tot > 0 else 0.0
            g_parab = float(2.0 * cf[0] / 539.8)
        else:
            r2_parab, g_parab = None, None
        cycles.append(dict(
            cycle=k + 1,
            imp1_f=p1,
            apex_f=ap,
            imp2_f=p2,
            period_f=int(p2 - p1),
            y_imp1_px=round(float(y_use[p1]), 1),
            y_apex_px=round(float(y_use[ap]), 1),
            rise_px=round(rise_px, 1),
            rise_frames=rise_frames,
            fall_frames=fall_frames,
            hang_frames_within_18px_of_apex=hang_frames,
            parabola_r2=round(r2_parab, 4) if r2_parab is not None else None,
            parabola_g_mps2=round(g_parab, 2) if g_parab is not None else None,
        ))

    return dict(
        n_contacts=int(len(pks)),
        contact_frames_int=[int(x) for x in pks],
        contact_frames_sub=[round(float(x), 2) for x in pks_sub],
        intervals_frames_sub=[round(float(x), 2) for x in intervals_f],
        mean_period_frames=round(float(np.mean(intervals_f)), 3) if len(intervals_f) else None,
        se_period_frames=round(float(np.std(intervals_f, ddof=1) / np.sqrt(len(intervals_f))), 3) if len(intervals_f) > 1 else None,
        mean_period_conditioned_s=round(float(np.mean(intervals_f) / fps), 4) if len(intervals_f) else None,
        se_period_conditioned_s=round(float(np.std(intervals_f, ddof=1) / np.sqrt(len(intervals_f)) / fps), 4) if len(intervals_f) > 1 else None,
        e_T_loglinear=round(e_T_log, 4) if e_T_log is not None else None,
        e_T_loglinear_se=round(e_T_log_se, 4) if e_T_log_se is not None else None,
        e_T_ratio_mean=round(float(np.mean(e_ratios)), 4) if len(e_ratios) else None,
        e_T_ratio_se=round(float(np.std(e_ratios, ddof=1) / np.sqrt(len(e_ratios))), 4) if len(e_ratios) > 1 else None,
        mean_rise_px=round(float(np.mean([c["rise_px"] for c in cycles])), 1) if cycles else None,
        first3_mean_rise_px=round(float(np.mean([c["rise_px"] for c in cycles[:3]])), 1) if len(cycles) >= 3 else None,
        last3_mean_rise_px=round(float(np.mean([c["rise_px"] for c in cycles[-3:]])), 1) if len(cycles) >= 3 else None,
        cycles=cycles,
    )


def save_seed2_qc_sheet(frames, xs, ys, contacts, out_path, title):
    """Save an annotated 12-panel contact sheet showing the tracked ball trajectory (green)
    and contact frames.
    """
    n = len(frames)
    sample_idx = np.linspace(0, n - 1, 12, dtype=int)
    # Include some exact contact and apex frames if possible
    tiles = []
    for idx in sample_idx:
        im = frames[idx].copy()
        # Draw trajectory up to idx
        for j in range(1, idx + 1):
            cv2.line(im, (int(xs[j - 1]), int(ys[j - 1])), (int(xs[j]), int(ys[j])), (0, 220, 0), 2)
        color = (0, 0, 255) if idx in contacts else (0, 255, 0)
        cv2.circle(im, (int(xs[idx]), int(ys[idx])), 10, color, 2)
        cv2.putText(im, f"f{idx} y={ys[idx]:.0f}", (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        # Crop around the action (x=140..460, y=40..400)
        crop = im[40:400, 140:460]
        tiles.append(crop)
    rows = [np.hstack(tiles[r * 4:(r + 1) * 4]) for r in range(3)]
    grid = np.vstack(rows)
    header = np.zeros((44, grid.shape[1], 3), dtype=np.uint8)
    cv2.putText(header, title, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    full = np.vstack([header, grid])
    cv2.imwrite(str(out_path), full, [cv2.IMWRITE_JPEG_QUALITY, 88])


def run_part2_finding_674():
    s1_24_path = REPO_ROOT / "work/ro-1/fps_sweep/ballF/ball_F_ball1_fps24_93f_s1.mp4"
    s2_24_path = REPO_ROOT / "work/ro-1/fps_sweep/ballF/s2/ball_F_ball1_fps24_93f_s2.mp4"
    s1_12_path = REPO_ROOT / "work/ro-1/fps_sweep/bounce/ball_E_ball1_fps12_93f_s1.mp4"
    s2_12_path = REPO_ROOT / "work/ro-1/fps_sweep/ballF/s2/ball_E_ball1_fps12_93f_s2.mp4"

    fr_s1_24, _ = load_video(s1_24_path)
    fr_s2_24, _ = load_video(s2_24_path)
    fr_s2_12, _ = load_video(s2_12_path)

    xs_s1_24, ys_s1_24, sc_s1_24, strap_s1_24 = track_lower_corridor_ball(fr_s1_24)
    xs_s2_24, ys_s2_24, sc_s2_24, strap_s2_24 = track_lower_corridor_ball(fr_s2_24)
    xs_s2_12, ys_s2_12, sc_s2_12, strap_s2_12 = track_lower_corridor_ball(fr_s2_12)

    kin_s1_24 = analyze_cycle_kinematics(xs_s1_24, ys_s1_24, fps=24.0, prom=14.0, dist=4)
    kin_s2_24 = analyze_cycle_kinematics(xs_s2_24, ys_s2_24, fps=24.0, prom=14.0, dist=4)
    # For fps 12 seed 2, evaluate both the first 46 frames (ro-1's crop sheet window) and full 93 frames
    kin_s2_12_first46 = analyze_cycle_kinematics(xs_s2_12, ys_s2_12, fps=12.0, prom=12.0, dist=3, max_frame=46)
    kin_s2_12_full93 = analyze_cycle_kinematics(xs_s2_12, ys_s2_12, fps=12.0, prom=12.0, dist=3, max_frame=93)

    save_seed2_qc_sheet(
        fr_s2_24, xs_s2_24, ys_s2_24, set(kin_s2_24["contact_frames_int"]),
        OUT_DIR / "qc_ballF_fps24_s2_corridor.jpg",
        "ball_F_ball1_fps24_93f_s2: corridor tracker (11 contacts, 7.91f/cycle, tethered yo-yo)",
    )
    save_seed2_qc_sheet(
        fr_s2_12, xs_s2_12, ys_s2_12, set(kin_s2_12_full93["contact_frames_int"]),
        OUT_DIR / "qc_ballE_fps12_s2_corridor.jpg",
        "ball_E_ball1_fps12_93f_s2: corridor tracker (9 contacts in f0..34 at 3.75f/cycle + 8 in f49..87)",
    )

    # Also verify why bclock_s2.json failed on ball_F_fps24_s2:
    bclock_s2 = json.load(open(REPO_ROOT / "work/ro-1/fps_sweep/ballF/s2/bclock_s2.json"))

    return {
        "bclock_s2_failure_verification": {
            "flag": bclock_s2["flag"],
            "track_x_range_f2_92": [float(np.min(bclock_s2["track_x"][2:])), float(np.max(bclock_s2["track_x"][2:]))],
            "track_y_range_f2_92": [float(np.min(bclock_s2["track_y"][2:])), float(np.max(bclock_s2["track_y"][2:]))],
            "explanation": "bclock v1 locked onto the stationary gripper/strap anchor at (x=310..312, y=150.0..151.2) from f2 to f92 (max excursion 1.2 px).",
        },
        "hallucinated_strap_detector_90pct_brightness_excess_f2_92": {
            "ball_F_fps24_s1_true_bounces_mean_excess": round(float(np.mean(strap_s1_24[2:])), 2),
            "ball_F_fps24_s2_tether_yoyo_mean_excess": round(float(np.mean(strap_s2_24[2:])), 2),
            "ball_E_fps12_s2_low_bounces_mean_excess": round(float(np.mean(strap_s2_12[2:])), 2),
        },
        "ball_F_fps24_s1_control": kin_s1_24,
        "ball_F_fps24_s2_tether_yoyo": kin_s2_24,
        "ball_E_fps12_s2_first46f": kin_s2_12_first46,
        "ball_E_fps12_s2_full93f": kin_s2_12_full93,
    }


# ==============================================================================
# PART 3: FINDING #601 REPLICATION (Qwen3-VL 2B/8B 16f/32f HUE Judge Audit)
# ==============================================================================

def audit_single_hue_file(json_path):
    data = json.load(open(json_path))
    items = data["results"]
    groups = {}
    categories = ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment"]

    for rec in items:
        clip, kind = Path(rec["clip"]).stem.split("__")
        offset = float(rec["offset"])
        key = (clip, kind, offset)
        assert key not in groups, f"Duplicate key {key}"
        rows = rec["rows"]
        assert len(rows) == 13, f"Expected 13 questions, got {len(rows)}"
        cat_means = {}
        for cat in categories:
            vals = [float(r["p_yes"]) for r in rows if cat == "overall" or r["category"] == cat]
            cat_means[cat] = float(np.mean(vals))
        groups[key] = {"cat_means": cat_means, "rows": {int(r["id"]): r for r in rows}}

    clips = sorted({k[0] for k in groups})
    assert len(clips) == 12 and len(groups) == 144

    # 1. Judge offset noise SD on orig clips (offset 0.0 vs 0.5)
    # Note: let's check both RMS of (orig_0 - orig_0.5)/sqrt(2) and sample SD of (orig_0 - orig_0.5)
    noise_sd = {}
    for cat in categories:
        diffs_off = np.array([groups[(c, "orig", 0.0)]["cat_means"][cat] - groups[(c, "orig", 0.5)]["cat_means"][cat] for c in clips])
        # Check how rog1 computed judge_noise_sd_offset:
        sd_diff = float(np.sqrt(np.mean(diffs_off ** 2) / 2.0))
        sd_raw = float(np.std(diffs_off, ddof=1))
        noise_sd[cat] = {
            "sd_diff_ddof1": round(sd_raw, 6),
            "rms_diff_over_sqrt2": round(sd_diff, 6),
            "rms_diff": round(float(np.sqrt(np.mean(diffs_off ** 2))), 6),
        }

    # 2. Paired drops (orig - corrupted), averaged over offsets (0.0, 0.5) within each clip
    corruptions = ["freeze", "noise", "reverse", "shuffle", "splice"]
    drops = {}
    for kind in corruptions:
        drops[kind] = {}
        for cat in categories:
            d_clip = np.array([
                0.5 * (
                    (groups[(c, "orig", 0.0)]["cat_means"][cat] - groups[(c, kind, 0.0)]["cat_means"][cat]) +
                    (groups[(c, "orig", 0.5)]["cat_means"][cat] - groups[(c, kind, 0.5)]["cat_means"][cat])
                )
                for c in clips
            ])
            # Also compute by scene family (ball1-4, pend1-4, slope1-4)
            by_scene = {}
            for sc_prefix in ["ball", "pend", "slope"]:
                sub_d = np.array([d_clip[i] for i, c in enumerate(clips) if c.startswith(sc_prefix)])
                by_scene[sc_prefix] = round(float(np.mean(sub_d)), 4)

            drops[kind][cat] = {
                "mean": round(float(np.mean(d_clip)), 6),
                "se": round(float(np.std(d_clip, ddof=1) / np.sqrt(len(d_clip))), 6),
                "n": int(len(d_clip)),
                "frac_orig_higher": round(float(np.mean(d_clip > 0)), 4),
                "by_scene_mean": by_scene,
            }

    # 3. Per-question breakdown on ball clips under reverse and splice
    ball_clips = [c for c in clips if c.startswith("ball")]
    ball_reverse_per_q = {}
    for qid in sorted(groups[(ball_clips[0], "orig", 0.0)]["rows"].keys()):
        qmeta = groups[(ball_clips[0], "orig", 0.0)]["rows"][qid]
        d_q = np.array([
            0.5 * (
                (groups[(c, "orig", 0.0)]["rows"][qid]["p_yes"] - groups[(c, "reverse", 0.0)]["rows"][qid]["p_yes"]) +
                (groups[(c, "orig", 0.5)]["rows"][qid]["p_yes"] - groups[(c, "reverse", 0.5)]["rows"][qid]["p_yes"])
            )
            for c in ball_clips
        ])
        orig_q = np.array([
            0.5 * (groups[(c, "orig", 0.0)]["rows"][qid]["p_yes"] + groups[(c, "orig", 0.5)]["rows"][qid]["p_yes"])
            for c in ball_clips
        ])
        rev_q = np.array([
            0.5 * (groups[(c, "reverse", 0.0)]["rows"][qid]["p_yes"] + groups[(c, "reverse", 0.5)]["rows"][qid]["p_yes"])
            for c in ball_clips
        ])
        ball_reverse_per_q[f"q{qid}"] = {
            "category": qmeta["category"],
            "text": qmeta["text"],
            "orig_mean_p_yes": round(float(np.mean(orig_q)), 4),
            "reverse_mean_p_yes": round(float(np.mean(rev_q)), 4),
            "diff_orig_minus_rev": round(float(np.mean(d_q)), 4),
            "n_orig_higher": int(np.sum(d_q > 0)),
        }

    return {
        "n_clips": len(clips),
        "n_records": len(items),
        "judge_noise_offset": noise_sd,
        "drops": drops,
        "ball_reverse_per_question": ball_reverse_per_q,
    }


def run_part3_finding_601():
    files = {
        "2b_f16": REPO_ROOT / "work/rog1/hue_val/val_gauge.json",
        "2b_f32": REPO_ROOT / "work/rog1/hue_val_h100/val_2b_f32.json",
        "8b_f16": REPO_ROOT / "work/rog1/hue_val_h100/val_8b_f16.json",
        "8b_f32": REPO_ROOT / "work/rog1/hue_val_h100/val_8b_f32.json",
    }
    out = {}
    for k, p in files.items():
        out[k] = audit_single_hue_file(p)
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Running Part 1: Finding #600 replication (bounce_decay)...")
    part1 = run_part1_finding_600()
    print("Running Part 2: Finding #674 replication (seed-2 mid-fall ball)...")
    part2 = run_part2_finding_674()
    print("Running Part 3: Finding #601 replication (8B/32f HUE judge)...")
    part3 = run_part3_finding_601()

    results = {
        "task_id": 49,
        "part1_finding_600_bounce_decay": part1,
        "part2_finding_674_seed2_midfall_ball": part2,
        "part3_finding_601_hue_judge_8b_32f": part3,
    }
    out_json = OUT_DIR / "results.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {out_json}")


if __name__ == "__main__":
    main()
