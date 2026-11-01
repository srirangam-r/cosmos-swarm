#!/usr/bin/env python3
"""Analyze paired layer-12 capture contrasts against the fixed ball vector."""

import argparse
import json
import math
from pathlib import Path

import numpy as np


SCENES = ("block", "top", "cart", "disc")
SEEDS = (4, 5, 6)
STEPS = (0, 5)
ARMS = ("R", "M", "N", "N2")
CONTRASTS = {"R_minus_M": ("R", "M"), "N2_minus_N": ("N2", "N"), "R_minus_N": ("R", "N")}


def cosine(first, second):
    first = np.asarray(first, dtype=np.float64)
    second = np.asarray(second, dtype=np.float64)
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    if denominator == 0 or not np.isfinite(denominator):
        raise ValueError("Cosine is undefined for zero or nonfinite vectors")
    return float(np.dot(first.ravel(), second.ravel()) / denominator)


def summarize(values):
    values = np.asarray(values, dtype=np.float64)
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "se": float(values.std(ddof=1) / math.sqrt(values.size)) if values.size > 1 else None,
    }


def analyze(directory, ball):
    ball = np.asarray(ball, dtype=np.float64)
    if ball.shape != (24, 4096) or not np.isfinite(ball).all():
        raise ValueError(f"Unexpected ball vector shape or nonfinite values: {ball.shape}")
    rows = []
    for scene in SCENES:
        for seed in SEEDS:
            arrays = {}
            for arm in ARMS:
                filename = Path(directory) / f"t145_{scene}_{arm}_s{seed}.npz"
                with np.load(filename, allow_pickle=False) as capture:
                    for step in STEPS:
                        key = f"s{step:03d}_cond_L12_mean"
                        array = np.asarray(capture[key], dtype=np.float64)
                        if array.shape != ball.shape or not np.isfinite(array).all():
                            raise ValueError(f"Invalid capture shape or values: {filename} {key}")
                        arrays[(arm, step)] = array
            for step in STEPS:
                row = {"scene": scene, "seed": seed, "step": step}
                for label, (positive, negative) in CONTRASTS.items():
                    difference = arrays[(positive, step)] - arrays[(negative, step)]
                    row[label] = cosine(ball[1:].mean(axis=0), difference[1:].mean(axis=0))
                    row[label + "_per_frame"] = [cosine(ball[frame], difference[frame]) for frame in range(1, 24)]
                    row[label + "_flattened"] = cosine(ball[1:], difference[1:])
                row["primary_difference"] = row["R_minus_M"] - row["N2_minus_N"]
                rows.append(row)
    scene_summaries = []
    for scene in SCENES:
        for step in STEPS:
            subset = [row for row in rows if row["scene"] == scene and row["step"] == step]
            scene_summaries.append({
                "scene": scene,
                "step": step,
                **{name: summarize([row[name] for row in subset]) for name in (*CONTRASTS, "primary_difference")},
            })
    across_scenes = []
    for step in STEPS:
        subset = [row for row in scene_summaries if row["step"] == step]
        across_scenes.append({
            "step": step,
            **{name: summarize([row[name]["mean"] for row in subset]) for name in (*CONTRASTS, "primary_difference")},
        })
    return {"rows": rows, "scene_summaries": scene_summaries, "across_scenes": across_scenes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acts", type=Path, required=True)
    parser.add_argument("--ball-vector", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    results = analyze(arguments.acts, np.load(arguments.ball_vector, allow_pickle=False))
    arguments.out.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {len(results['rows'])} matched scene-seed-step rows to {arguments.out}")


if __name__ == "__main__":
    main()
