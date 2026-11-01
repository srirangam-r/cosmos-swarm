"""Independent replication of pend_acf validation and Nano pendulum period scaling (findings 525 & 550).

Task 38 (agy-1):
1. Independently evaluate tools/pend_acf (L1 self-similarity) alongside three independent period estimators:
   - l2_med_acf: tracker-free temporal-median L2 frame distance on moving pixels (robust to transient robot-arm sweeps)
   - cos_med_acf: tracker-free temporal-median cosine distance on temporal-mean-centered moving pixels
   - dark_bob_zc: 80th-percentile bright-background subtraction isolating the dark pendulum bob, measuring zero-crossing and turning-point intervals
   across:
   - the 4 referee planted pendulum clips (planted-00, 07, 11, 13)
   - the 20 real GAUGE pendulum videos at Cosmos letterboxed 832x480 resolution (full 7.9 s window and short 2.0, 2.4, 3.0 s post-release windows)
2. Independently measure the available Nano pendulum clips in the repo (pend_A_fps24_93f_s1.mp4, pend_B_fps12_93f_s1.mp4) with all four methods,
   quantify non-stationary cycle-to-cycle variation, and cross-check the saved 189-frame Nano outputs (fps 48, fps 24, fps 12, and fps 24 duration-template-off).
"""
import os, sys, json, subprocess
import numpy as np
import cv2

REPO = "/home/nail/swarm-work/agy-1/cosmos-swarm"
PLANTED_DIR = "/home/nail/swarm-work/agy-1/planted"
REAL_DIR = "/home/nail/swarm-work/agy-1/real_pend_lb832"
OUT_DIR = "/home/nail/swarm-work/agy-1/cosmos-swarm/work/agy-1/pend_acf_review"
os.makedirs(OUT_DIR, exist_ok=True)


def load_frames(path, skip=0):
    c = cv2.VideoCapture(path)
    F = []
    while True:
        ok, f = c.read()
        if not ok:
            break
        F.append(f)
    c.release()
    return F[skip:]


def parab_peak(y, i):
    if i <= 0 or i >= len(y) - 1:
        return float(i)
    a, b, c = float(y[i - 1]), float(y[i]), float(y[i + 1])
    den = a - 2.0 * b + c
    off = 0.5 * (a - c) / den if abs(den) > 1e-12 else 0.0
    return float(i + np.clip(off, -0.5, 0.5))


def first_min_curve(lags, D, depth=0.35):
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


