# nv_scoreboard (raj-4, task 4): DOVER + VBench dynamic degree

Scores a folder of mp4s on two NVIDIA-scoreboard items:
- **DOVER** video quality (technical head, aesthetic head, fused overall in [0,1]);
- **VBench dynamic degree** (motion amount), plus continuous versions of it.

Out of scope: robot-clip prediction (`tools/robot_pred`) and the plausibility judge.

## Install
```
git clone https://github.com/VQAssessment/DOVER  <DOVER_DIR>
curl -L -o <DOVER_DIR>/pretrained_weights/DOVER.pth https://huggingface.co/teowu/DOVER/resolve/main/DOVER.pth   # 239,729,097 bytes, sha256 f4a42c0b...
pip install torch torchvision av decord timm einops pyyaml scipy scikit-video opencv-python-headless
```
A partial download gives "failed finding central directory". Check the file size.

## Run
```
python score.py CLIPS_DIR [more clips] --dover_dir <DOVER_DIR> --device cuda|cpu --dover_reps 3 --out scores.json
```
- Motion sampling uses the container playback fps. Sidecar `fps` and `cond_fps` describe generation and may differ from playback; if `play_fps` is provided, it must match the container (within 0.1% or 0.01 fps). New outputs record `fps_source=container`. Legacy outputs may have sampled using conditioning fps: rescore them when fps differs.
- Per clip it writes `dd_binary, dd_norm, dd_frac, dd_maxrad[...]` and `dover_fused, dover_technical, dover_aesthetic` (each with an `_sd` over `--dover_reps` random fragment draws).
- `--no_dd` / `--no_dover` turn either part off.
- Sidecar metadata is embedded in new score files so comparisons remain portable. Duplicate clip basenames are rejected, including collisions with existing output entries; use separate output files or unique names.

**Speed** (832x480, 189 frames): on GPU, ~15-20 s per clip for everything. On CPU, DOVER is ~17 s per draw, but RAFT-large dynamic degree takes ~8 min per clip.

## Before/after and seed noise: `compare.py` (numpy only, no GPU)
```
python compare.py noise  scores.json --real ../../work/raj-4/nv_scoreboard_real/gauge_real_matched.json
python compare.py paired before.json after.json --real ../../work/raj-4/nv_scoreboard_real/gauge_real_matched.json [--pair_by image,seed]
```
- Use a stable, unique `image_id` (or `image_sha256`) in each sidecar, identical for the same input across runs. Otherwise the entire image path is used; basename-only matching is unsafe. Missing or duplicate pairing keys and unmatched runs are errors.
- `noise` groups clips by image, prompt, negative prompt and listed settings. It requires explicit image, prompt, negative prompt (null and empty string are distinct valid values), seed, num_frames, fps, steps, guidance, flow_shift, width and height. Repeated seeds in a group are rejected. It also separates recorded `model`, `checkpoint`, `inference_stack`, `use_duration_template`, `use_resolution_template`, `use_system_prompt`, `negative_metadata_mode`, and `noise_context` (an optional object for other generation settings); these are read at the top level or in `extra_params`, and conflicting values are rejected. Absent fields are reported as unknown and grouped separately from explicit values. Unknown settings may differ even within a group: verify checkpoint, stack, templates and other conditioning manually. Explicit null's interpretation depends on the inference stack. Pooled within-group seed SD is not uncertainty across scenes.
- `paired` matches clips using image and seed by default. It averages seeds within each scene, weights scenes equally, and bootstraps scenes for a descriptive 95% CI of AFTER−BEFORE. With `--real`, the per-clip gap |dd − dd_real(task)| is descriptive and pair-weighted; its reference uncertainty is not included. It is **not NVIDIA's motion-fidelity score**: the comparator does not calculate the three-seed motion-control penalty or NVIDIA's dataset-level aggregation. A single scene cannot provide a scene-level CI. Use several independent scenes; a small-sample bootstrap may still be unreliable.
- No automated non-inferiority verdict is provided. A CI crossing zero does not establish no degradation: specify an acceptable margin in advance and use an appropriate design and interval, including reference uncertainty for motion fidelity.
- The task (ball / pend / slope) comes from the clip basename via `--task_re`. Reference clips whose names match no task are ignored.
- Seed-noise grouping also separates recorded `cond_fps`, `play_fps`, scored fps and its source; missing values remain unknown. Paired comparisons can intentionally vary fps, so check playback rate and use a real reference at the corresponding playback fps manually. The comparator has synthetic regression checks and a sidecar compatibility check; the Cosmos seed-noise baseline is pending (task 4). Older score files without embedded metadata still require their sidecars at the recorded paths.

