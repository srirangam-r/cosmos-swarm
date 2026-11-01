# Task 90: RoPE Spatial Frequency Scaling Experiment on GAUGE Held-Ball Frame 0

## Background & Hypothesis
In stock Cosmos3-Nano, when conditioned on frame 0 where an object is clamped by a mechanical holder/gripper (e.g., Franka robotic arm in GAUGE), the model exhibits a 100% release deadlock (0/31 baseline clips release). Instead, it spawns phantom duplicate clones (100% on Seed 1) or plunges the robotic arm into the table.

According to the spatial anchoring hypothesis (arXiv:2609.23658, Raj #696 item 1, human steering nail #1825):
> Early in denoising, frames compete over where the object is; positions that settle early anchor the other frames through RoPE spatial decay, producing "stays in mid-air" and "freezes".
> Fix: scale the RoPE height/width frequencies by about 0.7 during the first ~10% of steps.

This intervention tests whether relaxing the spatial frequency decay early in denoising allows the ball to detach and fall from the gripper from the original frame 0 (preserving baseline inputs).

## Experimental Setup
- **Model:** `nvidia/Cosmos3-Nano` (diffusers bf16, native scheduler UniPCMultistepScheduler with flow_shift 10.0).
- **Conditioning Image:** Fixed baseline GAUGE Ball 1 frame 0 (`work/raj-1/gauge_ball/gauge_ball1_f0_832x480.png`).
- **Prompt:** GAUGE official bouncing ball prompt (neutral, no negative prompt).
- **Resolution:** 832x480, 93 frames @ 24 fps, 35 steps, CFG 6.0, flow shift 10.0.
- **Arms:**
  - **Control:** Baseline standard RoPE (spatial scale 1.0 across all 35 steps).
  - **Treatment (RoPE 0.7x):** RoPE height and width frequencies scaled by 0.7 during the first 4 denoising steps ($t \ge 900.0$), and standard 1.0 thereafter.
- **Seeds:** 4 matched seeds: 1, 2, 3, 4 (8 clips total).
- **Hardware:** Running on GB10 board (`promaxgb10-99b5`, 128 GB unified memory).
- **Background Job:** Host `board.tail0c526a.ts.net`, PID `445545`, log `~/jobs/ro-agy1/task90_rope_scale/experiment.log`.

## Evaluation Plan
1. Visual inspection: Ball detachment rate vs gripper clamping, phantom duplicate cloning rate.
2. Kinematic tracking: Referee-validated `tools/realball/firstfall.py` (free-fall acceleration $g$, onset frame, fit flags).
3. NVIDIA Scoreboard: `tools/nv_scoreboard/score.py` (DOVER Technical, Aesthetic, Fused, Dynamic Degree).
