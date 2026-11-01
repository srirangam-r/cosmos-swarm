# Task 336 (dk1): ProxyUp region-wise noising (+SFR) vs Nano-Phys's DOVER cost

PREREG, frozen before any clip (this commit). Builder: `build_jobs.py` → `jobs.jsonl` (32 jobs), `boxes.json`, `boxes_check.jpg`.

## Question
#6690: Nano-Phys (whole-frame SDEdit of the proxy at σ 0.89844) costs −0.057 DOVER fused vs plain (18/18 pairs).
Does ProxyUp's region-wise latent noising (proxy latent only inside the pendulum box; variance-matched fresh noise outside),
with or without SFR (K=15, CFG 3), remove that cost while the output still copies the supplied period?

## Design
- t276 contract: prompt, proxy.py defaults, k19, 93 f @ 24 fps, 832x480, 35 steps, CFG 6, CPU noise, q8 (server 04e8e0de81).
- Scenes: real_12, 17, 18, 19 (t276 nphys 12/12 clean). Seeds 1-3, paired with t276 plain/nphys (same seed noise; inside
  the box the start latent is identical to t276 nphys).
- Arms: `reg` (latent.band region box), `regsfr` (reg + sfr 15, sfr_guidance 3), and the wrong-period controls `reg_x17`
  and `regsfr_x17` (1.7 × P_real proxy, seed 1).
- Box: moving proxy pixels (>30 grey) ∪ pivot/bob, dilated 32 px, bounding rectangle (7-9% of the frame). Rectangle, not
  a SAM mask (the server takes boxes only).

## Readouts (fixed now)
1. **Quality (primary):** DOVER fused via `tools/nv_scoreboard/score.py --dover_reps 3` on the same RTX 4060 laptop as
   t319. Baselines are t319 `scores_gen.json` @9e92945, plain and nphys, for these 4 scenes × seeds 1-3. If dk2's t276 mp4s
   are available locally, I also re-score 4 of them in the same run as a scorer drift check (report |Δ|).
   - Δ_A = mean over 4 scenes of the seed-mean (A − plain); 95% CI by exhaustive 4^4 scene bootstrap.
   - Recovery_A = (A − nphys) / (plain − nphys), pooled.
   - Also dover technical/aesthetic, and dd_norm vs real (1.94, t319).
2. **Period (primary):** the frozen 276 analyzer and gate (`work/dk1/t277_rep/analyze.py`, prefix changed only). Count
   clean and within 10% out of 12 per arm. x17 control: ungated ACF and MP ratio ≥ 1.5 on ≥ 3/4 scenes per arm.
3. **Fix candidate** (per arm): Δ_A ≥ −0.020 (inside the 0.026 seed noise of a 3-seed mean, #6690) AND period ≥ 10/12 clean
   within 10% AND the x17 control passes. Otherwise report which half failed.

## Not tested
Near-vertical scenes (need the supplied amplitude of #6747), ODE inversion inside the mask (ProxyUp's choice; SDEdit is kept
to stay matched to 276), plausibility judge, robot-clip prediction, and scenes outside the GAUGE rig.
