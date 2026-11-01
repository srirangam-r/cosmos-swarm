# ro-1 task 22 cause v5/v6: does a timed prompt make Nano's bounce settle?

Inputs: raj-3 mid-fall frames, GAUGE ball1 dd33 / ball2 dd35 (real photos), 832x480, 93 f @ 24 fps, 35 steps, cfg 6, flow_shift 10, no negative prompt.
Endpoint: ro-1 :8021 (diffusers bf16, RTX 6000 Ada). Exact prompts are in the sidecars and in jobs_v5/v6.jsonl.

Arms (one edit to the exact GAUGE ball prompt F):
- F: base GAUGE prompt ("...followed by a sequence of successive bounces with diminishing peak heights, before finally coming to rest on the plank.")
- QT (timed): "...bounces only twice with rapidly diminishing heights, and comes to rest on the plank within about one and a half seconds, staying still for the rest of the video."
- QS (control): F plus "The camera and the table stay still for the rest of the video." This adds stillness language with no ball timing.

Metrics:
- late_motion_v56.json: mean |frame diff| in the ball corridor (x220:360, y130:360) over the last 20 frames (analyze.py). Real GAUGE continuation: 0.47.
- eye_codes.csv: does the ball settle by f92, plus an approximate rest frame. UNBLINDED (the coder knew the arms).
- scores/: DOVER (reps 3) and VBench DD from tools/nv_scoreboard/score.py, CPU.
- table.py gives the paired QT−F and QS−F deltas by input+seed.

jobs_v7.jsonl (queued): the Deliverable-1 recipe prompt (tools/recipe DEFAULT_PROMPT) vs the same prompt plus the timed clause, ball1/ball2 × seeds 1-3.
