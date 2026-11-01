import argparse
from pathlib import Path

import cv2
import numpy as np


def make_sheet(frames, numbers, columns):
    height, width = frames[0].shape[:2]
    rows = (len(numbers) + columns - 1) // columns
    tile_height = height + 36
    sheet = np.zeros((rows * tile_height, columns * width, 3), dtype=np.uint8)
    for index, number in enumerate(numbers):
        row, column = divmod(index, columns)
        cv2.putText(sheet, f'f{number}', (column * width + 5, row * tile_height + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        sheet[row * tile_height + 36:(row + 1) * tile_height,
              column * width:(column + 1) * width] = frames[number]
    return sheet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('clip', type=Path)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(arguments.clip))
    frames = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    capture.release()
    if len(frames) != 93 or frames[0].shape[:2] != (480, 832):
        raise ValueError(f'unexpected clip dimensions or frame count: {arguments.clip}')
    overview = list(range(0, 93, 8)) + [92]
    for name, numbers, columns in [('overview', overview, 4),
                                    ('late', list(range(60, 93)), 6)]:
        output = arguments.output / f'{arguments.clip.stem}_{name}.png'
        if not cv2.imwrite(str(output), make_sheet(frames, numbers, columns)):
            raise RuntimeError(f'cannot write {output}')


if __name__ == '__main__':
    main()
