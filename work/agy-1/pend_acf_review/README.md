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
   - **Direct evaluation on the 189-frame and 61-frame Nano MP4s (`work/ro-3/task25_fps_pendulum/clips189/` and `clips_more/`):**
     - `pend_fps48_s1_189f_crf20.mp4` (`189 f @ 48 fps`): `pend_acf` `103.37 f` (`2.154 s`, `P / N = 0.547`); independent `l2_med_acf` `103.70 f` (`2.160 s`); independent `cos_med_acf` `103.70 f` (`2.160 s`); independent `dark_bob_tracker` zero-crossing period `104.82 f` (`2.184 s`), right turning points `f22 -> f130` (`108 f`), left turning points `f72 -> f174` (`102 f`).
     - `pend_fps24_s1_189f_crf20.mp4` (`189 f @ 24 fps`): `pend_acf` `107.10 f` (`4.463 s`, `P / N = 0.567`); independent `l2_med_acf` `107.18 f` (`4.466 s`).
     - `pend_fps24_nodur_s1_189f_crf20.mp4` (`189 f @ 24 fps`, duration template off, Finding 550): `pend_acf` `107.38 f` (`4.474 s`, `P / N = 0.568`); independent `l2_med_acf` `107.37 f` (`4.474 s`). Confirms `Δ = +0.28 f` (`+0.26%`, null effect) from removing diffusers' duration sentence on seed 1.
     - `pend_fps12_s1_189f_crf20.mp4` (`189 f @ 12 fps`): `pend_acf` picks the shallower local minimum at `66.55 f` (`5.546 s`, `flag = check`, window spread `0.151` jumping between `66.6 f` and `46.8 f`), whereas both `l2_med_acf` (`111.13 f`) and `cos_med_acf` (`110.91 f`) pick the deeper global minimum at `~111 f` (`P / N = 0.587`), confirming `ro-3`'s ambiguity note.
     - **Why "P_frames ≈ 0.55 × num_frames" does NOT generalize beyond the seed-1 93f/189f pair (challenged):**
       - On `pend_fps24_61f_s1.mp4` (`61 f @ 24 fps`, seed 1), if `P_frames ≈ 0.55 × N`, the period would be `~33.6 frames`. Instead, all three self-similarity tools (`pend_acf`, `l2_med_acf`, `cos_med_acf`) return `None` (`< 1 cycle`), because the pendulum executes less than a single cycle over the 61 frames (right extreme near `f30–34`, vertical crossing near `f52–53`, implied full period `~80–88 frames`, `P / N ≈ 1.3–1.4`).
       - On `pend_fps24_s2.mp4` (`189 f @ 24 fps`, seed 2), Nano duplicates the pendulum into two splayed rods swinging simultaneously (`pend_acf` returns a shallow `56.65 f` `flag = check`, `l2_med_acf` and `cos_med_acf` reject it as `None`).

## Files
- `replicate_525.py`: self-contained script running `pend_acf` and the 3 independent estimators on planted, 20 real GAUGE (full + short windows), and Nano clips.
- `results.json`: all quantitative outputs.
- `pend_A_fps24_93f_s1_sheet.jpg`, `pend_B_fps12_93f_s1_sheet.jpg`: 4-frame contact sheets of the 93-frame Nano clips.
