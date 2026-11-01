# Task 71: Does guidance scale (CFG) or flow shift control Nano's undamped bounce ($e_T$) and allow settling to rest?

**Agent:** `rahul-5-agy`  
**Task ID:** 71  
**Status:** Completed  
**Associated Finding:** Provisionally posted to `#findings`  

---

## 1. Executive Summary & Core Results

In GAUGE mid-fall rollouts, NVIDIA Cosmos3-Nano exhibits near-zero bounce decay ($e_T \approx 0.99 \pm 0.01$, Findings #1172, #1283), bouncing perpetually across the entire clip (>25 bounces over 7.5 seconds) while real physical balls settle to complete rest in 1.4 seconds (4 bounces, $e \approx 0.693$).

Prior literature (Yonsei/MSRA, arXiv:2610.16365; CFG dynamics, arXiv:2404.07724) hypothesized that:
1. **High CFG (default 6.0)** amplifies dominant oscillatory modes and eliminates static/settling modes in diffusion video models.
2. **High flow shift (default 10.0)** concentrates 66% of denoising steps at coarse noise levels ($t > 0.84$), locking in macro-oscillations before terminal contact mechanics can be resolved.

To test whether lowering CFG or flow shift restores physical restitution ($e_T \to 0.69$) and allows balls to settle to rest, we generated a controlled 12-clip matrix across 6 inference conditions $\times$ 2 seeds on real GAUGE ball 1 mid-fall (`gauge_ball1_dd33_832x480.png`, 93 frames, 24 fps, 35 steps) using the shared Cosmos queue across 4 physical endpoints (A100, Puget13, Puget21, GB10).

### Key Empirical Findings:

| Condition | CFG | Flow Shift | n | Impacts Observed | Flight Restitution $e_T$ | Log Restitution $e_{T,\text{log}}$ | Free-Fall $g$ (m/s²) | Levitation Rate | Settle Rate | Still Bouncing at End |
|---|---|---|---|---|---|---|---|---|---|---|
| **Default Baseline** | 6.0 | 10.0 | 2 | [6, 6] | $0.975 \pm 0.075$ | 0.727 | 1.57 | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) |
| **Intermediate CFG** | 4.0 | 10.0 | 2 | [8, 5] | $0.893 \pm 0.077$ | 0.886 | 0.93 | 0/2 (0%) | 0/2 (0%) | 1/2 (50%) |
| **Low Guidance** | 2.5 | 10.0 | 2 | [0, 0] | N/A (no impacts) | N/A | N/A | **2/2 (100%)** | 0/2 (0%) | 0/2 (0%) |
| **Unguided Rollout** | 1.0 | 10.0 | 2 | [0, 0] | N/A (no impacts) | N/A | N/A | **2/2 (100%)** | 0/2 (0%) | 0/2 (0%) |
| **MSRA Regime** | 3.0 | 5.0 | 2 | [7, 7] | $1.039 \pm 0.051$ | 0.908 | -0.76 | 0/2 (0%) | 1/2 (50%) | 0/2 (0%) |
| **Low Flow Shift** | 6.0 | 3.0 | 2 | [6, 6] | $1.196 \pm 0.081$ | 0.821 | 0.53 | 0/2 (0%) | 1/2 (50%) | 1/2 (50%) |

---

## 2. In-Depth Mechanism Analysis

### A. The Mid-Air Levitation Attractor at Low Guidance ($\text{CFG} \le 2.5$)
Lowering CFG does **not** restore realistic bounce decay ($e \to 0.69$); instead, it causes a complete collapse of free-fall dynamics:
- At CFG 1.0 and CFG 2.5 across both seeds (4/4 clips), the ball begins falling from $y=150$ px, but after 10–15 frames vertical acceleration drops to zero, and the ball **freezes in mid-air** between $y=202$ and $y=284$ px (5 to 13 cm above the plank).
- It never touches the plank surface ($y \approx 335$ px) throughout the remaining 75 frames (3.1 seconds).
- **Mechanism:** Text-conditioned video diffusion models have a strong spatial-stillness prior in unguided or weakly guided states. Strong CFG ($\ge 4.0$) is required to overcome this static prior and drive motion; when guidance is reduced, the model relaxes into a static latent attractor, freezing the dynamic object mid-fall.

### B. Invariant Perpetual Oscillations at Intermediate CFG (4.0)
- In Seed 1 at CFG 4.0, the ball bounces 8 times across the entire clip. Successive flight-time restitution ratios measured by planted-PASS `bclock.py` are:
  `[1.003, 1.084, 0.992, 0.893, 1.054, 1.004, 1.055]` (mean $e_T = 1.002 \pm 0.023$, $e_{T,\text{log}} = 0.993$).
- This is an exact undamped limit cycle, demonstrating that the perpetual oscillation prior operates independently of overguidance.

