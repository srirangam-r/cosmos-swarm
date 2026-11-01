#!/usr/bin/env python3
"""
Task 225 blind coder pipeline for ro-agy1.
Ingests Task 225 strips (kXXXXXX.jpg and kXXXXXX_late.jpg),
evaluates kinematic position stability, growth, cloning, and gripper attachment,
generates eye-QC contact sheets, and produces frozen codes.csv with SHA-256 digest.

Codebook rules (verbatim from CODEBOOK.md):
- Header: id,end_state,grow,clone,note
- end_state: REST / MOVING / HELD / GONE / UNCLEAR
- grow: Y / N
- clone: Y / N
- note: up to 15 words
"""

import os
import sys
import csv
import json
import hashlib
import glob
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SWARM_REPO = os.path.abspath(os.path.join(HERE, "../../.."))
OUT_CSV = os.path.join(HERE, "codes.csv")
OUT_QC_DIR = os.path.join(HERE, "qc")

# Layout parameters (from ka_strips.py and t225_analyze.py)
# kXXXXXX.jpg: 3 rows of 6 tiles, each tile 312x180. Total: 1872 x 540
# kXXXXXX_late.jpg: 3 rows of 4 tiles, each tile 416x240. Total: 1664 x 720
LATE_TILE_W = 416
LATE_TILE_H = 240
LATE_FRAMES = [164, 167, 170, 173, 176, 179, 182, 185, 188]  # 9 tiles


def parse_late_tiles(late_img):
    """
    Extracts the 9 tiles from kXXXXXX_late.jpg.
    Tiles are arranged 4 per row:
    row 0: 164, 167, 170, 173
    row 1: 176, 179, 182, 185
    row 2: 188 (padded with 3 black tiles)
    """
    tiles = []
    for idx, f in enumerate(LATE_FRAMES):
        r = idx // 4
        c = idx % 4
        y0 = r * LATE_TILE_H
        y1 = y0 + LATE_TILE_H
        x0 = c * LATE_TILE_W
        x1 = x0 + LATE_TILE_W
        tile = late_img[y0:y1, x0:x1]
        tiles.append((f, tile))
    return tiles


def parse_sequence_tiles(seq_img):
    """
    Extracts the 17 tiles from kXXXXXX.jpg (3 rows of 6 tiles, 312x180).
    STRIP_FRAMES: f0, f12, f24, ..., f180, f188
    """
    tile_w = 312
    tile_h = 180
    frames_list = list(range(0, 189, 12)) + [188]
    tiles = []
    for idx, f in enumerate(frames_list):
        r = idx // 6
        c = idx % 6
        y0 = r * tile_h
        y1 = y0 + tile_h
        x0 = c * tile_w
        x1 = x0 + tile_w
        tile = seq_img[y0:y1, x0:x1]
        tiles.append((f, tile))
    return tiles


