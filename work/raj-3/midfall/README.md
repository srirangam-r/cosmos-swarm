# Task 15: Nano's ball g from a real mid-fall first frame (raj-3)

Question: from GAUGE's held-ball first frame, Nano doesn't release the ball (raj-1, msgs 198/209). Is its gravity still slow when frame 0 already
shows the ball in free fall?
Inputs: `inputs/gauge_ball{1,2}_dd3{3,5}_832x480.png`, a real GAUGE frame ~2-3 frames after release, letterboxed like raj-1's inputs.
Jobs: `jobs_midfall.jsonl`, run by `jobs_gb10.jsonl` on the GB10 server. Exact GAUGE prompt, no negative prompt, 832x480, 189 f, 24 fps, 35/6/10, seeds 1-2.
Control: raj-1's held-frame clips at the same settings (work/raj-1/gauge_ball).

## Measuring: `measure_midfall.sh [clip_dir]` → `midfall_fit.py`
- Track: the seeded single-ball track of `tools/trk_ballfall/seeded.py` (firstfall v1; referee PASS msgs 264, 312).
  The trk.blobs tools are unsafe here because of the gripper (finding 296).
- `g_mid`: a free-v0 quadratic over frames 0 .. (lowest point of the first descent) − 1, with a residual-bootstrap CI.
  The impact frame is excluded (impact-frame bias, finding 109). `ok` needs n ≥ 7 frames, R² > 0.98 and g > 0.
  seeded.py's own fall fit needs a hold phase (hinge onset), so on a mid-fall start it returns `no_free_fall`. Ignore `g_fall` here.
- `g_bounce`: seeded.py's first-rebound curvature, unchanged.

## Validation of g_mid (not a referee check: planted clips start at rest)
rahul-3's sim_drop clips (seeds 1000-1019, known g, sidecar px/m), cut to start 2 frames after the fall starts, seeded at the true centre (`--simcheck`):
| arm | ok (n≥7) | g_mid / g_true | within 10% |
|---|---|---|---|
| real g = 9.81 | 10/20 | 0.996 ± 0.017 (SE; sd 0.054) | 9/10 |
| wrong g 1.5-4 | 16/20 | 1.003 ± 0.021 (sd 0.085) | 14/16 |
- 4/20 real and 3/20 wrong clips are `too_few_frames`: lost tracks or very short drops. With 5-6 fit frames the error reaches 1.23-1.28×, hence n ≥ 7.
- False oks: wrong_00006 (hand; 1.22×, its rebound track failed) and wrong_00017 (silver ball, short drop; 0.79×, the same scene that broke v5).
  Check every QC image, and distrust g_mid when g_bounce fails or disagrees.
- The `simcheck_mid_*.json` flags were written with the earlier n ≥ 5 rule. The table re-applies n ≥ 7.

## Real reference
At real speed, the GAUGE continuation (`real_cont/real_ball1_from_dd33.mp4`) reaches the floor ~5 frames after dd33, so g_mid can't be measured on it (weak, n=4).
The reference is the first-rebound g: seeded 9.02 [7.94, 10.10] (weak) and blob/measure_bounce 9.58 [9.31, 9.87].
If Nano's clock is slow by ×2-4, the fall takes 10-20 frames and g_mid becomes measurable.

## Results (S12, 2026-11-01 03:45 UTC). Clip 1 of 4: `out_gb10/midfall_ball1_dd33_noneg_s1.mp4` (sha256 a34d674a…, sidecar next to it)
What it shows (contact sheets `look/b1s1_f0_23.jpg`, `look/b1s1_f24_116.jpg`): the ball falls from frame 0 and hits the plank at frame 5.
It then **keeps bouncing to the end of the visible record (≥ frame 116, ~4.8 s) with no visible loss of height**: impacts at frames
5, 15, 23, 32, 43, 53, 62, 72, ~81, 90, 97, 107. The real ball (GAUGE ball 1 from the same frame) makes 3-4 bounces of shrinking height (120 → 58 → 36 → 23 px) and then rests.
| readout | Cosmos mid-fall b1 s1 | real reference | validated? |
|---|---|---|---|
| first-rebound g (seeded.py, flight 6-12) | **9.90 [8.53, 11.19] m/s², flag ok** | 9.58 [9.31, 9.87] (ball 1, measure_bounce); 9.63 ± 0.05 (n=19 real drops) | yes (referee PASS 20/20, msg 312) |
| g_mid, frames 0-4 (n=5) | 16.4 [12.0, 20.7], weak | n/a (real is too fast, n=4) | no (n<7) |
| 8h/T² per bounce cycle, 5 cycles (frames 5-62) | 12.8 ± 1.3 (SE) | — | no |
| frames from the input frame to first impact | 5 @ 24 fps (0.21 s) | ~4-5 @ 25.4 fps (README above) | — |
| height restitution √(h_{k+1}/h_k) | **0.99 ± 0.02** (4 ratios) | **0.72 median** (1st→2nd flight, n=19 real drops, `res/real22_restitution.json`) | no (direct track geometry) |
| flight-time ratio T_{k+1}/T_k | 1.01 ± 0.10 | 0.80 median (n=19) | no |
| prompt says | "coefficient of restitution is 0.58 … diminishing peak heights … come to rest" | | |
Control (only the first frame differs; same prompt, seed 1, settings, diffusers stack): raj-1's held-frame `gauge_ball1_noneg_s1`. The ball is never
released and a 3× larger ball spawns; SAM on the spawned ball gives 3.71 [3.26, 4.27] (unvalidated), and measure_bounce gives 1.90 weak.
Tools: `midfall_fit.py` (seeded track) → `bounce_seq.py` (impacts/apexes/rise/T/e from the saved track; unvalidated readouts). The track jumps off the ball at frame 63;
`res/*_from64*` re-seeds at frame 64 (294,249) and covers frames 64-107.

## Pendulum (task 8), `../cosmos_pend/res/`
`gauge_pend1_noneg_s1` (GAUGE pendulum prompt, held first frame, seed 1, no neg): **no pendulum swing.** The rod stays ~horizontal and the robot arm moves;
a ball appears and vanishes at various points on the rod (`pend_s1_sheet.jpg`). measure_pend reads flag=check, R² 0.25. That's noise, not a period.
