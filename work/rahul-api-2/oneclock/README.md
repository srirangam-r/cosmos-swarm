# oneclock (rahul-api-2, task 162): fall vs rebound-flight curvature inside one clip

See PREREG.md (committed b51f4a5 before any clip). `oneclock.py` = firstfall.track (planted PASS tracker) over the whole
clip, impacts = y maxima with prominence >= 8 px, per-segment free quadratic, rho1 = a_flight1 / a_fall (clock- and scale-free; physics 1).

Status (shift 1, 11:10 UTC):
- Synthetic known-rho clips (`synth.py`, 6 cases, rho 0.5/1/2, e 0.6-0.9, hold 0-10 f): rho1 recovered within 0.6% on 5/5 cases
  that have a complete first flight (synth_res_v1.json, synth_truth.json). syn3 has no second impact inside 93 f -> correctly no rho1.
- Real GAUGE control (agy-4 real_ball_1..4_f0_93f, 25 fps): FAILS. The colour-gated tracker loses the motion-blurred real ball
  during the fall and latches onto a static object near y~312 (real_res_v1_trackerfail.json). Needs a blur-tolerant
  (change-only near prediction) tracker before any rho on Nano clips is trusted. NOT validated on planted yet.
- Nano clips: 20 queued (owner rahul-api-2, oc_A_{ball1,ball2}_s21-30, q8).

## Update (shift 1, later)
- `track2.py`: blur-tolerant tracker (change vs per-pixel median background, prediction-gated, |diff|-weighted centroid). `--tracker t2`.
  - Synthetic: rho1 within 0.3% on 5/5 (synth_res_t2.json).
  - **Real GAUGE drops (agy-4 real_ball_1..4, 25 fps): rho1 = 1.118, 1.118, 1.106, 1.121 -> 1.116 ± 0.004 (SE, n=4 same-rig).**
    Not 1.00: ~+12% systematic (fall reads g_eq ~9.2, flight ~10.3 m/s² at 539.8 px/m; mocap 9.65-9.84). This is the
    same-scene/same-camera reference for Nano, not proof the tool is unbiased.
- Nano, first 4 clips (ball1 s21-24). QC codes frozen in qc_codes.csv BEFORE ratios: include s21, s23; exclude s22 (rolls, no flight), s24 (ghost/depth jump in flight 1).
  - s23: rho1 1.36 ± 0.09 (t2) / 1.41 ± 0.20 (ff). Fall g_eq 2.7, flight-1 g_eq 3.6 m/s².
  - s21: fall NOT a parabola (2nd differences 9 -> 50 px/f² over 5 frames), rho1 0.35 (t2) / 0.61 (ff), flight-1 a = 8.6 px/f² (g_eq 9.2).
  - excluded s24 for reference: rho1 2.8 / 2.1.
  - PROVISIONAL, n=2 included. Do not cite.
- Planted (planted_est_v1.json): NOT submitted. rho1 = 1.000/1.000/1.001 on 3 rendered bounce clips (06, 08, 15) but
  planted-14's rebound is not tracked (stuck on a static blob) and fall-only planted-03 gives g < 0. Fix before submitting.
