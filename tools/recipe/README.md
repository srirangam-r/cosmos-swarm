# tools/recipe: Candidate Cosmos3-Nano Recipe Runner

**Status:** This is a candidate runner, not a demonstrated general improvement.
Rule R's effectiveness on non-ball scenes and the complete NVIDIA scoreboard
remain under evaluation. The mid-event measurements below use later real-video
frames and do not establish a frame-0 recipe (Raj #2930; task 136, #3059).
Image role is a caller declaration, not something inferred or verified by the
runner. Endpoint sampler details must be obtained from the endpoint operator.

This runner supports two distinct workflows:
1. **Candidate frame-0 mode:** Applies **Generic End-State Rule R** to a caller-supplied first frame and plain-text prompt:
   > *"By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video."*
2. **Diagnostic mid-event mode:** Uses a later frame or motion-onset detector. This is not a valid frame-0 recipe input (Raj #2930).
3. **Sampler provenance:** Local mode records scheduler configuration. The effective remote sampler is unknown unless separately verified with its operator. Diffusers with Karras sigmas ignores requested `flow_shift` (#2870).

---

## 1. Overview

Results from later-frame conditioning and the timed ball-specific prompt are
diagnostics of those inputs and prompts, not evidence that Rule R fixes
first-frame inputs. Follow the board findings and task 133 for matched controls,
uncertainties, and limitations before drawing conclusions.

---

## 2. Command-Line Usage

### A. Primary User / Sealed Test Mode from Frame 0 with Generic Rule R (Raj #2930 req. 1 & 2)
```bash
python3 tools/recipe/run_recipe.py \
  --image assets/gauge_ball1_f0.png \
  --image-role frame0 \
  --prompt 'A ball falls and bounces on a plank.' \
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
  --image-role frame0 \
  --prompt 'A ball falls and bounces on a plank.' \
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
| `--image-role` | choice | `unspecified` | Caller-declared `frame0` or `diagnostic`; the runner cannot verify image origin |
| `--video` | path | None | Input video file to extract release frame from (e.g. `assets/gauge_ball1_raw.mp4`) |
| `--detect-release` | flag | False | Automatically detect release seam via localized peak motion and global difference |
| `--roi` | str | None | Bounding box ROI for release detection: `x1,y1,x2,y2` |
| `--diff-threshold`| float| 8.0 | Global frame difference threshold for release detection |
| `--local-threshold`| float| 15.0| Localized window difference threshold for release detection |
| `--frame-idx` | int | None | Explicit frame index to extract from video |
| `--prompt` | str | Timed settle prompt | Text prompt or path to a JSON string; required with `--rule-generic`. JSON objects/arrays cannot be combined with that flag. |
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

The CPU regression tests exercise both the earlier recipe checks and mocked
frame-0, prompt and local/remote request contracts. They do not run Nano or an endpoint:
```bash
python3 -m unittest discover -s tools/recipe -p 'test_*.py'
python3 -m unittest discover -s tests -p 'test_recipe.py'
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

Every run writes `<name>.json` and the actual letterboxed conditioning PNG.
The sidecar records its SHA-256, source path, selected video frame index or
caller-declared image role, effective prompt, requested generation settings,
and mode-specific provenance. A diagnostic input is not necessarily a verified
release seam. `flow_shift_requested` records a request, not its effective
schedule. `sampler_effective` records the local scheduler configuration, is
unknown for a remote endpoint, and is `not_run` for a dry run. Dry runs write
at most 24 mock frames and record that separately in `generated_num_frames`.
