#!/usr/bin/env python3
"""
Detailed visual audit of all 30 blind clips.
Tracks ball position, detect impacts, hops, and resting frame.
"""

import os
import glob
import cv2
import numpy as np

def detailed_audit(blind_dir):
    clips_dir = os.path.join(blind_dir, "clips")
    mp4s = sorted(glob.glob(os.path.join(clips_dir, "blind_*.mp4")))
    
    findings = {}
    
    for p in mp4s:
        bid = os.path.basename(p)[:-4]
        cap = cv2.VideoCapture(p)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret: break
            frames.append(frame)
        cap.release()
        
        # We track the ball by finding the red/orange/yellow ball in the corridor
        # In GAUGE, the ball is brightly colored (red/orange) against the neutral wooden plank and dark table
        hsv_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in frames]
        
        # Color mask for the ball in HSV
        # Ball is orange/red/brown: H in [0, 25] or [160, 180], S > 50, V > 50
        ball_pos = []
        for t, hsv in enumerate(hsv_frames):
            # Focus on corridor: y in [80:420], x in [180:420]
            crop_hsv = hsv[80:420, 180:420]
            mask1 = cv2.inRange(crop_hsv, np.array([0, 50, 50]), np.array([25, 255, 255]))
            mask2 = cv2.inRange(crop_hsv, np.array([160, 50, 50]), np.array([180, 255, 255]))
            mask = mask1 | mask2
            
            # Find contours
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if cnts:
                # Find contour closest to circular or largest area
                c = max(cnts, key=cv2.contourArea)
                area = cv2.contourArea(c)
                if area > 30: # at least 30 px
                    M = cv2.moments(c)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"]) + 180
                        cy = int(M["m01"] / M["m00"]) + 80
                        ball_pos.append((t, cx, cy, area))
                        continue
            ball_pos.append((t, None, None, 0))
            
        # Inspect ball_pos:
        valid_y = [(t, cy) for t, cx, cy, a in ball_pos if cy is not None]
        
        # Check motion in last 12 frames (t = 81..92)
        last12_y = [cy for t, cy in valid_y if t >= 81]
        
        # Terminal rest detection:
        # A ball is at rest on the plank if:
        # 1. In frame on/near plank (cy around 330-360)
        # 2. No airborne hop for >=12 frames before f92 (dy < 10 px over the last 12 frames, and cy >= 320)
        settled = False
        rest_frame = None
        
        if len(last12_y) >= 8:
            y_range = max(last12_y) - min(last12_y)
            mean_y = np.mean(last12_y)
            if y_range <= 12 and mean_y >= 320:
                settled = True
                # Find first frame where ball settled on plank without leaving
                # Look backwards from f92
                rf = 92
                for t in range(92, 10, -1):
                    # Check if ball at frame t is within 15 px of mean resting y
                    t_pos = [cy for time, cy in valid_y if time == t]
                    if t_pos and abs(t_pos[0] - mean_y) <= 15:
                        rf = t
                    else:
                        break
                rest_frame = rf
                
        # Check for duplicate ball: check if there are 2 large ball-colored components in the corridor
        dup_count = 0
        for t, hsv in enumerate(hsv_frames):
            crop_hsv = hsv[80:420, 180:420]
            mask1 = cv2.inRange(crop_hsv, np.array([0, 50, 50]), np.array([25, 255, 255]))
            mask2 = cv2.inRange(crop_hsv, np.array([160, 50, 50]), np.array([180, 255, 255]))
            mask = mask1 | mask2
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            large_cnts = [c for c in cnts if cv2.contourArea(c) > 60]
            if len(large_cnts) >= 2:
                dup_count += 1
                
        has_dup = 1 if dup_count >= 5 else 0
        
        findings[bid] = {
            "blind_id": bid,
            "settled": "Y" if settled else "N",
            "rest_frame": rest_frame if settled else None,
            "last12_y_range": round(max(last12_y) - min(last12_y), 1) if last12_y else None,
            "last12_mean_y": round(float(np.mean(last12_y)), 1) if last12_y else None,
            "has_duplicate": has_dup,
            "f92_pos": valid_y[-1] if valid_y else None
        }
        
    print(f"{'blind_id':<10} | {'settled':<8} | {'rest_frame':<10} | {'y_range_last12':<15} | {'mean_y_last12':<15} | {'dup':<5}")
    print("-" * 75)
    for bid in sorted(findings.keys()):
        f = findings[bid]
        rf_str = str(f['rest_frame']) if f['rest_frame'] is not None else "-"
        yr_str = str(f['last12_y_range']) if f['last12_y_range'] is not None else "-"
        my_str = str(f['last12_mean_y']) if f['last12_mean_y'] is not None else "-"
        print(f"{bid:<10} | {f['settled']:^8} | {rf_str:^10} | {yr_str:^15} | {my_str:^15} | {f['has_duplicate']:^5}")
        
    return findings

if __name__ == "__main__":
    detailed_audit("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation/blind_eval")
