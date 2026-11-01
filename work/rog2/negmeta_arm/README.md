# Recipe arm: NVIDIA-reference negative branch vs the swarm default (rog2, task 30)

2×2 factorial at identical seeds and inputs (GAUGE ball 1/2 frame 0 letterboxed 832x480; exact GAUGE ball prompt; 93 f @ 24 fps; 35 steps / cfg 6 / flow_shift 10; seeds 1-2):

| arm | negative text | negative metadata |
|---|---|---|
| inv_empty (swarm default, control) | "" | INVERSE |
| same_nvneg (NVIDIA cosmos-framework reference) | cf JSON negative | SAME |
| same_empty | "" | SAME |
| inv_nvneg | cf JSON negative | INVERSE |

The first 8 jobs are the two diagonal arms. The off-diagonal arms separate the negative's metadata effect from its text effect.
Run: `python tools/cosmos_local/client.py work/rog2/negmeta_arm/jobs_negmeta_ball93.jsonl --url http://<server> --out <dir>` from the repo root. The server needs `tools/cosmos_local` at or after the commit that adds `neg_meta.py`.
Measure: firstfall v1 (referee PASS msg 264) for g, fall time and release yes/no; flag=ok with QC checked. Also dynamic degree (tools/nv_scoreboard) to catch a motion-amount change.
