# t115 stack check: is q8 worse at rigid pendulum swings?

Inputs: real GAUGE pend10 (f93) / pend11 (f81) mid-swing frames, prompt and settings in ../jobs_*.jsonl (93 f, 24 fps, 35 steps, cfg 6, neutral "midB" prompt).

- blind1: 16 clips, f2-92 step 6. q8 4/10 rigid, refs 6/6.
- blind3 (primary): 32 unique midB clips (dedup: same seed on a100 = int-a100 = task-99 a100, pixel-identical), f2-50 step 3. q8 1/10, non-q8 13/22, one-sided Fisher p=0.011.
- Test-retest of one coder (ro-api-3) on 16 shared clips: 11/16 agree (all 5 disagreements 1->0 at the finer view). One coder only, so this needs an independent coder.

REVIEWERS: code blind3_crops/*.mp4 (pendulum crop, named by blind id) or blind3_sheet*.jpg BEFORE opening blind3_KEY.json / blind3_unblinded.json. Rule: rigid = straight rod of constant length, fixed pivot, one bob, smooth arc.
blind2 = q8 midT/midW s1-3 (rigid: midT 2/6, midW 2/6).
