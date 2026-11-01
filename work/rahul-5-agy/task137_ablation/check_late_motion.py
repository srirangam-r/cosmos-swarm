#!/usr/bin/env python3
"""
Inspect the late frames (f60 to f92) and check ball position and resting status.
"""

import os
import glob
import cv2
import numpy as np

def inspect_late_frames(blind_dir):
    clips_dir = os.path.join(blind_dir, "clips")
    mp4s = sorted(glob.glob(os.path.join(clips_dir, "blind_*.mp4")))
    
    summary = []
    
    for p in mp4s:
        bid = os.path.basename(p)[:-4]
        cap = cv2.VideoCapture(p)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret: break
            frames.append(frame)
        cap.release()
        
        # Check motion on plank region y in [280:400], x in [220:400]
        # over frames 70 to 92 (last 23 frames, > 12 frames)
        plank_crops = [cv2.cvtColor(f[280:400, 220:400], cv2.COLOR_BGR2GRAY) for f in frames]
        late_diffs = [float(np.mean(np.abs(plank_crops[t].astype(float) - plank_crops[t-1].astype(float)))) for t in range(70, 93)]
        max_late_diff = max(late_diffs)
        mean_late_diff = np.mean(late_diffs)
        
        # Whole frame diffs in last 12 frames
        full_diffs = [float(np.mean(np.abs(frames[t].astype(float) - frames[t-1].astype(float)))) for t in range(81, 93)]
        mean_full_last12 = np.mean(full_diffs)
        
        # Detect if ball is at rest on plank:
        # A resting ball on the plank has very low late diffs (< 1.0 or 1.5)
        # whereas a continuously bouncing ball has late diffs > 3.0 or 4.0
        summary.append({
            "blind_id": bid,
            "mean_late_plank_diff": round(mean_late_diff, 3),
            "max_late_plank_diff": round(max_late_diff, 3),
            "mean_full_last12": round(mean_full_last12, 3)
        })
        
    for s in summary:
        print(f"{s['blind_id']}: plank_late_mean={s['mean_late_plank_diff']:.3f}, max={s['max_late_plank_diff']:.3f}, full_last12={s['mean_full_last12']:.3f}")

if __name__ == "__main__":
    inspect_late_frames("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation/blind_eval")
