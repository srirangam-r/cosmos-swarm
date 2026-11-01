# Task 69: Independent Blind Evaluation of Task 24 LoRA Eval Clips

**Author:** `agy-2`  
**Parent Task:** Task 24 (rahul-3, LoRA fine-tuning and evaluation)  
**Input Clips:** 66 blinded clips from GB10 `~/jobs/rahul-3/eval_clips/`  
**Arms Represented (Blinded):** Base (unmodified Cosmos3-Nano), LoRA A (real-g drop + decay), LoRA B (wrong-g control), LoRA C (no-decay control), plus cross-box repeat base clips.  
**Generation Stack:** `cosmos-framework` `scripts.inference` on 1x H100 PCIe, official GAUGE bouncing-ball frame 0 (`frame.png`, 832x480), 93 frames @ 24 fps, 35 steps, CFG 6.0, flow shift 10, no negative prompt.

---

## 1. Executive Summary

We performed an independent blind kinematic evaluation across all **66 blinded evaluation clips** generated from Task 24 using two independent evaluation suites:
1. The frozen pre-registered scorer `tools/gauge_blind/gauge_blind.py` (`commit 6a68264`, `sha256 2d3ee65444c0` on `bclock` `3cde5a0351a0`);
2. An independent multi-ROI motion profiling and contact sheet tracker (`evaluate_task69_blind.py`) monitoring gripper retention, corridor occupancy, plank impact level, and 24-tile high-resolution contact sheets (`sheets/<clip_id>_sheet.jpg`).

### Key Findings
- **Zero Genuine Releases Across All 66 Clips:**
  - **Release Rate:** **`0 / 66` (0.0%, 95% Wilson CI: `[0.0%, 5.4%]`)**.
  - Not a single clip out of 66 clips released the held ball from the Franka gripper jaws into free fall down to the plank.
- **Behavioral Breakdown Across All 66 Clips:**
  - **`held_frozen` (60 / 66, 90.9%):** The ball remains bit-level static in the gripper jaws ($y = 119 \pm 2$ px; mean gripper patch difference $< 3.5$ gray levels; corridor and plank differences $< 5.0$ gray levels).
  - **`held_minor_noise` (3 / 66, 4.5%):** `213cda`, `714e0d`, `f2abd9`. Minor latent or background flicker, but the ball remains clamped in the gripper jaws across all 93 frames.
  - **`phantom_duplicate` (2 / 66, 3.0%):** `808ef1` and `f690ef`. The held ball remains fully clamped in the gripper jaws, while an unphysical phantom clone ball spawns on the plank surface ($y \approx 365$ px; plank diff up to $55.5$ gray levels) and undergoes brief bouncing/fading.
  - **`gripper_arm_twitch` (1 / 66, 1.5%):** `c99152`. The mechanical gripper arm base undergoes a vertical twitch ($y$ displacement $\approx 50$ px) around frame 30–45, but the fingers never open and the ball returns to rest in the gripper at frame 92 (end gripper diff $1.33$ gray levels).
- **First-Fall Gravity ($g$) & Bounce Restitution ($e_T$):**
  - Because no clip achieved genuine release into free fall down to the plank, **first-fall gravity $g$ is undefined (scorable clips = 0 / 66)**, and **rebound restitution is undefined**.
- **Conclusion for Candidate Fix (LoRA A/B/C):**
  - Fine-tuning Cosmos3-Nano on synthetic ball drops (`sim_drop v1`, 1000 clips) **completely fails to transfer to held-object release from real Franka gripper conditioning frames**.
  - Neither Arm A (real-g), Arm B (wrong-g control), Arm C (no-decay control), nor Base breaks the held-ball anchoring prior.
  - Release failure is an initial conditioning frame failure mode that cannot be solved by ballistic SFT data without gripper-release dynamics or mid-fall conditioning.

---

## 2. Quantitative Results & Auto Scorer Comparison

| Metric | Frozen `gauge_blind.py` (ro-1) | Independent Multi-ROI Audit (`evaluate_task69_blind.py`) | Binding Eye QC Call |
|---|---|---|---|
| **Total Clips Evaluated** | 66 | 66 | 66 |
| **Auto-Release Flag == 1** | 3 / 66 (4.5%) | 0 / 66 (0.0%) | **0 / 66 (0.0%)** |
| **Genuine Gravitational Release** | 0 / 66 (0.0%) | 0 / 66 (0.0%) | **0 / 66 (0.0%)** |
| **Held Static in Gripper** | 63 / 66 (95.5%) | 63 / 66 (95.5%) | **63 / 66 (95.5%)** |
| **Phantom Duplicate Spawning** | Not detected by bclock | 2 / 66 (3.0%) | **2 / 66 (3.0%)** |
| **Mechanical Arm Twitch** | Flagged as auto-release | 1 / 66 (1.5%) | **1 / 66 (1.5%)** |
| **Scorable Free-Fall $g$** | 0 / 66 (None) | 0 / 66 (None) | **0 / 66 (None)** |
| **At Rest at Frame 92** | 66 / 66 (100.0%) | 66 / 66 (100.0%) | **66 / 66 (100.0%)** |

### Audit of the 3 Auto-Release False Positives in `gauge_blind.py`
1. `7a02e8.mp4` (auto drop = 58.3 px, $g = \text{None}$):
   - Gripper patch difference between frame 0 and frame 92 is $3.46$ gray levels.
   - Plank difference is $1.79$ gray levels (zero motion at table level).
   - Visual inspection confirms the ball remained in the gripper; minor arm base drift caused template search to slide along the robot wrist.
2. `ddcc26.mp4` (auto drop = 25.9 px, $g = \text{None}$):
   - Gripper patch difference is $0.79$ gray levels (bit-identical ball patch).
   - Plank difference is $1.80$ gray levels.
   - Rest position is $-41.0$ px relative to impact level (i.e. at $y = 145$ px in the gripper).
3. `f690ef.mp4` (auto drop = 26.0 px, $g = \text{None}$):
   - Held ball in gripper remains clamped at $y = 119$ (gripper diff $2.69$ gray levels).
   - At frame 60, a phantom duplicate dark blob ($909$ px area) spawns directly on the plank at $y = 365.3, x = 303.3$ (plank diff $67$ gray levels).
   - This is an unphysical duplicate clone, not a release of the held ball.

---

## 3. Files and Artifacts

- `task69_blind_scores.csv`: Per-clip table with metrics for all 66 blinded clips.
- `task69_blind_results.json`: Full JSON record with ROI kinematic metrics and classifications.
- `ro1_gauge_blind_scores.csv`: Output from the frozen `tools/gauge_blind/gauge_blind.py` scorer.
- `ro1_gauge_blind_tracks.json`: Trajectory outputs from `bclock`.
- `evaluate_task69_blind.py`: Independent multi-ROI evaluation script.
- `sheets/`: 24-frame contact sheets for all 66 clips showing the cropped interaction corridor ($x \in [180, 380], y \in [80, 420]$).
