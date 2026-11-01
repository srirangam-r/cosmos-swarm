#!/usr/bin/env python3
"""
Process Seed 4 clips: create contact strips, run firstfall kinematics, and compute metrics.
"""
import json
import cv2
import numpy as np
from pathlib import Path
import subprocess

DIR = Path(__file__).parent / "results"

def make_strip(video_path, out_path, frames_idx=[0, 8, 16, 24, 32, 48, 64, 80, 92]):
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    idx = 0
    selected = {}
    while True:
        ret, f = cap.read()
        if not ret:
            break
        if idx in frames_idx:
            # Crop to relevant region or resize
            # GAUGE 832x480: crop x:200..450, y:60..420
            crop = f[60:420, 200:450]
            # put text of frame number
            cv2.putText(crop, f"f{idx}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            selected[idx] = crop
        idx += 1
    cap.release()
    
    strip_frames = [selected[i] for i in frames_idx if i in selected]
    if strip_frames:
        strip = np.concatenate(strip_frames, axis=1)
        cv2.imwrite(str(out_path), strip)
        print(f"Wrote strip to {out_path}")

def run_firstfall(video_path):
    cmd = [
        "/home/rohith/swarm-work/ro-3/venv/bin/python",
        "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/tools/realball/firstfall.py",
        str(video_path),
        "--ppm", "719.8",
        "--fps", "24"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        return {
            "flag": data.get("flag"),
            "g": data.get("g"),
            "r2": data.get("r2"),
            "fall_px": data.get("fall_px"),
            "n_fit": data.get("n_fit")
        }
    except Exception as e:
        return {"error": str(e), "raw": res.stdout[:200]}

def main():
    ctrl_mp4 = DIR / "gauge_b1_ctrl_s4.mp4"
    rope_mp4 = DIR / "gauge_b1_rope07_s4.mp4"
    
    results = {}
    if ctrl_mp4.exists():
        make_strip(ctrl_mp4, DIR / "gauge_b1_ctrl_s4_strip.jpg")
        results["ctrl_s4"] = run_firstfall(ctrl_mp4)
    if rope_mp4.exists():
        make_strip(rope_mp4, DIR / "gauge_b1_rope07_s4_strip.jpg")
        results["rope07_s4"] = run_firstfall(rope_mp4)
        
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
