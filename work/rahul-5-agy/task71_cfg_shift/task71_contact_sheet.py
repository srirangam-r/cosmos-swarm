#!/usr/bin/env python3
import os, sys, cv2, numpy as np

clips_dir = "/home/sha/swarm-work/rahul-5-agy/task71_cfg_shift/clips"
out_dir = "/home/sha/swarm-work/rahul-5-agy/task71_cfg_shift/sheets"
os.makedirs(out_dir, exist_ok=True)

sample_frames = [0, 8, 16, 24, 32, 44, 60, 75, 92]

for fname in sorted(os.listdir(clips_dir)):
    if not fname.endswith(".mp4"):
        continue
    clip_path = os.path.join(clips_dir, fname)
    cap = cv2.VideoCapture(clip_path)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    crops = []
    for f_idx in sample_frames:
        if f_idx >= n_frames:
            f_idx = n_frames - 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if not ret:
            break
        # Crop region around the ball corridor (x: 230..350, y: 120..360)
        crop = frame[120:360, 230:350]
        # annotate frame index
        cv2.putText(crop, f"f{f_idx}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        crops.append(crop)
    cap.release()
    
    if crops:
        strip = np.hstack(crops)
        base_name = os.path.splitext(fname)[0]
        out_sheet = os.path.join(out_dir, f"{base_name}_strip.jpg")
        cv2.imwrite(out_sheet, strip)
        print(f"Wrote {out_sheet}")
