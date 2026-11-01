# Task 175: fresh-seed replication of #3810 (Rule R on GAUGE slope and pendulum), kiro-1

36 clips: slope_wood, slope_plastic, pend_mid (ro-agy1's task-140 inputs and prompts, unchanged) × base / R (Rule R suffix) / N (neutral suffix) × seeds 4-7.
All on q8 endpoints (q8 outputs are pixel-identical across endpoints, #3815), so every seed-paired comparison shares one stack.
Nano3 I2V, 832x480, 93 f @ 24 fps, 35 steps, CFG 6, Karras sigmas (requested flow_shift 10 ignored, #2870), empty negative prompt.
Queue owner kiro-1; clips stay on the queue / kiro-1's laptop (249 MB, too big for the repo; hashes in clips_SHA256SUMS). Sidecars in sidecars/.

Code (independent of task-140 code):
- analyze.py: moving-pixel fraction (|Δgray|>12 after 3x3 blur) in a scene ROI; late_tail = mean over f80-92; contact sheets.
- pend_angle.py: rod angle about the axle pivot (318,120) from wood-coloured pixels in an annulus r 35-95 px; axle band excluded so angles past ~80° read as missing.
- stats.py: seed-paired R−base and R−N contrasts (mean ± SE over 4 seeds).
- eye_codes_slope.json: final-position codes at f92 from montage_slope_*.jpg (coder not blind to arm).
None of these measures is planted-validated.

## Follow-up (shift 2): correction of the "over-swing" claim in #3918
`pend_real_check.py` runs the same rod-angle measure (`pend_angle_lib.py`, constants unchanged) on the REAL GAUGE pendulum 10 continuation
(HF InternRobotics/GAUGE-Dataset data/rigid/pendulum/video/10.mp4, dedup + letterbox 832x480 as in raj-3 task 8; frame 93 matches the
pend10_mid_f93.png input, MAD 2.87/255), frames 93-185, and against mocap angle (json/10.json, swing-plane PCA + circle fit, L=0.273 m).
Results in `pend_real_check.json`:
- Tool on real video vs mocap, same window: half-range (p95-p5)/2 early 72.4 vs 78.4 deg, late 69.7 vs 73.7, peak |angle| 81.5 vs 82.2. The tool reads 4-6 deg low on half-range and within 1 deg on the peak (n=1 real clip; not a referee planted case).
- The real release is ~84 deg from vertical (raj-3 mocap, all 20 clips). The prompt's "10 degree" is not measured from vertical. #3918 was wrong to call 73-83 deg an over-swing.
- Nano (12 clips, all arms): peak 79.9 +- 0.8 deg (matches real), half-range early 55.6 +- 3.4, late 49.4 +- 2.7 (real 72.4 / 69.7 with the same tool).
