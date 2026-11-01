# Task 210: does the D1 Rule R suffix degrade Nano's real-robot clip prediction?

Bridge forward dynamics (shared `tools/robot_pred/devset_bridge`, 24 WidowX clips), chunk 1: real frame 0 + 16 actions -> 16 frames.
Arms: base / R (+Rule R) / N (+neutral, length-matched), seeds 0-3, q8-0..7 only, 288 clips. Design and decision rule: PREREG.md
(committed b2403e6 before the grid). 30 steps, CFG 1.0 (model-card FD setting), requested flow_shift 10 (Karras on board servers).

Files: make_jobs.py, submit_rest.py, fetch_t210.py, score_t210.py (shared score.py metrics), analyze_t210.py, sheet.py;
scores.json (per clip x arm x seed + static floor), results.json (contrasts), sidecars/ (one per clip), sheets/ (QC strips:
rows real/base/R/N, frames 0,4,8,12,16). Clips: swarm@board.tail0c526a.ts.net:~/jobs/rahul-api/t210/clips/ (clips_SHA256SUMS).

Reproduce: `python3 make_jobs.py <devset_bridge> jobs.jsonl --seeds 0 1 2 3`, submit to the queue pinned to q8,
`python3 fetch_t210.py clips`, `python score_t210.py <devset_bridge> clips scores.json`,
`python analyze_t210.py scores.json results.json <devset_bridge>/index.json`.
