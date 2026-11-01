# Task 319 (dk2): NVIDIA scoreboard for Nano-Phys on the 42 task-276 clips

This is a re-score, not a new generation. agy-3's original run (#6370) is on an unreachable machine and was never published (#6609).
- **Inputs:** the exact 42 queue mp4s. Sidecars are byte-identical to a33fc5a work/dk2/t276/clips (42/42), and the sha256 of every mp4 is in gen_sha256.txt.
  - Arms: plain (6 scenes x seeds 1-3), nphys (P = P_real, 6x3) and nphys_x17 (seed 1). 93 f at 24 fps, 832x480.
- **Real refs:** codex-api-4 t8 real_09/12/16/17/18/19 (93 f, 25 fps container, mp4v).
  - For the official-form MF only, I re-wrapped them as 24 fps (`ffmpeg -r 24`, libx264 crf 10, frames unchanged). This gives scores_real24.json.
  - The DD sampling interval is round(fps/8) = 3 at both rates.
- **Scorer:** tools/nv_scoreboard/score.py, unchanged, at the commit in scorer_commit.txt. Settings: `--dover_reps 3`, CUDA on an RTX 4060 laptop, DOVER.pth sha256 f4a42c0b.
- **Analysis:** `python3 -I analyze_t319.py .` For each scene it averages the 3 seeds, then takes nphys - plain.
  - Scenes weigh equally. The 95% interval enumerates all 6^6 scene-bootstrap resamples exactly; a t-interval (df 5) is also given.
  - Seed-noise baseline: the pooled within-scene SD of plain.
- **MF:** `motion_fidelity.py mf24_manifest_<arm>.json --ddof 0 --zero-denominator zero` (dd_binary, Cosmos 3 report §E.2 eqs 10-11).

## Result (t319_table.md)
| metric | real | plain | nphys | x17 (s1) | nphys-plain | exact boot 95% | scenes<0 | pairs<0 |
|---|---|---|---|---|---|---|---|---|
| DOVER fused | 0.546 | 0.544 | 0.487 | 0.495 | **-0.057** | [-0.068, -0.049] | 6/6 | 18/18 |
| DOVER technical | -0.047 | -0.044 | -0.054 | -0.055 | -0.0097 | [-0.011, -0.008] | 6/6 | 18/18 |
| DOVER aesthetic | 0.062 | 0.059 | 0.044 | 0.048 | -0.015 | [-0.018, -0.011] | 6/6 | 16/18 |
| dd_binary | 0 (6/6) | 0.389 (7/18) | 0 (0/18) | 0 | -0.39 | [-0.50, -0.33] | | |
| dd_norm (PROXY) | 1.94 | 4.83 | 0.44 | 0.34 | -4.39 | [-5.5, -3.3] | 6/6 | 18/18 |

- **DOVER fused falls by 0.057 under Nano-Phys.** That is 2.2x the seed noise of a 3-seed mean (0.026; plain per-clip seed SD 0.044).
  - The interval lies entirely below -0.030, so it **fails a 0.030 non-inferiority margin**. The margin itself was never approved; it is agy-3's proposal.
  - Nano-Phys clips also score below the real clips (0.487 vs 0.546). Plain matches real.
  - The wrong-period x17 arm scores the same as nphys (Δ -0.001), so the drop comes from the proxy path itself, not from the period.
  - Per-scene Δ: -0.080 (09), -0.051, -0.062, -0.043, -0.052, -0.056. Scene 09 agrees with agy-3's interim -0.078 (#6461).
- **Motion:** the real clips are dd_binary 0 everywhere. Plain flags 7/18 clips as dynamic; nphys flags 0/18.
  - The continuous dd_norm is NOT NVIDIA's DD. Here real = 1.94, plain = 4.83 (excess flow) and nphys = 0.44 (*less* flow than real). The mean |gen - real| is plain 3.00 vs nphys 1.50.
  - So Nano-Phys removes plain's excess motion but undershoots the real flow. Optical flow alone cannot say whether that is lost background/camera motion or a smaller bob swing (codex-1 #6501).
- **Official-form MF (dd_binary):** plain 0.238, nphys 1.000.
  - The nphys 1.0 is **degenerate**: the real band's mean DD is 0, and every nphys DD is 0. Any static generator scores 1.0 under the zero-denominator convention.
  - VBench DD is blind to a small pendulum (README caveat), so MF here mainly rewards removing plain's spurious motion.

## Not tested
- The plausibility judge and robot-clip prediction (Nano-Phys does not apply to robot clips).
- Other prompts or scenes.
- The cause of the DOVER drop. Candidates: the coarse inpainting and rig texture seen in the proxy (#6133), and the intermediate-noise start at sigma 0.90.
- DOVER on the proxy mp4s themselves.
