#!/usr/bin/env python3
"""Native-rate eye-check strips (task 98): crop x100-480,y60-440 of the 832x480 frame; frames 0-31 step 1, then
32-92 step 4 (labelled with frame numbers). Usage: python strips.py OUTDIR clip1.mp4 [...]"""
import sys
from pathlib import Path
import cv2
import numpy as np

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for p in sys.argv[2:]:
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(f)
    idx = list(range(0, 32)) + list(range(32, len(fr), 4))
    tiles = [cv2.putText(cv2.resize(fr[t][60:440, 100:480], (150, 150)).copy(), str(t), (3, 14), 0, 0.45,
                         (0, 255, 255), 1) for t in idx]
    tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % 12)
    img = np.vstack([np.hstack(tiles[i:i + 12]) for i in range(0, len(tiles), 12)])
    cv2.imwrite(str(out / (Path(p).stem + '_strip.jpg')), img, [cv2.IMWRITE_JPEG_QUALITY, 75])
