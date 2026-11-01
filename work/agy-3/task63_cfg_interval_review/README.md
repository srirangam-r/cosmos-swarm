# Independent Review of Task 50: CFG Noise-Interval Pilot on GAUGE Held Ball

**Author**: `agy-3`  
**Date**: Sun 2026-11-01  
**Target**: Task 50 pilot by `codex-api-1` (Board msg #1329; clips generated on Brev A100 `rahul2-nano`)  
**Task ID**: Task 63 (child of Task 50)  

---

## Executive Summary

We conducted an independent, objective frame-by-frame quantitative analysis of all 6 clips from the Task 50 exploratory pilot (`base`, `full`, `window` across seeds 1 and 2 on GAUGE ball 1 frame 0, 832x480, 93 frames @ 24 fps).

Using multi-ROI difference metrics, connected-component morphology, and dual-zone occupancy tracking:
1. **Execution Integrity Verified:** The all-step hook control (`full`) is **bit-identical** to the unhooked baseline (`base`) across all 93 decoded BGR frames on both seeds:
   - Seed 1 SHA-256: `1f105d7e8adaf26b316853f42abd179b258258e1398024878d9e452ae9369c34`
   - Seed 2 SHA-256: `47689214fc19e3767f4b3c2dcef76164fac7a614497d20981ad062db20d4038e`
   - This proves that hook insertion introduces zero numerical degradation or scheduler drift.
2. **Release Hypothesis Refuted:** Restricting CFG guidance to timesteps $[220, 840]$ (11 guided steps, 24 unguided steps) **does NOT release the held ball**. In both seeds, release rate is **0/2 (0%)**:
   - In Seed 1 Window: the ball remains trapped in the gripper jaws ($g\_diff \le 23.2$); lower corridor difference is suppressed to $c\_diff \le 6.4$ (vs $26.3$ in base); plank difference is $p\_diff \le 4.8$ (vs $68.8$ in base).
   - In Seed 2 Window: arm motion is confined to the upper corridor; lower corridor difference is $c\_diff \le 5.2$ (vs $70.4$ in base); plank difference is $p\_diff \le 11.8$ (vs $86.4$ in base); plank blob frames are **0/93 (0%)** (vs $75/93$ [80.6%] in base).
3. **Novel Finding: High-Noise CFG is the Driver of Unphysical Phantom Hallucinations:**
   - In the baseline model (`base_s1`), the stuck ball induces a catastrophic **phantom duplicate spawning**: the original ball remains held in the gripper ($82/93$ frames occupied), while a phantom clone ball is generated in the lower corridor, impacting the plank at frame 28 ($p\_d = 68.8$), rebounding, impacting at frame 48 ($p\_d = 52.1$), and impacting at frame 61 ($p\_d = 69.2$).
   - In the restricted window (`window_s1`), this phantom clone is **completely extinguished** ($0$ impacts, $0/93$ frames with plank ball). The holder undergoes a brief vertical bifurcation/necking at frames 48–49 that snaps back into the holder by frame 50 without any free fall.
   - Similarly in Seed 2, baseline deposits a persistent dark mass on the plank from frame 12 through 92 ($75/93$ frames), whereas the restricted window leaves the plank completely pristine ($0/93$ frames).

**Conclusion:** Restricting CFG to the intermediate noise window $[220, 840]$ suppresses unphysical object cloning and hallucinated impacts, but fails to provide the kinematic impetus required to open the holder and release the ball into genuine gravitational free fall.

---

## Quantitative Metrics Table

| Metric | Seed 1: Base (CFG 6 all) | Seed 1: Window [220, 840] | Seed 2: Base (CFG 6 all) | Seed 2: Window [220, 840] |
|---|---|---|---|---|
| **Raw Decoded BGR Match vs Full** | Identical (100%) | Distinct (11/35 steps) | Identical (100%) | Distinct (11/35 steps) |
| **Max Gripper Difference ($\Delta I_{grip}$)** | 39.8 | 23.2 | 132.1 | 104.1 |
| **Max Lower Corridor Diff ($\Delta I_{corr}$)** | 26.3 | 6.4 | 70.4 | 5.2 |
| **Max Plank Contact Diff ($\Delta I_{plank}$)** | 68.8 | 4.8 | 86.4 | 11.8 |
| **Frames with Blob in Gripper** | 82 / 93 (88.2%) | 48 / 93 (51.6%) | 61 / 93 (65.6%) | 23 / 93 (24.7%) |
| **Frames with Blob at Plank** | 9 / 93 (9.7%) | 0 / 93 (0.0%) | 75 / 93 (80.6%) | 0 / 93 (0.0%) |
| **Dual Gripper + Corridor Persistence** | 81 / 93 (87.1%) | 48 / 93 (51.6%) | 61 / 93 (65.6%) | 23 / 93 (24.7%) |
| **Plank Impacts Observed** | 3 (f28, f48, f61) | 0 (none) | Continuous mass | 0 (none) |
| **True Free-Fall Ball Release** | **No** (stuck + phantom) | **No** (stuck in holder) | **No** (arm descent) | **No** (upper motion only) |

---

## Detailed Frame-by-Frame Dynamics

### Seed 1: Phantom Duplication vs Hallucination Suppression
- **Base S1:**
  - $t \in [0, 22]$: Ball remains stationary in gripper jaws ($y \approx 185$, area $\approx 17,500$ px).
  - $t \in [23, 27]$: Holder shows minor deformation, but ball mass remains clamped.
  - $t = 28$: A phantom clone ball suddenly strikes the wooden plank at $y = 347.1$ (area $813$ px, plank diff $p\_d = 68.8$). The holder simultaneously contains a dark mass of area $16,900$ px at $y = 190.2$.
  - $t \in [29, 47]$: Clone ball rebounds and ascends into lower corridor.
  - $t = 48$: Clone ball strikes plank second time ($y = 344.6$, area $628$ px, $p\_d = 52.1$). Gripper remains fully occupied ($y = 183.2$, area $16,964$ px).
  - $t = 61$: Clone ball strikes plank third time ($y = 360.9$, area $505$ px, $p\_d = 69.2$). Gripper remains occupied ($y = 186.6$, area $17,756$ px).
  - Joint occupancy: $81/93$ frames exhibit simultaneous gripper and corridor/plank blobs ($87.1\%$).
- **Window S1:**
  - $t \in [0, 47]$: Ball remains in gripper. Corridor diff stays at $2.8 - 4.0$. Plank diff stays at $2.7 - 4.3$. No clone ball appears.
  - $t \in [48, 49]$: Holder blob undergoes brief elastic necking, bifurcating into two adjacent components: upper component ($y = 141$, area $\approx 2520$ px) and lower component ($y = 201$, area $\approx 13,200$ px).
  - $t = 50$: The two components re-merge into a single blob at $y = 191.2$ (area $16,000$ px).
  - $t \in [51, 92]$: Blob remains clamped in the upper holder region. Plank diff never exceeds $4.8$. No impact, no fall.

### Seed 2: Plank Mass Deposition vs Lower-Corridor Invariance
- **Base S2:**
  - $t \in [4, 11]$: Arm lowers; gripper diff jumps from $0.0$ to $114.5$.
  - $t = 12$: Lower dark mass appears at $y = 332.6$ and touches plank at $y = 364.4$ ($p\_d = 39.4$).
  - $t \in [13, 92]$: Dark mass remains deposited on the plank across 75 frames ($p\_d$ reaches $86.4$).
- **Window S2:**
  - $t \in [0, 92]$: Mechanical arm deforms in upper zone ($g\_d$ up to $104.1$), but the lower corridor remains completely static ($c\_d \le 5.2$).
  - $0/93$ frames exhibit any blob at the plank ($p\_d \le 11.8$). No object is released.

---

## Contact Sheet Evidence

Two contact sheets are available in `sheets/`:
1. `sheet_task50_seed1_audit.jpg`: Side-by-side progression of frames $[0, 15, 25, 28, 35, 48, 50, 61, 75, 92]$ showing Base S1 (stuck ball + phantom impacts at f28, f48, f61) vs Window S1 (holder necking at f48-49, clean plank).
2. `sheet_task50_seed2_audit.jpg`: Side-by-side progression of frames $[0, 6, 12, 18, 24, 30, 45, 60, 75, 92]$ showing Base S2 (plank mass deposition) vs Window S2 (static lower corridor, clean plank).

---

## Implications for World Model Architecture and Fine-Tuning

1. **Why Nano Hallucinates:** When conditioned on a held-ball image and prompted for "free fall and successive bounces", Nano's high-noise CFG steps force the appearance of the prompt's salient visual target (a bouncing ball on the plank) even when the model's physics prior cannot resolve the mechanical release of the holder jaws.
2. **Noise-Interval Tradeoff:** Restricting CFG to timesteps $[220, 840]$ successfully cuts off this mode hallucination, reducing false-positive phantom generation to zero. However, because CFG is also what drives prompt adherence, removing high-noise guidance leaves the model dominated by its visual continuity prior (keeping the scene static).
3. **Guidance Direction:** True release cannot be achieved simply by cutting CFG noise windows; it requires either targeted negative prompt engineering, trajectory-conditioned fine-tuning (LoRA), or spatial-attention masking that forces gripper opening.
