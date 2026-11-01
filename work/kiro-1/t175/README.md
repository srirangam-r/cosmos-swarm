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
