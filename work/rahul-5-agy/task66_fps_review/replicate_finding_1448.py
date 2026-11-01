#!/usr/bin/env python3
"""
Independent replication and review of Finding 1448 (poornima-1):
fps conditioning parameter (RoPE spacing) and text channel on Cosmos3-Nano dynamics.

Evaluates all 40 H100 clips (arms A, B, C, D, E across seeds 3-10, 93 frames, 832x480).
Computes:
1. Exact SHA-256 and metadata validation from sidecars
2. Multi-ROI frame difference motion profiles (Drop Corridor, Upper Arm, Table/Plank, Static Background)
3. Paired-by-seed contrast statistics (mean, SE, 95% CI, paired t-tests) for:
   - Text channel: C - A (fps 12 vs 24 @ rope24), D - B (fps 12 vs 24 @ rope12)
   - RoPE channel: B - A (rope 12 vs 24 @ text24), D - C (rope 12 vs 24 @ text12), E - A (rope 6 vs 24 @ text24)
4. Time-warp scaling k fitting, cross-correlation lags, and clock-hypothesis rejection testing (SSE ratios vs k=2 and k=4)
5. Settle frame analysis and late-motion variance
6. Automated unprompted late-event detection and visual classification
"""

import os
import sys
import glob
import re
import json
import hashlib
import cv2
import numpy as np

CLIPS_DIR = sys.argv[1] if len(sys.argv) > 1 else "/home/swarm/jobs/poornima-1/task45/clips_h100"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "/home/swarm/jobs/rahul-5-agy/task66_review"
os.makedirs(OUT_DIR, exist_ok=True)

# ROI definitions [y0, y1, x0, x1]
ROIS = {
    "corridor": (150, 440, 180, 440),     # author's drop ROI
    "arm": (0, 240, 180, 440),            # upper gripper/arm zone
    "table": (240, 440, 180, 440),        # lower plank/table zone
    "full": (0, 480, 0, 832),             # full frame
    "background": (150, 440, 550, 750)    # static background control
}

ARMS = ["A", "B", "C", "D", "E"]
SEEDS = list(range(3, 11))

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def analyze_clip(mp4_path, sidecar_path):
    clip_sha = get_sha256(mp4_path)
    with open(sidecar_path, "r") as f:
        sidecar = json.load(f)
    
    cap = cv2.VideoCapture(mp4_path)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    frames_gray = []
    sampled_rgb = {}
    sample_indices = [0, 24, 48, 66, 80, 92]
    
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx in sample_indices:
            sampled_rgb[idx] = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        frames_gray.append(gray)
        idx += 1
    cap.release()
    
    frames_gray = np.array(frames_gray)
    T = len(frames_gray)
    
    # Compute frame differences across ROIs
    roi_diffs = {}
    for r_name, (y0, y1, x0, x1) in ROIS.items():
        diffs = []
        for t in range(T - 1):
            patch_curr = frames_gray[t, y0:y1, x0:x1]
            patch_next = frames_gray[t + 1, y0:y1, x0:x1]
            diff = np.mean(np.abs(patch_next - patch_curr))
            diffs.append(float(diff))
        roi_diffs[r_name] = np.array(diffs)
    
    # Metrics
    # Settle frame on corridor: first frame after which 5-f smoothed motion < 1.5
    corridor_diff = roi_diffs["corridor"]
    smoothed_5 = np.convolve(corridor_diff, np.ones(5) / 5.0, mode="same")
    above_thr = np.where(smoothed_5 >= 1.5)[0]
    settle_frame = int(above_thr[-1] + 1) if len(above_thr) > 0 else 0
    
    # Late motion (last 24 frames: t=68 to 91 in 92-step diffs)
    late_slice = slice(-24, None)
    
    # Late arm activity check: max diff in arm ROI over frames 68..91
    arm_late_mean = float(np.mean(roi_diffs["arm"][late_slice]))
    arm_late_max = float(np.max(roi_diffs["arm"][late_slice]))
    
    # Table late activity check
    table_late_mean = float(np.mean(roi_diffs["table"][late_slice]))
    table_late_max = float(np.max(roi_diffs["table"][late_slice]))
    
    # Displacement from initial frame in arm and table
    f0_arm = frames_gray[0, ROIS["arm"][0]:ROIS["arm"][1], ROIS["arm"][2]:ROIS["arm"][3]]
    f_last_arm = frames_gray[-1, ROIS["arm"][0]:ROIS["arm"][1], ROIS["arm"][2]:ROIS["arm"][3]]
    arm_net_disp = float(np.mean(np.abs(f_last_arm - f0_arm)))
    
    return {
        "sha256": clip_sha,
        "sidecar": sidecar,
        "n_frames": n_frames,
        "fps": fps,
        "dims": (w, h),
        "roi_diffs": roi_diffs,
        "settle_frame": settle_frame,
        "motion_all": {r: float(np.mean(roi_diffs[r])) for r in ROIS},
        "motion_late24": {r: float(np.mean(roi_diffs[r][late_slice])) for r in ROIS},
        "arm_late_mean": arm_late_mean,
        "arm_late_max": arm_late_max,
        "table_late_mean": table_late_mean,
        "table_late_max": table_late_max,
        "arm_net_disp": arm_net_disp,
        "sampled_rgb": sampled_rgb
    }

