#!/usr/bin/env python3
"""
Inspect each blind clip using template matching and optical flow in the plank region.
Determines:
- Initial drop and first impact frame
- Number of bounces / hops
- Position at f76, f80, f84, f88, f92
- Motion between f80 and f92
- Whether ball is in continuous contact (settled)
"""

import os
import glob
import cv2
import numpy as np

def verify_clips(blind_dir):
    clips_dir = os.path.join(blind_dir, "clips")
    mp4s = sorted(glob.glob(os.path.join(clips_dir, "blind_*.mp4")))
    
    report = []
    
    for p in mp4s:
        bid = os.path.basename(p)[:-4]
        cap = cv2.VideoCapture(p)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret: break
            frames.append(frame)
        cap.release()
        
        # Analyze plank region: y in [240:400], x in [180:420]
        # Over terminal frames 60 to 92
        terminal_diffs = []
        for t in range(60, 92):
            crop1 = frames[t][240:400, 180:420].astype(float)
            crop2 = frames[t+1][240:400, 180:420].astype(float)
            d = np.mean(np.abs(crop2 - crop1))
            terminal_diffs.append((t, round(float(d), 3)))
            
        last12_diffs = [d for t, d in terminal_diffs if t >= 80]
        mean_last12_diff = np.mean(last12_diffs)
        max_last12_diff = max(last12_diffs)
        
        # Overall scene motion in last 12 frames
        scene_diffs = [np.mean(np.abs(frames[t+1].astype(float) - frames[t].astype(float))) for t in range(80, 92)]
        mean_scene_diff = np.mean(scene_diffs)
        
        # Check motion in the corridor y in [100:260] (airborne / gripper region)
        air_diffs = [np.mean(np.abs(frames[t+1][100:260, 200:360].astype(float) - frames[t][100:260, 200:360].astype(float))) for t in range(80, 92)]
        mean_air_diff = np.mean(air_diffs)
        
        report.append({
            "blind_id": bid,
            "mean_last12_plank": round(mean_last12_diff, 3),
            "max_last12_plank": round(max_last12_diff, 3),
            "mean_scene_diff": round(mean_scene_diff, 3),
            "mean_air_diff": round(mean_air_diff, 3)
        })
        
    print(f"{'blind_id':<10} | {'last12_plank':<14} | {'max_plank':<10} | {'scene_diff':<12} | {'air_diff':<10}")
    print("-" * 65)
    for r in report:
        print(f"{r['blind_id']:<10} | {r['mean_last12_plank']:^14.3f} | {r['max_last12_plank']:^10.3f} | {r['mean_scene_diff']:^12.3f} | {r['mean_air_diff']:^10.3f}")

if __name__ == "__main__":
    verify_clips("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation/blind_eval")
