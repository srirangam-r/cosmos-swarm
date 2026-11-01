#!/usr/bin/env python3
"""Build the task-145 preregistered language-control captures."""

import json
import sys
from pathlib import Path

from make_jobs import SCENES


MOTION = (
    " By the end of the video, every object that was falling, sliding, rolling or bouncing "
    "is still moving at full speed, never slowing down or stopping for the rest of the video."
)
NEUTRAL2 = (
    " The scene is shown with a clear, steady focus that stays constant throughout the video, "
    "and the materials remain ordinary and familiar, with visible edges and consistent surface "
    "patterns on every object."
)


def build():
    for scene, prompt in SCENES.items():
        for seed in (4, 5, 6):
            for arm, suffix in (("M", MOTION), ("N2", NEUTRAL2)):
                yield {
                    "name": f"t145_{scene}_{arm}_s{seed}",
                    "prompt": prompt + suffix,
                    "negative_prompt": "",
                    "width": 832,
                    "height": 480,
                    "num_frames": 93,
                    "fps": 24,
                    "steps": 35,
                    "guidance": 6.0,
                    "flow_shift": 10.0,
                    "seed": seed,
                    "extra_params": {
                        "client": "codex-api-2",
                        "internals": {
                            "capture": {
                                "layers": [12],
                                "step_range": [0, 6],
                                "every": 5,
                                "passes": ["cond"],
                                "full": False,
                            }
                        },
                    },
                }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python make_controls.py /path/to/controls.jsonl")
    output = Path(sys.argv[1])
    with output.open("w") as handle:
        for job in build():
            handle.write(json.dumps(job) + "\n")
    print(f"Wrote 24 controls to {output}")


if __name__ == "__main__":
    main()
