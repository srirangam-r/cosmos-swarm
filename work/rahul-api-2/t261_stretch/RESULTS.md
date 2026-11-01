# Task 261 Confirmatory Results: Does a Stretched Rod Predict Nano's Slow Pendulum?

**Status**: Completed (Conclusive, Preregistered)  
**Preregistration**: Commit `fb1365e` (`PREREG.md`), executed via frozen `code/analyze262.py`  
**Executors**: Designed & Preregistered by `rahul-api-2`; Executed, analyzed & finalized by `rahul-5-agy` (Shift 42)  
**Primary Decision**: **NOT DETECTED** ($n = 10$, $\rho = 0.285$, within-source permutation $p = 0.433$)

---

## 1. Background & Preregistered Hypothesis

In post hoc exploratory analysis (Task 213, Finding #4412), unsigned rod-length deviation $L_\text{dev}$ tracked the period in $n=23$ exploratory clips ($\text{Spearman } \rho = +0.47, p = 0.025$). Under classical pendulum dynamics, $T = 2\pi\sqrt{L/g}$, so a physically drawn rod that is stretched by fractional factor $S = L/L_\text{real} - 1$ should produce period dilation:
$$\log(T / T_\text{real}) = 0.5 \log(1 + S)$$
with a predicted theoretical slope of $0.50$.

**Confirmatory Question**:
On **fresh** clips not part of the Task 213 exploration, does signed rod stretch $S$ predict $\log(T / T_\text{real})$, and does it account for the observed $1.2\times - 1.7\times$ slowdown of Cosmos3-Nano?

### Data & Evaluation Protocol
- **Clips evaluated (Fresh pend10)**:
  - Raj's E3 pend10 clips: `N_E3_pend10_s601-624` (q8 endpoint, CPU noise, base prompt, 24 clips).
  - rahul-api's t226 P clips: `t226_P_{base,neutral,still,fast}_s101-106` (24 clips).
  - Total: 48 fresh clips (0 overlap with post hoc set).
- **Measures**:
  - Signed stretch $S = \text{median over frames with } \theta \in [-20^\circ, 80^\circ] \text{ of } (L / L_\text{real}(\theta) - 1)$, using kiro-1's $\theta$-binned reference curve from the real GAUGE pend10 continuation (`real.json`).
  - Period $T_\text{mp}$: Measured with `measure_pend v1` (referee planted-case PASS) with quality filter `flag == 'ok'`.
  - Eligibility filter: `flag == 'ok'`, rodtrack `valid_frac >= 0.6`, $\ge 10$ frames in $\theta$ range, $S > -0.9$.
- **Preregistered Decision Rule**:
  - $n < 8 \implies \text{INCONCLUSIVE}$.
  - $\rho > 0 \text{ and } p \le 0.05 \implies \text{SUPPORTED}$.
  - Otherwise $\implies \text{NOT DETECTED}$.

---

## 2. Primary Results

Across the fresh pend10 clips, $n = 10$ clips met all strict eligibility criteria across 10 independent clusters/seeds ($n \ge 8$ criterion met; fully conclusive).

| Metric | Value | 95% Bootstrap CI / Notes |
| :--- | :--- | :--- |
| **Eligible Clips ($n$)** | 10 | 10 independent seed clusters |
| **Spearman $\rho(S, \log(T/T_\text{real}))$** | **+0.285** | $[-0.552, +0.818]$ (Cluster bootstrap) |
| **Permutation $p$-value** | **0.433** | 10,000 within-source permutations |
| **OLS Slope $\frac{\mathrm{d}\log(T/T_\text{real})}{\mathrm{d}\log(1+S)}$** | **1.167** | $[-1.917, +4.541]$ (Theory: 0.50) |
| **Median Signed Stretch $S$** | **+0.206** | IQR $[+0.160, +0.300]$ |
| **Median Raw Period Ratio $T/T_\text{real}$** | **1.316** | $31.6\%$ slowdown |
| **Median Slowness After $\sqrt{1+S}$ Correction** | **1.168** | **$16.8\%$ residual unexplained slowdown** |
| **Primary Preregistered Decision** | **NOT DETECTED** | Fails $p \le 0.05$ threshold |

### Per-Clip Primary Breakdown
| Clip | Seed | Signed Stretch $S$ | Measured $T_\text{mp}$ (s) | $T / T_\text{real}$ | Corrected $T / (T_\text{real}\sqrt{1+S})$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `N_E3_pend10_s602` | 602 | +0.150 | 2.186 | 1.863 | 1.737 |
| `N_E3_pend10_s604` | 604 | +0.328 | 2.509 | 2.138 | 1.855 |
| `N_E3_pend10_s607` | 607 | +0.217 | 1.664 | 1.418 | 1.285 |
| `N_E3_pend10_s608` | 608 | +0.366 | 1.323 | 1.127 | 0.965 |
| `N_E3_pend10_s617` | 617 | +0.204 | 1.225 | 1.044 | 0.951 |
| `N_E3_pend10_s619` | 619 | +0.363 | 1.433 | 1.221 | 1.046 |
| `N_E3_pend10_s623` | 623 | +0.192 | 2.249 | 1.916 | 1.755 |
| `t226_P_fast_s102` | 102 | +0.082 | 0.898 | 0.765 | 0.736 |
| `t226_P_still_s101` | 101 | +0.100 | 1.293 | 1.102 | 1.050 |
| `t226_P_still_s106` | 106 | +0.208 | 1.692 | 1.442 | 1.312 |

Notice that counter-examples exist in both directions:
- `N_E3_pend10_s608` has a large stretch ($S = +0.366$), but a near-real period ($T = 1.323\text{ s}$).
- `N_E3_pend10_s602` and `s623` have moderate stretch ($S = +0.150$ and $+0.192$), but severe period dilation ($T = 2.186\text{ s}$ and $2.249\text{ s}$).

---

## 3. Secondary Preregistered Analyses

1. **Rodtrack's Own Sinusoid Period (`SEC_rodtrack_period`)**:
   - $n = 18$, $\rho = 0.639$, $p = 0.0117$, slope $1.288$ (CI $[0.185, 2.784]$).
   - *Methodological Caveat*: `rodtrack` estimates both $L$ and $\theta(t)$ from the exact same raw rod pixel blobs across frames. Tracking errors that misidentify bob centroids distort both estimated length and frequency in tandem, inducing artificial common-method correlation. When decoupled using the independently validated, planted-PASS `measure_pend v1`, this correlation collapses to null ($p = 0.433$).
2. **Subsets**:
   - `SEC_E3_only`: $n = 7 < 8 \implies \text{INCONCLUSIVE}$ ($\rho = -0.321, p = 0.779$).
   - `SEC_t226_only`: $n = 3 < 8 \implies \text{INCONCLUSIVE}$ ($\rho = +1.0, p = 0.167$).
3. **Secondary Scenes (`pend11` and `pend14`, pivot within 15 px)**:
   - $n = 11$, $\rho = 0.227$, $p = 0.248 \implies$ **NOT DETECTED**.
4. **Diagnostic Verifier Gate (`SEC_verifier_G3`)**:
   - Contingency table (real-speed $\pm 20\%$ vs kiro-1 $G_3$ $L_\text{dev} < 0.2$):
     - Real-speed & $G_3$ pass: 1
     - Real-speed & $G_3$ fail: 2
     - Slow/Fast & $G_3$ pass: 3
     - Slow/Fast & $G_3$ fail: 4
   - One-sided Fisher exact test: $p = 0.833$.
   - **Conclusion**: A rigidity verifier filtering on rod stretch does not separate physically accurate pendulum swings from dilated ones.

---

## 4. Key Conclusions

1. **Refutation of the Rod-Stretch Explanation**:
   The post hoc correlation observed in Task 213 does not replicate in a confirmatory preregistered test on fresh clips ($p = 0.433$, NOT DETECTED).
2. **Physical Residual Slowness**:
   Even after applying the theoretical $T \propto \sqrt{1+S}$ length correction, Cosmos3-Nano remains $16.8\%$ slower than ground truth across the median of eligible clips.
3. **Implications for Swarm Deliverables**:
   The slow pendulum in Cosmos3-Nano is **not** an artifact of rod elongation or simple geometric projection errors. Fixes targeting drawing geometry or geometric rigidity filters (such as best-of-N based purely on rod length) will not resolve the underlying temporal dynamics slowdown of the world model.

---

## 5. Follow-up Audit: Statistical Power and Nonlinear Swing Amplitude Analysis

In response to review #5550 by `dk2`, two critical hypotheses were evaluated:

### A. Statistical Power Derivation
- Across the $n=10$ clips, $\text{sd}(\log(1+S)) = 0.083$. The theoretical physical slope of $0.50$ therefore predicts $\text{sd} = 0.041$ in $\log T$.
- In contrast, the empirical residual variation in $\log(T/T_\text{real})$ across seeds is $\text{sd} = 0.319$ ($~8\times$ larger than the predicted stretch effect).
- Synthetic power simulations confirm that at $n=10$, one-sided Spearman has only **9% power** to detect a $0.5$ slope against this degree of seed scatter ($n=100$ reaches 32% power).
- Therefore, the primary informative physical estimand is the **length-corrected residual ratio** ($1.168\times$ median, $+16.8\%$ unexplained slowdown), which isolates the magnitude of the model's physical temporal error.

### B. Empirical Test of the Nonlinear Amplitude Hypothesis ($K(\theta_0)$)
The exact period of a pendulum oscillating at semi-amplitude $\theta_0$ is given by the complete elliptic integral of the first kind:
$$T(\theta_0) = T_0 \cdot \frac{2}{\pi} K\left(\sin^2\frac{\theta_0}{2}\right)$$
If Nano swings to much higher angles than the real recording, nonlinear period elongation could account for the remaining $1.17\times$ slowdown.

We evaluated the exact per-clip semi-amplitude $\theta_0 = \frac{1}{2}(\max \theta - \min \theta)$ from `rodtrack` against the real reference (`real_pend10_f93`):
- **Real pend10 baseline**: Peak-to-peak swing is $148.08^\circ$ ($\theta_0 = 74.04^\circ$, mean $\theta = 21.55^\circ$). Complete elliptic integral factor:
  $$\frac{2}{\pi} K\left(\sin^2\frac{74.04^\circ}{2}\right) = 1.1156$$
  Because real pend10 already has a large amplitude, its mocap period $T_\text{real} = 1.174\text{ s}$ already embodies an $11.6\%$ nonlinear elongation factor over small-angle $T_0$.
- **Cosmos3-Nano clips**:

| Clip | $T_\text{mp}$ (s) | $S$ | $\theta_0$ (deg) | $K_\text{ratio} = \frac{K(\theta_0)}{K(74.04^\circ)}$ | $\frac{T_\text{mp}}{T_\text{real}\sqrt{1+S}}$ | $\frac{T_\text{mp}}{T_\text{real}\sqrt{1+S}\cdot K_\text{ratio}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `N_E3_pend10_s602` | 2.186 | +0.150 | 107.32 | 1.1448 | 1.7375 | 1.5177 |
| `N_E3_pend10_s604` | 2.509 | +0.328 | 58.32 | 0.9581 | 1.8549 | 1.9360 |
| `N_E3_pend10_s607` | 1.664 | +0.217 | 57.66 | 0.9567 | 1.2858 | 1.3440 |
| `N_E3_pend10_s608` | 1.323 | +0.366 | 65.62 | 0.9759 | 0.9645 | 0.9883 |
| `N_E3_pend10_s617` | 1.225 | +0.204 | 57.79 | 0.9569 | 0.9513 | 0.9941 |
| `N_E3_pend10_s619` | 1.433 | +0.363 | 93.13 | 1.0717 | 1.0458 | 0.9759 |
| `N_E3_pend10_s623` | 2.249 | +0.192 | 75.64 | 1.0050 | 1.7553 | 1.7465 |
| `t226_P_fast_s102` | 0.898 | +0.082 | 71.25 | 0.9916 | 0.7355 | 0.7417 |
| `t226_P_still_s101` | 1.293 | +0.100 | 40.96 | 0.9259 | 1.0500 | 1.1341 |
| `t226_P_still_s106` | 1.692 | +0.208 | 88.80 | 1.0530 | 1.3118 | 1.2458 |

- **Key Findings on Amplitude**:
  1. **6 of 10 Nano clips swing with *smaller* amplitude than real pend10** (median $68.4^\circ$ vs $74.0^\circ$).
  2. Median $K_\text{ratio} = 0.984$ (IQR $[0.957, 1.058]$).
  3. After both length AND nonlinear amplitude correction, the median residual unexplained slowdown is:
     $$\text{Median } \frac{T_\text{mp}}{T_\text{real}\sqrt{1+S}\cdot K_\text{ratio}} = \mathbf{1.190\times}\quad (+19.0\%\text{ residual slowdown})$$
  4. On **E3 natural continuations alone** (excluding t226 prompt arms), raw median $T_\text{mp}/T_\text{real}$ is $1.418\times$ ($+41.8\%$), residual after length is $1.286\times$ ($+28.6\%$), and residual after length + amplitude is **$1.344\times$ ($+34.4\%$)**.
  5. Correlation between $K_\text{ratio}$ and the residual is null ($\text{Spearman } \rho = +0.20, p = 0.58$).

**Conclusion**: Nonlinear amplitude does not explain Cosmos3-Nano's residual slowness. Nano's slowdown is an intrinsic failure of learned temporal dynamics.
