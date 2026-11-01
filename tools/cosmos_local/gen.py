#!/usr/bin/env python
"""Batch Cosmos3-Nano I2V/T2V generation with diffusers on a 24 GB GPU.

Usage: python gen.py jobs.jsonl [--offload group|seq|none] [--model DIR]
Each job line: {"name":..., "image": path|null, "prompt": str|path.json, "negative_prompt": str|path.json|null,
                "width":832, "height":480, "num_frames":189, "fps":24, "steps":35, "guidance":6.0,
                "flow_shift":10.0, "seed":1}
Writes out/<name>.mp4 and out/<name>.json (sidecar with every setting). Skips jobs whose mp4 exists.
"""
import argparse, inspect, json, os, sys, time
from pathlib import Path

import torch
from PIL import Image
from diffusers import Cosmos3OmniPipeline
import cosmos_patch  # chunked attention (display watchdog)
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
from diffusers.utils import export_to_video

DEF = dict(width=832, height=480, num_frames=189, fps=24, steps=35, guidance=6.0, flow_shift=10.0, seed=1,
           negative_prompt=None, image=None)


def load_text(x):
    if x is None:
        return None
    if isinstance(x, (dict, list)):
        return json.dumps(x)
    if isinstance(x, str) and x.endswith(".json") and os.path.exists(x):
        return json.dumps(json.load(open(x)))
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--model", default=str(Path(__file__).parent / "models/Cosmos3-Nano"))
    ap.add_argument("--offload", default="group", choices=["group", "seq", "model", "none"])
    ap.add_argument("--out", default=str(Path(__file__).parent / "out"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    jobs = [j for j in jobs if not (out / f"{j['name']}.mp4").exists()]
    print(f"{len(jobs)} jobs to run", flush=True)
    if not jobs:
        return

    t0 = time.time()
    kw = dict(torch_dtype=torch.bfloat16)
    try:
        pipe = Cosmos3OmniPipeline.from_pretrained(a.model, enable_safety_checker=False, **kw)
    except TypeError:
        pipe = Cosmos3OmniPipeline.from_pretrained(a.model, **kw)
    if a.offload == "group":
        from diffusers.hooks import apply_group_offloading
        for name, comp in pipe.components.items():
            if isinstance(comp, torch.nn.Module):
                n = sum(p.numel() for p in comp.parameters())
                if n > 2e9:
                    print(f"group-offload {name} ({n/1e9:.1f}B params)", flush=True)
                    apply_group_offloading(comp, onload_device=torch.device("cuda"), offload_device=torch.device("cpu"),
                                           offload_type="leaf_level", use_stream=True, low_cpu_mem_usage=True)
                else:
                    comp.to("cuda")
    elif a.offload == "seq":
        pipe.enable_sequential_cpu_offload()
    elif a.offload == "model":
        pipe.enable_model_cpu_offload()
    else:
        pipe.to("cuda")
    print(f"loaded in {time.time()-t0:.0f}s", flush=True)
    sig = set(inspect.signature(pipe.__call__).parameters)
    print("pipeline args:", sorted(sig), flush=True)

    for j in jobs:
        j = {**DEF, **j}
        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=float(j["flow_shift"]))
        call = dict(prompt=load_text(j["prompt"]), num_frames=j["num_frames"], height=j["height"], width=j["width"],
                    num_inference_steps=j["steps"], guidance_scale=j["guidance"],
                    generator=torch.Generator(device="cuda").manual_seed(int(j["seed"])))
        neg = load_text(j["negative_prompt"])
        if neg is not None:
            call["negative_prompt"] = neg
        if j["image"]:
            call["image"] = Image.open(j["image"]).convert("RGB")
        for k in ("fps", "frame_rate"):
            if k in sig:
                call[k] = j["fps"]
        if "enable_safety_check" in sig:
            call["enable_safety_check"] = False
        call = {k: v for k, v in call.items() if k in sig}
        t1 = time.time()
        res = pipe(**call)
        dt = time.time() - t1
        vid = res.video if hasattr(res, "video") else res.frames[0]
        if isinstance(vid, list) and vid and isinstance(vid[0], list):
            vid = vid[0]
        mp4 = out / f"{j['name']}.mp4"
        export_to_video(vid, str(mp4), fps=j["fps"])
        side = {**j, "model": "nvidia/Cosmos3-Nano (local diffusers, bf16)", "offload": a.offload,
                "scheduler": "UniPCMultistepScheduler", "seconds": round(dt, 1),
                "passed_to_pipeline": sorted(k for k in call if k != "generator"),
                "prompt_text": call.get("prompt"), "negative_prompt_text": call.get("negative_prompt"),
                "torch": torch.__version__}
        json.dump(side, open(out / f"{j['name']}.json", "w"), indent=1)
        print(f"done {j['name']} in {dt:.0f}s", flush=True)


if __name__ == "__main__":
    main()
