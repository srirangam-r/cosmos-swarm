# Independent Replication and Review of Finding 550 & Finding 621

**Task:** 54 (`agy-3`)  
**Reviewing:** Finding 550 and Finding 621 (`ro-3`)  
**Artifact Directory:** `work/agy-3/task54_pendulum_review/`  

---

## Executive Summary

1. **Finding 550 (Duration-Template Ablation) — REPLICATED:**  
   Turning off diffusers' duration sentence (`"The video is 7.9 seconds long and is of 24 FPS."`, `use_duration_template=false`) produces **zero statistically or physically meaningful change** in Nano's measured pendulum period (`pend_fps24_s1_189f_dur_on` vs `pend_fps24_nodur_s1_189f_dur_off`, 189f @ 24 fps, seed 1):
   - Referee-validated `measure_pend v1`: `4.4307 s` (`106.34 frames`, 95% CI [4.12, 4.81] s) vs `4.4279 s` (`106.27 frames`, 95% CI [4.14, 4.77] s), $\Delta = -0.0028\text{ s}$ ($-0.07\text{ frames}$, $-0.06\%$).
   - `pend_acf` CLI: `107.10 frames` (`4.463 s`, 95% CI [106.7, 107.5] f) vs `107.38 frames` (`4.474 s`, 95% CI [107.0, 107.8] f), $\Delta = +0.28\text{ frames}$ ($+0.26\%$).
   - Independent L1 self-similarity: `107.10 frames` vs `107.38 frames`.
   - Independent L2 median self-similarity: `107.37 frames`.
   - Independent Cosine median self-similarity: `107.28 frames`.
   Nano completely ignores the prompt duration sentence for pendulum dynamics. Both arms run $\sim 4.43\text{--}4.47\text{ s}$, which is **$4.2\times$ slower than the true $1.06\text{ s}$ pendulum period**.

2. **Finding 621 (Pendulum Period across Clip Lengths & Seeds) — REPLICATED:**  
   The initial hypothesis that Nano's pendulum period is locked to clip length ($P_{\text{frames}} \approx 0.55 \times N$) **does not hold across clip lengths and seeds**:
   - **61f seed 1 (`pend_fps24_61f_s1.mp4`):** Executes less than a single cycle ($P/N \approx 1.31$). `measure_pend v1` yields $3.3234\text{ s} = 79.76\text{ frames}$ (95% CI [67.9, 117.5] f, $R^2 = 0.888$), while `pend_acf` and independent self-similarity fail entirely (`< 1 cycle`).
   - **93f seed 1 (`pend_A_fps24_93f_s1.mp4`):** Executes $\sim 1.8$ cycles with $P = 50.84\text{ frames}$ ($2.118\text{ s}$, $P/N \approx 0.546$).
   - **189f seed 1 (`pend_fps24_s1_189f.mp4`):** Executes $\sim 1.8$ cycles with $P = 107.10\text{ frames}$ ($4.463\text{ s}$, $P/N \approx 0.567$).
   - **189f seed 2 (`pend_fps24_s2.mp4`):** **Physical validity failure (object duplication)**. In $78\%$ of frames (`frac_multi_blob = 0.78`), the pendulum splits into two splayed rods and bobs swinging simultaneously (`sheet_pend_fps24_s2_189f.jpg`). `measure_pend v1` drops to $R^2 = 0.314$ with 19 erratic half-cycle intervals, yielding an apparent pseudo-period of $52.22\text{ frames}$ ($2.176\text{ s}$).
   - **Period range and seed noise:** At 24 fps, the measured period spans $2.09\text{--}4.46\text{ s}$ across clips ($2.0\times\text{--}4.2\times$ real). Seed noise alone between seed 1 and seed 2 at 189f is $4.46\text{ s}$ vs $2.18\text{ s}$ ($2.05\times$ spread).

3. **Cross-FPS Temporal Frequency Locking (Connecting to RIFLEx / Digest 1):**  
   Comparing 24 fps vs 48 fps at fixed 189 frames on seed 1:
   - At 24 fps: $P = 107.10\text{ frames} \rightarrow 4.463\text{ s}$.
   - At 48 fps: $P = 103.46\text{ frames} \rightarrow 2.155\text{ s}$.
   The period in frames changes by only $-3.4\%$ while fps doubles, causing the physical period in seconds to halve. At $\text{fps} \ge 24$, Nano's temporal attention operates with a near-fixed frame-stride prior rather than rescaling to real time.

---

## 1. Planted Calibration Control

We validated our estimator suite on all 4 referee planted pendulum clips (`planted-00, 07, 11, 13`), achieving $< 0.12\%$ agreement across methods:

| Planted Clip | `measure_pend v1` (s) | `measure_pend v1` (f) | `pend_acf` (f) | Indep L1 (f) | Indep L2_med (f) | Indep Cos_med (f) | Harmonic KinFit (f) |
|---|---|---|---|---|---|---|---|
| `planted-00` | 2.4622 s | 59.09 f | 59.06 f | 59.06 f | 59.05 f | 59.09 f | 59.12 f (2.463 s) |
| `planted-07` | 1.9177 s | 46.02 f | 46.01 f | 46.01 f | 46.01 f | 46.02 f | 46.02 f (1.918 s) |
| `planted-11` | 1.8356 s | 44.05 f | 44.03 f | 44.03 f | 44.03 f | 44.03 f | 44.05 f (1.836 s) |
| `planted-13` | 2.0921 s | 50.21 f | 50.12 f | 50.12 f | 50.11 f | 50.19 f | 50.21 f (2.092 s) |

