"""
nano_phys.runner: Backend runner for Nano-Phys.
Supports remote vLLM-Omni/tools/cosmos_local endpoints and local diffusers pipeline.
Enforces CPU noise draws for cross-platform deterministic portability (Charter Rule 11).
"""

import io
import json
import math
import os
from pathlib import Path
import time
import requests


# Archived native 35-step UniPC schedule (35 steps + terminal 0.0).
# Source: work/raj-demos/sidecars/sp_k19_s2.server.json, latent.sigmas_request.
# This reference table does not certify a current endpoint or its executed suffix.
# In normalized flow units [0, 1]: step 19 corresponds to sigma = 0.89844 (Raj #281 recipe target ~0.90)
NATIVE_SIGMAS_35 = [
    0.99502, 0.99432, 0.99349, 0.99253, 0.99140, 0.99007, 0.98851, 0.98666,
    0.98447, 0.98187, 0.97876, 0.97503, 0.97056, 0.96518, 0.95868, 0.95082,
    0.94127, 0.92968, 0.91558, 0.89844, 0.87762, 0.85242, 0.82207, 0.78581,
    0.74295, 0.69305, 0.63610, 0.57269, 0.50418, 0.43273, 0.36112, 0.29241,
    0.22942, 0.17428, 0.12816, 0.00000
]


def sigma_to_step(target_sigma: float, steps: int = 35) -> int:
    """Find the step index in native schedule closest to target_sigma.
    
    Only the archived 35-step grid is supported. Target sigma must be finite
    in [0, 1] (e.g. 0.90 for Raj's lead recipe,
    which maps directly to step 19 with sigma = 0.89844).
    """
    if not isinstance(target_sigma, (int, float)) or isinstance(target_sigma, bool):
        raise TypeError(f"target_sigma must be a float or int, got {type(target_sigma).__name__}")
    if not math.isfinite(target_sigma) or target_sigma < 0.0 or target_sigma > 1.0:
        raise ValueError(f"target_sigma must be in [0, 1], got {target_sigma}")
    if not isinstance(steps, int) or isinstance(steps, bool) or steps != 35:
        raise ValueError("sigma selection requires the recorded 35-step grid; use an explicit start_step for other step counts")
    # Selection candidates are strictly the non-terminal steps [0, steps - 1]
    return min(range(steps), key=lambda i: abs(NATIVE_SIGMAS_35[i] - target_sigma))


def resolve_start_step(steps: int, start_step: int | None = None, sigma: float | None = None) -> int:
    """Resolve CLI and HTTP requests identically, before any proxy or network work."""
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 1:
        raise ValueError("steps must be a positive integer")
    if sigma is not None:
        return sigma_to_step(sigma, steps)
    if start_step is None:
        start_step = 14
    if not isinstance(start_step, int) or isinstance(start_step, bool) or not 0 <= start_step < steps:
        raise ValueError(f"start_step must be an integer in [0, {steps - 1}], got {start_step}")
    return start_step


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

    start_step = resolve_start_step(steps, start_step, sigma)
    # The archived table does not establish a nominal sigma for other grids.
    effective_sigma = NATIVE_SIGMAS_35[start_step] if steps == 35 else None

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

        # Capture native latent schedule and executed start
        if "latent" in server_sidecar and isinstance(server_sidecar["latent"], dict):
            sidecar["server_latent"] = server_sidecar["latent"]
            if "sigmas_request" in server_sidecar["latent"]:
                sidecar["sigmas_request"] = server_sidecar["latent"]["sigmas_request"]
            if "sigma_start" in server_sidecar["latent"]:
                sidecar["actual_sigma_start"] = server_sidecar["latent"]["sigma_start"]
            if "start_step" in server_sidecar["latent"]:
                sidecar["actual_start_step"] = server_sidecar["latent"]["start_step"]

        # Capture summary metadata if present, checking for conflicts rather than silent override
        if "summary" in server_sidecar and isinstance(server_sidecar["summary"], dict):
            sidecar["server_summary"] = server_sidecar["summary"]
            if "sigma_start" in server_sidecar["summary"]:
                summary_sigma = server_sidecar["summary"]["sigma_start"]
                if "actual_sigma_start" in sidecar and sidecar["actual_sigma_start"] != summary_sigma:
                    sidecar["summary_sigma_start_conflict"] = summary_sigma
                elif "actual_sigma_start" not in sidecar:
                    sidecar["actual_sigma_start"] = summary_sigma

        # Capture server and scheduler identity
        for k in ["model", "scheduler", "torch", "server", "server_rev"]:
            if k in server_sidecar:
                sidecar[k] = server_sidecar[k]

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
