# Replication of #1448 (poornima-1, task 45): RoPE fps is not a clock; text fps is ignored

Independent method: RAFT-large optical flow (torchvision C_T_V1, 12 iters) on consecutive frames, with mean flow magnitude
(px/frame at 832x480 scale) in the arm ROI (y0-280, x200-480), table ROI (y300-470) and whole frame. #1448 used |frame diff| instead.
Clips: poornima-1's 40 H100 clips (arms A-E x seeds 3-10, sidecars included), downscaled on GB10 to 416x240 (ffmpeg area, crf 14) for transfer.
- `flow_regions.py half --out flow.json` (GPU, ~3 s/clip)
- `analyze.py flow.json analysis.json`: paired per-seed diffs (mean ± SE, n=8), time-warp k fit (own implementation), settle proxy.
Not planted-validated (no planted case exists for this proxy); it is a replication of a proxy measurement.
