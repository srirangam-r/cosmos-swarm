# Independent review of finding 369 (ro-2 pipeline audit). Task 29, rog2

I read the source myself (clones made in shift 3, 2026-11-01). Excerpts with line numbers are in `code_excerpts.txt`.
- diffusers @ 86ef420b17363c28 (the commit our servers run), `src/diffusers/pipelines/cosmos/pipeline_cosmos3_omni.py`
- vllm-omni @ 2f155262c537 (main), `vllm_omni/diffusion/models/cosmos3/pipeline_cosmos3.py`
- NVIDIA cosmos-framework @ 55f0554d0bf1 (main), `cosmos_framework/inference/{defaults/image2video/sample_args.json,args.py,inference.py}`

## How each I2V path builds the CFG text branches (plain-text prompt P, no negative supplied, 189 f @ 24 fps, 832x480)

| path | cond text | uncond text | system prompt (I2V) |
|---|---|---|---|
| diffusers @86ef420b (our servers) | P + "The video is 7.9 seconds long and is of 24 FPS." + "This video is of 480x832 resolution." | "" + "The video is **not** 7.9 seconds long and is **not** of 24 FPS. This video is **not** of 480x832 resolution." (INVERSE) | on (`default_use_system_prompt=True`) |
| vLLM-Omni main, defaults | P only (`use_duration_template`/`use_resolution_template` default **False**) | "" (inverse mode is the default, but it only adds anything when the templates are on) | off (`use_system_prompt` defaults to `is_v2v`, False for I2V) |
| cosmos-framework `image2video` defaults (NVIDIA reference) | P + duration + resolution templates | **default JSON negative `neg_prompts.json`** + the **SAME** duration/resolution text (`negative_metadata_mode: none` + `negative_prompt_keep_metadata: true` → promoted to SAME) | vlm_config default (not checked) |

## Verdict on 369
1. **Replicated.** diffusers swaps a None negative for "" and appends INVERSE templates. CFG then pushes along "7.9 s / 24 FPS" vs "not 7.9 s / not 24 FPS".
   **Extension:** this is NOT what NVIDIA's reference does. cosmos-framework puts the SAME metadata in both branches, so the duration/fps text cancels in the CFG difference. On top of that it uses a long JSON quality negative by default. vLLM-Omni puts no metadata in either branch. So the three "official" stacks run three different CFG contrasts on duration and fps, and ours is the only one that amplifies them.
2. **Replicated in substance.** NVIDIA's defaults include a default negative prompt (the JSON `neg_prompts.json`), so "no negative prompt" is off-reference in cosmos-framework too. vLLM-Omni wraps JSON-object prompts with metadata (`duration` as int seconds, `fps`, `resolution`, `aspect_ratio`) instead of the flat templates. I did not re-check the README line numbers.
3. **Replicated.** fps-modulated temporal mRoPE (`t = frame_idx / (fps/4) * (base_fps/4)`, base 24) appears in vllm-omni `transformer_cosmos3.py:339-350` as well.
4. **The vision_encoder question is resolved: it is NOT used for video generation.** In cosmos-framework, `self.visual` (Qwen3-VL ViT) is only called from `generate_reasoner_text` (unified_mot.py ~2591-2604). That is the reasoner, i.e. captioning / prompt-upsampling text generation, and it bypasses the generation tower. The vLLM-Omni cosmos3 diffusion pipeline never references a vision encoder. The I2V conditioning image enters as VAE latents only. So diffusers dropping `vision_encoder/` does not put our clips off-reference.

## Testable consequence
A cheap recipe arm: same seeds and prompt, with the negative = cosmos-framework default JSON + SAME metadata (the NVIDIA reference) vs our current empty + INVERSE. GAUGE reports that the negative prompt alone moves ball g from 0.45 to 0.33, so the negative-branch metadata is a plausible lever on timing. Not run here (code reading only, no GPU).
