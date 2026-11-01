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

## firstfall.py (v1): first fall of ONE seeded ball, for Cosmos clips with a moving scene
Why: trk.blobs (used by realball and measure_ball v5) takes the largest change blob. On Cosmos GAUGE clips that is
often the retracting gripper or the tilting plank, so both tools fit the wrong object (task 9 first clip).
```
python3 -I firstfall.py clip.mp4 --fps 24 --ppm 539.8 --point x,y [--pframe N] [--tmax N] [--qc qc.png]
python3 -I firstfall.py --planted planted.json clip_dir out.json
```
- Tracker: you seed a point on the ball at frame --pframe (default: the trk.blobs centroid). The seed colour is the median Lab of a 5x5 patch.
  A pixel is a candidate if its colour matches (Lab distance < 25) AND it differs by > 30 from frame 0 or from the last window frame.
  A static dark curtain fails the change test, and a light gripper or plank fails the colour test.
  Each frame keeps the component nearest the constant-velocity prediction. Scale (--diam only) is the minor side of the uncoloured change blob that contains the ball.
- Fit: the realball v1.1 recipe, unchanged. Flag as v5: ok needs dAIC > 10, R² > 0.98 and n ≥ 5.
- Extra readouts: fall_time_s, fall_px/fall_m, g_from_h_T = 2h/T², and d_growth (size at impact / at fit start).
- --tmax: for Cosmos clips that reset after impact, cut the window a few frames after first contact. The last window frame is a reference background, so g depends on it.
  On task-9 clip 1 it gave 3.39 [2.90, 3.88] with tmax=16 and 2.75 [1.77, 3.66] with no tmax. Report both.
- Planted: referee PASS 20/20 within 10%, with g 8/8 and e 4/4 < 5% (ff_referee_v1.json, ff_planted_estimates_v1.json; sha256 c7a1033f616c).
  g/e are within 3% of realball v1.1 on every clip. period/a use the trk_ballfall v3 code. The d_growth addition leaves the planted estimates byte-identical.
- Real footage: see work/raj-2/task9_duration/firstfall/firstfall_gauge_real.json (GAUGE real drops at Cosmos resolution, 539.8 px/m, vs mocap).
- Known failure: a black ball in front of the black curtain shows no change against the background, so the track is lost.
  Example: raj-1's spawned big ball, lost at frame 29. Use samball (SAM2.1) for those clips.
