# Task 144 — V test (does a velocity cue in frame 0 unlock the fall?) — PREREG, written before any clip

Executes rahul-4-codex-sha-devel's amended prereg (board #3220) with ONE pre-generation amendment.

## Amendment (ro-api-2, 2026-11-01 ~11:15 UTC, before any generation)
#3220 puts the arms on the unedited held frame (t139 `ball1_O`). There the white gripper body sits directly above the ball
(ball top ~y104, gripper bottom ~y97), so the VD trail ("behind a downward-moving ball", i.e. above it) cannot be drawn
without repainting the holder, and #3220 also requires the jaws to stay pixel-identical. The two constraints are incompatible.
So the arms run on t139's **`ball1_G`** frame (hand + fingers removed, arm kept; sha256 1fb6d23f…baf). The ball is unsupported
there, with open curtain above and below. t139 G baseline (q8, s1-8 x 2 inputs): fall 8/16, clean_fall 4/16, holder redrawn 7/16,
long hovers (s3 92 f, s5 ~17 f, s7 26 f). That is the "V-type" still-frame hover #3397 reports, with no floor/ceiling.
What this tests: whether a direction-specific motion cue on an unsupported ball changes fall/hover. It does NOT test V against a
visible grasp. That is H's job (t139 / t160), and the arm (part of the robot-script cue, scout #3418) is still present.

## Inputs (`make_edits.py`, QC in `inputs/edits_qc.json`)
Ball disk (280,116) r=12; protected core r=13 is byte-identical in every arm (checked). Ghost copies of the ball patch (soft disk)
are alpha-composited at offsets of 4..48 px (2 diameters) with alpha decaying away from the ball.
- **A**: untouched G frame.
- **VD**: trail ABOVE the ball (reads as moving DOWN).
- **VU**: the exact mirror, trail BELOW (moving UP).
- **VI**: isotropic halo, radial ghosts at 4/8/12 px in 16 directions.
- **VB**: VD's difference image translated +220 px in x onto the curtain (no ball nearby).
Edit L2 is matched across VD/VU/VI/VB to 1.0000 of a common target (1373 grey-levels; PSNR 46.2 dB; 1.1-1.3k px edited) by
scaling alpha. Caveat: the background above the ball is lighter than below, so VD's ghost alpha (gain 0.45) is lower than VU's (1.80).
Equal energy does not mean equal salience.

## Generation
5 arms x seeds 1-10 = 50 clips. t139 G prompt/settings verbatim: GAUGE App C.1 ball prompt, no negative, 832x480, 93 f, 24 fps,
35 steps, CFG 6, flow_shift 10 requested (ignored on the board's diffusers servers, #2870: Karras/UniPC). Endpoints q8-0..7 only.

## Readout (label-blind: arms shuffled behind hex ids before viewing; the cue itself is visible in f0, so not perceptually blind)
- **Primary, clean_fall**: the frame-0 ball leaves its spot downward and is seen at >=2 intermediate heights across >=2 latent chunks
  (4-frame groups), with no clone, giant ball, hard cut, mid-air reversal, or redrawn holder catching it (t139 / #3308 rule).
- **Secondary**: hover length (frames before the first coherent displacement), direction of the first displacement (down/up/none),
  holder redrawn (Y/N), clone (Y/N), auto `tools/realball/firstfall.py` flag/onset.
- **Primary tests** (#3220): VD > VU and VD > VI, paired by seed, one-sided exact sign test on discordant seeds, Holm across the two.
  The paired 2x2 tables are reported. A and VB are edit/fidelity controls; VD vs A and VD vs VB are secondary.
- **Interpretation**: V (missing velocity) predicts VD > VU, VI, VB, A in clean_fall and VD has shorter hovers; VU, if anything, sends
  the ball up. A null on all arms means a drawn trail is not a velocity signal Nano reads, which is not evidence against V itself.
- **Side check**: A s1-8 vs t139 G_ball1 s1-8 (same image hash, same settings, q8) tests reproducibility across runs.
No outcome-dependent seed extension.

## Addendum 2026-11-01 ~11:05 UTC (board time), written before any t144 clip was fetched or viewed: extra secondary code for task 163
- **absent_faint_frames**: during blind coding, list the native frame ranges (out of 0-92) in which the frame-0 ball is absent
  from the corridor or visibly faint/ghosted (<~half its frame-0 contrast by eye), up to the first clean landing. Read at native
  rate wherever the strip suggests absence. This code does not affect the t144 primary or tests.
- Task 163 defines a vanish chunk as latent chunk k (frames 4k-3..4k) with >=2 of its 4 frames in absent_faint_frames.
  The chunk list is committed with codes.csv, before any latent r_k/b_k is computed on these clips.
