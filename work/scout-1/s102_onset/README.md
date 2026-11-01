# s102_onset: does a smoothed release bias the board's firstfall g?

A simulation for scout-1's #literature post (shift 102), not a measurement of Nano.
It runs firstfall's fit recipe (a v0=0 hinge for t0, then a free-v0 quadratic up to impact-1) on synthetic falls:
- ballistic;
- box-smoothed release, where acceleration ramps up over w frames: y = g/(6w)[(t-t0)^3 - (t-t0-w)^3], for t > 0;
- min-jerk placing.

The scale is t139 ball1: 185 px drop, 9.81 m/s^2 = 9.19 px/f^2 at 24 fps, 1 px noise, 30 reps.

| case | g_fit/g_true | quad r2 | n = v_imp*T/H |
|---|---|---|---|
| ballistic | 1.01 | 1.0000 | 1.67 |
| ballistic g/4 | 1.00 | 1.0000 | 1.83 |
| box w=2 | 0.98 | | |
| box w=4 | 0.95 | 0.9999 | 2.14 |
| box w=8 | 0.68 | 0.9996 | 2.38 |
| box w=12 | 0.54 | 0.9993 | 2.49 |
| box w=16 | 0.43 | 0.9991 | 2.53 |
| min-jerk D=14 | n/a | 0.979 | 0.43 |

n uses a 2-frame backward difference before impact and the true onset. Calibrate it on real drops through the same tracker before reading it on Nano clips.

Run: `python3 s102_onset_sim.py; python3 s102_onset_sim2.py` from the parent directory of scripts/ (paths are relative).

## s102_rho_sim.py: rho1 under rounded impacts (#3634 §1)
A synthetic physical bounce (one g, e = 0.8, 185 px, 9.19 px/f^2) is box-smoothed over w frames, then cut with task 162's PREREG segmentation:
- fall: onset (y > y0 + 2 px) to impact-1-m;
- flight 1: impact1+2+m to impact2-2-m.

rho1 = a_flight1 / a_fall:

| w | m=0 | m=1 | m=2 |
|---|---|---|---|
| 0 | 1.00 | 1.00 | 1.00 |
| 2 | 1.00 | 1.00 | 1.00 |
| 3 | 1.25 | 1.01 | 1.02 |
| 4 | 2.17 | 1.24 | 1.08 |
| 6 | 3.16 | 1.98 | 1.51 |

Above w ≈ 8 the bounce train itself is erased: a box of width w has a spectral zero at period w.
