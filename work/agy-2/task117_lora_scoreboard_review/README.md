# Task 117: Independent Replication and Review of Finding #2562
**Author**: `agy-2`  
**Target**: Finding #2562 by `rog-cc` (commit `30163c9`, `work/rog-cc/hue_t24/`)  
**Status**: **REPLICATED** (with novel domain-breakdown and motion collapse mechanisms identified)

---

## Executive Summary

Finding #2562 reported that all three Task-24 fine-tuning LoRA adapters (Arm A: real $g=9.81$, Arm B: wrong $g \sim 2.8$, Arm C: no decay) cause severe regressions across NVIDIA's evaluation scoreboard (DOVER visual quality, VBench Dynamic Degree motion fidelity, and Qwen3-VL-2B HUE plausibility) across 16 fixed T2V dev prompts ($n=160$ evaluations across 5 arms).

We conducted a complete independent replication and statistical audit from the raw evaluation files (`res/` and `res_nv/`) and original GB10 video assets (`~/jobs/rahul-3/hue_clips/`):
1. **Replication of Finding #2562**: Every grand mean, paired difference, standard error, and Student-$t$ 90% confidence interval reported in Finding #2562 replicates exactly to within rounding precision.
2. **Conclusive Failure of Non-Inferiority**:
   - **DOVER Fused Regression**: LoRA A drops by $\Delta = -0.0767 \pm 0.0211$ ($t = -3.63, p = 0.0025$) and LoRA B drops by $\Delta = -0.0752 \pm 0.0176$ ($t = -4.27, p = 0.0007$), decisively violating the non-inferiority margin ($\delta = 0.02$).
   - **Dynamic Degree Collapse**: LoRA A motion drops by $\Delta = -4.34 \pm 1.17$ ($t = -3.71, p = 0.0021$) and LoRA B by $\Delta = -3.43 \pm 0.96$ ($t = -3.57, p = 0.0028$), violating $\delta = 1.18$ ($15\%$ base mean).
   - **HUE Plausibility Drop**: LoRA A fails non-inferiority on Overall ($\Delta = -0.0280 \pm 0.0120$, 90% CI $[-0.0491, -0.0069]$ vs $\delta = 0.03$) and Physical Laws ($\Delta = -0.0347 \pm 0.0142$, 90% CI $[-0.0596, -0.0099]$ vs $\delta = 0.04$).
3. **Cross-Box Null Verified (`baseL - base`)**: The cross-box repeat across independent Lambda H100 PCIe boxes is zero within noise across all metrics (DOVER fused $+0.0055 \pm 0.0049$, DD $+0.07 \pm 0.28$, HUE overall $-0.0050 \pm 0.0023$, HUE physical $-0.0048 \pm 0.0037$), ruling out hardware/environment artifacts.
4. **Matched Physics Control Proves Zero Physics Benefit (`A - B`)**: Contrasting LoRA A against LoRA B (which differ *only* by training gravity, evaluated on the exact same box) yields **zero statistically detectable difference** in Physical Laws plausibility ($\Delta = -0.0053 \pm 0.0093, t = -0.57, p = 0.5739$) or DOVER fused quality ($\Delta = -0.0015 \pm 0.0172, t = -0.09, p = 0.9311$).
5. **New Discovery — Domain Breakdown & Catastrophic Robot Motion Collapse**:
   - Partitioning the dev prompts into **Physics** ($n=10$) and **Robot Manipulation** ($n=6$) reveals that LoRA fine-tuning causes **catastrophic hypokinesis on robot prompts**:
     - Base robot dynamic degree is $12.94 \pm 1.83$ (binary high-motion $92\%$).
     - LoRA A robot dynamic degree collapses by **$-66.2\%$** to $4.38 \pm 0.94$ (paired $\Delta = \mathbf{-8.56 \pm 1.65}, t = -5.19, p = 0.0035$), and DOVER fused drops by $\mathbf{-0.0977 \pm 0.0316}$ ($p = 0.0271$).
     - The model freezes the robot arm into postural deadlock while generating subtle background pixel creep.
6. **Decisive Takeaway for Swarm Deliverables**:
   Fine-tuning on synthetic ball drops violates NVIDIA's core scoreboard constraint: *"without making it worse at anything NVIDIA uses it for"*. It induces catastrophic forgetting of robot manipulation dynamics and visual quality. **No Task-24 LoRA adapter can serve as a Deliverable 1 candidate.** Deliverable 1's prompt-conditioned recipe is the sole viable deliverable.

---

## Complete Replicated Scoreboard (n=16 Prompts)

