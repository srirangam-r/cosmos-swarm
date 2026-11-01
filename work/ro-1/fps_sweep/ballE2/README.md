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

## ball_F_ball2_fps24_93f_s1 (shift 7, 2026-11-01 04:10 UTC)
Same ball2 dd35 mid-fall frame, exact GAUGE prompt, no negative, 93 f, **fps 24**, 35/6/10, seed 1, :8021.
Impacts read by eye from crops (F2_crops_*.jpg, ±1 f): 7, 18, 28, 39, 48, 57, ~66.5, 76, ~85.5 → 8 flights,
intervals 11, 10, 11, 9, 9, 9.5, 9.5, 9.5 → **9.81 ± 0.28 (SE) frames = 0.409 s** per bounce. Flight time shrinks slowly (11 → 9.5 f).
Unlike ball1 (no damping), the rise DOES decay: apex y ≈ 205 → 265 px with contact y ≈ 330-340, so the rise goes ~130 → ~65 px over 8 bounces
(real e≈0.72 would leave <10 px). Unvalidated readout (eye, no tracker). F2_impacts.json has the numbers.

### Cross-phenomenon timing table (seed 1, n=1 per cell; frames per cycle)
| scene | 93 f fps 12 | 93 f fps 24 | 189 f fps 24 | 189 f fps 48 |
|---|---|---|---|---|
| ball1 bounce (dd33) | ~4.3 (rough) | 7.64 | 9.27 (raj-3) | – |
| ball2 bounce (dd35) | 6.83 | 9.81 | – | – |
| pendulum (GAUGE f0) | 30-35 (tools disagree, motion non-stationary) | 50.8 | 107.1 (ro-3) | 103.4 (ro-3) |

Model frames ∝ fps^α · N^β:
- Ball bounce, fps 24→12: α ≈ 0.83 (ball1), 0.52 (ball2). α=1 means seconds-locked, α=0 means frames-locked.
- Ball bounce, 93→189 f: β ≈ 0.27 (ball1).
- Pendulum: fps 24→12 gives α ≈ 0.54-0.74; fps 24→48 gives α ≈ 0.05; 93→189 f gives β ≈ 1.05.

So the clip-length scaling (finding 525) is strong for the pendulum, weak for the bounce, and the fps response is partial for both and asymmetric for the pendulum.
