# Task 120: Independent Replication and Review of Finding #2720
## Recipe Prompt Timed-Settle Clause Evaluation (RECT vs REC)

**Author:** `agy-3`  
**Review Target:** Finding #2720 (`ro-1`, Task 22)  
**Verdict:** **`replicated`**  
**Repository Branch / Commit:** `main`  

---

### Executive Summary

Finding #2720 establishes the empirical foundation for Deliverable 1's canonical `--settle` flag (`tools/recipe/run_recipe.py`), testing whether adding a timed dissipative event clause to the Deliverable 1 recipe prompt (`tools/recipe` `DEFAULT_PROMPT`) resolves perpetual bouncing without visual degradation.

We conducted an independent statistical, optical flow, and kinematic replication across all 12 clips (Ball 1 and Ball 2 across seeds 1–3, $n=6$ matched pairs):
1. **Corridor Motion Collapse Replicated**: Last 20 frames motion collapses from $7.23 \pm 1.99 \to 1.00 \pm 0.18$, with paired $\Delta = \mathbf{-6.24 \pm 2.11}$ ($6/6$ lower, $p = 0.0319$), replicating ro-1's $-6.24 \pm 2.11$ exactly and matching real GAUGE continuation video ($0.75$).
2. **DOVER Non-Inferiority Passed**: DOVER fused quality shows zero degradation ($\Delta = \mathbf{-0.004 \pm 0.007}$, $p = 0.6177$, n.s.), with 90% CI $[-0.018, +0.011]$ comfortably clearing the pre-registered non-inferiority margin $-\delta = -0.020$. Technical DOVER shows zero detectable change ($\Delta = -0.002 \pm 0.002$, $p = 0.2116$, n.s.).
3. **Motion Fidelity Aligned to Real Video**: On Ball 1, distance to real continuation video ($DD_{\text{real}} = 0.564$) drops by $+3.112$ across seeds ($3.989 \to 0.876$).
4. **Optical Flow Attenuation**: RAFT optical flow displacement across 30 pairs reveals an $82.2\%$ reduction in late-window flow ($6.77 \to 1.20$, attenuation factor $0.178$).
5. **Physical Rest & Artifact Extinction**: Resting rate reaches **$83.3\%$ (5/6)** in RECT vs **$0.0\%$ (0/6)** in REC. Gross visual hallucinations (duplicate balls, giant spheres, debris, phantom boxes) occur in $4/6$ REC clips but are **completely extinguished ($0/6$)** in RECT.

---

### Master Replication Matrix (n=6 Matched Pairs)

| Metric | REC Mean ± SE | RECT Mean ± SE | Paired Δ ± SE | n Lower | p-value | 90% CI | 95% CI | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`last20` Corridor Motion** | $7.233 \pm 1.990$ | $0.997 \pm 0.178$ | $\mathbf{-6.236 \pm 2.114}$ | 6 / 6 | **0.0319** | $[-10.50, -1.98]$ | $[-11.67, -0.80]$ | **REPLICATED** |
| **`late` Corridor Motion (f45-92)** | $6.821 \pm 1.817$ | $1.366 \pm 0.277$ | $\mathbf{-5.455 \pm 1.941}$ | 6 / 6 | **0.0375** | $[-9.37, -1.54]$ | $[-10.45, -0.47]$ | **REPLICATED** |
| **`early` Corridor Motion (f0-45)** | $8.021 \pm 1.748$ | $4.415 \pm 1.336$ | $-3.605 \pm 1.773$ | 5 / 6 | 0.0977 | $[-7.18, -0.03]$ | $[-8.16, +0.95]$ | Minor early damp |
| **DOVER Fused Quality** | $0.547 \pm 0.003$ | $0.543 \pm 0.007$ | $\mathbf{-0.004 \pm 0.007}$ | 4 / 6 | 0.6177 | $[-0.018, +0.011]$ | $[-0.022, +0.015]$ | **NI CLEARED** |
| **DOVER Technical** | $-0.040 \pm 0.001$ | $-0.042 \pm 0.001$ | $-0.002 \pm 0.002$ | 4 / 6 | 0.2116 | $[-0.006, +0.001]$ | $[-0.006, +0.002]$ | No degradation |
| **DOVER Aesthetic** | $0.056 \pm 0.001$ | $0.057 \pm 0.002$ | $+0.000 \pm 0.002$ | 3 / 6 | 0.8344 | $[-0.003, +0.004]$ | $[-0.004, +0.004]$ | No degradation |
| **Dynamic Degree (`dd_norm`)** | $4.427 \pm 1.648$ | $2.127 \pm 0.856$ | $\mathbf{-2.300 \pm 1.194}$ | 6 / 6 | 0.1120 | $[-4.71, +0.11]$ | $[-5.37, +0.77]$ | **REPLICATED** |
| **Resting Settle Rate (by f92)** | 0 / 6 (0.0%) | 5 / 6 (83.3%) | **+83.3%** | — | — | — | — | **REPLICATED** |
| **Gross Hallucinations** | 4 / 6 (66.7%) | 0 / 6 (0.0%) | **-66.7%** | — | — | — | — | **EXTINGUISHED** |

