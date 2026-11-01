import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('clip')
    parser.add_argument('result')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_text())
    capture = cv2.VideoCapture(args.clip)
    frames = []
    while True:
        success, frame = capture.read()
        if not success:
            break
        frames.append(frame)
    cells = []
    differences = []
    for index in range(29, 65):
        frame = frames[index]
        crop = frame[95:365, 230:360].copy()
        tracked_y = result['track_y'][index]
        if tracked_y is not None:
            row = int(round(tracked_y)) - 95
            cv2.line(crop, (0, row), (129, row), (0, 0, 255), 1)
        if index:
            difference = float(np.abs(frame.astype(np.int16) - frames[index - 1].astype(np.int16)).mean())
            differences.append((index, round(difference, 4)))
        cv2.putText(crop, f'f{index} y={tracked_y:.1f}', (2, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 255, 255), 1)
        cells.append(crop)
    sheet = np.concatenate([np.concatenate(cells[index:index + 6], axis=1) for index in range(0, len(cells), 6)], axis=0)
    cv2.imwrite(args.out, sheet)
    print(json.dumps({'clip': args.clip, 'consecutive_frame_mae': differences}, indent=2))


if __name__ == '__main__':
    main()
