# Cause test v4 (task 22): what controls bounce damping on the mid-fall GAUGE ball? (ro-1)
Input: raj-3 dd33 mid-fall frame of GAUGE ball1 (ball already in free fall), 832x480, 93f, 24 fps, 35 steps, cfg 6, shift 10, no neg, seeds 1-2.
Arms (one change vs base F = exact GAUGE prompt, e=0.58): R20 / R95 = stated restitution 0.20 / 0.95; QT = timed ("bounces only twice ...
comes to rest within about one and a half seconds, staying still for the rest of the video"); G1 / G3 = guidance 1 / 3.
Metric (`late_motion.py`, scale-free, NOT planted-validated): mean |frame diff| in the ball corridor x220-360,y130-360, early f2-45 vs late f46-92 and last 20 f.
bclock is unreliable on these clips (locks onto jitter: 2-frame "impacts"), so its JSONs are not used.

| arm | s1 last20 | s2 last20 | eye |
|---|---|---|---|
| F (base) | 3.02 | 3.41 | s1 perpetual bounce; s2 tether yo-yo |
| R20 (e=0.20) | 3.29 | 3.77 | keeps bouncing / yo-yo |
| R95 (e=0.95) | 2.81 | 4.71 | keeps bouncing |
| QT (timed) | **1.16** | **1.22** | 2-3 bounces, at rest by ~f20-45, still to f92 |
| G1 (cfg 1) | 1.44 | 5.42 | s1 ball fades; s2 scene collapse (robot appears) |
| G3 (cfg 3) | 2.38 | 3.03 | s2 gripper intrusion |
Reading: the stated restitution number does nothing, while stated timing/event count makes the ball settle (n=2). v5 (seeds 3-5, plus stillness control QS) is running.
