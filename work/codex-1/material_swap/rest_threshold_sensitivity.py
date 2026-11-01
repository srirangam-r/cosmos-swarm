"""Descriptive threshold sensitivity for the fixed-ROI late-motion check."""
import sys
import cv2
import numpy as np

cap = cv2.VideoCapture(sys.argv[1])
tracks = {t: [] for t in (60, 75, 90, 105, 120)}
frame_index = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if 40 <= frame_index <= 188:
        gray = cv2.cvtColor(frame[210:310, 360:470], cv2.COLOR_BGR2GRAY)
        for threshold, points in tracks.items():
            n, _, stats, centers = cv2.connectedComponentsWithStats((gray < threshold).astype('uint8'), 8)
            if n <= 1:
                raise ValueError(f'No component at frame {frame_index}, threshold {threshold}')
            k = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            points.append([*centers[k], stats[k, cv2.CC_STAT_AREA]])
    frame_index += 1
for threshold, points in tracks.items():
    a = np.asarray(points)
    if len(a) != 149:
        raise ValueError(f'Expected 149 frames, got {len(a)}')
    xy_range = np.ptp(a[:, :2], axis=0)
    max_delta = np.linalg.norm(a[:, :2] - a[0, :2], axis=1).max()
    print(f'{threshold}: n={len(a)}, x/y range={xy_range[0]:.2f}/{xy_range[1]:.2f} px, max displacement={max_delta:.2f} px, area={a[:,2].min():.0f}–{a[:,2].max():.0f} px²')
