# Task 104: Independent Replication and Review of Finding 2407 (Task 42 Chained I2V Generations vs Continuous Control)

**Author:** agy-2  
**Date:** 2026-11-01  
**Target Finding:** Finding #2407 by `agy-4` (Task 42, commit `8780f81`)  
**Status:** Completed (Replicated physics negative finding; Refuted 5-frame seam velocity stagnation)

---

## 1. Executive Summary

We performed an independent, methodologically separate replication and audit of **Finding #2407** across all generations from Task 42 (Chained 185-frame generation `chained_s1_185f.mp4` vs continuous 189-frame control `midfall_ball1_dd33_noneg_s1.mp4`, Segment 1 `ball_F_ball1_fps24_93f_s1.mp4`, and Segment 2 `20261101T043944_0037_codex-1.mp4`):

1. **Replicated (Core Physics Negative Finding):**
   - Chaining short I2V segments **fails to restore dissipative bounce decay or enable settling to rest**.
   - Both the chained 185-frame arm ($0\%$ settled, $25$ impacts, mean cycle period $6.7\text{ f} = 0.28\text{ s}$, apex height ratio $e_h = 1.346$) and the continuous 189-frame control ($0\%$ settled, $23$ impacts, mean cycle period $8.1\text{ f} = 0.34\text{ s}$, apex height ratio $e_h = 1.007$) exhibit perpetual undamped bouncing limit cycles through frame 185/189 ($7.7\text{--}7.9\text{ s}$).
   - Decisively refutes the serial-event hypothesis ([arXiv:2607.13031](https://arxiv.org/abs/2607.13031)) as an inference-time solution for world model energy dissipation.

2. **Refuted (The 5-Frame Velocity Stagnation Seam Artifact):**
   - Finding #2407 reported that I2V chaining introduces a *"5-frame velocity stagnation seam artifact ($v \approx 0$ displacement $< 0.1\text{ px}$ for f0–f4 of segment 2, then sudden table plunge at f5)"*, which scout-1 in Message #2415 hypothesized might reflect the 5-frame causal VAE latent group structure ($1 + 4\text{ frames}$).
   - **Root Cause Identified:** In `tools/track_ball_corridor` (`analyze_chain_vs_control.py`, lines 40–55), connected-component filtering strictly required `60 < area < 1200`. In frames 0 to 4 of Segment 2, the ball impacts and contacts the wooden plank surface at $y \approx 346\text{--}348\text{ px}$, merging with the dark table edge / support plank shadow into components exceeding $1200\text{ px}$ or fragmenting below $60\text{ px}$.
   - As a result, the tracker returned `missing: True` with uninitialized coordinates $(0.0, 0.0)$ for frames 0 to 4.
   - At frame 5, when the ball rebounded to $y = 331.3\text{ px}$, it detached from the plank and passed the filter at $(299.9, 396.0)$. The reported "496.7 px drop" was literally `np.hypot(299.88, 395.98) = 496.72 px` from the $(0, 0)$ origin!
   - Under independent sub-pixel tracking, the ball exhibits **continuous physical motion throughout frames 0 to 5**:
     - Frame 0: $y = 346.4\text{ px}$ (touching plank surface)
     - Frame 1: $y = 346.7\text{ px}$
     - Frame 2: $y = 347.7\text{ px}$ (maximum plank impact)
     - Frame 3: $y = 345.1\text{ px}$ (rebound upward, $v_y = -2.5\text{ px/f}$)
     - Frame 4: $y = 346.8\text{ px}$
     - Frame 5: $y = 331.3\text{ px}$ (rising upward, $v_y = -15.5\text{ px/f}$)
     - Frame 6 to 13: rises to apex at $y = 264.1\text{ px}$ (rebound height $\Delta y = 83.6\text{ px}$).
   - There is **no velocity freeze, no stagnation, and no sudden plunge**. Scout-1's VAE latent boundary hypothesis is refuted; the artifact was purely measurement error.

---

## 2. Quantitative Comparison Table

| Metric | Chained Arm (185f) | Continuous Control (189f) | Replication Verdict |
| :--- | :---: | :---: | :---: |
| **Total Frames** | 185 | 189 | Verified |
| **Total Impacts Detected** | 25 | 23 | Replicated (Perpetual bouncing) |
| **Mean Impact Interval** | $6.7\text{ f}$ ($0.28\text{ s}$) | $8.1\text{ f}$ ($0.34\text{ s}$) | Replicated ($8\text{ f}$ limit cycle) |
| **Apex Height Ratio $e_h$** | $1.346 \pm 0.38$ | $1.007 \pm 0.12$ | Replicated ($e_h \ge 1.0$) |
| **Settling to Rest at Horizon** | **NO ($0\%$)** | **NO ($0\%$)** | **REPLICATED (0/2 arms settled)** |
| **Seam Stagnation (Frames 0–4)** | **$v_y \ne 0$ (Continuous)** | N/A | **REFUTED (Tracker bug)** |
| **DOVER Fused Delta** | $+0.0028$ ($0.5398$ vs $0.5370$) | Base reference | Replicated (within seed noise) |
| **Dynamic Degree (norm) Delta** | $-0.256$ ($1.162$ vs $1.419$) | Base reference | Replicated (both low motion) |

---

## 3. Evidence Artifacts

- Comprehensive execution script: [`replicate_finding_2407.py`](replicate_finding_2407.py)
- Structured results: [`task104_review_results.json`](task104_review_results.json)
- Trajectory Comparison Plot: [`plots/trajectory_chained_vs_control.png`](plots/trajectory_chained_vs_control.png)
- Seam Kinematics & Velocity Audit: [`plots/seam_kinematics_audit.png`](plots/seam_kinematics_audit.png)
- 12-Panel Seam Contact Sheet: [`plots/seam_contact_sheet.jpg`](plots/seam_contact_sheet.jpg)
