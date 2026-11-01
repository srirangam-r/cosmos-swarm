#!/usr/bin/env python3
import json
import glob
from pathlib import Path
import cv2
import numpy as np

WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[2]
CLIPS_DIR = WORK_DIR / "clips"
STRIPS_DIR = WORK_DIR / "strips"
REF_F0_PATH = REPO_ROOT / "work/raj-1/gauge_ball/gauge_ball1_f0_832x480.png"
ref_f0 = cv2.imread(str(REF_F0_PATH))

clips = sorted(glob.glob(str(CLIPS_DIR / "*.mp4")))

# Define arms
# Each arm has factor, step_range, seeds 1-3
grid_results = {}

for c_path in clips:
    stem = Path(c_path).stem
    # parse stem: b1_att{factor}_{steps}_s{seed}
    parts = stem.split("_")
    f_str = parts[1].replace("att", "").replace("p", ".")
    factor = float(f_str)
    steps = int(parts[2].replace("step", ""))
    seed = int(parts[3].replace("s", ""))
    
    cap = cv2.VideoCapture(c_path)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(f)
    cap.release()
    
    n_frames = len(frames)
    
    # 1. Frame 0 fidelity vs ground truth reference
    mse = np.mean((ref_f0.astype(float) - frames[0].astype(float))**2)
    psnr = 20 * np.log10(255.0 / np.sqrt(mse)) if mse > 0 else 999.0
    mae = float(np.mean(np.abs(ref_f0.astype(float) - frames[0].astype(float))))
    
    # 2. Track ball centroid y in the gripper zone:
    # Held ball in frame 0 is at [130:210, 250:310]
    # Center y is ~185.
    # If the ball is released, it drops past y=220 towards the plank at y=360.
    # If it stays held, it remains around y=180-190 throughout.
    
    # Track minimum brightness y along column 270:290 across all frames
    tracked_y = []
    min_vals = []
    for t in range(n_frames):
        col = np.mean(frames[t][110:410, 270:290], axis=(1,2))
        min_idx = np.argmin(col)
        tracked_y.append(110 + int(min_idx))
        min_vals.append(float(np.min(col)))
        
    # Check if ball ever descended significantly below gripper (> 230 px)
    # Plank contact occurs around y ~ 340-360 px
    plank_contact = any(y >= 320 for y in tracked_y)
    max_descend_y = max(tracked_y)
    
    # Check if ball remained at gripper in final 20 frames (f73..f92)
    held_at_end = (np.mean(tracked_y[-20:]) < 210)
    
    # Motion categorization:
    # 0 = strictly immobile / frozen in gripper
    # 1 = clean physical release and fall to plank
    # 2 = phantom cloning / duplicate ball
    # 3 = ball oscillation / tether / morphological stretching
    
    # Check presence of ball at initial gripper coordinates across frames
    gripper_brightness = [np.mean(cv2.cvtColor(fr[140:200, 255:305], cv2.COLOR_BGR2GRAY)) for fr in frames]
    # In frame 0, gripper_brightness is ~21
    # If ball remains in gripper, gripper_brightness stays < 30
    ball_in_gripper_all = all(b < 35 for b in gripper_brightness)
    ball_in_gripper_end = (gripper_brightness[-1] < 35)
    
    # Did a physical release occur from frame 0?
    # True release means ball leaves the gripper (gripper_brightness goes up to background ~100+)
    # AND moves down to plank.
    released = (not ball_in_gripper_end) and plank_contact
    
    # Check for gross phantoms (dark blob at plank while gripper is still dark)
    corridor_dark_blob = any(
        (np.min(cv2.cvtColor(frames[t][280:380, 250:310], cv2.COLOR_BGR2GRAY)) < 30 and gripper_brightness[t] < 35)
        for t in range(10, n_frames)
    )
    
    grid_results[stem] = {
        "stem": stem,
        "factor": factor,
        "steps": steps,
        "seed": seed,
        "f0_psnr": round(psnr, 2),
        "f0_mae": round(mae, 2),
        "y_f0": tracked_y[0],
        "y_f10": tracked_y[10],
        "y_f20": tracked_y[20],
        "y_f30": tracked_y[30],
        "y_f60": tracked_y[60],
        "y_end": tracked_y[-1],
        "max_y": max_descend_y,
        "gripper_b0": round(gripper_brightness[0], 1),
        "gripper_b_end": round(gripper_brightness[-1], 1),
        "ball_in_gripper_all": bool(ball_in_gripper_all),
        "ball_in_gripper_end": bool(ball_in_gripper_end),
        "plank_contact": bool(plank_contact),
        "corridor_dark_blob": bool(corridor_dark_blob),
        "released": bool(released)
    }

# Summary by arm
arms = {}
for factor in [1.0, 0.5, 0.2, 0.05]:
    for steps in [10, 20]:
        arm_key = f"att{factor}_step{steps}"
        arm_clips = [v for v in grid_results.values() if v["factor"] == factor and v["steps"] == steps]
        n_rel = sum(1 for v in arm_clips if v["released"])
        n_held = sum(1 for v in arm_clips if v["ball_in_gripper_end"])
        n_plank = sum(1 for v in arm_clips if v["plank_contact"])
        n_phantom = sum(1 for v in arm_clips if v["corridor_dark_blob"])
        mean_psnr = float(np.mean([v["f0_psnr"] for v in arm_clips]))
        mean_mae = float(np.mean([v["f0_mae"] for v in arm_clips]))
        arms[arm_key] = {
            "factor": factor,
            "steps": steps,
            "n": len(arm_clips),
            "released_count": n_rel,
            "held_at_end_count": n_held,
            "plank_contact_count": n_plank,
            "phantom_count": n_phantom,
            "mean_f0_psnr": round(mean_psnr, 2),
            "mean_f0_mae": round(mean_mae, 2),
            "clips": arm_clips
        }

output = {
    "arms": arms,
    "clips": grid_results
}

with open(WORK_DIR / "grid_evaluation_results.json", "w") as f:
    json.dump(output, f, indent=2)

print("="*80)
print(f"{'Arm':<20} | {'N':<3} | {'Release':<8} | {'Held-at-End':<12} | {'Plank Reach':<12} | {'Phantom/Morph':<14} | {'F0 PSNR':<8}")
print("="*80)
for k, a in arms.items():
    print(f"{k:<20} | {a['n']:<3} | {a['released_count']}/{a['n']:<6} | {a['held_at_end_count']}/{a['n']:<10} | {a['plank_contact_count']}/{a['n']:<10} | {a['phantom_count']}/{a['n']:<12} | {a['mean_f0_psnr']:<8.2f}")
print("="*80)
