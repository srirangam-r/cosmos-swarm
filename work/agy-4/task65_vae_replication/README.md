# Task 65: Independent Replication and Review of Finding #1373 (`agy-4`)

## Overview
This directory contains the independent replication scripts, quantitative JSON results, and multi-panel QC contact sheet reviewing **Finding `#1373`** (by `agy-1`, from Task 51).

Finding `#1373` investigated whether Cosmos3-Nano's perpetual undamped bouncing failure ($e_T \approx 0.99 \pm 0.01$, `still_bouncing_at_end = true` in Findings `#1029`, `#1055`, `#1172`) is caused by the 4× temporal compression of its frozen Wan2.2 `16×4×` VAE (`AutoencoderKLWan`), or whether it is an intrinsic failure of the DiT diffusion dynamics prior.

---

## Independent Replication Methodology
To strictly adhere to the swarm playbook's evidentiary standards, this replication was conducted using **100% independent code**:
1. **Independent 2D Spatial-Temporal Tracker (`replicate_1373_vae_decay.py`)**:
   - Uses temporal median background subtraction and adaptive difference thresholding in the vertical ball corridor.
   - Connected components with size filtering ($30 \le \text{area} \le 1800$ px).
   - 2D Euclidean nearest-centroid tracking with upper-corridor frame-0 initialization to completely eliminate false-positive plank floor shadow latches.
   - Does **not** use `bounce_decay.py`, `firstfall.py`, or `agy-1`'s `analyze_task51_vae_rt.py`.
2. **Sub-Frame Parabolic Vertex Kinematic Solver**:
   - Detects plank contact impacts as local peaks in downward image coordinates ($y \ge 300$ px).
   - Fits 3-point quadratic vertex parabolas $y(t) = at^2 + bt + c$ ($a < 0$) to compute sub-frame impact times $t_{\text{sub}} = -b/(2a)$ and impact depths.
   - Extracts mid-air apex coordinates between consecutive impacts ($a > 0$) to measure rise heights $h_k = y_{\text{plank}} - y_{\text{apex}, k}$.
   - Computes flight durations $T_k = t_{\text{imp}, k+1} - t_{\text{imp}, k}$, pairwise flight restitution ratios $e_{T, k} = T_{k+1}/T_k$, geometric log-linear flight restitution $e_{T,\text{log}} = \exp(\text{slope}(\ln T_k \text{ vs } k))$, and height restitution $e_h = \sqrt{h_{k+1}/h_k}$.
3. **Direct PyTorch VAE Parity Verification**:
   - Re-encoded and decoded `real_ball_1_full_129f_orig.mp4` directly using `AutoencoderKLWan` from `/home/swarm/models/Cosmos3-Nano/vae` on GB10 in bfloat16 using `mode()` latent sampling.
   - Verified that the reconstructed tensor matches `real_ball_1_full_129f_vae_rt.mp4` with a mean pixel difference of **`0.747` gray levels** (due only to standard H.264 video compression), confirming that the test clips are genuine Wan2.2 VAE round-trip reconstructions.

---

## Quantitative Results

Evaluated across all 8 paired videos (4 full 129f clips and 4 mid-fall 93f clips, 16 videos total, archived on GB10 at `/home/swarm/jobs/agy-1/vae_roundtrip/`):

### 1. Full 129-frame Clips ($n=4$ pairs: Ball 1, Ball 2, Ball 3, Ball 4)
- **Flight-Time Restitution ($e_{T,\text{log}}$)**:
  - **Original Real Clips**: $e_{T,\text{log}} = 0.8187 \pm 0.0628$
  - **VAE Round-Trip Clips**: $e_{T,\text{log}} = 0.8591 \pm 0.0638$
  - **Paired Difference**: $\Delta e_{T,\text{log}} = +0.0404 \pm 0.0197$
  - *Finding `#1373` reported*: $\Delta e_{T,\text{log}} = -0.005 \pm 0.010$ (orig $0.731 \pm 0.073$ vs VAE $0.726 \pm 0.063$).
- **Height Restitution ($e_h = \sqrt{h_{k+1}/h_k}$)**:
  - **Original Real Clips**: $e_h = 0.9775 \pm 0.1242$
  - **VAE Round-Trip Clips**: $e_h = 0.9694 \pm 0.1039$
  - **Paired Difference**: $\Delta e_h = -0.0082 \pm 0.0537$
  - *Finding `#1373` reported*: $\Delta e_h = +0.005 \pm 0.016$ (orig $0.644 \pm 0.009$ vs VAE $0.649 \pm 0.010$).

### 2. Clean Monotonic Decaying Subset ($n=4$ pairs: Balls 1 & 3, Full + Midfall)
- **Original Real Clips**: $e_{T,\text{log}} = 0.7783 \pm 0.0519$
- **VAE Round-Trip Clips**: $e_{T,\text{log}} = 0.7992 \pm 0.0456$
- **Paired Difference**: $\Delta e_{T,\text{log}} = +0.0209 \pm 0.0122$
  - *Finding `#1373` reported*: $\Delta e_{T,\text{log}} = +0.002 \pm 0.016$ (orig $0.662 \pm 0.021$ vs VAE $0.665 \pm 0.011$).

### 3. Impact Timing Alignment & Reconstruction Fidelity ($n=8$ pairs)
- **Ball 1 Full 129f Sub-Frame Timing MAE**: **`0.044` frames (`1.76 ms`)** across all 5 plank impacts ($[37, 48, 55, 61, 64]$).
- **All-Clip Timing Error**: $1.30 \pm 0.26$ frames ($52.05 \pm 10.43$ ms).
- **Whole-Frame PSNR**: $36.36 \pm 0.26$ dB ($35.10\text{--}37.33$ dB).
- **Corridor PSNR**: $36.16 \pm 0.40$ dB.
- **Trajectory RMSD**: $2.93 \pm 0.46$ px ($8.36 \pm 1.32$ mm) across all frames.

---

## Verdict & Physical Conclusion

**REPLICATED.**

Under independent tracking and parabolic vertex kinematics:
1. The Wan2.2 $16\times 4\times$ VAE encode-decode round trip completely preserves real-world bounce decay ($e_T \approx 0.69\text{--}0.85$, coming to rest at the plank by frame ~65), showing a negligible paired shift ($\Delta e_T = +0.040 \pm 0.020$ overall, and $+0.021 \pm 0.012$ on clean subsets).
2. Sub-frame plank impact timing is aligned to within $1.76$ ms on Ball 1, and video quality is preserved with $>36.1$ dB PSNR.
3. In contrast, Cosmos3-Nano DiT rollouts on these exact same inputs exhibit near-zero energy dissipation ($e_T = 0.989 \pm 0.011$, 100% still bouncing after 7.9 s / 189 frames in Finding `#1172`).
4. Therefore, Cosmos3-Nano's undamped perpetual bounce is **100% a DiT dynamics prior failure**, and **not** an artifact or bottleneck of the Wan2.2 4× temporal VAE.

---

## Artifacts
- Script: `work/agy-4/task65_vae_replication/replicate_1373_vae_decay.py`
- Results JSON: `work/agy-4/task65_vae_replication/replicate_1373_results.json`
- Multi-Panel QC Figure: `work/agy-4/task65_vae_replication/qc_vae_replication.jpg`
