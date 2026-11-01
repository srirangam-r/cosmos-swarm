# Task 226, pendulum readout: PRE-REGISTRATION (rahul-api-2)

Written and committed **before any task-226 pendulum clip exists**. rahul-api owns the design and the generation
(#4626). I only measure the pendulum arms and do not code events by eye; the blind event codes go to the volunteer coders.

## Input and arms (as rahul-api specified them)
Real GAUGE pend10 mid-swing frame `work/rahul-api/t193/pend10_mid_f93.png` (sha256 c9f4ab90…), 832x480, 93 f @ 24 fps.
Arms: `base`, `N` (same-length neutral sentence), `STOP` (pendulum stopped), `FAST` (swinging fast). Seeds 1-6,
`noise.device=cpu`, one GPU type. I'll take the arm labels and seeds from the sidecars or the job names rahul-api posts.
If the labels differ, I map them one-to-one and record the mapping here before measuring.

## Per-clip measures (readout.py, this commit)
- `me_all` and `me_late`: tracker-free motion. This is the mean |Δgray| between consecutive frames inside a fixed disk
  around the pivot (322,127) with r = 165 px. `me_all` uses all frames, `me_late` frames 46-92. Every clip has these values.
- `pend`: measure_pend v1 (tools/trk_ballfall, planted PASS for the period). Fields: period_s, flag (ok / check / fail),
  and rms_px, the RMS of its principal-axis track.

## Primary outcomes and decision rule
Each contrast is seed-paired. The contrasts are STOP:base, FAST:base, N:base, STOP:N and FAST:N.
1. **Motion presence (STOP's target):** paired diff of log me_late, and of log me_all.
2. **Speed (FAST's target):** paired log(T_A/T_B), only on seeds where both clips have flag `ok`. log_T_any is NOT used
   for inference: the known-answer run shows it is unreliable (base s28 hits the 60 s bound, and s25 gives 0.24 s).
3. **Text moves the dynamics beyond seed spread** only if both of these hold:
   (a) |mean paired diff| ≥ 1 × SD across seeds of the reference arm (|d| ≥ 1);
   (b) an exact whole-seed sign-flip p ≤ 0.05 (with 6 seeds the minimum p is 0.031). For the period with fewer than 5 ok
       pairs, (b) is replaced by a log-t 95% CI that excludes 0.
   A p value alone does not count: the identity re-encode gives p = 0.002 at d = -0.04 (see below).
4. **Coder-free stop indicator (secondary):** me_late < 0.5 counts as "still". Frozen frames give 0.009, and the moving
   Nano pend10 clips give 2.9-6.5. I report the rate per arm.
5. **Seed carryover (secondary):** the mean Pearson r between the per-frame motion curves of arm A and arm B at the same
   seed, vs a seed-label permutation null (exact up to 8 seeds). This asks whether the seed's motion timing survives the
   text change. A large r_same with a large text effect would mean text overrides the event but the noise keeps the rhythm.

Reported for every arm: n, n_ok, n_fail, geometric means, the T values, the T ratio to the real pend10 period (raj-3 real
reference, measure_pend README), and every per-seed difference. Nothing is dropped. Clips the tracker fails on stay in
the motion-presence outcomes.

## Known-answer check (done before freezing; kac.py, results in kac_result.json)
Source: rahul-api t193 base clips, pend10_mid_f93, q8, seeds 21-30. Synthetic arms: SAME (re-encoded), FAST (every 2nd
frame, so the same motion at 2x speed), STOP (frame 0 held).
| contrast | log_T_ok ratio (n) | log_me_all ratio, d | carryover r_same / r_diff |
|---|---|---|---|
| SAME:base | 1.001 (6) | 0.991, d = -0.04 (p = 0.002, codec bias) | 0.981 / 0.041, p < 1e-4 |
| FAST:base | **0.500** (5), d = -2.35 | 1.22, d = 0.90 | 0.08 / 0.03 (time-misaligned, as expected) |
| STOP:base | n/a (10/10 tracker fail) | **0.008**, me_late 0.009 vs 2.9-6.5 | n/a |
Per-seed FAST/base period ratios on ok pairs: 0.497-0.504. Lessons, built into the rule above:
(i) me_all saturates with speed (2x speed gives only 1.22x), so it measures motion presence, not speed;
(ii) p alone is not evidence;
(iii) log_T_any is excluded.

## What this does not cover
- Event realism or category (stopped by what? fast but broken?): blind coders.
- Rigidity gates (kiro-1 G3/G4): not applied in the primary. measure_pend's ok flag is the only period gate. As a
  sensitivity check I'll report periods restricted to clips that pass rodtrack G4 if that is cheap.
- One input frame, one GPU type, 93 f. The me ROI also picks up any robot or background motion inside the disk.

## Amendment 1: align with rahul-api's frozen design (525c282)
Committed before any t226 clip is fetched or viewed. At commit time 1 of 72 jobs was done and I had not downloaded it.
- **Clips.** rahul-api's `t226_P_{base,neutral,still,fast}_s{101..106}` (owner rahul-api). I download only these, with
  `fetch_p.py` (queue API, name prefix `t226_P_`). Arm = sidecar `extra_params.arm`, seed = sidecar `seed`. The labels
  map STOP = `still`, FAST = `fast`, N = `neutral`. Seeds 101-104 ran on a6k and 105-106 on a100. The GPU type is part
  of the seed block, so I make no cross-type comparison within a seed.
- **Primary reference = `neutral`**, as in rahul-api's PREREG. My primary contrasts are `still:neutral` (log me_late;
  log me_all reported alongside) and `fast:neutral` (log T on measure_pend `ok` pairs). Secondary: `base:neutral`,
  `still:base`, `fast:base`, and the seed carryover for each pair.
- **Decision rule** (unchanged, with the period branch made explicit):
  - TEXT CONTROLS: |mean paired diff| ≥ 1 SD of the reference arm across seeds, and the inference passes. With 6 pairs
    the test is an exact sign-flip p ≤ 0.05. With 4-5 period pairs it is a log-t 95% CI that excludes 0.
  - NUDGES: the inference passes but |d| < 1.
  - NOT DETECTED: the inference fails. This is not equivalence.
  - Period with fewer than 4 ok pairs: INCONCLUSIVE, matching rahul-api's rule.
- **fast prompt.** It asks for ~3 oscillations/s, so a T of about 0.33 s (8 frames per cycle at 24 fps). That is inside
  measure_pend's fit range (grid ≥ 0.3 s, bound 0.15 s). If the clips show sub-0.3 s swings, I'll report it rather than
  change the grid.
- **Independent of rahul-api's primary.** rec_period v1 is theirs. Mine are measure_pend v1 (raj-3, planted PASS) and
  the tracker-free me. As rahul-api asked, I also report a secondary rodtrack period: kiro-1 t191 rodtrack, my t228
  gates G4 valid_frac ≥ 0.6 and R² ≥ 0.8. Rodtrack has no planted validation, so it is labelled unvalidated.
