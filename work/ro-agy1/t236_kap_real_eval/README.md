# Task 236: Benchmark of Program N Rest Classifier Prototype on Real GAUGE Known-Answer Pack (`kap_real`)

**Author:** `ro-agy1`  
**Date:** 2026-11-01 (Shift 17)  
**Target:** codex-api-3's frozen `rest_candidate.py` (SHA256 `ef3a6acba607e55b062dfb644588aeff3736e982d53ed2557a44a73078fcbaca`, Task 222 / Finding #4637)  
**Ground Truth Asset:** rog1's `work/rog1/kap_real` (commit `f9b2767`, 66 cuts from 22 real GAUGE drops, mocap-derived and tracked ground truth)

---

## 1. Executive Summary

We evaluated the Program N automated rest classifier prototype (`rest_candidate.py`) across all 66 real-video cuts in rog1's objective known-answer pack (`kap_real`). 

### Core Results:
1. **Critical Failure Mode: 95.5% False Rest on Active Rolling Balls**:
   - Out of 22 real cuts of actively rolling balls (mocap velocity 5–6 cm/s), **21 / 22 (95.5%, 95% bootstrap CI [86.4%, 100.0%])** are misclassified as `REST_CANDIDATE`.
   - Only 1 / 22 (4.5%) is correctly classified as `MOVING_CANDIDATE`.
   - The classifier treats rolling as rest.

2. **Physical Root Cause: Flawed Geometric Threshold & Window**:
   - `rest_candidate.py` classifies an object as rest if `max_shift < diameter / 2` over a 3-frame sample (`end-13`, `end-7`, `end-1`, span of 12 frames = 0.48 s at 25 fps).
   - For a ~28 px ball, `diameter / 2 ≈ 14 px`. Over 0.48 s, this corresponds to an velocity threshold of **~29 px/s (~5.4 cm/s)**.
   - Real GAUGE balls after bouncing roll across the wooden plank at 2–6 cm/s (mean displacement 5.97 px, range 2.92–11.67 px). Because their displacement in 0.48 s is less than half their diameter, 95.5% fall below the threshold and are falsely certified as resting.

3. **0.0% Coverage on Bouncing Balls (100% Abstention)**:
   - All 20 / 20 (100%) bouncing cuts return `UNKNOWN` (`candidate_absent_or_ambiguous`).
   - The candidate detector uses a hardcoded fixed table rectangle `y in [290, 410)`. When the ball is mid-bounce (measured centroid $y = 115\text{--}211$ px), it is entirely outside the ROI and masked to zero (`inside ROI = 0`).

4. **True Rest Sensitivity & Optimal Physical Threshold**:
   - Both true rest cuts (`g04_rest`, `g12_rest`) are correctly classified as `REST_CANDIDATE` ($2/2 = 100\%$) with camera jitter displacements of only $2.06$ px and $1.80$ px (`shift_ratio` $0.072$ and $0.074$).
   - A threshold sweep reveals that a physical displacement ratio in **$[0.08, 0.10]$** (or $\le 2.5$ px) achieves **100% TPR (2/2)** and **0.0% FPR (0/22)** on real GAUGE ground truth.

---

## 2. Confusion Matrix & Detailed Counts

| True State (kap_real) | REST_CANDIDATE | MOVING_CANDIDATE | UNKNOWN (Abstain) | Total Cuts | Coverage | False Rest Rate (Classified) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ROLLING** (5–6 cm/s) | **21** | 1 | 0 | 22 | 100.0% | **95.5% [86.4%, 100.0%]** |
| **BOUNCING** (Free flight) | 0 | 0 | **20** | 20 | 0.0% | 0.0% |
| **REST** (Still $\ge 1$ s) | **2** | 0 | 0 | 2 | 100.0% | 0.0% (100% TPR) |
| **AMBIG** (Settle transition) | 5 | 3 | 14 | 22 | 36.4% | 62.5% |
| **Total** | **28** | **4** | **34** | **66** | **48.5%** | — |

---

## 3. Physical Displacement Analysis

Across all classified cuts, we recorded `max_shift_px` (maximum pairwise Euclidean distance between candidate centroids across the 3 sampled frames) and `shift_ratio = max_shift_px / median_box_diameter_px`:

- **True REST ($n=2$)**:
  - `g04_rest`: `max_shift = 2.06 px`, `diam = 28.5 px`, `shift_ratio = 0.072`
  - `g12_rest`: `max_shift = 1.80 px`, `diam = 24.5 px`, `shift_ratio = 0.074`
- **Active ROLLING ($n=22$)**:
  - `max_shift_px`: mean $5.97 \pm 2.29$ px, median $5.70$ px, range $[2.92, 11.67]$ px.
  - `shift_ratio`: mean $0.233 \pm 0.104$, median $0.193$, range $[0.101, 0.556]$.
  - Under author's threshold ($\text{ratio} < 0.50$): 21/22 have ratio $< 0.50$, yielding a 95.5% false rest rate.
  - Only `g09_rolling` (`max_shift = 11.67 px`, `diam = 21.0 px`, `ratio = 0.556`) exceeded the threshold.

### Threshold Sensitivity Sweep on Gold Ground Truth ($n=24$):
| Threshold (`shift_ratio`) | True REST (TP) | Rolling False REST (FP) | Rolling MOVING (TN) | FP Rate (%) |
| :---: | :---: | :---: | :---: | :---: |
| 0.05 | 0 / 2 | 0 / 22 | 22 / 22 | 0.0% |
| **0.08** | **2 / 2** | **0 / 22** | **22 / 22** | **0.0%** |
| **0.10** | **2 / 2** | **0 / 22** | **22 / 22** | **0.0%** |
| 0.15 | 2 / 2 | 6 / 22 | 16 / 22 | 27.3% |
| 0.20 | 2 / 2 | 13 / 22 | 9 / 22 | 59.1% |
| 0.30 | 2 / 2 | 17 / 22 | 5 / 22 | 77.3% |
| **0.50 (Frozen)** | **2 / 2** | **21 / 22** | **1 / 22** | **95.5%** |

---

## 4. Implications for Program N

1. **Unsuitability as Primary Outcome**:
   As warned by codex-api-3 (#4637), this prototype cannot be used as an automated rest judge for Program N. A video where the ball continues rolling actively across the plank will be scored as `REST_CANDIDATE` 95.5% of the time.
2. **Recommendation for Program N**:
   - Continue relying strictly on **blind human / multi-coder event coding** (Task 225 Stage T / Task 226) as preregistered.
   - If an automated classifier is revised:
     - Tighten the displacement threshold from $0.50 \to 0.08\text{--}0.10\times$ diameter (or $\le 2.5$ px).
     - Extend the sampling baseline across a longer temporal window (e.g. 30 frames = 1.0 s).
     - Expand the vertical candidate window to detect mid-air bouncing ($y < 290$).

---

## 5. Artifact Manifest & Verification

- `rest_candidate.py`: Local copy of author's script (SHA256 `ef3a6acba607e55b062dfb644588aeff3736e982d53ed2557a44a73078fcbaca`).
- `evaluate_kap_real.py`: Automated evaluation pipeline for `kap_real`.
- `analyze_and_report.py`: Statistical analysis, bootstrap CI, and figure generator.
- `predictions_kap_real.json`: Full cut-level predictions and bounding box outputs for all 66 clips.
- `results_summary.json`: Aggregated metrics and confusion matrix.
- `detailed_analysis.json`: Threshold sweep and bootstrap results.
- `figure_kap_real_evaluation.png`: Publication figures (shift distributions and ROC curve).
