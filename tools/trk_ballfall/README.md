# trk_ballfall (raj-3)
Tracker for ball free fall (g, restitution e), incline block (a), pendulum (period).
Usage: python3 -I trk.py planted.json <clip_dir>   (writes est.json; clips named <clip_id>.mp4)
Ball: background built from first/last frame, blob via diff, scale from median minAreaRect minor side = known diameter; quadratic fit up to first impact; e=sqrt(rebound apex / drop height) on first rebound only.
Block: median-bg diff (THR=25), scale from median long side; v0=0 fit with free t0. Pendulum: damped cosine on blob x.
Referee planted check: v3 = 20/20 within 10% (PASS). Caveats: static camera only; untested on Cosmos output or real photos; block 'a' still 5-10% off.

## measure_ball.py (v4, Cosmos-ready single clip)
`python3 -I measure_ball.py clip.mp4 --fps 24 --diam 0.06` (or `--mpp <m/px>`). Prints JSON: g, g_ci95 (residual bootstrap), g_sd,
g_scale_sys_1px (g change per 1 px of diameter error; usually the dominant systematic), r2, t0 (release time), impact_frame, e, d_px, and g_poly_v3 for comparison.
Model up to first impact: y = y0 + ½g(t−t0)² for t>t0, so a ball that hovers before release is handled. 
Planted: `--planted planted.json clipdir` reproduces the v3 estimates exactly (ratio 1.000 on all 20), so the referee's v3 PASS (20/20) applies.
Synthetic hover test (`synth_hover_test.py outdir`): hinge/g_true = 0.965 ± 0.008 over 9 cases (g 0.45/2/9.81, hover 0/0.5/1 s), independent of hover.
Frame-0 fits collapse under hover (true 9.81 with 0.5 s hover gives 0.37 for b+kt² and 1.10 for a free quadratic). Results: work/raj-3/synth_hover_results.json.
Caveat: the CI covers fit noise only. Add the scale systematic (~4% per px for a ~23 px ball). Static camera only. Not yet run on Cosmos clips or real video.

## Caveat from real footage (raj-3, shift 4; see work/raj-3/gauge_mocap)
measure_ball v4's hinge model (v0=0 at a free t0) is unbiased only for a clean release. On GAUGE real mocap the gripper releases slowly
(~2 frames at 1-4 m/s^2), and the hinge reads 9.36 vs 9.74 for a free-v0 quadratic from the sustained-free-fall onset.
On held-ball clips (real or Cosmos), prefer a free-v0 fit from the onset. The classical diff tracker is too noisy on GAUGE real video
(black ball on a black curtain, 7-9 unique frames; see work/raj-3/gauge_video): use SAM masks there.

## WARNING (raj-3, shift 10): v5's flag=ok is NOT safe when a gripper or hand moves
trk.blobs takes the largest change blob. In scenes where a holder lifts away after release, it tracks the holder.
On rahul-3's sim_drop clips, the result on holder scenes was 0/15 usable for real g. 2 wrong-g holder clips came back **flag=ok with wrong g**, one at 0.036× truth (g=0.077, R² 0.988).
For GAUGE-style Cosmos clips with a gripper, use a seeded single-ball tracker (tools/realball/firstfall.py). Run `measure_bounce.fit_track` on its track for the first-rebound g.
Evidence: work/raj-3/simdrop_check/.

## seeded.py v1 (raj-3): use this on gripper/hand scenes (referee PASS 20/20, g 8/8 <5%, e 4/4 <5%)
`python3 -I seeded.py clip.mp4 --fps 24 --ppm 539.8 --point x,y [--pframe N] [--tmax N] [--qc out.png]`
- Track: raj-2's firstfall v1 seeded single-ball tracker (tools/realball/firstfall.py, which must sit next to this folder). Seed a point on the ball at frame `--pframe`.
- Output: `g_fall` (firstfall first-fall g), `g_bounce` (measure_bounce fit_track on the same track, first rebound flight), and `g` = g_bounce if its flag is ok, else g_fall.
- On sim_drop (work/raj-3/simdrop_check), measured/true is 0.996 ± 0.006 for the rebound and 1.003 ± 0.018 for the first fall (real g).
- Planted results: planted/est in work/raj-3/simdrop_check/referee_seeded_v1.json.

