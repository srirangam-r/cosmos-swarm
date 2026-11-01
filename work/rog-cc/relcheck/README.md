# Release continuity check on held-ball frame 0, 93 f, no negative prompt (rog-cc, review of raj-api-2 #3260)
Clips: task-31 negmeta arm inv_empty (rog2 jobs, work/rog2/negmeta_arm), GAUGE ball1/ball2 frame 0, exact GAUGE prompt,
832x480, 93 f @ 24 fps, 35 steps, CFG 6, empty negative, seeds 1-2, GB10 diffusers (sidecars in rog-cc local clips/negmeta).
inv_empty_f0_26.jpg: frames 0-26 every 2nd frame, crop x130-450 y20-420. Rows: ball1_s1, ball2_s1, ball1_s2, ball2_s2.
Made with `python3 strip.py out.jpg <clips...>`. One unblinded coder (rog-cc); not planted-validated.
Codes (continuous fall = the ball is seen leaving the jaws and at intermediate heights on >=2 sampled frames):
- ball1_s1: ball gone from jaws, nothing in mid-air f2-20, a LARGER ball appears just above the plank at f22. Not continuous.
- ball2_s1: ball appears near the plank already at f6-8 (larger than in the jaws), then bounces f10-16. Not continuous.
- ball1_s2: a small ball is on the plank by f6 while the arm swings down and smashes the plank (f14-26). Not continuous.
- ball2_s2: same as ball1_s2 (ball on the plank by f6, arm slams down, plank flips). Not continuous.
Lenient code "a ball is off the gripper / on the plank at f92": 4/4. Strict continuous fall: 0/4.
