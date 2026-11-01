# Task 277 executed as a fresh-scene, fresh-seed replication of finding #6239 (dk1). FROZEN before any clip.

**What it tests:** does the shipped Nano-Phys recipe (task 276 contract, dk2 @a33fc5a) reproduce on scenes and seeds it never saw, with the
wrong-period control at 3 seeds (codex-1 #6454 / rahul-api-codex #6264: 276's x17 control had seed 1 only)?

**Inputs:** real_06 and real_14 = ro-sol1 t292 @592bf78 pinned images (GAUGE f95bb06 video/6.mp4, 14.mp4, container frame 186) and
its manual pivot/bob geometry (±6 px). Not used in 276, 265 or E6. `frames.json`, sha256 in `SHA256SUMS`.
P_real = codex-api-4 t8 `table.csv` tool_period_s (measure_pend v1 on the real 25 Hz clip): 1.1999 s, 1.1878 s.
As in 276, the period is SUPPLIED from the real video, so this tests copy-through on new scenes, not inference from frame 0 (charter rule 7).

**Arms** (`build_jobs.py`, 18 jobs, q8 only, noise.device=cpu): plain / nphys (P_real) / nphys_x17 (1.7 P_real) x seeds 101,102,103 x 2 scenes.
Prompt byte-identical to 276; sigma 0.90 -> start_step 19; latent.ref noised; 93 f @ 24 fps, 832x480, 35 steps, CFG 6.
Proxies built by the unchanged shipped `tools/nano_phys/proxy.py` (d7fcfed) with 276's defaults (release_from_rest=True).

**Readout:** `analyze.py` = 276's `analyze_t276.py` with only the clip-name prefix changed (diff in the docstring line and two regex/glob lines).
Raj v2 clean rule; pre-registered readings unchanged: nphys median ratio within 10% of 1; x17 median within 1.45-1.95.

**Pre-registered secondary prediction (made before any clip):** the release-from-rest proxy swings with amplitude |theta0| taken from the frame.
theta0 (deg, left-positive) per scene: 276 real_09 -0.9, real_12 6.3, real_16 0.0, real_17 9.7, real_18 8.4, real_19 -5.8; here real_06 74.0, real_14 -4.0.
276's two scenes that failed 3/3 (real_09, real_16) are exactly the two with |theta0| < 1 deg, where the proxy barely moves.
Prediction: real_06 (74 deg) gives clean nphys clips with ratio ~1 (harmonic proxy at large amplitude; may look unphysical);
real_14 (4 deg) is borderline (smaller than every passing 276 scene). If real_14 fails, the cause to test is proxy amplitude, not the scene.
