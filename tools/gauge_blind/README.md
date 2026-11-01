# gauge_blind v1.1 (ro-1): blind scorer for task-24 GAUGE-ball eval clips

Frozen before any eval clip was opened: `gauge_blind.py` sha256 2d3ee65444c0, which imports `tools/bclock/bclock.py` sha256 3cde5a0351a0
(bclock referee planted PASS 12/12, msg 593). Run: `python3 -I tools/gauge_blind/gauge_blind.py CLIPDIR OUTDIR --fps 24`
→ `OUTDIR/scores.csv` (one row per clip), `scores_full.json` (tracks), `<clip>_sheet.jpg` (every 4th frame, tracked centre circled).

It applies the metrics rahul-3 pre-registered in msg 613 for clips made from the official GAUGE bouncing-ball frame (held ball at (281,119), 832x480, 539.8 px/m):
- **release**: the seeded NCC track drops more than 1 ball diameter (22 px) below frame 0. **The by-eye `eye_call` from the sheet is binding**
  (released | held | substitute | ambiguous), because Nano often makes a *second* ball do the fall (raj-1 task 2), and the tracker can latch onto it.
- **first-fall g**: bclock on the post-release track: curvature of the first flight if r2>0.98 and n>=5, else 2 h0/t_fall^2.
- **decay**: e1 = T1/(2 t_fall), median T_{k+1}/T_k, time-to-rest (<2 px for 6 frames after the first impact, censored at the last frame).
- Diagnostics: held_at_end_ncc, rest_minus_impact_px (negative = rests above the floor, e.g. back in the gripper), mean_ncc_post_release.

## Dry run on existing Nano GAUGE-ball clips (not task-24 clips) → work/ro-1/gauge_blind_test/
| clip | auto release | g | eye call | note |
|---|---|---|---|---|
| raj-1 gauge_ball1_neg_s1 (189 f) | 0 | – | held | held ball never leaves the gripper (raj-1 README agrees) |
| raj-1 gauge_ball1_noneg_s1 (189 f) | **1 (false)** | none (flag check) | substitute | a big second ball covers the gripper at f12-16; the track jumps 30 px, then sticks to the curtain |
| raj-2 raj2_dur_ball1_nf61_s1 (61 f) | 1 | **3.18** (r2 0.996) | released | falls to the plank by f10, then flies back up into the gripper (rest −200 px above the floor) |

Independent cross-check: raj-2's firstfall on the same 61 f clip gives g = 3.39 ± 0.26 (work/raj-2/task9_duration/firstfall/). The two agree within 1σ.
**Lesson: the automatic release flag alone is not enough. Use eye_call, and report substitute and return-to-gripper cases as their own failure categories.**
