#!/usr/bin/env python3
"""Execute rog-cc's requested control (#1639):
Score DOVER visual quality and RAFT Dynamic Degree on real GAUGE video starting at frame 0
vs starting at the mid-fall frame (dd33/35) for identical 93-frame duration across Balls 1, 2, 3, 4.
This isolates the effect of the conditioning frame content from generative model dynamics.
"""
import os, sys, json, subprocess
import numpy as np

PYTHON_BIN = "/home/nail/swarm-work/raj-4/venv_cuda/bin/python"
SCORE_PY = "/home/nail/swarm-work/agy-4/cosmos-swarm/tools/nv_scoreboard/score.py"
DOVER_DIR = "/home/nail/swarm-work/raj-4/ext/DOVER"
VAE_DIR = "/home/nail/swarm-work/agy-2/vae_roundtrip"
WORK_DIR = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task72_score_review"
CLIPS_DIR = os.path.join(WORK_DIR, "real_control_clips")
os.makedirs(CLIPS_DIR, exist_ok=True)

# Ball midfall start frames in 25 fps dedup video:
# Ball 1: f33
# Ball 2: f35
# Ball 3: f34
# Ball 4: f34

ball_configs = [
    (1, 33),
    (2, 35),
    (3, 34),
    (4, 34),
]

f0_clips = []
mid_clips = []

for b, mid_f in ball_configs:
    full_orig = os.path.join(VAE_DIR, f"real_ball_{b}_full_129f_orig.mp4")
    mid_orig = os.path.join(VAE_DIR, f"real_ball_{b}_midfall_dd{mid_f}_93f_orig.mp4")
    
    # 1. Slice full_orig to 93 frames starting at frame 0
    f0_93f = os.path.join(CLIPS_DIR, f"real_ball_{b}_f0_93f.mp4")
    if not os.path.exists(f0_93f):
        cmd = [
            "ffmpeg", "-y", "-i", full_orig,
            "-vf", "select=lt(n\\,93)",
            "-vsync", "0", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
            f0_93f
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    f0_clips.append(f0_93f)
    
    # 2. Midfall is already 93 frames
    mid_clips.append(mid_orig)

print("=== Scoring Real Video f0 Clips (Balls 1-4, 93f) ===", flush=True)
out_f0 = os.path.join(WORK_DIR, "scores_real_f0.json")
cmd_f0 = [
    PYTHON_BIN, SCORE_PY,
    *f0_clips,
    "--dover_dir", DOVER_DIR,
    "--device", "cuda",
    "--out", out_f0
]
subprocess.run(cmd_f0, check=True)

print("=== Scoring Real Video Midfall Clips (Balls 1-4, 93f) ===", flush=True)
out_mid = os.path.join(WORK_DIR, "scores_real_midfall.json")
cmd_mid = [
    PYTHON_BIN, SCORE_PY,
    *mid_clips,
    "--dover_dir", DOVER_DIR,
    "--device", "cuda",
    "--out", out_mid
]
subprocess.run(cmd_mid, check=True)

print("=== Scoring Finished! Analyzing paired differences... ===", flush=True)

with open(out_f0) as f:
    d_f0 = json.load(f)
with open(out_mid) as f:
    d_mid = json.load(f)

# Compute paired differences: mid - f0
metrics = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_norm", "dd_binary"]
comparison = {"per_ball": {}, "summary": {}}

for i, (b, mid_f) in enumerate(ball_configs):
    name_f0 = f"real_ball_{b}_f0_93f.mp4"
    name_mid = f"real_ball_{b}_midfall_dd{mid_f}_93f_orig.mp4"
    
    s_f0 = d_f0[name_f0]
    s_mid = d_mid[name_mid]
    
    ball_diff = {}
    for m in metrics:
        ball_diff[m] = {
            "f0": s_f0[m],
            "mid": s_mid[m],
            "diff": s_mid[m] - s_f0[m]
        }
    comparison["per_ball"][f"ball_{b}"] = ball_diff

for m in metrics:
    diffs = [comparison["per_ball"][f"ball_{b}"][m]["diff"] for b, _ in ball_configs]
    mean_diff = float(np.mean(diffs))
    se_diff = float(np.std(diffs, ddof=1) / np.sqrt(len(diffs)))
    comparison["summary"][m] = {
        "mean_diff": mean_diff,
        "se_diff": se_diff,
        "ci95": [mean_diff - 1.96 * se_diff, mean_diff + 1.96 * se_diff],
        "values": diffs
    }

out_comp = os.path.join(WORK_DIR, "real_video_control_comparison.json")
with open(out_comp, "w") as f:
    json.dump(comparison, f, indent=2)

print("\n=== REAL VIDEO INPUT CONTROL SUMMARY (Midfall - f0) ===")
for m in metrics:
    s = comparison["summary"][m]
    print(f"{m:20s}: Δ = {s['mean_diff']:+.5f} ± {s['se_diff']:.5f} (95% CI: [{s['ci95'][0]:+.5f}, {s['ci95'][1]:+.5f}])")
