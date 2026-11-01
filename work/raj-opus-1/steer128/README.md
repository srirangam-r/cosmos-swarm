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

## Results (steer_summary_all.txt, lm_steer.json, lm_steer_strips.jpg)
Δlast20 vs the α0 control (same input+seed), mean ± se:
- seeds 4-6 (n=6): S12α2 all-steps −0.87 ± 0.35 (5/6 lower); QT −1.43 ± 0.39; random α2 all-steps +0.92 ± 0.63.
- seeds 7-9 replication (n=6): the α0 control already mostly settles (floor), so QT −0.19 ± 0.27, S12α2 +0.22 ± 0.41, S12α4 −0.11 ± 0.36. Not informative.
- pooled seeds 4-9 (n=12): QT −0.81 ± 0.29 (proxy-settled 12/12 vs α0 7/12); S12α2 all −0.33 ± 0.30 (8/12); S12α4 all −0.51 ± 0.26 (7/12, proxy-settled 10/12); S12α2 − random α2 −1.03 ± 0.42 (8/12); random α2 vs α0 +0.70 ± 0.33.
Reading: the direction is clearly distinct from an equal-norm random direction (random raises late motion), but its effect versus no steering is at most ~40-60% of the prompt's and is only ~2 se at α4. Metric unvalidated (no planted case for settling); eye check unblinded, thumbnail size only.
