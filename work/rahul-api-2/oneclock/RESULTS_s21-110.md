# Task 162 close-out: seeds 21-110 (PREREG + Amendments 1-4)

Question: inside one Nano clip, do the fall and the first rebound flight share one curvature? rho1 = a_flight1 / a_fall
(clock-free, scale-free). Real GAUGE same-rig reference: rho1 1.01 / 0.94 / 1.24 / 1.17 (geo 1.08, n=4).

Setup: Cosmos3-Nano I2V, GAUGE ball1 / ball2 first frames ("oc_A" prompt, see jobs*.jsonl), 832x480, 93 f, fps 24, 35 steps,
guidance 6, flow_shift 10 requested (ignored on the board server stack, Karras sigmas, #2870), no negative prompt; as in
PREREG.md. Seeds 21-50 on the q8 queue endpoints; seeds 51-110 on brev-p6k-0/1 (board tools/cosmos_local/server.py stack,
server sidecars in brev/srv_sidecars on rahul-api-2's machine). Same settings otherwise.

## QC (single coder, visual, frozen before any ratio)
- qc_codes.csv (s21-50, frozen b891dfd) and qc_codes_amd3.csv (s51-110, committed in batches c2d23eb ... 5e3a4b0, all
  before score_amd3.json existed).
- Included: 6/180 clips (3.3%, Wilson 95% [1.5%, 7.1%]); 5/90 seeds with >= 1 included clip ([2.4%, 12.4%]).
  - q8 s21-50: 5/60 clips, 4/30 seeds. Brev s51-110: 1/120 clips (oc_A_ball2_s55), 1/60 seeds.
  - The q8-vs-Brev seed yield difference (Fisher p = 0.04) is NOT interpretable as a stack effect: different seed sets,
    coded in different shifts (rule wording sharpened in shift 3), not preregistered, single coder.
- Exclusion reasons (keyword counts over the 174 coder notes, multi-label, approximate): grows / giant / moves toward
  camera 78; no rebound flight (rolls, drifts, perches, hovers, leaves frame) 53; glassy / ghost / faint 49; morph / smear
  47; clone / fragment 39; vanishes 33.

## Scores (score.py Amendment-2 rule; pool.py Amendment 4)
- score_amd3.json: the single included Brev clip (b2s55) is **untracked** (neither tracker valid; median tracker
  disagreement 21 px). Brev contributes 0 seeds.
- pool_s21-110.json, pooled = unchanged from #3782: n = 3 seeds (all ball1: s21 0.61 ff-only, s23 1.39 both, s38 1.63
  both but tracker-divergent t2 1.33 / ff 2.01). Geo-mean 1.113; bootstrap 95% [0.61, 1.63] (descriptive; with n=3 the
  endpoints are the observed extremes); log-t 95% [0.30, 4.14].
- Dropping the tracker-divergent clip (Amd 4 sensitivity): n = 2, geo-mean 0.92, log-t [0.005, 170].

## Conclusion
Inconclusive. With 3 measurable seeds (all one input frame), the data neither show nor exclude a change of curvature
between the fall and the first rebound flight, relative to the real rig (1.08). Extending from 60 to 180 clips did not
help because Nano almost never produces a clean, trackable fall + first flight from these frames at these settings
(3/180 clips measurable). Exploratory, from s21-50: a_fall ranges 2.0-15.3 px/f^2 across seeds from the same frame and
prompt (~6.7x).

Not tested: other first frames, real-photo frames beyond GAUGE, other samplers / step counts, fps settings, a second coder.
