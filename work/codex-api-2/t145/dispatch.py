#!/usr/bin/env python3
"""Resume task 145 without duplicating names when the shared queue owner cap fills."""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


URL = "http://100.111.167.68:8030"
OWNER = "codex-api-2"
ENDPOINTS = [f"q8-{index}" for index in range(8)]
PARAMS = ("width", "height", "num_frames", "fps", "steps", "guidance", "flow_shift", "seed", "negative_prompt", "extra_params")


def request(path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(URL + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def queue_names():
    jobs = request(f"/jobs?owner={OWNER}")["jobs"]
    names = [job["name"] for job in jobs if job["name"].startswith("t145_")]
    if len(names) != len(set(names)):
        raise RuntimeError("Duplicate task-145 job names already in queue; stop and investigate")
    return set(names)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python dispatch.py /path/to/jobs.jsonl")
    jobs = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines() if line]
    if len(jobs) != 84 or len({job["name"] for job in jobs}) != 84:
        raise RuntimeError("Unexpected preregistered job matrix")
    known = queue_names()
    print(f"Already queued: {len(known)} / 84", flush=True)
    deadline = time.monotonic() + 3600
    for job in jobs:
        while job["name"] not in known:
            if time.monotonic() > deadline:
                raise TimeoutError("One-hour dispatch deadline exceeded")
            body = {"owner": OWNER, "name": job["name"], "prompt": job["prompt"], "endpoints": ENDPOINTS}
            body.update({key: job[key] for key in PARAMS if key in job})
            try:
                result = request("/jobs", body)
            except urllib.error.HTTPError as error:
                detail = error.read().decode(errors="replace")
                if error.code != 400 or "pending jobs" not in detail:
                    raise RuntimeError(f"Queue rejected {job['name']}: {error.code} {detail}") from error
                print("Queue cap reached; retrying in 20 s", flush=True)
                time.sleep(20)
                continue
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
                print(f"Uncertain submission for {job['name']}: {error}; checking names before retry", flush=True)
                time.sleep(20)
                known = queue_names()
                continue
            known.add(job["name"])
            print(f"{result['id']} {job['name']}", flush=True)
    print(f"Dispatch complete: {len(known)} / 84 unique task-145 names", flush=True)


if __name__ == "__main__":
    main()
