# End-to-end check of the Cosmos ball pipeline on REAL GAUGE drops (raj-3, task 6)
Real GAUGE bouncing-ball clips 1-22 (HF InternRobotics/GAUGE-Dataset, dev split, measured only) were prepared exactly like Cosmos I2V outputs.
Each clip is deduplicated (25-in-30 fps), letterboxed 1280x720 → 832x468 + 6 px pad (raj-1's input transform), and re-encoded as mp4.
Each clip is then measured with measure_ball v5 (trk.blobs tracker, free-v0 quadratic from hinge onset + 1 frame) at a fixed 539.8 px/m (830.5 × 0.65; raj-2's mocap calibration).
Reference: mocap g with the same v5 estimator (skip=1), which gives 9.815 ± 0.009 over 22 clips (`../gauge_mocap/onset_mocap_test.py`).

Result: flag=ok on 18/22 clips. g/mocap = 0.965 ± 0.020 (SE; sd 0.085; median 0.938); g = 9.46 ± 0.19 m/s². The CI95 covers mocap on 15/18.
The v4 hinge on the same clips: 0.889 ± 0.010. Per-clip precision is ~±9%, because a real-speed fall gives only 5-6 frames at 25 fps.
The 4 non-ok clips are all tracking failures (QC images: `gauge9_lb832_qc.png`, `gauge19_lb832_qc.png`). They give g = -0.04, 5.05, 0.03 and 3.12 with R² 0.70-0.97.
Clip 19 is the worst case: the robot re-grasps the ball by the last frame, so the first/last-frame background hides the held ball, and the fit reads 0.034 [0.024, 0.044].
That number looks like "slow gravity" with a tight CI. The flag catches it (R² 0.929 < 0.98).
Caveats: the flag thresholds were set after seeing clips 1-10, before 11-22. The tracker (trk.blobs) and the px/m constant are shared with raj-2's analysis, so this replicates fit/timing/resolution, not tracking or scale.
