# cosmos_local (raj-1): Cosmos3-Nano on one 24 GB GPU + a vLLM-Omni-compatible endpoint

Runs `nvidia/Cosmos3-Nano` with diffusers (`Cosmos3OmniPipeline`, bf16) on a 24 GB laptop RTX 5090. The 15B transformer uses leaf-level group offload to CPU (needs ~40 GB of CPU RAM). The safety checker is off.

## Files
- `server.py`: FastAPI server with **the same request format as vLLM-Omni** `POST /v1/videos/sync` (multipart). It returns `video/mp4`.
  - Fields: `prompt, negative_prompt, size, num_frames, fps, num_inference_steps, guidance_scale, flow_shift, seed, extra_params`, plus the file `input_reference`.
  - Leaving out `input_reference` gives T2V.
  - Forward dynamics: `extra_params.action_mode="forward_dynamics"` with `domain_name, action_chunk_size, image_size, view_point, action`. These map onto diffusers' `CosmosActionCondition`, so `tools/robot_pred/generate.py` works unchanged.
  - Other `extra_params`: `use_resolution_template`, `use_duration_template`, `use_system_prompt`, `crf` (default 0 = lossless x264), and `client` (a label stored in the sidecar).
  - Requests run one at a time, in arrival order.
  - The server keeps every clip with a JSON sidecar in `out_srv/`. The response headers `X-Clip-Id` and `X-Seconds` identify the clip and its generation time.
  - `GET /health` reports busy, waiting and served.
- `cosmos_patch.py`: **required on GPUs that also drive a display.** One 189-frame attention call (~75k query tokens) exceeds the X watchdog and crashes with `CUDA_ERROR_LAUNCH_TIMEOUT`. The patch splits non-causal attention into query chunks (`COSMOS_QCHUNK`, default 8192). This is exact: the max abs diff vs unchunked is 5e-4, which is bf16 rounding.
- `run_server.sh`: keeps the server running and restarts it if it dies.
- `client.py`: runs a jobs.jsonl against an endpoint (retries while the server restarts) and writes `<name>.mp4` + `<name>.json`.
- `gen.py`: the same jobs run in-process, with no server.

## Timing (5090 laptop, 832x480, offload)
- 33 frames: ~11 s/step.
- 189 frames: ~25 s/step, so ~15 min per clip at 35 steps.
- Bridge forward dynamics, 256², 17 frames: ~2.5 s/step.

## Install
`uv pip install "diffusers @ git+https://github.com/huggingface/diffusers.git" torch torchvision transformers accelerate fastapi uvicorn python-multipart av opencv-python-headless requests`
Tested with torch 2.14.1+cu130 and diffusers 0.42.0.dev0.

## NVIDIA-reference negative branch (rog2, `neg_meta.py`)
By default diffusers builds the CFG negative as `"" + INVERSE metadata` ("The video is **not** 7.9 seconds long and is **not** of 24 FPS. This video is **not** of 480x832 resolution."). NVIDIA's cosmos-framework image2video defaults instead use its JSON quality negative plus the **SAME** metadata as the positive, so the duration/fps text cancels in the CFG difference (board findings 369, 382).
- `extra_params.negative_metadata_mode`: `"inverse"` (default, unchanged behaviour) or `"same"` (cosmos-framework reference).
- `extra_params.negative_preset`: `"nvidia_default"` puts `assets/cf_default_neg_prompts.json` (cosmos-framework @55f0554d `defaults/image2video`) into the negative, serialized as `json.dumps(json.loads(file))` like cosmos-framework. It overrides `negative_prompt`.
- `gen.py` takes the same two keys per job line. The sidecar records `negative_metadata_mode` and the resolved negative text.
- `test_neg_meta.py <diffusers pipeline_cosmos3_omni.py>` runs the pinned diffusers `tokenize_prompt` on a stub tokenizer. It checks that the default is unchanged and that `same` + `nvidia_default` gives exactly cosmos-framework's SAME-mode negative text (5 frame/fps combinations, PASS at diffusers 86ef420b).
- **Running servers must `git pull` and restart to get this.** An old server silently ignores these keys, so check the sidecar's `negative_metadata_mode`.
