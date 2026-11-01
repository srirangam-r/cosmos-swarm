# t185 (kiro-1): more seeds and a second input for #3984 (Nano mid-swing pendulum period)

- Inputs: `pend10_mid_f93.png` (task 140, 1.52 s after release) and `pend12_mid_f101.png` (GAUGE pendulum 12, dev data, same transform: dedup + letterbox 832x468+6; 1.84 s after release, bob near the left turning point). `make_input.py`.
- Clips: 12 q8 I2V jobs (`jobs.jsonl`, sidecars/), base prompt, seeds 8-13, 832x480, 93 f @ 24 fps, 35 steps, CFG 6, Karras (flow_shift ignored, #2870). mp4s stay local (hashes in clips_SHA256SUMS).
- Tool: tools/trk_ballfall/measure_pend.py v1 unchanged (planted PASS). `run_nano.py`, `real_ref.py`.
- Real references (same tool on the real continuation; mocap zero crossings): pend10 f93 1.1777 s (mocap 1.1736), pend12 f101 1.1865 s (mocap 1.1746).
- Exclusion rule fixed before the clips: R² > 0.8.
- Result (`summary.json`): pend10 input, base arm, seeds 4-13: 6/10 readable, T = 2.07 ± 0.12 s (SE), ratio 1.76 ± 0.10 vs real. Excluded: s10 visibly FAST (0.90 s, R² 0.79, rod stretches), s4 broken geometry, s12/s13 track failures.
- pend12 f101 input: 0/6 readable by the tool. No period from it.
