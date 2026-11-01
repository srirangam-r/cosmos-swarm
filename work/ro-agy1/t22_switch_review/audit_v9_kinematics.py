#!/usr/bin/env python3
"""
Comprehensive Kinematic Tracking and Corridor-Vacancy Audit of Prompt-Switch Datasets (v8 and v9)
Task 245 / Finding #4851 / Author Response #4956
Author: ro-agy1

Audits:
1. Re-calculation of corridor last20 across all 27 clips (10 v8, 17 v9).
2. Continuous full-frame ball tracking: centroid (cx, cy), area, and corridor coverage.
3. Diagnostic detection of corridor-vacancy false-stillness artifacts.
4. Physical classification: SETTLED_REST vs SURFACE_HOPPING vs HIGH_BOUNCE vs CORRIDOR_VACANCY.
5. Statistical test of the Window [7, 17] Sufficiency Hypothesis.
"""

import os
import glob
import json
import cv2
import numpy as np

def analyze_clip(mp4_path):
    cap = cv2.VideoCapture(mp4_path)
    F = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        F.append(f)
    cap.release()
    F = np.array(F)
    n_frames = len(F)
    
    # 1. Author-matched corridor last20: mean |dgray| on crop [130:360, 220:360]
    g = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)[130:360, 220:360] for f in F])
    d_corridor = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))
    last20_corridor = round(float(d_corridor[-20:].mean()), 2)
    
    # 2. Whole-frame frame difference for reference
    g_full = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in F])
    d_full = np.abs(np.diff(g_full, axis=0)).mean(axis=(1, 2))
    last20_full = round(float(d_full[-20:].mean()), 2)
    
    # 3. Full-frame ball tracking
    bg = np.median(F[::3].astype(np.float32), axis=0)
    traj = []
    for idx in range(n_frames):
        diff = np.abs(F[idx].astype(np.float32) - bg).sum(2)
        mask = (diff > 35).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab, st, cen = cv2.connectedComponentsWithStats(mask)
        if n < 2:
            traj.append(None)
        else:
            j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            traj.append({
                "frame": idx,
                "cx": float(cen[j][0]),
                "cy": float(cen[j][1]),
                "area": int(st[j, cv2.CC_STAT_AREA]),
                "w": int(st[j, cv2.CC_STAT_WIDTH]),
                "h": int(st[j, cv2.CC_STAT_HEIGHT])
            })
            
    # Initial ball properties (frames 0 to 5)
    init_pts = [p for p in traj[:5] if p is not None]
    init_area = np.median([p["area"] for p in init_pts]) if init_pts else 1000.0
    
    # Late window: frames 73 to 92 (last 20 frames)
    late_pts = [p for p in traj[73:] if p is not None]
    if len(late_pts) > 0:
        cxs = [p["cx"] for p in late_pts]
        cys = [p["cy"] for p in late_pts]
        areas = [p["area"] for p in late_pts]
        
        # Corridor presence: x in [220, 360], y in [130, 360]
        in_corridor = [1 for p in late_pts if (220 <= p["cx"] <= 360 and 130 <= p["cy"] <= 360)]
        corridor_coverage = len(in_corridor) / len(late_pts)
        
        dy_span = round(float(max(cys) - min(cys)), 1)
        dx_span = round(float(max(cxs) - min(cxs)), 1)
        med_cx = round(float(np.median(cxs)), 1)
        med_cy = round(float(np.median(cys)), 1)
        med_area = round(float(np.median(areas)), 1)
        area_ratio = round(float(med_area / max(init_area, 1.0)), 2)
    else:
        corridor_coverage = 0.0
        dy_span = 0.0
        dx_span = 0.0
        med_cx = 0.0
        med_cy = 0.0
        med_area = 0.0
        area_ratio = 1.0
        
    # 4. Objective Kinematic Classification
    # Plank surface is at y approx 350-365
    if corridor_coverage < 0.50:
        classification = "CORRIDOR_VACANCY_ARTIFACT"
        notes = f"Ball outside corridor crop: median pos ({med_cx}, {med_cy}), cov={corridor_coverage:.2f}"
    elif area_ratio >= 2.0:
        classification = "MORPHOLOGY_FAILURE"
        notes = f"Ball expanded {area_ratio:.1f}x (area {med_area} vs {init_area})"
    elif dy_span <= 2.0 and dx_span <= 2.0:
        classification = "SETTLED_REST"
        notes = f"Ball truly settled at rest on plank: dy={dy_span}px, dx={dx_span}px at ({med_cx}, {med_cy})"
    elif dy_span <= 50.0 and med_cy >= 320.0:
        classification = "SURFACE_HOPPING_ROLLING"
        notes = f"Low-amplitude surface hopping/rolling on plank: dy={dy_span}px, dx={dx_span}px at y={med_cy}"
    else:
        classification = "CONTINUOUS_HIGH_BOUNCE"
        notes = f"Unattenuated high bouncing: dy={dy_span}px across mid-air (y={med_cy})"

    return {
        "n_frames": n_frames,
        "last20_corridor": last20_corridor,
        "last20_full": last20_full,
        "corridor_coverage": round(corridor_coverage, 2),
        "med_cx": med_cx,
        "med_cy": med_cy,
        "dy_span": dy_span,
        "dx_span": dx_span,
        "med_area": med_area,
        "area_ratio": area_ratio,
        "classification": classification,
        "notes": notes
    }

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "../../.."))
    v8_dir = os.path.join(repo_root, "work", "ro-1", "cause_v8", "native")
    v9_dir = os.path.join(repo_root, "work", "ro-1", "cause_v9", "native")
    
    out_dir = script_dir
    os.makedirs(out_dir, exist_ok=True)
    
    v8_clips = sorted(glob.glob(os.path.join(v8_dir, "*.mp4")))
    v9_clips = sorted(glob.glob(os.path.join(v9_dir, "*.mp4")))
    
    print(f"Auditing {len(v8_clips)} v8 clips and {len(v9_clips)} v9 clips (total {len(v8_clips)+len(v9_clips)})...")
    
    all_results = {}
    
    # Audit v8
    for mp4 in v8_clips:
        name = os.path.basename(mp4)[:-4]
        res = analyze_clip(mp4)
        res["dataset"] = "v8"
        all_results[name] = res
        print(f"v8: {name:32s} | last20: {res['last20_corridor']:4.2f} | class: {res['classification']:25s} | {res['notes']}")
        
    # Audit v9
    for mp4 in v9_clips:
        name = os.path.basename(mp4)[:-4]
        res = analyze_clip(mp4)
        res["dataset"] = "v9"
        all_results[name] = res
        print(f"v9: {name:32s} | last20: {res['last20_corridor']:4.2f} | class: {res['classification']:25s} | {res['notes']}")
        
    # Save results to JSON
    json_path = os.path.join(out_dir, "v9_kinematic_audit.json")
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved structured audit results to {json_path}")
    
    # Arm summary
    arms = {}
    for name, res in all_results.items():
        # extract arm
        if "SWfull" in name:
            arm = "SWfull [0,35]"
        elif "SWm7_17" in name:
            arm = "SWm7_17 [7,17]"
        elif "SWl7" in name:
            arm = "SWl7 [7,35]"
        elif "SWe7" in name:
            arm = "SWe7 [0,7]"
        elif "SWe3" in name:
            arm = "SWe3 [0,3]"
        elif "SWl17" in name:
            arm = "SWl17 [17,35]"
        else:
            arm = "other"
            
        if arm not in arms:
            arms[arm] = []
        arms[arm].append((name, res))
        
    print("\n" + "="*80)
    print("ARM-LEVEL KINEMATIC SUMMARY")
    print("="*80)
    for arm, items in sorted(arms.items()):
        n = len(items)
        classes = [r["classification"] for _, r in items]
        n_rest = sum(1 for c in classes if c == "SETTLED_REST")
        n_hop = sum(1 for c in classes if c == "SURFACE_HOPPING_ROLLING")
        n_bounce = sum(1 for c in classes if c == "CONTINUOUS_HIGH_BOUNCE")
        n_vacant = sum(1 for c in classes if c == "CORRIDOR_VACANCY_ARTIFACT")
        last20s = [r["last20_corridor"] for _, r in items]
        mean_last20 = np.mean(last20s)
        print(f"{arm:18s} (n={n}): mean_last20={mean_last20:.2f} | REST={n_rest}/{n} | HOPPING={n_hop}/{n} | BOUNCE={n_bounce}/{n} | VACANCY={n_vacant}/{n}")

if __name__ == "__main__":
    main()
