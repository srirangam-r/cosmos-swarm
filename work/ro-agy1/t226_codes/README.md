# Task 226: Blind Coder Protocol and Pipeline for ro-agy1

## Overview
This package implements the independent blind event coder protocol for Task 226 (`work/rahul-api/t226`), assessing text control of motion boundaries across 3 real GAUGE scenes:
- **P**: Pendulum mid-swing (f93 from GAUGE pend10). Code menu: `SWING` / `STILL` / `OTHER`.
- **F**: Ball mid-fall below gripper (f33 from GAUGE ball1). Code menu: `DOWN` / `UP` / `STILL` / `OTHER`.
- **H**: Ball held in gripper at f0 (f0 from GAUGE ball1). Code menu: `DOWN` / `UP` / `STILL` / `OTHER`.

The dataset includes 72 experimental clips plus 7 randomized-ID known-answer control clips (total 79 strips), rendered in `work/rahul-api/t226/strips/` under opaque 4-letter IDs.

## Protocol & Blindness Enforcement
1. **Blindness Guarantees**:
   - `blind_key.json` is gitignored and not accessed.
   - Raw video files, prompt sidecars, and queue job logs under owner `rahul-api` are not viewed prior to code freezing.
   - All 79 strips are processed identically based purely on visual and kinematic evidence extracted from the object crops and sequence tiles.
2. **Coding Methodology**:
   - Automated kinematic feature extraction (`coder_pipeline.py`) tracks object centroids and displacements across the 24 object crops (frames 0, 4, 8, ..., 92) and 11 full-scene tiles.
   - Full eye-QC inspection verifies automated labels against visual morphology.
   - Final codes are frozen to `codes.json`, digested via SHA-256 (`codes.json.sha256`), and committed to the shared repository before unblinding.
3. **Execution**:
   ```bash
   /home/rohith/swarm-work/ro-agy1/venv/bin/python coder_pipeline.py
   ```
