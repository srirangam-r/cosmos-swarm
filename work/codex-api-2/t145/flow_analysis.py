#!/usr/bin/env python3
"""Task 136's unvalidated affine-compensated flow metric, applied to task 145.

Method and parameters reproduced from rahul-3's board message 3441.
"""

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np


HEIGHT, WIDTH = 240, 416
Y_COORD, X_COORD = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
DESIGN = np.stack([np.ones(HEIGHT * WIDTH), X_COORD.ravel() / WIDTH, Y_COORD.ravel() / HEIGHT], 1)
SCENES = ("block", "top", "cart", "disc")
SEEDS = (4, 5, 6)
ARMS = ("F", "S2", "Z2", "S4", "Z4")
CONTRASTS = (("S2", "Z2"), ("S4", "Z4"), ("S2", "F"), ("S4", "F"), ("Z2", "F"), ("Z4", "F"))


def affine_fit(flow):
    flat = flow.reshape(-1, 2)
    indices = np.arange(0, len(flat), 7)
    coefficients = np.linalg.lstsq(DESIGN[indices], flat[indices], rcond=None)[0]
    residual = np.linalg.norm(DESIGN[indices] @ coefficients - flat[indices], axis=1)
    keep = indices[residual < np.quantile(residual, 0.8)]
    coefficients = np.linalg.lstsq(DESIGN[keep], flat[keep], rcond=None)[0]
    return (DESIGN @ coefficients).reshape(HEIGHT, WIDTH, 2)


def clip_motion(path):
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Could not open {path}")
    previous = None
    magnitudes = []
    while True:
        success, frame = capture.read()
        if not success:
            break
        grey = cv2.cvtColor(cv2.resize(frame, (WIDTH, HEIGHT)), cv2.COLOR_BGR2GRAY)
        if previous is not None:
            flow = cv2.calcOpticalFlowFarneback(previous, grey, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            magnitude = np.linalg.norm(flow - affine_fit(flow), axis=2).ravel()
            magnitudes.append(float(np.mean(np.sort(magnitude)[-int(0.02 * magnitude.size):])))
        previous = grey
    capture.release()
    if len(magnitudes) != 92:
        raise ValueError(f"Expected 93 frames in {path}, got {len(magnitudes) + 1}")
    return np.asarray(magnitudes)


def describe_motion(motion):
    smoothed = np.convolve(motion, np.ones(5) / 5, mode="valid")
    return {
        "early": float(motion[10:41].mean()),
        "late": float(motion[60:].mean()),
        "late_log_plus_0_05": float(np.log(motion[60:].mean() + 0.05)),
        "late_smoothed_max": float(smoothed[60:].max()),
        "rest_proxy_threshold_0_5": bool(smoothed[60:].max() < 0.5),
        "per_pair": motion.tolist(),
    }


def summary(values):
    values = np.asarray(values, dtype=float)
    return {"n": int(values.size), "mean": float(values.mean()),
            "se": float(values.std(ddof=1) / math.sqrt(values.size)) if values.size > 1 else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clips", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    arguments = parser.parse_args()
    cv2.setNumThreads(1)
    rows = []
    for scene in SCENES:
        for seed in SEEDS:
            for arm in ARMS:
                name = f"t145_{scene}_{arm}_s{seed}"
                sidecar = json.loads((arguments.clips / f"{name}.json").read_text())
                row = {"scene": scene, "seed": seed, "arm": arm,
                       "endpoint": sidecar.get("endpoint_url"),
                       **describe_motion(clip_motion(arguments.clips / f"{name}.mp4"))}
                rows.append(row)
                print(f"{len(rows):02d} {name} late={row['late']:.4f}", flush=True)
                if arguments.limit and len(rows) >= arguments.limit:
                    break
            if arguments.limit and len(rows) >= arguments.limit:
                break
        if arguments.limit and len(rows) >= arguments.limit:
            break
    if not arguments.limit and len(rows) != len(SCENES) * len(SEEDS) * len(ARMS):
        raise ValueError("Incomplete paired sample")
    paired = []
    by_key = {(row["scene"], row["seed"], row["arm"]): row for row in rows}
    for scene in SCENES:
        for seed in SEEDS:
            for treated, control in CONTRASTS:
                left = by_key.get((scene, seed, treated))
                right = by_key.get((scene, seed, control))
                if left and right:
                    paired.append({"scene": scene, "seed": seed, "contrast": f"{treated}-{control}",
                                   "log_late_difference": left["late_log_plus_0_05"] - right["late_log_plus_0_05"],
                                   "same_endpoint": left["endpoint"] == right["endpoint"]})
    aggregates = []
    for treated, control in CONTRASTS:
        contrast = f"{treated}-{control}"
        per_scene = []
        for scene in SCENES:
            values = [row["log_late_difference"] for row in paired if row["contrast"] == contrast and row["scene"] == scene]
            if values:
                per_scene.append({"scene": scene, **summary(values)})
        if per_scene:
            aggregates.append({"contrast": contrast, "per_scene": per_scene,
                               "across_scene_means": summary([row["mean"] for row in per_scene])})
    arguments.out.write_text(json.dumps({"method": "rahul-3 board #3441; unvalidated", "rows": rows,
                                         "paired": paired, "aggregates": aggregates}, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
