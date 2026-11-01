"""Roll out Cosmos3-Nano forward dynamics on the robot dev set through a vLLM-Omni endpoint.

Follows the Nano model card's 4-chunk AgiBot example: chunk k is conditioned on one frame
(real frame 0 for k=0, else the last generated frame of chunk k-1) plus one 16-step
normalised action chunk in extra_params["action"]. The output keeps the conditioning
frame of chunk 0 and drops it for later chunks, giving 1 + 16*n frames aligned with real.mp4.

Usage:
  python generate.py <devset_dir> <out_dir> --url http://HOST:PORT --seed 0 [--steps 30 --guidance 1.0 --flow-shift 10.0]
Writes <out_dir>/<clip_id>.mp4 and <clip_id>.json (sidecar with every setting).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import time

import av
import numpy as np
import requests
from PIL import Image


def decode(buf: bytes) -> np.ndarray:
    with av.open(io.BytesIO(buf)) as c:
        return np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)])


def write_mp4(path: str, frames: np.ndarray, fps: int) -> None:
    with av.open(path, "w") as c:
        s = c.add_stream("libx264", rate=fps)
        s.width, s.height, s.pix_fmt = frames.shape[2], frames.shape[1], "yuv420p"
        s.options = {"crf": "0"}
        for fr in frames:
            for p in s.encode(av.VideoFrame.from_ndarray(fr, format="rgb24")):
                c.mux(p)
        for p in s.encode():
            c.mux(p)


def rollout(url: str, clip_dir: str, a: argparse.Namespace) -> tuple[np.ndarray, list[float]]:
    spec = json.load(open(os.path.join(clip_dir, "action_chunks.json")))
    cond = Image.open(os.path.join(clip_dir, "first_frame.png")).convert("RGB")
    w, h = cond.size
    out, secs = [], []
    for k, chunk in enumerate(spec["action_chunks"]):
        extra = {
            "action_mode": "forward_dynamics",
            "domain_name": spec["domain_name"],
            "action_chunk_size": spec["action_chunk_size"],
            "image_size": spec["image_size"],
            "view_point": spec["view_point"],
            "action": chunk,
            "guardrails": True,
        }
        data = {
            "prompt": spec["prompt"],
            "num_frames": str(spec["action_chunk_size"] + 1),
            "fps": str(spec["fps"]),
            "size": f"{w}x{h}",
            "num_inference_steps": str(a.steps),
            "guidance_scale": str(a.guidance),
            "flow_shift": str(a.flow_shift),
            "seed": str(a.seed),
            "extra_params": json.dumps(extra),
        }
        if a.negative_prompt:
            data["negative_prompt"] = a.negative_prompt
        b = io.BytesIO()
        cond.save(b, format="PNG")
        t0 = time.time()
        r = requests.post(f"{url.rstrip('/')}/v1/videos/sync", data=data,
                          files={"input_reference": ("frame.png", b.getvalue(), "image/png")},
                          headers={"Accept": "video/mp4"}, timeout=1200)
        r.raise_for_status()
        secs.append(time.time() - t0)
        fr = decode(r.content)
        out.extend(fr if k == 0 else fr[1:])
        cond = Image.fromarray(fr[-1])
    return np.stack(out), secs


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("devset")
    p.add_argument("out")
    p.add_argument("--url", required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--steps", type=int, default=30)  # model card FD example
    p.add_argument("--guidance", type=float, default=1.0)  # model card FD example
    p.add_argument("--flow-shift", type=float, default=10.0)
    p.add_argument("--negative-prompt", default="")
    p.add_argument("--model", default="nvidia/Cosmos3-Nano", help="checkpoint/adapter label for the sidecar")
    p.add_argument("--only", nargs="*", help="clip ids to run (default all)")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    idx = json.load(open(os.path.join(a.devset, "index.json")))
    for c in idx["clips"]:
        if a.only and c["id"] not in a.only:
            continue
        dst = os.path.join(a.out, c["id"] + ".mp4")
        if os.path.exists(dst):
            continue
        frames, secs = rollout(a.url, os.path.join(a.devset, c["id"]), a)
        write_mp4(dst, frames, 5)
        json.dump({"clip_id": c["id"], "model": a.model, "url": a.url, "seed": a.seed, "steps": a.steps,
                   "guidance": a.guidance, "flow_shift": a.flow_shift, "negative_prompt": a.negative_prompt,
                   "prompt": c["prompt"], "fps": 5, "frames": int(len(frames)),
                   "size": f"{frames.shape[2]}x{frames.shape[1]}", "seconds_per_chunk": secs,
                   "input": os.path.join(a.devset, c["id"])},
                  open(os.path.join(a.out, c["id"] + ".json"), "w"), indent=1)
        print(c["id"], frames.shape, [round(s, 1) for s in secs], flush=True)


if __name__ == "__main__":
    main()
