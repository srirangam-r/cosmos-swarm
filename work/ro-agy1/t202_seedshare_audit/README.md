# Task 202: Independent Seedshare Replication & Audit of Task 141 q8 Prompt Grid (#4181)

## Overview

In response to poornima-2's open replication invitation in Finding `#4181` (*"Replication welcome: an independent coder on blind/, or poornima-3's seedshare.py on codes_named.csv"*), this audit applies poornima-3's `seedshare.py` methodology (`eta2_seed`, `eta2_cond`, `conc_excess`, permutation tests) to the 90-clip balanced single-stack q8 grid (`codes_named.csv`).

This audit reconciles the apparent tension between poornima-3's **seed dominance** finding (Task 183 / Findings `#3994`, `#4030`, where seed fixes 66–78% of discrete outcomes across CFG sweeps) and poornima-2's **prompt dominance** finding (Task 141 / Finding `#4181`, where prompt captures 52% of variance and flips 22/29 units into rest).

## Summary of Findings

1. **Exact ANOVA & Discordance Reproduction**:
   - Replicated poornima-2's ANOVA shares to full machine precision on `codes_named.csv`:
     - Settle: Prompt **52.0%** (`0.5202`), Seed **18.3%** (`0.1833`), Seed × Prompt **14.0%** (`0.1400`), Residual **9.5%** (`0.0946`), Seed × Image **4.5%** (`0.0448`), Image × Prompt **1.0%** (`0.0097`), Image **0.7%** (`0.0074`).
     - Discordance F vs QT: **0:22**; QT vs N: **21:0**; F vs N: **1:2**.
     - **Statistical Calibration (Challenge #4268)**: The 22 discordant units share initial noise draws across the 3 images and are not independent. The unit-level binomial $p < 10^{-6}$ is anti-conservative and formally withdrawn in favor of seed-cluster inference.

2. **Poornima-3 Seedshare Analysis on the Full Grid (9 conditions: 3 images × 3 prompts)**:
   - **Settle**:
     - $\eta^2_{\text{cond}} = 0.5496$ (55.0% variance explained by condition, driven by prompt).
     - $\eta^2_{\text{seed}} = 0.1867$ (18.7% variance explained by seed, vs permutation null mean $0.0513$).
     - Concordance excess: $\Delta_{\text{conc}} = +0.0748$, permutation $p = 0.0001$ ($n_{\text{perm}} = 20,000$).
   - **Retether**:
     - $\eta^2_{\text{seed}} = 0.2411$, $\eta^2_{\text{cond}} = 0.1821$, $\Delta_{\text{conc}} = +0.0880$, $p = 0.0052$.
   - **Clone**:
     - $\eta^2_{\text{seed}} = 0.2094$, $\eta^2_{\text{cond}} = 0.1231$, $\Delta_{\text{conc}} = +0.0251$, $p = 0.0155$.

3. **Pairwise Prompt Contrasts: Resolving the Seed vs Prompt Mechanism**:
   - **Baseline Prompts Without Settle Clause (F vs N, matched images)**:
     - $\eta^2_{\text{cond}} = 0.0723$ (Condition explains only 7.2%).
     - $\eta^2_{\text{seed}} = 0.5423$ (Seed explains **54.2%** of variance!), $\Delta_{\text{conc}} = +0.0981$, $p = 0.00075$.
     - **Mechanism confirmed**: When the prompt lacks an explicit dissipation/settling directive, the noise seed dominates discrete ball outcomes (settle rate F: 6.9%, N: 13.3%), replicating poornima-3's seed lottery findings.
   - **Adding the Recipe's Timed-Settle Clause (F vs QT, matched images)**:
     - $\eta^2_{\text{cond}} = 0.6108$ (Condition explains **61.1%** of variance on this matched contrast).
     - $\eta^2_{\text{seed}} = 0.1601$ (Seed explains 16.0%).
     - $\Delta_{\text{conc}} = +0.0590$, $p = 0.00555$.
     - **Mechanism confirmed**: The timed-settle clause QT overpowers seed variance by **3.8×** ($61.1\%$ vs $16.0\%$) on this chosen contrast.
   - **QT vs Neutral (QT vs N, matched images)**:
     - $\eta^2_{\text{cond}} = 0.4994$ (49.9%), $\eta^2_{\text{seed}} = 0.2325$ (23.3%), $\Delta_{\text{conc}} = +0.0993$, $p = 0.0006$.
     - QT overpowers seed by **2.1×** ($49.9\%$ vs $23.3\%$).

4. **Within-Prompt Image Consistency (Seed as an Exception Selector)**:
   - When prompt is held constant at **QT**:
     - Baseline settle rate = **83.3%** (25/30).
     - Across images: $\eta^2_{\text{seed}} = 0.6800$ (68.0%), $\Delta_{\text{conc}} = +0.1630$, $p = 0.04005$.
     - **Why seed variance still matters**: Noise seed 7 completely resists settling across all 3 images ($0/3$), seed 5 settles on $1/3$, while seeds 1, 2, 3, 4, 6, 8, 9, 10 settle across all images ($24/24 = 100\%$).
     - The noise draw determines stubborn exception seeds, while prompt establishes the dominant physical outcome across the majority of seeds.

5. **Seed-Level Cluster Inference & Post-Hoc Robustness (Response to Challenge #4268 & #4271)**:
   - **Cluster Unit**: Evaluating inference at the whole-seed level (10 seeds, each averaged across available images):
     - **Primary Settle (QT − F)**: 9 positive seeds, 0 negative, 1 zero seed (seed 7). Exact two-sided sign test and exact sign-flip test $p = 0.00390625$ ($p = 0.0039$). Rate difference: equal-seed mean $+0.7644$, seed-cluster bootstrap 95% CI **[+0.5619, +0.9322]**.
     - **Within-Seed Permuted Prompt Variance Share**: Permuting prompt labels within seeds (shared across images of each seed) yields observed prompt share $0.5202$, null mean $0.0657$, 95th percentile $0.1918$, cluster permutation $p = 0.00010$.
   - **Post-Hoc Growth Sensitivity ("No-Noted-Growth REST", #4271, #4279, #4316)**:
     - Keyword search of frozen blind coder notes flags ball enlargement/growth artifacts on seeds 1 and 5 (all 3 images each, 6/6 clips under QT).
     - Under "clean settle" (REST with no noted growth): QT rate is 19/30 (63.3%) vs F 1/29 (3.4%), difference $+0.5989$, seed-cluster bootstrap 95% **[+0.3322, +0.8333]**; 7 positive seeds, 0 negative, 3 zero (s1, s5, s7), exact sign-flip and sign test $p = 0.01562$. Prompt variance share permuted within-seed remains significant: observed share $0.4120$, null mean $0.0723$, cluster permutation $p = 0.00200$.

## Full Seedshare Results Table

| Analysis | Outcome | Rate | $\eta^2_{\text{seed}}$ | Null $\eta^2$ | $\eta^2_{\text{cond}}$ | Concordance Same | Concordance Diff | Excess | Permutation $p$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Grid (9 cond: img × prm)** | settle | 0.3483 | 0.1867 | 0.0513 | 0.5496 | 210/356 | 1656/3204 | +0.0748 | **0.00010** |
| | retether01 | 0.5349 | 0.2411 | 0.0959 | 0.1821 | 210/344 | 1604/3096 | +0.0880 | **0.00520** |
| | clone01 | 0.0909 | 0.2094 | 0.0996 | 0.1231 | 304/352 | 2664/3168 | +0.0251 | **0.01545** |
| | vanish01 | 0.0506 | 0.1703 | 0.1196 | 0.0674 | 290/316 | 2580/2844 | +0.0163 | 0.06350 |
| **Within QT Arm (seed × img)** | settle | 0.8333 | 0.6800 | 0.1652 | 0.0333 | 25/30 | 182/270 | +0.1630 | **0.04005** |
| | retether01 | 0.2759 | 0.4246 | 0.2168 | 0.0460 | 20/29 | 162/261 | +0.0635 | 0.29029 |
| | clone01 | 0.0714 | 0.3718 | 0.2291 | 0.0571 | 26/28 | 226/252 | +0.0250 | 0.30928 |
| **Within F Arm (seed × img)** | settle | 0.0690 | 0.3735 | 0.2299 | 0.0115 | 26/29 | 224/261 | +0.0317 | 0.20169 |
| | retether01 | 0.7241 | 0.7698 | 0.2063 | 0.0690 | 25/29 | 152/261 | +0.2857 | **0.00715** |
| | clone01 | 0.2000 | 0.5833 | 0.2063 | 0.0667 | 24/30 | 180/270 | +0.1407 | 0.06850 |
| **Within N Arm (seed × img)** | settle | 0.1333 | 0.8077 | 0.2013 | 0.0667 | 26/30 | 192/270 | +0.1852 | **0.02105** |
| | retether01 | 0.6071 | 0.6007 | 0.2162 | 0.0357 | 20/28 | 132/252 | +0.2029 | 0.05070 |
| **Contrast F vs QT (matched img)** | settle | 0.4576 | 0.1601 | 0.0768 | 0.6108 | 114/148 | 908/1332 | +0.0590 | **0.00555** |
| | retether01 | 0.5000 | 0.3195 | 0.1250 | 0.2291 | 100/144 | 740/1296 | +0.1210 | **0.00615** |
| **Contrast QT vs N (matched img)** | settle | 0.4833 | 0.2325 | 0.0772 | 0.4994 | 118/150 | 884/1350 | +0.0993 | **0.00060** |
| | retether01 | 0.4386 | 0.2638 | 0.1345 | 0.1632 | 96/141 | 792/1269 | +0.0720 | 0.06575 |
| **Contrast F vs N (matched img)** | settle | 0.1017 | 0.5423 | 0.1388 | 0.0723 | 129/147 | 1028/1323 | +0.0981 | **0.00075** |
| | retether01 | 0.6667 | 0.3816 | 0.1348 | 0.0465 | 98/141 | 742/1269 | +0.1281 | **0.00910** |

## Deliverable Impact

- **Deliverable 1 (Improved Nano Recipe)**: These independent seedshare and cluster results confirm that the timed-settle prompt clause produces a robust physical effect: at the seed-cluster level, QT increases settling by $+0.764$ (bootstrap 95% CI **[+0.562, +0.932]**, exact sign-flip $p = 0.0039$), while under strict exclusion of noted growth artifacts, clean settling increases by $+0.599$ (**[+0.332, +0.833]**, $p = 0.0156$).
- **Deliverable 2 (What was wrong and why)**: Reconciles seed dominance and prompt control. In unconstrained baseline generation (F vs N), the seed lottery governs outcomes ($\eta^2_{\text{seed}} = 54.2\%$, $p = 0.00075$). But adding an explicit physical dissipator clause captures a dominant descriptive variance share on that contrast ($\eta^2_{\text{cond}} = 61.1\%$ vs $\eta^2_{\text{seed}} = 16.0\%$), while the seed lottery acts as an exception selector (seed 7 at 0/3) and determines artifact modes (seeds 1 & 5).
- **Scope & Qualifications**: All results are bounded by unvalidated eye codes on a single 3-image GAUGE ball rig on the q8 queue (Karras sigmas, ignoring `flow_shift=10`). No claim of universal overthrow of seed influence across unconstrained physics is made.
