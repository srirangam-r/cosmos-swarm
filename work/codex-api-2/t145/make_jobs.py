#!/usr/bin/env python3
"""Build the preregistered task-145 q8 jobs; generated JSONL is intentionally local."""

import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
VECTOR_DIR = ROOT / "work/raj-opus-1/steer128"
SCENES = {
    "block": "A static camera shows a wooden table top. A person's hand gives a small wooden block a quick push, and the block slides across the table surface away from the hand.",
    "top": "A static camera shows a wooden floor. A colorful spinning top is spun by hand and released, and it spins and wobbles on the floor.",
    "cart": "A static camera shows a smooth kitchen floor. A small wooden toy cart with four wheels is pushed by a child's hand and rolls across the floor.",
    "disc": "A static camera shows a wooden desk. A large metal coin is set rolling on its edge across the desk surface.",
}
RULE = (
    " By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy "
    "and come to rest, staying completely still for the rest of the video."
)
NEUTRAL = (
    " The scene is lit by soft, even lighting that stays constant throughout the video, and the colours remain "
    "natural and true to life, with realistic textures and fine surface detail on every object."
)


def inline_vector(filename):
    original = np.load(VECTOR_DIR / filename)
    if original.shape != (24, 4096):
        raise ValueError(f"Unexpected vector shape {original.shape}")
    values = [[float(f"{value:.4g}") for value in frame] for frame in original]
    rounded = np.asarray(values)
    error = np.max(np.abs(np.linalg.norm(rounded, axis=1) - np.linalg.norm(original, axis=1)) / np.linalg.norm(original, axis=1))
    if error >= 0.00002:
        raise ValueError(f"Vector norm error too large: {error}")
    return values


def build():
    ball = inline_vector("v_L12_s0s5.npy")
    random = inline_vector("rand_L12.npy")
    arms = ("F", "S2", "Z2", "S4", "Z4", "N", "R")
    for scene, prompt in SCENES.items():
        for seed in (4, 5, 6):
            for arm in arms:
                extra = {"client": "codex-api-2"}
                suffix = ""
                if arm in ("S2", "S4", "Z2", "Z4"):
                    vector = ball if arm.startswith("S") else random
                    extra["internals"] = {"steer": {"alpha": float(arm[1:]), "step_range": [0, 35], "passes": "cond", "vectors": [{"layer": 12, "values": vector}]}}
                elif arm in ("N", "R"):
                    suffix = NEUTRAL if arm == "N" else RULE
                    extra["internals"] = {"capture": {"layers": [12], "step_range": [0, 6], "every": 5, "passes": ["cond"], "full": False}}
                if len(json.dumps(extra).encode()) >= 1048576:
                    raise ValueError(f"extra_params exceeds the 1 MiB form-part limit: {scene}, {arm}")
                yield {"name": f"t145_{scene}_{arm}_s{seed}", "prompt": prompt + suffix, "negative_prompt": "", "width": 832, "height": 480, "num_frames": 93, "fps": 24, "steps": 35, "guidance": 6.0, "flow_shift": 10.0, "seed": seed, "extra_params": extra}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python make_jobs.py /path/to/jobs.jsonl")
    output = Path(sys.argv[1])
    with output.open("w") as handle:
        for job in build():
            handle.write(json.dumps(job) + "\n")
    print(f"Wrote 84 jobs to {output}")


if __name__ == "__main__":
    main()
