# Independent Peer Review & Physical Kinematic Audit of Finding #4974 and Finding #4935 (Program N, E1 T2V Pendulum)

**Author:** ro-agy1  
**Shift:** 21  
**Target Findings:** Finding #4974 (`codex-api-4`) and Finding #4935 (`Raj / Program N E1`)  
**Status:** Replicated, Reconciled, and Physically Calibrated  

---

## 1. Executive Summary

We performed an independent mathematical, statistical, and pixel-level kinematic audit across Program N's E1 dataset (`work/codex-api-4/t223/e1_complete` and native MP4 examples):
1. **Mathematical & Statistical Replication of Finding #4974**:
   - Independently decoded native MP4s and confirmed float64 BT.601 luma `INTER_AREA` to `208x120` frame-difference metric $M$, matching recorded values to machine precision (`N_E1_blue_fast_s201`: $M = 0.9079342877952555$).
   - Confirmed the 16-seed ANOVA decomposition: Seed explains $\eta^2 = 0.6543$ (95% CI $[0.1322, 0.7783]$), Prompt explains $\eta^2 = 0.2129$ (95% CI $[0.1242, 0.6157]$), and Seed $\times$ Prompt interaction explains $\eta^2 = 0.1328$.
   - Confirmed that "fast" wording reliably increases whole-frame image change in **16/16 seeds** ($+0.7560 \pm 0.1233$ gray levels/native transition, bootstrap 95% CI $[0.5341, 1.0036]$).

2. **Color Compliance Replication of Finding #4935**:
   - Color prompt compliance is 100% (red prompt renders exclusively red bobs with 0 blue pixels; blue prompt renders blue bobs with minimal/zero red pixels, $p < 10^{-18}$).

3. **Physical Resolution of the Paradox (Reconciling #4974 and #4935)**:
   - Raj reported that Nano ignores text for swing speed ($0/16$ change in period; mean $\Delta T = 0.01$ s via `pend_acf`), while Codex-api-4 reported that "fast" wording increases image change $M$ across all 16 seeds ($p = 0.0001$).
   - **Continuous pixel tracking of the pendulum bob reveals why**:
     - Under "slow" wording ("taking about three seconds"), the pendulum remains virtually static ($\Delta x = 4.0$ px, $\Delta y = 6.0$ px in `red_slow`; $\Delta x = 9.2$ px, $\Delta y = 39.6$ px in `blue_slow`).
     - Under "fast" wording ("taking about half a second"), the model does **NOT** increase the frequency of a rigid horizontal pendulum swing. Instead, it triggers an **unphysical vertical rod stretching / elastic pumping mode** ($\Delta y = 221.6$ px in `red_fast`, $\Delta y = 377.7$ px in `blue_fast` across an 832x480 frame) while horizontal excursion remains pinned ($\Delta x = 4.7$ px in `red_fast`).
     - Concurrently, bob area expands by $+127\%$ (mean area $627.4 \to 1426.6$ px² in red).
   - **Conclusion**: The increased frame-difference magnitude $M$ under "fast" text is **not** a faster physical pendulum swing, but non-rigid visual deformation, rod elongation, and object morphing. This unifies Raj's period lock with Codex-api-4's image-change increase and provides direct kinematic corroboration for Scout-1 Hypothesis D and Finding 10.

---

## 2. Seed 201 Kinematic Audit Table

| Clip | Color Prompt | Speed Prompt | Image Change $M$ | Tracked Frames | $x$ Range | $y$ Range | Mean Bob Area | Dominant Motion Mode |
|---|---|---|---:|:---:|---:|---:|---:|---|
| `N_E1_red_slow_s201.mp4` | Red | Slow (3 s) | 0.2319 | 93/93 | 4.0 px | 6.0 px | 627.4 px² | Near-static stillness |
| `N_E1_red_fast_s201.mp4` | Red | Fast (0.5 s) | 0.5954 | 93/93 | 4.7 px | **221.6 px** | **1426.6 px²** | **Vertical rod stretching / pumping** |
| `N_E1_blue_slow_s201.mp4` | Blue | Slow (3 s) | 0.2751 | 93/93 | 9.2 px | 39.6 px | 1295.5 px² | Low-amplitude drift |
| `N_E1_blue_fast_s201.mp4` | Blue | Fast (0.5 s) | 0.9079 | 93/93 | 28.2 px | **377.7 px** | **1508.0 px²** | **Severe vertical deformation / elongation** |

---

## 3. Files and Reproducibility

- `audit_e1_kinematics.py`: Runnable audit script.
- `e1_kinematic_audit.json`: Audited values, metrics, and kinematic tables.
