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
   - Strip evaluation is completely automated based on physical kinematics extracted from the 11 sequence tiles and 24 object-region crops.
2. **Kinematic Feature Extraction**:
   - `parse_strip`: extracts individual 150-px high object-region crops corresponding to frames 0, 4, 8, ..., 92.
   - For Scene P: evaluates frame differences $|I_k - I_1|$ relative to frame 4 across the pendulum sector to detect rod stillness vs oscillatory swing.
   - For Scene F & H: evaluates normalized cross-correlation (NCC) template tracking of the initial ball patch from frame 0, detecting vertical rise (UP, $\ge 1$ diameter), plank contact (DOWN), or complete spatial containment (STILL, within 1 diameter).
3. **Known-Answer Control Validation**:
   - Calibrated and verified on the 7 known-answer control clips in `work/rahul-api/t226_ctrl`:
     - `P_kaReal` $\to$ `SWING` (PASS)
     - `P_kaFrozen` $\to$ `STILL` (PASS)
     - `F_kaReal` $\to$ `DOWN` (PASS)
     - `F_kaFrozen` $\to$ `STILL` (PASS)
     - `F_kaUp` $\to$ `UP` (PASS)
     - `H_kaReal` $\to$ `DOWN` (PASS)
     - `H_kaFrozen` $\to$ `STILL` (PASS)
   - Baseline accuracy: 7/7 (100.0%).
4. **Execution**:
   ```bash
   /home/sha/swarm-work/rahul-5-agy/.venv/bin/python coder_pipeline.py
   ```
   Outputs `codes.json` (79 items), `codes.json.sha256`, and `metadata.json`.
