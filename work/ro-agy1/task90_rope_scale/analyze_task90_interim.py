#!/usr/bin/env python3
"""
Task 90: Interim Kinematic and Visual Analysis of RoPE Early Spatial Frequency Scaling.
Hypothesis: Scaling RoPE height/width spatial frequencies by 0.7 for t >= 900 breaks the
mechanical gripper lock on GAUGE Ball 1 Frame 0 without changing the input image.
"""
import json
from pathlib import Path
import cv2
import numpy as np

RESULTS_DIR = Path(__file__).parent / "results"

def analyze_all():
    summary = {}
    for json_path in sorted(RESULTS_DIR.glob("*.json")):
        if json_path.name in ["scores_partial.json", "experiment_manifest.json"]:
            continue
        with open(json_path) as f:
            meta = json.load(f)
        clip_name = meta["clip"]
        mp4_path = RESULTS_DIR / clip_name
        if not mp4_path.exists():
            continue
        
        # Check ROI occupancy across frames
        cap = cv2.VideoCapture(str(mp4_path))
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        # In GAUGE ball 1, held ball sits at x: 270..295, y: 80..115
        # Fall corridor sits at x: 260..305, y: 140..350
        # Plank surface sits at y: 350..390
        held_counts = []
        corridor_counts = []
        plank_counts = []
        for fidx in range(0, len(frames), 5):
            f = frames[fidx]
            gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            held_dark = int(np.sum(gray[80:120, 270:295] < 70))
            corr_dark = int(np.sum(gray[140:340, 260:305] < 70))
            plank_dark = int(np.sum(gray[350:390, 250:320] < 70))
            held_counts.append(held_dark)
            corridor_counts.append(corr_dark)
            plank_counts.append(plank_dark)
            
        summary[clip_name] = {
            "seed": meta.get("seed"),
            "early_scale": meta.get("early_scale"),
            "frames": len(frames),
            "held_dark_f0": held_counts[0] if held_counts else 0,
            "held_dark_fmid": held_counts[len(held_counts)//2] if held_counts else 0,
            "held_dark_fend": held_counts[-1] if held_counts else 0,
            "corridor_max": max(corridor_counts) if corridor_counts else 0,
            "plank_fend": plank_counts[-1] if plank_counts else 0,
        }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    analyze_all()