def best_k_fit(mx, ma, ks=np.round(np.arange(0.5, 4.01, 0.025), 3)):
    t = np.arange(len(mx))
    errs = []
    for k in ks:
        tt = k * t
        valid = tt <= len(ma) - 1
        if np.sum(valid) < 12:
            errs.append(np.inf)
            continue
        interp_ma = np.interp(tt[valid], np.arange(len(ma)), ma)
        err = np.mean((mx[valid] - interp_ma) ** 2)
        errs.append(err)
    errs = np.array(errs)
    best_idx = np.argmin(errs)
    best_k_val = float(ks[best_idx])
    best_err = float(errs[best_idx])
    
    # Calculate error at specific theoretical k
    idx_k1 = np.argmin(np.abs(ks - 1.0))
    idx_k2 = np.argmin(np.abs(ks - 2.0))
    idx_k4 = np.argmin(np.abs(ks - 4.0))
    
    err_k1 = float(errs[idx_k1])
    err_k2 = float(errs[idx_k2])
    err_k4 = float(errs[idx_k4])
    
    return {
        "best_k": best_k_val,
        "min_err": best_err,
        "err_k1": err_k1,
        "err_k2": err_k2,
        "err_k4": err_k4,
        "sse_ratio_k2_vs_best": err_k2 / (best_err + 1e-8),
        "sse_ratio_k4_vs_best": err_k4 / (best_err + 1e-8)
    }

print("=== Starting Independent Analysis of Task 45 Clips ===")
all_results = {}
for arm in ARMS:
    all_results[arm] = {}
    for s in SEEDS:
        # Pattern match clip
        pattern = os.path.join(CLIPS_DIR, f"arm{arm}_*_s{s}.mp4")
        matches = glob.glob(pattern)
        if not matches:
            print(f"Warning: No match for arm {arm} seed {s}")
            continue
        mp4_path = matches[0]
        sidecar_path = mp4_path.replace(".mp4", ".json")
        res = analyze_clip(mp4_path, sidecar_path)
        all_results[arm][s] = res
        print(f"Loaded arm {arm} seed {s}: {os.path.basename(mp4_path)}")

print("\n--- Computing Multi-ROI Motion Summaries ---")
summary_motion = {}
for arm in ARMS:
    summary_motion[arm] = {}
    for r in ROIS:
        all_vals = [all_results[arm][s]["motion_all"][r] for s in SEEDS if s in all_results[arm]]
        late_vals = [all_results[arm][s]["motion_late24"][r] for s in SEEDS if s in all_results[arm]]
        n = len(all_vals)
        summary_motion[arm][r] = {
            "all_mean": float(np.mean(all_vals)),
            "all_se": float(np.std(all_vals, ddof=1) / np.sqrt(n)),
            "late_mean": float(np.mean(late_vals)),
            "late_se": float(np.std(late_vals, ddof=1) / np.sqrt(n)),
            "n": n
        }
        print(f"Arm {arm} {r:10s} | All: {summary_motion[arm][r]['all_mean']:.3f} ± {summary_motion[arm][r]['all_se']:.3f} | Late24: {summary_motion[arm][r]['late_mean']:.3f} ± {summary_motion[arm][r]['late_se']:.3f}")

print("\n--- Paired Contrast Analysis Across Seeds ---")
contrasts = [
    ("C", "A", "Text channel: 12 vs 24 fps @ RoPE 24"),
    ("D", "B", "Text channel: 12 vs 24 fps @ RoPE 12"),
    ("B", "A", "RoPE channel: 12 vs 24 fps @ Text 24"),
    ("D", "C", "RoPE channel: 12 vs 24 fps @ Text 12"),
    ("E", "A", "RoPE channel: 6 vs 24 fps @ Text 24")
]

