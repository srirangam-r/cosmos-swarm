import cv2
import numpy as np
import os
import json

# Inspect cause_v7 strips
strip_dir = "/home/nail/swarm-work/agy-2/cosmos-swarm/work/ro-1/cause_v7/strips"
out_dir = "/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task129_scout_hypotheses/sheets"
os.makedirs(out_dir, exist_ok=True)

# Let's inspect v7_REC_ball2_fps24_93f_s1.strip.jpg
# 8 cols x 4 rows, each tile 110x135. frames 0, 3, 6, 9...
def parse_strip(path):
    img = cv2.imread(path)
    tiles = []
    for r in range(4):
        for c in range(8):
            f_idx = (r * 8 + c) * 3
            if f_idx <= 92:
                tile = img[r*135:(r+1)*135, c*110:(c+1)*110]
                tiles.append((f_idx, tile))
    return tiles

strips = {
    "ball2_s1": os.path.join(strip_dir, "v7_REC_ball2_fps24_93f_s1.strip.jpg"),
    "ball2_s2": os.path.join(strip_dir, "v7_REC_ball2_fps24_93f_s2.strip.jpg"),
    "ball1_s3": os.path.join(strip_dir, "v7_REC_ball1_fps24_93f_s3.strip.jpg"),
    "ball2_s3": os.path.join(strip_dir, "v7_REC_ball2_fps24_93f_s3.strip.jpg"),
    "rect_ball2_s1": os.path.join(strip_dir, "v7_RECT_ball2_fps24_93f_s1.strip.jpg"),
    "rect_ball2_s2": os.path.join(strip_dir, "v7_RECT_ball2_fps24_93f_s2.strip.jpg"),
    "rect_ball1_s3": os.path.join(strip_dir, "v7_RECT_ball1_fps24_93f_s3.strip.jpg"),
    "rect_ball2_s3": os.path.join(strip_dir, "v7_RECT_ball2_fps24_93f_s3.strip.jpg"),
}

print("Loaded strip parser. Processing strips...")
for name, p in strips.items():
    if os.path.exists(p):
        tiles = parse_strip(p)
        print(f"{name}: {len(tiles)} frames extracted.")
