#!/usr/bin/env python3
"""
Task 137: QT-Component Ablation Blind Harness
Preregistration #3098:
- Arms: F (base), QT (full timed settle), QTnc (QT no count), CO (count only), R (F + Rule R)
- Inputs: ball1 dd33, ball2 dd35
- Seeds: 31, 32, 33 (paired)
- Outcome coding blind to arm after randomized blind IDs.
"""

import os
import sys
import glob
import json
import hashlib
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SALT = "task137_ablation_prereg3098_seed3133"

def make_blind_key(clip_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "clips"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "sheets"), exist_ok=True)
    
    mp4s = sorted(glob.glob(os.path.join(clip_dir, "t138_*.mp4")))
    print(f"Found {len(mp4s)} clips in {clip_dir}")
    
    # Generate deterministic blind hashes
    items = []
    for p in mp4s:
        base = os.path.basename(p)[:-4]
        h = hashlib.sha256((base + SALT).encode('utf-8')).hexdigest()[:10]
        items.append((h, p, base))
    
    # Sort by hash to randomize order
    items.sort(key=lambda x: x[0])
    
    key = {}
    blind_manifest = {}
    
    for idx, (h, p, orig_base) in enumerate(items, start=1):
        blind_id = f"blind_{idx:02d}"
        
        # Parse arm, ball, seed from original basename t138_<arm>_<ball>_s<seed>
        parts = orig_base.split("_")
        arm = parts[1]
        ball = parts[2]
        seed = int(parts[3][1:])
        
        json_path = os.path.join(clip_dir, orig_base + ".json")
        prompt = ""
        if os.path.exists(json_path):
            with open(json_path) as jf:
                sdata = json.load(jf)
                prompt = sdata.get("prompt", "")
                
        key[blind_id] = {
            "orig_base": orig_base,
            "arm": arm,
            "ball": ball,
            "seed": seed,
            "prompt": prompt,
            "hash": h
        }
        
        blind_manifest[blind_id] = {
            "blind_id": blind_id,
            "clip_file": f"{blind_id}.mp4",
            "sheet_file": f"{blind_id}_sheet.jpg",
            "zoom_file": f"{blind_id}_zoom.jpg"
        }
        
        # Symlink or copy clip
        target_mp4 = os.path.join(out_dir, "clips", f"{blind_id}.mp4")
        if not os.path.exists(target_mp4):
            os.system(f"cp {p} {target_mp4}")
            
    with open(os.path.join(out_dir, "KEY_LOCKED.json"), "w") as kf:
        json.dump(key, kf, indent=2)
    print(f"Saved locked key for {len(key)} clips to {out_dir}/KEY_LOCKED.json")
    
    with open(os.path.join(out_dir, "blind_manifest.json"), "w") as mf:
        json.dump(blind_manifest, mf, indent=2)
        
    return key, blind_manifest

def process_metrics_and_sheets(out_dir):
    clips_dir = os.path.join(out_dir, "clips")
    sheets_dir = os.path.join(out_dir, "sheets")
    
    mp4s = sorted(glob.glob(os.path.join(clips_dir, "blind_*.mp4")))
    metrics = {}
    
    for p in mp4s:
        blind_id = os.path.basename(p)[:-4]
        cap = cv2.VideoCapture(p)
        raw_frames = []
        gray_frames = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            raw_frames.append(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frames.append(gray)
        cap.release()
        
        n_frames = len(raw_frames)
        assert n_frames == 93, f"{blind_id} has {n_frames} frames, expected 93"
        
        # 1. ro-1 late corridor motion proxy:
        # Ball corridor: y in [130:360], x in [220:360]
        # Frame difference on float32 gray
        corr_stack = np.stack([gf[130:360, 220:360].astype(np.float32) for gf in gray_frames])
        diffs = np.abs(np.diff(corr_stack, axis=0)).mean(axis=(1, 2))
        
        early_corr = float(diffs[1:45].mean())
        late_corr = float(diffs[45:].mean())
        last20_corr = float(diffs[-20:].mean())
        
        # 2. rog1 plank change proxy:
        # Plank crop: y in [200:440], x in [60:700]
        plank_stack = np.stack([cv2.GaussianBlur(gf, (3, 3), 0)[200:440, 60:700].astype(np.int16) for gf in gray_frames])
        chg_px = [int((np.abs(plank_stack[i] - plank_stack[i-1]) > 20).sum()) for i in range(1, len(plank_stack))]
        late_chg_px = float(np.mean(chg_px[-24:]))
        
        metrics[blind_id] = {
            "frames": n_frames,
            "corridor_early": round(early_corr, 4),
            "corridor_late": round(late_corr, 4),
            "corridor_last20": round(last20_corr, 4),
            "plank_late_chg_px": round(late_chg_px, 2),
            "diffs_series": [round(float(x), 4) for x in diffs]
        }
        
        # 3. Create overview contact sheet (every 4 frames: 0, 4, 8, ..., 92 = 24 frames)
        # 4 rows x 6 cols
        sheet_tiles = []
        for t in range(0, n_frames, 4):
            tile = cv2.resize(raw_frames[t], (320, 185)).copy()
            cv2.putText(tile, f"f{t}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(tile, blind_id, (8, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
            sheet_tiles.append(tile)
            
        rows = [np.hstack(sheet_tiles[r:r+6]) for r in range(0, 24, 6)]
        sheet_img = np.vstack(rows)
        cv2.imwrite(os.path.join(sheets_dir, f"{blind_id}_sheet.jpg"), sheet_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # 4. Create zoomed plank/corridor contact sheet (y: 120-420, x: 180-420) for rest verification
        zoom_tiles = []
        for t in range(0, n_frames, 4):
            crop = raw_frames[t][120:420, 180:420].copy()
            tile = cv2.resize(crop, (240, 300))
            cv2.putText(tile, f"f{t}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            zoom_tiles.append(tile)
        zoom_rows = [np.hstack(zoom_tiles[r:r+6]) for r in range(0, 24, 6)]
        zoom_img = np.vstack(zoom_rows)
        cv2.imwrite(os.path.join(sheets_dir, f"{blind_id}_zoom.jpg"), zoom_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
    with open(os.path.join(out_dir, "automated_metrics_blind.json"), "w") as mf:
        json.dump(metrics, mf, indent=2)
    print(f"Computed automated metrics and sheets for {len(metrics)} clips.")

if __name__ == "__main__":
    clip_dir = sys.argv[1] if len(sys.argv) > 1 else "clips"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "blind_eval"
    make_blind_key(clip_dir, out_dir)
    process_metrics_and_sheets(out_dir)
