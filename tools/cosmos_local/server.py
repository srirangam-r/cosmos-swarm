#!/usr/bin/env python
"""Minimal vLLM-Omni-compatible Cosmos3-Nano server (diffusers, group offload, one request at a time).

POST /v1/videos/sync  multipart form, same fields as vLLM-Omni:
  prompt, negative_prompt, size ("WxH"), num_frames, fps, num_inference_steps, guidance_scale, flow_shift, seed,
  extra_params (JSON str), file field input_reference (image, optional -> T2V).
  extra_params keys honoured: action_mode="forward_dynamics" (+ domain_name, action_chunk_size, image_size, view_point,
  action), use_resolution_template, use_duration_template, use_system_prompt, crf (mp4 quality, default 0 = lossless),
  client (free-text label stored in the sidecar),
  negative_metadata_mode ("inverse" = diffusers default | "same" = NVIDIA cosmos-framework reference),
  negative_preset ("nvidia_default" = cosmos-framework image2video JSON negative; overrides negative_prompt). "guardrails" is ignored (safety checker off; research use).
  Optional extra_params.internals = {rope, conditioning, capture, steer} (see README "Internals hooks"); a request without it is
  unchanged. Uploaded steering vectors go in the multipart field internals_files (repeatable).
  Returns video/mp4. Every clip + JSON sidecar is also kept server-side in out_srv/. Header X-Artifact-Ids lists captures.
GET /health -> status, busy, served count.
GET /v1/artifacts/{id} -> a capture .npz.   POST /v1/probe/loss -> rectified-flow loss probe (JSON), see loss_probe.py.
Env: COSMOS_OFFLOAD=0 keeps every module on the GPU (80 GB cards); default is leaf-level group offload for the 15B DiT.
Run: python server.py --host <tailscale ip> --port 8011
"""
import argparse, contextlib, io, json, os, threading, time, traceback
from pathlib import Path

import av, numpy as np, torch, uvicorn
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import Response, JSONResponse, FileResponse
from PIL import Image
from diffusers import Cosmos3OmniPipeline
import cosmos_patch  # chunked attention (display watchdog)
import neg_meta  # negative_metadata_mode / negative_preset (NVIDIA reference CFG text)
import internals  # optional per-request hooks: temporal RoPE, conditioning frame, capture, steering
import loss_probe  # POST /v1/probe/loss
from diffusers.pipelines.cosmos.pipeline_cosmos3_omni import CosmosActionCondition
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler

HERE = Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("--host", default="127.0.0.1")
ap.add_argument("--port", type=int, default=8011)
ap.add_argument("--model", default=str(HERE / "models/Cosmos3-Nano"))
ap.add_argument("--out", default=str(HERE / "out_srv"))
A = ap.parse_args()
OUT = Path(A.out); OUT.mkdir(parents=True, exist_ok=True)
ARTIFACTS = internals.ArtifactStore(OUT / "artifacts")
OFFLOAD = os.environ.get("COSMOS_OFFLOAD", "1") != "0"  # COSMOS_OFFLOAD=0 keeps everything on the GPU (80 GB cards)

t0 = time.time()
pipe = Cosmos3OmniPipeline.from_pretrained(A.model, torch_dtype=torch.bfloat16, enable_safety_checker=False)
from diffusers.hooks import apply_group_offloading
for name, comp in pipe.components.items():
    if isinstance(comp, torch.nn.Module):
        if OFFLOAD and sum(p.numel() for p in comp.parameters()) > 2e9:
            apply_group_offloading(comp, onload_device=torch.device("cuda"), offload_device=torch.device("cpu"),
                                   offload_type="leaf_level", use_stream=True, low_cpu_mem_usage=True)
        else:
            comp.to("cuda")
BASE_SCHED = dict(pipe.scheduler.config)
print(f"loaded in {time.time()-t0:.0f}s", flush=True)

