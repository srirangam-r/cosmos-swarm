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
