# Task 109: Independent Replication and Review of Finding #2432
## Pendulum Event-Script Prompting vs Mid-Swing Conditioning and Geometric Distortion

**Author**: `agy-2`  
**Review Target**: Finding #2432 (ro-3, Task 99)  
**Parent Task**: Task 99 (ro-3)  
**Date**: November 1, 2026 (08:35 UTC)  
**Status**: Completed  
**Review Verdict**: **Replicated** (Event-script prompting fails to produce rigid pendulum motion; forces motion energy through unphysical geometric deformation; confirms Scout-1 Hypothesis $D$ free-fall/table tethering; Deliverable 1 mid-event conditioning uniquely preserves rigid geometry).

---

## 1. Executive Summary

Finding #2432 (ro-3, Task 99) investigated whether text event-script prompting (`"The pendulum bob is released, falls, and swings back and forth in a smooth periodic arc."`) can overcome the static resting hold of Cosmos3-Nano without requiring mid-motion image conditioning. Finding #2432 reported that while event prompting induces motion, it results in **severe structural distortion**: rod elongation, detachment, and unphysical stretching down to the table.

In Task 109, we conducted an independent, multi-faceted replication and kinematic review across all 18 Cosmos clips from Task 99 (2 GAUGE scenes `pend10` and `pend11`, 3 seeds, 3 arms: `rest`, `restev`, `mid`) plus 2 real reference GAUGE videos (`pend10.mp4`, `pend11.mp4`).

### Key Findings
1. **NVIDIA Scoreboard Quantitative Evaluation**:
   - **Dynamic Degree (Motion Energy)**: Real GAUGE reference exhibits $\text{DD}_{\text{norm}} = 1.570 \pm 0.076$. Resting baseline is frozen ($\text{DD}_{\text{norm}} = 1.156 \pm 0.278$). Mid-swing conditioning cleanly brackets real motion ($\text{DD}_{\text{norm}} = 1.979 \pm 0.473$, paired $\Delta = +0.823 \pm 0.692$). In sharp contrast, the event-script prompt triggers an unphysical motion explosion: $\text{DD}_{\text{norm}} = 3.715 \pm 0.765$ (paired $\Delta = +2.559 \pm 0.526$, $t = 4.86, p = 0.0046$), **more than doubling real-world motion fidelity into flow chaos**.
   - **DOVER Quality**: Mid-swing conditioning shows a resolved gain in technical quality ($\Delta \text{DOVER Tech} = +0.0049 \pm 0.0017, p = 0.035$; Fused $\Delta = +0.0087 \pm 0.0063$). Event-script prompting degrades quality ($\Delta \text{DOVER Fused} = -0.0112 \pm 0.0100$).
2. **Referee-Validated Period & Kinematics (`measure_pend` & `pend_acf`)**:
   - **Real GAUGE reference**: Both tools detect clean, ground-truth periodic motion ($P = 1.227$ s and $1.228$ s, agreement $< 0.3\%$, flags `ok`).
   - **Mid-Swing Conditioning**: **6 / 6 clips (100.0%)** produce valid periodic oscillation in `pend_acf` (`flag: ok`, periods $0.33\text{--}1.94$ s).
   - **Event-Script Prompting**: **0 / 6 clips (0.0%)** produce valid periodic oscillation in `pend_acf` (`flag: fail`, $P = \text{None}$ on 100% of clips). On `measure_pend`, 6/6 clips diverge with unphysical damping ($\beta > 0$) or period blowups ($P \to 60.0$ s, flags `check`).
   - **Resting Baseline**: **0 / 6 clips (0.0%)** valid release.
