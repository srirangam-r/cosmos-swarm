# Task 90: RoPE Spatial Frequency Scaling Experiment

## Hypothesis
Per arXiv 2609.23658, Raj #696 item 1, and steering #1825, scaling RoPE height/width spatial frequencies by 0.7 during early denoising steps ($t \ge 900$) was hypothesized to widen the generative model's spatial receptive field and dissolve the mechanical gripper grasp anchor at frame 0 without modifying the input conditioning image.

## Experimental Setup
- **Model:** `nvidia/Cosmos3-Nano` (16B mixture-of-transformers)
- **Input Image:** GAUGE Ball 1 Frame 0 (held ball in Franka gripper), letterboxed to $832 \times 480$.
- **Settings:** 93 frames, 24 fps, 35 UniPC steps, CFG 6.0, flow shift 10.0, diffusers standard prompt template.
- **Arms:**
  - **Control (Scale 1.0):** Standard Cosmos3-Nano generation.
  - **Treatment (Scale 0.7):** Spatial RoPE frequencies multiplied by 0.7 for $t \ge 900$.
- **Seeds:** 1, 2, 3 (paired).

## Results Summary (n = 3 Paired Seeds)

| Metric | Control (Scale 1.0) | Treatment (Scale 0.7) | Paired Delta ($\Delta$) | Physical Ground Truth |
| :--- | :--- | :--- | :--- | :--- |
| **Physical Release Rate** | 0/3 (0.0%) | 0/3 (0.0%) | $\Delta = 0.0 \pm 0.0$ | 100% Release |
| **Ball Trajectory (S1)** | Clamped in jaws | Clamped in jaws ($y \approx 147\text{ px}$) | No release | Free fall $g \approx 9.8\text{ m/s}^2$ |
| **Ball Trajectory (S2)** | Clamped in jaws | Clamped in jaws + phantom clone ($y \approx 330\text{ px}$) | No release; clone persists | Free fall $g \approx 9.8\text{ m/s}^2$ |
| **Ball Trajectory (S3)** | Clamped in jaws | Clamped in jaws ($y \approx 140\text{ px}, \Delta y = 0\text{ px}$) | No release | Free fall $g \approx 9.8\text{ m/s}^2$ |
| **Referee `firstfall.py`** | `weak` (all seeds) | `weak` (all seeds) | Fitting artifacts | PASS 20/20 |
| **DOVER Fused (3 reps)** | $0.4335 \pm 0.0172$ | $0.4367 \pm 0.0113$ | $+0.0033 \pm 0.0154$ (n.s.) | Real Ref $0.4988$ |
| **DOVER Technical (3 reps)** | $-0.0667 \pm 0.0029$ | $-0.0637 \pm 0.0010$ | $+0.0030 \pm 0.0027$ | N/A |
| **DOVER Aesthetic (3 reps)** | $0.0338 \pm 0.0044$ | $0.0327 \pm 0.0049$ | $-0.0011 \pm 0.0054$ | Real Ref $0.0464$ |
| **Dynamic Degree (`dd_norm`)** | $3.02 \pm 1.28$ | $6.19 \pm 2.70$ | $+3.17 \pm 1.42$ | Real Ref $0.255$ |

## Conclusion & Negative Finding
RoPE spatial frequency scaling ($0.7\times$ for $t \ge 900$) does not break the mechanical grasp deadlock. Physical release failure ($0\%$ release) and phantom duplicate cloning persist across all evaluated seeds. Spurious optical flow increases due to gripper/background motion jitter. This conclusively rules out early spatial RoPE scaling as an inference-time solution for object detachment.
