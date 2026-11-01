#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path
import cv2
import numpy as np

WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[2]
CLIPS_DIR = WORK_DIR / "clips"
STRIPS_DIR = WORK_DIR / "strips"
STRIPS_DIR.mkdir(parents=True, exist_ok=True)

REF_F0_PATH = REPO_ROOT / "work/raj-1/gauge_ball/gauge_ball1_f0_832x480.png"
ref_f0 = cv2.imread(str(REF_F0_PATH))
if ref_f0 is None:
    raise FileNotFoundError(f"Could not load reference frame 0 from {REF_F0_PATH}")

def compute_psnr(img1, img2):
    mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * np.log10(255.0 / np.sqrt(mse))

def generate_strip(frames, out_path):
    idx = list(range(0, min(32, len(frames)))) + list(range(32, len(frames), 4))
    tiles = []
    for t in idx:
        crop = frames[t][60:440, 100:480]
        resized = cv2.resize(crop, (150, 150))
        cv2.putText(resized, str(t), (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        tiles.append(resized)
    # Pad to multiple of 12
    pad_count = (-len(tiles)) % 12
    if pad_count > 0:
        tiles += [np.zeros_like(tiles[0])] * pad_count
    rows = []
    for i in range(0, len(tiles), 12):
        rows.append(np.hstack(tiles[i:i+12]))
    strip_img = np.vstack(rows)
    cv2.imwrite(str(out_path), strip_img, [cv2.IMWRITE_JPEG_QUALITY, 80])

def analyze_clip(mp4_path):
    cap = cv2.VideoCapture(str(mp4_path))
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    
    if len(frames) == 0:
        return {"error": "no_frames"}
    
    # Generate strip
    strip_path = STRIPS_DIR / f"{mp4_path.stem}_strip.jpg"
    generate_strip(frames, strip_path)
    
    # 1. Frame 0 fidelity
    gen_f0 = frames[0]
    psnr = compute_psnr(ref_f0, gen_f0)
    mae = float(np.mean(np.abs(ref_f0.astype(float) - gen_f0.astype(float))))
    max_diff = int(np.max(np.abs(ref_f0.astype(int) - gen_f0.astype(int))))
    
    # 2. Motion / Ball tracking in held position & corridor
    # Held ball in frame 0 is roughly y in [120, 220], x in [240, 320]
    held_roi_f0 = cv2.cvtColor(ref_f0[120:220, 240:320], cv2.COLOR_BGR2GRAY)
    
    # Measure frame-to-frame difference in the held ball region
    held_diffs = []
    for fr in frames[1:]:
        roi = cv2.cvtColor(fr[120:220, 240:320], cv2.COLOR_BGR2GRAY)
        diff = np.mean(np.abs(roi.astype(float) - held_roi_f0.astype(float)))
        held_diffs.append(float(diff))
    
    # Measure change in the falling corridor (y: 220 to 380, x: 240 to 320)
    corridor_diffs = []
    corridor_f0 = cv2.cvtColor(ref_f0[220:380, 240:320], cv2.COLOR_BGR2GRAY)
    for fr in frames:
        c_roi = cv2.cvtColor(fr[220:380, 240:320], cv2.COLOR_BGR2GRAY)
        c_diff = np.mean(np.abs(c_roi.astype(float) - corridor_f0.astype(float)))
        corridor_diffs.append(float(c_diff))
    
    max_corridor_change = float(np.max(corridor_diffs))
    mean_held_change = float(np.mean(held_diffs))
    
    # Detect release: if a significant dark blob moves into the corridor (below y=220)
    # The ball is dark (pixel intensity < 50)
    released = False
    phantom_detected = False
    release_frame = None
    
    for idx, fr in enumerate(frames):
        c_crop = fr[220:380, 230:330]
        # Dark pixels count (< 60 intensity)
        dark_pixels = np.sum(cv2.cvtColor(c_crop, cv2.COLOR_BGR2GRAY) < 60)
        # Background optical table has some dark dots, so check threshold
        if dark_pixels > 800: # Ball area is approx ~1500-2500 px
            released = True
            if release_frame is None:
                release_frame = idx
    
    # Check if ball remained in gripper while phantom spawned (phantom detection)
    late_held_dark = np.sum(cv2.cvtColor(frames[-1][120:220, 240:320], cv2.COLOR_BGR2GRAY) < 60)
    if released and late_held_dark > 1000:
        phantom_detected = True
        
    return {
        "clip": mp4_path.name,
        "n_frames": len(frames),
        "f0_psnr": round(psnr, 2),
        "f0_mae": round(mae, 2),
        "f0_max_diff": max_diff,
        "mean_held_diff": round(mean_held_change, 2),
        "max_corridor_change": round(max_corridor_change, 2),
        "released": released,
        "release_frame": release_frame,
        "phantom_detected": phantom_detected,
        "strip_path": str(strip_path.relative_to(WORK_DIR))
    }

def main():
    clips = sorted(list(CLIPS_DIR.glob("*.mp4")))
    print(f"Found {len(clips)} clips in {CLIPS_DIR}")
    results = {}
    for c in clips:
        print(f"Analyzing {c.name}...")
        res = analyze_clip(c)
        results[c.stem] = res
    
    out_json = WORK_DIR / "analysis_results.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved analysis to {out_json}")

if __name__ == "__main__":
    main()
