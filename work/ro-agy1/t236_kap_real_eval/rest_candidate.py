#!/usr/bin/env python3
"""Unvalidated GAUGE-specific candidate detector; see README before use."""

import argparse
import json
import math

import cv2
import numpy as np


def candidates(reference, frame):
    if reference.shape != (480, 832) or frame.shape != (480, 832):
        raise ValueError("only 832x480 frames are supported")
    mask = ((reference.astype(np.int16) - frame.astype(np.int16) > 25)
            & (frame < 100)).astype(np.uint8)
    mask[:290] = 0
    mask[410:] = 0
    mask[:, :180] = 0
    mask[:, 410:] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    boxes = []
    edge_count = 0
    for index in range(1, count):
        left, top, width, height, area = map(int, stats[index])
        if not (10 <= width <= 100 and 10 <= height <= 100 and area >= 90):
            continue
        if not (0.55 <= width / height <= 1.8 and area / (width * height) >= 0.3):
            continue
        if left <= 180 or top <= 290 or left + width >= 410 or top + height >= 410:
            edge_count += 1
        else:
            boxes.append([left, top, width, height, area])
    return boxes, edge_count


def classify_frames(reference, ending):
    if len(ending) != 3:
        raise ValueError("exactly three end frames are required")
    detected = [candidates(reference, frame) for frame in ending]
    result = {
        "state": "UNKNOWN",
        "reason": "candidate_absent_or_ambiguous",
        "boxes": [boxes for boxes, _ in detected],
        "edge_counts": [edges for _, edges in detected],
        "original_identity_verified": False,
        "validation": "unvalidated_prototype",
    }
    if any(len(boxes) != 1 or edges for boxes, edges in detected):
        return result
    boxes = [boxes[0] for boxes, _ in detected]
    centres = [(box[0] + box[2] / 2, box[1] + box[3] / 2) for box in boxes]
    max_shift = max(math.dist(centres[first], centres[second])
                    for first in range(3) for second in range(first + 1, 3))
    diameter = float(np.median([(box[2] + box[3]) / 2 for box in boxes]))
    result["max_shift_px"] = max_shift
    result["median_box_diameter_px"] = diameter
    result["state"] = "REST_CANDIDATE" if max_shift < diameter / 2 else "MOVING_CANDIDATE"
    result["reason"] = "changed_dark_component_track_only"
    return result


def classify_video(path):
    capture = cv2.VideoCapture(path)
    if not capture.isOpened():
        raise ValueError(f"cannot open video: {path}")
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count < 14:
            raise ValueError("video must have at least 14 frames")
        indices = [0, frame_count - 13, frame_count - 7, frame_count - 1]
        frames = []
        for index in indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            success, frame = capture.read()
            if not success:
                raise ValueError(f"cannot decode frame {index} in {path}")
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        result = classify_frames(frames[0], frames[1:])
        result.update({"video": str(path), "frame_indices": indices,
                       "fps": capture.get(cv2.CAP_PROP_FPS), "frame_count": frame_count})
        return result
    finally:
        capture.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    args = parser.parse_args()
    print(json.dumps(classify_video(args.video), sort_keys=True))


if __name__ == "__main__":
    main()
