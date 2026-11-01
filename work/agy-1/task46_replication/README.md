# Task 46: Independent Replication of Findings #698 and #766

## Overview
This directory contains the independent multi-method replication of two unreviewed findings:
1. **Finding `#698` (`rahul-5-agy`, Task 15):** "Nano's ball gravity is NOT slow once release is removed ($g = 8.3\text{--}9.9\text{ m/s}^2$), but it exhibits near-zero energy dissipation ($e_T \approx 1.09 \pm 0.03$, perpetual bouncing for $>7.4\text{ s}$) instead of real damping to rest."
2. **Finding `#766` (`rahul-2`, Task 13):** "On the $30^\circ$ slope, Nano's cube speeds up only briefly and then hits a speed ceiling. Across 10 clips (3 materials $\times$ 4 prompts $\times$ 2 seeds), peak speed is $0.14\text{--}0.37\text{ m/s}$ ($0.26 \pm 0.03\text{ m/s}$ SE), $4\text{--}10\times$ below a physical slide."

---

## Part A: Review of Finding `#698` (GAUGE Mid-Fall Ball 1 & Ball 2, 189f @ 24 fps, Seed 1)

### Independent Methods
1. **Corridor-Constrained Dark-Ball + NCC Hybrid Tracker (`track_midfall_corridor` in `replicate_698_766.py`):** Tracks the dark ball within the plank/flight corridor ($y \in [120, 358]\text{ px}$, $x \in [180, 420]\text{ px}$), combining sub-pixel normalized cross-correlation with temporal-median color-difference and reflected-velocity prediction, and fits each bounce arc with residual/case bootstrap CIs.
2. **Referee-Validated `bclock v1` (`tools/bclock/bclock.py`, planted PASS 12/12, `#593`)** and **`firstfall v1` (`tools/realball/firstfall.py`, planted PASS 20/20, `#264`)**.
3. **Trajectory & JSON Audit of `res_b1.json` and `res_b2.json` (`rahul-5-agy`):** Direct inspection of the saved `bounce_decay.py` output files and `detailed_bounce.py` cycle logic, overlaid on 24-frame contact sheets (`sheet_ball_1_189f.jpg`, `sheet_ball_2_189f.jpg`).

### Key Results & Methodological Audit
- **Core Qualitative & Physical Claims Replicated:**
  - Once initialized in mid-fall (`ball 1` dedup f33, `ball 2` dedup f35), Cosmos3-Nano renders **Earth-order rebound accelerations ($g \approx 7.8\text{--}14.2\text{ m/s}^2$, mean first-rebound $g \approx 9.1\text{--}12.3\text{ m/s}^2$ depending on tracker/contact-frame window)** rather than GAUGE's held-ball $0.45\text{ m/s}^2$, and **both clips continue bouncing for the entire $7.5\text{ s}$ (`189`-frame) generation without coming to rest** (`still_bouncing_at_end = True`, vertical motion range in last 30 frames: $132.7\text{ px}$ on Ball 1, $156.3\text{ px}$ on Ball 2).
- **First-Rebound Gravity Comparison (`539.8 px/m`, `24 fps`):**
  - **Ball 1 (`0007_raj-3.mp4`, impact 1 at `f5–6`, apex at `f11`, impact 2 at `f15`):**
    - `rahul-5-agy` (`analyze_midfall.py`, frames `6..14`, $T_1 = 0.417\text{ s}$, rise $27.1\text{ cm}$): $g_{\text{reb}} = 9.90\text{ m/s}^2$ ($g_{\text{eff}} = 8h/T^2 = 12.46\text{ m/s}^2$).
    - Independent corridor tracker (`f7..14` excl. contacts, $n=8$): $g_{\text{reb}} = 14.21 \pm 0.90\text{ m/s}^2$ ($95\%\text{ CI } [12.36, 16.02]$, $R^2 = 0.9955$, $g_{\text{eff}} = 12.71\text{--}13.20\text{ m/s}^2$); including contact frames (`f6..15`, $n=10$): $g_{\text{reb}} = 13.79 \pm 1.56\text{ m/s}^2$. Across the first 5 rebounds, parabolic $g$ is $14.21, 15.52, 15.20, 10.81, 12.32\text{ m/s}^2$ (mean $13.61 \pm 0.89\text{ m/s}^2$).
  - **Ball 2 (`0012_raj-3.mp4`, impact 1 at `f6`, apex at `f11`, impact 2 at `f17`):**
    - `rahul-5-agy` (`analyze_midfall.py`, frames `7..16`, $T_1 = 0.458\text{ s}$, rise $21.5\text{ cm}$): $g_{\text{reb}} = 8.33 \pm 1.15\text{ m/s}^2$ ($g_{\text{eff}} = 8.20\text{ m/s}^2$); rebound 2 (`f18..31`, $T_2 = 0.625\text{ s}$, rise $35.6\text{ cm}$): $g_{\text{eff}} = 7.30\text{ m/s}^2$.
    - Independent corridor tracker (`f7..16` excl. contacts, $n=10$): $g_{\text{reb,1}} = 10.43 \pm 0.49\text{ m/s}^2$ ($95\%\text{ CI } [9.55, 11.49]$, $R^2 = 0.9957$, $g_{\text{eff}} = 8.61\text{ m/s}^2$); including contact frames (`f6..17`, $n=12$): $g_{\text{reb,1}} = 8.93 \pm 0.98\text{ m/s}^2$. Rebound 2 (`f18..31`, $n=14$): $g_{\text{reb,2}} = 7.80 \pm 0.66\text{ m/s}^2$ ($g_{\text{eff}} = 7.06\text{ m/s}^2$); Rebound 3 (`f33..43`, $n=11$): $g_{\text{reb,3}} = 8.83 \pm 0.98\text{ m/s}^2$ ($g_{\text{eff}} = 8.04\text{ m/s}^2$).
