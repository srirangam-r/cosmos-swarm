# Task 239 interim (13:50 UTC): 3 of 6 same-seed pairs available

The frozen e0pend.py (e4d65e9) was run unchanged on the clips available at 13:47 UTC: refs t226_P_base s101 (a6k-3), s105 and s106 (a100);
l40s cpu s101-106. Refs s102-104 (a6k) and the 2 CUDA controls are still pending, so the frozen decision (which needs all pairs) is not yet final.

| seed | ref endpoint | l40s endpoint | MAE (gray levels) | r(ROI motion curves) | measure_pend T ref / l40s (flag) |
|---|---|---|---|---|---|
| 101 | a6k-3 | l40s-3 | **2.32** | **0.916** | 1.206 / 1.209 (ok/ok) |
| 105 | a100 | l40s-2 | 6.19 | 0.248 | 1.044 / 2.343 (check/check) |
| 106 | a100 | l40s-0 | 4.61 | 0.116 | 1.691 / 0.816 (check/ok) |
| different seeds (33 pairs) | | | median 4.85, min 4.38 | median -0.04 | |

Request params are byte-identical (sidecar check: size, frames, fps, steps, guidance, seed, prompt, image, extra_params incl. noise cpu).
sheet_s101_s105_s106.jpg: rows = ref/l40s for s101, s105, s106; columns = frames 0, 20, 45, 70, 92.
s101 is visibly the same swing; s105 and s106 are different swings.
Descriptive: MAE of a100 clips to other-seed clips is higher (median 5.36 vs l40s, n=10) than l40s-l40s (4.79, n=15) or a6k-l40s (4.80, n=5).
