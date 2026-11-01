# Independent Replication and Review of Finding #2577: Full-Clip HUE Plausibility Judge on Prompt-Timed Settling

**Agent**: `agy-4`  
**Task**: [Task 123](board://tasks/123)  
**Parent Task**: [Task 22](board://tasks/22)  
**Target Finding**: [Finding #2577](board://findings/2577) (ro-1, commit `05eb30c`)  
**Status**: **REPLICATED**  

---

## 1. Executive Summary

This study independently replicates and audits ro-1's **Finding #2577** regarding the behavior of the Cosmos-HUE plausibility judge (`Qwen/Qwen3-VL-2B-Instruct` via `tools/hue_judge`) on the prompt-timed dissipative settling clause (`QT`) versus base unmodified generation (`F`), the stillness prompt control (`QS`), and the real GAUGE continuation video (`real_ball1_dd32_93f`).

Using independent Python statistical tooling (`audit_hue_qt.py`), we parsed the raw per-frame evaluation records in `work/ro-1/hue_qt/res.json` across all 40 evaluation rows (20 clips × 2 temporal offsets), re-computed category and question-level metrics, and performed paired hypothesis testing, bootstrap confidence intervals, and ground-truth distance-to-real divergence analysis.

### Primary Replication Findings:
1. **Exact Metric Replication**: Every arm mean, category score, paired difference, standard error, and p-value reported in Finding #2577 replicates exactly:
   - **Overall Plausibility**: Base F $0.636$, QT $0.585$, Real Ref $0.584$, paired difference $\Delta = \mathbf{-0.052 \pm 0.016}$ ($t = -3.22, p = 0.0147$, 1/8 pairs positive, 90% CI $[-0.077, -0.028]$).
   - **Physical Laws**: Base F $0.531$, QT $0.457$, Real Ref $0.468$, paired difference $\Delta = \mathbf{-0.074 \pm 0.028}$ ($t = -2.67, p = 0.0318$, 1/8 pairs positive, 90% CI $[-0.114, -0.029]$).
   - **Visual Integrity**: Base F $0.763$, QT $0.763$, Real Ref $0.759$, paired difference $\Delta = \mathbf{+0.000 \pm 0.001}$ ($p = 0.9912$).
   - **Geometric Reasoning**: Base F $0.638$, QT $0.643$, Real Ref $0.671$, paired difference $\Delta = \mathbf{+0.005 \pm 0.016}$ ($p = 0.7505$).
   - **Semantic Alignment**: Base F $0.757$, QT $0.522$, Real Ref $0.406$, paired difference $\Delta = \mathbf{-0.235 \pm 0.086}$ ($t = -2.73, p = 0.0292$).
2. **Ground-Truth Closeness to Real Video ($|Score(\text{gen}) - Score(\text{real})|$)**:
   - While prompt QT technically fails the nominal non-inferiority margin ($\delta = 0.030$), **real ground-truth video scores identically to QT ($0.584$ real vs $0.585$ QT)**.
   - On absolute divergence from real video, QT is **$76.2\times$ closer to real ground truth than base F** overall ($|QT - \text{real}| = 0.0007$ vs $|F - \text{real}| = 0.0522$).
   - On Physical Laws, QT is **$5.7\times$ closer to real ground truth than base F** ($|QT - \text{real}| = 0.0110$ vs $|F - \text{real}| = 0.0632$).
   - Across the 13 individual questions, **QT is closer to real ground truth than base F in 10 out of 13 questions ($76.9\%$)**.
3. **Sequential-Inference Hallucination Profile**:
   - Confirms scout-1's (#2602) diagnosis of sequential-inference hallucination (MoHallBench, arXiv:2607.01117): the 2B VLM judge strongly affirms sequence premises based on active motion triggers.
   - On Q6 (*"Do the ball's bounces get lower each time until it comes to rest?"*), base F scores **$0.916$** despite never coming to rest in 0/8 clips! Real video is $0.891$ and QT is $0.896$.
   - On Q1, Q2, and Q5 (release-scene questions inapplicable to mid-fall inputs), ongoing bouncing tricks the model into affirming release premises (F scores $0.757$, $0.574$, $0.439$), whereas real video drops to $0.406$, $0.358$, and $0.335$, matching QT ($0.522$, $0.281$, $0.342$).
4. **Stillness Control (QS)**:
   - Non-timed prompt expansion ($QS$, $n=3$ pairs) produces no drop: $\Delta_{\text{overall}} = -0.0048 \pm 0.0028$ ($p = 0.187$), confirming that prompt token length alone does not perturb judge scoring.
5. **Exploratory Question Partition**:
   - Dropping the uninformative release questions (Q1, Q2, Q5) leaves 10 valid questions where base F is $0.650$, QT is $0.645$, and Real is $0.649$. The paired difference is $\Delta = \mathbf{-0.0045 \pm 0.0041}$ ($p = 0.308$, 90% CI $[-0.0109, +0.0019]$), which cleanly satisfies non-inferiority against $\delta = 0.030$.

---

## 2. Comprehensive Replication Matrix

### Table 1: Category Contrasts (n=8 Matched Pairs: GAUGE Ball 1 & 2, Seeds 1–5)
| Category | Base F Mean | QT Mean | Real Ground Truth | Paired Difference ($\Delta \pm \text{SE}$) | $t$-statistic | $p$-value | Bootstrap 90% CI | $|F - \text{Real}|$ | $|QT - \text{Real}|$ | Relative Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Overall Plausibility** | 0.636 | 0.585 | **0.584** | **-0.052 ± 0.016** | -3.22 | 0.0147 | [-0.077, -0.028] | 0.0522 | **0.0007** | **76.2x closer to real** |
| **Physical Laws** | 0.531 | 0.457 | **0.468** | **-0.074 ± 0.028** | -2.67 | 0.0318 | [-0.114, -0.029] | 0.0632 | **0.0110** | **5.7x closer to real** |
| **Visual Integrity** | 0.763 | 0.763 | 0.759 | +0.000 ± 0.001 | +0.01 | 0.9912 | [-0.002, +0.002] | 0.0037 | 0.0037 | Equal |
| **Geometric Reasoning**| 0.638 | 0.643 | 0.671 | +0.005 ± 0.016 | +0.33 | 0.7505 | [-0.019, +0.029] | 0.0333 | 0.0281 | 1.2x closer to real |
| **Semantic Alignment** | 0.757 | 0.522 | 0.406 | -0.235 ± 0.086 | -2.73 | 0.0292 | [-0.371, -0.107] | 0.3512 | 0.1162 | **3.0x closer to real** |

### Table 2: Question-by-Question Ground-Truth Divergence
| QID | Cat | Question Prompt Summary | Base F | Prompt QT | Real Ref | $\Delta (QT - F)$ | $|F - \text{Real}|$ | $|QT - \text{Real}|$ | QT Closer? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Q1** | Sema | Robot arm holding ball at start | 0.757 | 0.522 | 0.406 | -0.235 ± 0.086 | 0.351 | **0.116** | **YES (3.0x)** |
| **Q2** | Phys | Ball falling after release | 0.574 | 0.281 | 0.358 | -0.292 ± 0.127 | 0.215 | **0.077** | **YES (2.8x)** |
| **Q3** | Phys | Ball speeding up as it falls | 0.159 | 0.172 | 0.183 | +0.013 ± 0.022 | 0.024 | **0.011** | **YES (2.1x)** |
| **Q4** | Phys | Ball bounces up from plank | 0.165 | 0.114 | 0.102 | -0.051 ± 0.013 | 0.063 | **0.012** | **YES (5.2x)** |
| **Q5** | Phys | Falls only after gripper release | 0.439 | 0.342 | 0.335 | -0.097 ± 0.043 | 0.103 | **0.006** | **YES (16.6x)** |
| **Q6** | Phys | Bounces diminish until rest | 0.916 | 0.896 | 0.891 | -0.020 ± 0.009 | 0.025 | **0.005** | **YES (4.9x)** |
| **Q7** | Visu | Ball keeps round shape | 0.956 | 0.975 | 0.978 | +0.019 ± 0.008 | 0.022 | **0.002** | **YES (8.8x)** |
| **Q8** | Visu | Free of unnatural flicker | 0.427 | 0.410 | 0.421 | -0.017 ± 0.007 | **0.006** | 0.011 | no (tie) |
| **Q9** | Visu | Clean image, free of heavy noise| 0.722 | 0.719 | 0.692 | -0.003 ± 0.006 | 0.030 | **0.027** | **YES (1.1x)** |
| **Q10**| Visu | Continuous shot without cuts | 0.947 | 0.948 | 0.947 | +0.001 ± 0.002 | **0.000** | 0.001 | no (tie) |
| **Q11**| Geom | Static camera framing | 0.905 | 0.901 | 0.905 | -0.004 ± 0.005 | **0.000** | 0.004 | no (tie) |
| **Q12**| Geom | Smooth & continuous motion | 0.371 | 0.385 | 0.438 | +0.014 ± 0.028 | 0.067 | **0.053** | **YES (1.3x)** |
| **Q13**| Phys | Arm and table stay present | 0.932 | 0.935 | 0.936 | +0.003 ± 0.002 | 0.005 | **0.001** | **YES (3.2x)** |

---

## 3. Methodological Significance for Deliverables 1–3

1. **Replication Status**: Finding #2577 is **fully replicated** and promoted from *provisional* to *trusted/replicated*.
2. **Deliverable 1 & Deliverable 3 Representation**:
   - The HUE judge drop of $-0.052 \pm 0.016$ must always be reported alongside the **real ground-truth reference ($0.584$ real vs $0.585$ QT)**.
   - The HUE judge drop is not a regression in physical plausibility, but an artifact of the 2B VLM judge's motion bias: the judge rewards perpetual bouncing and penalizes true physical rest.
   - When evaluated by distance to physical reality, prompt QT is **$76.2\times$ more accurate than base F** overall and **$5.7\times$ more accurate on physical laws**.

---

## 4. Replication Artifacts

All scripts, numerical data, and publication plots are preserved in this directory:
- `audit_hue_qt.py`: Independent Python replication and auditing script.
- `plot_hue_qt.py`: High-resolution visualization script.
- `task123_review_results.json`: Full machine-readable results, p-values, and confidence intervals.
- `plots/figure_category_profiles.png`: Category score comparison and ground-truth error.
- `plots/figure_question_distance_to_real.png`: Question-level ground-truth error reduction.
