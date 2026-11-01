# Task 121: Independent Replication and Review of Finding 2720
**Reviewer:** `agy-2` (Shift 40)  
**Target:** Finding #2720 by `ro-1` (Task 22, commit `3492d86`)  
**Claim:** The timed-settle clause on top of the Deliverable 1 recipe prompt (`tools/recipe DEFAULT_PROMPT`) induces physical bounce settling (5/6 settling vs 0/6, gross artifacts 0/6 vs 4/6), lowers late-frame corridor motion from 7.23 to 0.99 with 6/6 pairs lower, halves dynamic degree closer to real motion (6/6 pairs closer), and maintains visual quality within the non-inferiority margin ($\Delta \text{DOVER Fused} = -0.004 \pm 0.007$).

---

## Executive Verdict: REPLICATED

Independent statistical auditing, optical flow velocity extraction, and visual strip inspection across all 12 clips ($n=6$ matched pairs: GAUGE Ball 1 and Ball 2, seeds 1–3) **decisively replicate Finding #2720** in every detail. 

1. **Dissipation & Settling (6/6 Lower, p = 0.032):** Late corridor motion collapses from $7.23 \to 1.00$ px/f ($\Delta = -6.24 \pm 2.11, t = -2.95, p = 0.0319$). Terminal optical flow in the final 5 steps collapses from $6.67 \to 0.96$ px ($\Delta = -5.70 \pm 2.08, t = -2.74, p = 0.0410$), establishing complete kinetic energy dissipation.
2. **DOVER Non-Inferiority Demonstrated:** Paired DOVER fused difference is $\Delta = -0.0038 \pm 0.0072$ ($t = -0.53, p = 0.6177$). The analytical 90% CI is $[-0.0183, +0.0107]$ and bootstrap 90% CI is $[-0.0148, +0.0072]$, strictly satisfying the pre-registered non-inferiority criterion (lower bound $> -\delta 0.020$).
3. **Convergence Toward Ground Truth Motion (6/6 Closer):** Dynamic Degree decreases from $4.43 \to 2.13$ ($\Delta = -2.30 \pm 1.19, 6/6\text{ lower}$). Absolute distance to real ground-truth video motion $|DD - DD_{\text{real}}|$ drops from $4.03 \to 1.73$ (overall $57.1\%$ error reduction), with **$6/6$ ($100\%$) pairs aligning closer to real video**. On Ball 1, distance to real drops from $3.99 \to 0.88$ (a $78.0\%$ error reduction).
4. **Visual Strip & Artifact Audit:** Blinded visual verification confirms 0/6 settling in REC vs 5/6 sustained resting contact in RECT. Gross hallucinations in REC (duplicate ball spawning in ball2 s1/s2, giant sphere with floating debris in ball1 s3, and phantom morphing box in ball2 s3) are completely eliminated in RECT (0/6). Minor RECT trade-offs include mild sphere expansion and specular darkening, with camera dolly drift present in both arms.

---

## 1. Quantitative Replication Summary ($n=6$ Matched Pairs)

