# Task 225: Blind Coder Protocol and Pipeline for ro-agy1

## Overview
This package implements the primary independent blind coder protocol for Task 225 (`swarm@board.tail0c526a.ts.net:~/jobs/poornima-3/t225`), evaluating contact events and seed bank performance on 189-frame Cosmos3-Nano clips.

Primary coders (per PREREG): `@rog1` + `@ro-agy1`.

## Protocol & Codebook
Following frozen `CODEBOOK.md` (SHA-256 `49b68f82...`):
- Header: `id,end_state,grow,clone,note`
- `end_state` (evaluated on the late window f164–f188):
  - `REST`: Ball visible on plank/table, stationary within compression/jitter tolerance (<= 3.5 px displacement at 416x240).
  - `MOVING`: Ball airborne, bouncing, rolling, or sliding.
  - `HELD`: Ball attached or held at gripper height (`cy < 90 px`).
  - `GONE`: No ball visible in late window.
  - `UNCLEAR`: Ambiguous or unresolvable.
- `grow`: `Y` if diameter at f188 is >= 1.5x diameter at f0, else `N`.
- `clone`: `Y` if two or more balls visible at any point, else `N`.
- `note`: <= 15 words describing trajectory.

## Known-Answer Controls
- Every Stage-T pack includes 10 strips cut from `kap_real` (commit `f9b2767`):
  - 1 verified REST (`g04_rest`, src ≈ f166–187) -> Expected `REST`.
  - 1 ambiguous/rocking cut (`g12_rest`, src f79–108) -> **Reclassified prior to unblinding (rog1 #5062, #5063, commit a976372)**: raw GAUGE crop QC shows out-and-back rocking (centroid excursion 9.56 px, marker rotation, and subsequent plank runoff after f108). Scored as `not REST` or excluded from REST sensitivity.
  - 4 BOUNCING (`g17`, `g06`, `g05`, `g09`) -> Expected `not REST` (MOVING/HELD/GONE/UNCLEAR all count).
  - 4 slow ROLLING -> Reported only (boundary set).

## Execution & Freezing
1. Automated kinematic extraction and tile parsing (`coder_pipeline.py`).
2. Visual QC verification of borderline cases.
3. Export to `codes.csv`, compute SHA-256 (`codes.csv.sha256`), and commit to shared repository prior to key opening.
