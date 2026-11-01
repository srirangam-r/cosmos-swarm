# Task 229: Independent Replication & Cluster Audit of Task 210 Robot Prediction

**Author**: `ro-agy1`  
**Targets**: Finding #4433 (`rahul-api`, Chunk 1), Finding #4562 (`rahul-api`, Chunk 2 Rollout)  
**Deliverable**: Deliverable 3, Pillar 4 (Real-Robot Bridge Forward Dynamics Prediction under Rule R)  

## Scope of Replication
1. **Independent MP4 Decoding & Hashing**: Independently fetched and verified all 288 Chunk 1 MP4s and 288 Chunk 2 MP4s (576 clips total, 24 Bridge episodes × 3 arms [base, R, N] × 4 seeds [0, 1, 2, 3]). Verified 100% bit-for-bit SHA256 concordance against published `clips_SHA256SUMS` and `clips_c2_SHA256SUMS`.
2. **Episode Independence**: Confirmed 24/24 clips belong to strictly distinct robot episodes (2407 to 51538; zero duplicate episodes).
3. **Standalone Scoring**: Recomputed all metrics using independent PyTorch/LPIPS-AlexNet and skimage/av pipelines:
   - Chunk 1 (frames 1..16): `independent_scores.json`
   - Window 'all' (frames 1..32): `independent_scores_c2_all.json`
   - Window 'c2' (frames 17..32): `independent_scores_c2_c2.json`
4. **Numerical Concordance**:
   - Chunk 1: Max discrepancies: PSNR $3.55 \times 10^{-15}\text{ dB}$, SSIM $2.22 \times 10^{-16}$, LPIPS $2.98 \times 10^{-8}$.
   - Rollout All (1..32): Max discrepancies: PSNR $3.55 \times 10^{-15}\text{ dB}$, SSIM $2.22 \times 10^{-16}$, LPIPS $2.98 \times 10^{-8}$.
   - Rollout C2 (17..32): Max discrepancies: PSNR $3.55 \times 10^{-15}\text{ dB}$, SSIM $2.22 \times 10^{-16}$, LPIPS $5.96 \times 10^{-8}$.
5. **Statistical Contrasts & Cluster Degrees of Freedom ($df=3$)**:
   - Chunk 1: LPIPS $R - \text{base} = -0.0012 \pm 0.0007$ ($t_{95\%} [-0.0027, +0.0004]$, cluster $df=3$ $[-0.0026, +0.0003] \to$ NONINFERIOR).
   - Rollout All (1..32): LPIPS $R - \text{base} = -0.0012 \pm 0.0011$ ($t_{95\%} [-0.0035, +0.0011]$, cluster $df=3$ $[-0.0067, +0.0043] \to$ NONINFERIOR).
   - Rollout C2 (17..32): LPIPS $R - \text{base} = -0.0013 \pm 0.0020$ ($t_{95\%} [-0.0055, +0.0029]$, cluster $df=3$ $[-0.0115, +0.0089] \to$ NONINFERIOR).
6. **Seed Noise Dominance**:
   - Within-base pseudo-contrast ({0,1} vs {2,3}):
     - Chunk 1: $\Delta = -0.0101 \pm 0.0030$ (8.6× larger than prompt effect).
     - Rollout All: $\Delta = -0.0173 \pm 0.0033$ (14.2× larger than prompt effect).
     - Rollout C2: $\Delta = -0.0246 \pm 0.0055$ (19.2× larger than prompt effect).
7. **Provenance Notes**:
   - Chunk 1: Analysis plan committed during generation (168/288 clips downloaded before commit `b2403e6`). The $+0.010$ margin is an empirically motivated choice (static floor gap).
   - Chunk 2: Amendment 2 pre-registered before chunk 2 generation (commit `b8a5e50`).

## Program N Blind Coding Tools
- `make_blind_pack.py`: Generates randomized opaque-ID clip packs interleaved with planted known-answer controls, creates blank coding sheets, and pre-commits to `KEY_DO_NOT_OPEN.json` SHA256.
- `verify_blind_coding.py`: Automated audit evaluating blind coding accuracy against planted ground truth and inter-rater agreement (Cohen's kappa).
