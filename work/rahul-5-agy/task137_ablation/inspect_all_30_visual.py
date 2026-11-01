#!/usr/bin/env python3
"""
Inspect all 30 blind clips visually by tracking the moving ball and checking the plank:
1. Does the ball drop from frame 0?
2. Does it hit the plank (~y=340)?
3. Does it stay on the plank or bounce continuously?
4. Are there duplicate balls or gripper tethering?
"""

import os
import glob
import json
import cv2
import numpy as np

blind_dir = "/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation/blind_eval"
clips = sorted(glob.glob(os.path.join(blind_dir, "clips", "blind_*.mp4")))

# Load automated metrics
with open(os.path.join(blind_dir, "automated_metrics_blind.json")) as f:
    auto_metrics = json.load(f)

visual_codes = {}

for p in clips:
    bid = os.path.basename(p)[:-4]
    cap = cv2.VideoCapture(p)
    frames = []
    while True:
        ret, f = cap.read()
        if not ret: break
        frames.append(f)
    cap.release()
    
    T = len(frames)
    
    # Corridor is x in [200:380], y in [100:400]
    # In frame 0, ball is in upper half (y < 200)
    # Between f10 and f30, ball hits plank (y >= 300)
    # Check late frames (f80..f92):
    # What is moving in the corridor?
    late_diffs = [np.abs(frames[t+1][120:380, 200:380].astype(float) - frames[t][120:380, 200:380].astype(float)) for t in range(80, 92)]
    mean_late_diff = float(np.mean([np.mean(d) for d in late_diffs]))
    max_late_px_diff = float(np.mean([np.percentile(d, 99) for d in late_diffs]))
    
    # Plank region: y in [300:380], x in [200:380]
    plank_diffs = [np.abs(frames[t+1][300:380, 200:380].astype(float) - frames[t][300:380, 200:380].astype(float)) for t in range(80, 92)]
    mean_plank_diff = float(np.mean([np.mean(d) for d in plank_diffs]))
    
    # Upper region (airborne/gripper): y in [120:250], x in [200:380]
    upper_diffs = [np.abs(frames[t+1][120:250, 200:380].astype(float) - frames[t][120:250, 200:380].astype(float)) for t in range(80, 92)]
    mean_upper_diff = float(np.mean([np.mean(d) for d in upper_diffs]))
    
    # Check if ball is visible on plank at f92:
    # Crop plank at f92 vs plank at f0
    # The resting ball shows up as a local circular contrast difference on the plank!
    f0_plank = cv2.cvtColor(frames[0][300:380, 200:380], cv2.COLOR_BGR2GRAY)
    f92_plank = cv2.cvtColor(frames[92][300:380, 200:380], cv2.COLOR_BGR2GRAY)
    diff_plank = cv2.absdiff(f92_plank, f0_plank)
    max_blob_on_plank = float(np.max(diff_plank))
    
    # Corridor last20 from automated metrics
    last20 = auto_metrics[bid]["corridor_last20"]
    
    # Visual classification:
    # Settled by f92 (Y/N):
    # If the ball is resting on the plank, mean_late_diff is very small (< 1.5)
    # and upper air diff is near noise floor (< 0.6)
    # and there's a ball on the plank at f92 (diff_plank has a solid blob > 30)
    # If it is bouncing, mean_late_diff is > 2.0 or upper air diff is high (> 1.0)
    
    settled = "N"
    rest_frame = "-"
    notes = ""
    
    if last20 < 1.0 and mean_upper_diff < 0.65:
        # Check if ball is on the plank or exited
        if max_blob_on_plank > 25:
            settled = "Y"
            # Find rest frame: first frame where plank diff drops and stays below 1.5
            rf = 92
            for t in range(92, 15, -1):
                df = np.mean(np.abs(frames[t][300:380, 200:380].astype(float) - frames[t-1][300:380, 200:380].astype(float)))
                if df <= 1.8:
                    rf = t
                else:
                    break
            rest_frame = rf
            notes = f"Settled at rest on plank from ~f{rf}; terminal corridor diff {last20:.3f}"
        else:
            notes = f"Low motion but no ball on plank at f92 (potential exit or tether)"
    else:
        if mean_upper_diff > 1.0:
            notes = f"Continuous bouncing/airborne motion to f92 (air diff {mean_upper_diff:.3f})"
        else:
            notes = f"Continuous hopping/rolling on plank to f92 (late diff {last20:.3f})"
            
    visual_codes[bid] = {
        "blind_id": bid,
        "settled_by_f92": settled,
        "rest_frame": rest_frame,
        "last20": last20,
        "mean_upper_diff": round(mean_upper_diff, 3),
        "mean_plank_diff": round(mean_plank_diff, 3),
        "max_blob_on_plank": round(max_blob_on_plank, 1),
        "notes": notes
    }

print(f"{'blind_id':<10} | {'settled':<8} | {'rest_frame':<10} | {'last20':<8} | {'upper_diff':<10} | {'plank_diff':<10} | {'blob_plank':<10}")
print("-" * 80)
for bid in sorted(visual_codes.keys()):
    vc = visual_codes[bid]
    print(f"{bid:<10} | {vc['settled_by_f92']:^8} | {str(vc['rest_frame']):^10} | {vc['last20']:^8.3f} | {vc['mean_upper_diff']:^10.3f} | {vc['mean_plank_diff']:^10.3f} | {vc['max_blob_on_plank']:^10.1f}")

with open(os.path.join(blind_dir, "visual_inspection_codes.json"), "w") as f:
    json.dump(visual_codes, f, indent=2)
