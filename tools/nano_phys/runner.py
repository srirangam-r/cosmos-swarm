"""
nano_phys.runner: Backend runner for Nano-Phys.
Supports remote vLLM-Omni/tools/cosmos_local endpoints and local diffusers pipeline.
Enforces CPU noise draws for cross-platform deterministic portability (Charter Rule 11).
"""

import io
import json
import os
from pathlib import Path
import time
import requests


def run_remote_nanophys(
    server_url: str,
    image_path: str | Path,
    proxy_path: str | Path,
    prompt: str,
    out_mp4: str | Path,
    negative_prompt: str = "",
    width: int = 832,
    height: int = 480,
    num_frames: int = 93,
    fps: int = 24,
    steps: int = 35,
    guidance: float = 6.0,
    flow_shift: float = 10.0,
    seed: int = 1,
    start_step: int = 14,
    sampler: str = "nv",
    timeout: int = 3600,
) -> dict:
    """Run Nano-Phys via HTTP POST to a tools/cosmos_local server endpoint."""
    image_p = Path(image_path)
    proxy_p = Path(proxy_path)
    out_p = Path(out_mp4)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    extra_params = {
        "client": "nano_phys",
        "noise": {"device": "cpu"},
        "sampler": sampler,
        "latent": {
            "ref": proxy_p.name,
            "start_step": start_step,
            "init": "noised",
        },
    }

    data = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "size": f"{width}x{height}",
        "num_frames": str(num_frames),
        "fps": str(fps),
        "num_inference_steps": str(steps),
        "guidance_scale": str(guidance),
        "flow_shift": str(flow_shift),
        "seed": str(seed),
        "extra_params": json.dumps(extra_params),
    }

    files = [
        ("input_reference", (image_p.name, open(image_p, "rb").read(), "image/png")),
        ("internals_files", (proxy_p.name, open(proxy_p, "rb").read(), "video/mp4")),
    ]

    t0 = time.time()
    url = f"{server_url.rstrip('/')}/v1/videos/sync"
    
    resp = requests.post(url, data=data, files=files, timeout=timeout)
    resp.raise_for_status()

    out_p.write_bytes(resp.content)
    elapsed = time.time() - t0

    sidecar = {
        "tool": "nano_phys",
        "method": "Analytical Sim-Proxy + SDEdit Latent Start",
        "out_mp4": str(out_p),
        "image_path": str(image_p),
        "proxy_path": str(proxy_p),
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_frames": num_frames,
        "fps": fps,
        "steps": steps,
        "guidance": guidance,
        "flow_shift": flow_shift,
        "seed": seed,
        "start_step": start_step,
        "sampler": sampler,
        "server_url": server_url,
        "wall_seconds": round(elapsed, 2),
    }

    sidecar_p = out_p.with_suffix(".json")
    sidecar_p.write_text(json.dumps(sidecar, indent=2))

    return sidecar


def run_local_nanophys(
    image_path: str | Path,
    proxy_path: str | Path,
    prompt: str,
    out_mp4: str | Path,
    **kwargs
) -> dict:
    """Run Nano-Phys via local in-process diffusers pipeline."""
    # Attempt importing cosmos_local pipeline if available in workspace
    try:
        from tools.cosmos_local.server import generate_video_local
        return generate_video_local(image_path=image_path, proxy_path=proxy_path, prompt=prompt, out_mp4=out_mp4, **kwargs)
    except Exception as e:
        raise RuntimeError(
            f"Local in-process pipeline requires local GPU with Cosmos3-Nano weights loaded: {e}. "
            f"Specify --server http://HOST:PORT to dispatch to an active swarm endpoint."
        )
