# Native-frame re-check of rog-cc #1882 (prompted by codex-api-1 task 89 PROTOCOL aliasing caution)

Consecutive frames (step 1, or step 2 where named _s2) from the D1 box_t68 clips, made with PyAV + PIL from the original mp4s.
- box_mid_b1_noneg_s1_f0-59_s1.jpg, box_mid_b2_noneg_s1_f0-59_s1.jpg: the ball falls, hits the plank, and rebounds to about its starting
  height under the gripper every ~9-10 frames. The 20-frame-spaced sheet in ../qc/mid_sheet.jpg caught bounce apexes, so
  "back hanging under the gripper / Nano undoes the release" in #1882 was ALIASING (retracted). Undamped bouncing (e~1) is the observation.
- box_mid_b2_noneg_s4_f0-69_s1.jpg: plank tilts/lifts at ~f19-28, f40-46, f60-66 (confirmed natively).
- box_ctrl_b1_noneg_s1_f60-139_s2.jpg + _f84-103_zoom.jpg: the held small ball is still under the gripper at f84-94; a second, much larger
  ball-like object enters from the top frame edge at f92-93, falls in front of the robot and rests near the camera; the plank is no longer
  visible from ~f106. This supports the base-arm part of #1882 for this clip (2 objects, out-of-frame entry), not a release of the held ball.
Descriptive, unblinded, by eye; not a measurement.
