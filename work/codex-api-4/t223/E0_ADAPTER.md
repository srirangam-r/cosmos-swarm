# E0 native-video adapter, version 1

Added before viewing any `raj-noise` outcomes. This implements the primary
temporal-change metric of PROTOCOL.md without changing its estimand. It is a
pixel comparison tool, **not a validated physics estimator**. Manufactured
FFV1 videos verify the software; they are not referee-planted cases.

The design manifest from the experiment owner is still pending. The schema below
is an input interface, not a substitute design or a selected comparison. Freeze
the actual owner-supplied design and reference/target GPUs before outcome access.

```bash
python3 work/codex-api-4/t223/test_e0_video.py
python3 work/codex-api-4/t223/e0_video.py frozen_design.json artifacts.json --out e0.json
```

Requires Python, NumPy and OpenCV; verification also needs FFmpeg. The existing
numerical core remains byte-for-byte unchanged. Artifact paths are relative to
the artifact index. Both input JSON hashes, all native video hashes, decoder
contracts, seed order, full distance matrix and per-reference-seed contributions
are retained. Output is deterministic on the tested decoder versions.

`frozen_design.json` is one comparison stratum. Illustrative fields only:

```json
{
  "schema_version": 1,
  "experiment": "E0",
  "stratum_id": "OWNER-TO-SUPPLY",
  "reference": {"gpu_type": "OWNER-TO-SUPPLY", "stack_id": "OWNER-TO-SUPPLY"},
  "target": {"gpu_type": "OWNER-TO-SUPPLY", "stack_id": "OWNER-TO-SUPPLY"},
  "input_sha256": "OWNER-TO-SUPPLY",
  "prompt_sha256": "OWNER-TO-SUPPLY",
  "noise_device": "cpu",
  "settings": {
    "width": 832, "height": 480, "num_frames": 93, "fps": 24,
    "steps": 35, "guidance": 6, "sampler": "OWNER-TO-SUPPLY"
  },
  "seeds": [101, 102],
  "runs": [
    {"run_id": "r101", "arm": "reference", "seed": 101},
    {"run_id": "r102", "arm": "reference", "seed": 102},
    {"run_id": "t101", "arm": "target", "seed": 101},
    {"run_id": "t102", "arm": "target", "seed": 102}
  ]
}
```

`artifacts.json` supplies exactly one artifact for every frozen run:

```json
{
  "artifacts": [
    {"run_id": "r101", "clip_path": "clips/r101.mp4", "clip_sha256": "ACTUAL-SHA256"},
    {"run_id": "r102", "clip_path": "clips/r102.mp4", "clip_sha256": "ACTUAL-SHA256"},
    {"run_id": "t101", "clip_path": "clips/t101.mp4", "clip_sha256": "ACTUAL-SHA256"},
    {"run_id": "t102", "clip_path": "clips/t102.mp4", "clip_sha256": "ACTUAL-SHA256"}
  ]
}
```

Repeated run IDs, repeated arm/seed cells, missing or extra artifacts, invalid
seed lists, changed video bytes, native frame-count/fps/geometry mismatches all
stop the primary comparison. Artifact index ordering cannot alter seed pairing.
A failed contract must be reported; do not generate a smaller post hoc design
to make it pass. Separate within-host repeats are separate predeclared strata,
not extra seed observations.

The exact grayscale implementation is float64 BT.601 luma
`(0.299 R + 0.587 G + 0.114 B)/255`, followed by OpenCV `INTER_AREA` resize to
208x120. No padding is removed and no temporal alignment is fitted. Frame 0 is
excluded as a direct RGB observation, but **f1-f0 remains the first change**.
With T decoded frames there are T-1 change arrays. Distances average absolute
differences over every change, row and column; units are fractions of full
grayscale range. Native videos must be at least 208x120 to avoid upsampling.

The output's GPU/stack/noise/settings fields are explicitly **design declarations**.
The adapter does not authenticate those fields from video pixels. Its provenance
gate always reads `pending`: frozen manifest versus actual queue requests,
native server execution metadata, checkpoint/sampler/sigmas, and executed CPU
noise shape/dtype/hash still require a separate audit once Raj supplies their
schema. In particular, the requested `noise_device=cpu` is never labeled verified
by this tool. A correspondence p-value cannot clear that provenance gate.

This adapter produces one E0 comparison; full registered-family Holm correction,
CPU-versus-CUDA advantage differences, raw RGB/label/period secondary metrics,
same-host repeat coverage and E1-E3 real-data joins remain pending. No thresholds
for cross-GPU equivalence or NVIDIA noninferiority are introduced.
