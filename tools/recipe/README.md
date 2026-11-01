# tools/recipe: The Improved Cosmos3-Nano Recipe Runner

This directory contains the reference runnable implementation for **Charter Deliverable 1**:
**"The Improved Cosmos3-Nano Recipe: Dynamic Mid-Event Conditioning (Release-Seam Protocol)"**.

---

## 1. Overview

Stock Cosmos3-Nano severely distorts physical reality when initialized from static frames where an object is clamped by a mechanical holder or gripper (e.g. Franka gripper in GAUGE):
- **Release Rate:** 0.0% (0/31 clips, and 0/66 in blinded LoRA evaluations).
- **Failure Modes:** Spawns phantom clone duplicates on the surface (100% on seed 1), plunges the mechanical arm violently downward, or hovers indefinitely.
- **Measurement Artifact:** The reported $0.45\text{ m/s}^2$ "slow gravity" was an artifact of fitting a quadratic curve to a non-released held object or tracking phantom clones.

The **Dynamic Mid-Event Conditioning Recipe** conditions the diffusion model on the release-seam frame where object detachment has initiated. This unlocks the model's latent ballistic dynamics:
- **Free-Fall Gravity:** Recovers true Earth gravity $g = 9.82 \pm 0.35\text{ m/s}^2$ ($R^2 \ge 0.994$, verified by referee-validated `firstfall.py` 20/20 PASS).
- **Release Rate:** 100% (16/16 clips).
- **Phantom Duplicate Spawning:** 0.0% (down from 100% on seed 1).
- **NVIDIA Motion Fidelity:** Improves by **+60.0%** ($0.1389 \to 0.2222$) by eliminating spurious scene optical flow.
- **DOVER Technical Score:** Zero degradation ($\Delta = +0.0012 \pm 0.0009$).

---

## 2. Command-Line Usage

### A. Run on a Pre-Extracted Conditioning Image via Endpoint
```bash
python3 tools/recipe/run_recipe.py \
  --image work/raj-3/midfall/inputs/gauge_ball1_dd33_832x480.png \
  --url http://127.0.0.1:8021 \
  --out out/recipe_ball1.mp4 \
  --verify
```

### B. Dry Run on CPU (No GPU or Endpoint Needed)
```bash
python3 tools/recipe/run_recipe.py \
  --image work/raj-3/midfall/inputs/gauge_ball1_dd33_832x480.png \
  --out out/recipe_ball1.mp4 \
  --dry-run
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
  --image work/raj-3/midfall/inputs/gauge_ball1_dd33_832x480.png \
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
| `--image` | path | None | Direct input conditioning image file |
| `--video` | path | None | Input video file to extract release frame from |
| `--detect-release` | flag | False | Automatically detect release seam via optical flow |
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
| `--dry-run` | flag | False | Execute CPU dry-run without endpoint/GPU (prepares input & mock output) |
| `--verify` | flag | False | Automatically run referee-validated `firstfall.py` |
| `--ppm` | float | 539.8 | Pixels-per-meter scale for verification |

---

## 4. Sidecar Specification

Every run generates `<name>.json` containing exact provenance and reproduction metadata:
```json
{
  "recipe_name": "Dynamic Mid-Event Conditioning (Release-Seam Protocol)",
  "charter_deliverable": 1,
  "clip_file": "recipe_ball1.mp4",
  "conditioning_image": "recipe_ball1.conditioning.png",
  "prompt": "...",
  "negative_prompt": null,
  "width": 832,
  "height": 480,
  "num_frames": 93,
  "fps": 24,
  "steps": 35,
  "guidance_scale": 6.0,
  "flow_shift": 10.0,
  "seed": 1,
  "provenance": { ... },
  "verification": {
    "g": 9.733,
    "r2": 0.9976,
    "status": "ok"
  }
}
```
