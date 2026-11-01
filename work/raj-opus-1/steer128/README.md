# Task 128: is there an activation direction for "settle"? (raj-opus-1)

Contrast: ro-1's v5 prompts F (base GAUGE ball) vs QT (timed-settle clause), exact text in prompts.json.
Inputs gauge_ball1_dd33 / gauge_ball2_dd35 (raj-3 mid-fall real GAUGE frames). 832x480, 93 f @ 24 fps, 35 steps, cfg 6, shift 10, no negative. Endpoints q8-*/int-a100 (tools/cosmos_local internals hooks), via the shared queue.

## Step 1: capture (jobs_capture.jsonl, seeds 1-3)
Cond-pass per-frame spatial means at layers 0,3,...,33,35 and steps 0,5,...,30. analyze_capture.py -> capture_sep.json.
- paired = mean per-frame ||QT-F|| (same seed+input); seednoise = per-frame ||F_si - F_sj||/sqrt2; cos_pairs = mean cosine between the 6 pairs' frame-averaged diffs; loo_cos = cosine of each pair vs the mean of the other 5.
- Note: the CFG uncond pass is identical for F and QT (same empty negative + metadata), so the prompt's effect enters only through the cond pass. Steering therefore uses passes=cond (it gets amplified by cfg 6, as the prompt is).
lm_capture.json / lm_capture_strips.jpg: ro-1's late-motion corridor metric on the capture clips (also a q8-stack check of #2460).

## Step 2: steer (jobs_steer.jsonl not committed: 55 MB of inline vectors; vectors are v_L12_s0s5.npy, v_L24_s0s5.npy, rand_L12.npy)
v = mean over 6 pairs and steps {0,5} of (QT - F), per latent frame [24,4096]. Applied to F (prompt unchanged), seeds 4-6, both inputs. Arms in steer_arms.json.
