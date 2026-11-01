# samball (raj-1): SAM2.1-tracked ball-drop g. WORK IN PROGRESS, UNVALIDATED (not yet run on the planted cases)

Why: on Cosmos GAUGE ball clips the held ball jitters during the hold. trk_ballfall v5 and realball then take that jitter as the first impact
and fit frames 1-4 (work/raj-1/gauge_ball). Nano also tends to spawn a second, larger ball. You therefore need to choose *which* object to track.

```
python3 -I samball.py clip.mp4 --fps 24 --ppm 539.8 --point x,y [--pframe N] [--device cpu|cuda] [--qc qc.png] [--track_out track.json]
```
- Tracking: SAM2.1-hiera-small via transformers (>= 5.x `Sam2VideoModel`), with a positive point prompt on frame `--pframe`, propagated forward.
  The default point is the trk_ballfall blob on the first frames.
- Fall window: y_top = median of the first 5 tracked y values; first impact = first frame with y >= y_max - 0.15*(y_max - y_top);
  the window starts 6 frames before the last frame still near y_top.
- Fit: trk_ballfall v5 `fit_onset` (skip=1) on that window, unchanged. Also reports a residual bootstrap CI, R², dAIC (quadratic vs linear), the same flag rule as v5,
  g_by_skip, fall_px, and d_px (mask equivalent diameter near impact).
- Speed: CPU is slow (>10 min for 189 frames at 832x480 while Cosmos is running on the same machine).

Status: does not count as a measurement until it passes the referee's planted cases.
