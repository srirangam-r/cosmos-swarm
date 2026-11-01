#!/usr/bin/env python3
"""Resume task 145 without duplicating names when the shared queue owner cap fills."""

import fcntl
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
    if len(sys.argv) != 3:
        raise SystemExit("usage: python dispatch.py /path/to/jobs.jsonl /path/to/controls.jsonl")
    jobs = [json.loads(line) for path in sys.argv[1:] for line in Path(path).read_text().splitlines() if line]
    expected = {f"t145_{scene}_{arm}_s{seed}"
                for scene in ("block", "top", "cart", "disc")
                for arm in ("F", "S2", "Z2", "S4", "Z4", "N", "R", "M", "N2")
                for seed in (4, 5, 6)}
    if len(jobs) != len(expected) or {job["name"] for job in jobs} != expected:
        raise RuntimeError("Unexpected preregistered job matrix or duplicate names")
    lock_path = Path(__file__).with_name("dispatch.lock")
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another task-145 dispatcher already holds the lock") from error
        dispatch(jobs, expected)


def dispatch(jobs, expected):
    known = queue_names()
    if not known <= expected:
        raise RuntimeError(f"Unexpected existing task-145 names: {sorted(known - expected)}")
    print(f"Already queued: {len(known)} / {len(expected)}", flush=True)
    deadline = time.monotonic() + 3 * 3600
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
    print(f"Dispatch complete: {len(known)} / {len(expected)} unique task-145 names", flush=True)


if __name__ == "__main__":
    main()
