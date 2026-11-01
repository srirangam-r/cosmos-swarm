#!/usr/bin/env python3
"""Create randomized paired contact sheets and native clips for task 145."""

import argparse
import json
import os
import secrets
from pathlib import Path

import cv2
import numpy as np

from analyze_capture import SCENES, SEEDS


ARMS = ("F", "S2", "Z2", "S4", "Z4")
FRAMES = (0, 24, 48, 60, 68, 76, 84, 92)
WIDTH, HEIGHT = 208, 120


def sample_frames(path):
    capture = cv2.VideoCapture(str(path))
    frames = {}
    index = 0
    while index <= FRAMES[-1]:
        ok, frame = capture.read()
        if not ok:
            break
        if index in FRAMES:
            frames[index] = cv2.resize(frame, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
        index += 1
    capture.release()
    if len(frames) != len(FRAMES):
        raise ValueError(f"Missing required frames in {path}")
    return frames


def make_sheet(paths, output):
    header = np.full((26, 48 + WIDTH * len(FRAMES), 3), 255, dtype=np.uint8)
    for index, frame in enumerate(FRAMES):
        cv2.putText(header, f"f{frame}", (48 + WIDTH * index + 70, 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)
    rows = [header]
    for label, path in paths:
        samples = sample_frames(path)
        band = np.full((HEIGHT, 48, 3), 255, dtype=np.uint8)
        cv2.putText(band, label, (12, 68), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 0), 2)
        rows.append(np.concatenate([band, *(samples[frame] for frame in FRAMES)], axis=1))
    if not cv2.imwrite(str(output), np.concatenate(rows, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 90]):
        raise OSError(f"Could not write {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clips", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    groups = []
    missing = []
    for scene in SCENES:
        for seed in SEEDS:
            clips = {arm: args.clips / f"t145_{scene}_{arm}_s{seed}.mp4" for arm in ARMS}
            missing.extend(str(path) for path in clips.values() if not path.is_file())
            groups.append((scene, seed, clips))
    if missing:
        raise SystemExit(f"Expected all 60 clips before blinding; {len(missing)} are missing")
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "native").mkdir()
    rng = secrets.SystemRandom()
    rng.shuffle(groups)
    key = {}
    for scene, seed, clips in groups:
        identifier = secrets.token_hex(6)
        arms = list(ARMS)
        rng.shuffle(arms)
        labelled = list(zip("ABCDE", arms))
        make_sheet([(label, clips[arm]) for label, arm in labelled], args.out / f"{identifier}.jpg")
        for label, arm in labelled:
            os.link(clips[arm], args.out / "native" / f"{identifier}_{label}.mp4")
        key[identifier] = {"scene": scene, "seed": seed, "rows": dict(labelled)}
    (args.out / "UNBLIND_key.json").write_text(json.dumps(key, indent=2) + "\n")
    print(f"Created {len(key)} blinded paired sheets and {len(key) * len(ARMS)} native clips")


if __name__ == "__main__":
    main()
