#!/usr/bin/env python3
"""Independent replication and review of Finding #1188 (slope slide-speed ceiling across CFG, fps, 189f, and materials).
Evaluates all 30 GAUGE slope sweep clips with:
1) Independent multi-channel (CIE Lab + Sobel Gradient Magnitude) causal sub-pixel NCC tracker (`indep_lab_grad_ncc`).
2) Independent clean-background CIE Lab color-difference blob tracker (`indep_lab_bgdiff_blob`).
3) Direct audit and comparison against rahul-2's kin3_orig.json.
"""
import os, sys, glob, json
import cv2, numpy as np

SLOPE_CFG = {
    "plastic": dict(box=(570, 28, 660, 115), top=(672.0, 85.0), bot=(190.0, 385.0)),
    "metal":   dict(box=(558, 27, 643, 110), top=(663.0, 77.0), bot=(183.0, 363.0)),
    "wood":    dict(box=(560, 8, 650, 93),   top=(668.0, 57.0), bot=(168.0, 362.0)),
}

def subpix(r, i, j):
    def p(a, b, c):
        den = a - 2 * b + c
        return 0.0 if abs(den) < 1e-9 else 0.5 * (a - c) / den
    dy = p(r[i - 1, j], r[i, j], r[i + 1, j]) if 0 < i < r.shape[0] - 1 else 0.0
    dx = p(r[i, j - 1], r[i, j], r[i, j + 1]) if 0 < j < r.shape[1] - 1 else 0.0
    return dx, dy