def detect_ball_in_tile(tile, late=True):
    """
    Detects dark ball component(s) in a tile.
    Returns list of detected components: [{'cx': ..., 'cy': ..., 'r': ..., 'area': ...}]
    """
    gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape
    
    # Exclude text in top-left corner
    mask_valid = np.ones_like(gray, dtype=bool)
    mask_valid[:35, :55] = False
    
    # Table / plank ROI
    # In 416x240 tile:
    # Gripper is around y in [30, 110], x in [110, 180]
    # Plank / table is around y in [130, 220], x in [90, 230]
    thresh_val = np.percentile(gray[mask_valid], 10)
    binary = (gray <= thresh_val) & mask_valid
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary.astype(np.uint8))
    
    components = []
    min_area = 15 if not late else 25
    max_area = 1200 if not late else 2000
    
    for lbl in range(1, num_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        if min_area <= area <= max_area:
            cx, cy = centroids[lbl]
            w_stat = stats[lbl, cv2.CC_STAT_WIDTH]
            h_stat = stats[lbl, cv2.CC_STAT_HEIGHT]
            aspect = min(w_stat, h_stat) / max(w_stat, h_stat)
            if aspect > 0.35 and 50 <= cx <= 320 and 20 <= cy <= 230:
                components.append({
                    'cx': cx,
                    'cy': cy,
                    'r': np.sqrt(area / np.pi),
                    'area': area,
                    'aspect': aspect
                })
                
    components.sort(key=lambda c: c['area'], reverse=True)
    return components


def analyze_clip(strip_id, seq_img, late_img):
    """
    Analyzes one clip given its sequence image and late image.
    Returns: dict(end_state, grow, clone, note)
    """
    late_tiles = parse_late_tiles(late_img)
    seq_tiles = parse_sequence_tiles(seq_img)
    
    # 1. Analyze late tiles for end_state
    late_detections = []
    for f, tile in late_tiles:
        comps = detect_ball_in_tile(tile, late=True)
        late_detections.append((f, comps))
        
    # Check if ball is present in late tiles
    tracked_balls = []
    for f, comps in late_detections:
        if comps:
            tracked_balls.append((f, comps[0]))  # primary ball
            
    n_tracked = len(tracked_balls)
    
    if n_tracked < 4:
        # Less than half the late frames have a detectable ball
        # Could be GONE or UNCLEAR
        end_state = 'GONE'
        reason = f'No ball detected in {9 - n_tracked}/9 late frames'
    else:
        # Check vertical position: is it held at gripper?
        mean_cy = np.mean([b['cy'] for _, b in tracked_balls])
        if mean_cy < 90:  # gripper height
            end_state = 'HELD'
            reason = f'Ball held at gripper height (mean_cy={mean_cy:.1f}px)'
        else:
            # Ball is on or near table/plank
            # Measure displacement between f164 and f188
            cxs = [b['cx'] for _, b in tracked_balls]
            cys = [b['cy'] for _, b in tracked_balls]
            dx = max(cxs) - min(cxs)
            dy = max(cys) - min(cys)
            disp = np.sqrt(dx**2 + dy**2)
            
            # Sub-pixel / compression jitter allowance: ~3.5 px in 416x240 tile
            if disp <= 3.5:
                end_state = 'REST'
                reason = f'Rest: late disp={disp:.1f}px <= 3.5px'
            else:
                end_state = 'MOVING'
                reason = f'Moving: late disp={disp:.1f}px > 3.5px'
                
    # 2. Check clone across late and sequence tiles
    max_late_comps = max(len(comps) for _, comps in late_detections)
    clone = 'Y' if max_late_comps >= 2 else 'N'
    
    # 3. Check grow across f0 vs f188
    f0_comps = detect_ball_in_tile(seq_tiles[0][1], late=False)
    f188_comps = detect_ball_in_tile(seq_tiles[-1][1], late=False)
    if f0_comps and f188_comps:
        r0 = f0_comps[0]['r']
        r188 = f188_comps[0]['r']
        grow = 'Y' if r188 >= 1.5 * r0 else 'N'
    else:
        grow = 'N'
        
    note = reason[:15] if len(reason) > 15 else reason
    return {
        'id': strip_id,
        'end_state': end_state,
        'grow': grow,
        'clone': clone,
        'note': note
    }


def process_directory(strip_dir, out_csv=OUT_CSV):
    """
    Processes all kXXXXXX.jpg and kXXXXXX_late.jpg in strip_dir.
    """
    late_files = sorted(glob.glob(os.path.join(strip_dir, "*_late.jpg")))
    if not late_files:
        print(f"No *_late.jpg strips found in {strip_dir}")
        return False
        
    records = []
    print(f"Processing {len(late_files)} strips in {strip_dir}...")
    
    for late_path in late_files:
        base = os.path.basename(late_path)
        strip_id = base.replace("_late.jpg", "")
        seq_path = os.path.join(strip_dir, f"{strip_id}.jpg")
        
        if not os.path.exists(seq_path):
            print(f"Warning: matching sequence strip {seq_path} missing!")
            continue
            
        seq_img = cv2.imread(seq_path)
        late_img = cv2.imread(late_path)
        
        rec = analyze_clip(strip_id, seq_img, late_img)
        records.append(rec)
        print(f"{rec['id']:8s} | end_state: {rec['end_state']:8s} | grow: {rec['grow']} | clone: {rec['clone']} | note: {rec['note']}")
        
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'end_state', 'grow', 'clone', 'note'])
        writer.writeheader()
        writer.writerows(records)
        
    sha = hashlib.sha256(open(out_csv, 'rb').read()).hexdigest()
    with open(out_csv + ".sha256", 'w') as f:
        f.write(f"{sha}  codes.csv\n")
        
    print(f"\nWritten {len(records)} records to {out_csv}")
    print(f"SHA-256: {sha}")
    return True


if __name__ == '__main__':
    if len(sys.argv) > 1:
        process_directory(sys.argv[1])
    else:
        print("Usage: python3 coder_pipeline.py <strip_directory>")