## Definitions
**Dynamic degree** is a re-implementation of VBench's `dynamic_degree.py`:
- frames sampled every `round(fps/8)`;
- RAFT-things (torchvision `raft_large` `C_T_V1`), 20 iterations, inputs padded to /8;
- per frame pair, `max_rad` = mean of the top 5% of flow magnitudes;
- `thres = 6*min(H,W)/256` and `count_num = round(4*n_frames/16)`;
- `dd_binary = [#pairs with max_rad > thres >= count_num]`. VBench's set score is mean(dd_binary).

Two continuous companions:
- `dd_norm` = mean max_rad / (min(H,W)/256), in px at a 256-px short side;
- `dd_frac` = fraction of pairs above the threshold.

Not bit-identical to VBench: it uses torchvision RAFT instead of the original RAFT repo, PyAV decoding instead of cv2, and removes padding from the flow before computing the top-5% statistic (VBench scores the padded flow). An independent comparison on 12 separately re-encoded 832x480 real clips agreed on all 12 binary scores; see `work/rog2/dd_replication/compare_raj4.txt`. This does not establish equivalence on other sizes or clips near the threshold.

**DOVER** uses the `dover.yml` val-l1080p sampling and DOVER's own `fuse_results` for the fused score. Fragment sampling is random, so use `--dover_reps`.

## Real reference: GAUGE dev clips (measured only, never trained on)
`results/gauge_real_matched.json`. The clips were matched to the Cosmos output format with ffmpeg: `scale=832:480,fps=24`, first 189 frames, libx264 crf 18. Per-task numbers are in `findings.md` and the board post.

## Caveat for physics prompts
VBench dynamic degree is almost blind to a small moving object. The top 5% of a 832x480 frame is ~20k px, much more than a 0.06 m ball. Real GAUGE ball drops score `dd_binary=0` with `dd_norm` ~0.2. Read a dynamic-degree increase on GAUGE-style prompts as spurious camera or scene motion, not as better object motion. Always compare against real clips at the same fps and size.

## Experimental FPS-band motion fidelity aggregation

`motion_fidelity.py` implements the Cosmos 3 technical report eqs. 10–11 using the `dd_binary` scores above. Supply a hand-audited JSON manifest with each band, real-reference clip, prompt, and exactly three distinct integer seeds per prompt. Paths are relative to the manifest; `key` is the exact top-level clip key in the score JSON:

```json
{"bands": [{"id": "24fps", "reference": [
  {"file": "real.json", "key": "real1.mp4"}
], "prompts": [{"id": "scene1", "clips": [
  {"file": "generated.json", "key": "s1.mp4", "seed": 1},
  {"file": "generated.json", "key": "s2.mp4", "seed": 2},
  {"file": "generated.json", "key": "s3.mp4", "seed": 3}
]}]}]}
```

```
python motion_fidelity.py manifest.json --ddof 0 --zero-denominator zero --out mf.json
python -m unittest discover -s tools/nv_scoreboard -p 'test_motion_fidelity.py' -v
```

Both convention flags are mandatory: NVIDIA does not specify the variance denominator, and the formula is 0/0 for three static seeds. `zero` substitutes zero for that case; `error` refuses to calculate. These are user choices, not verified NVIDIA conventions. Output includes each triplet, variance, MC, zero-case flag, band-level generated and reference DD, MF, and equally weighted band mean. The tool refuses duplicate file/key references, duplicate seeds, incomplete triplets and mismatched recorded playback fps. It does not establish video identity across different score files, or check seed labels against sidecars. Audit those, reference representativeness, conditioning, actual playback rate, resolution, duration and event matching manually. The original paper uses 5-second, 480p 16:9 generated clips and ~100 reference videos per FPS band. Scores from the existing GAUGE reference file need duration matching before use. This is an approximation due to the VBench implementation differences above; NVIDIA's exact conventions and DOVER scaling are unknown. No composite or non-inferiority verdict is computed. No fresh video scoring or planted validation was performed for this algebraic aggregation.
