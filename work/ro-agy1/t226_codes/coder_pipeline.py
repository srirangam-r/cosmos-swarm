#!/usr/bin/env python3
"""
Task 226 blind coder pipeline for ro-agy1.
Ingests randomized-ID strips from work/rahul-api/t226/strips/ and IDS_by_scene.json,
extracts kinematic trajectories from object crops, computes preliminary codes,
supports eye-QC inspection, and exports frozen codes.json with SHA-256 verification.

Code menu (verbatim from PREREG.md):
- P: SWING / STILL / OTHER
- F, H: DOWN / UP / STILL / OTHER
"""

import os
import sys
import json
import hashlib
import glob
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SWARM_REPO = os.path.abspath(os.path.join(HERE, "../../.."))
T226_DIR = os.path.join(SWARM_REPO, "work/rahul-api/t226")
STRIPS_DIR = os.path.join(T226_DIR, "strips")
IDS_FILE = os.path.join(STRIPS_DIR, "IDS_by_scene.json")
OUT_CODES = os.path.join(HERE, "codes.json")
OUT_QC_DIR = os.path.join(HERE, "qc")

# Strip layout parameters (from blind_t226.py)
FR = [0, 4, 8, 16, 24, 36, 48, 60, 72, 84, 92]
ROI = {'P': (180, 95, 460, 300), 'F': (230, 60, 345, 400), 'H': (230, 60, 345, 400)}
HDR_H = 28
TOP_H = 3 * 240  # 720
TOP_W = 4 * 416  # 1664
CROP_H = 150


def parse_strip(strip_img, scene):
    """
    Extracts individual object crops from the bottom rows of the strip.
    """
    H, W, _ = strip_img.shape
    crops_area = strip_img[HDR_H + TOP_H :, :]
    
    # Calculate crop dimensions as defined in blind_t226.py
    x0, y0, x1, y1 = ROI[scene]
    orig_w, orig_h = x1 - x0, y1 - y0
    scale = CROP_H / float(orig_h)
    crop_w = int(orig_w * scale)
    per = max(1, W // crop_w)
    
    n_crops = 24  # frames 0, 4, 8, ..., 92
    crops = []
    
    row_idx = 0
    curr_y = 0
    while len(crops) < n_crops and curr_y + CROP_H <= crops_area.shape[0]:
        row_img = crops_area[curr_y : curr_y + CROP_H, :]
        for col in range(per):
            if len(crops) >= n_crops:
                break
            x_start = col * crop_w
            x_end = x_start + crop_w
            if x_end <= W:
                crop = row_img[:, x_start:x_end]
                crops.append(crop)
        curr_y += CROP_H
        row_idx += 1
        
    return crops


def track_ball_in_crops(crops):
    """
    Tracks dark circular/elliptical object in ball crops (F and H scenes).
    Returns list of dicts: [{'frame': k*4, 'cx': float, 'cy': float, 'r': float, 'area': int}]
    """
    trajectory = []
    for k, crop in enumerate(crops):
        frame_num = k * 4
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # Dark ball on lighter table/plank/background
        # Exclude header text area in top-left corner
        mask_text = np.ones_like(gray, dtype=bool)
        mask_text[:20, :35] = False
        
        # Threshold lowest 10% pixel values or dark connected components
        thresh_val = np.percentile(gray[mask_text], 12)
        binary = (gray <= thresh_val) & mask_text
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary.astype(np.uint8))
        
        best_comp = None
        best_score = -1
        for lbl in range(1, num_labels):
            area = stats[lbl, cv2.CC_STAT_AREA]
            if 30 <= area <= 2000:
                cx, cy = centroids[lbl]
                # Circularity / compactness
                w_stat = stats[lbl, cv2.CC_STAT_WIDTH]
                h_stat = stats[lbl, cv2.CC_STAT_HEIGHT]
                aspect = min(w_stat, h_stat) / max(w_stat, h_stat)
                score = area * aspect
                if score > best_score:
                    best_score = score
                    best_comp = (cx, cy, np.sqrt(area / np.pi), area)
                    
        if best_comp:
            cx, cy, r, area = best_comp
            trajectory.append({'k': k, 'frame': frame_num, 'cx': cx, 'cy': cy, 'r': r, 'area': area, 'found': True})
        else:
            trajectory.append({'k': k, 'frame': frame_num, 'cx': np.nan, 'cy': np.nan, 'r': np.nan, 'area': 0, 'found': False})
            
    return trajectory


