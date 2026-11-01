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
- `internals.py`, `loss_probe.py`: optional per-request model-internals hooks and a denoising-loss probe (section "Internals hooks" below). `COSMOS_OFFLOAD=0` (env) skips group offload on big GPUs (80 GB cards); the default is unchanged.
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

## Internals hooks (`extra_params.internals`) and the loss probe
Opt-in, per request. A request without `internals` runs exactly the old code path. Every hook is installed around `pipe(**call)` and removed in a `finally` (hook handles, the attention function swap, the RoPE forward), so one server process can serve many agents in turn. The sidecar gets `internals`: the spec as parsed (vectors replaced by shape + sha256), `artifact_id`, and a summary of what fired. Bad specs return **HTTP 400** with the expected shapes/ranges in the message; nothing runs on the GPU first. Through the job queue use `extra_params` as usual; steering vectors must then be `artifact` references or inline `values` (the queue cannot upload files), and the artifact ids come back in the queue sidecar's `artifact_ids`.

Vocabulary: `T` = latent frames = `(num_frames-1)//4+1`; `step` = denoising step index `0..num_inference_steps-1`; `step_range` = `[start, end)` (omit = all steps); a block is `transformer.layers[i]`, `i` in `0..35`; each step runs a **cond** and an **uncond** (CFG) transformer pass, `passes` selects which.

### 1. Temporal RoPE scaling (`rope`)
```json
{"internals": {"rope": {"temporal_scale": 0.5}}}
{"internals": {"rope": {"temporal_scale": {"0": 0.5, "3": 0.5}}}}
```
A number scales all 24 temporal `inv_freq` entries; an object maps `inv_freq` index `j` to a multiplier. Allowed `j`: `0,3,..,57` and `60..63` (H is `1,4,..,58`, W is `2,5,..,59`; others give 400). Same indexes as poornima-1's `gen92.py` (`fast05` = `{"0":0.5,"3":0.5}`). It scales text positions' temporal rotation too, since text uses the same three axes. The buffer is never edited: `rotary_emb.forward` is temporarily replaced by the class forward run on scaled frequencies (an in-place edit of `inv_freq`, as gen92 did, is silently undone by group offload, which re-copies buffers from a CPU stash). Tests: does the model's motion/physics depend on temporal frequency bands (slower or faster dynamics)? `1.0` is a bit-exact no-op. `POST /v1/probe/loss` accepts the same `rope` in its settings.

### 2. Conditioning-frame control (`conditioning`)
How the conditioning frame enters (pipeline `prepare_latents`, `_prepare_vision_segment`, transformer `forward`): the image is VAE-encoded as a clean latent for frame 0 and put in `vision_tokens`; frame 0 is in the sequence like any other frame (same full attention, no mask); only the *noisy* frames (`vision_noisy_frame_indexes`) get a timestep embedding, and the velocity of frame 0 is masked to 0 by the pipeline. Possible: change what the model *sees* for frame 0, and change who attends to it. Not possible without rewriting the pipeline: giving frame 0 a timestep (the model cannot be told the frame is noisy, and `vision_timesteps`, `mse_loss_indexes` and the output unpatchify all assume frame 0 is not predicted), and changing the held latent that the scheduler integrates (the pipeline re-masks velocity every step).
```json
{"internals": {"conditioning": {
   "noise": {"level": 0.3, "seed": 0, "step_range": [0, 35]},
   "attention_scale": {"factor": 0.3, "step_range": [0, 20], "layers": [0, 1, 2]}}}}
```
- `noise`: in the transformer input only, frame 0 becomes `(1-level)*z_cond + level*eps` (fixed `eps` from a private CPU generator, so the sampling RNG is untouched). `level` 0..1; `0` is an exact no-op. Pure input perturbation, no timestep signal.
- `attention_scale`: adds `log(factor)` to the attention logits of the keys that are conditioning-frame tokens, in the generation pathway, for the chosen blocks (default all) and steps. Queries of the conditioning frame itself keep plain attention. `factor` 1 = no change (near-identical numerically: a zero bias may select another SDPA kernel), `0` = those keys are masked out. Text (und) keys are untouched. Applies to cond and uncond passes. Needs the native/SDPA attention backend (the default); `cosmos_patch.py` now chunks calls that carry this key bias too.

Hypothesis: "I2V conditioning dominance": the model won't release a held ball because frame 0 is a clean, always-attended anchor. If dominance is the cause, weakening attention to it or noising it in early steps should free the dynamics (look for the ball leaving the hand) without destroying scene identity.

### 3. Activation capture (`capture`)
```json
{"internals": {"capture": {"layers": [12, 24], "step_range": [0, 35], "every": 5, "passes": ["cond"], "full": false}}}
```
`layers` (list or `"all"`), `step_range`, `every` (stride within the range), `passes` (default `["cond"]`), `full` (default false). A forward hook on `transformer.layers[i]` takes the block output's generation stream, the first `T*S` rows (`S` = `patch_h*patch_w` tokens per frame; row order t,h,w): `s{step:03d}_{pass}_L{layer:02d}_mean` is float32 `[T, 4096]` (mean over the `S` spatial tokens of each latent frame); with `full`, `..._full` is float16 `[T, S, 4096]`. The npz also holds `_meta` (JSON). The response header `X-Artifact-Ids` and the sidecar `internals.artifact_id` carry the id (`act_xxxxxxxx`); `GET /v1/artifacts/{id}` downloads the npz. Capture is read-only (bit-identical output) and capped at ~1 GiB per request (400 over that). Hypothesis: where and when conditioning-frame information lives or is overwritten (per-frame, per-layer, per-step), and which layers carry "motion" vs "appearance" (diff two captures, e.g. a falling vs a held ball).