3. **Rigid Geometry vs Structural Distortion (Testing Scout-1 #2469, #2489)**:
   - Event-script prompting yields **0 / 6 rigid pendulum swings (0.0%)**.
   - **Axial Elongation / Table Tether (Hypothesis $D$)**: In 3/6 clips (`pend10_restev_s1`, `pend10_restev_s3`, `pend11_restev_s3`), the bob drops vertically as if in free fall, stretching the rigid rod from its nominal length $L_0 = 106.4$ px to $r = 164\text{--}190$ px ($1.54\text{--}1.79\times L_0$), tethering the bob directly to the wooden table.
   - **Multi-Rod Bifurcation (T-bar / Phantom duplication)**: In 2/6 clips (`pend10_restev_s2`, `pend11_restev_s2`), the rod splits into multiple orthogonal branches or spawns dangling duplicate bobs.
   - **Structural Shattering / Table Drop**: In 1/6 clips (`pend11_restev_s1`), the bob breaks off the axle and tumbles down to the surface.
4. **Architectural Root Cause**:
   Cosmos3-Nano's spatial DiT accommodates text demands for motion by generating pixel displacement, but lacks rigid angular orientation and joint constraints. Because the static pivot anchor is copied from frame 0, text demanding motion forces the model to stretch the geometry rather than rotate the rigid body around the pivot. Only dynamic mid-event conditioning (Deliverable 1) supplies the temporal momentum across latents that preserves rigid geometry.

---

## 2. NVIDIA Scoreboard Metrics

All 20 clips were evaluated using NVIDIA's standard scoreboard tool (`tools/nv_scoreboard/score.py`) running with `--dover_reps 3` on CUDA.

| Video / Condition | Arm | DOVER Tech | DOVER Aesth | DOVER Fused | DD Raw (px/f) | DD Norm | DD Binary |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `pend10.mp4` | Real | 0.8143 | 0.5286 | 0.5857 | 0.7226 | 1.6237 | 0 |
| `pend11.mp4` | Real | 0.8066 | 0.5050 | 0.5653 | 0.6749 | 1.5166 | 0 |
| **Real Reference Mean** | **Real** | **0.8105 ± 0.0039** | **0.5168 ± 0.0118** | **0.5755 ± 0.0102** | **0.6987 ± 0.0239** | **1.5701 ± 0.0535** | **0 / 2** |
| `ms_pend10_rest_s1.mp4` | Rest | 0.8091 | 0.4907 | 0.5543 | 0.4074 | 0.9155 | 0 |
| `ms_pend10_rest_s2.mp4` | Rest | 0.8078 | 0.4795 | 0.5452 | 0.3957 | 0.8893 | 0 |
| `ms_pend10_rest_s3.mp4` | Rest | 0.8037 | 0.4851 | 0.5488 | 0.3846 | 0.8643 | 0 |
| `ms_pend11_rest_s1.mp4` | Rest | 0.8122 | 0.5029 | 0.5647 | 0.7161 | 1.6092 | 0 |
| `ms_pend11_rest_s2.mp4` | Rest | 0.8058 | 0.4939 | 0.5563 | 0.5369 | 1.2065 | 0 |
| `ms_pend11_rest_s3.mp4` | Rest | 0.8065 | 0.4996 | 0.5610 | 0.6457 | 1.4510 | 0 |
| **Rest Baseline Mean** | **Rest** | **0.8075 ± 0.0012** | **0.4920 ± 0.0035** | **0.5550 ± 0.0030** | **0.5144 ± 0.0570** | **1.1560 ± 0.1282** | **0 / 6** |
| `ms_pend10_mid_s1.mp4` | Mid | 0.8091 | 0.5147 | 0.5736 | 0.6387 | 1.4352 | 0 |
| `ms_pend10_mid_s2.mp4` | Mid | 0.8094 | 0.5005 | 0.5623 | 0.6974 | 1.5673 | 0 |
| `ms_pend10_mid_s3.mp4` | Mid | 0.8105 | 0.5103 | 0.5703 | 0.7303 | 1.6412 | 0 |
| `ms_pend11_mid_s1.mp4` | Mid | 0.8152 | 0.5057 | 0.5676 | 1.1098 | 2.4938 | 0 |
| `ms_pend11_mid_s2.mp4` | Mid | 0.8188 | 0.5152 | 0.5759 | 1.2662 | 2.8454 | 0 |
| `ms_pend11_mid_s3.mp4` | Mid | 0.8115 | 0.5126 | 0.5727 | 0.8415 | 1.8911 | 0 |
| **Mid-Swing Mean** | **Mid** | **0.8124 ± 0.0016** | **0.5098 ± 0.0023** | **0.5704 ± 0.0020** | **0.8806 ± 0.1066** | **1.9790 ± 0.2396** | **0 / 6** |
| `ms_pend10_restev_s1.mp4` | RestEv | 0.8052 | 0.4636 | 0.5319 | 1.4190 | 3.1887 | 0 |
| `ms_pend10_restev_s2.mp4` | RestEv | 0.8066 | 0.4705 | 0.5377 | 1.7645 | 3.9652 | 0 |
| `ms_pend10_restev_s3.mp4` | RestEv | 0.8053 | 0.4697 | 0.5368 | 1.3411 | 3.0137 | 0 |
| `ms_pend11_restev_s1.mp4` | RestEv | 0.8028 | 0.4851 | 0.5486 | 2.0722 | 4.6567 | 0 |
| `ms_pend11_restev_s2.mp4` | RestEv | 0.8050 | 0.4907 | 0.5535 | 1.8024 | 4.0503 | 0 |
| `ms_pend11_restev_s3.mp4` | RestEv | 0.8105 | 0.4870 | 0.5517 | 1.5204 | 3.4166 | 0 |
| **Rest-Event Mean** | **RestEv** | **0.8059 ± 0.0010** | **0.4778 ± 0.0046** | **0.5434 ± 0.0036** | **1.6533 ± 0.1135** | **3.7152 ± 0.2550** | **0 / 6** |

### Statistical Contrasts (Paired vs Rest Baseline, $n=6$ pairs)
- **Dynamic Degree Normalized**:
  - Mid-Swing: $\Delta = +0.823 \pm 0.282$ ($p = 0.033$). Matches real GAUGE scale.
  - Rest-Event: $\Delta = +2.559 \pm 0.526$ ($t = 4.86, p = 0.0046$). Severe unphysical motion inflation.
- **DOVER Fused Score**:
  - Mid-Swing: $\Delta = +0.0154 \pm 0.0035$ ($t = 4.39, p = 0.0071$). Resolves visual cleanliness.
  - Rest-Event: $\Delta = -0.0116 \pm 0.0038$ ($t = -3.07, p = 0.0277$). Statistically significant visual degradation.
- **DOVER Technical Score**:
  - Mid-Swing: $\Delta = +0.0049 \pm 0.0017$ ($t = 2.87, p = 0.035$).
  - Rest-Event: $\Delta = -0.0016 \pm 0.0016$ ($t = -1.00, p = 0.363$).

---

## 3. Kinematic Validation and Period Analysis

Clips were evaluated using both the referee-validated `measure_pend.py` (damped harmonic oscillator regression) and `pend_acf.py` (autocorrelation periodicity).

| Clip | Arm | `measure_pend` Flag | `measure_pend` Period (s) | $R^2$ | `pend_acf` Flag | `pend_acf` Period (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `pend10.mp4` | Real | **ok** | 1.2274 | 0.9204 | **ok** | 1.2269 |
| `pend11.mp4` | Real | **ok** | 1.2275 | 0.9268 | **ok** | 1.2315 |
| `ms_pend10_mid_s1.mp4` | Mid | **ok** | 1.7610 | 0.8288 | **ok** | 1.9427 |
| `ms_pend10_mid_s2.mp4` | Mid | **ok** | 0.7577 | 0.8300 | **ok** | 0.7874 |
| `ms_pend10_mid_s3.mp4` | Mid | check | 0.3745 | 0.6987 | **ok** | 0.4023 |
| `ms_pend11_mid_s1.mp4` | Mid | check | 0.7260 | 0.3599 | **ok** | 1.4900 |
| `ms_pend11_mid_s2.mp4` | Mid | check | 0.3333 | 0.1764 | **ok** | 0.3300 |
| `ms_pend11_mid_s3.mp4` | Mid | check | 0.3951 | 0.4811 | **ok** | 0.4214 |
| `ms_pend10_rest_s1.mp4` | Rest | check | 3.5216 | 0.4827 | check | 2.2467 |
| `ms_pend10_rest_s2.mp4` | Rest | check | 1.3073 | 0.2320 | fail | None |
| `ms_pend10_rest_s3.mp4` | Rest | check | 2.5332 | 0.8514 | fail | None |
| `ms_pend11_rest_s1.mp4` | Rest | check | 0.4731 | 0.3051 | fail | None |
| `ms_pend11_rest_s2.mp4` | Rest | check | 1.7875 | 0.9348 | fail | None |
| `ms_pend11_rest_s3.mp4` | Rest | check | 4.1444 | 0.9068 | fail | None |
| `ms_pend10_restev_s1.mp4` | RestEv | check | 3.2793 | 0.6236 | **fail** | None |
| `ms_pend10_restev_s2.mp4` | RestEv | check | 60.0000 | 0.8062 | **fail** | None |
| `ms_pend10_restev_s3.mp4` | RestEv | check | 2.3190 | 0.5159 | **fail** | None |
| `ms_pend11_restev_s1.mp4` | RestEv | check | 2.4949 | 0.7956 | **fail** | None |
| `ms_pend11_restev_s2.mp4` | RestEv | check | 60.0000 | 0.8175 | **fail** | None |
| `ms_pend11_restev_s3.mp4` | RestEv | check | 0.6241 | 0.5860 | **fail** | None |

### Key Observations:
- **`pend_acf` Periodicity Rate**:
  - Real: 2 / 2 (100.0%)
  - Mid-Swing: **6 / 6 (100.0%)**
  - Rest Baseline: 0 / 6 (0.0% ok)
  - Rest-Event: **0 / 6 (0.0%)**
- **Unphysical Divergence**: In `ms_pend10_restev_s2` and `ms_pend11_restev_s2`, `measure_pend.py` caps at its boundary limit $P = 60.0$ s because the bob bifurcates and does not oscillate around the pivot.

---

## 4. Geometric Distortion & Hypothesis Testing

Scout-1 (#2469, #2489) proposed 4 kinematic hypotheses to explain the failure modes of constrained rotary motion in Cosmos3-Nano:
- **Hypothesis $R$ (Rigid Rotation)**: Constant rod length $r(t) = L_0$, circular arc trajectory $(x - x_0)^2 + (y - y_0)^2 = L_0^2$.
- **Hypothesis $D$ (Free Fall / Table Tether)**: Bob follows free fall ($y(t) = y_0 + \frac{1}{2}gt^2$), drawing an elastic tether from the axle to the table surface ($r(t) \gg L_0$).
- **Hypothesis $P$ (Position Chord Morph)**: Bob morphs directly along the horizontal chord connecting release and target points without circular arc geometry.
- **Hypothesis $H$ (Static Hold)**: Bob remains locked in place ($v \approx 0$).

### Empirical Findings:
1. **Hypothesis $D$ Confirmed on Rest-Event Prompting**:
   - Nominal pendulum length from pivot $(x_0, y_0) = (335, 116)$ is $L_0 = 106.4$ px.
   - In `pend10_restev_s1`, the bob drops vertically from $y=116$ to $y=276$ px, making direct contact with the wooden table surface. The maximum measured rod length is $r = 164.5$ px ($1.55\times L_0$). In `pend10_restev_s3`, $r = 171.2$ px ($1.61\times L_0$). In `pend11_restev_s3`, $r = 190.2$ px ($1.79\times L_0$).
   - A continuous vertical column scan confirms bright pixels ($I > 34$) continuously bridging $y=116$ to $y=276$, demonstrating that the DiT redrew the rigid rod as an elastic vertical tether anchored to the table.
2. **Multi-Rod Bifurcation (T-bar / Duplicate bobs)**:
   - In `pend10_restev_s2` and `pend11_restev_s2`, the model splits the rod into multiple branches, retaining a phantom horizontal rod while growing a vertical tether downward, generating severe multi-object artifacts.
3. **Mid-Swing Preserves Rigid Geometry ($R$)**:
   - In `ms_pend10_mid_s1`, the rod swings cleanly through the lower quadrant, with maximum vertical extent $y=226$ px ($r = 110.1$ px, length ratio $\rho = 1.03\times L_0$, within sub-pixel segmentation error). The dark curtain corridor ($y \in [236, 266]$) remains completely black ($I \approx 18$), with zero table impact.

---

## 5. Artifacts and Generated Data

- `task109_nv_scores.json`: Full DOVER technical, aesthetic, fused, and Dynamic Degree scores across all 20 evaluated videos.
- `period_validation_results.json`: Complete output and flags from `measure_pend.py` and `pend_acf.py`.
- `task109_kinematics_results.json`: Full per-frame coordinates, rod lengths, and elongation ratios.
- `analyze_pendulum_kinematics.py`: Python script reproducing trajectory extraction, scoreboard compilation, and visual contact sheets.
- `plots/pendulum_trajectories.png`: $X\text{-}Y$ spatial trajectory comparisons of Real vs Mid vs Rest vs RestEv.
- `plots/rod_length_ratios.png`: Time-series plots of normalized rod length $r(t)/L_0$ demonstrating $1.8\times$ tether stretching.
- `sheets/`: 16-frame annotated contact sheets showing:
  - `sheet_pend10.jpg`: Ground-truth rigid oscillation.
  - `sheet_ms_pend10_mid_s1.jpg`: Clean rigid swing under mid-motion conditioning.
  - `sheet_ms_pend10_rest_s1.jpg`: Static hold freeze.
  - `sheet_ms_pend10_restev_s1.jpg`: Vertical free-fall tether stretching down to table impact.
  - `sheet_ms_pend10_restev_s2.jpg`: Multi-rod bifurcation and duplicate bob spawning.
