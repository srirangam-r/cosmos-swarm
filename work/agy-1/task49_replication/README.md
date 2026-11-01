# Task 49: Independent Replication & Review of Findings #600, #674, and #601

**Agent:** `agy-1` (Shift 5)  
**Task:** `#49` — Independent replication and review of `bounce_decay` (`#600`), seed-2 mid-fall ball cycle/tether (`#674`), and 8B/32f HUE judge temporal blindness (`#601`).

## Contents

- `replicate_600_674_601.py`: Independent evaluation, piecewise parabola fitter, lower-corridor ball tracker + strap detector, and paired HUE judge corruption analysis.
- `results.json`: Full numeric outputs across all three replications.
- `qc_ballF_fps24_s2_corridor.jpg`: Trajectory + strip visualization of `ball_F_ball1_fps24_93f_s2.mp4` (`e_T = 1.0049 ± 0.0099`, period `7.871 ± 0.201 f`, strap brightness excess `+36.56`).
- `qc_ballE_fps12_s2_corridor.jpg`: Trajectory + strip visualization of `ball_E_ball1_fps12_93f_s2.mp4` (`e_T = 0.9937 ± 0.0224` over `f0..34`, period `3.765 ± 0.183 f` over `f0..45`, followed by `f34..48` hover and `f49..87` second bounce train).

---

## 1. Replication of Finding #600 (`rahul`, `bounce_decay.py` tool validation + Nano cross-check)

- **Verdict:** **Replicated** on synthetic (`n=40`, seed 4242) and planted (`12/12`), with a critical caveat on real/Cosmos GAUGE clips answering the requested cross-check against `ro-1`'s `bclock` (`#612` / `#707`).
- **Synthetic held-out validation (`n=40`, Conditions A–E, seed 4242):**
  - On `rahul`'s saved `held/` JSONs (`n=40`):
    - `e_T_fit`: `n=30/40`, ratio `1.0006 ± 0.0017 SD` (`± 0.0003 SE`), max error `0.51%`, `100%` within 5%
    - `e_v1`: `n=33/40`, ratio `1.0002 ± 0.0081 SD` (`± 0.0014 SE`), max error `2.77%`, `100%` within 5%
    - `e_v_med`: `n=33/40`, ratio `0.9995 ± 0.0047 SD`, max error `2.45%`
    - `e_h_med`: `n=31/40`, ratio `1.0000 ± 0.0020 SD`, max error `0.95%`
    - `g_joint`: `n=33/40`, ratio `0.9715 ± 0.0147 SD`, max error `6.23%` (`90.9%` within 5%)
    - `g_fall`: `n=10/40`, ratio `0.9832 ± 0.0276 SD`, max error `6.46%`
    - `still_bouncing_at_end`: `37/40` (`92.5%` match)
  - On our locally re-rendered 40-clip synthetic set (`gen_bounce.py`, seed 4242, verified `truth.json` identical):
    - `e_T_fit`: `n=30/40`, `1.0007 ± 0.0015 SD`, max error `0.47%`
    - `e_v1`: `n=34/40`, `1.0006 ± 0.0085 SD`, max error `2.74%`
    - `e_h_med`: `n=31/40`, `1.0002 ± 0.0024 SD`, max error `0.85%`
    - `g_joint`: `n=34/40`, `0.9732 ± 0.0154 SD`, max error `6.14%`
  - **Independent unshared-curvature piecewise parabola fitter (`indep_piecewise_parabola_fit`):** Allows per-flight $a_k$ rather than enforcing a single shared $a$ across all flights. Recovers `e_T_fit` on `n=32/40` (`0.9939 ± 0.0122 SD`), including `4/8` in Condition D (perspective depth drift, `0.9946 ± 0.0090 SD`, max error `2.10%` vs `n=0/8` for `bounce_decay.py`), and `e_v1` on `n=33/40` (`1.0002 ± 0.0091 SD`, `100%` within 5%).
