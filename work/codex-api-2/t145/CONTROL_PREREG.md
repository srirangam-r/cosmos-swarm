# Task 145: language-control addendum

Added before examining any task-145 output or submitting these controls.
The original R−N contrast can reflect the specific suffix tokens rather than
an abstract rest direction. This addendum retains the original preregistered
transfer and R−N analyses and adds two conditional layer-12 capture arms
for each of the same four T2V scenes and seeds 4–6:

- M: a syntax-matched continuation sentence specifying motion, rather than
  rest, throughout the remainder of the video.
- N2: a similarly sized neutral appearance sentence to compare with N.

The exact suffixes are in `make_controls.py`; all other generation settings
and capture keys match R and N from `make_jobs.py`. Capture steps are 0 and 5,
the only steps already captured for R and N. No new vector is estimated for
steering. The existing QT−F ball vector was trained on different text and
seeds 1–3. Capture results are diagnostic, not a recipe.

For each scene, seed and step, first average latent frames 1–23 separately
for the fixed ball vector and each paired activation difference. Calculate
cosine(ball, R−M) and cosine(ball, N2−N), and their paired difference. Report
each seed/scene/step and scene-level paired means; report seed variability
within scene and scene variation separately. Also report the preregistered
R−N cosines and per-frame cosines. Do not pool 12 scene-seed pairs as 12
independent scenes. Predefine step 0 as the main text-direction comparison,
since matched initial noise has not yet diverged; step 5 is secondary.

Positive differences support alignment relative to this particular neutral
swap, but not a uniquely identified rest concept: the neutral and motion
controls are not perfectly matched in token edit distance, semantics, or
length. Cosine similarities are descriptive unless their null calibration is
supported; null or negative values cannot rule out other rest directions,
layers, steps, prompt formulations, or nonlinear representations. An aligned
vector must still pass the independent steering comparison and native-frame
QC. No planted case validates semantic activation cosines or generic rest.
