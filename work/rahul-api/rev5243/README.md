# rev5243: replication of rog1 #5243 (task 255) on independent Bridge FD clips

Uses my existing t210 grid (no new generation): 24 tools/robot_pred/devset_bridge clips, chunk 1, arms base/R/N x seeds 0-3,
all on q8-0..7 with default CUDA noise (rog1 used noise.device=cpu, seeds 1-3), 30 steps, CFG 1, 256x256, 17 f @ 5 fps.
Script and planned quantities (rev5243.py docstring) committed before running it.
Replicates: correct-action LPIPS to real vs static floor, seed-to-seed spread D_seed (and its per-frame growth).
Cannot replicate: the action effect (no SWAP arm in t210).
New: D_prompt (base vs N / R suffix at the same seed = same noise) vs D_seed.
Run: `python rev5243.py ../../../tools/robot_pred/devset_bridge ../t210/clips ../t210/scores.json results.json`
(clips: GB10 ~/jobs/rahul-api/t210/clips/).
