"""Task 253 decoded equality and E1 image-change summaries; provenance is separate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'codex-api-4' / 't223'))
from e0_video import decode_changes

HERE = Path(__file__).resolve().parent
SETTINGS = {'fps': 24, 'width': 832, 'height': 480, 'num_frames': 93}


def decoded_hash(path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f'Cannot open {path}')
    h = hashlib.sha256()
    n = 0
    try:
        if not np.isclose(cap.get(cv2.CAP_PROP_FPS), 24, atol=1e-6, rtol=0):
            raise ValueError(f'fps mismatch: {path}')
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame.shape != (480, 832, 3):
                raise ValueError(f'geometry mismatch: {path}')
            h.update(frame.tobytes())
            n += 1
    finally:
        cap.release()
    if n != 93:
        raise ValueError(f'frame count mismatch ({n}): {path}')
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('clips', type=Path, help='Directory with one <manifest job name>.mp4 per job')
    args = p.parse_args()
    jobs = [json.loads(s) for s in (HERE / 'feasibility.jsonl').read_text().splitlines()]
    names = [j['name'] for j in jobs]
    if len(names) != 33 or len(set(names)) != 33:
        raise ValueError('Manifest must contain 33 unique jobs')
    paths = {n: args.clips / (n + '.mp4') for n in names}
    missing = [n for n, path in paths.items() if not path.is_file()]
    if missing:
        raise ValueError('Missing clips: ' + ', '.join(missing))
    hashes = {n: decoded_hash(path) for n, path in paths.items()}
    equality = []
    motion = []
    for seed in (201, 202, 203):
        stem = f't253_s{seed}_'
        for contrast in ('AB', 'AC'):
            a, b = contrast
            for source, target in ((a, a), (b, b), (a, b), (b, a)):
                name = stem + f'{contrast}_{source}to{target}'
                expected = stem + 'plain_' + target
                equality.append({'job': name, 'expected': expected, 'equal': hashes[name] == hashes[expected]})
        vals = {}
        for arm in ('A', 'C'):
            changes, _ = decode_changes(paths[stem + 'plain_' + arm], SETTINGS)
            vals[arm] = float(np.mean(np.abs(changes), dtype=np.float64))
        motion.append({'seed': seed, 'slow_M': vals['A'], 'fast_M': vals['C'], 'fast_minus_slow': vals['C'] - vals['A']})
    output = {'warning': 'Decoded equality and image change do not establish runtime hook, sampler, endpoint, CPU noise, or physical speed. Verify job-scoped provenance separately before interpreting.',
              'all_decoded_equal': all(x['equal'] for x in equality), 'equality': equality, 'image_change': motion}
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
