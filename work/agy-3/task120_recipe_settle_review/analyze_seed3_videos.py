#!/usr/bin/env python3
"""
Direct video and frame analysis of Seed 3 paired MP4s:
v7_REC_ball1_fps24_93f_s3.mp4 vs v7_RECT_ball1_fps24_93f_s3.mp4
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = "/home/nail/swarm-work/agy-3/cosmos-swarm"
V7_DIR = os.path.join(REPO_ROOT, "work/ro-1/cause_v7")
OUT_DIR = os.path.join(REPO_ROOT, "work/agy-3/task120_recipe_settle_review")

rec_mp4 = os.path.join(V7_DIR, "v7_REC_ball1_fps24_93f_s3.mp4")
rect_mp4 = os.path.join(V7_DIR, "v7_RECT_ball1_fps24_93f_s3.mp4")

def extract_frames(mp4_path):
    cap = cv2.VideoCapture(mp4_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Convert BGR to RGB
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return np.array(frames) # (T, H, W, 3)

print("Decoding REC Seed 3 MP4...")
rec_frames = extract_frames(rec_mp4)
print(f"REC shape: {rec_frames.shape}")

print("Decoding RECT Seed 3 MP4...")
rect_frames = extract_frames(rect_mp4)
print(f"RECT shape: {rect_frames.shape}")

T, H, W, _ = rec_frames.shape

# Ball corridor: y in [130, 360], x in [220, 360]
y0, y1 = 130, 360
x0, x1 = 220, 360

# Measure frame-to-frame difference across time in corridor
rec_gray = np.array([cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in rec_frames])
rect_gray = np.array([cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in rect_frames])

rec_corridor_diff = np.abs(np.diff(rec_gray[:, y0:y1, x0:x1], axis=0)).mean(axis=(1, 2))
rect_corridor_diff = np.abs(np.diff(rect_gray[:, y0:y1, x0:x1], axis=0)).mean(axis=(1, 2))

print(f"REC corridor diff: early={rec_corridor_diff[:45].mean():.3f}, late={rec_corridor_diff[45:].mean():.3f}, last20={rec_corridor_diff[-20:].mean():.3f}")
print(f"RECT corridor diff: early={rect_corridor_diff[:45].mean():.3f}, late={rect_corridor_diff[45:].mean():.3f}, last20={rect_corridor_diff[-20:].mean():.3f}")

# Connected component / dark blob analysis in corridor across frames
def track_dark_blobs(gray_seq):
    # plank background is light wood, ball is dark metallic
    # measure threshold < 75 in corridor
    areas = []
    centroids_y = []
    centroids_x = []
    num_blobs = []
    
    for i in range(len(gray_seq)):
        roi = gray_seq[i, y0:y1, x0:x1]
        mask = (roi < 70).astype(np.uint8) * 255
        # Clean small noise
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        
        # Filter components with area > 30 px
        valid_indices = [idx for idx in range(1, num_labels) if stats[idx, cv2.CC_STAT_AREA] >= 30]
        num_blobs.append(len(valid_indices))
        
        if len(valid_indices) > 0:
            # Pick largest component
            largest_idx = max(valid_indices, key=lambda idx: stats[idx, cv2.CC_STAT_AREA])
            areas.append(stats[largest_idx, cv2.CC_STAT_AREA])
            centroids_y.append(centroids[largest_idx][1] + y0)
            centroids_x.append(centroids[largest_idx][0] + x0)
        else:
            areas.append(0)
            centroids_y.append(np.nan)
            centroids_x.append(np.nan)
            
    return np.array(areas), np.array(centroids_y), np.array(centroids_x), np.array(num_blobs)

rec_areas, rec_cy, rec_cx, rec_blobs = track_dark_blobs(rec_gray)
rect_areas, rect_cy, rect_cx, rect_blobs = track_dark_blobs(rect_gray)

# Area-equivalent diameter: d = 2 * sqrt(area / pi)
rec_deq = 2 * np.sqrt(np.maximum(rec_areas, 0) / np.pi)
rect_deq = 2 * np.sqrt(np.maximum(rect_areas, 0) / np.pi)

print("\nBlob Geometry (Seed 3):")
print(f"  Frame 0: REC d_eq = {rec_deq[0]:.1f} px vs RECT d_eq = {rect_deq[0]:.1f} px (ground truth real ball is ~22 px)")
print(f"  Late Window (f45-92): REC mean d_eq = {rec_deq[45:].mean():.1f} px (max {rec_deq[45:].max():.1f} px) vs RECT mean d_eq = {rect_deq[45:].mean():.1f} px (max {rect_deq[45:].max():.1f} px)")
print(f"  Multi-blob frames (debris/duplication): REC = {(rec_blobs > 1).sum()}/{T} ({(rec_blobs > 1).sum()/T:.1%}) vs RECT = {(rect_blobs > 1).sum()}/{T} ({(rect_blobs > 1).sum()/T:.1%})")

# Resting stillness verification in RECT (f45 to f92)
rect_late_y_disp = np.nanmax(rect_cy[45:]) - np.nanmin(rect_cy[45:])
rect_late_x_disp = np.nanmax(rect_cx[45:]) - np.nanmin(rect_cx[45:])
print(f"\nRECT Late Displacement (f45 to f92):")
print(f"  Y range: {np.nanmin(rect_cy[45:]):.1f} to {np.nanmax(rect_cy[45:]):.1f} px (total vertical travel: {rect_late_y_disp:.1f} px)")
print(f"  X range: {np.nanmin(rect_cx[45:]):.1f} to {np.nanmax(rect_cx[45:]):.1f} px (total horizontal travel: {rect_late_x_disp:.1f} px)")

# Save contact sheet of key frames: f0, f15, f30, f45, f60, f75, f90
selected_frames = [0, 15, 30, 45, 60, 75, 92]
sheet_h = 2 * 240
sheet_w = len(selected_frames) * 208 # 1/4 resolution

fig, axes = plt.subplots(2, len(selected_frames), figsize=(18, 5.5))
for col_idx, f_idx in enumerate(selected_frames):
    # Crop around corridor
    crop_y0, crop_y1 = 100, 420
    crop_x0, crop_x1 = 180, 460
    
    # Row 0: REC
    axes[0, col_idx].imshow(rec_frames[f_idx, crop_y0:crop_y1, crop_x0:crop_x1])
    axes[0, col_idx].set_title(f"Frame {f_idx}", fontsize=10)
    axes[0, col_idx].axis("off")
    if col_idx == 0:
        axes[0, col_idx].text(-20, 160, "REC (Default)\n[Giant Sphere + Debris]", 
                              fontsize=10, fontweight="bold", color="darkred", rotation=90, va="center", ha="right")
        
    # Row 1: RECT
    axes[1, col_idx].imshow(rect_frames[f_idx, crop_y0:crop_y1, crop_x0:crop_x1])
    axes[1, col_idx].axis("off")
    if col_idx == 0:
        axes[1, col_idx].text(-20, 160, "RECT (+Timed Settle)\n[Physically Settled]", 
                              fontsize=10, fontweight="bold", color="darkgreen", rotation=90, va="center", ha="right")

plt.suptitle("Task 120 / Finding #2720 Visual Verification: Ball 1 Seed 3 REC vs RECT", fontsize=14, fontweight="bold", y=0.98)
plt.tight_layout()
sheet_path = os.path.join(OUT_DIR, "sheets/sheet_seed3_rec_vs_rect.jpg")
plt.savefig(sheet_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"\nSaved contact sheet to {sheet_path}")