- **Cross-check on `ro-1`'s Nano mid-fall clip `ball_F_ball1_fps24_93f_s1.mp4` (`--seed 287,155 --mpp 0.0018525`):**
  - Default `bounce_decay.py` returns **`n_fitted: 0, n_impacts: 0, e_T_fit: null`** (just as on the 189f clips in `#870`), even though its raw `peaks` array detects all 11 real plank contacts (`[8, 17, 25, 34, 42, 48, 56, 64, 72, 78, 86]`, plus false peaks at `f2` and `f82`).
  - **Why `n_fitted=0`:** (1) `f2` has a false early peak (`y=180 -> f3 y=170 -> f4 NaN`), leaving segment 0 with only 2 points (`< min_pts=3`), which immediately triggers `if len(idx) < min_pts: break` at `k=0`; and (2) Nano's non-parabolic bounce shape + perspective drift exceeds `seg_tol = 1.5 px` in the shared-$a$ fitter.
  - Our independent unshared-$a$ parabola fitter on the exact same `bounce_decay` trajectory (`y` array) fits `8` flights (`impacts = [6.93, 17.64, 25.00, 34.47, 42.34, 48.36, 56.11]`), yielding `e_T_fit = 0.9038`, `e_v_med = 0.9182`, and `e_h_med = 0.9163`, while our lower-corridor contact timing tracker recovers all 11 contacts (`e_T = 0.9765 ± 0.0065`, matching `ro-1`'s `bclock` `0.975 ± 0.006`).

---

## 2. Replication of Finding #674 (`ro-1`, seed-2 mid-fall ball clips at fps 24 and fps 12)

- **Verdict:** **Replicated** — provides quantitative full-clip trajectories and strap-brightness metrics where `bclock v1` returned `flag="no_track"` (because `bclock` locked onto the stationary gripper/strap anchor `x=310..312, y=150.0..151.2 px` from `f2..92`).
- **Control (`ball_F_ball1_fps24_93f_s1.mp4`, seed 1, fps 24):**
  - `11` plank contacts (`[6.93, 16.68, 24.97, 32.97, 40.53, 48.25, 55.94, 63.68, 70.96, 77.86, 85.47]`), period `7.855 ± 0.242 f` (`0.327 ± 0.010 s`), `e_T = 0.9765 ± 0.0065` (log-linear) / `0.9751 ± 0.0231` (ratio mean), matching `ro-1`'s `bclock` (`7.84 ± 0.25 f`, `e_T = 0.975 ± 0.006`).
- **Seed 2 at fps 24 (`ball_F_ball1_fps24_93f_s2.mp4`):**
  - Lower-corridor tracker (`y in [165, 355] px`) tracks all `11` interior plank contacts (`[6.03, 13.98, 21.74, 28.07, 36.97, 45.10, 52.93, 60.98, 68.97, 77.07, 84.74]`, plus final contact at `f92`).
  - **Mean cycle period:** **`7.871 ± 0.201 frames` (`0.3280 ± 0.0084 s`)**, matching `ro-1`'s by-eye `7.8 f/cycle` (`0.33 s`) and nearly identical to seed 1's `7.855 ± 0.242 f`.
  - **Decay ratio:** **`e_T = 1.0049 ± 0.0099`** (log-linear) / `1.0063 ± 0.0542` (adjacent ratio mean), with non-decaying cycle amplitude (`first 3 cycles mean rise = 129.0 px`, `last 3 cycles = 139.3 px`, overall `138.1 px`).
  - **Tether/strap quantification:** Mean 90th-percentile grayscale excess in the vertical corridor between the gripper (`y=135`) and the ball top (`x in [278, 316]`) relative to `f0` is **`+36.56` gray levels** (`frac > +20 = 96.6%`) on `ball_F_fps24_s2`, vs **`+6.89`** (`0.0%`) on `ball_F_fps24_s1` and **`+1.67`** (`0.0%`) on `ball_E_fps12_s2`.
- **Seed 2 at fps 12 (`ball_E_ball1_fps12_93f_s2.mp4`):**
  - Over the first 46 frames (`ro-1`'s crop-sheet window), the corridor tracker finds `9` contacts (`[2.90, 6.84, 10.65, 13.96, 17.64, 21.86, 25.33, 29.99, 33.02]`, matching `ro-1`'s by-eye `7, 11, 14, 18, 22, 26, 30, 34` plus initial contact at `f3`).
  - **Mean cycle period (`f0..45`):** **`3.765 ± 0.183 frames` (`0.3138 ± 0.0152 s` at 12 fps)**, matching `ro-1`'s by-eye `3.8 f/bounce (0.32 s)` within `0.035 frames`, confirming that lowering `fps` from `24 -> 12` halves the frame period (`7.87 -> 3.77 f`) while keeping wall-clock period constant (`~0.32 s`).
  - **Decay ratio (`f0..34`):** **`e_T = 0.9937 ± 0.0224`** (`first 3 rise = 51.3 px`, `last 3 rise = 51.2 px`).
  - **Full 93-frame extension (`f34..92`):** After contact at `f33.0`, the ball hovers in mid-air (`y ≈ 281–297 px`) from `f34` to `f48`, then resumes a second train of `8` low bounces from `f49` to `f87` (`[48.91, 57.03, 61.00, 65.11, 70.05, 73.71, 78.02, 83.07, 87.10]`, period `4.27 ± 0.20 f` over `f57..87`).

---

## 3. Replication of Finding #601 (`rog1`, HUE judge 8B & 32-frame validation)

- **Verdict:** **Replicated** across all 4 validation sets (`2b_f16`, `2b_f32`, `8b_f16`, `8b_f32`, `n=12` clips × `6` variants = `72` records for `2b_f32` and `n=12` × `12` = `144` records for the others).
- **Summary of paired drops (`orig - corrupted`, `n=12` clips: 4 ball, 4 pend, 4 slope):**

| Variant | Offset noise SD (`overall / Phys`) | Freeze (`overall / Phys`) | Noise (`overall / Phys`) | Reverse (`overall / Phys`) | Shuffle (`overall / Phys`) | Splice (`overall / Phys / VI / GR`) |
|---|---|---|---|---|---|---|
| **2B @ 16f** | `0.0256 / 0.0309` | `+0.068±0.008 / +0.097±0.013` | `+0.214±0.012 / +0.165±0.014` | `-0.010±0.005 / -0.025±0.009` | `+0.002±0.005 / +0.007±0.007` | `+0.027±0.012 / +0.019±0.015 / +0.036 / +0.014` |
| **2B @ 32f** | `0.0257 / 0.0352` | `+0.055±0.007 / +0.065±0.012` | `+0.217±0.011 / +0.164±0.013` | `-0.010±0.007 / -0.020±0.009` | `+0.002±0.005 / +0.012±0.009` | `+0.027±0.013 / +0.028±0.014 / +0.031 / +0.011` |
| **8B @ 16f** | `0.0197 / 0.0187` | `+0.100±0.012 / +0.117±0.033` | `+0.151±0.011 / +0.017±0.006` | `-0.002±0.008 / -0.026±0.010` | `+0.007±0.004 / +0.003±0.007` | `+0.075±0.023 / -0.069±0.020 / +0.151 / +0.300` |
| **8B @ 32f** | `0.0136 / 0.0140` | `+0.100±0.012 / +0.113±0.035` | `+0.156±0.011 / +0.025±0.005` | `-0.009±0.005 / -0.055±0.020` | `+0.014±0.005 / -0.005±0.007` | `+0.105±0.012 / -0.070±0.020 / +0.176 / +0.396` |

- **Per-question diagnosis on `ball` time-reversal (`orig - reverse`, `n=4` clips):**
  - Static start-state check **`q1`** (*"At the start of the video, does a robot arm hold a black ball above a wooden plank?"*): **penalizes reversal** at 8B (`+0.2718` at 16f, `+0.5269` at 32f vs `+0.0398` at 2B@16f, `+0.0584` at 2B@32f) because reversed clips start on the plank instead of in the gripper.
  - Temporal direction check **`q2`** (*"In the middle of the video, after the ball is released, does it fall downward?"*): **strongly prefers the time-reversed video (`0/4` orig higher across all 4 judge configs)**: `-0.1453` (2B@16f), `-0.1533` (2B@32f), **`-0.2241`** (`0.0252 -> 0.2494`, 8B@16f), and **`-0.4776`** (`0.0069 -> 0.4844`, 8B@32f).
  - Similarly, **`q4`** (*bounces up instead of passing through*) drops `-0.2093` (`0/4` orig higher) on 8B@32f under reversal, and **`q6`** (*bounces get lower each time until it comes to rest*) is saturated at `~0.989` on both forward and reversed clips on 8B (`diff = -0.0017` at 16f, `+0.0015` at 32f).
