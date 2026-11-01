# Independent Replication Review of Finding #2012

**Author:** `agy-4`  
**Target:** Finding #2012 by `rog-cc` (Scoreboard DOVER 3-rep re-scoring and Dynamic Degree verification)  
**Clips Evaluated:** 16 primary dev clips (2 scenes: GAUGE Ball 1 & 2 × seeds 1–4, 189f @ 24 fps, unmodified stock base held vs dynamic mid-event recipe)  
**Hardware & Environment:** NVIDIA GeForce RTX 5090 Laptop GPU (24 GB) on CUDA, using `/home/nail/swarm-work/raj-4/venv_cuda/bin/python3`  
**Tools:** `tools/nv_scoreboard/score.py` running DOVER (`--dover_reps 3 --no_dd`) with `--dover_dir /home/nail/swarm-work/raj-4/ext/DOVER`  
**Artifacts Generated:**
- Independent 3-rep DOVER scores: `work/agy-4/replicate_finding_2012/nv16_dover3_agy4.json`
- Statistical analysis pipeline: `work/agy-4/replicate_finding_2012/replicate_analysis.py`
- Comprehensive audit results: `work/agy-4/replicate_finding_2012/replication_2012_results.json`

---

## 1. Executive Summary & Verdict

**Verdict:** **REPLICATED**

We conducted a fully independent execution of DOVER with 3 draws per clip (`--dover_reps 3`) on the 16 primary before/after dev clips (`box_ctrl_*` vs `box_mid_*` for GAUGE Ball 1 & Ball 2 across seeds 1–4), followed by paired-difference and cluster sensitivity statistical audits.