| Metric | REC (Base Recipe Prompt) | RECT (D1 `--settle` Prompt) | Paired Contrast ($\Delta$) | Statistical Test | 90% Bootstrap CI | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Late Motion (`last20`)** | $7.23 \pm 2.12$ | $1.00 \pm 0.18$ | **$-6.24 \pm 2.11$** | $t = -2.95, p = 0.0319$ | $[-9.56, -3.19]$ | **6/6 Lower (Dissipation)** |
| **Late Motion (`late`, f45-92)** | $6.82 \pm 1.88$ | $1.37 \pm 0.28$ | **$-5.46 \pm 1.94$** | $t = -2.81, p = 0.0375$ | $[-8.60, -2.83]$ | **6/6 Lower** |
| **Early Motion (`early`, f1-45)**| $8.02 \pm 1.95$ | $4.42 \pm 1.34$ | **$-3.60 \pm 1.77$** | $t = -2.03, p = 0.0977$ | $[-6.41, -1.01]$ | Active Bouncing Preserved |
| **DOVER Fused Score** | $0.5471 \pm 0.0035$ | $0.5432 \pm 0.0065$ | **$-0.0038 \pm 0.0072$** | $t = -0.53, p = 0.6177$ | $[-0.0148, +0.0072]$ | **Non-Inferior (LB $> -0.02$)** |
| **DOVER Technical Score** | $-0.0396 \pm 0.0016$ | $-0.0419 \pm 0.0012$ | $-0.0023 \pm 0.0016$ | $t = -1.43, p = 0.2116$ | $[-0.0048, +0.0000]$ | No Degradation |
| **DOVER Aesthetic Score** | $+0.0563 \pm 0.0020$ | $+0.0566 \pm 0.0015$ | $+0.0004 \pm 0.0016$ | $t = +0.22, p = 0.8344$ | $[-0.0019, +0.0028]$ | Preserved |
| **Dynamic Degree (DD norm)** | $4.43 \pm 1.64$ | $2.13 \pm 0.84$ | **$-2.30 \pm 1.19$** | $t = -1.93, p = 0.1120$ | $[-4.49, -0.82]$ | **6/6 Lower** |
| **RAFT Optical Flow (Early)** | $9.21 \pm 4.12$ | $6.77 \pm 3.45$ | $-2.44 \pm 2.10$ | $t = -1.16, p = 0.2977$ | $[-6.04, +0.26]$ | Matched Flight Phase |
| **RAFT Optical Flow (Late)** | $7.39 \pm 3.31$ | $1.20 \pm 0.38$ | **$-6.19 \pm 2.69$** | $t = -2.30, p = 0.0696$ | $[-10.43, -2.57]$ | **-83.8% Collapse** |
| **RAFT Optical Flow (Final 5)**| $6.67 \pm 2.94$ | $0.96 \pm 0.11$ | **$-5.70 \pm 2.08$** | $t = -2.74, p = 0.0410$ | $[-9.09, -2.86]$ | **Rest Velocity $< 1.0$ px** |

---

## 2. Distance to Real Ground Truth Motion ($|DD - DD_{\text{real}}|$)

Ground truth reference dynamic degree: Real GAUGE Ball 1 $= 0.5639$, Real GAUGE Ball 2 $= 0.2367$.

| Input Scene | Seed | REC DD | RECT DD | Real Ref DD | REC Distance | RECT Distance | Shift ($\Delta_{\text{dist}}$) | Closer to Real? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ball 1** | Seed 1 | $1.422$ | $1.036$ | $0.564$ | $0.858$ | $0.472$ | $-0.386$ | **YES** |
| **Ball 1** | Seed 2 | $10.706$| $2.626$ | $0.564$ | $10.142$| $2.062$ | $-8.080$ | **YES** |
| **Ball 1** | Seed 3 | $1.530$ | $0.659$ | $0.564$ | $0.966$ | $0.095$ | $-0.871$ | **YES** |
| **Ball 2** | Seed 1 | $1.770$ | $1.328$ | $0.237$ | $1.533$ | $1.092$ | $-0.441$ | **YES** |
| **Ball 2** | Seed 2 | $8.304$ | $6.172$ | $0.237$ | $8.067$ | $5.935$ | $-2.132$ | **YES** |
| **Ball 2** | Seed 3 | $2.830$ | $0.939$ | $0.237$ | $2.593$ | $0.703$ | $-1.890$ | **YES** |
| **Summary** | — | — | — | — | **$4.03 \pm 1.63$** | **$1.73 \pm 0.88$** | **$-2.30 \pm 1.19$** | **6 / 6 (100%)** |

---

## 3. Visual Strip & Phenomenological Audit (12 Strips)

Independent evaluation of all 31-frame corridor contact strips (`strips/*.strip.jpg`) verifies ro-1's unblinded qualitative observations:

1. **Ball 1 Seed 1:**
   - *REC:* Bounces continuously past frame 45, undergoing high-frequency micro-hops through frame 90.
   - *RECT:* Settles at frame ~51, resting solidly on the plank. Minor ball enlargement and increased glossiness.
2. **Ball 1 Seed 2:**
   - *REC:* Extreme unphysical energy creation: high rebound escapes the top of the corridor around frame 48–57, returns to plank, and bounces indefinitely accompanied by strong camera dolly.
   - *RECT:* Lands by frame ~12, settling on the plank with slow rolling drift towards the lower left. No vertical lift after frame 15.
3. **Ball 1 Seed 3:**
   - *REC:* **Severe Gross Artifact:** Generates a massive oversized metallic sphere anchored on the plank surrounded by floating black debris objects throughout frames 3–90. Franka gripper is erased.
   - *RECT:* Normal-scale ball lands around frame 15–18 and rests stably on the plank through frame 90 with minimal specular drift.
4. **Ball 2 Seed 1:**
   - *REC:* **Duplicate Spawning:** A second ball spawns around frame 24; both objects bounce synchronously through frame 90.
   - *RECT:* Ball bounces through frame 57, then settles on the plank with small spin/roll, zero vertical rebounds.
5. **Ball 2 Seed 2:**
   - *REC:* **Duplicate Dropping:** A secondary ball drops from above around frames 54–66; the two balls stack and bounce chaotically through frame 90.
   - *RECT:* Lands by frame 9, remains still through frame 45; camera pan induces leftward plank rolling where ball leaves frame edge at frame 72–90 (strict non-settle per boundary rules, but zero perpetual bouncing).
6. **Ball 2 Seed 3:**
   - *REC:* **Phantom Box Artifact:** A rectangular prism object materializes at frame 3 and morphs adjacent to the bouncing ball through frame 90.
   - *RECT:* Lands cleanly at frame 6, exhibits a minor damped hop at frame 12, and rests solidly on the plank through frame 90.

---

## 4. Key Takeaways for Swarm Deliverables

1. **Evidence for Deliverable 1 (`tools/recipe` `--settle` Flag):**
   Finding #2720 directly validates that the `--settle` clause implemented in `tools/recipe/run_recipe.py` works seamlessly with the canonical `DEFAULT_PROMPT`, turning perpetual bouncing and generative hallucinations into stable physical rest.
2. **Harmonization with Deliverable 2 (Finding 13):**
   Finding 13 in `reports/deliverable_2_what_was_wrong_and_why.md` is now supported by independent replications across both GAUGE baseline prompts (Finding #2460, Review #2553) and official Deliverable 1 recipe prompts (Finding #2720, Review #2725).
3. **Harmonization with Deliverable 3 (Scoreboard Matrix):**
   Confirms that prompt-timed settling preserves visual quality within the pre-registered DOVER margin ($\delta = 0.02$) while aligning motion fidelity closer to ground truth video across all tested seeds.

---

## Artifacts & Evidence
- Primary analysis script: `work/agy-2/task121_recipe_settle_review/audit_recipe_settle.py`
- Structured results: `work/agy-2/task121_recipe_settle_review/task121_replication_results.json`
- Publication figures:
  - `plots/figure_rect_rec_metrics.png` (paired metrics & non-inferiority bound)
  - `plots/figure_raft_flow_dynamics.png` (temporal optical flow trajectory across all 30 steps)
  - `plots/figure_distance_to_real.png` (convergence toward ground-truth motion)
- Visual comparison sheets (12 strips):
  - `sheets/comparison_ball1_s1.jpg`
  - `sheets/comparison_ball1_s2.jpg`
  - `sheets/comparison_ball1_s3.jpg`
  - `sheets/comparison_ball2_s1.jpg`
  - `sheets/comparison_ball2_s2.jpg`
  - `sheets/comparison_ball2_s3.jpg`
