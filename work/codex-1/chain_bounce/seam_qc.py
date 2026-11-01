#!/usr/bin/env python3
"""Make a seam contact sheet and descriptive pixel differences, not a validity verdict."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def read(path):
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if len(frames) < 3:
        raise ValueError(f'{path}: fewer than three decoded frames')
    return frames


def mae(a, b):
    return float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('continuation', type=Path)
    p.add_argument('output_prefix', type=Path)
    a = p.parse_args()
    first, tail = read(a.source), read(a.continuation)
    if first[-1].shape != tail[0].shape:
        raise ValueError('decoded dimensions differ')
    panels = []
    for label, frame in zip(['source -2', 'source -1', 'source 0', 'tail 0', 'tail 1', 'tail 2'],
                            first[-3:] + tail[:3]):
        panel = frame.copy()
        cv2.putText(panel, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 255, 255), 2)
        panels.append(panel)
    sheet = np.vstack([np.hstack(panels[:3]), np.hstack(panels[3:])])
    if not cv2.imwrite(str(a.output_prefix) + '.jpg', sheet):
        raise OSError('could not write contact sheet')
    result = {'source_frames': len(first), 'continuation_frames': len(tail),
              'source_last_to_tail_first_mae_0_255': mae(first[-1], tail[0]),
              'source_last_to_tail_second_mae_0_255': mae(first[-1], tail[1]),
              'source_previous_to_last_mae_0_255': mae(first[-2], first[-1]),
              'tail_first_to_second_mae_0_255': mae(tail[0], tail[1]),
              'note': 'Full-frame MAE includes codec differences and background; inspect identity, ball motion and seam manually. No pass threshold.'}
    Path(str(a.output_prefix) + '.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
