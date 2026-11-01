# realball (raj-2): ball-drop g for real or Cosmos clips (held/slow release, duplicated frames)
Single-clip CLI. It builds on tools/trk_ballfall (trk.blobs tracking, measure_ball.fit_hinge), so it needs that folder next to it.
```
python3 -I realball.py clip.mp4 --fps 24 --mpp 0.001806   # GAUGE ball first frames at 832x480: 1/554 m/px vertical
python3 -I realball.py clip.mp4 --fps 24 --diam 0.10      # synthetic / clean footage
python3 -I realball.py --planted planted.json clip_dir out.json
```
Method:
1. Periodic exact-duplicate frames (e.g. 25 fps content in a 30 fps container) are dropped and re-timed uniformly. Dedup only fires when the repeats are periodic, so static frames are not dropped.
2. The release onset t0 comes from a v0=0 hinge fit.
3. g is a free-v0 quadratic from 1 frame after onset to the frame before first impact, with a residual-bootstrap CI.
4. Scale is --mpp, or the diameter divided by the median minor side of the post-onset, pre-impact blobs.
5. e is from the first rebound apex.
Output fields: g, g_ci95, r2, t0, fit_frames, n_fit, dup_period, fps_true, g_hinge_v0 (the v0=0 model for comparison), e.
Validation:
- Planted cases: referee PASS 20/20 within 10% (g 8/8 <5%, e 4/4 <5%, period 4/4 <5%, a 1/4 <5% + 3/4 5-10%); referee_result_v1.json, planted_estimates_v1.json. period/a use trk_ballfall v3 code unchanged.
- Real footage: GAUGE real drops, with dedup and a mocap-calibrated 830.5 px/m at 1280x720. Free-v0-from-onset+1 g = 9.94 ± 0.18 (n=17) vs 9.81 (work/raj-2/gauge_realcheck_v2).
Caveats:
- On real footage the blob size is a biased scale (+32 to +38% in g). Use a calibrated --mpp.
- Static camera only. The tracker is a thresholded diff, not SAM.
