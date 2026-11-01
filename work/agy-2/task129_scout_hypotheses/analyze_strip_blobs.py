import cv2
import numpy as np
import os
import json

strip_dir = "/home/nail/swarm-work/agy-2/cosmos-swarm/work/ro-1/cause_v7/strips"

def analyze_strip(strip_path):
    img = cv2.imread(strip_path)
    results = []
    for r in range(4):
        for c in range(8):
            f_idx = (r * 8 + c) * 3
            if f_idx > 90:
                continue
            tile = img[r*135:(r+1)*135, c*110:(c+1)*110]
            # convert to gray
            gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
            # Plank is light wood, optical table is black/gray perforations, ball is dark
            # Let's threshold dark pixels in the central corridor: x in [20, 90], y in [5, 125]
            roi = gray[5:125, 20:90]
            # Background in tile is roughly 80-140 for wood, <40 for table/ball
            # dark mask: gray < 50
            mask = (roi < 45).astype(np.uint8)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
            blobs = []
            for b in range(1, num_labels):
                area = stats[b, cv2.CC_STAT_AREA]
                if area >= 12: # meaningful object in 0.5x scale
                    bx = centroids[b][0] + 20
                    by = centroids[b][1] + 5
                    bw = stats[b, cv2.CC_STAT_WIDTH]
                    bh = stats[b, cv2.CC_STAT_HEIGHT]
                    # convert back to full frame coordinates
                    orig_x = 180 + bx * 2.0
                    orig_y = 110 + by * 2.0
                    blobs.append({
                        "tile_x": float(bx), "tile_y": float(by),
                        "orig_x": float(orig_x), "orig_y": float(orig_y),
                        "area": int(area), "w": int(bw), "h": int(bh)
                    })
            results.append({"frame": f_idx, "blobs": blobs})
    return results

rec_b2s1 = analyze_strip(os.path.join(strip_dir, "v7_REC_ball2_fps24_93f_s1.strip.jpg"))
rec_b2s2 = analyze_strip(os.path.join(strip_dir, "v7_REC_ball2_fps24_93f_s2.strip.jpg"))
rec_b1s3 = analyze_strip(os.path.join(strip_dir, "v7_REC_ball1_fps24_93f_s3.strip.jpg"))
rec_b2s3 = analyze_strip(os.path.join(strip_dir, "v7_REC_ball2_fps24_93f_s3.strip.jpg"))

print("=== REC Ball 2 Seed 1 ===")
for r in rec_b2s1:
    if len(r["blobs"]) > 1:
        print(f"Frame {r['frame']}: {len(r['blobs'])} blobs: {[ (b['orig_x'], b['orig_y'], b['area']) for b in r['blobs']]}")

print("\n=== REC Ball 2 Seed 2 ===")
for r in rec_b2s2:
    if len(r["blobs"]) > 1 or r["frame"] in [48, 54, 60, 66]:
        print(f"Frame {r['frame']}: {len(r['blobs'])} blobs: {[ (b['orig_x'], b['orig_y'], b['area']) for b in r['blobs']]}")

print("\n=== REC Ball 1 Seed 3 ===")
for r in rec_b1s3[:10]:
    print(f"Frame {r['frame']}: {len(r['blobs'])} blobs: {[ (b['orig_x'], b['orig_y'], b['area']) for b in r['blobs']]}")

print("\n=== REC Ball 2 Seed 3 ===")
for r in rec_b2s3[:10]:
    print(f"Frame {r['frame']}: {len(r['blobs'])} blobs: {[ (b['orig_x'], b['orig_y'], b['area']) for b in r['blobs']]}")
