#!/usr/bin/env python
"""Minimal vLLM-Omni-compatible Cosmos3-Nano server (diffusers, group offload, one request at a time).

POST /v1/videos/sync  multipart form, same fields as vLLM-Omni:
  prompt, negative_prompt, size ("WxH"), num_frames, fps, num_inference_steps, guidance_scale, flow_shift, seed,
  extra_params (JSON str), file field input_reference (image, optional -> T2V).
  extra_params keys honoured: action_mode="forward_dynamics" (+ domain_name, action_chunk_size, image_size, view_point,
  action), use_resolution_template, use_duration_template, use_system_prompt, crf (mp4 quality, default 0 = lossless),
  client (free-text label stored in the sidecar). "guardrails" is ignored (safety checker off; research use).
  Returns video/mp4. Every clip + JSON sidecar is also kept server-side in out_srv/.
GET /health -> status, busy, served count.
Run: python server.py --host <tailscale ip> --port 8011
"""
import argparse, io, json, threading, time, traceback
from pathlib import Path

import av, numpy as np, torch, uvicorn
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import Response, JSONResponse
from PIL import Image
from diffusers import Cosmos3OmniPipeline
import cosmos_patch  # chunked attention (display watchdog)
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

t0 = time.time()
pipe = Cosmos3OmniPipeline.from_pretrained(A.model, torch_dtype=torch.bfloat16, enable_safety_checker=False)
pipe.to("cuda")  # ro-3: 48 GB RTX 6000 Ada, no offload
BASE_SCHED = dict(pipe.scheduler.config)
print(f"loaded in {time.time()-t0:.0f}s", flush=True)

# --- ALG (Adaptive Low-Pass Guidance, arXiv 2506.08456) hook, ro-3 shift 69 ---
# extra_params alg_steps=k (default 0 = off) and alg_factor=f (default 2.5): for the first k denoising steps the clean
# conditioning latent (latent frame 0) seen by the transformer (cond AND uncond passes) is bilinearly down-sampled by f
# and up-sampled back; from step k on the original clean latent is restored, so the output keeps the exact frame 0.
import torch.nn.functional as _F
ALG = dict(steps=0, factor=2.5, clean=None)
_orig_prep = pipe.prepare_latents


def _lowpass(x, f):
    lead, (H, W) = x.shape[:-2], x.shape[-2:]
    h, w = max(1, round(H / f)), max(1, round(W / f))
    y = _F.interpolate(x.reshape(1, -1, H, W).float(), size=(h, w), mode="bilinear", align_corners=False)
    return _F.interpolate(y, size=(H, W), mode="bilinear", align_corners=False).reshape(*lead, H, W).to(x.dtype)


def _prep(*a, **k):
    out = _orig_prep(*a, **k)
    ALG["clean"] = None
    if ALG["steps"] > 0:
        lat = out[0]
        ALG["clean"] = lat[..., 0, :, :].clone()
        lat[..., 0, :, :] = _lowpass(ALG["clean"], ALG["factor"])
        print(f"ALG on: steps={ALG['steps']} factor={ALG['factor']} lat={tuple(lat.shape)} d={float((lat[..., 0, :, :]-ALG['clean']).float().abs().mean()):.4f}", flush=True)
    return out


pipe.prepare_latents = _prep


def _alg_cb(p, i, t, kw):
    lat = kw["latents"]
    if ALG["clean"] is not None:
        c = ALG["clean"].to(lat.dtype)
        lat[..., 0, :, :] = _lowpass(c, ALG["factor"]) if i + 1 < ALG["steps"] else c
    return {"latents": lat}


LOCK = threading.Lock()
STATE = dict(busy=False, served=0, waiting=0, started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
app = FastAPI()


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
         extra_params: str | None = Form(None), input_reference: UploadFile | None = File(None)):
    extra = json.loads(extra_params) if extra_params else {}
    img = Image.open(io.BytesIO(input_reference.file.read())).convert("RGB") if input_reference is not None else None
    W, H = (int(v) for v in size.lower().split("x")) if size else (img.size if img is not None else (832, 480))
    call = dict(prompt=prompt, num_inference_steps=num_inference_steps, guidance_scale=guidance_scale, fps=fps,
                enable_safety_check=False, output_type="np")
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
    STATE["waiting"] += 1
    with LOCK:
        STATE["waiting"] -= 1; STATE["busy"] = True
        try:
            pipe.scheduler = UniPCMultistepScheduler.from_config(BASE_SCHED, flow_shift=float(flow_shift))
            call["generator"] = torch.Generator(device="cuda").manual_seed(int(seed))
            ALG["steps"] = int(extra.get("alg_steps", 0)); ALG["factor"] = float(extra.get("alg_factor", 2.5))
            if ALG["steps"] > 0 and img is not None and not extra.get("action_mode"):
                call["callback_on_step_end"] = _alg_cb
            else:
                ALG["steps"] = 0
            t1 = time.time()
            res = pipe(**call)
            dt = time.time() - t1
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
                seed=seed, extra_params={k: v for k, v in extra.items() if k != "action"},
                has_action=("action" in extra), input_image=(f"{stem}_input.png" if img is not None else None),
                frames_out=len(frames), out_hw=list(frames[0].shape[:2]), seconds=round(dt, 1),
                model="nvidia/Cosmos3-Nano (local diffusers bf16, no offload, RTX 6000 Ada, safety check off)",
                scheduler="UniPCMultistepScheduler", torch=torch.__version__, server="ro-3 srv/server.py (raj-1 tools/cosmos_local/server.py @ no-offload)", model_path=A.model)
    (OUT / f"{stem}.json").write_text(json.dumps(side, indent=1))
    print(f"served {stem} {len(frames)}f in {dt:.0f}s", flush=True)
    return Response(mp4, media_type="video/mp4", headers={"X-Seconds": f"{dt:.1f}", "X-Clip-Id": stem})


if __name__ == "__main__":
    uvicorn.run(app, host=A.host, port=A.port, workers=1)
