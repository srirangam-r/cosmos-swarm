#!/usr/bin/env python3
"""
Generate visual comparison contact sheets showing Base F vs Rule R vs Count-Only vs QT
across native frames t = 0, 16, 32, 48, 64, 76, 84, 92.
"""

import os
import json
import cv2
import numpy as np

def make_comparisons(base_dir):
    clips_dir = os.path.join(base_dir, "clips")
    out_dir = os.path.join(base_dir, "comparison_sheets")
    os.makedirs(out_dir, exist_ok=True)
    
    # Target frames to display
    sample_frames = [0, 16, 32, 48, 64, 76, 84, 92]
    
    # We compare arms across Ball 1 (s31, s33) and Ball 2 (s31, s33)
    arms = ["F", "CO", "QTnc", "QT", "R"]
    arm_labels = {
        "F": "Base Prompt (F)",
        "CO": "Count-Only (CO)",
        "QTnc": "Persistence No-Count (QTnc)",
        "QT": "Full Timed-Settle (QT)",
        "R": "Canonical Rule R (R)"
    }
    
    for ball in ["ball1", "ball2"]:
        for seed in [31, 33]:
            rows = []
            for arm in arms:
                mp4_path = os.path.join(clips_dir, f"t138_{arm}_{ball}_s{seed}.mp4")
                if not os.path.exists(mp4_path):
                    continue
                cap = cv2.VideoCapture(mp4_path)
                frames = []
                while True:
                    ret, f = cap.read()
                    if not ret: break
                    frames.append(f)
                cap.release()
                
                # Create row
                tiles = []
                for t in sample_frames:
                    # Crop to corridor: y in [80:420], x in [180:420] -> 340 x 240
                    crop = frames[t][80:420, 180:420]
                    tile = cv2.resize(crop, (150, 210))
                    cv2.putText(tile, f"f{t}", (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    tiles.append(tile)
                    
                row_img = np.hstack(tiles)
                # Add label banner on left
                banner = np.zeros((210, 260, 3), dtype=np.uint8)
                cv2.putText(banner, f"{arm}: {arm_labels[arm][:18]}", (8, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
                cv2.putText(banner, f"{ball} seed {seed}", (8, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1)
                
                labeled_row = np.hstack([banner, row_img])
                rows.append(labeled_row)
                
            if rows:
                sheet = np.vstack(rows)
                out_path = os.path.join(out_dir, f"comparison_{ball}_seed{seed}.jpg")
                cv2.imwrite(out_path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
                print(f"Saved {out_path}")

if __name__ == "__main__":
    make_comparisons("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation")
