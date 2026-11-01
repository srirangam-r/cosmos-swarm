# PhaseLock Step & Guidance Sweep on GAUGE Ball 1 Frame 0

Investigation of the PhaseLock hypothesis (arXiv:2606.06361) for Task 44 / Task 43.

## Hypothesis
Late diffusion denoising erodes physical velocity and freezes held objects in the gripper. Reducing inference steps (`steps ∈ {2, 4, 8, 15, 35}`) or guidance scale (`CFG ∈ {1.0, 6.0}`) might allow Nano to release held objects from GAUGE frame 0.

## Setup
- **Endpoint**: `http://100.77.182.40:8021` (sha-devel L40S, vLLM-Omni `nvidia/Cosmos3-Nano`, flow_shift=10.0, prompt: GAUGE ball 1 frame 0 prompt, size 832x480, 93 frames @ 24 fps)
- **Tracker**: `tools/realball/firstfall.py` (referee-validated PASS 20/20, seed point `(282, 117)` on ball)
- **Input**: `work/raj-1/gauge_ball/gauge_ball1_f0_832x480.png`

## Results Summary Table

| Condition | Steps | CFG | Seed | Flag | Fall (px) | Fall (m) | Fall Time (s) | g (m/s²) | 95% CI | R² | dAIC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ball1_steps2_cfg6_s1` | 2 | 6.0 | 1 | `weak` | 0.0 | 0.000 | -0.167 | -0.80 | [-0.93, -0.69] | 0.9983 | 13.3 |
| `ball1_steps2_cfg6_s2` | 2 | 6.0 | 2 | `no_free_fall` | 0.0 | 0.000 | -0.167 | -7.39 | [-15.94, -0.54] | 0.4892 | 0.6 |
| `ball1_steps2_cfg1_s1` | 2 | 1.0 | 1 | `no_free_fall` | 0.0 | 0.000 | 1.000 | -0.27 | [-0.59, 0.13] | 0.4000 | -0.2 |
| `ball1_steps4_cfg6_s1` | 4 | 6.0 | 1 | `weak` | 5.5 | 0.010 | 0.042 | -0.38 | [-0.54, -0.25] | 0.9572 | 6.3 |
| `ball1_steps4_cfg6_s2` | 4 | 6.0 | 2 | `no_free_fall` | 54.8 | 0.102 | 0.771 | 0.23 | [-0.14, 0.62] | 0.9733 | -0.9 |
| `ball1_steps8_cfg6_s1` | 8 | 6.0 | 1 | `weak` | 0.0 | 0.000 | -0.127 | 0.40 | [0.31, 0.48] | 0.9823 | 10.6 |
| `ball1_steps15_cfg6_s1` | 15 | 6.0 | 1 | `no_free_fall` | 243.8 | 0.452 | 0.332 | -1.35 | [-10.90, 9.18] | 0.9464 | -1.9 |
| `ball1_steps35_cfg1_s1` | 35 | 1.0 | 1 | `weak` | 0.6 | 0.001 | 0.063 | 0.37 | [0.22, 0.55] | 0.9333 | 5.2 |
| `ball1_steps35_cfg6_s1` | 35 | 6.0 | 1 | `no_free_fall` | 0.0 | 0.000 | -0.167 | -11.42 | [-21.31, 0.94] | 0.9641 | 0.9 |
| `ball1_steps35_cfg6_s2` | 35 | 6.0 | 2 | `ok` | 77.8 | 0.144 | 0.312 | 4.35 | [3.85, 4.90] | 0.9993 | 17.7 |

## Key Findings
1. **PhaseLock (low step count) does NOT fix the gripper release problem**: Across all 2-step runs (CFG 6 seeds 1-2, CFG 1 seed 1), fall distance is 0.0 px (`flag: no_free_fall` / `weak`). In fact, low steps introduce severe visual blurring and do not cause the gripper to open.
2. **Release failure is seed-dependent at 35 steps**:
   - Seed 1 fails to open gripper and yields `0.0 px` fall (`flag: no_free_fall`).
   - Seed 2 opens gripper and releases the ball, yielding `77.8 px` fall, `g = 4.35 ± 0.28 m/s²`, `R² = 0.9993`, `dAIC = 17.7` (`flag: ok`).
3. **Conclusion for Task 43 / 44**: Reducing denoising steps is NOT an effective inference recipe for the gripper hold problem. True solutions must either condition on a post-release state (as proven in Finding #698 where mid-fall initialization yields real Earth gravity $g \approx 8.3-9.9\text{ m/s}^2$), or apply latent motion / force guidance.
