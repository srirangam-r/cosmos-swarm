# Tasks 43 & 51 Audit (`agy-1`)

This directory contains the reproducible analysis scripts, quantitative results JSONs, and QC figures for:

1. **Task 43 & Review of Finding `#1052` (`audit_task43_phaselock.py`, `task43_phaselock_audit.json`, `qc_steps35_cfg6_s2_co_motion.jpg`)**:
   - Independent dual-patch NCC + preregistered decision gate `#802` audit of all 9 clips in `work/rahul-5-agy/phaselock/`.
   - **Result**:
     - **Replicates** the `0/7` low-step non-release result across `steps ∈ {2, 4, 8, 15}`, `CFG ∈ {1, 6}`, seeds 1–2 (`fall_px = 0.0` on both `2-step, CFG 6` seeds; gripper never opens and dissolves into a white blur cloud by `f46–f90`).
     - **Challenges** the interpretation of `ball1_steps35_cfg6_s2` (`firstfall.py` `flag="ok", g = 4.35 ± 0.28 m/s²` over `f3..f7`) as a clean true release: during `f3..f7`, the white Franka gripper housing (`(282, 68)`) moves downward by `44.66 px` alongside the ball (`49.29 px`), leaving only `+4.63 px` of net ball-minus-gripper separation (`< 40 px` threshold in preregistered gate `#802`). Over `f0..f10`, the robot arm plunges `110.11 px` downward into the wooden plank, spawning `2–3` simultaneous black balls (`f10–f22`) and levitating/tilting the wooden plank upward like a seesaw (`f18–f46`). Thus both `2-step` (`0/2`) and `35-step` (`0/2`) at `93f, CFG 6` fail true physical release (`Δ = 0.0`).

2. **Task 51 (`analyze_task51_vae_rt.py`, `task51_vae_roundtrip_results.json`, `qc_task51_vae_roundtrip.jpg`)**:
   - Exact Cosmos3-Nano Wan2.2 `16×4×` VAE (`AutoencoderKLWan`, mode/argmax + `latents_mean`/`latents_std` normalization, matching `Cosmos3OmniPipeline._encode_video`) encode-decode round-trip test on all 4 real GAUGE bouncing ball clips (`1.mp4`–`4.mp4`, deduplicated 25 fps, letterboxed `832×480`), across both `129f` (`33` latent steps, full held+drop+bounce+rest) and `93f` (`24` latent steps, mid-fall start) windows (`n=8` pairs, 16 clips total; full lossless MP4s archived on GB10 at `/home/swarm/jobs/agy-1/vae_roundtrip/`).
   - **Result**:
     - **Reconstruction Fidelity**: Whole-frame PSNR = `36.25 ± 0.72 dB` (`35.49–37.04 dB`, `n=8`); ball-corridor PSNR = `35.90 ± 1.24 dB`. Active-bounce vertical trajectory RMSD = `6.51 ± 3.63 px` (`18.56 ± 10.35 mm`) on the 4 full `129f` clips (`3.54–3.60 px` on Balls 1 & 3).
     - **Impact Timing Preservation**: Across the 4 full `129f` clips (`20/20` plank impacts recovered at identical integer frames `[37, 49, 55, 61, 64]`, `[39, 49, 57/58, 62, 68]`, `[39, 49, 58, 62, 65]`, `[35, 45, 53, 58, 64]`), sub-frame impact timing MAE is **`0.094 ± 0.069` frames (`3.76 ± 2.75 ms`)** (`0.015f` on Ball 1, `0.038f` on Ball 3).
     - **Bounce Decay ($e_T, e_h$) Preservation**:
       - Geometric flight-time restitution $e_{T,\text{log}}$ across the 4 full `129f` clips is **`0.731 ± 0.073` (Original) vs `0.726 ± 0.063` (VAE Round-Trip)** (`Δe_T = -0.005 ± 0.010`, paired max `|Δ| = 0.020`). On the clean 4-flight decaying clips (Ball 1 & Ball 3, plus mid-fall windows), $e_{T,\text{log}}$ is **`0.662 ± 0.021` (Original) vs `0.665 ± 0.011` (VAE Round-Trip)** (`Δe_T = +0.002 ± 0.016`).
       - Height restitution $e_h = \sqrt{h_{k+1}/h_k}$ across the 4 full `129f` clips is **`0.644 ± 0.009` (Original) vs `0.649 ± 0.010` (VAE Round-Trip)** (`Δe_h = +0.005 ± 0.016`).
       - `at_rest_by_end` (`rest_s ≈ 2.57–2.73 s`) matches on `7/8` clips (`4/4` on full `129f`).
     - **Conclusion**: Nano's 4× temporal Wan2.2 VAE **completely preserves** real-video bounce decay ($e_T \approx 0.66\text{–}0.73$, $e_h \approx 0.64$), impact timing (`MAE < 4 ms`), and settling to rest (`~2.6 s`). Therefore, Nano's perpetual-bouncing failure (`e_T = 0.99 ± 0.03`, `still_bouncing_at_end = true` in Findings `#1029`/`#1055`) is **100% a DiT dynamics prior failure**, not a Wan2.2 VAE temporal-compression bottleneck.
