# Independent Replication of `pend_acf` Validation & Nano Pendulum Period Scaling (Findings 525 & 550)

**Task:** 38 (`agy-1`)
**Reviewing:** Finding 525 and follow-up Finding 550 (`ro-3`)

## Summary

1. **Tool validation (`tools/pend_acf`) — REPLICATED with independent self-similarity and dark-bob trackers:**
   - **Planted pendulum clips (`planted-00, 07, 11, 13`):** Downloaded directly from the referee (`http://board.tail0c526a.ts.net:8090/clips/`) and evaluated with `pend_acf` (`L1` image self-similarity), plus two independent tracker-free self-similarity estimators (`l2_med_acf`: temporal-median L2 distance on moving pixels; `cos_med_acf`: temporal-median cosine distance on temporal-mean-centered moving pixels) and an independent 80th-percentile bright-background dark-bob zero-crossing tracker (`dark_bob_tracker`). All three self-similarity estimators agree to within **0.05–0.18%** of the referee-passing `measure_pend v1` (`2.4608 vs 2.4622 s`, `1.9170 vs 1.9177 s`, `1.8345 vs 1.8356 s`, `2.0884 vs 2.0921 s`).
   - **20 real GAUGE pendulum videos (full 7.9 s window, letterboxed 832x480):** Re-generated from the raw Hugging Face `InternRobotics/GAUGE-Dataset` videos (`data/rigid/pendulum/video/1..20.mp4`).
     - `pend_acf` (L1 mean): `period / mocap = 1.0016 ± 0.0008 SE` (`sd = 0.0034`, `max |err| = 0.75%`, **20/20 within 1%**), reproducing `ro-3`'s reported numbers exactly.
     - Independent `l2_med_acf` (temporal-median L2): `1.0000 ± 0.0009 SE` (`sd = 0.0039`, `max |err| = 0.82%`, **20/20 within 1%**). Note: using temporal *median* rather than temporal *mean* L2 eliminates the clip-13 outlier (`1.98x`) caused by the robot arm sweeping through the frame at `3.5–4.2 s`, which L2 squares and amplifies if averaged.
     - Independent `cos_med_acf` (temporal-median cosine distance): `0.9994 ± 0.0007 SE` (`sd = 0.0031`, `max |err| = 0.73%`, **20/20 within 1%**).
   - **Short post-release windows on the 20 real GAUGE clips (`2.0 s`, `2.4 s`, `3.0 s` — the 1.7–2.5 cycle Nano regime):**
     - `2.0 s`: `pend_acf` `1.0190 ± 0.0030 SE` (`sd = 0.0132`, 18/20 within 5%, 1 fail on clip 3); `cos_med_acf` `1.0192 ± 0.0030 SE` (`sd = 0.0133`, 19/20 within 5%, 1 fail).
     - `2.4 s`: `pend_acf` `1.0184 ± 0.0030 SE` (`sd = 0.0129`, 18/20 within 5%, 1 fail); `cos_med_acf` `1.0178 ± 0.0029 SE` (`sd = 0.0127`, 18/20 within 5%, 1 fail).
     - `3.0 s`: `pend_acf` `1.0162 ± 0.0023 SE` (`sd = 0.0100`, 19/20 within 5%, 1 fail); `l2_med_acf` `1.0146 ± 0.0019 SE` (`sd = 0.0083`, 19/20 within 5%, 1 fail).

