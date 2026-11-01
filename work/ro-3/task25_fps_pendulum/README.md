# Task 25 (ro-3): does the conditioned fps change Nano's pendulum period?
Input: GAUGE official `input/first frames/832x480/pendulum/frame.png` + `input/text prompts/pendulum/prompt.txt` (exact), no negative prompt,
832x480, 189 f, 35 steps, cfg 6, flow_shift 10, seeds 1-2. Arms: fps 24 / 12 / 48, and fps 24 with the duration template off (`jobs.jsonl`).
Server: `server_ro3_nooffload.py` (raj-1's tools/cosmos_local server, offload removed) on puget GPU 0, http://100.77.182.40:8013.
Measure: `measure_all.py` runs tools/trk_ballfall/measure_pend v1 on each clip, full and with frames 0-11 dropped -> `results.json`, `qc/`.
Clip sidecars: `pend_*.json`. The mp4s stay on puget (~/swarm-work/ro-3/exp_fps/clips), since the GitHub link is slow; ask ro-3.

## Status (shift 1, 03:50 UTC): PROVISIONAL, tracking unreliable
- Nano outpaints the pillarbox. By frame ~11 the black side bars are filled with scene and the camera has reframed.
- The prompt says 10°, but the pendulum swings through very large arcs (often near-horizontal), and the ball passes behind or in front of the post.
- measure_pend flags every clip so far `check`. fps24 s1: T_fit 4.41 s (106 f), T_zc 4.58 s. fps12 s1: T_fit 4.65 s (56 f), but T_zc 2.29 s (inconsistent).
  So nothing quantitative yet. Next: a more robust angle tracker (SAM2 or pivot-angle), validated on planted + real GAUGE pendulum.

## Update 03:55 UTC (seed 1, three arms; all flag=check, so UNVALIDATED)
| arm | T_fit (s) | T_fit (frames) | T_zc (s) | R² | note |
|---|---|---|---|---|---|
| fps 24 | 4.41 | 106 | 4.58 | 0.69 | large swings |
| fps 12 | 4.65 | 56 | 2.29 | 0.39 | fit and zc disagree; ball occluded by the post |
| fps 48 | 2.17 | 104 | 2.09 | 0.76 | cleanest track; fit and zc within 4% |
Tentative reading: fps 24 vs 48 gives the same period in frames (~105 f), so the period in stated seconds goes as 1/fps. Nano seems not to scale its
pendulum dynamics with the conditioned fps, which is consistent with "fixed events per clip" (task 9). Needs seed 2, the template-off arm and a better tracker.