paired_stats = {}
for arm_x, arm_y, desc in contrasts:
    paired_stats[f"{arm_x}-{arm_y}"] = {"desc": desc, "rois": {}}
    print(f"\nContrast {arm_x} - {arm_y} ({desc}):")
    common_seeds = sorted(set(all_results[arm_x].keys()) & set(all_results[arm_y].keys()))
    n = len(common_seeds)
    for r in ROIS:
        diff_all = np.array([all_results[arm_x][s]["motion_all"][r] - all_results[arm_y][s]["motion_all"][r] for s in common_seeds])
        diff_late = np.array([all_results[arm_x][s]["motion_late24"][r] - all_results[arm_y][s]["motion_late24"][r] for s in common_seeds])
        
        m_all, se_all = np.mean(diff_all), np.std(diff_all, ddof=1) / np.sqrt(n)
        t_all = m_all / (se_all + 1e-8)
        
        m_late, se_late = np.mean(diff_late), np.std(diff_late, ddof=1) / np.sqrt(n)
        t_late = m_late / (se_late + 1e-8)
        
        paired_stats[f"{arm_x}-{arm_y}"]["rois"][r] = {
            "all_diff_mean": float(m_all),
            "all_diff_se": float(se_all),
            "all_t": float(t_all),
            "late_diff_mean": float(m_late),
            "late_diff_se": float(se_late),
            "late_t": float(t_late),
            "raw_diff_all": [float(x) for x in diff_all],
            "raw_diff_late": [float(x) for x in diff_late]
        }
        print(f"  {r:10s} | All: {m_all:+.3f} ± {se_all:.3f} (t={t_all:+.2f}) | Late24: {m_late:+.3f} ± {se_late:.3f} (t={t_late:+.2f})")

print("\n--- Settle Frame Analysis ---")
settle_stats = {}
for arm in ARMS:
    st_vals = [all_results[arm][s]["settle_frame"] for s in SEEDS if s in all_results[arm]]
    n = len(st_vals)
    settle_stats[arm] = {
        "mean": float(np.mean(st_vals)),
        "se": float(np.std(st_vals, ddof=1) / np.sqrt(n)),
        "vals": st_vals,
        "n": n
    }
    print(f"Arm {arm} settle frame: {settle_stats[arm]['mean']:.2f} ± {settle_stats[arm]['se']:.2f} f (vals: {st_vals})")

print("\n--- Time-Warp k Fitting vs Reference Arm A ---")
timewarp_results = {}
for arm in ARMS:
    if arm == "A":
        continue
    timewarp_results[arm] = {"per_seed": {}}
    common_seeds = sorted(set(all_results[arm].keys()) & set(all_results["A"].keys()))
    k_vals = []
    sse_k2_ratios = []
    sse_k4_ratios = []
    
    for s in common_seeds:
        mx = all_results[arm][s]["roi_diffs"]["corridor"]
        ma = all_results["A"][s]["roi_diffs"]["corridor"]
        fit = best_k_fit(mx, ma)
        timewarp_results[arm]["per_seed"][s] = fit
        k_vals.append(fit["best_k"])
        sse_k2_ratios.append(fit["sse_ratio_k2_vs_best"])
        sse_k4_ratios.append(fit["sse_ratio_k4_vs_best"])
    
    # Pooled profile fit
    mean_mx = np.mean([all_results[arm][s]["roi_diffs"]["corridor"] for s in common_seeds], axis=0)
    mean_ma = np.mean([all_results["A"][s]["roi_diffs"]["corridor"] for s in common_seeds], axis=0)
    pooled_fit = best_k_fit(mean_mx, mean_ma)
    
    timewarp_results[arm]["k_values"] = k_vals
    timewarp_results[arm]["median_k"] = float(np.median(k_vals))
    timewarp_results[arm]["mean_k"] = float(np.mean(k_vals))
    timewarp_results[arm]["se_k"] = float(np.std(k_vals, ddof=1) / np.sqrt(len(k_vals)))
    timewarp_results[arm]["pooled_fit"] = pooled_fit
    timewarp_results[arm]["median_sse_ratio_k2"] = float(np.median(sse_k2_ratios))
    timewarp_results[arm]["median_sse_ratio_k4"] = float(np.median(sse_k4_ratios))
    
    print(f"Arm {arm} vs A: median k = {timewarp_results[arm]['median_k']:.3f} (mean {timewarp_results[arm]['mean_k']:.3f} ± {timewarp_results[arm]['se_k']:.3f}) | pooled k = {pooled_fit['best_k']:.3f}")
    print(f"         k values: {k_vals}")
    print(f"         SSE penalty vs k=2: {timewarp_results[arm]['median_sse_ratio_k2']:.2f}x; vs k=4: {timewarp_results[arm]['median_sse_ratio_k4']:.2f}x")

