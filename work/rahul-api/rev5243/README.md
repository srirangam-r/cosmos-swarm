# rev5243: replication of rog1 #5243 (task 255) on independent Bridge FD clips

Uses my existing t210 grid (no new generation): 24 tools/robot_pred/devset_bridge clips, chunk 1, arms base/R/N x seeds 0-3,
all on q8-0..7 with default CUDA noise (rog1 used noise.device=cpu, seeds 1-3), 30 steps, CFG 1, 256x256, 17 f @ 5 fps.
Script and planned quantities (rev5243.py docstring) committed before running it.
Replicates: correct-action LPIPS to real vs static floor, seed-to-seed spread D_seed (and its per-frame growth).
Cannot replicate: the action effect (no SWAP arm in t210).
New: D_prompt (base vs N / R suffix at the same seed = same noise) vs D_seed.
Run: `python rev5243.py ../../../tools/robot_pred/devset_bridge ../t210/clips ../t210/scores.json results.json`
(clips: GB10 ~/jobs/rahul-api/t210/clips/).

## Result (results.json, run 14:48-14:56 UTC)
| quantity | this (t210, seeds 0-3, CUDA noise) | rog1 #5243 (seeds 1-3, CPU noise) |
|---|---|---|
| L_real (base, correct actions) | 0.1106 ± 0.0085 | 0.115 |
| L_static (repeat frame 0) | 0.1300 | 0.130 |
| margin static − real | 0.0194 ± 0.0084, boot CI [0.003, 0.036], 19/24 | 0.015 ± 0.009, 17/24 |
| D_seed (base) | 0.0953 ± 0.0086 [0.080, 0.113] (R 0.0957, N 0.0932) | 0.107 |
| D_seed f1/f4/f8/f16 | 0.018 / 0.066 / 0.103 / 0.138 | 0.021 / 0.076 / 0.117 / 0.149 |
| L_real / D_seed per clip | median 1.14 [1.07, 1.34], mean 1.20 | (0.115/0.107 ≈ 1.07) |
| D_prompt base↔N (same seed) | 0.0108 ± 0.0017; /D_seed median 0.092 [0.068, 0.119]; < D_seed 24/24 | — |
| D_prompt base↔R (same seed) | 0.0163 ± 0.0034; /D_seed median 0.114 [0.088, 0.160]; < D_seed 24/24 | — |
Per-frame: static beats the prediction at f1 (0.015 vs 0.028); prediction wins from f4 on. Seed means of L_real: 0.105/0.106/0.112/0.119.
