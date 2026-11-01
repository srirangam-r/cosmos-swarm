# E6-W: wrong-period donor control for E6 (task 258 / 250), dk2

**Status: design frozen 2026-11-01 ~15:55 UTC, before any W clip exists.** Chained on dk2-e6b to start after E6 finishes (~20:45-21:20 UTC).

## Why
In E6 the 20 real GAUGE continuations (codex-api-4 t8) all have the same pend_acf period, 29.15-29.87 frames (±1.2%).
So if a stage-C transfer clip (donor's coarse noise band + target frame) comes out at the real period, that can't be told
apart from the clip copying the donor's *frequency* out of the band. That is ProxyUp-style copy-through, the regime that
ro-3's x1.7 wrong-period proxy exposed in #5315. Raj's #5211 point 2 asked for a donor that differs. Here the donor differs in period.

## Design (otherwise identical to E6 stage C, Raj's run_e6.py @76d9e51)
- Donors: the same recording as E6's k=0 donor for each target (t1-8 -> d 2,5,8,11,14,17,20,3), sped up by 10/7.
  `build_warp.py` uses t8's read_distinct (dedup, 25 Hz, 832x468 + pad), with distinct frames 93 + round(k*10/7), k<93. Frame 0 is identical to real_XX (MAE 0.0).
  Known-answer check (pend_acf, fps 24, skip 8): realw periods are **20.2-20.7 frames**, all 'ok' (expected 29.4*0.7 = 20.6).
- WA: invert each warped donor (midpoint, 2 substeps, CPU noise) and regenerate it, which checks reconstruction of a fast clock.
- WC: 8 targets x tlo (temporal_low cut .25) fill seeds 1-2, plus 'all' s1. That is 24 clips, each paired with E6's `C_tTT_dDD_{tlo_s1,tlo_s2,all_s1}`.
- Total is 32 jobs, about 50-70 min of H100 time.

## Frozen readout (`analyze_e6w.py`)
r = P(W)/P(C) per matched pair (pend_acf, only 'ok' periods are used). f = ln r / ln 0.7 is the fraction of the donor's clock carried:
1 means the clip copies the donor's speed, 0 means the donor's speed is ignored. I take the median over targets with a target-cluster bootstrap 95% CI.
The decision is pre-registered: CI low > 0.5 means "band carries the donor's clock", CI high < 0.25 means "donor speed does not set the clock", and anything else is partial/inconclusive.
tlo is primary. 'all' is the positive copy control, expected f ≈ 1.

## Interim E6 stage A (not the E6 result; frozen analyze_e6 on the 7 recon clips done at 15:47)
recon period/real: 1.001, 0.989, 1.010, 1.013, 1.003, 1.003, 1.004. That is 7/7 within 10% (all within 1.3%), with a median corr to the real motion course of 0.77.
Inversion + regeneration reproduces the real clock, so stage C is not invalidated by a reconstruction failure. File: `interim_stageA_n7.json`.
Gaussianity of x_inverted (n=6): `gauss_interim6.json`, as in #5457.
