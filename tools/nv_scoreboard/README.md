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
- fps comes from the sidecar `<clip>.json` key `fps` if there is one, otherwise from the container.
- Per clip it writes `dd_binary, dd_norm, dd_frac, dd_maxrad[...]` and `dover_fused, dover_technical, dover_aesthetic` (each with an `_sd` over `--dover_reps` random fragment draws).
- `--no_dd` / `--no_dover` turn either part off.

**Speed** (832x480, 189 frames): on GPU, ~15-20 s per clip for everything. On CPU, DOVER is ~17 s per draw, but RAFT-large dynamic degree takes ~8 min per clip.

## Before/after and seed noise: `compare.py` (numpy only, no GPU)
```
python compare.py noise  scores.json --real ../../work/raj-4/nv_scoreboard_real/gauge_real_matched.json
python compare.py paired before.json after.json --real ../../work/raj-4/nv_scoreboard_real/gauge_real_matched.json [--pair_by image,seed]
```
- `noise` groups clips that differ only in seed (same input image, prompt, negative prompt, settings, read from sidecars). It reports the pooled within-group seed sd per metric and the overall sd.
- `paired` matches clips across two score files. The default key is the same input image plus the same seed, because a fix may change the prompt, settings or checkpoint. Per metric it reports the paired mean AFTER−BEFORE with a bootstrap 95% CI over pairs. With `--real` it also gives the motion-fidelity gap |dd − dd_real(task)| before and after, and the CI of its change.
- Verdict: DOVER "DROP" if the CI of the paired difference lies entirely below 0. Dynamic degree is "FURTHER from real" if the CI of the gap change lies entirely above 0.
- The task (ball / pend / slope) comes from the clip basename via `--task_re`. Reference clips whose names match no task are ignored.
- Tested only on synthetic score files so far. The Cosmos seed-noise baseline is pending (task 4).

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

Not bit-identical to VBench: it uses torchvision RAFT instead of the original RAFT repo, and pyav decoding instead of cv2.

**DOVER** uses the `dover.yml` val-l1080p sampling and DOVER's own `fuse_results` for the fused score. Fragment sampling is random, so use `--dover_reps`.

## Real reference: GAUGE dev clips (measured only, never trained on)
`results/gauge_real_matched.json`. The clips were matched to the Cosmos output format with ffmpeg: `scale=832:480,fps=24`, first 189 frames, libx264 crf 18. Per-task numbers are in `findings.md` and the board post.

## Caveat for physics prompts
VBench dynamic degree is almost blind to a small moving object. The top 5% of a 832x480 frame is ~20k px, much more than a 0.06 m ball. Real GAUGE ball drops score `dd_binary=0` with `dd_norm` ~0.2. Read a dynamic-degree increase on GAUGE-style prompts as spurious camera or scene motion, not as better object motion. Always compare against real clips at the same fps and size.
