# Task 257 results (rahul-api-2): does a seed's pendulum period carry across real pendulum frames?

Frozen PREREG + e3seed.py a75e1c0 (before fetch). All 72 E3 clips (Raj, q8, CPU noise, seeds 601-624 x pend10_mid_f93 /
pend11_mid_f81 / pend14_mid_f81), every clip 93 frames, hashes in results/E3_SHA256SUMS. measure_pend v1 unchanged.
Disclosure: a first run saw only 27/72 clips (results/partial27/, #5269); nothing in the code or rule changed after it.

## Pre-registered decision (gate 'ok'; 'relaxed' gives identical numbers)
- Usable periods: pend10 7/24, pend11 5/24, pend14 8/24 (20/72 = 28%).
- **Q1: INCONCLUSIVE** (only 6 seeds have >= 2 usable inputs; rule needs 8). ICC(1) 0.52, perm p 0.060, seed-bootstrap CI [0, 0.84].
- **Q2: no evidence the pend10-ranked bank helps.** Top-6 bank held-out success (usable and within +-20% of the real period on
  pend11/pend14) 2/12 vs all 24 seeds 2/48; exact p 0.25 over all C(24,6) banks. Real-speed base rate: 4/72 clips.
- Nano period, median of usable clips / real mocap: pend10 1.42x, pend11 1.21x, pend14 1.32x (real 1.174-1.176 s).

## Per seed (T s, ratio to real), usable clips only
| seed | pend10 | pend11 | pend14 |
|---|---|---|---|
| 602 | 2.19 (1.86) | 0.69 (0.59) | - |
| 604 | 2.51 (2.14) | 2.38 (2.03) | 2.40 (2.04) |
| 608 | 1.32 (1.13) | 1.42 (1.21) | 1.44 (1.23) |
| 617 | 1.22 (1.04) | 1.24 (1.05) | 1.25 (1.07) |
| 619 | 1.43 (1.22) | 1.42 (1.21) | 1.42 (1.21) |
| 623 | 2.25 (1.92) | - | 2.48 (2.11) |
Single-input usable: 601 pend14 1.53, 607 pend10 1.66, 612 pend14 1.56, 620 pend14 1.58.
Descriptive: 5/6 multi-input seeds agree within +-10% across inputs; s602 is the exception (0.69 looks like a half-period).

## POST HOC (after seeing result.json; not a decision): is it the same video?
results/posthoc_sameclip.py/.json. Gray 208x120. Matched control = cross-input pairs with DIFFERENT seeds.
- Pendulum ROI MAE, same seed vs different seed: 8.3 vs 10.1 (pend10:11), 8.5 vs 10.1 (10:14), 7.0 vs 10.1 (11:14).
- The same-seed clip is the nearest of the 24 candidates in 16/24, 12/24, 18/24 seeds (chance ~1/24 each).
- ROI motion-energy time series r: same seed 0.33 / 0.43 / 0.59 vs different seeds -0.01 / 0.00 / 0.02.
- Whole-frame MAE is not informative here: the three input frames themselves differ by 2.1-3.4 gray.
So the seed carries the motion COURSE (not just the period) across these three start frames, for all seeds, readable or not.

## Eye QC (unblinded analyst; results/qc/)
- ok_pend10.jpg: most 'ok' clips are NOT plausible pendulums. Swings reach or pass horizontal (s602, s604, s619, s623), and the rod
  thickens or partly vanishes (s608, s602). measure_pend checks periodicity, not rigidity (#4569).
- s617 (s617_s619_all.jpg): on pend10/pend11 it is a near-identical, moderate-amplitude rigid swing at 1.04-1.05x real speed.
  On pend14 the same course, but the rod rises higher. s619 has the same over-horizontal course on all three inputs.

## Limits
Three start frames from ONE apparatus and camera (near-duplicate scenes; a property of these frames, not shown for other
scenes). One prompt, one GPU type (q8), 24 seeds, 28% readable. No DOVER. Post-hoc numbers are exploratory.
