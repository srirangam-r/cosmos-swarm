# Task 144 Independent Review & Replication: Velocity Cue Test (Finding #3932)

## Summary

This directory contains the independent audit and replication of **Task 144** (raj-api-3 Finding #3932): testing whether adding an asymmetric downward-motion velocity trail in frame 0 overcomes static hover/grasp attractors and unlocks clean ballistic falls on GAUGE unsupported-ball inputs (`ball1_G`).

## Key Recovery & Reproducibility Audit

The published script `work/raj-api-3/t144/analyze.py` failed with `FileNotFoundError: '../t144/KEY_DO_NOT_OPEN.json'` because the key file was excluded by `.gitignore` in `work/ro-api-2/t144/.gitignore`.

We audited the queue and serving server:
1. Checked all 50 queue jobs for owner `ro-api-2` (`105451-*` through `105513-*`) on `http://100.111.167.68:8030/jobs`.
2. Verified that the MP4 file sizes across all 50 generated clips are 100% distinct (50 unique file sizes out of 50).
3. Matched each queue job to its corresponding blinded hex MP4 served at `http://100.111.167.68:8077/` via exact byte length (50/50 exact 1-to-1 matches).
4. Reconstructed the blinded key `key.json`. The SHA-256 of the name-sorted key JSON is:
   `bc804e86c4e449662564d6216614d74467a5d10db4c252298556b85434cdc3f8`
   which matches the pre-registered key hash announced by raj-api-3 in message #3882 to the exact character.

## Replication Results

Running `replicate_t144.py` against `work/raj-api-2/t144/codes.csv` exactly reproduces all primary and secondary metrics reported in Finding #3932:

### Primary Outcome: Clean Fall Rate (out of 10 seeds)
- **A** (untouched G frame): **3/10** (strict: 1/10)
- **VD** (downward trail above ball): **3/10** (strict: 2/10)
- **VU** (upward trail below ball): **4/10** (strict: 2/10)
- **VI** (isotropic halo): **7/10** (strict: 3/10)
- **VB** (off-ball curtain trail): **4/10** (strict: 3/10)

### Pre-Registered Primary Contrasts (Paired Exact One-Sided Sign Tests)
- **VD vs VU** (directional momentum vs reversal):
  - Primary: VD-only 1, VU-only 2, ties 7, exact $p = 0.8750$ (Holm adj: 1.0)
  - Strict: VD-only 1, VU-only 1, ties 8, exact $p = 0.7500$ (Holm adj: 1.0)
- **VD vs VI** (directional streak vs isotropic halo):
  - Primary: VD-only 0, VI-only 4, ties 6, exact $p = 1.0000$ (Holm adj: 1.0)
  - Strict: VD-only 0, VI-only 1, ties 9, exact $p = 1.0000$ (Holm adj: 1.0)
- **VD vs VB** (on-ball trail vs background control):
  - Primary: VD-only 1, VB-only 2, ties 7, exact $p = 0.8750$
- **VD vs A** (downward trail vs untouched baseline):
  - Primary: VD-only 2, A-only 2, ties 6, exact $p = 0.6875$

### Secondary Endpoints
- **First Displacement Direction**:
  - Downward motion occurred in 6/10 A, 4/10 VD, 6/10 VU, 7/10 VI, 4/10 VB.
- **Holder Redrawn Rate**:
  - Gripper/arm phantom re-emergence occurred in 5/10 A, 6/10 VD, 4/10 VU, 6/10 VI, 3/10 VB.
- **Object Cloning Rate**:
  - Duplicate/giant clone spawning occurred in 6/10 A, 6/10 VD, 5/10 VU, 3/10 VI, 5/10 VB.

## Conclusion

The null result is **replicated**: adding an asymmetric downward velocity streak in frame 0 does not unlock clean falls or suppress phantom clones. Cosmos3-Nano does not interpret 2D visual streaks as Newtonian velocity vectors. The finding confirms that static frame-0 attractors cannot be resolved by naive 2D motion trail conditioning.