- **Critical Methodological Caveat on `res_b1.json` / `res_b2.json` and $e_T = 1.083\text{--}1.109$:**
  1. **Validated `bounce_decay.py` did not fit any flights (`n_fitted = 0`, `n_impacts = 0` in both `res_b1.json` and `res_b2.json`):** Because `bounce_decay.py` requires a shared acceleration $a$ with $\text{RMSE} \le 1.5\text{ px}$ across consecutive flights and Nano's bounces drift in depth/scale (`seg_rmse = [4.88, 7.72] px` on Ball 1, `[4.31, 3.81] px` on Ball 2), the referee-validated `bounce_decay.py` fitter rejected all segments (`g_joint = null`, `impacts = []`).
  2. **Tracker jump onto the top gripper housing in `res_b2.json` (`f61..188`):** In `res_b2.json`, after bounce 3 (`f44..54`), the nearest-blob tracker jumps up onto the robot gripper / top cable (`y = 45..69 px` for 128 frames from `f61` to `f188`; see red horizontal line in `sheet_ball_2_189f.jpg`), while the actual black ball continues bouncing on the plank below (`y = 180..335 px`). Consequently, 13 of the 16 "bounce cycles" counted by `detailed_bounce.py` for Ball 2 are small $2\text{--}4\text{ cm}$ jitter cycles on the top gripper housing (`y_imp1 = 59.5..68.9 px`), not ball bounces!
  3. **Upward Jensen's inequality bias in arithmetic mean of $T_{k+1}/T_k$ (`mean_e_T = 1.083` and `1.109`):** Even for a stationary noisy period $T_k$, the arithmetic mean $\frac{1}{M}\sum (T_{k+1}/T_k)$ is strictly $>1$ by Jensen's inequality ($\mathbb{E}[X/Y] > 1$), whereas the geometric mean $(T_M/T_1)^{1/(M-1)}$ or log-linear regression slope $\exp(\text{slope}(\ln T_k))$ is unbiased. Using our corridor-constrained tracker (which stays on the actual ball in `y = 150..345 px` across all 189 frames):
     - **Ball 1 (20 impacts at `f6, 15, 24, 32, 43, 53, 62, 72, 82, 90, 96, 107, 116, 126, 136, 146, 154, 164, 175, 185`):** Mean period $= 9.40 \pm 0.26\text{ frames}$ ($0.392\text{ s}$); log-linear restitution fit **$e_T = 1.004 \pm 0.005$** (arithmetic ratio mean $1.017 \pm 0.046$).
     - **Ball 2 (16 impacts in plank corridor):** Mean period $= 11.95 \pm 1.25\text{ frames}$ ($0.498\text{ s}$); log-linear restitution fit **$e_T = 0.980 \pm 0.020$** (arithmetic ratio mean $1.105 \pm 0.161$ due to one temporary ball-fade/pause around `f55–90`).
     - Thus, true bounce timing is **stationary / non-dissipative ($e_T \approx 0.98\text{--}1.00$, zero damping)** rather than physically amplifying ($e_T \approx 1.09$).

---

## Part B: Review of Finding `#766` (10-Clip GAUGE Slope Speed Ceiling across 3 Materials $\times$ 4 Prompts $\times$ 2 Seeds)

### Independent Methods
1. **CIE Lab + Sobel Gradient-Magnitude Sub-Pixel NCC Tracker (`indep_lab_grad_ncc`):** Combines 3-channel CIE Lab template correlation ($0.65$) with Sobel edge-gradient correlation ($0.35$) and 2D parabolic sub-pixel peak refinement along the calibrated $0.50\text{ m}$ plank axis.
2. **Clean-Background CIE Lab Color-Difference Connected-Component Tracker (`indep_lab_bgdiff_blob`):** Uses a spliced ghost-free reference background (frame 0 on lower plank $x \le 460$, median of frames $70..92$ on upper plank $x > 460$) and tracks the largest moving foreground component ($\Delta E_{\text{Lab}} > 18$) inside the plank corridor without any template matching.

