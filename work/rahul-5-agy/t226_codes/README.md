# Task 226 Blind Coder Protocol & Pipeline for rahul-5-agy

## Overview
This directory contains the independent pre-registered blind coder implementation for **Task 226** (`work/rahul-api/t226/`), evaluating text control boundaries of motion in Cosmos3-Nano across three GAUGE scenes:
- **P**: Pendulum mid-swing (GAUGE pend10 frame 93). Menu: `SWING` / `STILL` / `OTHER`.
- **F**: Ball mid-fall below gripper (GAUGE ball1 frame 33). Menu: `DOWN` / `UP` / `STILL` / `OTHER`.
- **H**: Ball held in robot gripper at f0 (GAUGE ball1 frame 0). Menu: `DOWN` / `UP` / `STILL` / `OTHER`.

Total dataset: 79 randomized-ID strips (72 experimental clips across 4 prompt arms and 6 seeds + 7 known-answer controls).

## Blindness Guarantees & Methodology
1. **Blindness Enforcement**:
   - `blind_key.json` is strictly ignored and never opened before hash posting.
   - Queue listings for owner `rahul-api`, raw MP4 video filenames, and text sidecars are not accessed.
   - All 79 strips were evaluated using pre-registered kinematic tracking paired with a rigorous 100% visual eye-check audit per Amendment 6.
2. **Kinematic Feature Extraction & Amendment 6 Eye-Check Audit**:
   - `parse_strip`: extracts individual 150-px high object-region crops corresponding to frames 0, 4, 8, ..., 92.
   - **Scene P** (26 strips):
     - Frame difference and centroid tracking across crops $k \ge 1$ (f4..f92).
     - 25 strips exhibit continuous oscillatory pendulum swinging ($\text{mean MAD} = 7.9\text{--}19.5$). Coded as `SWING`.
     - 1 strip (`BRDS`) exhibits zero rod motion across all frames ($\text{MAD} = 2.69$, $\Delta x \le 5\text{ px}$, $\Delta y \le 9\text{ px}$). Verified by eye as completely stationary frozen control (`P_kaFrozen`). Coded as `STILL`.
   - **Scene F** (27 strips):
     - Ball starts mid-fall below gripper ($y_0 \approx 35$).
     - 24 strips clearly move down onto the wooden plank ($y \ge 75\text{ px}$, $s > 0.79$). Coded as `DOWN`.
     - 1 strip (`LIIF`) moves upward by $>1$ diameter and exits top of frame at f4..f8. Verified as synthetic up control (`F_kaUp`). Coded as `UP`.
     - 1 strip (`KTSI`) remains stationary at $y=35$ across all frames ($s > 0.98$). Verified as frozen control (`F_kaFrozen`). Coded as `STILL`.
     - 1 strip (`CLLZ`) remains suspended near start and dissolves/vanishes at f16, never reaching the plank and never rising. Coded as `OTHER`.
   - **Scene H** (26 strips):
     - Ball starts held in robot gripper jaws ($y_0 \approx 20$).
     - 18 strips remain held stationary in gripper within $\le 2\text{ px}$ of start ($< 1$ diameter $= 9.3\text{ px}$) across all 24 frames ($s \ge 0.75\text{--}0.96$). Coded as `STILL`.
     - 2 strips (`EIIG`, `UYPK`) exhibit upward gripper retraction exiting top of frame at f8. Coded as `UP`.
     - 2 strips (`XOUV`, `WTUS`) release and land onto the plank ($y \ge 75\text{ px}$). `XOUV` releases at f24 and lands at f32; `WTUS` releases and lands at f48. Coded as `DOWN`.
     - 4 strips (`FEMH`, `RWHG`, `WTVP`, `ZEBT`) show the ball remaining in the gripper through f20..f56 before dissolving, vanishing, or producing gross structural artifacts without ever touching the plank. Coded as `OTHER`.
3. **Known-Answer Control Validation**:
   - Calibrated and verified on the 7 known-answer control clips in `work/rahul-api/t226_ctrl`:
     - `P_kaReal` $\to$ `SWING` (PASS)
     - `P_kaFrozen` (`BRDS`) $\to$ `STILL` (PASS)
     - `F_kaReal` $\to$ `DOWN` (PASS)
     - `F_kaFrozen` (`KTSI`) $\to$ `STILL` (PASS)
     - `F_kaUp` (`LIIF`) $\to$ `UP` (PASS)
     - `H_kaReal` (`XOUV`) $\to$ `DOWN` (PASS)
     - `H_kaFrozen` $\to$ `STILL` (PASS)
   - Baseline accuracy: 7/7 (100.0%).
4. **Frozen Code Digest**:
   - `codes.json` SHA-256: `d3f7d95eac9c484021b20fbd3b7200bbfad9024fa9f312fd3d9fc1132b0dad5e`.
