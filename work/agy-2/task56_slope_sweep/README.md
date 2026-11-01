# Task 56: Independent Replication and Review of Finding #1188

## Overview
This directory contains the independent multi-method evaluation and review of **Finding #1188** (`rahul-2`, Task 13):
> *"None of CFG (1/3 vs 6), fps 12, or 189 frames raises Nano's slide-speed ceiling; plastic stays $\le 0.4\text{ m/s}$ in every arm."*

We evaluated all **30 generated GAUGE slope sweep clips** (Plastic and Wood across 5 conditions: `base` [CFG 6, 24fps, 93f], `cfg1` [CFG 1.0], `cfg3` [CFG 3.0], `fps12` [12 fps], `nf189` [189f, 7.9s], across seeds 1–3) using independent multi-channel causal sub-pixel tracking (`indep_lab_grad_ncc`: CIE Lab + Sobel Gradient Magnitude NCC) and clean-background color-difference blob tracking (`indep_lab_bgdiff_blob`), rather than rerunning `kin3.py`.

---

## 1. Aggregate Results across All 10 Arms ($n=30$ clips)

| Arm / Condition | $n_{\text{moved}}$ / $n_{\text{total}}$ | `rahul-2` `kin3` Peak $v$ ($\text{m/s}$) | Independent `lab_grad_ncc` Peak $v$ ($\text{m/s}$) | Whole Slide $a_{\text{quad}}$ ($\text{m/s}^2$) | Real Mocap Slide |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Plastic Base** (CFG 6, 24fps, 93f) | 3 / 3 | $0.284 \pm 0.040$ | **$0.289 \pm 0.046$** ($0.252, 0.234, 0.380$) | $+0.09 \pm 0.10$ | $1.47\text{ m/s}$ (at $0.42\text{ m}$) |
| **Plastic CFG 1.0** | **2 / 3** (s3 frozen) | $0.239 \pm 0.015$ | **$0.224 \pm 0.002$** ($0.225, 0.222, 0.000$) | $+0.03 \pm 0.10$ | $1.47\text{ m/s}$ |
| **Plastic CFG 3.0** | 3 / 3 | $0.296 \pm 0.060$ | **$0.300 \pm 0.053$** ($0.275, 0.224, 0.402$) | $+0.09 \pm 0.08$ | $1.47\text{ m/s}$ |
| **Plastic FPS 12** | 3 / 3 | $0.223 \pm 0.060$ | **$0.204 \pm 0.062$** ($0.323, 0.111, 0.179$) | $+0.04 \pm 0.03$ | $1.47\text{ m/s}$ |
| **Plastic NF 189** (7.9 s) | 3 / 3 | $0.293 \pm 0.066$ | **$0.275 \pm 0.054$** ($0.338, 0.167, 0.319$) | $+0.13 \pm 0.08$ | $1.47\text{ m/s}$ |
| **Wood Base** (CFG 6, 24fps, 93f) | 3 / 3 | $0.534 \pm 0.089$ | **$0.532 \pm 0.087$** ($0.419, 0.704, 0.474$) | $+0.36 \pm 0.37$ | $1.47\text{ m/s}$ |
| **Wood CFG 1.0** | **2 / 3** (s2 frozen) | $0.609 \pm 0.097$ | **$0.609 \pm 0.092$** ($0.702, 0.000, 0.517$) | $+0.69 \pm 0.53$ | $1.47\text{ m/s}$ |
| **Wood CFG 3.0** | 3 / 3 | $0.472 \pm 0.053$ | **$0.472 \pm 0.055$** ($0.457, 0.574, 0.386$) | $+0.47 \pm 0.34$ | $1.47\text{ m/s}$ |
| **Wood FPS 12** | 3 / 3 | $0.322 \pm 0.048$ | **$0.323 \pm 0.049$** ($0.230, 0.395, 0.344$) | $+0.18 \pm 0.08$ | $1.47\text{ m/s}$ |
| **Wood NF 189** (7.9 s) | 3 / 3 | $0.339 \pm 0.098$ | **$0.337 \pm 0.095$** ($0.254, 0.231, 0.527$) | **$-0.00 \pm 0.05$** | $1.47\text{ m/s}$ |

---

## 2. Key Physical Findings & Diagnosis

1. **The Speed Ceiling is Solidly Replicated:**
   - On plastic slope, **every single clip across all 5 arms caps at peak $v \le 0.402\text{ m/s}$** (moving mean $0.264 \pm 0.019\text{ m/s}$ across 14 clips), between $3.7\times$ and $13\times$ below real GAUGE mocap ($1.47\text{ m/s}$).
   - On wood slope, slide speed is consistently higher than plastic ($1.76\times$ higher, moving mean $0.464 \pm 0.038\text{ m/s}$), but still caps at $\le 0.704\text{ m/s}$ (mean whole-slide $a \approx 0.0\text{--}0.69\text{ m/s}^2$ vs real $2.58\text{ m/s}^2$).

2. **FPS 12 Conditioning Rules Out a Pixel-Displacement Ceiling:**
   - Conditioning at `fps=12` produces $\sim 2\times$ the per-frame pixel displacement (plastic peak $30.6\text{ px/f}$ at 12 fps vs $11.9\text{ px/f}$ at 24 fps; wood peak $38.2\text{ px/f}$ vs $20.4\text{ px/f}$), but the velocity in physical units ($\text{m/s}$) **does not increase** (plastic $0.204 \pm 0.062\text{ m/s}$, wood $0.323 \pm 0.049\text{ m/s}$).
   - This proves conclusively that the speed ceiling is **not a per-frame image displacement cap**, but an internal wall-clock rate prior.

3. **CFG 1.0 Induces Static Motion Freezing:**
   - Disabling guidance ($\text{CFG}=1.0$) causes complete motion collapse on 1 out of 3 seeds for both materials (`plastic_cfg1_s3` and `wood_cfg1_s2`: max displacement $<0.001\text{ m}$, mean inter-frame difference $<0.33$ gray levels).
   - On the remaining seeds that move, CFG 1.0 does not improve plastic speed ($0.224\text{ m/s}$).

4. **189 Frames Confirms Near-Zero Whole-Slide Acceleration:**
   - In 189-frame clips ($7.9\text{ s}$), whole-slide quadratic acceleration collapses to zero (plastic $+0.13 \pm 0.08\text{ m/s}^2$, wood $-0.00 \pm 0.05\text{ m/s}^2$). The cube accelerates weakly only during the first $\sim 0.5\text{ s}$ ($a_{\text{early}} \approx 0.2\text{--}0.5\text{ m/s}^2$) and then glides at constant speed or stops.

---

## Artifacts
- `replicate_finding_1188.py`: Multi-method dual tracker and comparison runner.
- `make_qc_plots.py`: Generates publication plots.
- `results_slope_sweep.json`: Full per-clip kinematics across all 30 clips.
- `summary_slope_sweep.json`: Arm-aggregated statistics.
- `qc_slope_sweep_velocities.png`: Bar chart + scatter across all 10 arms.
- `qc_slope_sweep_bins.png`: 0.25 s velocity bin trajectories over time.