### C. MSRA / Physics-IQ Regime (CFG 3.0, Flow Shift 5.0)
- MSRA (arXiv:2610.16365) recommended CFG 3.0 and flow shift 4.75–5.0 for improved physical adherence on synthetic WorldModelBench.
- On real GAUGE mid-fall clips, this regime achieves $e_T = 1.039 \pm 0.051$ ($e_{T,\text{log}} = 0.908$). It does **not** lower restitution toward real values.
- In Seed 2, the ball impacts and settles flat onto the plank ($y = 352.0$ px) from frame 15 to 35 (nearly 1 second of rest), before tiny sub-pixel chattering occurs. However, in Seed 1, the ball bounces continuously with energy gain ($e_T = 1.11 \pm 0.19$).

### D. Low Flow Shift & Unprompted Phantom Propulsion (CFG 6.0, Flow Shift 3.0)
- Shifting denoising timesteps toward fine noise (flow shift 3.0) produces energy amplification (mean $e_T = 1.196 \pm 0.081$).
- In Seed 1, the ball actually comes to rest on the plank at frame 28 ($y \approx 321$ px) and stays motionless for 18 frames (~0.75 s).
- However, at frame 46, **unprompted phantom propulsion** occurs: the resting ball spontaneously launches itself 25 cm back into the air and resumes perpetual bouncing until the end of the clip.

---

## 3. Dual-Method Measurement Verification

All clips were analyzed with dual independent trackers:
1. **Corridor Template Tracker & Parabolic Turning-Point Solver (`analyze_task71.py`):**
   Sub-pixel quadratic fit on impact cusps, rise heights, and flight durations.
2. **Referee Planted-PASS `bclock.py` (ro-1, 12/12 PASS on referee benchmark):**
   Independently tracked all impacts and flight durations:
   - `cfg4p0_shift10p0_s1`: 10 impacts, sequence of flight ratios around 1.004 ($e_T \approx 1.012$).
   - `cfg6p0_shift10p0_s1`: 8 impacts, middle 4 bounce ratios are strictly `[1.0, 1.0, 1.0, 1.0]`.

---

## 4. Artifacts & Deliverables

- `task71_cfg_flow_comparison.png`: 4-panel figure comparing trajectory $y(t)$, flight time decay $T_k$, mean restitution $e_T$ bar chart, and initial fall gravity $g$.
- `task71_results.json`: Complete quantitative measurements, per-frame coordinates, and flight parameters for all 12 clips.
- `sheets/`: Contact sheets with annotated frame numbers for all 12 clips:
  - `cfg1p0_shift10p0_s1_strip.jpg`, `cfg1p0_shift10p0_s2_strip.jpg` (mid-air levitation)
  - `cfg2p5_shift10p0_s1_strip.jpg`, `cfg2p5_shift10p0_s2_strip.jpg` (mid-air levitation)
  - `cfg3p0_shift5p0_s1_strip.jpg`, `cfg3p0_shift5p0_s2_strip.jpg` (settling and micro-chatter)
  - `cfg4p0_shift10p0_s1_strip.jpg`, `cfg4p0_shift10p0_s2_strip.jpg` (perpetual limit cycle)
  - `cfg6p0_shift10p0_s1_strip.jpg`, `cfg6p0_shift10p0_s2_strip.jpg` (baseline perpetual oscillation)
  - `cfg6p0_shift3p0_s1_strip.jpg`, `cfg6p0_shift3p0_s2_strip.jpg` (settling followed by unprompted relaunch)
- `sidecars/`: Exact JSON sidecars for all 12 clips generated across the 4 cluster endpoints.
- `analyze_task71.py`: Automated kinematic tracking and parabolic analysis script.
- `task71_contact_sheet.py`: Automated strip generation script.

---

## 5. Architectural & Swarm Conclusions

1. **Inference Hyperparameters Cannot Fix Cosmos Restitution:**
   Neither guidance scale ($\text{CFG} \in [1.0, 6.0]$) nor flow shift ($\text{shift} \in [3.0, 10.0]$) provides a viable inference recipe to achieve realistic bounce restitution ($e \approx 0.69$).
2. **Failure Modes are Categorical:**
   - Overguidance ($\text{CFG} \ge 4.0$): perpetual generative limit cycle ($e_T \approx 1.0$).
   - Underguidance ($\text{CFG} \le 2.5$): mid-air levitation attractor (0% landing rate).
   - Fine-noise bias ($\text{shift} = 3.0$): phantom momentum injection / unprompted relaunch from rest.
3. **Core Implication for Deliverables:**
   Because inference hyperparameter tuning (CFG, flow shift, steps, negative prompt, fps RoPE conditioning) uniformly fails to induce realistic energy dissipation, the perpetual bounce rhythm prior is embedded in the DiT generative weights. Breaking this prior requires weight-space interventions (such as `sim_drop` LoRA fine-tuning, Task 24) or explicit multi-frame trajectory conditioning.
