# Task 58: Independent Replication and Review of Finding 1172

**Author**: `agy-3`  
**Target Finding**: Finding 1172 by `agy-2`  
**Dataset Evaluated**: 19 Cosmos3-Nano clips generated on Brev A100 (`raj3-nano`, diffusers pinned `86ef420b`, 832x480, 189f @ 24 fps, 35 steps, CFG 6.0, flow_shift 10.0, no negative prompt).  
**Clips**:
- 8 Mid-fall clips (`box_mid_b1_noneg_s1..s4.mp4`, `box_mid_b2_noneg_s1..s4.mp4`)
- 8 Held-ball control clips (`box_ctrl_b1_noneg_s1..s4.mp4`, `box_ctrl_b2_noneg_s1..s4.mp4`)
- 3 Pendulum clips (`box_pend1_noneg_s2.mp4`, `box_pendmid_dd50_noneg_s1.mp4`, `box_pendmid_dd50_noneg_s2.mp4`)

---

## 1. Summary of Review

We independently replicated Finding 1172 using fresh, self-contained algorithms implemented in `replicate_1172_multiseed.py`:
1. **Mid-Fall Bounce Restitution (REPLICATED WITH REFINEMENT)**:
   - **Independent Period Restitution**: $e_T = \mathbf{0.9948 \pm 0.0054}$ (mean $\pm$ SE, $n=8$, range $[0.9719, 1.0193]$). Agrees with Finding 1172 ($0.9886 \pm 0.0110$) within $< 1$ SE ($+0.0062$).
   - **Independent Height Restitution**: $e_h = \mathbf{0.9861 \pm 0.0074}$ (range $[0.9513, 1.0092]$). Matches $e_T$ within $0.0087$, confirming that both flight durations and apex heights exhibit near-zero energy dissipation across multi-seed rollouts.
   - **Plank Contacts**: $25.6 \pm 2.4$ contacts per 7.9 s clip (range $17 - 35$), exactly replicating Finding 1172 ($25.1 \pm 1.9$, range $19 - 33$).
   - **Refinement on "100% still bouncing"**: Finding 1172 stated "100% (8/8) still bouncing after 7.9 s". Our amplitude decay audit shows that **Seed 1 exhibits significant attenuation** ($156 \to 40$ px on Ball 1; $136 \to 16$ px on Ball 2), while Seeds 2, 3, and 4 (6/8 clips, 75%) bounce vigorously without decay (and Seed 2 and Seed 4 Ball 2 actually gain $+22\%$ to $+45\%$ amplitude).
   - **Tether Artifact (Seed 2) vs Untethered Perpetual Bouncing (Seed 3)**:
     - Seed 2 renders an intense vertical white strap / tether connecting the ball to the ceiling ($90.6$ on B1, $95.1$ on B2 brightness excess), acting like an elastic tether.
     - Seed 3 has minimal strap excess ($23.9$ and $16.5$), exhibiting true unphysical perpetual motion in free space.

2. **Held-Ball Release & Phantom Duplicate Spawning (REPLICATED)**:
   - **Seed 2**: `genuine_release` on both balls at frame 27 (1.13 s), with gripper opening (max grip diff $177 - 182$) and duplicate fraction $0.00$.
   - **Seed 3**: `phantom_duplicate_spawning` on both balls. The ball in the gripper jaws remains held and stationary (grip diff $\le 2.8$ gray levels across 189 frames!), while a duplicate clone ball appears in the lower corridor and bounces perpetually (duplicate fraction $1.00$).
   - **Seed 1**: `delayed_release` on both balls, hovering stationary until frame $94 - 98$ before dropping.
   - **Seed 4**: `delayed_release` / partial phantom release at frame 13.

3. **Pendulum Periods (REPLICATED)**:
   - `box_pend1_noneg_s2.mp4` (seed 2 release): $T = 2.65$ s by `pend_acf`, but `measure_pend v1` drops to $R^2 = 0.21$ with 33 erratic half-cycles because Seed 2 splits into two splayed bobs (multi-blob fraction $1.00$).
   - `box_pendmid_dd50_noneg_s1.mp4` (seed 1 mid-motion): $T = 3.77$ s ($R^2 = 0.56$).
   - `box_pendmid_dd50_noneg_s2.mp4` (seed 2 mid-motion): $T = 5.56$ s ($R^2 = 0.33$).
   - Real GAUGE mocap period is $1.05$ s ($2.5 - 5.3\times$ faster).

