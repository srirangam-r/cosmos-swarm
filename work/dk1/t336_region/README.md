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

## Amendment 1 (20:33 UTC, after 5 clips): region-band arm fails qualitatively; t336b dual-clock, FROZEN before any t336b clip
- Observation (`peek_real12_reg_regsfr_s1.jpg`, real_12 reg s1-3 and regsfr s1-2; sidecars confirm band box, σ_start 0.89844,
  sfr 0/15): outside the box the scene is not rebuilt from frame 0. From the first generated frame on, the background is a flat
  brown/grey textured wall, and only the boxed rod/bob remains. Variance-matched fresh noise at σ 0.898 with 16 steps left gives
  Nano nothing to rebuild the background from; SFR15 does not help. 25 pending t336 jobs cancelled; real_17 reg_s1 and regsfr_s1
  kept as a second-scene check. The 7 clips are still scored as preregistered (descriptive, n is small).
- t336b (`build_jobs_b.py` → `jobs_b.jsonl`, 32 jobs): Time-to-Move-style dual clock via the server's `latent.x0_inject`
  (PhyRPR latent fusion). start_step 0, so the background runs plain Nano's full schedule. Inside the same boxes, the predicted
  clean video is replaced by the proxy latent for steps [0, K), K = 19 (release at σ 0.898) or 27 (σ 0.573). Arms inj19,
  inj27 (seeds 1-3), inj19_x17, inj27_x17 (seed 1).
- Readouts and decision rules unchanged: `analyze_b.py` (276 analyzer, prefix t336b_) and `quality_b.py` (same as quality.py,
  t336b names). Fix candidate per arm: ΔDOVER vs plain ≥ −0.020 AND ≥ 10/12 clean within 10% AND the x17 control ≥ 1.5 on ≥ 3/4.
  Extra QC (eye check, contact strips): a seam or a duplicate pendulum at the box edge is reported as a failure mode
  (TTM reports duplicates when the background is unconstrained).
