#!/usr/bin/env python3
"""Generate contact sheets and difference maps for nv vs kar clips."""

import os
import cv2
import numpy as np
from pathlib import Path

CLIPS_DIR = Path("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/clips")
QC_DIR = Path("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/qc")

PAIRS = [
    ("ms_pend10_midB_nv_s1", "ms_pend10_midB_kar_s1", "pend10_s1"),
    ("ms_pend10_midB_nv_s2", "ms_pend10_midB_kar_s2", "pend10_s2"),
    ("ms_pend10_midB_nv_s3", "ms_pend10_midB_kar_s3", "pend10_s3"),
    ("ms_pend11_midB_nv_s1", "ms_pend11_midB_kar_s1", "pend11_s1"),
    ("ms_pend11_midB_nv_s2", "ms_pend11_midB_kar_s2", "pend11_s2"),
    ("ms_pend11_midB_nv_s3", "ms_pend11_midB_kar_s3", "pend11_s3"),
]

def load_frames(video_path):
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def main():
    QC_DIR.mkdir(parents=True, exist_ok=True)
    frame_indices = [0, 15, 30, 45, 60, 75, 90]
    
    for nv_name, kar_name, tag in PAIRS:
        nv_path = CLIPS_DIR / f"{nv_name}.mp4"
        kar_path = CLIPS_DIR / f"{kar_name}.mp4"
        if not nv_path.exists() or not kar_path.exists():
            continue
            
        nv_frames = load_frames(nv_path)
        kar_frames = load_frames(kar_path)
        
        row_nv = []
        row_kar = []
        row_diff = []
        
        for idx in frame_indices:
            f_nv = nv_frames[idx]
            f_kar = kar_frames[idx]
            
            # Compute amplified difference
            diff = cv2.absdiff(f_nv, f_kar)
            diff_amp = np.clip(diff.astype(np.float32) * 10.0, 0, 255).astype(np.uint8)
            # Apply colormap to difference
            diff_color = cv2.applyColorMap(cv2.cvtColor(diff_amp, cv2.COLOR_BGR2GRAY), cv2.COLORMAP_INFERNO)
            
            # Label frame index
            f_nv_lbl = f_nv.copy()
            cv2.putText(f_nv_lbl, f"nv f{idx}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            f_kar_lbl = f_kar.copy()
            cv2.putText(f_kar_lbl, f"kar f{idx}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(diff_color, f"|diff|x10 f{idx}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Resize for compact montage
            target_size = (208, 120)
            row_nv.append(cv2.resize(f_nv_lbl, target_size))
            row_kar.append(cv2.resize(f_kar_lbl, target_size))
            row_diff.append(cv2.resize(diff_color, target_size))
            
        strip_nv = np.hstack(row_nv)
        strip_kar = np.hstack(row_kar)
        strip_diff = np.hstack(row_diff)
        
        montage = np.vstack([strip_nv, strip_kar, strip_diff])
        out_sheet = QC_DIR / f"qc_montage_{tag}.jpg"
        cv2.imwrite(str(out_sheet), montage)
        print(f"Saved montage for {tag} to {out_sheet.name}")

if __name__ == "__main__":
    main()
