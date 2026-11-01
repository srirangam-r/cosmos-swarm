# GAUGE bouncing-ball I2V on Cosmos3-Nano (raj-1, task 2)

Setup: nvidia/Cosmos3-Nano, local diffusers Cosmos3OmniPipeline, bf16 with CPU group offload. Input is GAUGE real `bouncing ball/video/1.mp4`
frame 0, letterboxed 1280x720 -> 832x468 plus a 6 px black pad (GAUGE App. C.1.1), so the scale is 539.8 px/m. Output is 832x480, 189 frames at 24 fps,
35 steps, guidance 6, flow_shift 10, with the exact GAUGE prompt. Each `<name>.json` sidecar has every setting. The other 6 clips (ball 2 and seed 2) are still generating.

## What the clips show (visual inspection, n=2; qualitative, not a measurement)
In **both** clips Nano never releases the ball held in the gripper (~25-30 px, it stays in the fingers to the end).
Instead a **second, ~3x larger black ball (~90-100 px)** appears and does the "drop":
- `gauge_ball1_noneg_s1` (no negative prompt): the big ball slides in from the top edge (frames ~8-12) and covers the gripper.
  It falls at frames ~26-33 (~300 px in ~0.3 s), then rests on the plank. See `b1_noneg_s1_frames0-26.jpg` and `_frames24-47.jpg`.
- `gauge_ball1_neg_s1` (493-char negative prompt): a ghostly big ball fades in under the gripper at frames ~12-30. A solid big ball then
  **materializes mid-air** near the plank at frame ~36, lands at ~48 and bounces. See `b1_neg_s1_frames0-90.jpg`.

Consequences for measuring g:
- trk_ballfall v5 (`measure_dir`) gives flag=no_free_fall, g=-0.007 on the noneg clip. realball gives 0.65 [0.37, 0.88].
  Both fit frames 1-4: the held ball jitters by >2 px, and `first_impact` reads that jitter as the impact. Neither tracks the big ball's fall.
- Even with a perfect track, g depends on which ball and which scale. With the fixed 539.8 px/m, the big ball's fall reads roughly 10 m/s²
  (eyeballed, unvalidated). If the big ball has the real ball's size, the scale is ~3x smaller and g reads ~3 m/s².
  A ball that materializes mid-air has no defined free fall.
