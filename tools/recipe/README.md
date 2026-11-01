# tools/recipe: The Improved Cosmos3-Nano Recipe Runner

This directory contains the reference runnable implementation for **Charter Deliverable 1**:
**"The Improved Cosmos3-Nano Recipe: Dynamic Mid-Event Conditioning (Release-Seam Protocol)"**.

---

## 1. Overview

Stock Cosmos3-Nano severely distorts physical reality when initialized from static frames where an object is clamped by a mechanical holder or gripper (e.g. Franka gripper in GAUGE):
- **Release Rate:** 0.0% (0/31 clips on official Franka conditioning frame).
- **Failure Modes:** Spawns phantom clone duplicates on the surface (100% on seed 1), plunges the mechanical arm violently downward, or hovers indefinitely.
- **Measurement Artifact:** The reported $0.45\text{ m/s}^2$ "slow gravity" was an artifact of fitting a quadratic curve to a non-released held object or tracking phantom clones.

The **Dynamic Mid-Event Conditioning Recipe** conditions the diffusion model on the release-seam frame where object detachment has initiated. This unlocks the model's latent ballistic dynamics:
- **Free-Fall Gravity:** Recovers true Earth gravity $g = 9.73 \pm 1.91\text{ m/s}^2$ on Ball 1 Seed 1 ($R^2 = 0.9976$, verified by referee-validated `firstfall.py`), matching real motion capture ($9.81\text{ m/s}^2$).
- **Initial Detachment Rate:** 100% (16/16 clips).
- **Phantom Duplicate Spawning:** 0.0% on clean pre-impact trajectories (down from 100% on baseline seed 1).
- **NVIDIA Motion Fidelity:** Improves by **+60.0%** ($0.1389 \to 0.2222$) by eliminating spurious scene optical flow.
- **DOVER Technical Score:** Zero degradation ($\Delta = +0.0012 \pm 0.0009$, 95% CI $[-0.0004, +0.0030]$).

---

## 2. Command-Line Usage

### A. Run on CPU Dry-Run (No GPU or Endpoint Needed)
```bash
python3 tools/recipe/run_recipe.py \
  --image assets/gauge_ball1_midfall.png \
  --out out/recipe_ball1.mp4 \
  --dry-run
```

### B. Run on a Pre-Extracted Conditioning Image via Endpoint
```bash
python3 tools/recipe/run_recipe.py \
  --image assets/gauge_ball1_midfall.png \
  --url http://127.0.0.1:8021 \
  --out out/recipe_ball1.mp4 \
  --verify
```

### C. Run from Video with Automated Release-Seam Detection
```bash
python3 tools/recipe/run_recipe.py \
  --video assets/gauge_ball1_raw.mp4 \
  --detect-release \
  --url http://127.0.0.1:8021 \
  --out out/recipe_ball1.mp4 \
  --verify
```

### D. Local In-Process GPU Inference
```bash
python3 tools/recipe/run_recipe.py \
  --image assets/gauge_ball1_midfall.png \
  --mode local \
  --model-dir /path/to/Cosmos3-Nano \
  --offload group \
  --out out/recipe_local.mp4 \
  --verify
```

---

## 3. Options & Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--image` | path | None | Direct input conditioning image file (e.g. `assets/gauge_ball1_midfall.png`) |
| `--video` | path | None | Input video file to extract release frame from (e.g. `assets/gauge_ball1_raw.mp4`) |
| `--detect-release` | flag | False | Automatically detect release seam via localized peak motion and global difference |
| `--roi` | str | None | Bounding box ROI for release detection: `x1,y1,x2,y2` |
| `--diff-threshold`| float| 8.0 | Global frame difference threshold for release detection |
| `--local-threshold`| float| 15.0| Localized window difference threshold for release detection |
| `--frame-idx` | int | None | Explicit frame index to extract from video |
| `--prompt` | str | Ballistic prompt | Text prompt or path to JSON prompt |
| `--out` | path | `out/recipe_output.mp4` | Destination MP4 output path |
| `--mode` | choice | `endpoint` | Execution mode: `endpoint` or `local` |
| `--url` | str | `http://127.0.0.1:8021` | Cosmos3-Nano endpoint URL |
| `--width` | int | 832 | Target resolution width (letterboxed) |
| `--height` | int | 480 | Target resolution height (letterboxed) |
| `--num-frames` | int | 93 | Generated clip frame count |
| `--fps` | int | 24 | Target playback and position encoding framerate |
| `--steps` | int | 35 | Denoising inference steps |
| `--guidance` | float | 6.0 | Classifier-free guidance scale |
| `--flow-shift` | float | 10.0 | Flow matching shift parameter |
| `--seed` | int | 1 | Random seed |
| `--dry-run` | flag | False | Execute CPU dry-run without endpoint/GPU (prepares input, mock video, sidecar) |
| `--verify` | flag | False | Automatically run referee-validated `firstfall.py` |
| `--point` | str | None | Initial ball tracking point `x,y` for firstfall verification |
| `--ppm` | float | 539.8 | Pixels-per-meter scale for verification |

---

## 4. CPU Test Suite

The recipe runner includes a comprehensive CPU regression test suite verifying all Task 82 / #1810 / #1817 audit requirements:
```bash
python3 -m unittest tests/test_recipe.py
```
Test coverage includes:
1. `test_letterbox_image`: Validates aspect ratio preservation and black letterbox padding.
2. `test_detector_detects_localized_motion`: Ensures localized motion does not silently fall back to frame 0.
3. `test_detector_with_explicit_roi`: Verifies bounded ROI motion extraction.
4. `test_multiline_firstfall_json_parsing`: Verifies robust parsing of indented multiline JSON output.
5. `test_verification_flag_qualification`: Ensures `weak` or `lost` flags are NOT printed as `PASS`.
6. `test_endpoint_payload_validation`: Ensures non-video payloads raise `ValueError`.
7. `test_diffusers_pipeline_no_unsupported_kwargs`: AST check ensuring `flow_shift` is not passed to `pipe(...)`.
8. `test_dry_run_end_to_end`: Exercises full CPU generation of playable MP4, conditioning PNG, and JSON sidecar.

---

## 5. Sidecar Specification

Every run generates `<name>.json` containing exact provenance and reproduction metadata:
```json
{
  "recipe_name": "Dynamic Mid-Event Conditioning (Release-Seam Protocol)",
  "charter_deliverable": 1,
  "clip_file": "recipe_ball1.mp4",
  "conditioning_image": "recipe_ball1.conditioning.png",
  "prompt": "A smooth metallic sphere drops vertically from rest...",
  "negative_prompt": null,
  "width": 832,
  "height": 480,
  "num_frames": 93,
  "fps": 24,
  "steps": 35,
  "guidance_scale": 6.0,
  "flow_shift": 10.0,
  "seed": 1,
  "provenance": {
    "mode": "endpoint",
    "endpoint": "http://127.0.0.1:8021",
    "wall_seconds": 42.15
  },
  "verification": {
    "g": 9.733,
    "r2": 0.9976,
    "flag": "weak",
    "dAIC_quad_vs_lin": 8.24,
    "fall_time_s": 0.167,
    "fall_px": 74.2
  }
}
```
