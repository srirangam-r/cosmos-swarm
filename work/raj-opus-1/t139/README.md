# Task 139: does Nano drop the GAUGE ball once the holder is painted out of frame 0?

Question (scout-1 #3097): is "won't release" a **holder prior** (H: a visible grasp keeps the object held) or a
**still-frame / zero-velocity lock** (V)? A scene-template prior (S: robot lab implies manipulation) predicts something in between.

## Inputs (`inputs/`, sha256 in `inputs/edits.json`; built by `make_edits3.py`, classical texture copy, no generative model)
- `ballN_O.png`: unedited GAUGE frame 0 (raj-1 ball1 / raj-2 ball2 letterboxed 832x480). The Franka gripper holds the ball.
- `ballN_A.png`: the **whole robot removed** (hand, fingers, cables, arm, base, LED glow). The ball floats in front of the curtain.
- `ballN_G.png`: **hand + fingers removed, arm kept**. The arm's flange ends ~25 px above a floating ball.
- The ball disk (280,116) r=12 is untouched in every edit. Previews: `preview.jpg` (top: O | A ball1; bottom: G ball1 | A ball2), `preview_ball.jpg`.
- Edit caveat: the copied curtain block is a faintly visible rectangular panel; the base area has a small seam.

## Generation (`jobs.jsonl`, queue owner raj-opus-1, q8-0..7 only, submitted 09:58 UTC Nov 1)
3 arms x 2 inputs x seeds 1-4 = 24 clips (jobs.jsonl), plus seeds 5-8 (jobs_s5-8.jsonl, submitted 10:01 UTC after seeing only O_ball1_s1, for power) = 48 clips. GAUGE ball prompt (App. C.1, same as raj-1's `gauge_ball1_noneg_s1`), no negative,
832x480, 93 f, 24 fps, 35 steps, guidance 6. flow_shift 10 requested (ignored on the board diffusers servers, #2870).

## PRE-REGISTERED readout (written before any clip was seen)
Per clip, from per-frame crops of the ball corridor (f0-40 every frame, then every 4th frame):
1. **fall** (primary, Y/N): by f92 the ball has left its frame-0 position downward by > 1 diameter (> 23 px)
   AND it passes through >= 3 intermediate heights on the way (continuous descent, not a jump within one 4-frame latent).
2. **jump** (Y/N): the ball reaches a lower position with no intermediate heights (teleport / mode switch).
3. **clone** (Y/N): a ball stays at the frame-0 position while another ball appears lower.
4. **holder back** (A/G only, Y/N): a gripper, hand, string or arm appears and holds the ball.
5. Automatic secondary: `tools/realball/firstfall.py` (planted PASS 20/20) seeded at (280,116): flag, onset frame, fall_time_s.
Primary contrast: fall rate A vs O and G vs O (pooled over inputs; n=8 per arm, Fisher exact + difference with Wilson CI).
H predicts A >> O (towards the ~15/24 white-wall rate, #3097); V predicts A ~ O ~ 0; G between O and A tells
"contact/grasp" (G ~ A) from "robot present" (G ~ O).
Coding is not blind to arm (the edit is visible in every frame), so the primary call uses the mechanical criteria above.

### Amendment (10:01 UTC, after seeing only one clip, O_ball1_s1)
That clip shows a path the primary code doesn't name: the gripper lifts the ball out of frame (f6), then a larger ball
re-enters from the top (f16) and falls continuously; the gripper later returns holding a ball. Added codes, reported
alongside (not replacing) the primary:
6. **reentry** (Y/N): the ball leaves the frame or vanishes, and a ball later enters from the frame edge.
7. **any_fall** (Y/N): any ball falls continuously through >= 3 intermediate heights anywhere in the clip.
Primary stays as pre-registered (a fall that starts from the frame-0 position).

### Amendment 2 (10:22 UTC, after 31 clips): post-hoc codes, labelled as such
- `carried` (O/G): the arm or a tether lowers the ball. Not a fall under the primary; `fall_or_carried` is reported as a sensitivity check.
- `morph` / `descent_artifact`: the ball swells, morphs or duplicates during its descent. `clean_fall` = fall AND no descent artifact. This is post-hoc and secondary.
- The two inputs are near-identical frames and outcomes cluster by seed, so `summarize.py` also reports a seed-level paired analysis (arm − O per seed, sign test). Treat that as the honest n.
Interim status: see `summary.json` (regenerate with `python3 summarize.py codes.json ff_summary.json`).

### Final, all 48 clips (seeds 1-8 × ball1/ball2 × O/A/G), coded 10:30-10:45 UTC
- Seed-8 clips coded with `zc.py` zooms (frames listed in `zooms_s8/`). New post-hoc flag `midair_reversal`: the ball descends from its f0 position but turns upward in mid-air with no contact. Counted as `fall` by the prereg letter, and as `descent_artifact` (so not `clean_fall`). It occurs in A_ball2_s8 and G_ball1_s8 (same seed).
- A_ball1_s8 is borderline. The ball hovers unsupported for 49 frames and then shows only 2 sharp intermediate heights, so `fall=0` under the same rule as G_ball1_s7.
- Counts (n=16 per arm): fall O 2, A 12, G 8. clean_fall O 0, A 11, G 4. holder_back O 0, A 0, G 7. clone O 6, A 1, G 1. auto_fall O 6, A 14, G 7.
- A−O fall: +0.625, Fisher p=0.001 at clip level. At seed level: 6 up / 1 down / 1 tie, sign p=0.125. A−O clean_fall at seed level: 6 up / 0 down, sign p=0.031.
- Full output: `summary.json`.
