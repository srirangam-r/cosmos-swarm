# Task 219 protocol

Scope and primary rules were posted to board task 219 as messages **4450**
and **4455**, before `audit.py` was run. Existing findings and aggregate
results were already known; this is a same-data review, not a blind test.

- Keep #4312's six gate-PASS pend10 clips unchanged. Independently integrate
  `theta'' = -sin(theta)`, measure the first downward zero crossing, and use
  `F(A) = 2 * crossing_time / pi` to recompute the published correction.
- Report log-t intervals on these six distinct seeds. Independently regroup
  #4313's broader set by seed and reproduce its corrected arithmetic means.
- Use task 198's previously frozen native-Y intersection (s23/s24), including
  its independent planted-PASS periods; no new visual coding or selection.
- Independent angle sensitivity: interpolate the existing valid angle samples
  at 24 fps; median filter width 5; `find_peaks` of angle and negative angle,
  prominence 10 degrees, minimum distance `floor(0.3*T*24)` samples. Reject
  incomplete endpoint cycles and require at least two successive extrema pairs.
  Take median opposite-extrema half-range. Widths 1 and 3 are fixed sensitivities.
  Consecutive same-sign extrema retain the more extreme value. This method has
  no planted amplitude validation.
- Explicitly audit common-camera projection, equilibrium, damping, missing
  extrema, physical versus image length, and the G3 median gate.
- Addition 4455: set real `F=1` for a deliberately generous sensitivity. Under
  a planar, image-vertical, orthographic model with a complete measured angle
  envelope, also use `max(90 degrees, measured absolute peak)` as an upper cap
  on true excursion. This is a conditional model calculation, not a certified
  physical bound on the videos.

No generation, new seeds, training, referee submissions, or NVIDIA scores.