LOCK = threading.Lock()
STATE = dict(busy=False, served=0, waiting=0, started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
app = FastAPI()


def parse_internals(extra, num_frames, num_inference_steps, uploads):
    """Validate extra['internals'] -> internals.Spec (None if absent). Raises HTTP 400 on a bad spec; no GPU use."""
    if "internals" not in extra:
        return None
    cfg = pipe.transformer.config
    n = int(extra.get("action_chunk_size", num_frames - 1)) + 1 if extra.get("action_mode") else num_frames
    env = internals.Env(num_layers=cfg.num_hidden_layers, hidden_size=cfg.hidden_size, num_steps=num_inference_steps,
                        latent_frames=(n - 1) // pipe.vae_scale_factor_temporal + 1, artifacts=ARTIFACTS, uploads=uploads,
                        temporal=internals.temporal_indices(pipe.transformer.rotary_emb))
    try:
        return internals.parse(extra["internals"], env)
    except internals.InternalsError as e:
        raise HTTPException(400, f"internals: {e}")


def encode_mp4(frames, fps, crf):
    buf = io.BytesIO()
    with av.open(buf, "w", format="mp4") as c:
        s = c.add_stream("libx264", rate=int(round(fps)))
        s.width, s.height, s.pix_fmt = frames[0].shape[1], frames[0].shape[0], "yuv420p"
        s.options = {"crf": str(crf)}
        for fr in frames:
            for p in s.encode(av.VideoFrame.from_ndarray(fr, format="rgb24")):
                c.mux(p)
        for p in s.encode():
            c.mux(p)
    return buf.getvalue()


@app.get("/health")
def health():
    return STATE


@app.post("/v1/videos/sync")
def sync(prompt: str = Form(""), negative_prompt: str | None = Form(None), size: str | None = Form(None),
         num_frames: int = Form(93), fps: float = Form(24.0), num_inference_steps: int = Form(35),
         guidance_scale: float = Form(6.0), flow_shift: float = Form(10.0), seed: int = Form(0),
         extra_params: str | None = Form(None), input_reference: UploadFile | None = File(None),
         internals_files: list[UploadFile] | None = File(None)):
    extra = json.loads(extra_params) if extra_params else {}
    img = Image.open(io.BytesIO(input_reference.file.read())).convert("RGB") if input_reference is not None else None
    W, H = (int(v) for v in size.lower().split("x")) if size else (img.size if img is not None else (832, 480))
    call = dict(prompt=prompt, num_inference_steps=num_inference_steps, guidance_scale=guidance_scale, fps=fps,
                enable_safety_check=False, output_type="np")
    neg_mode = str(extra.get("negative_metadata_mode", "inverse")).lower()
    if neg_mode not in neg_meta.MODES:
        raise HTTPException(400, f"negative_metadata_mode must be one of {neg_meta.MODES}")
    try:
        negative_prompt = neg_meta.resolve_negative(negative_prompt, extra.get("negative_preset"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if negative_prompt:
        call["negative_prompt"] = negative_prompt
    for k_in, k_out in (("use_resolution_template", "add_resolution_template"),
                        ("use_duration_template", "add_duration_template"), ("use_system_prompt", "use_system_prompt")):
        if k_in in extra:
            call[k_out] = bool(extra[k_in])
    if extra.get("action_mode"):
        call["action"] = CosmosActionCondition(
            mode=extra["action_mode"], chunk_size=int(extra.get("action_chunk_size", num_frames - 1)),
            domain_name=extra["domain_name"], resolution_tier=int(extra.get("image_size", 480)),
            raw_actions=torch.tensor(extra["action"], dtype=torch.float32) if "action" in extra else None,
            image=img, view_point=extra.get("view_point", "ego_view"))
    else:
        call.update(num_frames=num_frames, height=H, width=W)
        if img is not None:
            call["image"] = img
    spec = parse_internals(extra, num_frames, num_inference_steps,
                           {Path(f.filename or "").name: f.file.read() for f in internals_files or []})
    rec, artifact_id = None, None
    STATE["waiting"] += 1
    with LOCK:
        STATE["waiting"] -= 1; STATE["busy"] = True
        try:
            pipe.scheduler = UniPCMultistepScheduler.from_config(BASE_SCHED, flow_shift=float(flow_shift))
            call["generator"] = torch.Generator(device="cuda").manual_seed(int(seed))
            t1 = time.time()
            with neg_meta.negative_metadata(pipe, neg_mode), \
                    (internals.installed(pipe, spec) if spec else contextlib.nullcontext()) as rec:
                res = pipe(**call)
            dt = time.time() - t1
            if spec:  # captured activations -> .npz (hooks are already removed here)
                artifact_id = internals.save_capture(ARTIFACTS, rec, spec, dict(prompt=prompt, seed=seed, num_frames=num_frames,
                                                     num_inference_steps=num_inference_steps, guidance_scale=guidance_scale))
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(500, f"{type(e).__name__}: {e}")
        finally:
            STATE["busy"] = False
    v = res.video
    v = v[0] if (isinstance(v, np.ndarray) and v.ndim == 5) else v
    frames = [(np.clip(f, 0, 1) * 255).round().astype(np.uint8) if f.dtype != np.uint8 else f for f in np.asarray(v)]
    mp4 = encode_mp4(frames, fps, int(extra.get("crf", 0)))
    STATE["served"] += 1
    stem = f"{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}_{STATE['served']:04d}_{str(extra.get('client', 'anon'))[:32]}"
    (OUT / f"{stem}.mp4").write_bytes(mp4)
    if img is not None:
        img.save(OUT / f"{stem}_input.png")
    side = dict(prompt=prompt, negative_prompt=negative_prompt, size=f"{W}x{H}", num_frames=num_frames, fps=fps,
                num_inference_steps=num_inference_steps, guidance_scale=guidance_scale, flow_shift=flow_shift,
                seed=seed, negative_metadata_mode=neg_mode,
                extra_params={k: v for k, v in extra.items() if k not in ("action", "internals")},
                has_action=("action" in extra), input_image=(f"{stem}_input.png" if img is not None else None),
                frames_out=len(frames), out_hw=list(frames[0].shape[:2]), seconds=round(dt, 1),
                model="nvidia/Cosmos3-Nano (local diffusers bf16, group offload, safety check off)",
                scheduler="UniPCMultistepScheduler", torch=torch.__version__, server="raj-1 server.py")
    headers = {"X-Seconds": f"{dt:.1f}", "X-Clip-Id": stem}
    if spec:
        side["internals"] = dict(spec=spec.raw, artifact_id=artifact_id, **rec.summary())
        if artifact_id:
            headers["X-Artifact-Ids"] = artifact_id
    (OUT / f"{stem}.json").write_text(json.dumps(side, indent=1))
    print(f"served {stem} {len(frames)}f in {dt:.0f}s", flush=True)
    return Response(mp4, media_type="video/mp4", headers=headers)


@app.get("/v1/artifacts/{artifact_id}")
def artifact(artifact_id: str):
    path = ARTIFACTS.path(artifact_id)
    if path is None:
        raise HTTPException(404, f"no artifact {artifact_id!r}")
    return FileResponse(path, media_type="application/octet-stream", filename=path.name)


@app.post("/v1/probe/loss")
def probe_loss(prompt: str = Form(...), settings: str | None = Form(None), video: UploadFile = File(...),
               image: UploadFile | None = File(None)):
    """Rectified-flow velocity-MSE of a given video (overall and per latent frame) at fixed noise levels and seeds."""
    try:
        cfg = json.loads(settings) if settings else {}
        if not isinstance(cfg, dict):
            raise loss_probe.ProbeError("settings must be a JSON object")
        frames, fps = loss_probe.decode_video(video.file.read(), cfg.get("size"))
        s = loss_probe.validate(cfg, len(frames))
        frames = frames[s["start"]:s["start"] + s["num_frames"]]
        img = Image.open(io.BytesIO(image.file.read())).convert("RGB") if image is not None else None
        rope = None
        if "rope" in cfg:  # same RoPE spec as internals.rope: {"temporal_scale": ...}
            rope = internals.parse({"rope": cfg["rope"]}, internals.Env(
                num_layers=1, hidden_size=1, num_steps=1, latent_frames=1, artifacts=ARTIFACTS,
                temporal=internals.temporal_indices(pipe.transformer.rotary_emb)))
    except (loss_probe.ProbeError, internals.InternalsError, json.JSONDecodeError) as e:
        raise HTTPException(400, str(e))
    STATE["waiting"] += 1
    with LOCK:
        STATE["waiting"] -= 1; STATE["busy"] = True
        try:
            with (internals.installed(pipe, rope) if rope else contextlib.nullcontext()):
                result = loss_probe.run_probe(pipe, frames, fps, prompt, img, s)
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(500, f"{type(e).__name__}: {e}")
        finally:
            STATE["busy"] = False
    result["settings"]["rope"] = cfg.get("rope")
    STATE["served"] += 1
    print(f"probe_loss {len(result['rows'])} rows in {result['seconds']}s", flush=True)
    return JSONResponse(result)


if __name__ == "__main__":
    uvicorn.run(app, host=A.host, port=A.port, workers=1)
