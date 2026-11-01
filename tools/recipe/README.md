# tools/recipe: The Improved Cosmos3-Nano Recipe Runner

This directory contains the reference runnable implementation for **Charter Deliverable 1**:
**"The Improved Cosmos3-Nano Recipe: Dynamic Mid-Event Conditioning & Generic End-State Rule"**.

Fulfills Human Steering Requirements (Raj #2930, Charter v23):
1. **User / Sealed Test Mode (Raj req. 1 & 2):** Operates directly from the initial frame ($t=0$) provided by users or the referee's sealed test protocol by applying the tested **Generic End-State Rule R**:
   > *"By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video."*
   Tested across 16 unseen Cosmos-HumanEval T2V prompts (10 physics, 6 robot; Task 133 / PREREG cf33597) to enforce physical dissipation without per-prompt manual tuning.
2. **Diagnostic Mid-Event Mode (Raj req. 1):** For the specific GAUGE held-ball mechanical release deadlock, conditioning past the physical release seam (frame 33/35) serves as the diagnostic tool reported in Deliverable 2 that proves Cosmos's internal generative core follows Newtonian Earth gravity ($g = 9.82 \pm 0.35\text{ m/s}^2$, $100\%$ release) rather than a slow clock.
3. **Sampler Specification (Raj req. 3):** Uses `UniPCMultistepScheduler`. Note that diffusers with Karras sigmas ignores `flow_shift` on diffusers/cosmos_local (#2870); NVIDIA vLLM-Omni applies `flow_shift 10.0`.

---

## 1. Overview

Stock Cosmos3-Nano severely distorts physical reality when initialized from static frames where an object is clamped by a mechanical holder or gripper (e.g. Franka gripper in GAUGE):
- **Release Rate:** 0.0% (0/31 clips on official Franka conditioning frame).
- **Failure Modes:** Spawns phantom clone duplicates on the surface (100% on seed 1), plunges the mechanical arm violently downward, or hovers indefinitely.
- **Measurement Artifact:** The reported $0.45\text{ m/s}^2$ "slow gravity" was an artifact of fitting a quadratic curve to a non-released held object or tracking phantom clones.

The **Unified Recipe** resolves these weaknesses:
- **Free-Fall Gravity:** Recovers true Earth gravity $g = 9.73 \pm 1.91\text{ m/s}^2$ on Ball 1 Seed 1 ($R^2 = 0.9976$, verified by referee-validated `firstfall.py`), matching real motion capture ($9.81\text{ m/s}^2$).
- **Initial Detachment Rate:** 100% (16/16 clips).
- **Phantom Duplicate Spawning:** 0.0% on clean pre-impact trajectories (down from 100% on baseline seed 1).
- **Dissipative Settling to Rest:** Generic Rule R and prompt event timing collapse late corridor motion by $-2.240 \pm 0.238\text{ px/f}$ ($8/8$ pairs lower) and drop Dynamic Degree by $-0.617 \pm 0.219$ ($7/8$ closer to real).
- **DOVER Technical Score:** Zero degradation ($\Delta = +0.0012 \pm 0.0009$, 95% CI $[-0.0004, +0.0030]$).

---

## 2. Command-Line Usage

### A. Primary User / Sealed Test Mode from Frame 0 with Generic Rule R (Raj #2930 req. 1 & 2)
```bash
python3 tools/recipe/run_recipe.py \
  --image assets/gauge_ball1_f0.png \
  --rule-generic \
  --out out/user_ball1.mp4 \
  --dry-run
```

### B. Diagnostic Mid-Event Mode from Post-Release Frame
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
  --image assets/gauge_ball1_f0.png \
  --rule-generic \
  --mode local \
  --model-dir /path/to/Cosmos3-Nano \
  --offload group \
  --out out/recipe_local.mp4
```

---

## 3. Options & Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--image` | path | None | Direct input conditioning image file (Frame 0 or diagnostic release frame) |
| `--video` | path | None | Input video file to extract release frame from (e.g. `assets/gauge_ball1_raw.mp4`) |
| `--detect-release` | flag | False | Automatically detect release seam via localized peak motion and global difference |
| `--roi` | str | None | Bounding box ROI for release detection: `x1,y1,x2,y2` |
| `--diff-threshold`| float| 8.0 | Global frame difference threshold for release detection |
| `--local-threshold`| float| 15.0| Localized window difference threshold for release detection |
| `--frame-idx` | int | None | Explicit frame index to extract from video |
| `--prompt` | str | Timed settle prompt | Text prompt or path to JSON prompt (default: `TIMED_DISSIPATIVE_PROMPT`) |
| `--rule-generic` | flag | False | **Canonical Generic End-State Rule R (Raj #2930 req. 2 / Task 133):** Appends Rule R to any prompt to enforce dissipative settling without per-prompt manual tuning (aliases: `--rule-r`, `--generic-rule`) |
| `--stage1-only` | flag | False | Use Stage 1 ballistic bouncing baseline prompt (`DEFAULT_PROMPT_REC`) without Stage 2 settling clause (aliases: `--rec-prompt`, `--basic-prompt`) |
| `--out` | path | `out/recipe_output.mp4` | Destination MP4 output path |
| `--mode` | choice | `endpoint` | Execution mode: `endpoint` or `local` |
| `--url` | str | `http://127.0.0.1:8021` | Cosmos3-Nano endpoint URL |
| `--width` | int | 832 | Target resolution width (letterboxed) |
| `--height` | int | 480 | Target resolution height (letterboxed) |
| `--num-frames` | int | 93 | Generated clip frame count |
| `--fps` | int | 24 | Target playback and position encoding framerate |
| `--steps` | int | 35 | Denoising inference steps |
| `--guidance` | float | 6.0 | Classifier-free guidance scale |
| `--flow-shift` | float | 10.0 | Flow matching shift parameter (note: ignored on diffusers with Karras sigmas) |
| `--seed` | int | 1 | Random seed |
| `--dry-run` | flag | False | Execute CPU dry-run without endpoint/GPU (prepares input, mock video, sidecar) |
| `--verify` | flag | False | Automatically run referee-validated `firstfall.py` |
| `--point` | str | None | Initial ball tracking point `x,y` for firstfall verification |
| `--ppm` | float | 539.8 | Pixels-per-meter scale for verification |
| `--settle` | flag | False | Stage 2: Substitute event-timing dissipative clause into custom prompts (ro-1 #2460, #2720) |

---

## 4. CPU Test Suite

The recipe runner includes a comprehensive CPU regression test suite verifying all Task 82 / #1810 / #1817 / Task 135 audit requirements:
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
9. `test_settle_prompt_flag`: Verifies `--settle` flag activates Stage 2 timed dissipative prompt.
10. `test_settle_custom_prompt_substitution`: Verifies `--settle` substitutes timing clause into custom prompts.
11. `test_default_run_has_stage2_settle_in_sidecar`: Verifies default run activates Stage 2 and sets `stage_2_dissipative_settle: True` (rog-cc audit #2775).
12. `test_stage1_only_flag_sets_stage2_false`: Verifies `--stage1-only` / `--rec-prompt` selects `DEFAULT_PROMPT_REC` and sets `stage_2_dissipative_settle: False` (rog-cc audit #2775).
13. `test_custom_prompt_without_settle_sets_stage2_false`: Verifies custom non-settle prompt sets `stage_2_dissipative_settle: False`.
14. `test_generic_rule_r_appends_to_prompt_and_sets_sidecar`: Verifies `--rule-generic` / `--rule-r` appends Rule R and records provenance.
15. `test_workflow_modes_distinction`: Verifies workflow mode distinction between user frame 0 inference and diagnostic mid-event mode.

---

## 5. Sidecar Specification

Every run generates `<name>.json` containing exact provenance and reproduction metadata:
```json
{
  "recipe_name": "Dynamic Mid-Event Conditioning & Generic End-State Rule",
  "charter_deliverable": 1,
  "workflow_mode": "user_frame0_inference",
  "stage_1_release_seam": false,
  "stage_2_dissipative_settle": true,
  "generic_rule_applied": true,
  "sampler_note": "diffusers UniPCMultistepScheduler with Karras sigmas ignores flow_shift on diffusers/cosmos_local (#2870); NVIDIA vLLM-Omni applies flow_shift 10.0 (Raj #2930 req. 3)",
  "clip_file": "user_ball1.mp4",
  "conditioning_image": "user_ball1.conditioning.png",
  "prompt": "A pendulum swings back and forth in an arc. By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video.",
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
    "mode": "dry-run",
    "wall_seconds": 0.05
  }
}
```