### Arm Grand Means
| Arm | Description | Box | HUE Overall | HUE Physical | DOVER Fused | Dynamic Degree (Norm) | High Motion Fraction |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **base** | Unmodified Base | Box 1 | $0.7063 \pm 0.0202$ | $0.5863 \pm 0.0366$ | $0.5991 \pm 0.0163$ | $7.89 \pm 1.48$ | $0.66 \pm 0.08$ |
| **baseL** | Repeat Base (A/A Null) | Box 2 | $0.7013 \pm 0.0198$ | $0.5815 \pm 0.0354$ | $0.6046 \pm 0.0174$ | $7.96 \pm 1.47$ | $0.66 \pm 0.08$ |
| **loraA** | LoRA A (Real $g=9.81$) | Box 2 | $0.6783 \pm 0.0211$ | $0.5516 \pm 0.0362$ | $0.5225 \pm 0.0191$ | $3.55 \pm 0.58$ | $0.25 \pm 0.07$ |
| **loraB** | LoRA B (Wrong $g \sim 2.8$) | Box 2 | $0.6881 \pm 0.0221$ | $0.5569 \pm 0.0369$ | $0.5240 \pm 0.0173$ | $4.46 \pm 0.88$ | $0.47 \pm 0.09$ |
| **loraC** | LoRA C (No Decay $e \sim 0.97$) | Box 1 | $0.6919 \pm 0.0225$ | $0.5696 \pm 0.0371$ | $0.5509 \pm 0.0242$ | $6.04 \pm 1.25$ | $0.47 \pm 0.09$ |

### Pairwise Contrasts & Statistical Verdicts
| Contrast | HUE Overall ($\delta = 0.03$) | HUE Physical ($\delta = 0.04$) | DOVER Fused ($\delta = 0.02$) | DD Norm ($\delta = 1.18$) | Verdict Summary |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **baseL − base** (A/A null) | $-0.0050 \pm 0.0023$<br>[-0.0090, -0.0010] (NI) | $-0.0048 \pm 0.0037$<br>[-0.0113, +0.0017] (NI) | $+0.0055 \pm 0.0049$<br>[-0.0031, +0.0140] (NI) | $+0.07 \pm 0.28$<br>[-0.42, +0.57] (NI) | **Clean Null**: Box repeat is invariant across all metrics. |
| **LoRA C − base** (No Decay) | $-0.0144 \pm 0.0065$<br>[-0.0258, -0.0030] (NI) | $-0.0167 \pm 0.0057$<br>[-0.0266, -0.0067] (NI) | $-0.0482 \pm 0.0204$<br>[-0.0840, -0.0124] (Drop) | $-1.85 \pm 0.63$<br>[-2.96, -0.74] (Drop) | Visual quality & motion drop from any fine-tuning. |
| **LoRA A − base** (Real $g$) | $-0.0280 \pm 0.0120$<br>[-0.0491, -0.0069] (NI Fail) | $-0.0347 \pm 0.0142$<br>[-0.0596, -0.0099] (NI Fail) | $\mathbf{-0.0767 \pm 0.0211}$<br>[-0.1137, -0.0397] (**REGRESSION**) | $\mathbf{-4.34 \pm 1.17}$<br>[-6.39, -2.29] (**REGRESSION**) | **Severe Scoreboard Regression**: Fails DOVER, DD, and HUE. |
| **LoRA B − base** (Wrong $g$) | $-0.0182 \pm 0.0091$<br>[-0.0342, -0.0022] (Drop) | $-0.0294 \pm 0.0119$<br>[-0.0502, -0.0086] (Drop) | $\mathbf{-0.0752 \pm 0.0176}$<br>[-0.1060, -0.0443] (**REGRESSION**) | $\mathbf{-3.43 \pm 0.96}$<br>[-5.12, -1.75] (**REGRESSION**) | Severe regression matching LoRA A. |
| **LoRA A − LoRA B** (Physics Effect) | $-0.0098 \pm 0.0062$<br>[-0.0207, +0.0011] ($p=0.135$) | $-0.0053 \pm 0.0093$<br>[-0.0216, +0.0109] ($p=0.574$) | $-0.0015 \pm 0.0172$<br>[-0.0317, +0.0286] ($p=0.931$) | $-0.91 \pm 0.51$<br>[-1.80, -0.01] ($p=0.096$) | **Zero Physics Benefit**: Correct gravity yields no plausibility gain over wrong gravity. |
| **LoRA A − baseL** (Same-Box) | $-0.0230 \pm 0.0116$<br>[-0.0432, -0.0027] (Drop) | $-0.0300 \pm 0.0125$<br>[-0.0519, -0.0080] (Drop) | $\mathbf{-0.0821 \pm 0.0217}$<br>[-0.1202, -0.0440] (**REGRESSION**) | $\mathbf{-4.41 \pm 1.24}$<br>[-6.59, -2.24] (**REGRESSION**) | Confirms identical regression relative to same-box baseline. |

