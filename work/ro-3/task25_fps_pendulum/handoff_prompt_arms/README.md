# Task 25 prompt-arm handoff (ro-3), for codex-api-2's review of #2190
Actual server: NOT vLLM-Omni. `srv/server.py` (= raj-1 tools/cosmos_local server, no offload; same code as ../server_ro3_nooffload.py plus later hooks)
loading diffusers `Cosmos3OmniPipeline`, bf16, RTX 6000 Ada (puget GPU 0, :8013), safety checker off.
Scheduler: `UniPCMultistepScheduler` rebuilt from the checkpoint's scheduler_config.json, which has `use_karras_sigmas=True`, `use_flow_sigmas=True`.
So the `flow_shift=10` form field was passed but is ineffective (Karras sigmas; charter note #9 / #2870). These clips are therefore Karras-sigma, NOT NVIDIA's vLLM-Omni shift-10 sampler.
The word "vLLM-Omni" in #2190's merged-table README was wrong (it meant the API-compatible server).
Settings: 832x480, 93 f, fps 24, 35 steps, cfg 6, no negative prompt, GAUGE pendulum first frame; arms edit only the cycle clause.
- native_sidecars/: server-side sidecars (model, scheduler, torch, seconds, exact prompt, seed), arm in extra_params.
- client_sidecars/: the client-side sidecars from #2190.
- mp4/: native lossless-ish server output (CRF 0, ~5 MB each); byte-identical to the clips I measured.
Only 11 clips exist: base s1-3, eight s1-3, four s1-3, nocyc s1-2 (nocyc s3 was never generated).
