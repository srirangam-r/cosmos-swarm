# Task 152: does a Nano clip's PhyFPS (Visual Chronometer) predict its ball's g?
Tool: Visual Chronometer, https://github.com/taco-group/Visual_Chronometer (commit cloned 2026-11-01), ckpt HF xiangbog/Visual_Chronometer
vc_common_10_60fps.ckpt (1,846,470,358 B). Unmodified predict.py: 30-frame windows, stride 4, 216x216 resize.
`run_vc.py` loads the ckpt with weights_only=True after listing its non-tensor globals; they are all omegaconf, builtins, collections or typing.
Env: uv venv, Python 3.11, torch 2.11.0+cu128, RTX 5090 laptop.

## Validation (vc_ref.json)
- Authors' demo clips at known 24/30/50 fps read 24.2 / 30.3 / 50.5, matching their README, so the install is faithful.
- Real GAUGE ball clips are 25 fps physical (dedup) and use the Cosmos input transform (832x480 letterbox):
  - Windows over the ball's fall and bounces: **14.3 ± 0.2** (range 13.5-15.3; 7 windows-means from 4 recordings).
  - Windows over a still hold or the resting ball: **52.2 ± 1.3** (45.1-55.7).
  - Whole-clip mean: 19.8 (from-f0 clips) vs 34.9 (mid-fall dd33-35 clips). The footage is the same at the same physical rate; only the clip start differs.
- **Fails the pre-stated check (≈25).** On this scene PhyFPS tracks how much of the frame moves, not the clock. In ball-motion windows it reads real motion as ×1.75 too fast, which would mean ×3 in g.

## Nano clips
run_all.sh also runs the 48 task-139 clips (vc_t139.json) and `analyze.py` joins them with firstfall g. Because of the failed validation and the
ball-is-most-of-the-motion confound, a PhyFPS-g correlation there is descriptive only.