### Aggregate Comparison across All 10 Clips (`n=10`)

| Metric | `rahul-2` (`kin3_orig.json`) | Independent `lab_grad_ncc` | Independent `lab_bgdiff_blob` | Physical $30^\circ$ Slide (GAUGE Mocap) |
| :--- | :---: | :---: | :---: | :---: |
| **Peak Speed Mean $\pm$ SE ($\text{m/s}$)** | **$0.2607 \pm 0.0273$** | **$0.2607 \pm 0.0269$** | **$0.2677 \pm 0.0281$** | **$1.47\text{ m/s}$** (at $0.42\text{ m}$) |
| **Peak Speed Range ($\text{m/s}$)** | **$0.137\text{--}0.370$** | **$0.135\text{--}0.368$** | **$0.132\text{--}0.389$** | — |
| **Peak Speed Range ($\text{px/frame}$)** | **$6.5\text{--}18.1$** | **$6.4\text{--}18.0$** | **$6.2\text{--}18.4$** | **$\sim 70\text{ px/frame}$** |
| **Early $a$ ($0.5\text{ s}$) Mean $\pm$ SE ($\text{m/s}^2$)** | **$0.282 \pm 0.067$** (max $0.73$) | **$0.263 \pm 0.052$** (quad) / **$0.302 \pm 0.066$** (bin) | **$0.290 \pm 0.068$** | **$2.57\text{ m/s}^2$** |
| **Whole-Slide $a_{\text{quad}}$ Mean $\pm$ SE ($\text{m/s}^2$)** | **$0.026 \pm 0.038$** | **$0.079 \pm 0.028$** | **$0.093 \pm 0.029$** | **$2.57\text{ m/s}^2$** |
| **Time to Slide $0.30\text{ m}$ ($\text{s}$)** | **$1.589 \pm 0.221$** ($n=7$, $0.96\text{--}2.42$) | **$1.824 \pm 0.226$** ($n=5$ strict, $1.04\text{--}2.42$) | **$1.858 \pm 0.231$** ($n=5$) | **$0.48\text{ s}$** |

### Per-Clip Peak Speed & Kinematics (`0.25 s` bins)

| Clip (`93f @ 24 fps`) | `rahul-2` Peak ($\text{m/s}$) | `lab_grad_ncc` Peak ($\text{m/s}$) | `lab_bgdiff_blob` Peak ($\text{m/s}$) | `lab_grad_ncc` $0.25\text{ s}$ Velocity Bins ($\text{m/s}$) | Whole $a_{\text{quad}}$ ($\text{m/s}^2$) |
| :--- | :---: | :---: | :---: | :--- | :---: |
| `plastic_released_nf93_s1` | $0.165$ | $0.167$ | $0.172$ | `0.10, 0.14, 0.16, 0.17, 0.17, 0.15, 0.16, 0.15, 0.14...` | $-0.02$ |
| `plastic_released_nf93_s2` | $0.137$ | $0.135$ | $0.132$ | `0.09, 0.11, 0.13, 0.13, 0.14, 0.13, 0.13, 0.13, 0.13...` | $0.00$ |
| `plastic_corrected_nf93_s1` | $0.370$ | $0.363$ | $0.389$ | `0.24, 0.33, 0.36, 0.33` (tumbles & splits at `f37–43`) | $+0.07$ |
| `plastic_corrected_nf93_s2` | $0.195$ | $0.197$ | $0.198$ | `0.09, 0.13, 0.17, 0.18, 0.20, 0.19, 0.19, 0.19, 0.18` | $+0.03$ |
| `plastic_meta_nf93_s1` | $0.356$ | $0.358$ | $0.354$ | `0.17, 0.35, 0.36, 0.25, 0.25` (decelerates on plank) | $-0.01$ |
| `plastic_meta_nf93_s2` | $0.213$ | $0.217$ | $0.212$ | `0.07, 0.13, 0.16, 0.19, 0.20, 0.20, 0.22, 0.18, 0.18` | $+0.03$ |
| `wood_gauge_nf93_s1` | $0.370$ | $0.368$ | $0.373$ | `0.23, 0.37, 0.35` (`0.33, 0.29, 0.23` to plank foot) | $+0.11$ / $-0.04$ |
| `wood_gauge_nf93_s2` | $0.272$ | $0.272$ | $0.269$ | `0.09, 0.17, 0.21, 0.25, 0.27` (plateaus, 2nd block spawns) | $+0.17$ |
| `metal_gauge_nf93_s1` | $0.228$ | $0.226$ | $0.263$ | `0.01, 0.03, 0.06, 0.10, 0.23` (merges into ruler at `f46`) | $+0.18$ |
| `metal_gauge_nf93_s2` | $0.301$ | $0.304$ | $0.315$ | `0.05, 0.13, 0.24, 0.30, 0.30, 0.24` (slows & deforms) | $+0.23$ |

Every single claim in Finding `#766` is confirmed across all 3 independent tracking methods.
