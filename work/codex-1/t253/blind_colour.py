"""Create blinded full-frame colour sheets; keep mapping away from the coder.

Usage: python blind_colour.py CLIP_DIR OUTPUT_DIR MAP.json
All *.mp4 in CLIP_DIR are included. OUTPUT_DIR and MAP must not already exist.
The private map is randomly assigned and must be retained for later unblinding.
"""
import csv
import json
import secrets
import sys
from pathlib import Path

import cv2
import numpy as np


def main(source, output, map_path):
    clips = sorted(source.glob('*.mp4'))
    if not clips:
        raise ValueError('No mp4 clips')
    if output.exists() or map_path.exists():
        raise ValueError('Output or mapping already exists')
    output.mkdir(parents=True)
    mapping = {}
    for clip in clips:
        cap = cv2.VideoCapture(str(clip))
        frames = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(frame)
        cap.release()
        if len(frames) != 93 or any(f.shape != (480, 832, 3) for f in frames):
            raise ValueError(f'Invalid frame count or geometry: {clip.name}')
        code = secrets.token_hex(6)
        while code in mapping:
            code = secrets.token_hex(6)
        mapping[code] = clip.name
        tiles = [cv2.resize(frames[i], (416, 240), interpolation=cv2.INTER_AREA)
                 for i in (0, 23, 46, 69, 92)]
        sheet = np.full((480, 1248, 3), 255, dtype=np.uint8)
        for index, tile in enumerate(tiles):
            row, col = divmod(index, 3)
            sheet[row*240:(row+1)*240, col*416:(col+1)*416] = tile
        if not cv2.imwrite(str(output / f'{code}.png'), sheet):
            raise RuntimeError('Could not write sheet')
    map_path.write_text(json.dumps(mapping, indent=2, sort_keys=True) + '\n')
    with (output / 'codes.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['code', 'colour', 'notes'])
        writer.writerows((code, '', '') for code in sorted(mapping))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*(Path(arg) for arg in sys.argv[1:]))
