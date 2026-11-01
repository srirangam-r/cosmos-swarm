# hue_judge: plausibility judge for NVIDIA scoreboard item 3

This tool asks a fixed open VLM the Cosmos-HUE Yes/No/Unclear questions about each clip. HUE is `nvidia/Cosmos-HumanEval-v1`, the HUE-PaiBench v1.2 question bank. The tool reads the next-token logits for Yes/No/Unclear and reports **P(Yes)**, renormalised over those three, per question, per HUE category (Physical Laws / Visual Integrity / Geometric Reasoning / Semantic Alignment) and overall. HUE questions are phrased so that Yes = good, so higher is better.

- Judge, pinned: `Qwen/Qwen3-VL-2B-Instruct`, bf16, 16 uniformly sampled frames, short side 256 px, true timestamps passed as metadata. It is deterministic. It fits in about 6.6 GB of VRAM, so an 8 GB laptop GPU is enough.
- Speed: it encodes the video once and scores each question from a copy of the KV cache, at about 10-20 s per clip for 13 questions on an RTX 4060. Batching questions with the video repeated was about 10× slower.
- **Use the same judge, frames and settings before and after a fix.** Report paired differences over the same prompts and seeds.

## Usage
```
# custom question sets (HUE format) for GAUGE-style scenes
python3 make_gauge_questions.py gauge_questions.json
python3 hue_judge.py --questions gauge_questions.json \
   --clip a.mp4 --sample gauge_ball --clip b.mp4 --sample gauge_pend --out res.json
# HUE T2V prompts: put clips in a dir named <sample_name>.mp4 (or give a sidecar json with "hue_sample")
hf download nvidia/Cosmos-HumanEval-v1 --repo-type dataset --local-dir hue
python3 hue_judge.py --questions hue/hue-v1p2-t2v-public.json --clipdir clips/ --out res.json
# judge-noise reps: --offsets 0,0.5 shifts the frame-sampling grid by half a step
python3 analyze_val.py res.json
```
For I2V, HUE's own questions need the PAI-Bench first frames, which are not in the HF dataset. For HUE dev prompts use the T2V file, where the prompt is the HUE `prompt` field.

## Validation (no Cosmos)
The test: real GAUGE dev clips (ball drop, pendulum, wood slope; 4 each; 8 s, 832x480 @ 24 fps) against five corruptions of the same clip: freeze (one frame repeated), reverse, frame shuffle, Gaussian noise sd 45, and a splice where the second half comes from another scene. A usable judge should score the original higher than each corruption, paired over clips. Results are in `val_gauge.json` and `val_summary.json` (see the board, task 10).

## Known limits
- The 2B judge has a yes-bias, and some physics questions it misses (e.g. "does the ball speed up as it falls"). Treat per-question answers as noisy. Use category means over many questions and clips.
- The GAUGE question sets were written by rog1 (`make_gauge_questions.py`). They are not NVIDIA's.

## Before/after on the HUE dev subset (for any fix)
- Dev subset: `work/rog1/hue_dev/hue_dev_subset.json`, which is HUE v1.2 T2V physics ×10 + robot ×6. The base-Nano jobs are in `work/rog1/hue_dev/jobs_base.jsonl` (832x480, 93 f, 24 fps, 35/6/10, no negative, seed 1 for all 16, plus seed 2 for 6 physics prompts as seed noise). Each sidecar has `hue_sample`.
- To score a fix, generate the same jobs with the fixed model under the same names, then:
```
python3 hue_judge.py --questions hue-v1p2-t2v-public.json --clipdir after/ --offsets 0,0.5 --out after.json
python3 compare.py before.json after.json --seednoise before.json
```
`compare.py` gives the paired diff (after − before) ± SE per category, and the per-clip seed SD from the `_s1`/`_s2` pairs.
