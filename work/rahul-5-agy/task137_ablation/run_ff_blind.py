#!/usr/bin/env python3
"""
Run firstfall tracking on all 30 blind clips with both seed points:
ball1: (287, 155)
ball2: (290, 172)
"""

import sys, os, glob, json, cv2, numpy as np
sys.path.insert(0, "/home/sha/devel/cosmos-swarm/tools/realball")
sys.path.insert(0, "/home/sha/devel/cosmos-swarm/tools/trk_ballfall")
import firstfall as ff

blind_dir = "/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task137_ablation/blind_eval"
clips = sorted(glob.glob(os.path.join(blind_dir, "clips", "blind_*.mp4")))

results = {}

for p in clips:
    bid = os.path.basename(p)[:-4]
    cap = cv2.VideoCapture(p)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret: break
        frames.append(frame)
    cap.release()
    F = np.array(frames)
    
    # Try ball 1 seed (287, 155), and ball 2 seed (290, 172)
    # Pick the one that tracks more frames
    cx1, cy1, a1, info1 = ff.track(F, point=(287, 155), pframe=0)
    cx2, cy2, a2, info2 = ff.track(F, point=(290, 172), pframe=0)
    
    ok1 = np.sum(np.isfinite(cy1))
    ok2 = np.sum(np.isfinite(cy2))
    
    if ok1 >= ok2:
        cx, cy, a, pt = cx1, cy1, a1, (287, 155)
    else:
        cx, cy, a, pt = cx2, cy2, a2, (290, 172)
        
    n_tracked = int(np.sum(np.isfinite(cy)))
    
    # Analyze the trajectory:
    # Impacts = local maxima of cy
    # Last 12 frames (frames 81 to 92):
    cy_last12 = cy[81:]
    ok_last12 = np.isfinite(cy_last12)
    n_last12 = int(np.sum(ok_last12))
    
    if n_last12 >= 8:
        vals = cy_last12[ok_last12]
        y_range_l12 = float(np.max(vals) - np.min(vals))
        mean_y_l12 = float(np.mean(vals))
        std_y_l12 = float(np.std(vals))
    else:
        y_range_l12 = None
        mean_y_l12 = None
        std_y_l12 = None
        
    # Check if settled:
    # Rule #2726: in frame on/near plank with no airborne hop for >=12 frames before f92
    # On the plank is cy >= 320. No airborne hop means y_range_l12 <= 10 px.
    settled = False
    rest_frame = None
    if y_range_l12 is not None and y_range_l12 <= 12.0 and mean_y_l12 >= 320.0 and n_last12 == 12:
        settled = True
        # Find first frame of continuous contact
        # Look backwards from frame 92
        rf = 92
        for t in range(92, 10, -1):
            if np.isfinite(cy[t]) and abs(cy[t] - mean_y_l12) <= 12.0:
                rf = t
            else:
                break
        rest_frame = rf
        
    results[bid] = {
        "blind_id": bid,
        "n_tracked": n_tracked,
        "settled": "Y" if settled else "N",
        "rest_frame": rest_frame,
        "y_range_last12": round(y_range_l12, 2) if y_range_l12 is not None else None,
        "mean_y_last12": round(mean_y_l12, 2) if mean_y_l12 is not None else None,
        "cy_80_92": [round(float(y), 1) if np.isfinite(y) else None for y in cy[80:]]
    }

print(f"{'blind_id':<10} | {'tracked':<8} | {'settled':<8} | {'rest_frame':<10} | {'y_range_l12':<12} | {'mean_y_l12':<12}")
print("-" * 75)
for bid in sorted(results.keys()):
    r = results[bid]
    rf_str = str(r['rest_frame']) if r['rest_frame'] is not None else "-"
    yr_str = str(r['y_range_last12']) if r['y_range_last12'] is not None else "-"
    my_str = str(r['mean_y_last12']) if r['mean_y_last12'] is not None else "-"
    print(f"{bid:<10} | {r['n_tracked']:^8} | {r['settled']:^8} | {rf_str:^10} | {yr_str:^12} | {my_str:^12}")

with open(os.path.join(blind_dir, "firstfall_tracks.json"), "w") as f:
    json.dump(results, f, indent=2)
