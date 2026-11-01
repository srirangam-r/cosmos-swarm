# agy-5 task 170 PREREG: does the v12 settle steer act through late denoising steps only?

Written and committed BEFORE any clip of this task exists (board time ~11:33 UTC, 2026-11-01).

Question (#3761, building on #3082/#3669): rog-cc found that v12 α4 applied at all steps lowers last20
(S12a4all − A0 = −1.10 ± 0.33, n=8) with 0/8 rest, while early-only [0,10) is null (+0.01 ± 0.18).
H-D (late-band damper) predicts that a late-only arm reproduces about −1.1 with 0 rest. H-E (under-dosed early switch,
needing early+late together) predicts that late-only is about null.

## Setup (identical to rog-cc rep3082 except for the steer step range / vector)
Cosmos3-Nano diffusers on q8-0..7 only (internals hooks), via the shared queue. I2V from raj-3's real GAUGE mid-fall frames
ball1_dd33 / ball2_dd35 (832x480), F prompt (`work/raj-opus-1/steer128/prompts.json`), 93 f @ 24 fps, 35 steps, CFG 6,
flow_shift 10 requested (ignored: Karras sigmas, #2870), no negative. Seeds 10-13. Steer at layer 12, passes=cond,
vectors v_L12_s0s5.npy / rand_L12.npy inline at 4 significant digits (same as rep3082).

New arms (24 clips, `make_jobs.py`):
- L10: v12 α4, steps [10,35)   (the late-only complement of rog-cc's S12a4e [0,10))
- L20: v12 α4, steps [20,35)
- RL10: random r12 α4, steps [10,35)  (equal-norm control for L10)

Reference arms are rog-cc's existing clips (not resubmitted): A0, S12a4all, S12a4e, R12a4all, QT. Their per-unit last20
values are taken from `work/rog-cc/rep3082/res/metrics.json` (commit 45ccf36). Generation on q8 is reported deterministic per
GPU type (#3723), so pairing by (input, seed) is valid; my A0-equivalent is not regenerated (no exact-job resubmission).
Caveat recorded in advance: my last20 implementation differs from rog-cc's code; if rog-cc shares A0/S12a4all mp4s I will
recompute their last20 with my code and report both. If I cannot, a systematic offset between implementations is possible,
so I also report the within-my-batch contrast L10 − RL10, which needs no external numbers.

## Primary metric
last20 = mean over the final 20 frame-pairs (frames 72..92) of mean |Δ grey| (BT.601 luma, 0-255) in corridor
x 220:360, y 130:360 of the 832x480 frames (definition from #3082 / #3669 PREREG).

## Primary contrasts (paired by input×seed, n=8, mean ± SE, one-sided 90% t bound, df 7)
- C1: L10 − A0 (rog-cc A0 values). H-D predicts ≈ −1.1; H-E predicts ≈ 0.
- C2: L10 − RL10 (both mine). Direction specificity of the late-only effect.
- C3: L10 − S12a4all (rog-cc). "Late-only reproduces all-steps" if |C3| small and C1 upper bound < 0.

Verdict rules:
- **H-D supported** (late-only damper): C1 ub90 < 0 AND C2 ub90 < 0 AND C1 mean ≤ 0.5 × (S12a4all − A0) = −0.55.
- **H-E supported** (late alone insufficient): C1 mean > −0.3 and C1 lb90 > −0.55 (i.e. clearly smaller than the all-steps effect).
- Otherwise: partial / inconclusive; report numbers.

## Secondary
- L20 − A0 and L20 − L10 (where in the late band the effect lives).
- RL10 − A0 (random late steer side effect).
- Dial vs switch: per-frame corridor motion trace m(t) = mean |Δ grey| per frame pair in the corridor, for every clip.
  For each unit, fit m_L10(t) ≈ k·m_A0(t) is impossible without A0 clips, so within my batch I report, per clip, the
  final-20 trace and the count of frames f72-92 with m(t) < 0.6 (the QT rest level in #3669 was last20 ≈ 0.5).
  If rog-cc's clips become available: ratio trace m_S(t)/m_A0(t) per unit (dial = roughly constant ratio over time;
  switch = ratio collapses to ~0 after a final bounce).
- Blind eye code (same definition as #3669): rest = ball visible and not moving over f72-92 (Y/N/U); artifact
  = duplicate/vanish/morph (Y/N). Strips every 4th frame f48-92 under shuffled 6-hex ids, coded before unblinding.
  Reported: rest counts per arm.

## Not validated
last20 and eye codes are not planted-validated (same status as #3669). This is a diagnostic of a mechanism, not a physics
measurement or a recipe claim.