## measure_ball.py v5 (referee PASS 20/20, msg 147, commit 3f6f104)
Change from v4: the hinge fit only locates the release t0. g is a **free-v0 quadratic from the first frame ≥ t0 + 1 frame** up to the frame before
first impact. That handles slow gripper releases. skip=1 was chosen on GAUGE real **mocap** (n=22): skip 0/1/2/3 give 9.742/9.815/9.828/9.831,
hinge 9.363. That choice was made before any video numbers. Planted: v5/v4 ratio 0.998-1.004 on all g; all g within 5% of truth.
New outputs: `g_by_skip` (stability over 0-3 skipped frames), `n_quad`, `r2_lin` and `dAIC_quad_vs_lin` (quadratic vs constant velocity),
`g_hinge_v4`, `onset_frame`, and `flag` = ok (dAIC>10, R²>0.98, n_quad≥5) | weak | no_free_fall (dAIC≤2: the track is not an accelerating fall).
CLI: `--ppm <px/m>`, `--skip`, `--dedup` (drops exact-duplicate frames and re-times at the distinct rate; GAUGE real video is 25 fps inside 30).

### Cosmos clips: `measure_dir.py <dir> --ppm 539.8`
Batch over `<name>.mp4` + `<name>.json` sidecars (fps from the sidecar). Writes `results_v5.json` and `<name>_qc.png`: the y(t) track with onset and impact, plus frames with the
tracked blob circled. **Look at every QC image.** On GAUGE real clip 4 the tracker locks onto the resting ball and then the gripper (g ≈ 0, R² 0.70, flag no_free_fall).
Scale for GAUGE ball first frames: the mocap-calibrated 830.5 px/m at 1280x720 (raj-2, msg 146) × the input resize. Letterbox 0.65 → 539.8 px/m; stretch to 480 rows → 553.7 vertical.
Do not use the blob size on this scene: the black ball on the black curtain is undercounted by ~30%.

Fallback (commit after 6531c12): if the primary tracker (first/last-frame background) gives flag≠ok, measure() retries with a temporal-median background
(`tracker` = ball | diff in the output; the other result is kept under `primary` / `fallback`). The fallback rescued none of the 4 GAUGE real failures (clips 4, 9, 19, 20).
It is kept because it only replaces a non-ok result with an ok one. Planted results are unchanged, since all planted clips are ok with the primary.

## measure_pend.py v1: pendulum period, release-aware (raj-3, task 8)
`python3 -I measure_pend.py clip.mp4 --fps 24 [--dedup] [--qc out.png]` prints JSON with period_s, period_ci95 (moving-block residual bootstrap),
period_zc_s (median full period from zero crossings), zc_periods, beta (damping, free sign), r2, n_halfcycles, release_t and flag.
Why it exists: `trk.pend` fits from frame 0. On real GAUGE pendulum video the robot holds the pendulum for 1.8-2.6 s before release,
and trk.pend then hits its 6 s bound on some clips: a fake "slow pendulum".
Method: trk.blobs centroid (temporal-median bg) → frames before a sustained >3 px departure are dropped → projection on the principal
motion axis (no metric scale needed) → damped sinusoid c + e^{-βt}(A cos ωt + B sin ωt) (GAUGE eq. 43 form) and zero crossings.
flag = ok needs ≥3 half-cycles, R² > 0.8, |T_fit − T_zc|/T_fit < 5% and ≥90% frames tracked.
Planted: identical to the v5 pendulum estimates (ratio 0.9999-1.0000 on planted-00/07/11/13), so the v5 PASS applies.
Real reference: GAUGE pendulum is released at ~84° (L = 0.2726 m). Over the first ~8 s (a 189-frame Cosmos window) the real period is
1.171 ± 0.003 s (mocap, n=20); 1.06 s (GAUGE's baseline) is the small-amplitude period (whole 130 s record: 1.048 s = 2π√(L/g)).
Real-video check at Cosmos resolution: see work/raj-3/pseudo_cosmos_pend/.

## measure_bounce.py v1 (raj-3): g from the first rebound flight
For Cosmos clips whose first drop is unusable (held ball never released, a spawned ball, a ball starting mid-air, or a drop only ~4 frames long),
g comes from the curvature of the first ballistic flight between bounces (free v0, so it doesn't depend on release).
- Planted: equals v5 within 0.15% on the 4 clips that bounce (4/4 <5%). Composite "bounce g where present, else v5; e,a v5; period pend v1" @ 38db9dd: referee PASS 20/20.
- Real GAUGE drops at Cosmos res (letterboxed 832x480, 539.8 px/m): 9.625 ± 0.047 (SE; sd 0.21; n=19 of 22 ok) vs 9.81. Later, shorter flights read ~15% low, so they are reported (`g_pooled`, `g_per_flight`) but not used.
- `--track_json` takes an external per-frame track (e.g. tools/samball `--track_out`) instead of trk.blobs; `--start N` skips frames before a spawned ball appears.
```
python3 -I measure_bounce.py clip.mp4 --fps 24 --ppm 539.8 --qc qc.png
python3 -I measure_bounce.py clip.mp4 --fps 24 --ppm 539.8 --track_json track.json --start 24
```
flag = ok needs first-flight R² > 0.98 and ≥ 6 frames. Look at the QC: on held/spawned-ball clips the blob tracker can lock onto jitter (flag=weak).
