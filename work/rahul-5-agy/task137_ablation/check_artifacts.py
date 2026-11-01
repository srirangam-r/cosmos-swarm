#!/usr/bin/env python3
"""
Inspect artifact flags (duplicate, morph, exit, tether) across all 30 blind clips.
"""

import os
import glob
import json
import cv2
import numpy as np

blind_dir = "/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation/blind_eval"
clips = sorted(glob.glob(os.path.join(blind_dir, "clips", "blind_*.mp4")))

artifacts = {}

for p in clips:
    bid = os.path.basename(p)[:-4]
    cap = cv2.VideoCapture(p)
    frames = []
    while True:
        ret, f = cap.read()
        if not ret: break
        frames.append(f)
    cap.release()
    
    # Tether check: does the gripper at the top (y 80-160, x 240-320) keep moving or hold a ball throughout?
    # Tether occurs when the ball is re-lifted or stays in the gripper while a second ball drops
    # Check upper motion after frame 40:
    upper_motion = [np.mean(np.abs(frames[t][80:160, 240:320].astype(float) - frames[t-1][80:160, 240:320].astype(float))) for t in range(40, 93)]
    mean_upper_motion = float(np.mean(upper_motion))
    
    # Exit check: does the ball leave the field of view?
    # Check if plank region at f92 has NO ball (y in [300:400], x in [200:400])
    # and corridor has no ball
    f0_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    f92_gray = cv2.cvtColor(frames[92], cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(f92_gray, f0_gray)
    
    # Check right edge (x > 750) and bottom edge (y > 450) for ball exit
    exit_bottom = float(np.max(diff[450:, 200:400])) > 50
    exit_right = float(np.max(diff[200:400, 750:])) > 50
    
    # Check duplicate ball:
    # Look for two distinct moving centroids in frames 20 to 60
    dup = 0
    tether = 0
    exit_flag = 0
    morph = 0
    
    # If upper motion is high late in the video, check for gripper tethering
    if mean_upper_motion > 1.8:
        tether = 1
        
    artifacts[bid] = {
        "blind_id": bid,
        "mean_upper_motion": round(mean_upper_motion, 3),
        "exit_bottom": exit_bottom,
        "exit_right": exit_right,
        "tether": tether
    }

for bid in sorted(artifacts.keys()):
    a = artifacts[bid]
    print(f"{bid}: upper_motion={a['mean_upper_motion']:.3f}, tether={a['tether']}, exit_b={a['exit_bottom']}, exit_r={a['exit_right']}")
