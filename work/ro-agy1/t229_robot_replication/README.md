# Task 229: Independent Pixel-Level Replication & Metric Verification of Task 210 Robot Forward Dynamics

Independent replication and statistical audit of Task 210 (Finding #4433 by `rahul-api`), evaluating whether appending the D1 Generic Rule R suffix degrades Cosmos3-Nano's real-robot clip prediction on Bridge forward dynamics.

## Overview & Scope
- **Dataset**: Shared `tools/robot_pred/devset_bridge` (24 WidowX manipulation episodes, 256×256 resolution, 5 fps, chunk 1: 17 frames).
- **Episodes**: Rigorous audit of `index.json` confirms all 24 clips belong to strictly distinct robot episodes (episodes 2407 to 51538; zero duplicate episodes).
- **Arms & Seeds**: 3 arms (`base`, `R`, `N`) across 4 seeds (`s0`, `s1`, `s2`, `s3`) = 288 total clips.
- **Model / Setting**: Cosmos3-Nano on `q8-0..7` endpoints, 30 steps, guidance 1.0 (official model card forward dynamics specification), requested `flow_shift=10` (Karras sigmas on board endpoints).

## Replication Protocol
1. **SHA256 Manifest Verification (`audit_integrity.py`)**:
   - Independently verified SHA256 checksums of all 288 downloaded MP4 clips against `work/rahul-api/t210/clips_SHA256SUMS`.
   - Result: **288/288 matched bit-for-bit**.
2. **Independent Pixel Decoding & Metric Scoring (`independent_scorer.py`)**:
   - Independently decoded all 24 ground-truth videos and 288 generated clips from raw MP4 files using PyTorch and `lpips` (AlexNet).
   - Computed frame-0 echo (`mean |gen[0] - real[0]|`), motion MAD (`mean |gen[1:17] - gen[0]|`), real motion MAD, motion ratio, PSNR, SSIM, and LPIPS on predicted frames 1..16.
   - Re-scored the static floor baseline (repeating frame 0 across frames 1..16).
3. **Statistical Contrasts & Cluster-Level Inference (`replicate_contrasts.py`)**:
   - Primary contrast: LPIPS $R - \text{base}$ evaluated against pre-registered non-inferiority margin $+0.010$.
   - Evaluated clip-level paired t-tests and 20,000-draw clip bootstrap.
   - **Whole-Seed Cluster Analysis**: Because seeds 0..3 are shared across all 24 clips, computed seed-level mean contrasts across the 24 clips and evaluated exact seed-level degrees of freedom ($df=3$) and seed-cluster confidence intervals.
   - Evaluated within-base pseudo-contrast (seeds {0,1} vs seeds {2,3}).
   - Stratified into Instructed (13 clips) vs Default-Prompt ("A robot manipulates an object.", 11 clips).
