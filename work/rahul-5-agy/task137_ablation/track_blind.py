#!/usr/bin/env python3
"""
Track ball trajectory and contact states for blind clips blind_01 to blind_30.
"""

import os
import sys
import glob
import json
import cv2
import numpy as np

def analyze_blind_clips(blind_dir, out_json):
    clips_dir = os.path.join(blind_dir, "clips")
    mp4s = sorted(glob.glob(os.path.join(clips_dir, "blind_*.mp4")))
    
    results = {}
    
    for p in mp4s:
        blind_id = os.path.basename(p)[:-4]
        cap = cv2.VideoCapture(p)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        n_frames = len(frames)
        
        # Track ball centroid in corridor crop: y in [100:400], x in [200:400]
        # Using background subtraction against temporal median
        grays = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
        bg = np.median(np.stack(grays), axis=0).astype(np.uint8)
        
        traj = []
        ball_radii = []
        
        for t in range(n_frames):
            diff = cv2.absdiff(grays[t], bg)
            # Crop to corridor
            crop_diff = diff[100:400, 200:400]
            _, thresh = cv2.threshold(crop_diff, 25, 255, cv2.THRESH_BINARY)
            
            # Find largest component
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
            if num_labels > 1:
                # Exclude background label 0
                areas = stats[1:, cv2.CC_STAT_AREA]
                max_idx = 1 + np.argmax(areas)
                area = stats[max_idx, cv2.CC_STAT_AREA]
                cx = centroids[max_idx][0] + 200
                cy = centroids[max_idx][1] + 100
                traj.append((round(float(cx), 2), round(float(cy), 2), int(area)))
            else:
                traj.append((None, None, 0))
                
        # Analyze motion over the terminal window (last 24 frames, t=69..92)
        # Check plank region: y >= 320
        # Terminal motion energy in ball crop
        last12_y = [pos[1] for pos in traj[-12:] if pos[1] is not None]
        last12_y_std = float(np.std(last12_y)) if len(last12_y) >= 6 else 999.0
        
        # Check airborne hops in last 12 frames:
        # A hop has vertical displacement > 15 px above plank resting level (~335-345)
        # Check max height in last 12 frames
        min_y_last12 = min(last12_y) if last12_y else 0 # lower y means higher in air
        max_y_last12 = max(last12_y) if last12_y else 0
        hop_range_last12 = max_y_last12 - min_y_last12 if last12_y else 999.0
        
        results[blind_id] = {
            "blind_id": blind_id,
            "last12_y_std": round(last12_y_std, 2),
            "hop_range_last12": round(hop_range_last12, 2),
            "min_y_last12": round(min_y_last12, 2),
            "max_y_last12": round(max_y_last12, 2),
            "terminal_y_sample": [pos[1] for pos in traj[-12:]],
            "traj_sample_f0_f92_every_4": [traj[t] for t in range(0, 93, 4)]
        }
        
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Tracked {len(results)} clips -> {out_json}")

if __name__ == "__main__":
    analyze_blind_clips(sys.argv[1], sys.argv[2])
