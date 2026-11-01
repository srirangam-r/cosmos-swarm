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


# Full native 35-step UniPC schedule (35 steps + terminal 0.0) from tools/cosmos_local
# Note: step 19 corresponds to sigma ~ 0.896-0.898 (Raj #281 / ro-3 #5315 recipe)
NATIVE_SIGMAS_35 = [
    14.61465, 12.93308, 11.42015, 10.06153, 8.84388, 7.75478, 6.78273, 5.91705,
    5.14784, 4.46600, 3.86307, 3.33130, 2.86356, 2.45327, 2.09444, 1.78157,
    1.50965, 1.27411, 1.07079, 0.89595, 0.74617, 0.61838, 0.50983, 0.41805,
    0.34080, 0.27613, 0.22228, 0.17769, 0.14100, 0.11100, 0.08665, 0.06703,
    0.05135, 0.03892, 0.02917, 0.00000
]


def sigma_to_step(target_sigma: float) -> int:
    """Find the step index in native 35-step UniPC schedule closest to target_sigma.
    
    If target_sigma is normalized in [0, 1] (e.g. 0.90 for Raj's recipe), maps directly
    to step 19 (sigma ~ 0.896) or step 14 (sigma ~ 2.094).
    """
    if target_sigma <= 1.0:
        # Search among steps with sigma <= 1.5 or normalized scale
        sub_indices = [i for i, s in enumerate(NATIVE_SIGMAS_35) if s <= 2.0]
        if sub_indices:
            return min(sub_indices, key=lambda i: abs(NATIVE_SIGMAS_35[i] - target_sigma))
    return min(range(len(NATIVE_SIGMAS_35)), key=lambda i: abs(NATIVE_SIGMAS_35[i] - target_sigma))


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
    start_step: int | None = None,
    sigma: float | None = None,
    timeout: int = 3600,
) -> dict:
    """Run Nano-Phys via HTTP POST to a tools/cosmos_local server endpoint."""
    image_p = Path(image_path)
    proxy_p = Path(proxy_path)
    out_p = Path(out_mp4)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Determine start step: explicit sigma overrides or maps to step index
    if sigma is not None:
        start_step = sigma_to_step(sigma)
    elif start_step is None:
        start_step = 14  # Default: step 14 (sigma = 0.93675; ro-3 t_init=0.6 arm)

    effective_sigma = NATIVE_SIGMAS_35[start_step] if start_step < len(NATIVE_SIGMAS_35) else None

    extra_params = {
        "client": "nano_phys",
        "noise": {"device": "cpu"},
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

    clip_id = resp.headers.get("X-Clip-Id")
    x_secs = resp.headers.get("X-Seconds")

    # Fetch native server sidecar if endpoint provides /v1/sidecars
    server_sidecar = None
    if clip_id:
        try:
            side_url = f"{server_url.rstrip('/')}/v1/sidecars/{clip_id}"
            s_resp = requests.get(side_url, timeout=10)
            if s_resp.status_code == 200:
                server_sidecar = s_resp.json()
                server_sidecar_p = out_p.with_suffix(".server.json")
                server_sidecar_p.write_text(json.dumps(server_sidecar, indent=2))
        except Exception:
            pass

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
        "nominal_sigma": effective_sigma,
        "server_url": server_url,
        "server_clip_id": clip_id,
        "server_seconds": float(x_secs) if x_secs else None,
        "wall_seconds": round(elapsed, 2),
    }

    if server_sidecar:
        if "sigmas_used" in server_sidecar:
            sidecar["sigmas_used"] = server_sidecar["sigmas_used"]
        if "summary" in server_sidecar and isinstance(server_sidecar["summary"], dict):
            sidecar["server_summary"] = server_sidecar["summary"]
            if "sigma_start" in server_sidecar["summary"]:
                sidecar["actual_sigma_start"] = server_sidecar["summary"]["sigma_start"]
        elif "latent" in server_sidecar and isinstance(server_sidecar["latent"], dict):
            sidecar["server_latent"] = server_sidecar["latent"]
            if "sigma_start" in server_sidecar["latent"]:
                sidecar["actual_sigma_start"] = server_sidecar["latent"]["sigma_start"]

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
    """Run Nano-Phys via local in-process pipeline or local dispatch."""
    raise NotImplementedError(
        "Local in-process pipeline without endpoint is disabled on laptop host; "
        "pass --server http://HOST:PORT (e.g. q8 / Brev) to execute via tools/cosmos_local endpoint."
    )
