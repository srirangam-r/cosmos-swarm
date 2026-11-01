# Task 31 results: CFG negative text x negative metadata (finished by rog-cc for rog2)

Design (rog2, work/rog2/negmeta_arm): 2x2 = negative text {"" (empty), cosmos-framework JSON negative (nvneg)}
x negative metadata {INVERSE (diffusers default: "not 3.9 s / not 24 FPS"), SAME (cf default, metadata cancels)}.
GAUGE ball1/ball2 frame 0, 832x480, exact GAUGE prompt, 93 f @ 24 fps, 35 steps, CFG 6, flow_shift 10, seeds 1-2.
16 clips (sidecars in rog-cc's local clips/negmeta; the clips are not pushed, only the measurements and sheets).

## Files
- meas/*.json: firstfall v1 output per clip (seed 281,115 at frame 0, 539.8 px/m), from work/rog2/negmeta_arm/measure.sh.
- qc_sheets/<arm>.jpg: frames 0,6,12,18,24,36,48,60,72,92 (crop x130-450, y20-420), rows ball1_s1, ball1_s2, ball2_s1, ball2_s2.
- pixel_effects.json: motion = mean |frame diff| (gray, 416x240); pair_mae = mean |pixel diff| between two arms at the same seed x ball.

## Result (n=4 clips per arm: 2 balls x 2 seeds; small)
- Metadata (INV vs SAME) barely changes the clip. Paired pixel MAE INV vs SAME is 1.8-5.8 gray levels, against 5.3-14.9 for
  empty vs nvneg and 11.6-11.9 for seed 1 vs seed 2. The visual outcome is the same in all 8 INV/SAME pairs (sheets).
- The negative text sets the motion amount: nvneg lowers mean |frame diff| in 8/8 pairs (empty 2.06 +- 0.08, nvneg 1.49 +- 0.03, mean +- SE, n=8).
- Release: no arm gives a clean release then free fall.
  - Seed 1 (all 4 arms, both balls): arm lifts, ball shows up on the plank by f18-24 and looks much larger than the ball in the gripper; arm then swings down to it.
  - Seed 2, empty negative (INV and SAME): arm swings violently down onto the plank by f18; the plank flips; the ball ends on the plank or floor.
  - Seed 2, nvneg (INV and SAME): arm holds still to ~f36, then slowly lowers the ball, still gripped, to the plank by f72-92. No release.
- firstfall g values (meas/) mostly track arm-carried motion here (e.g. same_nvneg_ball1_s2 g=0.11 is the gripper lowering
  the ball). Do not read them as free-fall gravity. The hypothesis "SAME metadata shortens the fall" is not supported:
  the metadata does not change the outcome at this n.

## Dynamic degree (tools/nv_scoreboard/score.py --no_dover, RAFT on the 4060; dd_negmeta.json)
- dd_norm per arm (mean +- SE, n=4): inv_empty 6.99+-0.45, same_empty 7.06+-0.53, inv_nvneg 4.17+-0.50, same_nvneg 4.31+-0.41.
- Paired empty - nvneg: 2.79 +- 0.61 (8/8 positive; seed 1 ~1.1-1.35, seed 2 ~3.9-4.8). dd_binary 8/8 (empty) vs 5/8 (nvneg).
- Paired SAME - INV: +0.10 +- 0.09 (no effect).
