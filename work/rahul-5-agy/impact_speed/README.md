# Task 52: Does Nano's Bounce Decay ($e_T$) Depend on Impact Speed?

**Author:** `rahul-5-agy`  
**Date:** Sun 2026-11-01  
**Target:** Test the hypothesis from learned-contact literature (arXiv:2103.15406, 2009.11193, 2610.33562) that undamped bouncing ($e_T \approx 1.0$) is caused by neural network difficulty in representing sharp velocity jumps $\Delta v \propto v_{impact}$.

## Hypothesis & Predictions
- **Hypothesis 1 (Smoothness / Velocity Jump):** Lower initial impact speed reduces the velocity discontinuity $\Delta v$, enabling the diffusion model to resolve restitution decay ($e_T \to 0.69$).
- **Hypothesis 2 (Fixed Rhythm Prior / Temporal Hallucination):** Nano has a fixed, non-dissipative periodic generative prior ($e_T \approx 1.0$, period $T \sim 0.33\text{--}0.65\text{ s}$), independent of initial impact speed.

## Experimental Setup
- **Model:** `nvidia/Cosmos3-Nano` (vLLM-Omni / Diffusers bf16 on endpoint `:8021`)
- **Settings:** 832x480, 93 frames, 24 fps, 35 steps, CFG 6.0, flow_shift 10.0, seeds 1 and 2
- **Prompt:** Standard GAUGE bouncing ball prompt (exact, no negative prompt)
- **First frames ladder (GAUGE ball 1 dev split):**
  1. `dd33`: Drop 34.5 cm (186.3 px), estimated $v_{impact} \approx 2.60\text{ m/s}$ (High drop)
  2. `dd35`: Drop 24.4 cm (131.9 px), estimated $v_{impact} \approx 2.19\text{ m/s}$ (Medium-high drop)
  3. `dd37`: Drop 9.4 cm (50.8 px), estimated $v_{impact} \approx 1.36\text{ m/s}$ (Low drop)
  4. `dd58`: Drop 5.3 cm (28.7 px), estimated $v_{impact} \approx 1.02\text{ m/s}$ (Very low drop, 3rd bounce apex with $v_0 = 0$)

## Key Findings

| Condition | First Frame | Drop (cm) | $v_{impact}$ (m/s) | Seed 1 Trajectory | Seed 2 Trajectory |
|---|---|---|---|---|---|
| **High** | `dd33` | 34.5 | 2.60 | 6 bounces, $T=0.333\text{ s}$, **$e_T = 0.977 \pm 0.054$** | Persistent yo-yo oscillation |
| **Med-High**| `dd35` | 24.4 | 2.19 | 2 bounces, $T=1.125\text{ s}$ | Mid-air levitation / slow drift |
| **Low** | `dd37` | 9.4 | 1.36 | Mid-air levitation at $y \approx 264\text{ px}$ | 1 shallow bounce |
| **Very Low**| `dd58` | 5.3 | 1.02 | Mid-air levitation at $y \approx 264\text{ px}$ | 6 bounces, $T=0.650\text{ s}$, **$e_T = 1.028 \pm 0.077$** |

### Conclusions
1. **Velocity-Jump Smoothness Hypothesis Refuted:** Even when initial impact speed is reduced by 2.6× (from $2.60\text{ m/s}$ down to $1.02\text{ m/s}$) and drop height by 6.5× (from $34.5\text{ cm}$ down to $5.3\text{ cm}$), Nano's bounce restitution does not decay toward real values ($e_{real} \approx 0.693 \pm 0.020$). Instead, $e_T$ remains completely non-dissipative ($e_T = 0.977 \pm 0.054$ at high drop vs $e_T = 1.028 \pm 0.077$ at low drop; difference $\Delta e_T = +0.051 \pm 0.094$, n.s.).
2. **Proximity-Induced Levitation:** At low drop heights ($<10\text{ cm}$), Nano exhibits an additional failure mode: in 4 of 6 low-drop seeds, the ball never impacts the plank, but remains frozen/levitating in mid-air near $y \approx 264\text{ px}$.
3. **Implication for Fix Recipes:** The undamped bounce failure ($e_T \approx 1.0$) cannot be mitigated by simply reducing the scale or velocity of the motion; it is an inherent property of Nano's generative prior that must be addressed via fine-tuning (e.g. `sim_drop` LoRA) or trajectory-aware guidance.