def independent_estimators(path, fps, skip=0, release=False, max_s=None):
    F = load_frames(path, skip=skip)
    G_full = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in F])
    G = np.array([
        cv2.GaussianBlur(
            cv2.resize(g, (g.shape[1] // 8, g.shape[0] // 8), interpolation=cv2.INTER_AREA),
            (3, 3), 0
        )
        for g in G_full
    ])
    r0 = 0
    if release:
        e = np.abs(np.diff(G, axis=0)).mean(axis=(1, 2))
        thr = 0.15 * np.percentile(e, 90)
        m = e > thr
        for k in range(len(m) - 3):
            if m[k:k + 4].all():
                r0 = k
                break
    G = G[r0:]
    G_full = G_full[r0:]
    if max_s is not None:
        n_keep = int(round(max_s * fps)) + 1
        G = G[:n_keep]
        G_full = G_full[:n_keep]

    n = len(G)
    lags = np.arange(1, int(n / 1.3) + 1)
    sd = G.std(axis=0)
    mask = sd >= np.percentile(sd, 90)
    Xm = G[:, mask]

    # 1. L1 mean self-similarity (reimplements pend_acf math independently)
    D_l1 = np.array([np.abs(Xm[:-L] - Xm[L:]).mean() for L in lags])
    m_l1 = first_min_curve(lags, D_l1)

    # 2. L2 self-similarity: standard mean L2 distance and temporal-median L2 distance
    D_l2 = np.array([np.sqrt(np.mean((Xm[:-L] - Xm[L:]) ** 2)) for L in lags])
    m_l2_mean = first_min_curve(lags, D_l2)
    D_l2_med = np.array([np.median(np.sqrt(np.mean((Xm[:-L] - Xm[L:]) ** 2, axis=1))) for L in lags])
    m_l2 = first_min_curve(lags, D_l2_med) or m_l2_mean

    # 3. Temporal-median Cosine distance on temporal-mean-centered moving pixels
    Xc = Xm - Xm.mean(axis=0, keepdims=True)
    norms = np.linalg.norm(Xc, axis=1) + 1e-8
    D_cos_med = np.array([
        np.median(1.0 - np.sum(Xc[:-L] * Xc[L:], axis=1) / (norms[:-L] * norms[L:]))
        for L in lags
    ])
    m_cos = first_min_curve(lags, D_cos_med)

    # 4. 80th-percentile bright-background subtraction (isolates dark bob from static stand)
    bg_bright = np.percentile(G_full, 80, axis=0)
    dark_diff = np.clip(bg_bright - G_full, 0, 255)
    h, w = G_full.shape[1], G_full.shape[2]
    dark_diff[:, :int(0.10 * h), :] = 0
    dark_diff[:, int(0.83 * h):, :] = 0
    dark_diff[:, :, :int(0.25 * w)] = 0
    dark_diff[:, :, int(0.75 * w):] = 0
    cx_list, cy_list, area_list, ang_list = [], [], [], []
    for t in range(n):
        mb = (dark_diff[t] > 32).astype(np.uint8)
        mb = cv2.morphologyEx(mb, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n_cc, _, st, cen = cv2.connectedComponentsWithStats(mb)
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
        ang_list.append(float(np.degrees(np.arctan2(cx - 415.0, max(20.0, cy - 135.0)))))

    x_sig = np.array(cx_list) - np.median(cx_list)
    sg = np.sign(x_sig)
    zc_intervals = []
    for up in (True, False):
        idx = np.where((sg[:-1] < 0) & (sg[1:] >= 0))[0] if up else np.where((sg[:-1] > 0) & (sg[1:] <= 0))[0]
        tc = idx - x_sig[idx] / (x_sig[idx + 1] - x_sig[idx] + 1e-12)
        if len(tc) > 1:
            zc_intervals.extend(np.diff(tc).tolist())
    P_zc_f = float(np.median(zc_intervals)) if zc_intervals else None

    ang_arr = np.array(ang_list)
    right_peaks = [
        int(t + skip + r0) for t in range(1, n - 1)
        if ang_arr[t] >= ang_arr[t - 1] and ang_arr[t] >= ang_arr[t + 1] and ang_arr[t] > 8.0
    ]
    left_peaks = [
        int(t + skip + r0) for t in range(1, n - 1)
        if ang_arr[t] <= ang_arr[t - 1] and ang_arr[t] <= ang_arr[t + 1] and ang_arr[t] < -8.0
    ]

    # Also invoke ro-3's pend_acf.py subprocess for exact comparison
    cmd = ["python3", "-I", f"{REPO}/tools/pend_acf/pend_acf.py", path, "--fps", str(fps), "--skip", str(skip)]
    if release:
        cmd.append("--release")
    if max_s is not None:
        cmd.extend(["--max-s", str(max_s)])
    r_sub = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)

    return {
        "fps": fps,
        "skip": skip,
        "release_frame": int(r0 + skip),
        "n_used": n,
        "pend_acf_cli": {
            "period_frames": r_sub.get("period_frames"),
            "period_s": r_sub.get("period_s"),
            "ci95_frames": r_sub.get("ci95_frames"),
            "flag": r_sub.get("flag"),
            "window_spread": r_sub.get("window_spread"),
        },
        "l1_acf": {
            "period_frames": m_l1[0] if m_l1 else None,
            "period_s": (m_l1[0] / fps) if m_l1 else None,
        },
        "l2_med_acf": {
            "period_frames": m_l2[0] if m_l2 else None,
            "period_s": (m_l2[0] / fps) if m_l2 else None,
        },
        "cos_med_acf": {
            "period_frames": m_cos[0] if m_cos else None,
            "period_s": (m_cos[0] / fps) if m_cos else None,
        },
        "dark_bob_tracker": {
            "period_zc_frames": P_zc_f,
            "period_zc_s": (P_zc_f / fps) if P_zc_f else None,
            "zc_intervals_frames": [round(float(x), 3) for x in zc_intervals],
            "right_turning_frames": right_peaks,
            "left_turning_frames": left_peaks,
            "right_turning_diffs": np.diff(right_peaks).tolist() if len(right_peaks) > 1 else [],
            "left_turning_diffs": np.diff(left_peaks).tolist() if len(left_peaks) > 1 else [],
        },
    }


def summarize_ratios(ratios):
    a = np.array([x if x is not None else np.nan for x in ratios], dtype=float)
    valid = a[~np.isnan(a)]
    return {
        "n_total": int(len(a)),
        "n_valid": int(len(valid)),
        "n_fail": int(np.sum(np.isnan(a))),
        "mean": float(np.mean(valid)),
        "se": float(np.std(valid, ddof=1) / np.sqrt(len(valid))),
        "sd": float(np.std(valid, ddof=1)),
        "median": float(np.median(valid)),
        "max_abs_err_pct": float(np.max(np.abs(valid - 1.0)) * 100.0),
        "within_1pct": int(np.sum(np.abs(valid - 1.0) < 0.01)),
        "within_5pct": int(np.sum(np.abs(valid - 1.0) < 0.05)),
    }


def main():
    results = {"planted": {}, "real_gauge_full": {}, "real_gauge_short": {}, "nano_clips": {}}

    # 1. Planted pendulum clips
    mp_v1 = json.load(open(f"{REPO}/tools/trk_ballfall/planted_estimates_pend_v1.json"))
    for cid in ["00", "07", "11", "13"]:
        key = f"planted-{cid}"
        p = f"{PLANTED_DIR}/{key}.mp4"
        r = independent_estimators(p, 24.0, skip=0, release=False)
        r["measure_pend_v1_s"] = mp_v1[key]["period_s"]
        r["rel_diff_vs_measure_pend_v1_pct"] = (
            abs(r["pend_acf_cli"]["period_s"] - mp_v1[key]["period_s"]) / mp_v1[key]["period_s"] * 100.0
        )
        results["planted"][key] = r

    # 2. 20 real GAUGE pendulum videos (full 7.9s window and short 2.0, 2.4, 3.0s windows)
    ref_mocap = json.load(open(f"{REPO}/work/raj-3/gauge_pend/pend_pseudo_cosmos_results.json"))
    methods = ["pend_acf_cli", "l2_med_acf", "cos_med_acf", "dark_bob_tracker"]
    full_ratios = {m: [] for m in methods}
    per_clip_full = {}
    for i in range(1, 21):
        fps = ref_mocap[str(i)]["fps"]
        tmocap = ref_mocap[str(i)]["T_mocap_zc"]
        r = independent_estimators(f"{REAL_DIR}/pend{i}.mp4", fps, skip=0, release=True)
        r["T_mocap_zc"] = tmocap
        per_clip_full[str(i)] = r
        full_ratios["pend_acf_cli"].append(r["pend_acf_cli"]["period_s"] / tmocap)
        full_ratios["l2_med_acf"].append(r["l2_med_acf"]["period_s"] / tmocap)
        full_ratios["cos_med_acf"].append(r["cos_med_acf"]["period_s"] / tmocap)
        full_ratios["dark_bob_tracker"].append(r["dark_bob_tracker"]["period_zc_s"] / tmocap)

    results["real_gauge_full"] = {
        "summary": {m: summarize_ratios(full_ratios[m]) for m in methods},
        "per_clip": per_clip_full,
    }

    for ms in [2.0, 2.4, 3.0]:
        short_ratios = {m: [] for m in ["pend_acf_cli", "l2_med_acf", "cos_med_acf"]}
        for i in range(1, 21):
            fps = ref_mocap[str(i)]["fps"]
            tmocap = ref_mocap[str(i)]["T_mocap_zc"]
            r = independent_estimators(f"{REAL_DIR}/pend{i}.mp4", fps, skip=0, release=True, max_s=ms)
            for m in short_ratios:
                val = r[m]["period_s"]
                short_ratios[m].append((val / tmocap) if val is not None else None)
        results["real_gauge_short"][str(ms)] = {
            m: summarize_ratios(short_ratios[m]) for m in short_ratios
        }

    # 3. All available Nano clips (93f, 189f, 61f)
    for name, rel_path, fps, nf in [
        ("pend_A_fps24_93f_s1", "work/ro-1/fps_sweep/pend_A_fps24_93f_s1.mp4", 24.0, 93),
        ("pend_B_fps12_93f_s1", "work/ro-1/fps_sweep/pend_B_fps12_93f_s1.mp4", 12.0, 93),
        ("pend_fps48_189f_s1", "work/ro-3/task25_fps_pendulum/clips189/pend_fps48_s1_189f_crf20.mp4", 48.0, 189),
        ("pend_fps24_189f_s1", "work/ro-3/task25_fps_pendulum/clips189/pend_fps24_s1_189f_crf20.mp4", 24.0, 189),
        ("pend_fps24_nodur_189f_s1", "work/ro-3/task25_fps_pendulum/clips189/pend_fps24_nodur_s1_189f_crf20.mp4", 24.0, 189),
        ("pend_fps12_189f_s1", "work/ro-3/task25_fps_pendulum/clips189/pend_fps12_s1_189f_crf20.mp4", 12.0, 189),
        ("pend_fps24_189f_s2", "work/ro-3/task25_fps_pendulum/clips_more/pend_fps24_s2.mp4", 24.0, 189),
        ("pend_fps24_61f_s1", "work/ro-3/task25_fps_pendulum/clips_more/pend_fps24_61f_s1.mp4", 24.0, 61),
    ]:
        r = independent_estimators(f"{REPO}/{rel_path}", fps, skip=12, release=False)
        r["num_frames"] = nf
        r["p_over_num_frames_acf"] = (
            (r["pend_acf_cli"]["period_frames"] / float(nf))
            if r["pend_acf_cli"]["period_frames"] is not None
            else None
        )
        results["nano_clips"][name] = r

    # Cross-check saved 189f JSON outputs from ro-3
    saved_189 = {}
    for name, jf, num_f in [
        ("pend_fps48_189f_s1", "nano_pend_fps48_s1.json", 189),
        ("pend_fps24_189f_s1", "nano_pend_fps24_s1.json", 189),
        ("pend_fps24_nodur_189f_s1", "pend_fps24_nodur_s1_acf.json", 189),
        ("pend_fps12_189f_s1", "nano_pend_fps12_s1.json", 189),
    ]:
        d = json.load(open(f"{REPO}/work/ro-3/task25_fps_pendulum/pend_acf_v1/{jf}"))
        d["num_frames"] = num_f
        d["p_over_num_frames"] = d["period_frames"] / float(num_f)
        saved_189[name] = d
    results["nano_saved_189f"] = saved_189

    out_path = f"{OUT_DIR}/results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print("Saved results to", out_path)


if __name__ == "__main__":
    main()
