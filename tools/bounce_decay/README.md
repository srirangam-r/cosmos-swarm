# bounce_decay.py: multi-bounce restitution + time-to-rest (rahul, task 36)

`python bounce_decay.py CLIP.mp4 [--diam 0.10 | --mpp M] [--seed x,y] [--rest-at-0] [--fps F] --out res.json`
Needs: numpy, scipy, opencv. Static camera. One ball.

Track: seeded nearest-blob track on a two-pass ghost-free background. Auto-seed takes the highest compact blob in frame 0, because a resting ball's median ghost sits on the floor. Flat blobs (contact shadows) are skipped.
Fit: impacts are y-maxima with prominence >= --min-rise px (default 3). All flights are fitted jointly with a shared curvature (constant g), a robust refit, and contact frames dropped. Flights are added one at a time while each stays consistent (segment rmse <= 1.5 px).
A hold before release is trimmed. Each impact time comes from intersecting adjacent parabolas.
Outputs:
- e_v: per-impact velocity ratio
- e_T: T_{k+1}/T_k, which needs no scale and no depth
- e_T_fit: geometric fit of the flight times, with SE
- e_h: sqrt(h ratio)
- g_joint and g_fall: g_fall uses --rest-at-0
- n_impacts
- still_bouncing_at_end: an impact in the last 15% of the clip
- rest_s
- track_y

Validation
- Planted (referee): `bounce_decay @ sha256:93b57894ffd6` gave 12/12 within 10% (PASS). g <5% on 6/8 and 5-10% on 2/8; e <5% on 4/4. Files: submit1.json, score1.json.
- Own synthetic set `held/` (gen_bounce.py seed 4242, 40 clips, 832x480 @ 24 fps, x264 crf 23). Conditions:
  - A: release at t=0
  - B: hold, then rest at the end (ghost)
  - C: e 0.9-1.0, still bouncing
  - D: ±30% depth drift plus x drift
  - E: small ball, jitter 0.5 px, flicker 3%
- Results (every estimate the tool produced; est/true):
  - e_T_fit: n=30, 1.0006 ± 0.0017, max error 0.5%
  - e_v (first impact): n=33, 1.0002 ± 0.0081, max error 2.8%
  - e_h: n=31, 1.0000 ± 0.0020
  - g_joint: n=33, 0.972 ± 0.015 (the 50%-contrast diameter reads about 3% large)
  - g_fall (A/E): n=10, 0.983 ± 0.028
  - still-bouncing flag: correct on 37/40
- Coverage gaps: no estimate rather than a wrong one. D (depth drift) gets e_v on 4/8 and e_T on 1/8, because the shared-a fit breaks under scale drift. Bounces with < 3 airborne frames are never fitted, so very low e gives the first-impact e_v only. A late-bounce shadow lock can end the track early.
See held_summary.txt and held_results.json.

Not tested yet: real GAUGE ball video (a contact shadow, a real camera), and Cosmos clips.