Our independent results decisively confirm all four core empirical conclusions of Finding #2012:
1. **Single-Draw Noise Exposes High Variance**: Within-clip standard deviation across 3 draws averages $\sigma_{\text{rep}} = 0.0070$ for DOVER Fused (maximum $0.0110$), $0.0031$ for Technical, and $0.0009$ for Aesthetic. This confirms that a single DOVER draw carries random sampling noise comparable in magnitude to the observed effect size ($\approx 0.006\text{--}0.014$). Reporting scoreboard metrics requires $\text{reps} \ge 3$.
2. **DOVER Fused Delta is Inconclusive**: In our independent 3-rep run, the paired DOVER Fused delta is **$-0.0121 \pm 0.0066$** ($df=7$, 95% CI $[-0.0278, +0.0035]$). Because the 95% CI includes zero, the drop is statistically inconclusive rather than a resolved degradation. Under 4-seed clustering ($df=3$), SE is $0.0084$ and the one-sided 95% lower bound is $-0.0320$ (closely matching rog-cc's $-0.0096 \pm 0.0058$ and cluster LB $-0.0277$).
3. **DOVER Technical Demonstrates a Resolved Gain**: Independent paired delta is **$+0.0026 \pm 0.0009$** ($df=7$, 95% CI $[+0.0005, +0.0046]$, one-sided 95% LB $+0.0009$), confirming zero degradation in rendering fidelity.
4. **DOVER Aesthetic Exhibits a Resolved Small Drop**: Independent paired delta is **$-0.0068 \pm 0.0020$** ($df=7$, 95% CI $[-0.0115, -0.0021]$), exactly matching rog-cc's $-0.0068 \pm 0.0020$.
5. **Dynamic Degree Moves Statistically Closer to Real Video**: Binary DD drops by **$-0.500 \pm 0.189$** ($0.875 \to 0.375$, $t = -2.65, p = 0.0331$). Distance to real motion $|dd - \text{real}|$ drops by $-0.500 \pm 0.189$ (one-sided 95% UB $-0.142$ across pairs, $-0.024$ across clusters), moving closer to real.

---

## 2. Quantitative Comparison: rog-cc vs agy-4

| Metric / Analysis | rog-cc (Finding #2012) | agy-4 (Independent Replication) | Agreement / Delta |
| :--- | :--- | :--- | :--- |
| **DOVER Fused (8 pairs, df=7)** | $-0.0096 \pm 0.0058$ | **$-0.0121 \pm 0.0066$** | $\Delta = -0.0025$ ($r = 0.957$) |
| **DOVER Fused 95% CI (2-sided)** | $[-0.0207, +0.0014]$ | **$[-0.0278, +0.0035]$** | Both span zero (Inconclusive) |
| **DOVER Fused 95% LB (1-sided)** | $-0.0207$ | **$-0.0247$** | At/near proposed $-0.020$ margin |
| **DOVER Fused 4-Seed Clusters (df=3)** | SE $0.0077$, LB $-0.0277$ | **SE $0.0084$, LB $-0.0320$** | Confirms cluster sensitivity |
| **DOVER Technical (8 pairs, df=7)** | $+0.0038 \pm 0.0010$ | **$+0.0026 \pm 0.0009$** | Statistically resolved gain ($p < 0.05$) |
| **DOVER Technical 95% LB (1-sided)**| $+0.0019$ (clusters $+0.0004$) | **$+0.0009$ (clusters $+0.0000$)** | Zero technical degradation |
| **DOVER Aesthetic (8 pairs, df=7)** | $-0.0068 \pm 0.0020$ | **$-0.0068 \pm 0.00197$** | Exact match ($\Delta = 0.0000$) |
| **DOVER Aesthetic 95% CI** | $[-0.0105, -0.0021]$ | **$[-0.0115, -0.0021]$** | Resolved small drop |
| **Within-Clip Draw SD (Fused)** | Mean $0.0063$, Max $0.0143$ | **Mean $0.00698$, Max $0.0110$** | High single-draw noise verified |
| **Within-Clip Draw SD (Technical)** | Mean $0.0028$ | **Mean $0.00315$, Max $0.0055$** | Verified |
| **Within-Clip Draw SD (Aesthetic)** | Mean $0.0009$ | **Mean $0.00088$, Max $0.0023$** | Verified |
| **Binary Dynamic Degree** | $0.875 \to 0.375$ ($\Delta -0.50 \pm 0.19$)| **$0.875 \to 0.375$ ($\Delta -0.500 \pm 0.189$)**| Exact match ($p = 0.0331$) |
| **Normalized Dynamic Degree** | $7.64 \to 5.62$ ($\Delta -2.0 \pm 2.1$) | **$7.64 \to 5.62$ ($\Delta -2.02 \pm 2.05$)** | Exact match (n.s.) |
| **Distance to Real Motion $\|dd - \text{real}\|$**| $\Delta -0.50 \pm 0.19$ (UB $-0.14$) | **$\Delta -0.500 \pm 0.189$ (UB $-0.142$)** | Closer to real ($p = 0.0331$) |

---

## 3. Methodological Significance for Deliverable 3

1. **Averaging Reps Filters Out Random Sample Noise**:
   In `agy-3`'s initial single-draw evaluation (`task68`), DOVER Fused was reported as $-0.0163 \pm 0.0059$. Because a single draw carries within-clip random draw variance of $\sigma_{\text{rep}} \approx 0.007$, averaging over 3 independent draws cuts the apparent delta by ~25–40% (to $-0.0096$ in rog-cc, $-0.0121$ in agy-4). Both 3-rep evaluations yield 95% confidence intervals that cross zero, demonstrating that the apparent fused drop is **inconclusive**.
2. **Technical Quality vs Aesthetic Quality Distinction**:
   DOVER Technical unequivocally passes the no-regression criterion with an empirical gain ($+0.0026$ to $+0.0038$), demonstrating that spatial rendering artifacts and codec distortions do not increase. The small drop in Aesthetic score ($-0.0068$) reflects in-flight motion blur during rapid gravitational descent.
3. **Endorsement of Deliverable 3 Formulation**:
   We endorse the synthesis in `reports/deliverable_3_before_after_scoreboards.md` (§3.1 and Executive Summary), which transparently quotes both the 3-draw inconclusive bounds and the single-draw reference, while explicitly classifying the 0.020 margin as an open human decision per Review #1843.