### 4. Activation steering (`steer`)
```json
{"internals": {"steer": {"alpha": 4.0, "step_range": [0, 20], "passes": "both",
   "frame_profile": [0, 1, 1, 1, 1],
   "vectors": [{"layer": 12, "artifact": "act_1a2b3c4d", "key": "s010_cond_L12_mean", "average_frames": true},
               {"layer": 24, "file": "v.npy"}, {"layer": 30, "values": [0.0, "... 4096 numbers"]}]}}}
```
Adds `alpha * v` to the generation-stream output of each listed block (after the block, before the next), for the steps and passes chosen (`passes` default both; with CFG, steering only `cond` also gets amplified by the guidance scale). A vector is `[4096]` (same for every frame) or `[T, 4096]` (per latent frame; `T` must equal this request's latent frames). Sources: `artifact` + `key` (a `_mean` array of a capture; `average_frames` averages `[T,D]` to `[D]`; a `_full` `[T,S,D]` array must be reduced first), `file` (an `.npy`, or an `.npz` with `key` unless it holds one array; sent in the multipart field `internals_files`, repeatable, matched by filename), or inline `values`. `frame_profile` (`T` numbers) scales the addition per latent frame; conditioning frames are skipped unless `include_conditioning_frames: true`. Everything is validated to 400 with the expected shape in the message. `alpha: 0` is an exact no-op; blocks captured in the same request see the steered output. Hypothesis: a direction found by differencing captures (e.g. "ball released" minus "ball held", or "fall" minus "bounce") causally changes the generated dynamics.

### 6. Prompt switch during sampling (`prompt_switch`)
```json
{"internals": {"prompt_switch": {"prompt": "<another prompt>", "step_range": [0, 7]}}}
```
For the denoising steps in `step_range` (default all), the **conditional** CFG pass gets the other prompt's packed text instead of the request's `prompt`; the unconditional pass and the noisy latents are untouched. The other prompt's packing comes from a 1-step dry run before the real one (ro-1's `work/ro-1/switch_probe` method). Needs `guidance_scale > 1`. Checked on the real model (A100 and RTX Pro 6000): switching to the same prompt is bit-identical to a plain request, and switching to prompt B for every step is **bit-identical to a plain request with prompt B**; steps 0-1 only gives a clip that differs from both. Composes with the other hooks. The sidecar lists `prompt_switch_steps`. Hypothesis: when in denoising a text-level decision (e.g. the settle clause) is committed; sweep the window start/end to get a commitment curve (task 142). Steps map to sigma through the Karras schedule (#2870), so report sigma per step.

### 5. Denoising-loss probe: `POST /v1/probe/loss`
Multipart: `prompt`, `video` (mp4), optional `image` (conditioning image), optional `settings` (JSON). Returns JSON.
```json
{"sigmas": [0.1, 0.3, 0.5, 0.7, 0.9], "seeds": [1, 2], "variants": ["forward", "reverse", "freeze_first"],
 "start": 0, "num_frames": 93, "fps": 24, "size": "832x480", "image_from_video_frame0": false,
 "determinism_check": true, "rope": {"temporal_scale": 0.5}}
```
The video is decoded (width/height must be multiples of 16, or give `size`), a `4k+1`-frame window is VAE-encoded (posterior mode, like the pipeline), and for each variant x sigma x seed the server computes the rectified-flow velocity MSE `mean((v_theta(z_sigma, 1000*sigma) - (eps - z))^2)` with `z_sigma=(1-sigma)z+sigma*eps`, overall and per latent frame. Variants (applied to decoded frames before the VAE): `forward`, `reverse`, `freeze_first`. Controls from codex-api-1's probe: `eps` is drawn once per seed on the CPU and shared by every variant and sigma (paired), one conditional pass (no CFG), an identical-input repeat must agree, everything recorded. With an `image` (or `image_from_video_frame0`) the pipeline's I2V packing is used: latent frame 0 is the clean image latent, gets no timestep, and is excluded from the loss (`per_frame[0]` is null). Result keys: `rows` (`variant, sigma, seed, loss, per_frame`), `summary` (per variant: mean, per-frame mean, by sigma), `paired` (`<variant>_minus_forward`: mean delta, fraction positive, per-frame delta), plus settings and shapes. Hypothesis: does the model assign lower denoising loss to real than to time-reversed or frozen clips, and at which noise levels and latent frames (e.g. around the bounce)? It is a surrogate, not a likelihood. Via the queue: `{"kind": "probe_loss", "name": ..., "prompt": ..., "video": "clip.mp4", "image": "f0.png", "probe": {<settings>}}`; `cosmos_queue.py fetch` writes `<name>.json`.

### Tests
CPU only, no weights (a real tiny `Cosmos3OmniTransformer` in a fake pipeline). With the server's venv: `python test_internals.py && python test_loss_probe.py && python test_prompt_switch.py && python test_server_fake.py` (the last starts the real FastAPI app on a loopback port). `python smoke_internals.py --url ... --image ...` is the GPU smoke test: run it only on a server you started on a free GPU.

**Controls (measured on the real model).** Sampling amplifies tiny numeric differences: two clips whose settings differ
by a hair (attention factor 1.0 vs 0.999) differ by ~14/255 per pixel. So judge every hook across seeds, never one clip.
`conditioning.attention_scale` also switches attention to a different SDPA kernel (it passes a key bias), so even factor
1.0 differs from a plain clip (~10/255). Use **factor 1.0 as the control arm** for that hook, not a plain request. The
other hooks (rope 1.0, noise 0, steer alpha 0, capture) are bit-identical to plain requests.