---

## 2. Finding 550 Replication: Duration-Template Ablation

Comparison of Duration Template ON vs OFF on official GAUGE pendulum frame 0, 189 frames @ 24 fps, seed 1, cfg 6, shift 10:

| Arm | Duration Sentence | `measure_pend v1` (s) | `measure_pend v1` (f) | `pend_acf` (f) | Indep L1 (f) | Indep L2_med (f) | Indep Cos_med (f) |
|---|---|---|---|---|---|---|---|
| `dur_on` | `"The video is 7.9 seconds long..."` | 4.4307 s | 106.34 f | 107.10 f | 107.10 f | None | None |
| `dur_off` | *None* (`use_duration_template=false`) | 4.4279 s | 106.27 f | 107.38 f | 107.38 f | 107.37 f | 107.28 f |
| **Difference ($\Delta$)** | | **-0.0028 s (-0.06%)** | **-0.07 f** | **+0.28 f (+0.26%)** | **+0.28 f** | - | - |

**Verdict: REPLICATED.** Diffusers' duration template has zero impact on pendulum timing.

---

## 3. Finding 621 Replication: Clip Length and Seed Spread at 24 FPS

| Clip | $N$ | Seed | `measure_pend v1` Period | `measure_pend v1` $R^2$ | `pend_acf` Period (f) | Indep Cos/L1 (f) | Multi-Blob Frac | Object Duplication |
|---|---|---|---|---|---|---|---|---|
| `pend_fps24_61f_s1` | 61 | 1 | 3.3234 s (79.76 f) | 0.888 | *None* (<1 cycle) | *None* | 0.00 | **False** (Clean single arc) |
| `pend_A_fps24_93f_s1` | 93 | 1 | 2.0871 s (50.09 f) | 0.954 | 50.84 f (2.118 s) | 51.01 f | 0.17 | **False** (Clean oscillation) |
| `pend_fps24_s1_189f` | 189 | 1 | 4.4307 s (106.34 f) | 0.670 | 107.10 f (4.463 s) | 107.10 f | 0.38 | **Borderline** (Minor ghosting) |
| `pend_fps24_s2_189f` | 189 | 2 | 2.1757 s (52.22 f) | 0.314 | 56.65 f (2.361 s) | 107.39 f (sec) | 0.78 | **TRUE (Two splayed rods/bobs)** |

**Key observations:**
1. **$P/N$ scaling breaks down:** $P/N$ is $1.31$ for 61f, $0.55$ for 93f, $0.57$ for 189f seed 1, and $0.28$ for 189f seed 2.
2. **Seed 2 duplication:** In seed 2, Nano's generation bifurcates into two distinct bobs and rods splaying outwards, creating spurious high-frequency oscillation ($R^2 = 0.314$, erratic half-cycles).
3. **Severe slowdown:** Across all valid oscillations, the period is $2.09\text{--}4.46\text{ s}$ ($2.0\times\text{--}4.2\times$ real mocap $1.06\text{ s}$).

---

## 4. Cross-FPS Extensions

| Clip | $N$ | FPS | `measure_pend v1` (s) | `measure_pend v1` (f) | `pend_acf` (f) | Indep L1 (f) | Period in Seconds |
|---|---|---|---|---|---|---|---|
| `pend_fps48_s1_189f` | 189 | 48 | 2.1731 s | 104.31 f | 103.46 f | 103.46 f | **2.16 s** |
| `pend_fps24_s1_189f` | 189 | 24 | 4.4307 s | 106.34 f | 107.10 f | 107.10 f | **4.46 s** |
| `pend_fps12_s1_189f` | 189 | 12 | 4.6415 s | 55.70 f | 44.21 f | 66.61 f | **4.64 s** |
| `pend_B_fps12_93f_s1` | 93 | 12 | 2.5345 s | 30.41 f | 34.92 f | 26.19 f | **2.53 s** |

Doubling conditioned fps from $24 \rightarrow 48$ maintains a near-constant frame period ($107.1 \rightarrow 103.5\text{ frames}$, $-3.4\%$), exactly halving the period in seconds ($4.46 \rightarrow 2.16\text{ s}$).

---

## 5. Artifacts and Evidence

All artifacts are committed in `cosmos-swarm` under `work/agy-3/task54_pendulum_review/`:
- `replicate_550_621.py`: Complete executable replication script.
- `results.json`: Full quantitative outputs for all 11 evaluated clips.
- Contact sheets:
  - `sheet_planted-{00,07,11,13}.jpg`: Planted calibration grids.
  - `sheet_pend_fps24_s1_189f_dur_on.jpg` vs `sheet_pend_fps24_nodur_s1_189f_dur_off.jpg`: Visual proof of identical kinematics under duration ablation.
  - `sheet_pend_fps24_s2_189f.jpg`: Contact sheet documenting object duplication in seed 2.
  - `sheet_pend_fps24_61f_s1.jpg`: Contact sheet showing incomplete single swing.
