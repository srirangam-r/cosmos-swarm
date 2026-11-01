# GAUGE real ball drops, v2: timing, scale, and the v4 tools (raj-2, task #7)
Data: HF `InternRobotics/GAUGE-Dataset`, `data/rigid/bouncing ball/{video,json}/1..22`. Dev data, measured only, never trained on.
Tracks: `trk.blobs(mode='ball')` per frame (trk_ballfall @5e06ff7), dumped by `../gauge_realcheck/dumptracks.py`.

Findings
1. **The videos are 25 fps footage in a 30 fps container.** Every 6th frame is an exact duplicate in all 22 clips (frame diff < 0.1× median). Distinct-frame rate is 25.16 ± 0.03 fps.
   Hinge-fit residuals (median over 19 clips, same frames):
   - A: drop dups, re-time uniformly at the distinct-frame rate: 3.6 px
   - B: keep dups at t = i/30: 11.4 px
   - C: drop dups, keep i/30 stamps: 9.7 px
   A is the right clock. B and C give per-clip g sd 0.23 vs 0.135 (ratio to mocap). See `timing_test.py` and `timing_test_results.json`.
2. **The blob-size scale is badly biased on real footage.** The thresholded blob short side of the free/rest ball is 34.5 px (median). The mocap-calibrated diameter is 49.83 ± 0.11 px, so g comes out ×1.32 too high. In the gripper-hold frames it is ~24 px, so ×2. Mocap calibration: px/m = (rest_y − hold_y)/(z_release − z_rest). It is **830.5 ± 8.0 px/m (sd over 19 clips) at 1280x720**, a fixed camera for all 22 drops.
   → For Cosmos clips made from GAUGE ball first frames at 832x480: about **554 px/m vertical** (×480/720) and 540 px/m horizontal. The ball is about 33 px. This assumes the ball stays at the same depth.
3. **Dedup + hinge (free t0, measure_ball.fit_hinge) + calibrated scale** gives g/mocap_hinge = 0.900 ± 0.031 (SE; sd 0.135; n=19; 3 clips excluded for n_fit<10: 4, 16, 19). With the fit-rms < 8 px quality cut it is 0.941 ± 0.015 (sd 0.060, n=17, 82% within 10%), g = 8.82 ± 0.14 m/s².
   The mocap reference itself reads 9.37 ± 0.01 (hinge) / 8.77 ± 0.02 (free quadratic) rather than 9.81.
4. **The v4 tools run unchanged** (`gauge_eval2.py`, results file when done):
   - rohith_measure `fit_ball` crashes on every real clip: IndexError in `hm_width` from the frame-0 chord scale.
   - measure_ball v4 is erratic: clips 1-6 give 12.1, 14.5, 18.4, 0.7, 16.4, 0.0, because the scale comes from the median blob, which is the occluded hold.

Not tested: SAM-based masks; Cosmos clips; the hold-centroid bias in the calibration (the gripper occludes the ball top).
