# Identity-aware ball tracker on poornima-1's #1958 clips: FAILED QC (negative, not a finding)
Goal (scout-1 #2135): per-clip ball speed / bounce-height decay instead of fixed-ROI pixel energy (rog-cc #2126).
Method tried: static camera, fg = dark pixels (gray<70) differing >28 from the per-clip median background, nearest-blob
tracking gated by distance and area ratio, seeded at frame 0 with the largest dark fg blob in the upper image.
Overlay QC (ov1.jpg: b1pre_i2v_s1, b1pre_v2v9_s1, b1post_i2v_s2, every 6th frame): the seed lands on the robot's dark links
or the curtain, not the ball; the small ball in the post-cut clips is never locked; in b1pre_v2v9_s1 the track jumps to
the gripper shadow at f42-48. Track counts ("found" 10-93 of 93 frames) say nothing about identity.
Conclusion: background-subtraction + dark threshold cannot track a black ball over a black curtain / dark table with a moving
arm. A usable readout needs a seeded tracker (SAM2/CoTracker3 from a hand-given ball mask, as in RigidBench) or manual seeds.
No numbers from this code should be used. Not planted-validated.
