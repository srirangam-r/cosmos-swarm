# Task 9: Duration Sweep (`61f / 93f / 189f`) & Gripper-Lowering Artifact Audit (`agy-1`, Shift 3)

## Overview
Evaluates `nvidia/Cosmos3-Nano` across clip durations `num_frames ∈ {61, 93, 189}` (`2.54 s`, `3.88 s`, `7.88 s` at `24 fps`) on the official GAUGE bouncing-ball conditioning frames (`ball1` and `ball2` frame 0, `832x480`, `539.8 px/m`, `steps=35`, `guidance=6.0`, `flow_shift=10.0`, `negative_prompt=null`, `seed=1`).

## Key Findings

### 1. Discrete Regime Switch Across Clip Duration (Not Smooth $g \propto N^{-2}$ Scaling)
 Preregistered in Task 9 (`#685`, `#688`): if Nano stretches a fixed event script to fill the clip duration $T = N / \text{fps}$, free-fall acceleration would scale as $g(N) = g(61)\cdot(61/N)^2$ (`3.39 -> 1.46 -> 0.35 m/s²` across `61 / 93 / 189` frames). Instead, changing `num_frames` switches the **discrete physical failure mode** of the held-ball scene:

| Clip ID | Scene | `num_frames` (`T`) | Seeded `firstfall v1` (`(282,117)`) | `gauge_blind v1.1` (`bclock`) | Dual-Patch Gripper vs. Ball (`f0–42`) | Physical Regime (Verified by Contact Sheets) |
|---|---|---:|---|---|---|---|
| `ball1_nf61_s1` | Ball 1 | `61` (`2.54s`) | `flag="ok"`, `g = 2.75 m/s²` (`[1.77, 3.66]`, `g_hT = 3.26 m/s²`; `3.39 m/s²` on raw MP4) | `release=1`, `flag="ok"`, `g = 3.18 m/s²` (`R²=0.9956`) | Gripper stationary during drop (`Δy_grip(f0..14) = 0 px`, `Δy_sep = +96 px`) | **True release from stationary gripper** (`f3–11`, `2.9–3.6×` slow $g$), then plank tilts & ball flies back into gripper (`f44`). |
| `ball1_nf93_s1` | Ball 1 | `93` (`3.88s`) | `flag="no_free_fall"`, `dAIC = -1.62`, `fall_px = 1.5 px` | **FALSE POSITIVE:** `release=1`, `flag="ok"`, `g = 0.090 m/s²` (`R²=0.9840`) | Gripper lowers `161 px` with ball held (`r = 0.9859`, median `|Δy_sep| = 4.0 px`) | **Gripper lowers with held ball (`f4–38`) & retracts (`f40–68`)** while a 2nd ball spawns on the plank (`f24–92`). |
| `ball2_nf93_s1` | Ball 2 | `93` (`3.88s`) | `flag="no_free_fall"`, `dAIC = -1.89`, `fall_px = 0.0 px` | **FALSE POSITIVE:** `release=1`, `flag="ok"`, `g = 0.031 m/s²` (`R²=0.9959`) | Gripper lowers `162 px` with ball held (`r = 0.9871`, median `|Δy_sep| = 4.5 px`) | **Gripper lowers with held ball (`f4–38`) & retracts (`f40–68`)** while a 2nd ball spawns on the plank (`f8–92`). |
| `ball1_nf189_s1` | Ball 1 | `189` (`7.88s`) | `flag="no_free_fall"`, `dAIC = -2.00`, `fall_px = 0.0 px` | `release=1`, `flag="check"`, `g = null` | Held ball stays high (`Δy_ball = 15 px`, `Δy_sep = 2 px`); large ball (`d≈56 px`) on plank | **Held ball never drops; large substitute ball enters from top edge (`f12–36`)** and sits on plank (`f32–188`). |
| `ball2_nf189_s1` | Ball 2 | `189` (`7.88s`) | `flag="no_free_fall"`, `dAIC = -2.00`, `fall_px = 0.0 px` | `release=1`, `flag="check"`, `g = 5.26 m/s²` (`R²=0.657`) | Held ball stays high (`Δy_ball = 17 px`, `Δy_sep = 3 px`); large ball (`d≈56 px`) on plank | **Held ball never drops; large substitute ball enters from top edge (`f12–36`)** and sits on plank (`f34–188`). |

### 2. Critical Vulnerability in `gauge_blind v1.1` for 93-Frame Evaluations (Task 24 / Task 28)
- In both 93-frame base Nano clips (`ball1_nf93_s1` and `ball2_nf93_s1`), the Franka robot arm bends downward from `f4` to `f38` (`Δy = 161–162 px`) carrying the still-held ball in its jaws (`r(y_gripper, y_ball) = 0.986` and `0.987`, `max_ball_minus_gripper_sep = 0.0 px`), touches the plank, and lifts back up (`f40–68`).
- Because `gauge_blind v1.1` (`tools/gauge_blind/gauge_blind.py`) tracks only the ball patch `(281, 119)` without tracking the gripper above it `(282, 68)`, it scores both 93f clips as `release = 1`, `bclock_flag = "ok"`, `first_fall_r2 = 0.9840` / `0.9959`, and reports spurious ultra-slow `g = 0.090 m/s²` and `0.031 m/s²`!
- **Automated Gate Fix:** Require either `max_ball_minus_gripper_sep_f0_14_px > 40 px` (dual-patch separation) or `firstfall v1` `dAIC_quad_vs_lin > 10` (`flag == "ok"`), which cleanly separates true ball release (`ball1_nf61_s1`: `Δy_sep = +96 px`, `dAIC = +10.1` to `+25.1`) from robot-arm lowering (`ball1/2_nf93_s1`: `Δy_sep = 0.0 px`, `dAIC = -1.62` and `-1.89`).
