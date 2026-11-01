# rohith_measure: planted-case measurer (rohith-cc-1)

Third independent tracker, separate from `trk_ballfall` (raj-3) and rahul's tracker, so you can replicate their numbers with different code.

Measures g and e from ball free fall, period_s from a pendulum, and a from a block on an incline.

## Run
```
pip install numpy scipy opencv-python-headless   # tested: numpy 2.5.4, scipy 1.18.1, opencv 5.0.0.93
python measure.py <index.json> <clip_dir> <out.json>
```
`index.json` is the referee's `GET /planted` response: a list of clips with `clip_id`, `params` and `notes`. Object sizes are read from the notes.

## Method
- **Background:** the per-pixel temporal median.
- **Foreground strength:** the Lab distance from the background, smoothed with σ 0.7.
- **Tracking:** the largest blob above threshold 12. Position is a centroid weighted by the foreground strength, saturated at the body level so specular highlights don't pull it. Frames where the blob touches the image edge are dropped.
- **Scale:** measured on frame 0, where the object is at rest and not blurred. It's the median of 12 chords through the centroid, taken at half the body contrast with sub-pixel crossings.
- **Ball:**
  - **g:** a quadratic fit up to the first impact (the first local maximum of y). Since v4, trailing points with residual over max(0.5 px, 4×median) are dropped; these come from the ball merging with the floor or its shadow just before contact.
  - **e:** −v_out/v_in at the intersection of the pre- and post-impact parabolas, both with the same curvature.
- **Pendulum:** a damped-cosine fit, with the period bounded near the zero-crossing estimate.
- **Incline:** 1-D position along the main direction of motion, fitted with v0 ≈ 0.

## Validation
- `planted_estimates_v4.json` holds the estimates submitted to the referee, with per-clip debug fields such as fit residual, px/m and v0.
- The referee's result is posted in #findings.
- Limits: static camera only, uncluttered background, one moving object. It hasn't been tested on Cosmos output or real photos.
