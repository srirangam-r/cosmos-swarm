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

## Interim 2 (14:05 UTC): 5 of 6 pairs + both CUDA controls (e0pend_interim2.json)
| seed | ref | l40s | MAE | r_me | T ref / l40s (flags) |
|---|---|---|---|---|---|
| 101 | a6k-3 | l40s-3 | 2.32 | 0.92 | 1.206 / 1.209 (ok/ok) |
| 102 | a6k-2 | l40s-2 | 2.22 | 0.94 | 0.925 / 0.928 (ok/check) |
| 103 | a6k-3 | l40s-0 | 2.35 | 0.58 | 0.843 / 0.527 (check/check; small swing in front of the robot, same swing by eye) |
| 105 | a100 | l40s-2 | 6.19 | 0.25 | 1.044 / 2.343 |
| 106 | a100 | l40s-0 | 4.61 | 0.12 | 1.691 / 0.816 |
| CUDA 101 | a6k-3 | l40s-2 cuda | 5.53 | 0.01 | 1.206 / 2.449 |
| CUDA 102 | a6k-2 | l40s-3 cuda | 4.35 | 0.05 | 0.925 / 2.478 |
DIFF (50 cpu pairs): MAE median 4.87, min 4.27. Frozen decision on all available pairs: identity_replicates False (a100 pairs),
period_carries False, cuda_switch_matters True. a6k<->l40s pairs only (post hoc split, motivated by endpoint_health_1400.txt):
3/3 below min DIFF, median 2.32 < 0.5 x 4.87. s104 (a6k) still pending.
