#!/usr/bin/env python3
"""
Independent replication and audit of Finding #4709 (task 204, ro-3):
Sampler schedule (NVIDIA-style non-Karras sigmas, 'nv', vs UniPC+Karras default, 'kar')
on mid-swing pendulum I2V.
"""

import os
import sys
import json
import glob
import hashlib
import subprocess
import numpy as np
import cv2
from pathlib import Path
from scipy import signal, fft

CLIPS_DIR = Path("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/clips")
WORK_DIR = Path("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit")
REPO_DIR = Path("/home/sha/devel/cosmos-swarm")

MEASURE_PEND = REPO_DIR / "tools" / "trk_ballfall" / "measure_pend.py"
PEND_ACF = REPO_DIR / "tools" / "pend_acf" / "pend_acf.py"

PAIRS = [
    ("ms_pend10_midB_nv_s1", "ms_pend10_midB_kar_s1", "pend10", 1),
    ("ms_pend10_midB_nv_s2", "ms_pend10_midB_kar_s2", "pend10", 2),
    ("ms_pend10_midB_nv_s3", "ms_pend10_midB_kar_s3", "pend10", 3),
    ("ms_pend11_midB_nv_s1", "ms_pend11_midB_kar_s1", "pend11", 1),
    ("ms_pend11_midB_nv_s2", "ms_pend11_midB_kar_s2", "pend11", 2),
    ("ms_pend11_midB_nv_s3", "ms_pend11_midB_kar_s3", "pend11", 3),
]

REAL_PERIODS = {
    "pend10": 1.17,  # GAUGE ground truth mocap
    "pend11": 1.18,  # GAUGE ground truth mocap
}

def load_frames(video_path):
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def run_tools(clip_path, qc_prefix):
    # Run measure_pend v1 (do not pass --qc as it requires matplotlib)
    mp_cmd = [sys.executable, str(MEASURE_PEND), str(clip_path), "--fps", "24"]
    p = subprocess.run(mp_cmd, capture_output=True, text=True)
    mp_res = {}
    try:
        idx = p.stdout.index('{')
        mp_res = json.loads(p.stdout[idx:])
    except Exception as e:
        mp_res = {"error": str(e), "raw": p.stdout, "stderr": p.stderr}

    # Run pend_acf
    acf_cmd = [sys.executable, str(PEND_ACF), str(clip_path), "--fps", "24", "--skip", "0"]
    p_acf = subprocess.run(acf_cmd, capture_output=True, text=True)
    acf_res = {}
    try:
        idx = p_acf.stdout.index('{')
        acf_res = json.loads(p_acf.stdout[idx:])
    except Exception as e:
        acf_res = {"error": str(e), "raw": p_acf.stdout, "stderr": p_acf.stderr}

    return mp_res, acf_res