def track_pendulum_in_crops(crops):
    """
    Tracks pendulum bob / rod in pendulum crops (P scene).
    """
    trajectory = []
    for k, crop in enumerate(crops):
        frame_num = k * 4
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        mask_text = np.ones_like(gray, dtype=bool)
        mask_text[:20, :35] = False
        
        # The pendulum bob is a dark metal weight
        thresh_val = np.percentile(gray[mask_text], 8)
        binary = (gray <= thresh_val) & mask_text
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary.astype(np.uint8))
        best_comp = None
        best_score = -1
        for lbl in range(1, num_labels):
            area = stats[lbl, cv2.CC_STAT_AREA]
            if 40 <= area <= 3000:
                cx, cy = centroids[lbl]
                # Bob is in lower half of pivot region
                if cy > 40:
                    score = area
                    if score > best_score:
                        best_score = score
                        best_comp = (cx, cy, np.sqrt(area / np.pi), area)
                        
        if best_comp:
            cx, cy, r, area = best_comp
            trajectory.append({'k': k, 'frame': frame_num, 'cx': cx, 'cy': cy, 'r': r, 'area': area, 'found': True})
        else:
            trajectory.append({'k': k, 'frame': frame_num, 'cx': np.nan, 'cy': np.nan, 'r': np.nan, 'area': 0, 'found': False})
            
    return trajectory


def classify_scene_p(trajectory, strip_img):
    """
    P: SWING (back-and-forth motion visible) / STILL (no visible rod motion after frame 4) / OTHER.
    """
    valid = [p for p in trajectory if p['found']]
    if len(valid) < 8:
        return 'OTHER', 'Low bob tracking coverage (<8 frames)'
        
    xs = [p['cx'] for p in valid]
    ys = [p['cy'] for p in valid]
    dx = max(xs) - min(xs)
    
    # Check motion after frame 4 (k >= 1)
    late_valid = [p for p in valid if p['k'] >= 1]
    if not late_valid:
        return 'OTHER', 'No tracking after frame 4'
    late_xs = [p['cx'] for p in late_valid]
    late_dx = max(late_xs) - min(late_xs)
    
    # Check directional changes / zero-crossings
    diffs = np.diff(late_xs)
    sign_changes = np.sum((diffs[:-1] * diffs[1:]) < -0.5)
    
    if late_dx <= 4.0:
        return 'STILL', f'Still: late_dx={late_dx:.1f}px <= 4px'
    elif late_dx > 8.0 or sign_changes >= 1:
        return 'SWING', f'Swing: late_dx={late_dx:.1f}px, sign_changes={sign_changes}'
    else:
        return 'SWING', f'Marginal swing: late_dx={late_dx:.1f}px'


