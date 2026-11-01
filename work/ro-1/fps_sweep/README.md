# ro-1 task 22: does the conditioned fps change Nano's motion speed?

Endpoint: puget GPU 1, `server.py` (the GB10 copy of raj-1's tools/cosmos_local, model fully on GPU), torch 2.14.1+cu130, diffusers @86ef420.
Input: GAUGE official `input/first frames/832x480/pendulum/frame.png` plus the exact `prompt.txt`, no negative prompt, 35/6/10.
Arms (93 f): A = fps 24 (3.9 s stated), B = fps 12 (7.75 s stated); seeds 1-2. Ball arms E/F use raj-3's mid-fall frames at fps 12/24.
This complements ro-3's task 25 (fps 12/24/48 at 189 f), so 189 f arms were dropped here to avoid duplication.
Measurement: tools/trk_ballfall/measure_pend v1 (referee PASS) at the conditioned fps; measure_bounce v1 for balls.

## Seed 1 (provisional, n=1 per arm, both flag=check)
| arm | fps | period_s (CI95) | period_frames | R2 | half-cycles |
|---|---|---|---|---|---|
| A | 24 | 2.087 (2.02-2.16) | 50.1 | 0.95 | 2 |
| B | 12 | 2.535 (2.44-2.64) | 30.4 | 0.74 | 5 |
Real: small-angle 1.04 s (msgs 211/219). Halving the fps cut the period in frames 50 → 30 (if the period in seconds were fixed, it would be 25). In stated seconds the period stays ~2-2.5x real.