def independent_bob_tracking(frames):
    """
    Independent tracker: tracks x-position of dark bob in pendulum ROI
    across frames 0..92, then fits sinusoidal period & autocorrelation.
    """
    # Pendulum ROI: y in [120, 420], x in [220, 620]
    # Find minimum intensity centroid in ROI
    x_positions = []
    y_positions = []
    for f in frames:
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        roi = gray[120:420, 220:620]
        # Invert so dark bob is peak
        inv = 255 - roi
        # Threshold top 5% darkest pixels
        th = np.percentile(inv, 98)
        mask = (inv >= th).astype(np.float32)
        # Centroid
        M = cv2.moments(mask)
        if M["m00"] > 0:
            cx = M["m10"] / M["m00"] + 220
            cy = M["m01"] / M["m00"] + 120
        else:
            cx = 420.0
            cy = 270.0
        x_positions.append(cx)
        y_positions.append(cy)

    x = np.array(x_positions)
    y = np.array(y_positions)
    # Detrend
    x_detrend = signal.detrend(x)
    
    # Autocorrelation
    ac = np.correlate(x_detrend, x_detrend, mode='full')
    ac = ac[len(ac)//2:]
    ac /= ac[0]
    
    # Peaks in autocorrelation for period (lag > 5 frames)
    peaks, _ = signal.find_peaks(ac[5:], height=0.1)
    if len(peaks) > 0:
        first_peak_lag = peaks[0] + 5
        indep_T = first_peak_lag / 24.0
    else:
        indep_T = None

    return {
        "x_track": x.tolist(),
        "y_track": y.tolist(),
        "indep_T_s": indep_T,
        "x_span_px": float(np.max(x) - np.min(x)),
    }

def main():
    os.makedirs(WORK_DIR / "qc", exist_ok=True)
    results = {
        "pairs": {},
        "per_clip": {},
        "pixel_summary": {},
        "period_summary": {},
        "sigma_check": {},
    }

    # Verify server sidecars
    print("Checking server sidecars...")
    for sidecar_file in glob.glob(str(REPO_DIR / "work/ro-3/task204_sampler/sidecars_server/*.json")):
        with open(sidecar_file) as f:
            sc = json.load(f)
        qid = sc.get("extra_params", {}).get("queue_id")
        sampler = sc.get("sampler")
        sigmas = sc.get("sigmas", [])
        if qid:
            results["sigma_check"][qid] = {
                "sampler": sampler,
                "n_sigmas": len(sigmas),
                "sigmas_first5": sigmas[:5],
                "sigmas_last3": sigmas[-3:],
            }

    # Process all clips
    print("\nProcessing clips and running kinematic tools...")
    for nv_name, kar_name, scene, seed in PAIRS:
        nv_path = CLIPS_DIR / f"{nv_name}.mp4"
        kar_path = CLIPS_DIR / f"{kar_name}.mp4"

        if not nv_path.exists() or not kar_path.exists():
            print(f"Waiting for {nv_path.name} or {kar_path.name} to exist...")
            return

        print(f"\nAnalyzing pair: {scene} seed {seed} ({nv_name} vs {kar_name})")

        # Load video frames
        nv_frames = load_frames(nv_path)
        kar_frames = load_frames(kar_path)

        assert len(nv_frames) == 93, f"Expected 93 frames, got {len(nv_frames)}"
        assert len(kar_frames) == 93, f"Expected 93 frames, got {len(kar_frames)}"

        # Frame 0 check
        f0_mad = float(np.mean(np.abs(nv_frames[0].astype(np.float32) - kar_frames[0].astype(np.float32))))

        # Pixel difference matrices
        # Frames 10..92
        diffs_10_92 = []
        diffs_all = []
        roi_pend_diffs = []
        roi_bg_diffs = []

        for i in range(1, 93):
            nv_f = nv_frames[i].astype(np.float32)
            kar_f = kar_frames[i].astype(np.float32)
            mad = float(np.mean(np.abs(nv_f - kar_f)))
            diffs_all.append(mad)
            if i >= 10:
                diffs_10_92.append(mad)

            # Pendulum ROI: y in [100, 450], x in [200, 600]
            pend_mad = float(np.mean(np.abs(nv_f[100:450, 200:600] - kar_f[100:450, 200:600])))
            roi_pend_diffs.append(pend_mad)

            # BG ROI: y in [0, 150], x in [600, 832] (top-right background)
            bg_mad = float(np.mean(np.abs(nv_f[0:150, 600:832] - kar_f[0:150, 600:832])))
            roi_bg_diffs.append(bg_mad)

        mean_mad_10_92 = float(np.mean(diffs_10_92))
        mean_mad_all = float(np.mean(diffs_all))
        mean_pend_roi = float(np.mean(roi_pend_diffs))
        mean_bg_roi = float(np.mean(roi_bg_diffs))

        # Kinematic measurements
        nv_mp, nv_acf = run_tools(nv_path, str(WORK_DIR / f"qc/{nv_name}"))
        kar_mp, kar_acf = run_tools(kar_path, str(WORK_DIR / f"qc/{kar_name}"))

        # Independent tracking
        nv_indep = independent_bob_tracking(nv_frames)
        kar_indep = independent_bob_tracking(kar_frames)

        results["per_clip"][nv_name] = {
            "mp_T": nv_mp.get("period_s"),
            "mp_ci": nv_mp.get("period_ci95"),
            "mp_r2": nv_mp.get("r2"),
            "mp_flag": nv_mp.get("flag"),
            "acf_T": (nv_acf.get("period_frames") or 0) / 24.0 or None,
            "acf_flag": nv_acf.get("flag"),
            "indep_T": nv_indep["indep_T_s"],
            "x_span_px": nv_indep["x_span_px"],
        }
        results["per_clip"][kar_name] = {
            "mp_T": kar_mp.get("period_s"),
            "mp_ci": kar_mp.get("period_ci95"),
            "mp_r2": kar_mp.get("r2"),
            "mp_flag": kar_mp.get("flag"),
            "acf_T": (kar_acf.get("period_frames") or 0) / 24.0 or None,
            "acf_flag": kar_acf.get("flag"),
            "indep_T": kar_indep["indep_T_s"],
            "x_span_px": kar_indep["x_span_px"],
        }

        # Pair delta
        mp_nv_t = nv_mp.get("period_s")
        mp_kar_t = kar_mp.get("period_s")
        delta_mp = (mp_nv_t - mp_kar_t) if (mp_nv_t is not None and mp_kar_t is not None) else None

        acf_nv_t = (nv_acf.get("period_frames") or 0) / 24.0 or None
        acf_kar_t = (kar_acf.get("period_frames") or 0) / 24.0 or None
        delta_acf = (acf_nv_t - acf_kar_t) if (acf_nv_t is not None and acf_kar_t is not None) else None

        pair_key = f"{scene}_s{seed}"
        results["pairs"][pair_key] = {
            "scene": scene,
            "seed": seed,
            "f0_mad": f0_mad,
            "mad_10_92": mean_mad_10_92,
            "mad_all": mean_mad_all,
            "pend_roi_mad": mean_pend_roi,
            "bg_roi_mad": mean_bg_roi,
            "nv_mp_T": mp_nv_t,
            "kar_mp_T": mp_kar_t,
            "delta_mp": delta_mp,
            "nv_acf_T": acf_nv_t,
            "kar_acf_T": acf_kar_t,
            "delta_acf": delta_acf,
            "nv_flag": nv_mp.get("flag"),
            "kar_flag": kar_mp.get("flag"),
            "real_T": REAL_PERIODS[scene],
        }

        print(f"  f0_mad: {f0_mad:.4f}, mad_10_92: {mean_mad_10_92:.3f}, pend_roi: {mean_pend_roi:.3f}, bg_roi: {mean_bg_roi:.3f}")
        print(f"  mp_T: nv={mp_nv_t}, kar={mp_kar_t}, delta={delta_mp} (real={REAL_PERIODS[scene]})")
        print(f"  acf_T: nv={acf_nv_t}, kar={acf_kar_t}, delta={delta_acf}")

    # Control comparison: Between-seed differences under same sampler
    print("\nComputing between-seed baseline controls...")
    seed_controls = []
    for scene in ["pend10", "pend11"]:
        for arm in ["nv", "kar"]:
            f_s1 = load_frames(CLIPS_DIR / f"ms_{scene}_midB_{arm}_s1.mp4")
            f_s2 = load_frames(CLIPS_DIR / f"ms_{scene}_midB_{arm}_s2.mp4")
            s1_s2_mad = float(np.mean([np.mean(np.abs(f_s1[i].astype(np.float32) - f_s2[i].astype(np.float32))) for i in range(10, 93)]))
            seed_controls.append(s1_s2_mad)
            print(f"  Between-seed ({scene} {arm} s1 vs s2): {s1_s2_mad:.3f}")

    results["pixel_summary"]["between_seed_mad_mean"] = float(np.mean(seed_controls))
    results["pixel_summary"]["between_seed_mad_range"] = [float(np.min(seed_controls)), float(np.max(seed_controls))]

    all_mad_10_92 = [p["mad_10_92"] for p in results["pairs"].values()]
    results["pixel_summary"]["nv_vs_kar_mad_10_92_mean"] = float(np.mean(all_mad_10_92))
    results["pixel_summary"]["nv_vs_kar_mad_10_92_range"] = [float(np.min(all_mad_10_92)), float(np.max(all_mad_10_92))]

    # Valid period pairs (where both arms have reliable fits, i.e. not flagged 'check')
    valid_mp_deltas = [p["delta_mp"] for p in results["pairs"].values() if p["nv_flag"] == "ok" and p["kar_flag"] == "ok"]
    all_mp_deltas = [p["delta_mp"] for p in results["pairs"].values() if p["delta_mp"] is not None]

    results["period_summary"]["valid_mp_deltas"] = valid_mp_deltas
    results["period_summary"]["all_mp_deltas"] = all_mp_deltas
    if valid_mp_deltas:
        results["period_summary"]["valid_mp_delta_mean"] = float(np.mean(valid_mp_deltas))
        results["period_summary"]["valid_mp_abs_delta_max"] = float(np.max(np.abs(valid_mp_deltas)))

    # ACF deltas
    all_acf_deltas = [p["delta_acf"] for p in results["pairs"].values() if p["delta_acf"] is not None]
    results["period_summary"]["all_acf_deltas"] = all_acf_deltas
    results["period_summary"]["acf_abs_delta_mean"] = float(np.mean(np.abs(all_acf_deltas)))

    # Save full JSON
    with open(WORK_DIR / "replication_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nReplication audit finished successfully. Results saved to replication_results.json.")

if __name__ == "__main__":
    main()
