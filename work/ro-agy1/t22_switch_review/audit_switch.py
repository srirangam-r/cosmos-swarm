#!/usr/bin/env python3
"""
Independent Audit and Replication of Prompt-Switch Window Findings (#4263 and #4851, Task 22)
Author: ro-agy1

Audits:
1. Quantitative replication of v8 native clips in work/ro-1/cause_v8/native/
2. Audit of repository evidence completeness for Finding #4851 (v9)
3. Trajectory analysis across prompt conditioning windows
"""

import os
import glob
import json
import numpy as np
import cv2

def analyze_clip(clip_path):
    cap = cv2.VideoCapture(clip_path)
    fr = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Grayscale corridor crop: y in [130, 360], x in [220, 360]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        crop = gray[130:360, 220:360]
        fr.append(crop)
    cap.release()
    
    if len(fr) == 0:
        raise ValueError(f"No frames decoded from {clip_path}")
        
    g = np.stack(fr)
    # Absolute frame difference
    d = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))
    
    early = float(np.mean(d[1:45]))
    late = float(np.mean(d[45:]))
    last20 = float(np.mean(d[-20:]))
    
    return {
        "n_frames": len(fr),
        "early": round(early, 3),
        "late": round(late, 3),
        "last20": round(last20, 3),
        "d_curve": [round(float(x), 3) for x in d]
    }

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "../../.."))
    cause_v8_dir = os.path.join(repo_root, "work", "ro-1", "cause_v8")
    native_dir = os.path.join(cause_v8_dir, "native")
    eye_codes_csv = os.path.join(cause_v8_dir, "eye_codes.csv")
    
    out_dir = os.path.join(repo_root, "work", "ro-agy1", "t22_switch_review")
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Audit v8 native clips
    mp4_files = sorted(glob.glob(os.path.join(native_dir, "*.mp4")))
    clip_results = {}
    print(f"Decoding {len(mp4_files)} native MP4 clips from {native_dir}...")
    
    for mp4 in mp4_files:
        name = os.path.basename(mp4)[:-4]
        res = analyze_clip(mp4)
        clip_results[name] = res
        print(f"  {name:35s} | frames: {res['n_frames']} | early: {res['early']:5.2f} | late: {res['late']:5.2f} | last20: {res['last20']:5.2f}")
        
    # 2. Check eye_codes.csv contents
    with open(eye_codes_csv, "r") as f:
        csv_lines = [line.strip() for line in f if line.strip()]
    
    v8_rows = [l for l in csv_lines[1:] if "v8_" in l]
    v9_rows = [l for l in csv_lines[1:] if "v9_" in l]
    
    print(f"\neye_codes.csv audit: Total lines = {len(csv_lines)}, v8 rows = {len(v8_rows)}, v9 rows = {len(v9_rows)}")
    
    # 3. Check for existence of cause_v9 directory in work/ro-1/
    ro1_dir = os.path.join(repo_root, "work/ro-1")
    cause_v9_dir = os.path.join(ro1_dir, "cause_v9")
    cause_v9_exists = os.path.exists(cause_v9_dir)
    print(f"cause_v9 directory exists in shared repo: {cause_v9_exists}")
    
    # 4. Check author reported vs independently computed last20
    author_v8_reported = {
        "v8_SWfull_ball1_fps24_93f_s3": 2.02,
        "v8_SWfull_ball1_fps24_93f_s5": 0.56,
        "v8_SWe3_ball1_fps24_93f_s3": 3.49,
        "v8_SWe3_ball1_fps24_93f_s5": 4.29,
        "v8_SWe7_ball1_fps24_93f_s3": 2.49,
        "v8_SWe7_ball1_fps24_93f_s5": 1.28,
        "v8_SWl7_ball1_fps24_93f_s3": 1.79,
        "v8_SWl7_ball1_fps24_93f_s5": 0.57,
        "v8_SWl17_ball1_fps24_93f_s3": 3.62,
        "v8_SWl17_ball1_fps24_93f_s5": 3.63
    }
    
    concordance = {}
    for name, auth_val in author_v8_reported.items():
        comp_val = clip_results[name]["last20"]
        delta = round(comp_val - auth_val, 3)
        concordance[name] = {
            "reported_last20": auth_val,
            "replicated_last20": comp_val,
            "delta": delta,
            "exact_match": abs(delta) < 0.015
        }
        
    summary = {
        "n_v8_clips": len(clip_results),
        "v8_concordance": concordance,
        "v8_perfect_matches": sum(1 for v in concordance.values() if v["exact_match"]),
        "repo_evidence_audit": {
            "eye_codes_csv_v8_rows": len(v8_rows),
            "eye_codes_csv_v9_rows": len(v9_rows),
            "cause_v9_exists_in_repo": cause_v9_exists,
            "jobs_v9_jsonl_exists": os.path.exists(os.path.join(cause_v8_dir, "jobs_v9.jsonl"))
        },
        "clip_measurements": clip_results
    }
    
    out_json = os.path.join(out_dir, "replication_results.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote full replication and audit ledger to {out_json}")

if __name__ == "__main__":
    main()
