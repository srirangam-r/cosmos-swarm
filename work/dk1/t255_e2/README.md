# Task 255 E2: does Nano's Bridge forward-dynamics rollout stay still when commanded to stay still?

Continues rog1's E1 (finding #5243, work/rog1/t255). Ports CoCo's zero-action "drift energy" (https://arxiv.org/abs/2608.04653) to Cosmos3-Nano FD.
- `make_jobs.py`: 24 Bridge dev clips x {OWN, ZERO} x seeds 1-3 + 2 dupes = 146 jobs, CPU noise, model-card FD settings (17 f @ 5 fps, 256², 30 steps, CFG 1).
  ZERO = physical zero translation + identity rot6d + gripper held, quantile-normalised with tools/robot_pred/bridge_orig_lerobot_stats.json.
- `analyze.py`: frozen readout (docstring). Primary: rho = DE(zero)/DE(own), median + clip-bootstrap CI; decision thresholds 0.5 / 0.8.
  Secondary: drift inside vs outside the real-motion mask; same-seed vs different-seed motion coupling (does the noise carry motion when the action says stop); seed spread per arm; cross-stack check vs E1 q8 clips.
- Dry run of analyze.py on E1 clips renamed (own->own, swap->zero) ran clean; DE(static frame 0) = 0, DE(real) = 0.054 ± 0.004.
Frozen before any E2 clip was generated.

## Result (run 2026-11-01 15:20 UTC, analyze.py unchanged since 951ec6b)
- All 146 jobs ran on the GB10 queue's q8-0..7 (the new RTX Pro 6000 deployment, #5398), with CPU noise, 30 steps and CFG 1.
- Output: `e2.json` (full results), `analyze.log`, and `clips/`, which holds every sidecar plus the zero-arm and dup mp4s.
- The OWN mp4s are not committed. They are bit-identical to rog1's E1 clips in `work/rog1/t255/clips` (S4 max |diff| = 0), so use those.
- Primary: median rho = DE(zero)/DE(own) = 0.222 [0.198, 0.284], 24/24 clips < 0.5, so the decision is "stops when told".
