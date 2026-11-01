# robot_pred: real-robot clip prediction (NVIDIA scoreboard item 4)

Measures how well Cosmos3-Nano predicts the **real future of a robot clip** from its first frame and the robot's actions (action-conditioned forward dynamics). Use it before and after any fix: the score must not drop beyond seed noise. Owner: rohith-cc-1 (board task 5).

## Dev set: `devset_bridge/` (24 clips, about 20 MB)
- **Source:** `IPEC-COMMUNITY/bridge_orig_lerobot` (LeRobot v2.0, WidowX 250, camera `image_0`, 256×256, 5 fps).
- **Selection:** `random.Random(20261101).sample(episodes with length ≥ 33, 24)`. See `selection.json`.
- **Per clip:**
  - `first_frame.png`;
  - `real.mp4`: 33 real frames, encoded losslessly with x264;
  - `action_chunks.json`: 2 chunks × 16 steps × 10-D, in the same format as the Nano model card's AgiBot example.
- **Actions** follow NVIDIA's own `BridgeOrigLeRobotDataset` (cosmos-framework@55f0554):
  - domain `bridge_orig_lerobot` (domain id 7);
  - 10-D: position change (3), 6-number rotation change (6), gripper (1), frame to frame;
  - NVIDIA's frame corrections (`_DEFAULT_ROTATION`, `_TCP_TO_FLANGE`, `_BRIDGE_TO_OPENCV`) applied;
  - each dimension scaled to [−1, 1] with `bridge_orig_lerobot_stats.json`, using NVIDIA's 1st and 99th percentiles.
  - Check: 1–5% of values per dimension fall outside [−1, 1], which is what that scaling should give.
- **Do not train or fine-tune on these 24 episodes.** They are the swarm's dev set. They come from Bridge's *train* split, so Nano may have seen them in pretraining. That makes this a regression check (before vs after), not a test of generalization.

## Run
```
pip install torch lpips scikit-image av pandas pyarrow requests pillow
# 1. generate (GPU machine with a vLLM-Omni Cosmos3-Nano endpoint)
python generate.py devset_bridge runs/base_s0 --url http://HOST:PORT --seed 0
# 2. score (CPU is fine)
python score.py devset_bridge runs/base_s0 runs/base_s0.json
```
- `generate.py` follows the model card's autoregressive recipe:
  - chunk 1 is conditioned on real frame 0 and actions 0–15;
  - chunk 2 is conditioned on chunk 1's last generated frame and actions 16–31;
  - defaults are the model card's forward-dynamics example: 30 steps, guidance 1.0, flow_shift 10.
- A JSON sidecar with every setting is saved next to each clip.
- `build_devset.py` rebuilds the dev set from the raw episodes, or makes a bigger one.

## Metrics (`score.py`)
- Computed on predicted frames 1–32 against the real ones at 256×256:
  - PSNR (higher is better);
  - SSIM (higher is better);
  - LPIPS-alex (lower is better).
- Each is reported overall and per chunk, as mean ± standard error over clips.

**Floor baseline (`baseline_static.json`):** "predict nothing moves", i.e. repeat frame 0.

| | PSNR (dB) | SSIM | LPIPS |
|---|---|---|---|
| all frames | 18.23 ± 0.49 | 0.796 ± 0.011 | 0.154 ± 0.011 |
| chunk 1 | 19.30 ± 0.55 | 0.818 ± 0.011 | 0.130 ± 0.010 |
| chunk 2 | 17.16 ± 0.50 | 0.773 ± 0.013 | 0.179 ± 0.014 |

A model that follows the actions should beat this clearly, at least in LPIPS and in chunk 2.

## To do
- Base Nano runs at ≥ 2 seeds, to measure seed noise. Any "no drop" claim needs those seeds.
- Optional DROID set: NVIDIA's DROID data is an internal LeRobot conversion. The public data would need its own check that the actions match.

## Not yet verified
- Whether a stock vLLM-Omni server accepts `domain_name=bridge_orig_lerobot`. The model card only shows `agibotworld`, but `EMBODIMENT_TO_DOMAIN_ID` in cosmos-framework lists Bridge.
- Whether 256×256 input works, or needs `size` and `image_size` set to 480.
- Test one clip first: `--only bridge_002407`.
