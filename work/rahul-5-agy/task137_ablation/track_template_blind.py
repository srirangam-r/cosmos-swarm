#!/usr/bin/env python3
"""
Track the ball across all 93 frames using normalized cross-correlation template matching.
Extracts ball template from frame 0 and tracks (x, y, score) across all frames.
"""

import os
import glob
import cv2
import numpy as np
import json

def track_template_blind(blind_dir, out_json):
    clips_dir = os.path.join(blind_dir, "clips")
    mp4s = sorted(glob.glob(os.path.join(clips_dir, "blind_*.mp4")))
    
    results = {}
    
    for p in mp4s:
        bid = os.path.basename(p)[:-4]
        cap = cv2.VideoCapture(p)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret: break
            frames.append(frame)
        cap.release()
        
        # Frame 0 crop of the ball:
        # In GAUGE midfall, the ball is roughly around y=110..180, x=240..310
        # Let's find the circle using HoughCircles or crop a 40x40 box around max saturation/contrast
        f0 = frames[0]
        f0_roi = f0[100:200, 230:330]
        gray_roi = cv2.cvtColor(f0_roi, cv2.COLOR_BGR2GRAY)
        
        # Detect circle in frame 0 ROI
        circles = cv2.HoughCircles(gray_roi, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                                   param1=50, param2=20, minRadius=12, maxRadius=26)
        if circles is not None:
            cx = int(circles[0][0][0]) + 230
            cy = int(circles[0][0][1]) + 100
            r = int(circles[0][0][2])
        else:
            # Fallback to center of ROI
            cx, cy, r = 280, 145, 18
            
        # Extract template
        tmpl = f0[cy-r:cy+r, cx-r:cx+r]
        tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
        th, tw = tmpl_gray.shape
        
        # Track across all frames in search window: y in [80:440], x in [180:440]
        traj = []
        for t, f in enumerate(frames):
            search_roi = cv2.cvtColor(f[80:440, 180:440], cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(search_roi, tmpl_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            bx = max_loc[0] + 180 + tw//2
            by = max_loc[1] + 80 + th//2
            traj.append((t, int(bx), int(by), round(float(max_val), 3)))
            
        # Now analyze trajectory:
        # Find first ground impact: max y in early flight (around f10-f18)
        # Check trajectory in frames 70 to 92 (last 23 frames):
        late_traj = traj[70:]
        late_ys = [pt[2] for pt in late_traj]
        late_xs = [pt[1] for pt in late_traj]
        
        # Check last 12 frames (f81 to f92):
        last12_traj = traj[81:]
        last12_ys = [pt[2] for pt in last12_traj]
        last12_xs = [pt[1] for pt in last12_traj]
        
        y_span_last12 = max(last12_ys) - min(last12_ys)
        x_span_last12 = max(last12_xs) - min(last12_xs)
        mean_y_last12 = np.mean(last12_ys)
        
        # Check airborne hop: if y drops by > 12 px (higher up)
        # Note: plank surface is around y = 330..355
        # If settled, y_span_last12 <= 6 px and mean_y >= 325
        settled_candidate = (y_span_last12 <= 8) and (mean_y_last12 >= 320)
        
        # Find rest frame: look back from f92 to see how long y stays within 6 px of f92 y
        f92_y = traj[92][2]
        rest_frame = 92
        if settled_candidate:
            for t in range(92, 10, -1):
                if abs(traj[t][2] - f92_y) <= 8 and abs(traj[t][1] - traj[92][1]) <= 15:
                    rest_frame = t
                else:
                    break
                    
        results[bid] = {
            "blind_id": bid,
            "f0_pos": (cx, cy),
            "settled_candidate": "Y" if settled_candidate else "N",
            "rest_frame": rest_frame if settled_candidate else None,
            "y_span_last12": y_span_last12,
            "x_span_last12": x_span_last12,
            "mean_y_last12": round(float(mean_y_last12), 1),
            "f92_pos": (traj[92][1], traj[92][2]),
            "traj_last12": [(pt[0], pt[1], pt[2]) for pt in last12_traj]
        }
        
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"{'blind_id':<10} | {'settled':<8} | {'rest_frame':<10} | {'y_span':<8} | {'x_span':<8} | {'mean_y':<8} | {'f92_pos':<12}")
    print("-" * 75)
    for bid in sorted(results.keys()):
        r = results[bid]
        rf = str(r['rest_frame']) if r['rest_frame'] is not None else "-"
        pos_str = f"({r['f92_pos'][0]},{r['f92_pos'][1]})"
        print(f"{bid:<10} | {r['settled_candidate']:^8} | {rf:^10} | {r['y_span_last12']:^8} | {r['x_span_last12']:^8} | {r['mean_y_last12']:^8.1f} | {pos_str:^12}")

if __name__ == "__main__":
    track_template_blind("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation/blind_eval",
                         "/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation/blind_eval/template_tracking.json")
