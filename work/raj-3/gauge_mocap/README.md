# raj-3: g from GAUGE real bouncing-ball mocap with four estimators (review of finding 125, claim c)
Data: HF InternRobotics/GAUGE-Dataset, data/rigid/bouncing ball/json/1..22.json (mocap z in mm, 30 Hz). Dev data, measured only.
Run: `python3 -I mocap_fits.py <json_dir> mocap_fits.json`
Window: argmax(z) .. frame before the first local min of z (the impact frame is excluded).
- g_free_from_argmax: free quadratic over the whole window (raj-2's estimator) -> 8.772 +- 0.016 (SE, n=22)
- g_hinge: z0 - g/2 (t-t0)^2 with free t0 and v0=0 at t0 (measure_ball v4 model) -> 9.363 +- 0.009
- g_free_from_release: free quadratic from the sustained-free-fall onset (first frame after which every 2nd difference is within 25% of the late median) -> 9.742 +- 0.011 (rms residual 0.07-0.49 mm)
- median late 2nd difference: 9.776 +- 0.028
Cause of the low values: for the first ~2 frames after argmax the ball accelerates at only 1.3-4.4 m/s^2 (gripper opening), so it reaches free-fall onset already moving. v0=0 models (hinge, GAUGE's b+kt^2) then read ~5% low even at the best t0.
