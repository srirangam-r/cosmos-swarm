# Phantom-ball diameter (scout-1 #2519, test 1), rog1

Clips: work/rog1/condnoise (base + condition-noise arms, GAUGE ball1 frame 0, 832x480, seeds 1-3).
phantom_size.py: dark-new-blob detector (dark at t, bright at f0, round). It has many false positives where the gripper or arm
is erased (that region turns dark), so every number below was checked by eye on qc_all.jpg and big_fullframe.jpg.
Eye-confirmed invented balls (native px, equivalent diameter):
- s005t_s1: ~34 (f8-9, on the plank)
- s010t_s3: ~60 (f40, on the plank)
- s005t_s3: ~62 (f15-57, on the plank)
- base_s1: ~78 (f8, at the gripper; partly occluded)
- s005t_s2: ~140 (f21-24 at the gripper; the detector box covers only the part over the white arm)
Real ball in frame 0: ~19 px (eye, x4 crop real_vs_phantom_s005t_s1_x4.jpg).
The other detections (base_s2/s3, s010t_s2, s015t_*, s03*, s06*) are scene-change false positives. They aren't used.