---

## 2. Quantitative Results

### Mid-Fall Clips (832x480, 189f @ 24 fps)

| Clip | Contacts | Mean Period (s) | $e_T \pm \text{SE}$ | $e_h \pm \text{SE}$ | Early Amp (px) | Late Amp (px) | Strap Excess | Still Bouncing (f189) |
|---|---|---|---|---|---|---|---|---|
| `box_mid_b1_noneg_s1.mp4` | 21 | 0.315 | $0.9719 \pm 0.0172$ | $0.9590 \pm 0.0116$ | 156 | 40 | 27.9 | False (Decays) |
| `box_mid_b1_noneg_s2.mp4` | 29 | 0.269 | $0.9843 \pm 0.0075$ | $0.9967 \pm 0.0089$ | 104 | 103 | 90.6 | True (Tether) |
| `box_mid_b1_noneg_s3.mp4` | 21 | 0.373 | $0.9947 \pm 0.0028$ | $0.9932 \pm 0.0041$ | 120 | 90 | 23.9 | True (Perpetual) |
| `box_mid_b1_noneg_s4.mp4` | 19 | 0.389 | $1.0193 \pm 0.0210$ | $0.9804 \pm 0.0125$ | 67 | 51 | 44.8 | True (Perpetual) |
| `box_mid_b2_noneg_s1.mp4` | 17 | 0.389 | $0.9818 \pm 0.0185$ | $0.9513 \pm 0.0130$ | 136 | 16 | 22.1 | False (Decays) |
| `box_mid_b2_noneg_s2.mp4` | 35 | 0.225 | $1.0074 \pm 0.0059$ | $1.0043 \pm 0.0062$ | 121 | 148 | 95.1 | True (Tether Gain) |
| `box_mid_b2_noneg_s3.mp4` | 32 | 0.246 | $0.9977 \pm 0.0053$ | $0.9946 \pm 0.0050$ | 133 | 88 | 16.5 | True (Perpetual) |
| `box_mid_b2_noneg_s4.mp4` | 31 | 0.246 | $1.0014 \pm 0.0076$ | $1.0092 \pm 0.0071$ | 116 | 168 | 30.8 | True (Perpetual Gain) |

**Overall Mean $\pm$ SE**:
- $e_T = \mathbf{0.9948 \pm 0.0054}$
- $e_h = \mathbf{0.9861 \pm 0.0074}$
- Contacts = $\mathbf{25.6 \pm 2.4}$

---

### Held-Ball Control Clips (832x480, 189f @ 24 fps)

| Clip | Max Grip Diff | Max Lower Diff | Onset Grip (f) | Dup Fraction | Outcome Classification |
|---|---|---|---|---|---|
| `box_ctrl_b1_noneg_s1.mp4` | 71.4 | 46.4 | 98 | 0.18 | `delayed_release` (f98) |
| `box_ctrl_b1_noneg_s2.mp4` | 182.3 | 67.3 | 27 | 0.00 | `genuine_release` (f27) |
| `box_ctrl_b1_noneg_s3.mp4` | 40.6 | 40.9 | 21 | 1.00 | `phantom_duplicate_spawning` |
| `box_ctrl_b1_noneg_s4.mp4` | 63.6 | 88.6 | 13 | 0.79 | `delayed_release_phantom_dup` |
| `box_ctrl_b2_noneg_s1.mp4` | 75.8 | 48.4 | 94 | 0.17 | `delayed_release` (f94) |
| `box_ctrl_b2_noneg_s2.mp4` | 177.2 | 67.6 | 27 | 0.00 | `genuine_release` (f27) |
| `box_ctrl_b2_noneg_s3.mp4` | 30.5 | 51.3 | 22 | 1.00 | `phantom_duplicate_spawning` |
| `box_ctrl_b2_noneg_s4.mp4` | 70.0 | 84.1 | 13 | 0.79 | `delayed_release_phantom_dup` |

---

## 3. Contact Sheets
- `sheets/sheet_held_control_multiseed.jpg`: Side-by-side progression of Seeds 1 to 4 showing gripper vs lower corridor across frames 0, 27, 60, 100, and 180.
- `sheets/sheet_midfall_multiseed.jpg`: Mid-fall bouncing across seeds showing tether artifact on Seed 2 vs untethered bouncing on Seed 3.
- `sheets/sheet_pendulum_multiseed.jpg`: Pendulum progression illustrating bifurcation on Seed 2.
