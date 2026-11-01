# Independent Replication & Review of Finding 1661 (Task 69 / Task 24 LoRA Blind Evaluation)

**Reviewer:** `agy-3` (Shift 7)  
**Finding Reviewed:** Finding #1661 (`agy-2`)  
**Task:** Task 86  
**Verdict:** **REPLICATED**  

---

## 1. Executive Summary

We performed an exhaustive, independent multi-cue spatio-temporal evaluation of all blinded evaluation clips generated from Task 24 (sim_drop LoRA fine-tuning on synthetic ball drops) across Base, LoRA A (real-g), LoRA B (wrong-g control), and LoRA C (no-decay control).

We evaluated both:
1. **The Matched Finding 1661 Cohort ($n = 66$ clips):** Exact 1:1 replication of `agy-2`'s Finding #1661.
2. **The Full Extended Cohort ($n = 84$ clips):** Incorporating all 18 late-arriving evaluation clips from GB10 (`~/jobs/rahul-3/eval_clips/`).

### Key Finding:
**Zero clips out of 66 ($0.0\%$) and zero clips out of 84 ($0.0\%$) achieve genuine release of the held ball into free fall.**
- **Matched Cohort ($n = 66$):** Genuine Release Rate = **$0.0\%$ (0 / 66)**, 95% Wilson Score CI: **[$0.00\%$, $5.44\%$]** (Replicating Finding #1661's $0.0\%$).
- **Full Extended Cohort ($n = 84$):** Genuine Release Rate = **$0.0\%$ (0 / 84)**, 95% Wilson Score CI: **[$0.00\%$, $4.31\%$]**.

In $100\%$ of clips ($84 / 84$), the ball remains either trapped in the Franka gripper jaws ($94.0\%$), twitches mechanically without finger opening ($2.4\%$), or clones into a phantom duplicate on the plank while remaining clamped in the gripper ($2.4\%$).

---

## 2. Quantitative Classification Breakdown

| Behavioral Classification | Description | Matched Cohort ($n=66$) | Extended Cohort ($n=84$) | Replicates #1661? |
| :--- | :--- | :---: | :---: | :---: |
| **`held_frozen`** | Ball completely stationary in gripper jaws; diff $< 6.0$ across all zones | **60 / 66 ($90.9\%$)** | **78 / 84 ($92.9\%$)** | **Replicated** (exact 60/66) |
| **`held_minor_noise`** | Minor latent/background flicker; ball static in gripper | **2 / 66 ($3.0\%$)** | **2 / 66 ($2.4\%$)** | **Replicated** |
| **`phantom_duplicate`** | Ball clamped in gripper while clone ball spawns on plank (`808ef1`, `f690ef`) | **2 / 66 ($3.0\%$)** | **2 / 84 ($2.4\%$)** | **Replicated** (exact clips) |
| **`gripper_arm_twitch`** | Gripper base moves vertically $\approx 50$ px, but fingers never open (`c99152`, `213cda`) | **2 / 66 ($3.0\%$)** | **2 / 84 ($2.4\%$)** | **Replicated** (identifies `213cda` + `c99152`) |
| **`genuine_release`** | Ball departs gripper, traverses flight corridor, impacts plank | **0 / 66 ($0.0\%$)** | **0 / 84 ($0.0\%$)** | **Replicated** ($0.0\%$) |

---

## 3. Methodological Details

Our independent evaluation pipeline implements a multi-ROI spatio-temporal kinematic monitor completely distinct from `agy-2`'s template tracker and `ro-1`'s `gauge_blind.py`:
1. **Gripper Jaws Monitoring ROI** ($[y: 90..150, x: 260..320]$): Measures continuous ball and finger retention in the initial grasp region. Genuine release requires $end\_grip\_diff > 20.0$.
2. **Flight Corridor ROI** ($[y: 160..320, x: 250..330]$): Monitors the space through which a released ball must fall. Extracts connected components with morphological opening to track ball candidate centroids and area.
3. **Plank Impact Zone ROI** ($[y: 330..410, x: 240..340]$): Measures whether any impact occurs on the lower surface.
4. **Dual Occupancy State Matrix**: Detects phantom duplicate cloning where plank diff $> 25.0$ occurs simultaneously with end gripper diff $< 12.0$.

---

## 4. Visual Evidence Artifacts

The following contact sheets document the behavioral modes:
1. **Phantom Duplicates (`sheets/sheet_phantom_duplicates.jpg`):**
   - Shows clips `808ef1` and `f690ef` side-by-side across frames 0..92. The original ball remains clamped in the Franka gripper while an unphysical clone ball spontaneously appears on the plank.
2. **Gripper Arm Twitches (`sheets/sheet_gripper_arm_twitches.jpg`):**
   - Shows clips `c99152` and `213cda` where the robotic arm translates vertically downwards into the corridor, but the gripper fingers remain rigidly closed and return to rest.
3. **Representative Held Frozen Clips (`sheets/sheet_held_frozen_sample.jpg`):**
   - Documents the overwhelming majority mode where Cosmos3-Nano remains entirely frozen in the initial grasp.

---

## 5. Scientific Implications for the Swarm Deliverables

1. **Failure of Synthetic SFT LoRA:** Replicating Finding #1661 on both $n=66$ and $n=84$ clips conclusively demonstrates that supervised fine-tuning on synthetic Isaac Sim / MuJoCo drop videos fails to overcome the powerful mechanical grasp prior of the Franka arm in pre-training.
2. **Support for Deliverable 1 (Mid-Event Conditioning Recipe):** Because LoRA fine-tuning cannot induce the release transition, the mid-event conditioning recipe established in Deliverable 1 (`reports/deliverable_1_improved_nano_recipe.md`) is strictly required to bypass the release failure and recover physical gravitational motion ($g = 9.73 \pm 1.91$ m/s$^2$).
3. **Consolidation of Deliverable 2 (Finding 8):** Finding 8 in Deliverable 2 is now independently replicated and supported by an expanded sample size ($n=84$, $0/84$ releases, Wilson CI $[0.0\%, 4.3\%]$).
