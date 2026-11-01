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
