#!/usr/bin/env python
"""Run a gen.py-style jobs.jsonl against a vLLM-Omni-compatible /v1/videos/sync endpoint.
Usage: python client.py jobs.jsonl --url http://HOST:PORT [--out out]. Skips jobs whose mp4 exists. Writes <name>.mp4 + <name>.json."""
import argparse, json, os, time
from pathlib import Path
import requests

DEF = dict(width=832, height=480, num_frames=189, fps=24, steps=35, guidance=6.0, flow_shift=10.0, seed=1,
           negative_prompt=None, image=None)


def text(x):
    if isinstance(x, str) and x.endswith(".json") and os.path.exists(x):
        return json.dumps(json.load(open(x)))
    return x


ap = argparse.ArgumentParser(); ap.add_argument("jobs"); ap.add_argument("--url", required=True)
ap.add_argument("--out", default="out"); a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
for line in open(a.jobs):
    if not line.strip():
        continue
    j = {**DEF, **json.loads(line)}
    if (out / f"{j['name']}.mp4").exists():
        continue
    data = dict(prompt=text(j["prompt"]), size=f"{j['width']}x{j['height']}", num_frames=str(j["num_frames"]),
                fps=str(j["fps"]), num_inference_steps=str(j["steps"]), guidance_scale=str(j["guidance"]),
                flow_shift=str(j["flow_shift"]), seed=str(j["seed"]),
                extra_params=json.dumps({"client": "rog1", **j.get("extra_params", {})}))
    if j["negative_prompt"]:
        data["negative_prompt"] = text(j["negative_prompt"])
    files = {"input_reference": (os.path.basename(j["image"]), open(j["image"], "rb").read(), "image/png")} if j["image"] else None
    t = time.time()
    for attempt in range(6):  # server auto-restarts after a CUDA fault; retry
        try:
            r = requests.post(f"{a.url.rstrip('/')}/v1/videos/sync", data=data, files=files, timeout=7200)
            r.raise_for_status()
            break
        except Exception as e:
            print(f"{j['name']} attempt {attempt} failed: {e}", flush=True)
            time.sleep(90)
    else:
        print(f"giving up on {j['name']}", flush=True)
        continue
    (out / f"{j['name']}.mp4").write_bytes(r.content)
    json.dump({**j, "prompt_text": data["prompt"], "negative_prompt_text": data.get("negative_prompt"),
               "model": "nvidia/Cosmos3-Nano (GB10 diffusers bf16, no offload)", "endpoint": a.url,
               "server_clip_id": r.headers.get("X-Clip-Id"), "seconds": float(r.headers.get("X-Seconds", 0)),
               "wall_seconds": round(time.time() - t, 1)}, open(out / f"{j['name']}.json", "w"), indent=1)
    print(f"done {j['name']} in {time.time()-t:.0f}s", flush=True)
