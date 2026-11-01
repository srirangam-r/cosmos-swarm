# Task 36: real-clip fit coverage diagnostic

This is a diagnostic of the existing tool, not a restitution or model-physics
estimate. The referee PASS is for planted first-impact restitution and gravity,
not multi-flight fits on real footage. See board findings #596, #600, #1042,
and #2960.

## Inputs and method

The four `real*_bounce_decay.json` files are the unchanged outputs of
`tools/bounce_decay/bounce_decay.py` at SHA-256
`93b57894ffd6f7c988957da8186f973fe5e4988d828425c719fc19938af9cea0`
on the four `work/agy-4/task72_score_review/real_control_clips/real_ball_*_f0_93f.mp4`
clips. They were run with `--fps 25 --mpp 0.001852538 --seed 280,116` and the
tool's default detection and fitting settings. Each rejects both-flight fits
at the 1.5 px per-segment threshold, so no `e_T_fit` is available.

`compare_fit.py` reconstructs the tool's first two candidate segments from its
peaks and **rounded** `track_y`. It compares ordinary least-squares fits with
a shared quadratic curvature (five parameters) against separate curvatures
(six parameters). This diagnostic does not reproduce the tool's robust
outlier-refitting; it uses the same points for both arms. Leave-one-frame-out
(LOO) error is calculated analytically from regression leverage. The fits are
exploratory, and no estimate from them was submitted to the referee. The
remaining time-series points are correlated, so LOO is not an independent
clip-level evaluation.

The `drop_adjacent` arms 1 and 2 additionally remove the nearest one or two
frames on each side of each detected impact bounding the two segments. This is
a sensitivity check with fewer and different observations, not a comparison on
held-out frames and not evidence that those frames are incorrect.

## Results

| Real clip | Shared / separate training RMSE, px | Shared / separate LOO RMSE, px | Shared training RMSE after 2-frame trim, px |
| --- | --- | --- | --- |
| 1 | 3.989 / 3.692 | 6.231 / 6.386 | 2.101 |
| 2 | 4.373 / 3.987 | 6.292 / 6.426 | 1.961 |
| 3 | 3.476 / 3.401 | 4.445 / 4.813 | 3.155 |
| 4 | 3.815 / 3.647 | 5.202 / 5.460 | 2.131 |

On these four same-rig clips, the free-curvature model has lower training RMSE
by construction, but higher LOO error in all four. The mean paired difference
(free minus shared) in LOO RMSE is +0.229 ± 0.054 px (sample SE, n=4); this
is descriptive, not a population-level uncertainty interval. Simply freeing the
curvatures does not solve this particular residual problem. Removing nearby
observations reduces the shared fit's *in-sample* RMSE, but it stays above
1.5 px here and the observed reduction may just reflect omitting hard points.
It does not establish contact bias, depth drift, or a fix.

`real1_native_qc.jpg` shows native-resolution crops for frames 29–64 of ball 1,
with the estimator's tracked y as a red horizontal line; several moving frames
are visibly blurred. The sheet is visual context, not a hand-labeled accuracy
test. We have not determined which of tracking bias, motion blur, nonuniform
timing, camera geometry, contact, or model mismatch drives the residuals.
The reported `n_impacts=0` means no impacts were successfully *fitted*; it
must not be interpreted as no actual impacts.

## Reproduce

From the shared repository root, with Python, NumPy, OpenCV and SciPy installed:

```bash
for ball in 1 2 3 4; do
  python3 tools/bounce_decay/bounce_decay.py \
    "work/agy-4/task72_score_review/real_control_clips/real_ball_${ball}_f0_93f.mp4" \
    --fps 25 --mpp 0.001852538 --seed 280,116 \
    --out "work/codex-api-3/task36/real${ball}_bounce_decay.json"
done
python3 work/codex-api-3/task36/compare_fit.py > work/codex-api-3/task36/real_fit_diagnostics.json
python3 work/codex-api-3/task36/inspect_real.py \
  work/agy-4/task72_score_review/real_control_clips/real_ball_1_f0_93f.mp4 \
  work/codex-api-3/task36/real1_bounce_decay.json \
  --out work/codex-api-3/task36/real1_native_qc.jpg
```

Next: independently label ball centers and impact windows on real clips; compare
with the track, and validate any revised method on multi-bounce simulations and
the referee before interpreting restitution. Do not relax the 1.5 px threshold
or swap fitters and treat the resulting number as validated.

## Frame-center audit (shift 3)

An exploratory visual audit identifies a plausible source of some, but not
necessarily all, of the above fit errors. `center_annotations.csv` contains
16 approximate center-y estimates from four same-rig real clips (four selected
near-apex frames per clip, two ascending and two descending). These were read
by one annotator from frame crops with no tracker overlay
(`blind_centers_sheet.py`); the annotator had previously examined tracked
frames, so this is **not a blinded study**. The estimated centers are rough,
and near-apex frames were selected after reviewing the footage. Frame numbers
and phase labels are in the CSV; phase refers to the apparent path before and
after the first rebound's apex, not to the first fall.

As a second image-based check, `hough_centers.py` detects exactly one circle
in a fixed 75×80-pixel ROI for each of those same selected frames, without
using the tracker or manual center coordinates. The fixed detection settings
were selected during this exploratory audit. `hough_tracker_overlay.png`
shows the detected outline in green and the original tracked y in red; it is
not evidence on blurred contact frames or other scenes. The Hough and manual
center estimates differ by 1.56 px mean absolute (maximum 4.5 px) on these
selected 16 frames. Neither method is planted-validated or establishes true
instantaneous physical position during motion blur.

For each clip, the difference between mean (tracker minus Hough) on the two
ascending frames and the same mean on the two descending frames is +7.31,
+13.08, +0.95, and +6.93 px. The four-clip mean is +7.07 ± 2.48 px (sample
SE), but this descriptive SE excludes annotation/method uncertainty, and the
clips share one setup; the frame/phase choice was exploratory. The prior
1.5 px per-segment rejection is thus not simply evidence of different
parabolic curvatures: the measured image-centroid mismatch is large on several
clearer frames as well. The result does not establish which component of the
tracker causes the shift.

As a sensitivity exercise, `center_substitution.py` replaces only those four
tracked y values in each clip with the Hough values and runs the original
ordinary shared-curvature diagnostic on the same segment indices. Overall
in-sample RMSE changes from 3.99/4.37/3.48/3.82 to 3.74/3.39/2.59/2.61 px,
respectively (mean change −0.83 px). This changes observations on a
hand-selected subset and is **not** an out-of-sample control, a validated
tracker, or a restitution measurement. All fits remain above the original
per-segment 1.5 px threshold even under this partial substitution. The full
tool uses robust fitting, unlike this sensitivity check. Contact centers and
other frames were not corrected; a clean new tracker must be tested on
held-out synthetic multi-bounce clips and the referee before use.

Reproduce from the repository root (Python, NumPy, SciPy, OpenCV 4.13.0):

```bash
for ball in 1 2 3 4; do
  python3 work/codex-api-3/task36/blind_centers_sheet.py \
    "work/agy-4/task72_score_review/real_control_clips/real_ball_${ball}_f0_93f.mp4" \
    --out "work/codex-api-3/task36/real${ball}_blind.png"
done
python3 work/codex-api-3/task36/compare_centers.py > work/codex-api-3/task36/center_comparison.json
python3 work/codex-api-3/task36/hough_centers.py > work/codex-api-3/task36/hough_comparison.json
python3 work/codex-api-3/task36/center_substitution.py > work/codex-api-3/task36/center_substitution.json
```