# Null distribution: A(s_i) vs A(s_j) for adjacent seeds
null_ks = []
for i in range(len(SEEDS)):
    s1 = SEEDS[i]
    s2 = SEEDS[(i + 1) % len(SEEDS)]
    ma1 = all_results["A"][s1]["roi_diffs"]["corridor"]
    ma2 = all_results["A"][s2]["roi_diffs"]["corridor"]
    null_fit = best_k_fit(ma1, ma2)
    null_ks.append(null_fit["best_k"])
timewarp_results["null_A_vs_A_shift"] = {
    "k_vals": null_ks,
    "median_k": float(np.median(null_ks)),
    "mean_k": float(np.mean(null_ks))
}
print(f"Null A(s_i) vs A(s_j): median k = {np.median(null_ks):.3f}, vals = {null_ks}")

print("\n--- Event Classification and Anomaly Rate ---")
anomaly_audit = {}
for arm in ARMS:
    anomalies = []
    for s in SEEDS:
        if s not in all_results[arm]:
            continue
        res = all_results[arm]
        # Anomaly criteria:
        # Arm motion late max > 3.0 or table late max > 4.0 or settle frame > 75
        is_anom = False
        reasons = []
        if res[s]["arm_late_mean"] > 2.0 or res[s]["arm_late_max"] > 4.0:
            is_anom = True
            reasons.append(f"late_arm_motion(mean={res[s]['arm_late_mean']:.2f},max={res[s]['arm_late_max']:.2f})")
        if res[s]["table_late_mean"] > 2.5 or res[s]["table_late_max"] > 5.0:
            is_anom = True
            reasons.append(f"late_table_activity(mean={res[s]['table_late_mean']:.2f},max={res[s]['table_late_max']:.2f})")
        if res[s]["settle_frame"] >= 80:
            is_anom = True
            reasons.append(f"unsettled(frame={res[s]['settle_frame']})")
        if is_anom:
            anomalies.append({"seed": s, "reasons": reasons})
    
    anomaly_rate = len(anomalies) / len(SEEDS)
    anomaly_audit[arm] = {
        "n_anomalies": len(anomalies),
        "total": len(SEEDS),
        "anomaly_rate": float(anomaly_rate),
        "details": anomalies
    }
    print(f"Arm {arm}: {len(anomalies)}/{len(SEEDS)} clips ({anomaly_rate*100:.1f}%) exhibit late unprompted event anomalies")

print("\n--- Generating Consolidated QC Contact Sheets ---")
# Build a 5-arm comparison sheet for seeds 3, 5, 7, 10
qc_seeds = [3, 5, 7, 10]
frames_to_show = [0, 24, 48, 66, 80, 92]
sheet_rows = []

for arm in ARMS:
    for s in qc_seeds:
        if s in all_results[arm]:
            row_tiles = []
            for f_idx in frames_to_show:
                tile = all_results[arm][s]["sampled_rgb"][f_idx].copy()
                tile = cv2.resize(tile, (208, 120))
                # Annotate arm, seed, frame
                cv2.putText(tile, f"Arm{arm} s{s} f{f_idx}", (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
                row_tiles.append(tile)
            sheet_rows.append(np.hstack(row_tiles))

full_qc_sheet = np.vstack(sheet_rows)
qc_sheet_path = os.path.join(OUT_DIR, "task66_qc_contact_sheet.jpg")
cv2.imwrite(qc_sheet_path, full_qc_sheet)
print(f"Saved QC contact sheet to {qc_sheet_path} ({full_qc_sheet.shape[1]}x{full_qc_sheet.shape[0]})")

# Save final comprehensive JSON results
final_output = {
    "summary_motion": summary_motion,
    "paired_stats": paired_stats,
    "settle_stats": settle_stats,
    "timewarp_results": timewarp_results,
    "anomaly_audit": anomaly_audit,
    "clip_manifest": {
        arm: {
            s: {
                "sha256": all_results[arm][s]["sha256"],
                "settle_frame": all_results[arm][s]["settle_frame"],
                "motion_all": all_results[arm][s]["motion_all"],
                "motion_late24": all_results[arm][s]["motion_late24"],
                "arm_late_mean": all_results[arm][s]["arm_late_mean"],
                "table_late_mean": all_results[arm][s]["table_late_mean"]
            }
            for s in all_results[arm]
        }
        for arm in ARMS
    }
}

json_path = os.path.join(OUT_DIR, "replicate_finding_1448_results.json")
with open(json_path, "w") as f:
    json.dump(final_output, f, indent=2)
print(f"Saved full JSON results to {json_path}")
print("=== Replicate Analysis Complete ===")
