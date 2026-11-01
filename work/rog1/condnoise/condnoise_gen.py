#!/usr/bin/env python3
"""Task 98: noised I2V conditioning frame for Cosmos3-Nano (diffusers Cosmos3OmniPipeline @86ef420b).

Stock pipeline: latent frame 0 = clean VAE(x_image), its velocity is masked to 0, and it gets NO timestep
embedding (it is excluded from vision_noisy_frame_indexes). The leakage paper (Zhao et al., arXiv 2406.15735)
argues the model then over-relies on the clean condition, which suppresses motion. Inference fix: show the
model a noised condition.

Modes (per job):
  sigma_c = 0                -> stock pipeline (control; no patch active)
  sigma_c > 0, tag = True    -> the transformer sees frame-0 latent (1-s)*x0 + s*eps with a timestep embedding
                                of s*1000 (frame 0 is moved into the noisy-frame set for packing only).
  sigma_c > 0, tag = False   -> same noised latent, but frame 0 stays an untagged clean-condition frame.
In all modes the frame-0 velocity stays masked, so the latent that gets decoded keeps the clean x0 in frame 0
(only the transformer INPUT is noised, on both the cond and uncond passes, with a fixed eps per seed).

Usage: python condnoise_gen.py jobs.jsonl --model DIR --out DIR
Job keys: name, image, prompt, seed, sigma_c, tag, [num_frames 93, fps 24, steps 35, guidance 6, flow_shift 10,
          height 480, width 832, negative_prompt None]
"""
import argparse, json, time
from pathlib import Path

import torch
from PIL import Image
from diffusers import Cosmos3OmniPipeline
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
from diffusers.utils import export_to_video

DEF = dict(num_frames=93, fps=24, steps=35, guidance=6.0, flow_shift=10.0, height=480, width=832,
           negative_prompt=None, sigma_c=0.0, tag=True)

STATE = dict(on=False, sigma=0.0, tag=True, eps=None, seed=0, calls=0, n0_logged=False)


def install(pipe):
    orig_seg = pipe._prepare_vision_segment

    def seg(*args, **kw):
        if STATE["on"] and STATE["tag"]:
            kw["condition_frame_indexes"] = []  # frame 0 packed as a "noisy" frame -> gets a timestep embedding
        return orig_seg(*args, **kw)

    pipe._prepare_vision_segment = seg

    tr = pipe.transformer
    orig_fwd = tr.forward

    def fwd(*args, **kw):
        if STATE["on"]:
            STATE["calls"] += 1
            vt = kw["vision_tokens"][0]
            s = STATE["sigma"]
            if STATE["eps"] is None or STATE["eps"].shape != vt[..., 0, :, :].shape:
                g = torch.Generator(device=vt.device).manual_seed(10_000 + STATE["seed"])
                STATE["eps"] = torch.randn(vt[..., 0, :, :].shape, generator=g, device=vt.device,
                                           dtype=torch.float32)
            vt = vt.clone()
            x0 = vt[..., 0, :, :].float()
            vt[..., 0, :, :] = ((1 - s) * x0 + s * STATE["eps"]).to(vt.dtype)
            kw["vision_tokens"] = [vt]
            if STATE["tag"]:
                lt, ph, pw = kw["vision_token_shapes"][0]
                n0 = ph * pw
                ts = kw["vision_timesteps"].clone()
                assert ts.numel() == lt * n0, (ts.numel(), lt, n0)  # all frames packed as noisy
                ts[:n0] = s * 1000.0
                kw["vision_timesteps"] = ts
                if not STATE["n0_logged"]:
                    print(f"  [hook] tagged: frame0 tokens={n0}, latent_t={lt}, t0={s*1000:.0f}", flush=True)
                    STATE["n0_logged"] = True
        return orig_fwd(*args, **kw)

    tr.forward = fwd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    jobs = [j for j in jobs if not (out / f"{j['name']}.mp4").exists()]
    print(f"{len(jobs)} jobs", flush=True)
    if not jobs:
        return
    try:
        pipe = Cosmos3OmniPipeline.from_pretrained(a.model, torch_dtype=torch.bfloat16, enable_safety_checker=False)
    except TypeError:
        pipe = Cosmos3OmniPipeline.from_pretrained(a.model, torch_dtype=torch.bfloat16)
    pipe.to("cuda")
    install(pipe)
    import inspect
    sig = set(inspect.signature(pipe.__call__).parameters)
    for j in jobs:
        j = {**DEF, **j}
        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=float(j["flow_shift"]))
        call = dict(prompt=j["prompt"], image=Image.open(j["image"]).convert("RGB"), num_frames=j["num_frames"],
                    height=j["height"], width=j["width"], num_inference_steps=j["steps"],
                    guidance_scale=j["guidance"], generator=torch.Generator(device="cuda").manual_seed(int(j["seed"])))
        if j["negative_prompt"] is not None:
            call["negative_prompt"] = j["negative_prompt"]
        for k in ("fps", "frame_rate"):
            if k in sig:
                call[k] = j["fps"]
        if "enable_safety_check" in sig:
            call["enable_safety_check"] = False
        STATE.update(on=float(j["sigma_c"]) > 0, sigma=float(j["sigma_c"]), tag=bool(j["tag"]), eps=None,
                     seed=int(j["seed"]), calls=0, n0_logged=False)
        t1 = time.time()
        res = pipe(**call)
        dt = time.time() - t1
        vid = res.video if hasattr(res, "video") else res.frames[0]
        if isinstance(vid, list) and vid and isinstance(vid[0], list):
            vid = vid[0]
        export_to_video(vid, str(out / f"{j['name']}.mp4"), fps=j["fps"])
        side = {**j, "model": "nvidia/Cosmos3-Nano (local diffusers 86ef420b, bf16, H100, no offload)",
                "scheduler": "UniPCMultistepScheduler", "seconds": round(dt, 1), "hook_calls": STATE["calls"],
                "hook": "condnoise_gen.py (task 98)", "torch": torch.__version__}
        json.dump(side, open(out / f"{j['name']}.json", "w"), indent=1)
        print(f"done {j['name']} in {dt:.0f}s hook_calls={STATE['calls']}", flush=True)
        STATE["on"] = False


if __name__ == "__main__":
    main()
