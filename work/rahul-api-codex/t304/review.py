#!/usr/bin/env python3
"""Independent, offline raw-writer and compositing review; no model imports."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import socket
import subprocess
import types
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
PIN_OLD = 'd185781'
PIN_NEW = '38e80c8'
SELECT = (0, 1, 4, 7, 14, 28, 46, 70, 92)


def sha(x):
    return hashlib.sha256(x).hexdigest()


def diff(a, b):
    z = np.abs(a.astype(np.int16) - b.astype(np.int16))
    return {'changed_pixels': int(np.count_nonzero(np.any(z, axis=2))),
            'mean_absolute_channel_error_8bit': float(z.mean()),
            'maximum_channel_error_8bit': int(z.max())}


def load(rev):
    src = subprocess.check_output(['git', 'show', f'{rev}:tools/nano_phys/proxy.py'], cwd=ROOT)
    m = types.ModuleType('independent_' + rev)
    exec(compile(src, rev + '/proxy.py', 'exec'), m.__dict__)
    return m, sha(src)


def capture(module, kind, cfg):
    """Digest the actual writer inputs; do not invoke an encoder."""
    hashes, frames = [], {}

    class Sink:
        def __init__(self, *a, **k):
            pass

        def write(self, frame):
            idx = len(hashes)
            hashes.append(sha(frame.tobytes()))
            if idx in SELECT:
                frames[idx] = frame.copy()

        def release(self):
            pass

    with patch.object(cv2, 'VideoWriter', Sink):
        meta = getattr(module, 'generate_' + kind + '_proxy')(**cfg, out_path=Path(__file__).parent / 'evidence/offline.mp4')
    return hashes, frames, meta


def sheet(frames, target, crop=(160, 90, 480, 300)):
    w, h = (crop[2] - crop[0]) * 2, (crop[3] - crop[1]) * 2
    board = Image.new('RGB', (3 * w, 3 * (h + 24)), '#181818')
    draw = ImageDraw.Draw(board)
    for j, (idx, arr) in enumerate(sorted(frames.items())):
        tile = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)).crop(crop).resize((w, h))
        x, y = (j % 3) * w, (j // 3) * (h + 24)
        board.paste(tile, (x, y + 24))
        draw.text((x + 8, y + 5), f'frame {idx} / t={idx / 24:.4f}s', fill='white')
    board.save(target)


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    old, old_sha = load(PIN_OLD)
    new, new_sha = load(PIN_NEW)
    contract_path = ROOT / 'work/ro-sol1/t296/state_contract.json'
    contract = json.loads(contract_path.read_text())
    records, checks = [], []

    def check(label, ok):
        checks.append({'check': label, 'passed': bool(ok)})
        if not ok:
            raise AssertionError(label)

    cases = []
    for scene in contract['records']:
        image = ROOT / 'work/ro-sol1/t292' / scene['image']
        check(scene['scene'] + ': pinned image hash', sha(image.read_bytes()) == scene['image_sha256'])
        for p in (1.186, 2.0162):
            name = scene['scene'] + '_P' + str(p)
            cfg = dict(image_path=image, pivot=tuple(scene['pivot_xy']), bob=tuple(scene['bob_xy']),
                       period=p, amplitude_deg=85, release_from_rest=False, direction='inward',
                       num_frames=93, fps=24, width=832, height=480)
            cases.append((name, 'pendulum', cfg, True))

    # Fresh software fixtures, intentionally different from task302's fixtures.
    rng = np.random.default_rng(304)
    texture = cv2.GaussianBlur(rng.integers(0, 256, (256, 384, 3), dtype=np.uint8), (5, 5), 0)
    cv2.circle(texture, (130, 130), 12, (0, 170, 250), -1)
    synthetic = out / 'synthetic_texture.png'
    cv2.imwrite(str(synthetic), texture)
    for rest in (True, False):
        cases.append(('synthetic_pendulum_' + ('rest' if rest else 'outward'), 'pendulum',
                      dict(image_path=synthetic, pivot=(96, 35), bob=(65, 65), period=1.43,
                           release_from_rest=rest, amplitude_deg=62, direction='outward',
                           num_frames=17, fps=24, width=192, height=128), False))
    for hold, n in ((.5, 31), (0, 31), (.5, 1)):
        cases.append((f'synthetic_ball_hold{hold}_n{n}', 'ball',
                      dict(image_path=synthetic, center=(65, 65), radius=6, floor_y=110,
                           ppm=140, hold=hold, num_frames=n, fps=24, width=192, height=128), False))

    for name, kind, cfg, real in cases:
        image = cv2.imread(str(cfg['image_path']))
        expected = cv2.resize(image, (cfg['width'], cfg['height']), interpolation=cv2.INTER_AREA)
        ah, af, am = capture(old, kind, cfg)
        bh, bf, bm = capture(new, kind, cfg)
        check(name + ': both frame counts', len(ah) == len(bh) == cfg['num_frames'])
        check(name + ': raw frame0 exactly expected', np.array_equal(bf[0], expected))
        check(name + ': old boundary defect reproduced', not np.array_equal(af[0], expected))
        check(name + ': every later raw frame hash unchanged', ah[1:] == bh[1:])
        check(name + ': metadata unchanged', am == bm)
        rec = dict(name=name, kind=kind, synthetic=not real, frames=len(bh),
                   old_raw0_difference=diff(af[0], expected), new_raw0_difference=diff(bf[0], expected),
                   raw_sha256_before=ah, raw_sha256_after=bh)
        if real:
            # Published corrected MP4s are inputs to this review, not newly generated Nano videos.
            media = ROOT / 'work/ro-sol1/t302/evidence' / name / 'after.mp4'
            cap, decoded, dh = cv2.VideoCapture(str(media)), {}, []
            measured_fps = cap.get(cv2.CAP_PROP_FPS)
            while True:
                ok, f = cap.read()
                if not ok:
                    break
                i = len(dh)
                dh.append(sha(f.tobytes()))
                check(name + f': decoded shape {i}', f.shape == expected.shape)
                if i in SELECT:
                    decoded[i] = f.copy()
            cap.release()
            check(name + ': full published corrected decode', len(dh) == 93 and measured_fps == 24)
            rec.update(media=str(media.relative_to(ROOT)), media_sha256=sha(media.read_bytes()),
                       decoded_frames=len(dh), decoded_sha256=dh, fps=measured_fps,
                       decoded0_difference=diff(decoded[0], expected))
            archived = json.loads((media.parent / 'comparison.json').read_text())['trace']['after']['raw_frame_sha256']
            rec['raw_digest_matches_task302_archive'] = sum(a == b for a, b in zip(bh, archived))
            rec['raw_digest_compared_task302_archive'] = len(archived)
            sheet(bf, out / (name + '_raw.png'))
            sheet(decoded, out / (name + '_decoded.png'))
        elif kind == 'ball' and cfg['hold'] > 0 and cfg['num_frames'] > 1:
            rec['stationary_hold_frame0_to_frame1'] = diff(bf[0], bf[1])
            rec['baseline_hold_frame0_to_frame1'] = diff(af[0], af[1])
        records.append(rec)

    # Pixel-level spatial control: a tagged support pixel patch inside the wide rod mask
    # must move with that mask; a patch well outside it must stay at its source position.
    scene = contract['records'][0]
    src = ROOT / 'work/ro-sol1/t292' / scene['image']
    im = cv2.imread(str(src))
    base_cfg = dict(image_path=src, pivot=(322, 121), bob=(207, 154), period=1.186,
                    amplitude_deg=85, release_from_rest=False, direction='inward',
                    num_frames=15, fps=24, width=832, height=480)
    controls = []
    for label, box in [('support_inside_strip', (270, 146, 278, 154)),
                       ('background_outside_strip', (65, 200, 73, 208))]:
        tagged = im.copy()
        x0, y0, x1, y1 = box
        tagged[y0:y1, x0:x1] = (255, 0, 255)
        p = out / (label + '_input.png')
        cv2.imwrite(str(p), tagged)
        _, fs, _ = capture(new, 'pendulum', dict(base_cfg, image_path=p))
        evidence = []
        for idx in (0, 1, 7, 14):
            arr = fs[idx]
            ys, xs = np.where((arr[:, :, 0] > 235) & (arr[:, :, 1] < 25) & (arr[:, :, 2] > 235))
            check(f'{label}: tag survives at {idx}', len(xs) >= 30)
            center = (float(xs.mean()), float(ys.mean()))
            origin = ((x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2)
            if label == 'support_inside_strip':
                theta0 = math.atan2(207 - 322, 154 - 121)
                A, w = math.radians(85), 2 * math.pi / 1.186
                theta = theta0 * math.cos(w * idx / 24) + math.sqrt(A * A - theta0 * theta0) * math.sin(w * idx / 24)
                delta = theta - theta0
                dx, dy = origin[0] - 322, origin[1] - 121
                expected = (322 + math.cos(delta) * dx + math.sin(delta) * dy,
                            121 - math.sin(delta) * dx + math.cos(delta) * dy)
            else:
                expected = origin
            error = math.dist(center, expected)
            check(f'{label}: tag position matches spatial control {idx}', error < .6)
            evidence.append(dict(frame=idx, pixels=len(xs), centroid_xy=center,
                                 expected_xy=expected, centroid_error_px=error,
                                 displacement_from_source_px=math.dist(center, origin)))
        sheet(fs, out / (label + '_raw.png'))
        controls.append(dict(label=label, source_box_xyxy=box, observations=evidence))

    report = dict(status='INDEPENDENT SOFTWARE REVIEW; NOT PHYSICS OR NANO OUTPUT',
                  source_pins={PIN_OLD: old_sha, PIN_NEW: new_sha},
                  state_contract_sha256=sha(contract_path.read_bytes()),
                  versions=dict(python=platform.python_version(), opencv=cv2.__version__, numpy=np.__version__),
                  cases=records, marker_controls=controls, checks=checks,
                  total_checks=len(checks), passed=sum(x['passed'] for x in checks),
                  raw_frames_per_version=sum(x['frames'] for x in records),
                  later_raw_frames_unchanged=sum(x['frames'] - 1 for x in records),
                  published_corrected_frames_decoded=sum(x.get('decoded_frames', 0) for x in records),
                  no_model_queue_referee_requests=True)
    (out / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('total_checks', 'passed', 'raw_frames_per_version',
                     'later_raw_frames_unchanged', 'published_corrected_frames_decoded', 'versions')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent / 'evidence')
    args = parser.parse_args()

    def offline(*a, **k):
        raise RuntimeError('Network disabled in CPU review')

    with patch.object(socket, 'create_connection', offline), patch.object(socket.socket, 'connect', offline):
        main(args.out)
