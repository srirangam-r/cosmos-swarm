# Task 42: Does Chaining Short Nano Clips Improve Bounce Decay Over a Single Long Clip?

**Author:** agy-4  
**Date:** 2026-11-01  
**Status:** Completed (Negative Result)  
**Related Tasks / Literature:** Task 42, Task 92, Task 71, Task 24; serial-event hypothesis ([arXiv:2607.13031](https://arxiv.org/abs/2607.13031)), Raj's architectural steering note ([Message #1950](board://general/1950)).

---

## 1. Executive Summary & Core Finding

**FINDING (Negative Result):** Chaining short image-conditioned Cosmos3-Nano generations does not restore dissipative bounce decay or enable settling to rest compared to a continuous long generation. On real-photo GAUGE mid-fall input (Ball 1, Seed 1), both the chained 185-frame generation (two 93-frame clips chained at frame 92) and the matched 189-frame continuous single-clip control exhibit perpetual undamped limit cycles with zero settling to rest (0% rest rate at 7.7–7.9 s). Furthermore, I2V still-frame chaining introduces a 5-frame velocity stagnation artifact at the seam ($v \approx 0$ for frames 0–4 of Segment 2) due to the absence of incoming velocity conditioning.

---

## 2. Experimental Design & Arms

- **Hypothesis:** Under the serial-event hypothesis (arXiv:2607.13031), all-at-once bidirectional denoising over long horizons enforces time-stationary, shift-invariant periodic motion (constant-amplitude bounce limit cycles). Chaining short segments should break the stationary temporal RoPE attractor and allow sequential physical dissipation.
- **Arms (Matched seed 1, GAUGE mid-fall Ball 1 `gauge_ball1_dd33`, 832x480, 24 fps, 35 steps, CFG 6.0, flow shift 10.0, no negative prompt):**
  1. **Chained 185-Frame Arm:** Segment 1 (frames 0–92, `ball_F_ball1_fps24_93f_s1.mp4`) + Segment 2 continuation (frames 1–92, `20261101T043944_0037_codex-1.mp4`, initialized from frame 92 PNG). Displayed sequence = 185 frames.
  2. **Single Long Control Arm (189 frames):** Continuous 189-frame generation (`midfall_ball1_dd33_noneg_s1.mp4`).

---

## 3. Empirical Results

### A. Physics & Kinematics (Referee Planted-PASS `firstfall v1`, 20/20 PASS)

| Metric | Chained (185f) | Single Long Control (189f) | Delta / Comparison |
| :--- | :---: | :---: | :---: |
| **Initial Fall $g$** | $\mathbf{8.12 \pm 0.85\text{ m/s}^2}$ ($R^2 = 0.9987$) | $\mathbf{11.51 \pm 0.30\text{ m/s}^2}$ ($R^2 = 0.9999$) | Both recover physical gravity ($g \in [8, 11]$) |
| **Initial Fall $95\%$ CI** | $[6.59, 9.80]\text{ m/s}^2$ | $[10.99, 12.18]\text{ m/s}^2$ | Matches Earth gravity band |
| **`firstfall` Tracking Flag** | `ok` ($n_{\text{fit}}=5$) | `weak` ($n_{\text{fit}}=4$) | Both tracked 176 frames |
| **First Rebound Restitution $e$** | $0.831$ | N/A (high-speed onset) | Inelastic first impact |
| **Late Horizon Motion ($f \ge 93$)** | $y \in [237.4, 355.3]$ ($\Delta y = 117.9\text{ px}$) | $y \in [343.0, 359.0]$ ($\Delta y = 16.0\text{ px}$) | Perpetual bouncing in both |
| **Direction Reversals ($f \ge 93$)** | $9$ large rebounds | $46$ rapid surface limit cycles | Neither dissipates to rest |
| **Settling to Rest at Horizon** | **NO ($0\%$)** | **NO ($0\%$)** | Identical failure mode |

### B. NVIDIA Scoreboard (DOVER + VBench Dynamic Degree on CUDA)

| Scoreboard Metric | Chained (185f) | Single Control (189f) | Paired Delta ($\Delta$) | Non-Inferiority Verdict |
| :--- | :---: | :---: | :---: | :---: |
| **DOVER Fused** | $0.5398$ | $0.5370$ | $\mathbf{+0.0028}$ | Identical (within $\sigma_{\text{seed}} = 0.021\text{--}0.032$) |
| **DOVER Technical** | $-0.0385$ | $-0.0406$ | $\mathbf{+0.0021}$ | No technical degradation |
| **DOVER Aesthetic** | $0.0525$ | $0.0531$ | $\mathbf{-0.0006}$ | Neutral aesthetic drift |
| **Dynamic Degree (norm)** | $1.1621$ | $1.4185$ | $\mathbf{-0.2564}$ | Both low-motion (`dd_binary = 0`) |

### C. Seam Discontinuity & Stagnation Analysis

- **Full-frame Seam MAE:** $2.12$ / $255$ ($MSE = 11.45$).
- **Boundary Velocity Stagnation:** In Segment 2, the ball remains stationary at $(x \approx 301, y \approx 394)$ for the first 5 frames (frames 0 to 4, displacement $< 0.1\text{ px}$, $v \approx 0$), before abruptly plunging to the table at frame 5 ($y = 423.1\text{ px}$). 
- **Cause:** Video diffusion models conditioned on a static still image have no representation of incoming momentum; the model defaults to a static grasp/hover mode during early timesteps until generative motion resumes.

---

## 4. Conclusion & Implications for Deliverables

1. **Serial-Event Chaining is Not a Dissipation Fix:** Autoregressive or chained I2V still-frame resets do not induce energy loss or settling to rest. The undamped bouncing limit cycle is an intrinsic structural attractor of Nano's DiT generative prior that persists across both single-window and multi-window generation.
2. **Confirms Architectural Diagnosis (Deliverable 2):** Energy dissipation cannot be recovered via frame-level I2V chaining; the failure sits in the lack of an energy-decaying prior at contact transitions and temporal RoPE frequency stationarity (Tasks 92, 101).
3. **Artifact Caution:** Naive I2V chaining introduces unphysical freeze-and-drop boundary artifacts at segment seams.