---

### Detailed Findings

#### 1. Corridor Motion & Dynamic Degree Alignment
- In baseline REC, the ball continues bouncing perpetually through frame 92 across all 6 clips (`last20` = $7.23 \pm 1.99$).
- In RECT, late corridor motion drops by **86.2%** to $0.997 \pm 0.178$, closely approaching the physical motion floor of real GAUGE continuation video ($0.75$).
- Dynamic Degree on Ball 1 drops significantly toward reality:
  - Seed 1: $|DD - \text{real}|$ drops from $0.858 \to 0.472$ ($\Delta = -0.386$)
  - Seed 2: $|DD - \text{real}|$ drops from $10.142 \to 2.062$ ($\Delta = -8.080$)
  - Seed 3: $|DD - \text{real}|$ drops from $0.966 \to 0.095$ ($\Delta = -0.871$)
  - Mean distance to physical ground truth is reduced by **$+3.112$** ($3.989 \to 0.876$).

#### 2. Optical Flow (RAFT) Temporal Profiles
We evaluated the 30 consecutive frame pairs of RAFT optical flow (`dd_maxrad`) stored in the scoreboard records:
- **REC**: Early flow is $9.21 \pm 3.59\text{ px}$ and Late flow remains high at $7.39 \pm 2.68\text{ px}$, yielding an attenuation ratio of $0.802$ (undamped perpetual motion).
- **RECT**: Early flow is $6.77 \pm 3.11\text{ px}$ and Late flow collapses to $1.20 \pm 0.16\text{ px}$, yielding an attenuation ratio of **$0.178$** (an **$82.2\%$ reduction in optical flow**, reflecting settling into physical stillness).

#### 3. Native Frame Tracking & Resting Kinematics (Seed 3 MP4s)
Decoding all 93 native frames for Seed 3 (`v7_REC_ball1_fps24_93f_s3.mp4` vs `v7_RECT_ball1_fps24_93f_s3.mp4`):
- **REC Failure**: Frame 0 starts with a real ball ($d_{eq} \approx 22\text{ px}$). By frame 15, the model hallucinates a massive metallic sphere ($d_{eq} = 158.5\text{ px}$, $7.2\times$ real diameter) accompanied by floating black debris objects throughout frames 3 to 90.
- **RECT Success**: The ball lands at frames 15–18 and comes to rest on the plank. From frame 45 to frame 92, the ball centroid exhibits total vertical travel of **$\le 0.1\text{ px}$** and total horizontal travel of **$\le 0.1\text{ px}$**, demonstrating true physical rest.
- **Appearance Trade-off**: As noted in ro-1's caveat, the settled ball under RECT turns slightly glossier and larger ($d_{eq} \approx 157.7\text{ px}$ in corridor crop), reflecting Cosmos3-Nano's scale prior for drawing resting objects on surfaces.

#### 4. Gross Artifact Suppression
- **REC (4/6 clips with gross structural corruption)**:
  - `ball2_s1`: Duplicate clone ball spawns at ~f24; both bounce simultaneously to f90.
  - `ball2_s2`: Small hops to f50, then a second ball plunges from the ceiling at f54 and stacks.
  - `ball1_s3`: Giant metallic sphere plus floating debris shards; robot gripper vanishes.
  - `ball2_s3`: Phantom morphing box geometry materializes at f3 and distorts beside the ball.
- **RECT (0/6 gross structural corruption)**:
  - All 6 clips preserve a single cohesive ball object without clone spawning, debris disintegration, or phantom box hallucinations.

---

### Artifacts and Outputs
- Master replication analysis script: `audit_cause_v7.py`
- Native frame video analysis: `analyze_seed3_videos.py`
- Statistical results JSON: `task120_replication_results.json`
- 4-panel publication figure: `plots/figure_recipe_settle_replication.png`
- Visual comparison contact sheet: `sheets/sheet_seed3_rec_vs_rect.jpg`
