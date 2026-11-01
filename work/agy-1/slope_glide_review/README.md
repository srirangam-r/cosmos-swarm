# Independent Replication of Finding 434 (Nano Constant-Velocity Slope Glide)

Reviews `rahul-2`'s finding 434 on the two seed-1 Cosmos3-Nano GAUGE plastic slope-slider clips (`plastic_released_nf93_s1.mp4` and `plastic_corrected_nf93_s1.mp4`, 832x480, 93 frames @ 24 fps).

## Independent Methods (`replicate_434.py`)
1. **Ghost-free CIE Lab background-difference tracker (`lab_bgdiff`)**:
   - Reference background built by splicing the median of frames 70–92 over the upper-right half (`x > 430`, after the cube has slid away) and frame 0 over the lower-left half (`x <= 430`), completely eliminating any resting-cube ghost.
   - Foreground pixels require CIE Lab distance `> 22.0` from the reference background AND dark luminance (`L < 65`), morphologically opened (`3x3`), tracking the largest connected component along the plank corridor.
2. **Normalized cross-correlation template tracker (`ncc_template`)**:
   - Matches the initial `44x44` frame-0 cube template (`cv2.TM_CCOEFF_NORMED`) within a causal neighborhood along the plank.
3. **Independent axis & scale checks**:
   - Trajectory PCA motion axis agrees with the geometric plank axis to `0.48°` (released) and `2.63°` (corrected, larger due to cube tumbling).
   - Scale sensitivity compared between the 0.50 m plank calibration (`0.880 mm/px`) and the frame-0 0.05 m cube bounding box (`61.82 px` -> `0.809 mm/px`, -8.1%).

## Summary of Results (plank scale `0.880 mm/px`, bootstrap SE over 1000 resamples)
- **Arm A (`plastic_released_nf93_s1`, turntable prompt)**:
  - Sustained onset: frame 6 (`rahul-2`: 6). Single-frame (>3 mm) jitter at frame 4 returns to frame-0 position at frame 5.
  - Early acceleration (frames 5–14): `0.17 ± 0.06 m/s²` (`rahul-2`: `0.17`), sensitive to single-frame onset frame 4 (`0.31 ± 0.06 m/s²`).
  - Steady glide velocity (frames 15–62, n=48): `0.1605 ± 0.0009 m/s` (`rahul-2`: `0.161 m/s`), linear `R² = 0.9991` (RMSE `2.78 mm`). PCA axis: `0.1605 m/s`; NCC template tracker: `0.1602 m/s`.
  - Late acceleration (frames 15–62): `-0.013 ± 0.003 m/s²` (`rahul-2`: `-0.01 m/s²`).
  - Whole-slide quadratic acceleration (frames 6–62, n=57): `0.004 ± 0.004 m/s²`, linear `R² = 0.9987` vs quadratic `R² = 0.9988` (`rahul-2`: `0.00 m/s²`).
- **Arm B (`plastic_corrected_nf93_s1`, corrected slope prompt)**:
  - Onset: frame 15 (`rahul-2`: 15).
  - Early acceleration (frames 14–23): `0.79 ± 0.19 m/s²` (`rahul-2`: `0.79 m/s²`), window-sensitive (`0.42–0.94 m/s²` over 6–12 frames).
  - Steady glide velocity (frames 24–39, n=16): `0.331 ± 0.007 m/s` (`rahul-2`: `0.334 m/s`), linear `R² = 0.9960` (RMSE `4.03 mm`). PCA axis: `0.332 m/s`; NCC template tracker: `0.291 m/s` (lower because the cube tumbles and changes shape).
  - Late acceleration (frames 24–39): `-0.13 ± 0.09 m/s²` (`rahul-2`: `-0.10 m/s²`).
  - Whole-slide quadratic acceleration (frames 15–39, n=25): `0.027 ± 0.038 m/s²` (`rahul-2`: `0.04 m/s²`), with `dAIC(lin - quad) = -0.64` (linear model preferred by AIC; linear `R² = 0.9977` vs quadratic `R² = 0.9978`).
  - Cube splitting confirmed: at frames 40–43, the cube splits into two dark components of comparable size (e.g. frame 42: `1969 px` at `(324, 376)` falling to the table and `1457 px` at `(262, 295)` continuing along the plank), vs 0 split frames in Arm A.
