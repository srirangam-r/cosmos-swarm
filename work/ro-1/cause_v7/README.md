# v7: timed-settle clause on top of the D1 recipe prompt (ro-1, task 22)

Arms (fps_sweep/jobs_v7.jsonl, endpoint :8021, 832x480, 93 f, fps 24, 35 steps, cfg 6, shift 10, no negative):
- REC  = tools/recipe DEFAULT_PROMPT: "A smooth metallic sphere drops vertically from rest above a flat wooden surface, falling freely under gravity, impacting the plank, and bouncing in real time."
- RECT = the same, with "and bouncing in real time." replaced by "bounces only twice with rapidly diminishing heights, and comes to rest on the plank within about one and a half seconds, staying still for the rest of the video."
Inputs: mid-fall GAUGE real frames ball1 dd33 and ball2 dd35 (same as #2460). Seeds 1-3. 12 clips.

| | settles by f92 (eye, UNBLINDED) | gross artifact | last20 | DOVER fused | DD |
|---|---|---|---|---|---|
| REC | 0/6 | 4/6 (duplicate ball x2, giant sphere+debris, phantom box) | 7.23 | 0.547 | 4.43 |
| RECT | 5/6 (6th: no lift after f45 but rolls out of frame) | 0/6 (ball turns glossier/larger) | 0.99 | 0.543 | 2.13 |

Paired RECT−REC (n=6): last20 −6.24 ± 2.11 (6/6 lower); DOVER −0.004 ± 0.007, CI90 [−0.018, +0.011]; DD −2.30 ± 1.19 (6/6 lower).
ball1 |DD − real| (real GAUGE continuation 0.564): REC 0.86/10.14/0.97, RECT 0.47/2.06/0.10.
Caveat: REC has no "static camera" wording, so the camera dollies in several clips. That inflates last20 and DD for both arms (more for REC).
Files: eye_codes.csv, strips/, scores/ (tools/nv_scoreboard, CPU, DOVER reps 3), sidecars/, the s3 pair of mp4s.
