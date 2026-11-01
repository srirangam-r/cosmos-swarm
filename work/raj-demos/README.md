# Two slide demos: original vs improved Cosmos3-Nano (task #281, Raj via Claude)

Both are labelled **demo, provisional**. MP4 (H.264, 24 fps, ~3.9 s) and looping GIF of each. Also served at
http://board.tail0c526a.ts.net:8031/demos/ .

## 1. `pendulum_physics_start`: real | original Nano | Nano + physics start
Same first frame (GAUGE recording 10, frame 93, E6 `f0_10.png`), same seed (1), same prompt (E6 `pend_base.txt`).
- **Physics start** = ro-3's #5315 recipe (task 252): a crude simulated pendulum built from frame 0 (`make_simproxy_left.py`,
  ro-3's `make_simproxy.py` with the swing direction flipped to match this recording, amplitude 85°, period 1.216 s = the
  real recording's measured period), VAE-encoded and noised to sigma 0.898 (`latent`: ref + init 'noised' + start_step 19 of
  35), then Nano denoises from there. Nano renders the simulated motion. It doesn't discover the physics itself.
- Periods (`xcheck.json`, dk2's frozen two-tool check d56e3c7; seconds at 24 fps):

| clip | pend_acf | measure_pend (r2) | flicker |
|---|---|---|---|
| real_10 | 1.216 ok | 1.228 ok (0.97) | |
| original Nano, seed 1 (E6 B_rec10_s1) | 0.929 check | 0.863 check (0.76) | 0.070 |
| original Nano, seeds 2/3 | 1.214 / 1.118 check | 2.058 / 0.956 check (0.34 / 0.30) | |
| **physics start, seed 1** | **1.213 ok** | **1.217 ok (0.96)** | 0.011 |
| **physics start, seed 2** | **1.213 ok** | **1.215 ok (0.97)** | 0.014 |
| physics start at sigma 0.97 (step 12), seeds 1/2 | 1.573 / 1.107 | 1.521 / 1.150 | 0.007 |

  At noise level 0.9 the clock holds on both seeds. At 0.97 Nano drifts away from the proxy, so the strength matters.
  By eye: the original's rod turns into a long white stick and drifts out of phase with the real swing; the physics-start
  clip stays in step with the real one.

## 2. `ball_settle`: original prompt | + timed-settle sentence
ro-1's task 22 / #2720 (`work/ro-1/cause_v7`, the matched seed-3 pair), unchanged clips. Over 6 clips per arm (eye-coded, unblinded):
original prompt 0/6 settle and 4/6 gross artifacts (duplicate ball, giant sphere, phantom box); with the sentence "bounces
only twice with rapidly diminishing heights, and comes to rest on the plank within about one and a half seconds" 5/6 settle
and 0/6 artifacts. DOVER quality unchanged (-0.004). This is a prompt fix, not a sampler fix.

`compose.py` builds the side-by-sides; `gen.py` made the physics-start clips on raj-q8.
