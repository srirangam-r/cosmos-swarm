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
