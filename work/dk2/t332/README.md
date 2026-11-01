# t332: does region-wise latent noising remove Nano-Phys' DOVER cost while keeping the period transfer? (dk2, FROZEN before any clip)

Why: t331 (e36f89c, #6767) puts ~70% of the −0.064 fused-DOVER cost in the static background. Nano-Phys noises the WHOLE proxy latent (no mask).
Fix (ProxyUp https://arxiv.org/abs/2607.03732 RLN; Time-to-Move https://arxiv.org/abs/2511.08633): keep the proxy x_k only inside the corridor box,
fresh noise at the same σ elsewhere. Server option `extra_params.latent.band = {"band":"region","box":[x0,y0,x1,y1]}` (tools/cosmos_local/latent.py). No SFR.
Jobs: jobs.jsonl from build_jobs.py. These are the t276 nphys jobs unchanged (prompt, proxy, start_step 19 σ 0.898, CPU noise, 832x480, 93 f, 24 fps, 35 steps, CFG 6) plus the band.
The box is the bbox of the proxy motion mask (>30 grey), dilated 32 px. 5 scenes (09, 12, 17, 18, 19; real_16 skipped because its proxy is static) × seeds 1–3 = 15 rln, plus 5 x17_rln (seed 1) wrong-period controls. Endpoints q8-0..7 only (same stack as t276).

## Pre-registered readout
1. Quality: tools/nv_scoreboard score.py DOVER ×3 (RTX 4060, same weights as t319) on the ORIGINAL queue mp4s (no re-encode). Paired by scene×seed: rln − plain and rln − nphys, using the t319 scores of the same seeds; CIs from an exact 5-scene bootstrap. PASS-quality = rln − plain lower CI > −0.030 (the proposed 0.030 margin of #6690).
2. Period: work/dk2/t276/analyze_t276.py (pend_acf + measure_pend v1, Raj v2 gate) with the prefix changed to t332. PASS-period = clean rln clips with median P/P_real within 10%, a clean count not lower than nphys on the same scenes by more than 2, and x17_rln median ratio ≥ 1.4 (copy-through still active).
3. Fix = PASS-quality AND PASS-period. Anything else is reported as is, including a partial recovery (the fraction of the −0.057 recovered).
Not tested here: plausibility judge, robot prediction, other rigs.

## Arm B (added 20:23 UTC after arm A failed, before any arm-B clip): rln + SFR
Arm A (band only) failed: DOVER fused 0.11–0.31 on 8/8 interim clips, with the background regenerated as a flat wall (#6811). The server fills outside the box with pure noise (latent.py: fill = randn·sqrt((1−s)²+s²)), so no background signal is left.
Arm B = arm A + `latent.sfr = 15` (ProxyUp's K=15 stochastic flow relaxation at s_k, default guidance), same 5 scenes × seeds 1–3 (15 clips, jobs_sfr.jsonl, names t332_<scene>_rlnsfr_s<seed>).
The readout and PASS rules are the same as above. If it passes quality, the x17 control at seed 1 is added before any period claim.
