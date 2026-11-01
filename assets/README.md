# Canonical Assets for Cosmos3-Nano Recipe

This directory contains canonical reference input images and demonstration video clips for running and verifying **Charter Deliverable 1**:
"The Improved Cosmos3-Nano Recipe: Dynamic Mid-Event Conditioning (Release-Seam Protocol)".

## Files

1. `gauge_ball1_midfall.png`:
   - Canonical 832x480 mid-fall conditioning frame for GAUGE Ball 1 (dedup frame 33 / time-point $t \approx 1.38\text{ s}$).
   - The ball has physically separated from the Franka mechanical gripper and is in active downward gravitational descent.
   - Provenance: `work/raj-3/midfall/inputs/gauge_ball1_dd33_832x480.png`.

2. `gauge_ball2_midfall.png`:
   - Canonical 832x480 mid-fall conditioning frame for GAUGE Ball 2 (dedup frame 35 / time-point $t \approx 1.46\text{ s}$).
   - Provenance: `work/raj-3/midfall/inputs/gauge_ball2_dd35_832x480.png`.

3. `gauge_ball1_f0.png`:
   - Official baseline initial frame for GAUGE Ball 1 (frame 0).
   - Shows the stationary ball clamped firmly within the Franka gripper jaws ($y \approx 119\text{ px}$).
   - Used for the stock baseline comparison demonstrating the static-grasping deadlock artifact.
   - Provenance: `work/raj-1/gauge_ball/gauge_ball1_f0_832x480.png`.

4. `gauge_ball1_raw.mp4`:
   - 48-frame sample clip at 24 fps (832x480) for testing automatic release-seam detection (`--detect-release`).
   - Provenance: Initial 48 frames of `work/raj-1/gauge_ball/gauge_ball1_noneg_s1.mp4`.
