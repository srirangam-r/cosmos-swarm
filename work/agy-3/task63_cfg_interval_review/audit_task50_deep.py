import cv2
import numpy as np
import json
from pathlib import Path

def analyze_clip(path):
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        frames.append(f)
    cap.release()
    
    fn = Path(path).name
    f0 = frames[0]
    f0_gray = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    
    frame_stats = []
    for i, f in enumerate(frames):
        diff = cv2.absdiff(f0, f)
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        
        # Upper Gripper / Holder ROI: y in [120, 185], x in [270, 330]
        # Lower Drop Corridor ROI: y in [200, 350], x in [260, 340]
        # Plank Contact ROI: y in [340, 380], x in [260, 340]
        g_diff = float(diff[120:185, 270:330].mean())
        c_diff = float(diff[200:350, 260:340].mean())
        p_diff = float(diff[340:380, 260:340].mean())
        
        # Dark pixel segmentation (threshold < 35) in vertical strip y in [100, 380], x in [250, 360]
        roi = gray[100:380, 250:360]
        dark = (roi < 35).astype(np.uint8)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dark)
        
        blobs = []
        for l in range(1, num_labels):
            x, y, w, h, area = stats[l]
            if area >= 60:
                cx, cy = centroids[l]
                blobs.append({
                    "label": int(l),
                    "cy": round(float(100 + cy), 1),
                    "cx": round(float(250 + cx), 1),
                    "w": int(w),
                    "h": int(h),
                    "area": int(area),
                    "ymin": int(100 + y),
                    "ymax": int(100 + y + h),
                    "in_gripper": bool(120 <= (100 + cy) <= 190),
                    "in_corridor": bool(190 < (100 + cy) <= 340),
                    "at_plank": bool((100 + cy) > 340)
                })
                
        # Count blobs in gripper vs in corridor
        n_grip = sum(1 for b in blobs if b["in_gripper"])
        n_corr = sum(1 for b in blobs if b["in_corridor"])
        n_plank = sum(1 for b in blobs if b["at_plank"])
        
        frame_stats.append({
            "frame": i,
            "g_diff": round(g_diff, 2),
            "c_diff": round(c_diff, 2),
            "p_diff": round(p_diff, 2),
            "n_blobs": len(blobs),
            "n_grip": n_grip,
            "n_corr": n_corr,
            "n_plank": n_plank,
            "blobs": blobs
        })
        
    return {
        "clip": fn,
        "n_frames": len(frames),
        "frame_stats": frame_stats
    }

def main():
    clips = ["base_s1.mp4", "full_s1.mp4", "window_s1.mp4", "base_s2.mp4", "full_s2.mp4", "window_s2.mp4"]
    results = {}
    base_dir = Path("/home/nail/swarm-work/agy-3/task50_review")
    
    for c in clips:
        p = base_dir / c
        print(f"Processing {c}...")
        res = analyze_clip(p)
        results[c] = res
        
    out_json = base_dir / "audit_task50_stats.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved stats to {out_json}")

if __name__ == "__main__":
    main()
