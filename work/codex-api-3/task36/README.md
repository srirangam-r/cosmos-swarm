# Task 36: real-clip fit coverage diagnostic

## Mocap-only rebound sensitivity (shift 6)

`mocap_rebounds.py` fits the first two full rebound flights in the separate
30 fps GAUGE position JSONs, without using the video track or a camera–mocap
clock alignment. It estimates the plane as the median of the last ten height
samples, excludes the three detected local-minimum samples, fits one quadratic
per flight, and divides the second flight's two-root interval by the first's.
This is a time-ratio diagnostic for the second impact, not first-impact e.

For the four same-rig files `1.json`–`4.json`, the ratios are 0.70483,
0.70640, 0.71052, and 0.70615; their mean is 0.70698 ± 0.00123 (sample SE).
Deleting one more sample next to each contact gives mean 0.70563; the largest
individual change is 0.00758. Offsetting the inferred resting plane ±5 mm
changes the mean to 0.71526 or 0.69819. This sensitivity is not a confidence
interval: the sensor's preprocessing, calibration, plane uncertainty, contact
dynamics and dependence among clips remain unknown. Discrete impact-index
ratios are 0.69231, 0.75, 0.75, 0.69231; their one-frame quantization is large.

The script checks 2,000 idealized numerical 30 fps bouncing trajectories per
noise level, generated with seed 881122. Independent white position noise of
0, 0.5 and 2 mm yields 2,000/2,000 returned ratios, with absolute-error 95th
percentiles near 0, 0.00504 and 0.02058, respectively. This is **not** a video
tracker, codec, correlated-error, mocap-instrument, or planted-case validation.
Therefore the real values are provisional diagnostic reference estimates, not
a validated restitution finding or evidence of Nano's behavior.

Download the four publicly released GAUGE dev JSON files under
`data/rigid/bouncing ball/json/{1,2,3,4}.json` into `mocap/`, then run:

```bash
python3 work/codex-api-3/task36/mocap_rebounds.py > work/codex-api-3/task36/mocap_rebounds.json
python3 -m unittest discover -s work/codex-api-3/task36 -p 'test_mocap_rebounds.py' -v
```

The intended source is `InternRobotics/GAUGE-Dataset` on Hugging Face. The
script never uses later frames for any recipe; these are evaluation inputs.

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

## Contact-free residual and fixed-segment noise audit (shift 4)

This diagnostic is not a new tracker, restitution estimate, or planted-case
validation. Starting from `compare_fit.py`'s existing detected first-two-flight
segments, remove the two frames nearest each detected impact: remove the last
two frames of the first segment and the first and last two from the second.
Fit each segment independently with three free quadratic coefficients. The
first-flight training RMSE values are 1.146, 1.681, 1.702, and 1.754 px;
second-flight values are 2.283, 0.869, 1.420, and 2.552 px. Each segment has
only 5–7 frames and three fitted coefficients, so its in-sample RMSE is
downward-biased; these numbers are not unbiased estimates of tracker error.
Impact trimming does not remove the initial gripper-release transition.

`noise_floor_audit.py` also draws 30,000 independent Gaussian noise vectors
per clip from a fixed RNG seed and projects them onto the residual subspace
of the *untrimmed*, fixed observed two-flight shared-quadratic design. At
assumed per-frame standard deviation 1.0 px, at least one segment exceeds
1.5 px in 0.65–0.80% of simulations; at 2.3 px, it does so in 93.5–94.0%.
Monte Carlo SE is at most 0.15 percentage points at 2.3 px. This tests only
the ordinary-least-squares residual gate conditional on chosen segment frames:
it does not simulate ball images, peak detection, robust refitting, correlated
tracker errors, or the original tool's end-to-end rejection rate.

The Gaussian model explains a high hypothetical rejection rate, but **not
the magnitude** of the observed untrimmed OLS residuals: maximum per-segment
observed RMSE is 4.586, 5.552, 3.940, and 4.698 px. At sigma=2.3 px, 0, 0,
10, and 0 out of 30,000 draws respectively reach those maxima. These are
conditional, exploratory model-tail comparisons, not calibrated p-values:
segments were selected from the same tracks and the four clips share one rig.
Systematic/heteroscedastic tracking errors, contacts, selection, and imperfect
flight models remain possible. This does not identify their causes or justify
loosening the original threshold.

```bash
OPENBLAS_NUM_THREADS=1 python3 work/codex-api-3/task36/noise_floor_audit.py > work/codex-api-3/task36/noise_floor_audit.json
OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s work/codex-api-3/task36 -p 'test_noise_floor_audit.py'
```

## Mocap alignment sensitivity (shift 5)

This is an exploratory measurement diagnostic, **not** a planted-validated
tracker or a gravity/restitution estimate. The corresponding real GAUGE dev
mocap samples are at `InternRobotics/GAUGE-Dataset`, under
`data/rigid/bouncing ball/json/1.json` through `4.json`. They are 30 Hz, in mm;
the shared video tracks are 25 fps. The mocap files begin at the release and
the videos include a hold, so their origin offset is not known independently.

`mocap_alignment.py` linearly interpolates mocap height and fits its clock
offset, projected scale and intercept to the first two track segments. A
0.025-frame grid spans ±2 frames around the difference between the first
detected video peak and the first sampled mocap minimum (SciPy `find_peaks`,
prominence 10 mm and distance three mocap samples). Scale is constrained to
[-0.75, -0.35] px/mm. The four pre-existing hand-annotated frames per clip,
the two peak frames and the nearest frame on either side of the first two
peaks are excluded from the training fit; the peak locations still influence
the offset search and the segment selection. The annotations were selected
after reviewing footage, by an annotator who had previously seen the tracks.

At the fitted offsets, absolute error versus the projected mocap is lower for
the manual centers by 1.20, 10.29, 5.72 and 6.79 px per clip, respectively
(mean tracker-minus-manual MAE +6.00 ± 1.87 px, sample SE, four same-rig clips
and four selected frames per clip). But this depends on synchronization: on
the common training-frame subset valid for all offset perturbations, the
baseline differences are +1.19, +10.31, +5.71 and +6.81 px (mean +6.00 ± 1.88).
Increasing
each fitted offset by 0.5 video frames and refitting intercept and scale gives
per-clip differences of -4.21, -1.47, +0.87 and -1.67 px (mean -1.62 ± 1.04).
The common-subset fit RMSE at the original versus shifted offsets is 5.30/10.83,
7.65/7.23, 3.46/10.66, 5.77/6.70 px, respectively. The perturbation is a
sensitivity analysis, not a calibrated timing confidence interval. Clock and
camera projection error, mocap interpolation, and selected frames are all
confounded with tracking error. Consequently the apparent benefit at the
fitted offsets is **not** independent confirmation of tracker bias; an
independently synchronized clock or more accurate ground-truth image centers
are needed. No changed fitter or physical claim follows.

```bash
mkdir -p work/codex-api-3/task36/mocap
for ball in 1 2 3 4; do
  curl -fsSL "https://huggingface.co/datasets/InternRobotics/GAUGE-Dataset/resolve/main/data/rigid/bouncing%20ball/json/${ball}.json" \
    -o "work/codex-api-3/task36/mocap/${ball}.json"
done
python3 work/codex-api-3/task36/mocap_alignment.py > work/codex-api-3/task36/mocap_alignment.json
python3 -m unittest discover -s work/codex-api-3/task36 -p 'test_mocap_alignment.py'
```
