# Task 231: Independent Replication and Review of Finding #4505

**Target Finding**: Finding #4505 (poornima-3, exploratory follow-up to Task 217)  
**Author**: `poornima-3`  
**Reviewer**: `agy-3` (Shift 42)  
**Target Claim**: *"With QT, Nano's ball goes quiet about 2.6× later than the real GAUGE ball from the same input frame. Without QT (F) it mostly never goes quiet."*  
**Review Verdict**: **replicated** (exact numerical agreement on author's data + independent cross-grid replication on mixed-GPU clips + continuous rolling-window validation + ANOVA variance decomposition + ball-growth stratification).

---

## 1. Executive Summary

Finding #4505 establishes a critical temporal fact for Cosmos3-Nano and Charter Deliverable 1:
While appending a timed dissipative prompt clause (`QT`: *"within about one and a half seconds, the ball comes to rest on the plank and stays still..."*) successfully resolves the perpetual limit-cycle bouncing of baseline Cosmos (`F`), **it does NOT produce settling within 1.5 seconds**. Instead, Cosmos3-Nano exhibits an intrinsic temporal delay, settling at **3.75 s to 4.00 s**—a **~2.6× to 2.8× slowdown** relative to real physical video (**1.43 s**).

This independent replication verifies:
1. **Exact Numerical Replicability**:
   - Re-implementation of author's seed-cluster bootstrap on published `quiet2_results.json` reproduces author's figures to the second decimal:
     - Real continuations: **1.43 ± 0.01 s** (1.42 s on `b1dd33_lb`, 1.44 s on `vaert`/`orig93`/`b2`).
     - Nominal Threshold (TH = 2.0): Median **3.75 s**, 95% seed-cluster CI **[3.00, 6.00] s**, Ratio vs Real **2.62× [2.10, 4.20]×**.
     - Loose Threshold (TH = 2.5): Median **3.50 s [2.50, 5.00] s**, Ratio vs Real **2.45× [1.75, 3.50]×**.
     - Strict Threshold (TH = 1.5): Median **6.25 s [3.50, 99.00] s**, Ratio vs Real **4.37× [2.45, 69.23]×** (13/30 never reach TH 1.5).
     - Baseline `F`: 25/30 (83.3%) never quiet (median = $\infty$).
     - Neutral `N`: 19/30 (63.3%) never quiet (median = $\infty$).
2. **Cross-Grid / Cross-Stack Replication**:
   - Decoded and evaluated all 90 native 189-frame MP4 clips from the independent mixed-GPU grid (`raj-api-1`):
     - Prompt `QT`: Median **4.00 s** (TH = 2.0, 2.80× real) and **3.75 s** (TH = 2.5, 2.62× real).
     - Prompt `F`: 24/30 (80.0%) never quiet (median = $\infty$).
     - Prompt `N`: 17/30 (56.7%) never quiet (median = $\infty$).
3. **Lattice Artifact Ruled Out (Rolling-Window Check)**:
   - Evaluated a continuous rolling 12-frame window (1.0 s persistence) to ensure the 0.5 s discrete binning was not an artifact of boundary quantization.
   - In clean settled clips (`clean_settle2`), rolling window median is **3.96 s** (TH = 2.0) and **3.00 s** (TH = 2.5), fully matching discrete binning.
4. **ANOVA Variance Decomposition (Corroborating Program N)**:
   - Within the `QT` condition, noise seed explains **49.1% of the total variance** in time to quiet ($\eta^2_{\text{seed}} = 0.491$), while input image explains only **6.1%** ($\eta^2_{\text{img}} = 0.061$).
   - The initial noise draw is **8.1× more powerful** than the input conditioning image in determining the exact settle timing.
5. **Ball Growth Stratification**:
   - Normal-sized balls (`clean_settle2`, end-ratio < 1.6×, $n=21$) settle with median **4.0 s** (discrete) and **3.96 s** (rolling) at TH = 2.0.
   - Giant growth balls (`growth_end == 1`, $n=4$) settle with median **3.5 s** (discrete) and **3.44 s** (rolling).
   - The ~2.6× slowdown is NOT driven by the giant ball growth mode.

---

## 2. Master Statistical Table

| Cohort | Grid / Stack | Threshold (TH) | Median Time to Quiet (s) | 95% Seed-Cluster CI | Ratio vs Real (1.43 s) | Non-Settling Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Real Continuations** | Physical Video | 1.5 – 2.5 | **1.43 s** | [1.42, 1.44] | **1.00×** | 0/6 (0.0%) |
| **Nano QT (Author)** | q8 Karras | 2.0 (Nominal) | **3.75 s** | [3.00, 6.00] | **2.62× [2.10, 4.20]×** | 6/30 (20.0%) |
| **Nano QT (Author)** | q8 Karras | 2.5 (Loose) | **3.50 s** | [2.50, 5.00] | **2.45× [1.75, 3.50]×** | 4/30 (13.3%) |
| **Nano QT (Author)** | q8 Karras | 1.5 (Strict) | **6.25 s** | [3.50, 99.00] | **4.37× [2.45, 69.23]×** | 13/30 (43.3%) |
| **Nano QT (Ours)** | Mixed GPU | 2.0 (Nominal) | **4.00 s** | [3.25, 99.00] | **2.80× [2.27, 69.23]×** | 11/30 (36.7%) |
| **Nano QT (Ours)** | Mixed GPU | 2.5 (Loose) | **3.75 s** | [2.50, 99.00] | **2.62× [1.75, 69.23]×** | 11/30 (36.7%) |
| **Nano F (Baseline)** | q8 Karras | 2.0 (Nominal) | **> 7.88 s** | [—] | **$\infty$** | 25/30 (83.3%) |
| **Nano N (Neutral)** | q8 Karras | 2.0 (Nominal) | **> 7.88 s** | [—] | **$\infty$** | 19/30 (63.3%) |
| **QT Clean Settle** | Mixed GPU | 2.0 (Discrete) | **4.00 s** | [3.00, 6.50] | **2.80×** | 6/21 (28.6%) |
| **QT Clean Settle** | Mixed GPU | 2.0 (Rolling) | **3.96 s** | [2.50, 6.17] | **2.77×** | 7/21 (33.3%) |

---

## 3. Evidence Artifacts

- **Publication Figure**: `plots/figure_quiet_time_replication.png` (4-panel synthesis):
  - (a) Real vs Nano Settle Timing distributions at TH = 2.0;
  - (b) Threshold Sensitivity Curve (TH 1.5 to 2.5);
  - (c) Seed-Locking of Settle Time ($\eta^2_{\text{seed}} = 0.491$);
  - (d) Ball Growth Stratification & Rolling-Window Check.
- **Evaluation Script**: `evaluate_quiet_time.py` (executed natively on `board` via `cosmos-venv`).
- **Plotting Script**: `plot_replication.py`.
- **Master Dataset**: `replicate_4505_results.json` (per-clip metrics, rolling and discrete times across all 8 thresholds).
- **Author Source Dataset**: `author_quiet2_results.json` (mirrored from `swarm@board:~/jobs/poornima-3/t141px/quiet2_results.json`).
