import argparse
from pathlib import Path

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('clip')
    parser.add_argument('--start', type=int, default=30)
    parser.add_argument('--stop', type=int, default=49)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    capture = cv2.VideoCapture(args.clip)
    cells = []
    for index in range(args.stop):
        success, frame = capture.read()
        if not success:
            raise ValueError(f'cannot read frame {index}')
        if index < args.start:
            continue
        crop = frame[95:355, 245:350].copy()
        for row in range(100, 351, 10):
            y = row - 95
            cv2.line(crop, (0, y), (5, y), (0, 255, 0), 1)
            cv2.putText(crop, str(row), (7, y + 2), cv2.FONT_HERSHEY_SIMPLEX,
                        0.23, (0, 255, 0), 1)
        cv2.putText(crop, f'f{index}', (65, 12), cv2.FONT_HERSHEY_SIMPLEX,
                    0.35, (0, 255, 255), 1)
        cells.append(crop)
    width = 5
    while len(cells) % width:
        cells.append(np.zeros_like(cells[0]))
    sheet = np.concatenate([np.concatenate(cells[i:i + width], axis=1)
                            for i in range(0, len(cells), width)], axis=0)
    sheet = cv2.resize(sheet, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(args.out, sheet):
        raise ValueError('could not write sheet')


if __name__ == '__main__':
    main()