def classify_scene_f_or_h(trajectory, scene, strip_img):
    """
    F, H:
    - DOWN: ball moves down onto the plank at some point
    - UP: ball rises >= 1 diameter before any plank contact, or leaves top of frame
    - STILL: ball stays within 1 diameter of its start all clip
    - OTHER: breaks, vanishes, drifts
    """
    valid = [p for p in trajectory if p['found']]
    if len(valid) < 6:
        # Check if ball vanished or left frame early
        return 'OTHER', 'Low ball tracking coverage (<6 frames)'
        
    start_p = valid[0]
    y0 = start_p['cy']
    x0 = start_p['cx']
    diam = 2.0 * start_p['r']
    if np.isnan(diam) or diam < 5:
        diam = 20.0  # nominal diameter in 150px crop
        
    ys = [p['cy'] for p in valid]
    xs = [p['cx'] for p in valid]
    
    max_down = max(ys) - y0
    max_up = y0 - min(ys)
    max_disp = max(np.sqrt((p['cx'] - x0)**2 + (p['cy'] - y0)**2) for p in valid)
    
    # Check if ball rises >= 1 diameter before any plank contact
    # Or leaves top of frame (min y < 5)
    if min(ys) < 10 or max_up >= 0.85 * diam:
        return 'UP', f'Up: max_up={max_up:.1f}px >= 0.85*D ({diam:.1f}px)'
        
    # Check if ball moves down onto plank at some point
    # Plank contact in 150px crop is typically around cy > 100
    if max_down >= 1.0 * diam or max(ys) > 105:
        return 'DOWN', f'Down: max_down={max_down:.1f}px >= 1.0*D ({diam:.1f}px), max_y={max(ys):.1f}'
        
    # Check if stays within 1 diameter of start
    if max_disp <= 1.0 * diam:
        return 'STILL', f'Still: max_disp={max_disp:.1f}px <= 1.0*D ({diam:.1f}px)'
        
    return 'OTHER', f'Other: max_down={max_down:.1f}, max_up={max_up:.1f}, max_disp={max_disp:.1f}'


def process_all_strips(dry_run=False):
    """
    Processes all available strips in STRIPS_DIR according to IDS_FILE.
    """
    if not os.path.exists(IDS_FILE):
        print(f"IDS_by_scene.json not found at {IDS_FILE}.")
        return False
        
    with open(IDS_FILE) as f:
        ids_by_scene = json.load(f)
        
    total_ids = sum(len(v) for v in ids_by_scene.values())
    print(f"Loaded {total_ids} IDs across scenes: { {k: len(v) for k, v in ids_by_scene.items()} }")
    
    os.makedirs(OUT_QC_DIR, exist_ok=True)
    
    codes = {}
    details = {}
    
    for scene, ids in sorted(ids_by_scene.items()):
        for bid in ids:
            strip_path = os.path.join(STRIPS_DIR, f"{bid}.jpg")
            if not os.path.exists(strip_path):
                print(f"Warning: strip {strip_path} missing!")
                continue
                
            img = cv2.imread(strip_path)
            if img is None:
                print(f"Warning: could not read {strip_path}!")
                continue
                
            crops = parse_strip(img, scene)
            
            if scene == 'P':
                traj = track_pendulum_in_crops(crops)
                code, reason = classify_scene_p(traj, img)
            else:
                traj = track_ball_in_crops(crops)
                code, reason = classify_scene_f_or_h(traj, scene, img)
                
            codes[bid] = code
            details[bid] = {
                'scene': scene,
                'code': code,
                'reason': reason,
                'n_tracked': sum(1 for p in traj if p['found']),
            }
            print(f"ID {bid} | Scene {scene} | Code: {code:6s} | {reason}")
            
    print(f"\nTotal coded: {len(codes)} / {total_ids}")
    
    # Save codes and verification details
    if not dry_run and len(codes) == total_ids:
        with open(OUT_CODES, 'w') as f:
            json.dump(codes, f, indent=1, sort_keys=True)
            
        sha = hashlib.sha256(open(OUT_CODES, 'rb').read()).hexdigest()
        with open(OUT_CODES + ".sha256", 'w') as f:
            f.write(f"{sha}  codes.json\n")
            
        with open(os.path.join(HERE, "coding_details.json"), 'w') as f:
            json.dump(details, f, indent=2, sort_keys=True)
            
        print(f"\nSuccessfully written {OUT_CODES}")
        print(f"SHA-256: {sha}")
        return True
    else:
        print("Dry run or incomplete strip set. Output not finalized.")
        return False


if __name__ == '__main__':
    process_all_strips()
