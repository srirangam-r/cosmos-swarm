# realball (raj-2): ball-drop g for real or Cosmos clips (held/slow release, duplicated frames)
Single-clip CLI. It builds on tools/trk_ballfall (trk.blobs tracking, measure_ball.fit_hinge), so it needs that folder next to it.
```
python3 -I realball.py clip.mp4 --fps 24 --mpp 0.0018525  # GAUGE ball first frames letterboxed to 832x480 (raj-1 cosmos_local): 1/539.8 m/px
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
- v1.1 (motion prior: ignore hold-phase jitter before the first frame >=4 px below the start): planted estimates byte-identical to v1; GAUGE real drops 10.01 ± 0.21 (n=16 with the rms<8 px & n_fit>=5 cut), median 9.89 over all 22 (gauge_realball_v11.json).
- Scale: raj-1's cosmos_local letterboxes 1280x720 -> 832x468 + 6 px pad, so 830.5 x 0.65 = 539.8 px/m (raj-3 msg 154). 554 px/m (stretch) reads g 2.6% high. tools/trk_ballfall/calib_frame0.py recovers the resize from frame 0.
Caveats:
- On real footage the blob size is a biased scale (+32 to +38% in g). Use a calibrated --mpp.
- Static camera only. The tracker is a thresholded diff, not SAM.
