# Task 140: Rule R Generalization on GAUGE Slope and Pendulum Dev Scenes

**Agent:** `ro-agy1`  
**Task ID:** #140  
**Context:** Raj Steering #2930 Requirement 8 & Charter v23/24 Constraint (8)  
**Status:** In Progress / Evaluated (Audited with codex-api-2 Blind QC #3616, #3621, #3624)

---

## 1. Objective & Hypothesis

Raj's steering requirement 8 (#2930) directs the swarm to test the recipe's generic end-state rule:
> *"By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video."*

on scenes and prompts it was not designed on (other dev scenes, specifically the GAUGE slope and pendulum), with $\ge 3$ seeds and matched controls.

**Hypothesis:** Appending Rule R will induce kinetic energy dissipation and physical rest on inclined slopes (wood/plastic) and damp pendulum oscillations (rest/mid-swing) without destroying object geometry.

---

## 2. Experimental Design & Arms

A $4 \times 3 \times 3 = 36$ clip paired factorial grid:
- **Scenes (4):**
  1. `slope_wood`: GAUGE wood cube on 30° wood incline (steep, real $a = 2.58\text{ m/s}^2$).
  2. `slope_plastic`: GAUGE plastic cube on 30° wood incline (real $a = 2.57\text{ m/s}^2$).
  3. `pend_rest`: GAUGE rigid pendulum at 10° initial deflection held at rest from frame 0.
  4. `pend_mid`: GAUGE rigid pendulum in dynamic mid-swing state (frame 93 continuation).
- **Arms (3):**
  - **Base (`base`):** Unmodified scene prompt.
  - **Rule R (`r`):** Base prompt + canonical generic Rule R verbatim.
  - **Control N (`n`):** Base prompt + length-matched neutral suffix (lighting/camera description).
- **Seeds:** 1, 2, 3.
- **Inference Setup:** Cosmos3-Nano via shared `cosmos_queue` (93 frames, 24 fps, 35 steps, CFG 6.0, flow_shift 10 requested, empty negative prompt).

---

## 3. Results & Findings by Scene

### A. GAUGE Slope Wood ($n=9$ clips)
- **Kinematics:** In all 9 clips (Base 3/3, Rule R 3/3, Control N 3/3), the wood cube accelerates rapidly down the plank (peak velocity $0.52\text{--}0.90\text{ m/s}$), slides $>0.44\text{ m}$ (the entire length of the plank), and runs off the plank onto the optical table.
  - Peak velocity: Base $0.687\text{ m/s}$, Rule R $0.772\text{ m/s}$, Control N $0.673\text{ m/s}$.
  - Slide distance: Base $0.463\text{ m}$, Rule R $0.465\text{ m}$, Control N $0.466\text{ m}$.
- **Tracker vs Visual Reality Reconciliation:** The automated corridor tracker initially classified wood clips as "at rest at f92" because the block came to a stop after falling off the plank onto the table edge ($\Delta v_{\text{late}} \approx 0$). However, as audited by `codex-api-2` (#3566, #3616, #3621), this is a **runoff false positive**. In blind sampled-frame QC, 6/7 tracker-rest clips are visually unclear or exit the view. Rule R does not impart dissipative rest on the inclined plank.

### B. GAUGE Slope Plastic ($n=9$ clips)
- **Kinematics:** Plastic cube slides more slowly down the incline (peak speed $0.23\text{--}0.76\text{ m/s}$).
  - In both Base and Rule R, **2/3 seeds stay on the plank** (Seed 2: $0.337\text{ m}$ Base vs $0.336\text{ m}$ R; Seed 3: $0.345\text{ m}$ Base vs Seed 1: $0.345\text{ m}$ R) and **1/3 seeds run off** ($0.435\text{ m}$ Base s1 vs $0.467\text{ m}$ R s3).
  - Rule R shows no statistically resolved improvement over Base in rest rate (2/3 vs 2/3) or terminal motion.

### C. GAUGE Pendulum Rest Frame 0 ($n=9$ clips)
- **Static Boundary Grasp Deadlock:**
  - Base: 0/3 release (2 stay frozen at 10°, 1 shows small non-rigid jitter).
  - Rule R: 0/3 release (3/3 stay 100% frozen at 10°).
  - Control N: 0/3 release (3/3 stay frozen).
- **Significance:** Directly corroborates Deliverable 2 Finding 10 and Finding 14: text prompting cannot break the static boundary grasp deadlock ($\Delta v = 0$) from frame 0.

### D. GAUGE Pendulum Mid-Swing ($n=9$ clips)
- **Limit-Cycle Oscillation Persistence:**
  - In dynamic mid-swing, all 9 clips continue oscillating through frame 92.
  - Decay ratio ($\text{motion energy}_{\text{late}} / \text{motion energy}_{\text{early}}$):
    - Base: $0.972 \pm 0.051$ (oscillates perpetually).
    - Rule R: $1.142 \pm 0.093$ (late motion energy $1.77$ vs early $1.53$; active oscillation).
    - Control N: $1.033 \pm 0.080$ (oscillates perpetually).
  - Physical rest rate at f92: Base 0/3, Rule R 0/3, Control N 0/3.
  - **Conclusion:** Rule R completely fails to damp pendulum oscillations to rest. Cosmos3-Nano maintains undamped harmonic/limit-cycle motion.

---

## 4. Hardware & Endpoint Confound Audit

Per `codex-api-2` audit (#3578):
- 7/12 R–Base pairs and 4/12 R–Neutral pairs share exact endpoints (`a100`, `q8-6`, `int-a100`).
- The remaining pairs mix `q8`, `a100`, `int-a100`, `gb10`, and `puget13`.
- While `flow_shift` is ignored across all Diffusers servers due to Karras sigmas (#2870), potential cross-stack quantization/precision differences between quantized `q8` and bf16 endpoints mean paired differences must be interpreted with caution.

---

## 5. Artifacts & Outputs

- Full Kinematics & Tracking Data: `work/ro-agy1/task140_rule_r_devscenes/kinematics_results.json`
- Contrast Summaries: `work/ro-agy1/task140_rule_r_devscenes/summary_contrasts.json`
- Contact Strips (every 8 frames): `work/ro-agy1/task140_rule_r_devscenes/strips/`
- Queue Request Job Sidecars: `work/ro-agy1/task140_rule_r_devscenes/clips/t140_*.json`
- Background Scoreboard Evaluator: `work/ro-agy1/task140_rule_r_devscenes/parallel_score.py`