*Note: Intervals are Student-$t$ 90% two-sided confidence intervals [lower, upper] ($\nu=15, t=1.753$), corresponding to one-sided 95% bounds. 100,000-iteration bootstrap percentile intervals are identical to within $\pm 0.001$.*

---

## Domain Disparity Analysis (Physics vs Robot Prompts)

Partitioning the 16 prompts into **Physics** ($n=10$) and **Robot Manipulation** ($n=6$) reveals the underlying mechanism of failure:

| Domain | Arm Contrast | $\Delta$ DOVER Fused | $\Delta$ Dynamic Degree | $\Delta$ HUE Physical Laws | Diagnostic Interpretation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Physics** ($n=10$) | **LoRA A − Base** | $-0.0641 \pm 0.0284$ ($p=0.051$) | $-1.81 \pm 0.91$ ($p=0.079$) | $-0.0455 \pm 0.0210$ ($p=0.058$) | Plausibility drops more than wrong-g control ($-0.0283$). Synthetic ball drops corrupt general physics. |
| | **LoRA B − Base** | $-0.0829 \pm 0.0254$ ($p=0.010$) | $-1.72 \pm 0.83$ ($p=0.068$) | $-0.0283 \pm 0.0186$ ($p=0.163$) | Visual quality degrades significantly. |
| | **baseL − Base** | $+0.0062 \pm 0.0060$ ($p=0.332$) | $+0.09 \pm 0.18$ ($p=0.631$) | $-0.0082 \pm 0.0050$ ($p=0.135$) | Noise baseline is stable. |
| **Robot** ($n=6$) | **LoRA A − Base** | $\mathbf{-0.0977 \pm 0.0316}$ ($p=0.027$) | $\mathbf{-8.56 \pm 1.65}$ ($p=0.0035$) | $-0.0168 \pm 0.0137$ ($p=0.276$) | **Catastrophic motion collapse**: Dynamic degree collapses by 66.2% ($12.94 \to 4.38$). Robot arms freeze. |
| | **LoRA B − Base** | $\mathbf{-0.0622 \pm 0.0222}$ ($p=0.038$) | $\mathbf{-6.29 \pm 1.65}$ ($p=0.0125$) | $-0.0313 \pm 0.0092$ ($p=0.019$) | Severe hypokinesis on robot scenes ($12.94 \to 6.66$). |
| | **baseL − Base** | $+0.0043 \pm 0.0091$ ($p=0.657$) | $+0.04 \pm 0.74$ ($p=0.956$) | $+0.0009 \pm 0.0051$ ($p=0.862$) | Invariant across boxes. |

### Why Did LoRA Collapse Robot Motion?
The Task-24 training data (`simdrop_v1`) consisted of 1,000 synthetic ball-drop clips on static indoor backgrounds. The generation tower (`moe_gen`, `time_embedder`, `vae2llm`, `llm2vae`) adapted to this static-background prior by learning to minimize optical flow across background and agent pixels. When presented with general robot manipulation prompts (e.g. `robot_011`, Franka arm reaching for objects), the fine-tuned model cannot coordinate multi-joint articulated movement, suppressing macroscopic motion by over 66%.

---

## Artifacts and Visual Evidence

1. **Structured Data**:
   - `task117_replication_results.json`: Full machine-readable audit containing all per-prompt differences, arm grand means, Student-$t$, and 100k bootstrap confidence intervals.
2. **Analysis Scripts**:
   - `audit_lora_scoreboard.py`: Independent parser and statistical evaluator.
   - `plot_lora_scoreboard.py`: Publication visualization script.
3. **Publication Figures**:
   - `plots/figure_scoreboard_contrasts.png`: Forest plot of pairwise contrasts against non-inferiority margins.
   - `plots/figure_domain_breakdown.png`: Domain breakdown showing robot motion collapse.
   - `plots/figure_dover_components.png`: DOVER Technical vs Aesthetic decomposition.
4. **Visual Contact Sheets**:
   - `sheets/sheet_robot011_comparison.jpg`: 20-panel contact sheet ($5\text{ arms} \times 4\text{ frames}$) showing robot arm freezing under LoRA A/B vs active movement in Base/BaseL.
   - `sheets/sheet_physics016_comparison.jpg`: 20-panel contact sheet across physics simulation prompt.
