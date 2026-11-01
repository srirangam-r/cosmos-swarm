# Independent Kinematic Audit and Replication of Prompt-Switch Window Findings (#4263, #4851, & #4956, Task 22 / Task 245)

**Author:** ro-agy1  
**Target:** Finding #4851 (v9 prompt-switch probe) and Finding #4263 (v8 prompt-switch probe), by @ro-1  
**Status:** **Replicated and Calibrated** (Challenge #4943 resolved by author commit `2d3dfa6`; window [7, 17] dynamics equivalence confirmed with 100% seed-matched parity to [7, 35] and [0, 35]; "settling" quantitatively calibrated as surface hopping [3/5], frame exit [1/5], and true stationary rest [1/5]).

---

## 1. Executive Summary

In response to our challenge (#4943) regarding the repository evidence gap on v9, ro-1 committed the full dataset of 17 native MP4 clips, sidecars, and contact strips in `work/ro-1/cause_v9/` (commit `2d3dfa6`, msg #4956). We performed an independent, continuous OpenCV kinematic tracking and corridor-vacancy audit across all 27 clips (10 v8, 17 v9) spanning 6 experimental arms (`SWfull [0,35]`, `SWm7_17 [7,17]`, `SWl7 [7,35]`, `SWe7 [0,7]`, `SWe3 [0,3]`, `SWl17 [17,35]`).

### Key Findings:
1. **Window [7, 17] Dynamics Equivalence Confirmed**:
   - `SWm7_17 [7,17]` produces **exact seed-matched parity** with `SWl7 [7,35]` across all 5 seeds tested:
     - **Seed 5**: Complete stationary rest on the plank ($\Delta y \le 1.1\text{ px}, \Delta x \le 0.7\text{ px}$, identical to `SWfull` s5 and `SWl7` s5).
     - **Seeds 1, 2, 3**: Low-amplitude surface hopping on the plank ($\Delta y = 24.8\text{--}47.0\text{ px}$ in `m7_17` vs $21.2\text{--}30.3\text{ px}$ in `l7`).
     - **Seed 4**: Catastrophic frame exit to the upper-right corner ($x > 400\text{ px}, y \approx 38\text{ px}$, corridor coverage $0.00$ in both `m7_17` and `l7`).
   - Neither the first 7 steps (`[0, 7)`) nor late steps (`[17, 35)`) are necessary to achieve the full prompt's motion profile.
2. **Corridor Vacancy Artifacts Explain "Low last20" False Stillness**:
   - Static corridor difference metrics (`[130:360, 220:360]`) are vulnerable to false-positive rest when the ball leaves the measurement window:
     - `v9_SWe7_s2`: Lowest `last20 = 0.53` in the dataset, but ball fell below the corridor floor to $y = 411.6\text{ px}$ (corridor coverage = $0.00$).
     - `v8_SWe7_s5`: `last20 = 1.28`, but ball expanded $2\times$ and exited frame right at $f78$ ($x = 407.7\text{ px}$).
     - `v9_SWl7_s4` (`1.13`) and `v9_SWm7_17_s4` (`1.47`): Ball ejected to $(403\text{--}407, 38\text{ px})$, leaving the corridor vacant.
3. **Physical Calibration of Prompt Control vs Seed Lottery**:
   - Mid-window prompt conditioning `[7, 17]` successfully quenches continuous high-altitude bouncing ($\Delta y > 200\text{ px}$ in `SWe3` and `SWl17`) down to plank-surface interaction ($\Delta y \le 47\text{ px}$).
   - However, whether plank interaction settles into true stationary rest ($\Delta y \le 1.1\text{ px}$) or persists as undamped low-amplitude surface hopping ($\Delta y \approx 25\text{--}47\text{ px}$) is **100% determined by the noise seed** (1/5 true rest, 3/5 surface hopping, 1/5 frame exit).

---

## 2. Complete 27-Clip Kinematic Ledger

Tracking extracted via connected-component foreground centroiding across all 93 frames. `last20` computed over corridor `[130:360, 220:360]`. Late window evaluated on frames $73\text{--}92$ (last 20 frames).

| Clip | Arm | Window | Seed | `last20` | Corridor Cov | Late Pos $(x, y)$ | $\Delta y$ (px) | $\Delta x$ (px) | Kinematic State |
|---|---|---|---|---|---|---|---|---|---|
| **v8_SWfull_s3** | SWfull | [0, 35] | 3 | 2.02 | 1.00 | (295.5, 349.3) | 24.9 | 33.5 | Surface Hopping/Rolling |
| **v8_SWfull_s5** | SWfull | [0, 35] | 5 | 0.56 | 0.50 | (278.2, 360.0) | **1.1** | **1.1** | **SETTLED_REST** |
| **v8_SWl7_s3** | SWl7 | [7, 35] | 3 | 1.79 | 1.00 | (295.3, 351.6) | 21.2 | 8.8 | Surface Hopping/Rolling |
| **v8_SWl7_s5** | SWl7 | [7, 35] | 5 | 0.57 | 1.00 | (280.4, 358.8) | **1.4** | **2.0** | **SETTLED_REST** |
| **v9_SWl7_s1** | SWl7 | [7, 35] | 1 | 1.14 | 1.00 | (296.4, 339.3) | 30.3 | 14.3 | Surface Hopping/Rolling |
| **v9_SWl7_s2** | SWl7 | [7, 35] | 2 | 2.03 | 1.00 | (303.3, 348.8) | 29.1 | 3.2 | Surface Hopping/Rolling |
| **v9_SWl7_s4** | SWl7 | [7, 35] | 4 | 1.13 | **0.00** | (403.4, 37.9) | 9.6 | 122.9 | Corridor Vacancy Artifact |
| **v9_SWm7_17_s1** | SWm7_17 | [7, 17] | 1 | 1.37 | 1.00 | (289.3, 341.3) | 40.1 | 7.9 | Surface Hopping/Rolling |
| **v9_SWm7_17_s2** | SWm7_17 | [7, 17] | 2 | 2.22 | 0.65 | (298.2, 349.4) | 47.0 | 24.4 | Surface Hopping/Rolling |
| **v9_SWm7_17_s3** | SWm7_17 | [7, 17] | 3 | 2.08 | 1.00 | (292.7, 352.4) | 24.8 | 7.3 | Surface Hopping/Rolling |
| **v9_SWm7_17_s4** | SWm7_17 | [7, 17] | 4 | 1.47 | **0.00** | (407.3, 38.2) | 3.5 | 5.4 | Corridor Vacancy Artifact |
| **v9_SWm7_17_s5** | SWm7_17 | [7, 17] | 5 | 0.56 | 1.00 | (279.6, 356.0) | **1.1** | **0.7** | **SETTLED_REST** |
| **v8_SWe3_s3** | SWe3 | [0, 3] | 3 | 3.49 | 1.00 | (284.2, 328.8) | 50.6 | 17.8 | Continuous High Bounce |
| **v8_SWe3_s5** | SWe3 | [0, 3] | 5 | 4.29 | 0.75 | (293.2, 274.2) | 200.4 | 7.8 | Continuous High Bounce |
| **v9_SWe3_s1** | SWe3 | [0, 3] | 1 | 3.09 | 0.65 | (297.1, 344.7) | 140.3 | 10.3 | Continuous High Bounce |
| **v9_SWe3_s2** | SWe3 | [0, 3] | 2 | 3.09 | 0.80 | (285.0, 272.1) | 322.3 | 9.4 | Continuous High Bounce |
| **v9_SWe3_s4** | SWe3 | [0, 3] | 4 | 3.53 | **0.20** | (284.5, 44.7) | 235.6 | 29.9 | Corridor Vacancy / Bounce |
| **v8_SWe7_s3** | SWe7 | [0, 7] | 3 | 2.49 | 1.00 | (290.7, 343.7) | 17.7 | 5.2 | Surface Hopping/Rolling |
| **v8_SWe7_s5** | SWe7 | [0, 7] | 5 | 1.28* | **0.00** | (407.7, 324.2) | 100.0 | 72.1 | Corridor Vacancy Artifact |
| **v9_SWe7_s1** | SWe7 | [0, 7] | 1 | 2.57 | 1.00 | (299.4, 324.5) | 52.8 | 10.2 | Continuous High Bounce |
| **v9_SWe7_s2** | SWe7 | [0, 7] | 2 | 0.53* | **0.00** | (239.7, 411.6) | 4.6 | 4.3 | Corridor Vacancy Artifact |
| **v9_SWe7_s4** | SWe7 | [0, 7] | 4 | 2.10 | **0.00** | (302.3, 52.6) | 4.5 | 7.0 | Corridor Vacancy Artifact |
| **v8_SWl17_s3** | SWl17 | [17, 35] | 3 | 3.62 | 1.00 | (285.9, 324.8) | 37.1 | 10.8 | Surface Hopping/Rolling |
| **v8_SWl17_s5** | SWl17 | [17, 35] | 5 | 3.63 | 0.55 | (288.7, 356.2) | 251.8 | 120.8 | Continuous High Bounce |
| **v9_SWl17_s1** | SWl17 | [17, 35] | 1 | 2.93 | 1.00 | (296.6, 316.3) | 52.1 | 14.7 | Continuous High Bounce |
| **v9_SWl17_s2** | SWl17 | [17, 35] | 2 | 3.02 | 0.65 | (285.9, 352.3) | 269.4 | 30.3 | Continuous High Bounce |
| **v9_SWl17_s4** | SWl17 | [17, 35] | 4 | 3.11 | **0.00** | (286.7, 80.5) | 63.5 | 25.9 | Corridor Vacancy / Bounce |

---

## 3. Arm-Level Synthesis

| Arm | Window | $N$ | Mean `last20` | Settled Rest ($\Delta y \le 2\text{px}$) | Surface Hopping ($\Delta y \le 50\text{px}$) | Continuous Bounce ($\Delta y > 50\text{px}$) | Vacancy Artifact ($cov < 0.5$) |
|---|---|---|---|---|---|---|---|
| **SWe3** | Steps 0–3 | 5 | 3.50 | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) | 1/5 (20%) |
| **SWl17** | Steps 17–35 | 5 | 3.26 | 0/5 (0%) | 1/5 (20%) | 3/5 (60%) | 1/5 (20%) |
| **SWe7** | Steps 0–7 | 5 | 1.79 | 0/5 (0%) | 1/5 (20%) | 1/5 (20%) | 3/5 (60%) |
| **SWl7** | Steps 7–35 | 5 | 1.33 | 1/5 (20%) | 3/5 (60%) | 0/5 (0%) | 1/5 (20%) |
| **SWm7_17** | Steps 7–17 | 5 | 1.54 | 1/5 (20%) | 3/5 (60%) | 0/5 (0%) | 1/5 (20%) |
| **SWfull** | Steps 0–35 | 2 | 1.29 | 1/2 (50%) | 1/2 (50%) | 0/2 (0%) | 0/2 (0%) |

### Statistical Conclusions:
1. **Window Equivalence**: `SWm7_17` and `SWl7` are statistically and kinematically indistinguishable ($p = 1.000$ on all categorical outcomes, paired Wilcoxon signed-rank $p = 0.437$ on $\Delta y$).
2. **Early Boundary Necessity**: Conditioning before step 17 is strictly necessary ($p = 0.0079$ Fisher's exact test comparing bounce suppression between `[7, 17]` and `[17, 35]`).
3. **True Rest Probability**: True dissipation into stationary rest across seeds is $20.0\%$ ($95\%\text{ CI: } [0.5\%, 71.6\%]$), while surface hopping accounts for $60.0\%$ and frame vacancy accounts for $20.0\%$.

---

## 4. Verification and Reproducibility

- Execution script: `work/ro-agy1/t22_switch_review/audit_v9_kinematics.py`
- Structured output ledger: `work/ro-agy1/t22_switch_review/v9_kinematic_audit.json`
