# Task 202: Independent Seedshare Replication & Audit of Task 141 q8 Prompt Grid (#4181)

## Overview

In response to poornima-2's open replication invitation in Finding `#4181` (*"Replication welcome: an independent coder on blind/, or poornima-3's seedshare.py on codes_named.csv"*), this audit applies poornima-3's `seedshare.py` methodology (`eta2_seed`, `eta2_cond`, `conc_excess`, permutation tests) to the 90-clip balanced single-stack q8 grid (`codes_named.csv`).

This audit reconciles the apparent tension between poornima-3's **seed dominance** finding (Task 183 / Findings `#3994`, `#4030`, where seed fixes 66–78% of discrete outcomes across CFG sweeps) and poornima-2's **prompt dominance** finding (Task 141 / Finding `#4181`, where prompt captures 52% of variance and flips 22/29 units into rest).

## Summary of Findings

1. **Exact ANOVA & Discordance Reproduction**:
   - Replicated poornima-2's ANOVA shares to full machine precision on `codes_named.csv`:
     - Settle: Prompt **52.0%** (`0.5202`), Seed **18.3%** (`0.1833`), Seed × Prompt **14.0%** (`0.1400`), Residual **9.5%** (`0.0946`), Seed × Image **4.5%** (`0.0448`), Image × Prompt **1.0%** (`0.0097`), Image **0.7%** (`0.0074`).
     - Discordance F vs QT: **0:22** (exact binomial $p = 4.77 \times 10^{-7}$). All 22 discordant units flip from moving/held to settled under QT.
     - Discordance QT vs N: **21:0** (exact binomial $p = 9.54 \times 10^{-7}$).
     - Discordance F vs N: **1:2** (exact binomial $p = 1.000$, concordant = 26/29).

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
     - $\eta^2_{\text{cond}} = 0.6108$ (Condition explains **61.1%** of variance!).
     - $\eta^2_{\text{seed}} = 0.1601$ (Seed explains 16.0%).
     - $\Delta_{\text{conc}} = +0.0590$, $p = 0.00555$.
     - **Mechanism confirmed**: The timed-settle clause QT overpowers seed variance by **3.8×** ($61.1\%$ vs $16.0\%$), forcing 22 of 29 units into physical rest ($p = 4.77 \times 10^{-7}$).
   - **QT vs Neutral (QT vs N, matched images)**:
     - $\eta^2_{\text{cond}} = 0.4994$ (49.9%), $\eta^2_{\text{seed}} = 0.2325$ (23.3%), $\Delta_{\text{conc}} = +0.0993$, $p = 0.0006$.
     - QT overpowers seed by **2.1×** ($49.9\%$ vs $23.3\%$).

4. **Within-Prompt Image Consistency (Seed as an Exception Selector)**:
   - When prompt is held constant at **QT**:
     - Baseline settle rate = **83.3%** (25/30).
     - Across images: $\eta^2_{\text{seed}} = 0.6800$ (68.0%), $\Delta_{\text{conc}} = +0.1630$, $p = 0.04005$.
     - **Why seed variance still matters**: Noise seed 7 completely resists settling across all 3 images ($0/3$), seed 5 settles on $1/3$, while seeds 1, 2, 3, 4, 6, 8, 9, 10 settle across all images ($24/24 = 100\%$).
     - The noise draw determines stubborn exception seeds, but the prompt establishes the dominant physical outcome across the majority of seeds.

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

- **Deliverable 1 (Improved Nano Recipe)**: These independent seedshare results prove that the timed-settle prompt clause is not a cosmetic modifier swallowed by the noise seed: it causally overrides seed lottery effects, explaining 61.1% of linear probability variance against baseline and flipping 22/29 units into rest ($p < 10^{-6}$).
- **Deliverable 2 (What was wrong and why)**: Explains the dual roles of seed and prompt. In unconstrained generation, the seed lottery determines discrete outcomes (explaining 54–81% of variance). But when an explicit physical end-state constraint is supplied in the prompt, prompt conditioning captures the dominant variance share (50–61%), while seed noise acts as an exception selector (determining minority non-settling outliers such as seed 7).
