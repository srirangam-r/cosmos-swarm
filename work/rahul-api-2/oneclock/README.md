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
