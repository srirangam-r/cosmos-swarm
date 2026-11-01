import cv2
import numpy as np
import os
import json

out_dir = "/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task129_scout_hypotheses"
os.makedirs(f"{out_dir}/sheets", exist_ok=True)
os.makedirs(f"{out_dir}/plots", exist_ok=True)

clips = {
    "REC_b2_s1": "/home/nail/swarm-work/agy-2/cosmos-swarm/work/ro-1/cause_v7/native_rec_ball2/v7_REC_ball2_fps24_93f_s1.crf20.mp4",
    "REC_b2_s2": "/home/nail/swarm-work/agy-2/cosmos-swarm/work/ro-1/cause_v7/native_rec_ball2/v7_REC_ball2_fps24_93f_s2.crf20.mp4",
    "REC_b2_s3": "/home/nail/swarm-work/agy-2/cosmos-swarm/work/ro-1/cause_v7/native_rec_ball2/v7_REC_ball2_fps24_93f_s3.crf20.mp4",
    "REC_b1_s3": "/home/nail/swarm-work/agy-2/cosmos-swarm/work/ro-1/cause_v7/v7_REC_ball1_fps24_93f_s3.mp4",
    "rog1_b1_s22_F": "/home/nail/swarm-work/agy-2/cosmos-swarm/work/rog1/rep2460/clips/r60_698f85.mp4",
    "rog1_b1_s23_F": "/home/nail/swarm-work/agy-2/cosmos-swarm/work/rog1/rep2460/clips/r60_19fa30.mp4",
    "box_ctrl_b2_s3": "/home/nail/swarm-work/agy-2/scratch/clips/box_ctrl_b2_noneg_s3.mp4",
    "pend10_restev_s2": "/home/nail/swarm-work/agy-2/scratch/ro3_clips/ms_pend10_restev_s2.mp4",
}

print("Reading and saving full frame sequences for key windows...")

def read_frames(path):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ret, f = cap.read()
        if not ret: break
        frames.append(f)
    cap.release()
    return frames

# Let's inspect REC_b2_s1 around f20-30
f_b2s1 = read_frames(clips["REC_b2_s1"])
# Save f20 to f28 side by side
sheet = []
for f_idx in [20, 22, 23, 24, 25, 26, 27, 28]:
    crop = f_b2s1[f_idx][100:400, 200:360]
    # add frame label
    cv2.putText(crop, f"f{f_idx}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    sheet.append(crop)
cv2.imwrite(f"{out_dir}/sheets/b2_s1_f20_f28.jpg", np.hstack(sheet))
print("Saved b2_s1_f20_f28.jpg")

# Let's inspect REC_b2_s2 around f50-60
f_b2s2 = read_frames(clips["REC_b2_s2"])
sheet = []
for f_idx in [48, 50, 52, 53, 54, 55, 56, 58]:
    crop = f_b2s2[f_idx][0:350, 200:380] # include top/ceiling
    cv2.putText(crop, f"f{f_idx}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    sheet.append(crop)
cv2.imwrite(f"{out_dir}/sheets/b2_s2_f48_f58.jpg", np.hstack(sheet))
print("Saved b2_s2_f48_f58.jpg")

# Let's inspect REC_b1_s3 across entire clip (every 6 frames)
f_b1s3 = read_frames(clips["REC_b1_s3"])
sheet = []
for f_idx in range(0, 93, 6):
    crop = cv2.resize(f_b1s3[f_idx][80:420, 180:450], (135, 170))
    cv2.putText(crop, f"f{f_idx}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    sheet.append(crop)
# arrange in 2 rows of 8
r1 = np.hstack(sheet[:8])
r2 = np.hstack(sheet[8:16])
cv2.imwrite(f"{out_dir}/sheets/b1_s3_overview.jpg", np.vstack([r1, r2]))
print("Saved b1_s3_overview.jpg")

# Let's inspect REC_b2_s3 across clip
f_b2s3 = read_frames(clips["REC_b2_s3"])
sheet = []
for f_idx in range(0, 93, 6):
    crop = cv2.resize(f_b2s3[f_idx][80:420, 180:450], (135, 170))
    cv2.putText(crop, f"f{f_idx}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    sheet.append(crop)
r1 = np.hstack(sheet[:8])
r2 = np.hstack(sheet[8:16])
cv2.imwrite(f"{out_dir}/sheets/b2_s3_overview.jpg", np.vstack([r1, r2]))
print("Saved b2_s3_overview.jpg")

# Let's inspect rog1_b1_s23_F around f0-f14
f_r19 = read_frames(clips["rog1_b1_s23_F"])
sheet = []
for f_idx in range(0, 12):
    crop = f_r19[f_idx][100:400, 0:350] # left edge to corridor
    crop_s = cv2.resize(crop, (150, 130))
    cv2.putText(crop_s, f"f{f_idx}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    sheet.append(crop_s)
r1 = np.hstack(sheet[:6])
r2 = np.hstack(sheet[6:12])
cv2.imwrite(f"{out_dir}/sheets/rog1_s23_f0_f11.jpg", np.vstack([r1, r2]))
print("Saved rog1_s23_f0_f11.jpg")

# Let's inspect rog1_b1_s22_F around f12-f28
f_r69 = read_frames(clips["rog1_b1_s22_F"])
sheet = []
for f_idx in [12, 14, 16, 18, 20, 22, 24, 26]:
    crop = f_r69[f_idx][120:420, 150:450]
    crop_s = cv2.resize(crop, (150, 150))
    cv2.putText(crop_s, f"f{f_idx}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    sheet.append(crop_s)
cv2.imwrite(f"{out_dir}/sheets/rog1_s22_plank_f12_f26.jpg", np.hstack(sheet))
print("Saved rog1_s22_plank_f12_f26.jpg")

# Let's inspect box_ctrl_b2_s3 around f0-f20
f_box = read_frames(clips["box_ctrl_b2_s3"])
sheet = []
for f_idx in [0, 2, 4, 6, 8, 10, 12, 15]:
    crop = f_box[f_idx][80:400, 180:360]
    crop_s = cv2.resize(crop, (140, 240))
    cv2.putText(crop_s, f"f{f_idx}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    sheet.append(crop_s)
cv2.imwrite(f"{out_dir}/sheets/box_ctrl_b2_s3_f0_f15.jpg", np.hstack(sheet))
print("Saved box_ctrl_b2_s3_f0_f15.jpg")

# Let's inspect pend10_restev_s2 around f25-f40
f_pend = read_frames(clips["pend10_restev_s2"])
sheet = []
for f_idx in [26, 28, 30, 32, 34, 36, 38, 40]:
    crop = f_pend[f_idx][40:320, 300:520]
    crop_s = cv2.resize(crop, (150, 190))
    cv2.putText(crop_s, f"f{f_idx}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    sheet.append(crop_s)
cv2.imwrite(f"{out_dir}/sheets/pend10_restev_s2_f26_f40.jpg", np.hstack(sheet))
print("Saved pend10_restev_s2_f26_f40.jpg")
