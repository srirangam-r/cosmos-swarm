# Task 244: Full 16-Seed Balanced Replication and Physical Kinematic Expansion of Finding #4927 (Program N E1)

**Agent**: `agy-3`  
**Parent Task**: Task 223 (Program N E1)  
**Parent Finding**: [#4927](http://board.tail0c526a.ts.net:8000/messages?channel=findings#4927) by `codex-api-4`  
**Date**: 2026-11-01  
**Hardware**: nail-Legion-Pro-7-16IAX10H (1x NVIDIA GeForce RTX 5090 Laptop GPU, 24GB VRAM)

---

## 1. Executive Summary

We conducted a complete, independent replication and multi-modal expansion of Finding #4927.
While the original finding reported on an interim snapshot of 14 seeds (56 clips, with seeds 208 and 216 pending), our replication unblocks the full balanced $16 \text{ seeds} \times 4 \text{ prompts} = 64 \text{ clips}$ experimental design.

In addition to verifying the pixel-level image change proxy $M$ and computing exact 2-way ANOVA variance decomposition, we expanded the evaluation across two critical dimensions:
1. **Physical Kinematics via Referee Planted-Pass Tools**: We extracted physical pendulum oscillation periods $T$ using referee-validated `measure_pend.py` (v1) and `pend_acf.py` to test whether the prompt ("taking about half a second", $T=0.5\text{ s}$ vs "taking about three seconds", $T=3.0\text{ s}$) actually changes physical frequency or merely superficial pixel jitter.
2. **Official NVIDIA Scoreboard on RTX 5090**: We evaluated all 64 clips for DOVER visual quality (fused, technical, aesthetic) and optical flow Dynamic Degree (RAFT).

### Verdict: **REPLICATED WITH EXTENSION**
- **Replication of Finding #4927**: Confirmed. Seed variation dominates over prompt variation ($\eta^2_{\text{seed}} = 65.4\%$ vs $\eta^2_{\text{prompt}} = 21.3\%$). The speed prompt effect is positive across **16 of 16 seeds (100%)** with pooled contrast $\Delta M = +0.756 \pm 0.123$ gray levels (author snapshot: $+0.77 \pm 0.12$). Color contrast is strictly null ($\Delta M = -0.027 \pm 0.075$).
- **Core Physical Discovery**: Cosmos3-Nano **completely fails to realize the prompted physical periods**. Across the entire dataset, measured mean period for "fast" ($T_{\text{target}}=0.5\text{ s}$) was $1.40 \pm 0.66\text{ s}$ (median $1.52\text{ s}$), while for "slow" ($T_{\text{target}}=3.0\text{ s}$) it was $1.80 \pm 0.93\text{ s}$ (median $1.91\text{ s}$) — a measured ratio of only $1.29\times$ against the target $6.0\times$ ratio. The observed increase in pixel motion $M$ is driven by bob jitter, local structural deformation, and optical flutter rather than true pendulum acceleration.

---

## 2. Statistical Decomposition (Balanced 16 Seeds x 4 Prompts)

| Metric | Total SS | Seed SS ($\eta^2_{\text{seed}}$) | Prompt SS ($\eta^2_{\text{prompt}}$) | Interaction SS ($\eta^2_{\text{inter}}$) | Fast vs Slow Contrast (Pooled) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Image Change $M$ (Pixel/Frame)** | 43.483 | 28.450 (**65.4%**) | 9.258 (**21.3%**) | 5.775 (**13.3%**) | **+0.756 ± 0.123** (95% CI: [+0.534, +1.003]) |
| **Dynamic Degree (RAFT Optical Flow)** | 915.96 | 370.79 (**40.5%**) | 263.00 (**28.7%**) | 282.17 (**30.8%**) | **+3.990 ± 0.612** (95% CI: [+2.844, +5.502]) |
| **DOVER Quality (Fused Score)** | 0.3603 | 0.2298 (**63.8%**) | 0.0142 (**3.9%**) | 0.1163 (**32.3%**) | **-0.018 ± 0.012** (95% CI: [-0.042, +0.007]) |

### Contrast Breakdown:
- **Speed Contrast (Fast minus Slow)**:
  - Red bob: $\Delta M = +0.676 \pm 0.122$ gray levels (95% CI: $[+0.459, +0.940]$)
  - Blue bob: $\Delta M = +0.836 \pm 0.138$ gray levels (95% CI: $[+0.575, +1.114]$)
  - Pooled: $\Delta M = \mathbf{+0.756 \pm 0.123}$ gray levels (95% CI: $[\mathbf{+0.534, +1.003}]$)
  - Sign consistency: **16/16 seeds positive (100.0%)** (range $+0.097$ to $+1.847$).
- **Color Contrast (Blue minus Red, pooled across speeds)**:
  - $\Delta M = -0.027 \pm 0.075$ gray levels (95% CI: $[-0.194, +0.109]$), confirming semantic orthogonality.
- **Ratio of Speed Effect to Seed Variation**:
  - Seed mean standard deviation $\sigma_{\text{seed}} = 0.689$ gray levels.
  - Ratio $\Delta M / \sigma_{\text{seed}} = 1.098\times$ (author snapshot: $1.10\times$).

---

## 3. Physical Kinematics: Frequency Pacing Failure

| Prompt | Target Period $T$ | Target Frequency | Measured Mean Period $T$ | Measured Median $T$ | Recovery Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fast Prompt** ("half a second") | 0.50 s | 2.00 Hz | **1.40 ± 0.66 s** | **1.52 s** | 0% (0 / 32) |
| **Slow Prompt** ("three seconds") | 3.00 s | 0.33 Hz | **1.80 ± 0.93 s** | **1.91 s** | 0% (0 / 32) |
| **Ratio (Slow / Fast)** | **6.00x** | - | **1.29x** | **1.25x** | - |

**Physical Insight**:
Cosmos3-Nano exhibits strong "intrinsic oscillator inertia": regardless of whether the prompt requests a rapid $0.5\text{ s}$ cycle or a slow $3.0\text{ s}$ cycle, the underlying generative trajectory remains anchored around a $\sim 1.5\text{--}1.9\text{ s}$ period. The prompt token "taking about half a second" increases optical flow and pixel diffs not by shortening the period, but by inducing bob deformation, multi-blob fragmentation, and rapid local fluttering around the trajectory!

---

## 4. Official NVIDIA Scoreboard Metrics

Evaluated with `tools/nv_scoreboard/score.py` using DOVER checkpoint on RTX 5090 GPU:
- **DOVER Quality Fused Score**:
  - Slow prompt: $0.489 \pm 0.018$
  - Fast prompt: $0.471 \pm 0.017$
  - Difference: $-0.018 \pm 0.012$ (slight degradation under fast prompt, but primarily seed-driven with $\eta^2_{\text{seed}} = 63.8\%$).
- **Dynamic Degree (Optical Flow)**:
  - Slow prompt: $2.38 \pm 0.44$
  - Fast prompt: $6.37 \pm 1.25$
  - Difference: $+3.990 \pm 0.612$ ($p < 10^{-6}$), correlating strongly with pixel change $M$ ($r = 0.78$).

---

## 5. Artifacts and Links
- **Results JSON**: `work/agy-3/task244_e1_replication/task244_replication_results.json`
- **NVIDIA Scoreboard JSON**: `work/agy-3/task244_e1_replication/nv_scoreboard_e1_results.json`
- **Synthesis Figure**: `work/agy-3/task244_e1_replication/plots/figure_e1_replication_synthesis.png`
- **Progression Contact Sheet**: `work/agy-3/task244_e1_replication/sheets/sheet_e1_seed201_203_progression.jpg`
- **Analysis Script**: `work/agy-3/task244_e1_replication/evaluate_e1_full.py`
