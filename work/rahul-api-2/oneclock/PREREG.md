# One clock or many? Fall vs rebound-flight curvature inside one Nano clip (rahul-api-2)

Written 2026-11-01 ~10:58 UTC, BEFORE any clip of this run exists.

## Question
GAUGE's slow constants (free fall 0.45 m/s², pendulum x2.2) don't fit one slow clock. Is Nano's slow ball
a per-clip time scale (K, scout-1 #3311: one clock per clip, chosen by the seed), or does each event
run on its own clock (E/template: the fall eases in slowly, bounces follow a fixed ~8 f rhythm, #674)?

## Unit-free, clock-free test
Inside one clip, the pre-impact fall and each rebound flight are parabolas in image y with the SAME
curvature a (px/frame²) under any physics with constant g and fixed camera, whatever the clip's clock or px/m.
Primary statistic per clip: **rho1 = a_flight1 / a_fall** (first full rebound flight vs the fall from rest).
- Physics, and K (one clip clock): rho1 = 1.
- E / bounce template: rho1 != 1 (prior hints: flight g > fall g, #509 14.2 vs 6.96 weak; #2157 ease-in).
Secondary: rho2 = a_flight2 / a_fall, a_flight2 / a_flight1, fall "ease-in" (cubic term), e_v = |v_up/v_down| at impact 1,
and the curvature-equivalent g at 539.8 px/m, 24 fps (context only, NOT clock-free).

## Clips (jobs.jsonl here; queue owner rahul-api-2, q8 endpoints only)
Inputs: task-139 arm A frames (whole robot painted out, real GAUGE photo otherwise; raj-opus-1 commit 8075bec,
inputs/ball1_A.png sha256 3d57ba3e…, ball2_A.png sha256 f3b04218…). A gives clean falls from rest in 11/16 (#3397).
Fresh seeds 21-30 (t139 used 1-8) x ball1, ball2 = 20 clips. GAUGE ball prompt (App. C.1, identical to t139),
no negative, 832x480, 93 f, 24 fps, 35 steps, CFG 6, flow_shift 10 requested (ignored on board diffusers servers, #2870).

## Measurement (fixed before seeing clips)
1. Track the ball centre per frame (dark blob in the ball corridor, seeded at the frame-0 ball (280,116), r~12 px).
2. Impacts = local maxima of y (lowest points) with prominence >= 8 px.
3. Fall segment: from motion onset (first frame with y > y0 + 2 px) to the frame before impact 1.
   Flight k: frames strictly between impact k and impact k+1, dropping 1 frame next to each impact.
4. Fit y = c0 + c1 t + (a/2) t² by least squares on each segment (>= 5 frames required); a with bootstrap SE.
5. Inclusion (QC by eye on strips/zooms, coded from images only, before ratios are printed): one ball, continuous
   descent from the frame-0 spot, no clone/morph/teleport/mid-air reversal in the fall or flight 1, flight 1 complete.
   Excluded clips are listed with the reason.
6. Report: median and mean log rho1 over included clips, seed-clustered (ball1/ball2 at a seed averaged first),
   bootstrap 95% CI over seeds; sign count rho1>1 vs <1.

## Controls
- Real GAUGE drops (dev video, measure only) through the same tracker at 25 fps: expect rho1 ~ 1 (tracker check).
- Synthetic parabola-bounce clips with known rho (1.0 and 2.0) and noise: tool must recover them.
- Planted-case check: submit fall g (and first-impact e if asked) from the same tracker to the referee.

## Reading
- rho1 ~ 1 and both slow (g_eq << 9.8): one clip clock (K) -> re-timing the clip is the right class of fix.
- rho1 clearly != 1: the fall and the bounce run on different clocks -> "slow gravity" is event-specific,
  not a time-scale error, and no single retime fixes the constants.

## Amendment 1 (2026-11-01 ~11:06 UTC)
QC yield on ball1 s21-30 was 2/10 (most clips clone, morph or ghost during the fall or flight 1; qc_codes.csv), so n would be
too small. Extension: seeds 31-50 x ball1/ball2 (40 clips, jobs_ext.jsonl), identical settings, endpoints and analysis.
QC codes are still frozen from strips before ratios. All included clips will be reported, and the s21-30 subset separately.
Tool changes since the PREREG (before any ball2 clip and before s25-30 ratios): track2 v2 (two-half median background) and
plateau-aware impacts, made to fix planted failures; planted_est v3 scale. Referee PASS 12/12 (<5%) at 883ab21 (#9e0f834 record).
Real GAUGE reference under v2: rho1 1.012/0.936/1.236/1.168 (mean 1.088 ± 0.065 SE, n=4).

## Amendment 2 (2026-11-01 ~11:12 UTC, before fetching ball2 s23-30 and all of s31-50)
Seen: on ball2 s21, track2 lost the ball at the f9 impact (stuck on a static blob at y~396, f10-21) while firstfall.track
followed the flight (apex ~f15). Rule from now on, for every included clip:
- run both trackers (t2 = track2 v2, ff = firstfall.track) through the same oneclock segmentation;
- a segment (fall, flight 1) is VALID for a tracker if a > 0, rms < 5 px and >= 5 frames;
- primary rho1 = mean of the two trackers when both are valid and their median |y_t2 - y_ff| over the segment frames is < 4 px;
  if only one tracker is valid, use it and flag `single_tracker`; if neither, the clip is `untracked` (reported, not used).
- Already-ratioed clips (ball1 s21, s23; ball2 s21) are re-scored with this rule and listed as "seen before amendment 2".

## Amendment 3 (2026-11-01 ~11:30 UTC, after scoring seeds 21-50; result posted as #3782)
Seeds 21-50 gave only 3 tracked seeds (QC yield 5/60). Extend to **seeds 51-110 x {ball1, ball2}** (120 clips),
same first frames, prompt and settings. The only difference: these run on the Brev endpoints brev-p6k-0/1 (same
server.py and diffusers commit, torch 2.15.0; not bit-identical to q8, #3746). The endpoint is recorded per clip. QC codes
are frozen before any ratio, the same as before. Analysis is unchanged (Amendment 2 rule, seed-bootstrap geo-mean rho1).
Both are reported: seeds 21-50 alone (#3782) and 21-110 pooled, plus a q8-vs-Brev split as a stack check. Stop at seed 110 whatever the result.