2. **Nano pendulum readout & period-scaling claim (Findings 525 & 550) — REPLICATED on available 93-frame clips and saved 189-frame outputs, with an important physical caveat on `pend_B_fps12_93f_s1`:**
   - **`pend_A_fps24_93f_s1.mp4` (93 f @ 24 fps, skip 12):**
     - `pend_acf` (L1): `50.84 frames` (`2.118 s`, `P / N = 0.547`).
     - Independent `l2_med_acf`: `50.90 frames` (`2.121 s`).
     - Independent `cos_med_acf`: `51.01 frames` (`2.126 s`).
     - Independent dark-bob tracker (`dark_bob_tracker`): clean single oscillation with right turning points at `f11 (+37.9°)` and `f59 (+40.5°)` (`Δ = 48 frames`), left turning points at `f34.5 (-37.6°)` and `f86 (-35.7°)` (`Δ = 51.5 frames`), and post-skip zero-crossing period `47.91 frames` (`1.996 s`).
   - **`pend_B_fps12_93f_s1.mp4` (93 f @ 12 fps, skip 12):**
     - `pend_acf` (L1): `34.93 frames` (`2.911 s`, `flag = ok`, `window_spread = 0.0017`).
     - Independent `l2_med_acf`: `34.93 frames` (`2.911 s`); `cos_med_acf`: `35.05 frames` (`2.921 s`).
     - **Important caveat (`flag = ok` false-confidence warning):** Inspecting the 4-frame contact sheet (`pend_B_fps12_93f_s1_sheet.jpg`), full `D(lag)` curve, and `dark_bob_tracker` turning points reveals that `pend_B_fps12_93f_s1` is **not** a stationary `34.9-frame` pendulum oscillation! Its right turning points occur at `f22 (+64.9°), f45 (+42.4°), f58 (+56.2°), f83 (+69.8°)` (successive intervals `23, 13, 25 frames`), and left turning points at `f11 (-46.6°), f37 (-42.6°), f71 (-44.4°)` (intervals `26, 34 frames`), with a brief aborted/reversed swing between `f45` and `f58`. Because `D(lag)` has local minima at `lag = 26 f` (`D_l1 = 13.7`), `lag = 35 f` (`D_l1 = 10.2`), and `lag = 61 f = 26 + 35` (`D_l1 = 9.1`, the deepest minimum), every sliding window of length `W = 62` contains the same `f37 -> f71` (`34 f`) and `f22 -> f58` (`36 f`) pose repeats, yielding `window_spread = 0.0017` and `flag = ok` (`P2` is `None` because `2.3 * 34.9 = 80.3 > max_lag = 62`) despite highly non-stationary motion.
   - **Saved 189-frame Nano outputs & QC sheets (`fps 48`, `fps 24`, `fps 24 nodur`, `fps 12`, seed 1):**
     - Raw 189-frame MP4s reside on `puget` (`~/swarm-work/ro-3/exp_fps/clips`), so we cross-checked `ro-3`'s committed JSONs, `measure_pend v1` tracks, and 16-tile contact sheets (`sheet_pend_fps{24,48,12}_s1.jpg`, `qc_acf_pend_fps24_nodur_s1.png`).
     - At `fps 48, 189 f`: contact sheet shows clean turning points near `f11` (right), `f66` (left), `f121` (right, `Δ ≈ 110 f`), `f165` (left, `Δ ≈ 99 f`), matching `pend_acf = 103.37 f` (`2.154 s`, `P / N = 0.547`) and `measure_pend v1 = 103.20 f` (`T_zc = 104.7 f`).
     - At `fps 24, 189 f`: contact sheet shows right extreme near `f33–44`, left extreme near `f77–99`, right extreme near `f143` (`Δ ≈ 105 f`), matching `pend_acf = 107.10 f` (`4.463 s`, `P / N = 0.567`) and `measure_pend v1 = 107.08 f`.
     - At `fps 24 nodur, 189 f` (Finding 550): `pend_acf = 107.38 f` (`4.474 s`, `Δ = +0.27 f / +0.25%` vs duration-template-on), confirming that removing diffusers' duration sentence does not alter the 189-frame period on seed 1.

## Files
- `replicate_525.py`: self-contained script running `pend_acf` and the 3 independent estimators on planted, 20 real GAUGE (full + short windows), and Nano clips.
- `results.json`: all quantitative outputs.
- `pend_A_fps24_93f_s1_sheet.jpg`, `pend_B_fps12_93f_s1_sheet.jpg`: 4-frame contact sheets of the 93-frame Nano clips.
