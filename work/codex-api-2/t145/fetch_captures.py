#!/usr/bin/env python3
"""Download task-145 capture artifacts from already-fetched queue sidecars."""

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

from analyze_capture import ARMS, SCENES, SEEDS, STEPS


def artifact_url(sidecar):
    endpoint = urllib.parse.urlsplit(sidecar["endpoint_url"])
    if endpoint.scheme != "http" or not endpoint.hostname or not endpoint.port:
        raise ValueError("Sidecar must specify an HTTP endpoint with a port")
    if endpoint.hostname not in ("127.0.0.1", "localhost") or not 8001 <= endpoint.port <= 8099:
        raise ValueError("Expected a queue-side localhost endpoint on a permitted port")
    identifiers = sidecar.get("artifact_ids", [])
    if len(identifiers) != 1 or not identifiers[0].startswith("act_") or not identifiers[0][4:].isalnum():
        raise ValueError("Expected exactly one valid activation artifact ID")
    return f"http://100.111.167.68:{endpoint.port}/v1/artifacts/{identifiers[0]}"


def check_artifact(path):
    with np.load(path, allow_pickle=False) as capture:
        for step in STEPS:
            key = f"s{step:03d}_cond_L12_mean"
            if capture[key].shape != (24, 4096):
                raise ValueError(f"Unexpected shape for {path}: {key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sidecars", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.out.mkdir(parents=True, exist_ok=True)
    ready = 0
    missing = []
    for scene in SCENES:
        for seed in SEEDS:
            for arm in ARMS:
                name = f"t145_{scene}_{arm}_s{seed}"
                sidecar = arguments.sidecars / f"{name}.json"
                output = arguments.out / f"{name}.npz"
                if not sidecar.exists():
                    missing.append(name)
                    continue
                if not output.exists():
                    url = artifact_url(json.loads(sidecar.read_text()))
                    temporary = output.with_suffix(".npz.part")
                    try:
                        with urllib.request.urlopen(url, timeout=90) as response, temporary.open("wb") as handle:
                            while chunk := response.read(1024 * 1024):
                                handle.write(chunk)
                        check_artifact(temporary)
                        temporary.replace(output)
                    finally:
                        temporary.unlink(missing_ok=True)
                check_artifact(output)
                ready += 1
    print(f"Valid captures: {ready}/48; missing sidecars: {len(missing)}")
    if missing:
        print("Missing: " + ", ".join(missing))


if __name__ == "__main__":
    main()
