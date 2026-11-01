# Recipe arm: NVIDIA-reference negative branch vs the swarm default (rog2, task 30)

2×2 factorial at identical seeds and inputs (GAUGE ball 1/2 frame 0 letterboxed 832x480; exact GAUGE ball prompt; 93 f @ 24 fps; 35 steps / cfg 6 / flow_shift 10; seeds 1-2):

| arm | negative text | negative metadata |
|---|---|---|
| inv_empty (swarm default, control) | "" | INVERSE |
| same_nvneg (NVIDIA cosmos-framework reference) | cf JSON negative | SAME |
| same_empty | "" | SAME |
| inv_nvneg | cf JSON negative | INVERSE |

The first 8 jobs are the two diagonal arms. The off-diagonal arms separate the negative's metadata effect from its text effect.
Jobs are built by `make_jobs.py`. The SAME arms are emulated client-side: templates are off and the metadata sentences are appended to both the prompt and the negative using diffusers' own `_append` rule, so the jobs run on any existing server with no restart. The script verifies 16/16 jobs give exactly the text diffusers @86ef420b builds with `neg_meta` 'same' (checked against the real `tokenize_prompt`).
Queued 2026-11-01 03:40 UTC: `jobs_s1.jsonl` (all 4 arms, seed 1) on GB10 :8011, `jobs_s2.jsonl` (seed 2) on puget :8013. Arms are blocked by seed, so each comparison is within one server.
Measure: firstfall v1 (referee PASS msg 264) for g, fall time and release yes/no; flag=ok with QC checked. Also dynamic degree (tools/nv_scoreboard) to catch a motion-amount change.