def load_video(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(f)
    cap.release()
    return np.array(frames), float(fps)

def track_slope_dual(frames, mat):
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

    # Clean background: frame 0 on lower plank, late median on upper plank
    bg = frames[0].copy()
    late_idx = min(70, len(frames) - 10)
    flate = np.median(frames[late_idx:], axis=0).astype(np.uint8)
    bg[:, 460:] = flate[:, 460:]
    lab_bg = cv2.cvtColor(bg, cv2.COLOR_BGR2Lab).astype(np.float32)

    H, W = frames.shape[1:3]
    yy, xx = np.mgrid[0:H, 0:W]
    rel_x = xx - top[0]
    rel_y = yy - top[1]
    along = rel_x * ax[0] + rel_y * ax[1]
    perp = rel_x * (-ax[1]) + rel_y * ax[0]
    corridor = (along >= -50) & (along <= L_px + 40) & (perp >= -30) & (perp <= 85) & (yy < 365) & (xx >= 130) & (xx <= 700)

    # Templates
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

        # 2. Lab + Gradient Magnitude NCC
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

        # 3. Clean-BG Lab difference blob tracker
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

def summarize_slope_track(s_arr, sc_arr, fps=24.0, mpp=0.50 / 568.0, min_sc=0.55):
    n_total = len(s_arr)
    end = n_total
    for k in range(n_total):
        if np.isnan(s_arr[k]) or s_arr[k] > 0.42 or sc_arr[k] < min_sc:
            end = k
            break
    idx = np.arange(end)
    s = s_arr[:end]
    sc = sc_arr[:end]
    if len(idx) < 6 or (len(s) > 0 and np.max(s) < 0.01):
        return {"moved": False, "n": len(idx), "max_s": round(float(np.max(s)) if len(s) else 0.0, 4)}

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

    # Early 0.5s acceleration
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

def main():
    kin3_orig = json.load(open("kin3_sweep.json"))
    clip_names = sorted(kin3_orig.keys())
    results = {}

    print(f"Starting independent multi-method evaluation on {len(clip_names)} slope clips...")

    for name in clip_names:
        mat = name.split("_")[0]
        mp4_path = f"sweep_clips/{name}.mp4"
        side_path = f"sweep_clips/{name}.json"
        side = json.load(open(side_path))
        fps = float(side["fps"])
        frames, _ = load_video(mp4_path)

        tr = track_slope_dual(frames, mat)

        sum_lg = summarize_slope_track(tr["s_lg"], tr["sc_lg"], fps=fps, mpp=tr["mpp"], min_sc=0.55)
        sum_bgr = summarize_slope_track(tr["s_bgr"], tr["sc_bgr"], fps=fps, mpp=tr["mpp"], min_sc=0.58)

        # Blob summary using valid blob frames up to last_tracked
        end_blob = sum_lg["last_tracked_frame"] + 1 if sum_lg["moved"] else len(tr["s_blob"])
        s_blob_clip = tr["s_blob"][:end_blob]
        sc_blob_clip = np.where(np.isnan(s_blob_clip), 0.0, 1.0)
        sum_blob = summarize_slope_track(s_blob_clip, sc_blob_clip, fps=fps, mpp=tr["mpp"], min_sc=0.5)

        results[name] = {
            "meta": {
                "material": mat,
                "arm": "_".join(name.split("_")[1:-1]),
                "seed": int(name.split("_")[-1].replace("s", "")),
                "fps": fps,
                "num_frames": len(frames),
                "cfg": float(side.get("guidance_scale", 6.0)),
            },
            "rahul2_kin3": kin3_orig[name],
            "indep_lab_grad_ncc": sum_lg,
            "indep_lab_bgdiff_blob": sum_blob,
            "indep_bgr_ncc": sum_bgr,
        }

        v_pk = sum_lg.get("v_peak_mps") if sum_lg["moved"] else 0.0
        r2_v = sum_lg.get("v_peak") if kin3_orig[name].get("moved") else 0.0
        print(f"[{name}] LG v_peak={v_pk} m/s | kin3={r2_v} m/s | moved={sum_lg['moved']}")

    # Save complete results
    with open("results_slope_sweep.json", "w") as f:
        json.dump(results, f, indent=2)

    # Compute arm aggregations
    print("\n" + "="*80)
    print("ARM SUMMARY (Mean +- SE across seeds)")
    print("="*80)

    arms = {}
    for name, data in results.items():
        mat = data["meta"]["material"]
        arm = data["meta"]["arm"]
        key = f"{mat}_{arm}"
        if key not in arms:
            arms[key] = []
        arms[key].append(data)

    summary_table = {}
    for key, items in sorted(arms.items()):
        peaks_lg = [it["indep_lab_grad_ncc"]["v_peak_mps"] for it in items if it["indep_lab_grad_ncc"]["moved"]]
        peaks_kin3 = [it["rahul2_kin3"]["v_peak"] for it in items if it["rahul2_kin3"].get("moved") and it["rahul2_kin3"].get("v_peak") is not None]
        a_quads_lg = [it["indep_lab_grad_ncc"]["a_quad_whole"] for it in items if it["indep_lab_grad_ncc"]["moved"]]
        moved_count = sum(1 for it in items if it["indep_lab_grad_ncc"]["moved"])
        
        m_lg = float(np.mean(peaks_lg)) if peaks_lg else 0.0
        se_lg = float(np.std(peaks_lg, ddof=1) / np.sqrt(len(peaks_lg))) if len(peaks_lg) > 1 else 0.0
        m_k = float(np.mean(peaks_kin3)) if peaks_kin3 else 0.0
        se_k = float(np.std(peaks_kin3, ddof=1) / np.sqrt(len(peaks_kin3))) if len(peaks_kin3) > 1 else 0.0
        m_aq = float(np.mean(a_quads_lg)) if a_quads_lg else 0.0
        se_aq = float(np.std(a_quads_lg, ddof=1) / np.sqrt(len(a_quads_lg))) if len(a_quads_lg) > 1 else 0.0

        summary_table[key] = {
            "n_total": len(items),
            "n_moved": moved_count,
            "peak_v_lg_mean": round(m_lg, 3),
            "peak_v_lg_se": round(se_lg, 3),
            "peak_v_kin3_mean": round(m_k, 3),
            "peak_v_kin3_se": round(se_k, 3),
            "a_quad_lg_mean": round(m_aq, 3),
            "a_quad_lg_se": round(se_aq, 3),
            "peaks_lg_per_seed": [it["indep_lab_grad_ncc"].get("v_peak_mps", 0.0) if it["indep_lab_grad_ncc"]["moved"] else 0.0 for it in items],
            "peaks_kin3_per_seed": [it["rahul2_kin3"].get("v_peak", 0.0) if it["rahul2_kin3"].get("moved") else 0.0 for it in items],
        }

        print(f"{key:<18}: Moved {moved_count}/{len(items)} | LG peak={m_lg:.3f} +- {se_lg:.3f} m/s | kin3 peak={m_k:.3f} +- {se_k:.3f} m/s | whole a={m_aq:.2f} +- {se_aq:.2f} m/s^2")

    with open("summary_slope_sweep.json", "w") as f:
        json.dump(summary_table, f, indent=2)

if __name__ == "__main__":
    main()
