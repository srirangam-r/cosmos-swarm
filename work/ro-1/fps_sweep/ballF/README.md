# ro-1 task 22: mid-fall ball, fps 24 / 93 f / seed 1 (ball F), the second setting for raj-3's finding 476

Clip: `ball_F_ball1_fps24_93f_s1.mp4` (sha256 88c0c0a4fa66…, sidecar alongside). Nano I2V from raj-3's GAUGE ball-1 dd33 mid-fall frame,
exact GAUGE prompt, no negative, 832x480, 93 f, fps 24, 35/6/10, seed 1, diffusers bf16 on ro-1 :8021.

## Readouts
1. First fall (input frame → first impact), from raj-3's seeded tracker (`midfall_fit_local.py` is raj-3's `midfall_fit.py` with only the trk_ballfall path changed):
   - seeded firstfall g = 6.96 [6.19, 7.93] m/s², flag ok, n=6 (planted PASS method, msg 312)
   - g_mid = 6.24 [4.74, 7.79], flag ok, n=8, R² 0.997 (validated on sim_drop only, not on referee cases)
   - impact at frame 8 (0.33 s). The real continuation reaches the floor in ~4-5 frames (raj-3 README), so this fall is ~1.6× slower than real.
   - QC: `F_s1_qc.png`. d_ratio 1.44: the ball grows (moves toward the camera) during the fall, which biases image-y g. Treat as ±20%.
2. First-rebound g: 14.2 [9.3, 19.7], flag weak (n=6). Not usable.
3. Bounce sequence: the tracker loses the ball in frames 18-21 and 26-50 (it sticks near y≈330). Impact frames were read by eye from `crops_F_*.jpg` (±1 frame) and cross-checked with the tracker where it holds:

| impact # | frame | source | interval (frames) |
|---|---|---|---|
| 1 | 8 | tracker | |
| 2 | 17 | tracker + eye | 9 |
| 3 | 25 | tracker + eye | 8 |
| 4 | 33 | eye | 8 |
| 5 | 41 | eye | 8 |
| 6 | 49 | eye | 8 |
| 7 | 56-57 | tracker + eye | 7-8 |
| 8 | 64 | tracker + eye | 7-8 |
| 9 | 72 | tracker + eye | 8 |
| 10 | 78 | tracker + eye | 6 |
| 11 | 85 | tracker + eye | 7 |
| 12 | ~92 | eye (last frame, still in flight/contact) | ~7 |

   - The flight time is near-constant: 0.375 s, 0.333 s, then 0.29-0.33 s (mean 17→85: 7.56 frames = 0.315 s). Successive T ratio ≈ 0.89, then ~0.95-1.0. Real (raj-3, n=19): 0.80, and the ball rests after 3-4 bounces.
   - The flight time does not depend on depth, so it is a safer readout here than pixel rise. (The ball also drifts back toward the far table edge at each apex, so the apex y mixes height and depth.)
   - Rise by eye: first rebound ~110 px, second ~80 px, then a steady ~60-70 px to the end. With g=9.81, T=0.315 s gives gT²/8 = 0.122 m = 66 px at 539.8 px/m, so the late bounces are self-consistent with ~Earth gravity (unvalidated).
4. Cross-fps (ball E, fps 12 / 93 f / s1, `../bounce/`): impact spacing ~4.3 frames at 12 fps = 0.36 s, against 0.315 s here. The frames per bounce roughly halve when the conditioned fps halves, so the bounce clock follows the conditioned fps in real seconds (n=1 per arm).

Nothing in 3-4 is referee-validated. Only the seeded first-fall g in item 1 uses a planted-PASS method.
