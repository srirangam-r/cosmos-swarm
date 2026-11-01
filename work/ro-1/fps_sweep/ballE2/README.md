# ball_E_ball2_fps12_93f_s1 — impact times by eye (ro-1, task 22, UNVALIDATED)
Clip: Cosmos3-Nano (local diffusers, :8021), image gauge_ball2_dd35_832x480.png (GAUGE ball, mid-air first frame), 832x480, 93 f, cond fps 12, 35 steps, guidance 6, flow_shift 10, seed 1. Sidecar: ../out/ball_E_ball2_fps12_93f_s1.json (local only).
Method: impacts = frame of lowest ball position, read from crops_*.jpg (crops.py; 240x380 crop, y ticks every 50 px). ±0.5 frame.

Impacts (frame): 2, 7, 13, 19, 27, 33, 40.5, 48, 55, 63, 71, 77, 83, 89  -> 14 impacts, ball still bouncing at f92.
Intervals: 5, 6, 6, 8, 6, 7.5, 7.5, 7, 8, 8, 6, 6, 6 frames. Mean (f7->f89) 6.83 frames = 0.57 s at cond fps 12 (0.28 s if played at 24).
Apex y (px, smaller=higher): ~240, ~275, ~250, ~215, ~190, ~190, ~220, ~225, ~180, ~230, ~245, ~255, (rising at f92). Start y at f0 ~165.
=> NO damping (apex does not decay over 13 bounces; e_eff ~1.0), same as ball1 (fps12 E and fps24 F) and raj-3 finding 476.

Comparison (same seed 1):
| clip | cond fps | impacts in 93 f | mean flight (frames) | flight (cond s) |
| ball1 E | 12 | ~20 | ~4.3 | 0.36 |
| ball1 F | 24 | ~12 | ~7.6 | 0.32 |
| ball2 E | 12 | 14 | 6.83 | 0.57 |
Flight time per bounce differs ~1.6x between the two first frames at the same fps, so the image matters as much as fps here.
