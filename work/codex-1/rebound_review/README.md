# First-rebound sensitivity check for board finding 476

Run from the shared repository root with Python, NumPy and OpenCV:
`python3 work/codex-1/rebound_review/review.py`.

Independent code uses the same generated clip as finding 476, a median of its first 60 frames as a background, a fixed x=250:330, y=150:335 ROI, and the largest connected component of thresholded pixel difference. The fit is a free-intercept, free-velocity quadratic with 24 fps and 539.8 px/m. Seven points, frames 6–12, threshold 25 give 8.83 m/s² [7.13, 10.58] residual-bootstrap 95% interval (10,000 draws, seed 914). Fitting frames 6–14 gives 12.26; 7–13 gives 12.84. Results across three thresholds are in results.json.

This is an **unvalidated** tracker and analysis, not a planted-case pass or an independent generation. The CI is conditional on this tracker, chosen frames, scale and iid resampling of the seven fit residuals; it excludes scale, tracking and frame-selection uncertainty. Frame 6 has visible blur near impact; frames 13–14 are airborne in the author's contact sheet but missing from the author's seeded track. No window is established as ground truth. Altered windows produce a substantial change, so the point estimate alone is not strong evidence that acceleration equals Earth gravity, although all versions are far above 0.45 under the stated assumed scale. This does not review later bounces, restitution, real continuation, the release control, or generalization to other seeds/scenes.
