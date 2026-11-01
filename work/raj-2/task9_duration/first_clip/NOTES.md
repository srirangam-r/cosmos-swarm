# First duration-sweep clip: raj2_dur_ball1_nf61_s1 (61 frames, 24 fps, stated 2.5 s, GAUGE flat prompt, no neg, seed 1)
Eyeballed ball centre y (px, 832x480 letterbox; ticks in fall.jpg are full-frame y):
f2-f4 in gripper ~120 | f5 160 | f6 195 | f7 225 | f8 255 | f9 280 | f10 320 | f11 ~340 contact with plank.
Drop ~220 px = 0.41 m at 539.8 px/m (real mocap drop 0.41 m) in ~7 frames = 0.29 s (real free fall from 0.41 m: 0.29 s) -> implied g ≈ 2h/t² ≈ 9.7 m/s².
The profile looks closer to constant velocity (~30 px/frame) than to a parabola, so the fall *time* is right but the shape is unclear at this precision.
After impact the clip turns unphysical: the ball rebounds high and grows (perspective/size drift), the plank tilts up (f20-f36), the gripper reappears and the ball is back in the gripper by f44 (scene reset), static until f60.
Both automatic trackers fail: measure_ball v5 flag=no_free_fall (it tracks the block/gripper); realball g=1.52 from 4 points (wrong segment). Need a fall-time / ROI-constrained measure for Cosmos clips.
UNVALIDATED, n=1, eyeballed. Compare with GAUGE 189 frames: g=0.45 -> fall time ~1.35 s from 0.41 m.
