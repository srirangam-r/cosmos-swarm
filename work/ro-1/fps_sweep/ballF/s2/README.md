# Seed-2 mid-fall ball-1 clips (task 22), read BY EYE (unvalidated)

Same input/prompt/settings as ballF seed 1 (GAUGE ball1 dd33 mid-fall frame, exact GAUGE prompt, no negative, 832x480, 93 f, 35/6/10, :8021).

## ball_F_ball1_fps24_93f_s2 (fps 24)
- bclock v1 (3cde5a0351a0, seed 287,155): `no_track` -> the template locks on the hallucinated strap/gripper region (qc_s2.png). Not a valid track.
- By eye (crops_0_46.jpg, crops_46_92.jpg): NOT a bounce. A white strap appears from the gripper by f2 and the ball is
  tethered to it: it drops to the plank, then is pulled back up to ~y190 within 2-3 frames, hangs ~3 frames, drops again (yo-yo).
- Plank contacts ~5.5, 13.5, 21, 29, 37, 45, 53, 61, 69, 77, 85, 91 -> 12 contacts, (91-5.5)/11 = 7.8 f/cycle, no decay.
- Seed 1 (true bounces, bclock): 7.84 +- 0.25 f/bounce. Same cycle length, different mechanism.

## ball_E_ball1_fps12_93f_s2 (fps 12), first 46 frames
- Real low bounces near the back of the plank (y ~280-330), constant amplitude, no decay.
- Contacts ~7, 11, 14, 18, 22, 26, 30, 34, 38, 42, 45 -> (45-7)/10 = 3.8 f/bounce = 0.32 s at the conditioned 12 fps
  (fps-24: 7.8 f = 0.33 s). Seed 1 fps12: 4.3 f.
