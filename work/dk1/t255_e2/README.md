# Task 255 E2: does Nano's Bridge forward-dynamics rollout stay still when commanded to stay still?

Continues rog1's E1 (finding #5243, work/rog1/t255). Ports CoCo's zero-action "drift energy" (https://arxiv.org/abs/2608.04653) to Cosmos3-Nano FD.
- `make_jobs.py`: 24 Bridge dev clips x {OWN, ZERO} x seeds 1-3 + 2 dupes = 146 jobs, CPU noise, model-card FD settings (17 f @ 5 fps, 256², 30 steps, CFG 1).
  ZERO = physical zero translation + identity rot6d + gripper held, quantile-normalised with tools/robot_pred/bridge_orig_lerobot_stats.json.
- `analyze.py`: frozen readout (docstring). Primary: rho = DE(zero)/DE(own), median + clip-bootstrap CI; decision thresholds 0.5 / 0.8.
  Secondary: drift inside vs outside the real-motion mask; same-seed vs different-seed motion coupling (does the noise carry motion when the action says stop); seed spread per arm; cross-stack check vs E1 q8 clips.
- Dry run of analyze.py on E1 clips renamed (own->own, swap->zero) ran clean; DE(static frame 0) = 0, DE(real) = 0.054 ± 0.004.
Frozen before any E2 clip was generated.
