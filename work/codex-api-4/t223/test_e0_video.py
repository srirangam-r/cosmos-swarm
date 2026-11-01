"""Manufactured native videos only; not Cosmos outcomes or referee clips."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import e0_video as e

HERE = Path(__file__).resolve().parent


def encode(path, frames, fps=24):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                    '-s', str(frames.shape[2]) + 'x' + str(frames.shape[1]), '-r', str(fps),
                    '-i', '-', '-c:v', 'ffv1', '-pix_fmt', 'bgr0', str(path)],
                   input=frames.tobytes(), check=True, capture_output=True)


def main():
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        assert condition, name
    def reject(name, function):
        try:
            function()
        except ValueError:
            check(name, True)
        else:
            check(name, False)

    with tempfile.TemporaryDirectory(prefix='program-n-e0-') as scratch:
        root = Path(scratch)
        settings = {'width': 416, 'height': 240, 'num_frames': 6, 'fps': 24,
                    'steps': 35, 'guidance': 6, 'sampler': 'synthetic-only'}
        design = {'schema_version': 1, 'experiment': 'E0', 'stratum_id': 'synthetic-only',
                  'input_sha256': 'synthetic-input', 'prompt_sha256': 'synthetic-prompt',
                  'settings': settings, 'noise_device': 'cpu',
                  'reference': {'gpu_type': 'synthetic-A', 'stack_id': 'fixture-A'},
                  'target': {'gpu_type': 'synthetic-B', 'stack_id': 'fixture-B'},
                  'seeds': [101, 102, 103], 'runs': []}
        artifacts = {'artifacts': []}
        frames_by_seed = []
        for j, seed in enumerate(design['seeds']):
            frames = np.full((6, 240, 416, 3), 20, dtype=np.uint8)
            for t in range(6):
                frames[t, 40:80, (20 + j*80 + t*4):(60 + j*80 + t*4), j] = 180
            frames_by_seed.append(frames)
            path = root / (str(seed) + '.mkv')
            encode(path, frames)
            for arm in ['reference', 'target']:
                run_id = arm + '-' + str(seed)
                design['runs'].append({'run_id': run_id, 'seed': seed, 'arm': arm})
                artifacts['artifacts'].append({'run_id': run_id, 'clip_path': path.name,
                                                'clip_sha256': e.sha256(path)})
        got = e.measure(design, artifacts, root, bootstraps=100, perms=100)
        check('matched lossless clips distance zero', got['correspondence']['same_seed_distance'] == 0)
        check('different synthetic motion gives positive null', got['correspondence']['different_seed_distance'] > 0)
        check('all-pairs matrix keeps frozen seed order', got['seed_order'] == [101, 102, 103])
        check('all planned clips audited', len(got['artifact_contracts']) == 6)
        check('per-seed contributions average to primary', np.isclose(
            np.mean([r['row_difference'] for r in got['per_reference_seed']]),
            got['correspondence']['different_minus_same']))
        check('declared CPU noise remains unverified', got['provenance_gate'].startswith('pending:'))
        shuffled = copy.deepcopy(artifacts)
        shuffled['artifacts'].reverse()
        check('artifact order cannot permute seeds', got == e.measure(design, shuffled, root, bootstraps=100, perms=100))

        # Independent FFmpeg RGB decode + hand 2x2 averaging (no cv2 conversion).
        path = root / '101.mkv'
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'rawvideo',
                              '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
        rgb = np.frombuffer(raw, dtype=np.uint8).reshape(6, 240, 416, 3)
        check('FFV1 fixture exactly preserves RGB bytes', np.array_equal(rgb, frames_by_seed[0]))
        gray = (rgb.astype(float) * np.array([.299, .587, .114])).sum(axis=3) / 255
        manual = gray.reshape(6, 120, 2, 208, 2).mean(axis=(2, 4))
        changes, _ = e.decode_changes(path, settings)
        check('independent decode and hand area average agree', np.allclose(changes, np.diff(manual, axis=0), atol=1e-15, rtol=0))
        check('f0-to-f1 transition retained', np.max(np.abs(changes[0])) > 0)
        check('six frames give exactly five changes', changes.shape == (5, 120, 208))
        # An isolated initial-frame change must not disappear when frame 0 is
        # excluded as an RGB observation but retained as the first difference.
        pulse = np.full((6, 240, 416, 3), 40, dtype=np.uint8)
        pulse[0] = 0
        encode(root / 'pulse.mkv', pulse)
        pc, _ = e.decode_changes(root / 'pulse.mkv', settings)
        check('initial pulse included once', np.isclose(pc[0].mean(), 40/255) and np.max(np.abs(pc[1:])) == 0)
        still = np.full((6, 240, 416, 3), 40, dtype=np.uint8)
        encode(root / 'still.mkv', still)
        st, _ = e.decode_changes(root / 'still.mkv', settings)
        sd = e.distances([st, st, st], [st, st, st])
        check('static clips create zero correspondence advantage', e.core.correspondence(sd, bootstraps=50)['different_minus_same'] == 0)
        offset = frames_by_seed[0] + np.uint8(10)
        encode(root / 'offset.mkv', offset)
        oc, _ = e.decode_changes(root / 'offset.mkv', settings)
        check('constant background offset cancels in changes', np.allclose(changes, oc, atol=1e-15, rtol=0))
        permuted = copy.deepcopy(artifacts)
        targets = [r for r in permuted['artifacts'] if r['run_id'].startswith('target')]
        first_path, first_hash = targets[0]['clip_path'], targets[0]['clip_sha256']
        for j in range(2):
            targets[j]['clip_path'], targets[j]['clip_sha256'] = targets[j+1]['clip_path'], targets[j+1]['clip_sha256']
        targets[2]['clip_path'], targets[2]['clip_sha256'] = first_path, first_hash
        wrong = e.measure(design, permuted, root, bootstraps=50, perms=100)
        check('wrong seed mapping loses correspondence', wrong['correspondence']['different_minus_same'] < 0)

        def mutate_design(name, change):
            item = copy.deepcopy(design)
            change(item)
            reject(name, lambda: e.validate_design(item, artifacts))
        mutate_design('duplicate seed rejected', lambda d: d['seeds'].append(101))
        mutate_design('one seed rejected', lambda d: d.update(seeds=[101]))
        mutate_design('missing planned cell rejected', lambda d: d['runs'].pop())
        mutate_design('duplicate planned run rejected', lambda d: d['runs'].append(d['runs'][0]))
        mutate_design('duplicate factorial cell rejected', lambda d: d['runs'].append(dict(d['runs'][0], run_id='new')))
        mutate_design('unplanned seed rejected', lambda d: d['runs'][0].update(seed=900))
        mutate_design('missing stack declaration rejected', lambda d: d['target'].pop('stack_id'))
        mutate_design('missing settings declaration rejected', lambda d: d.pop('settings'))
        mutate_design('invalid fps rejected', lambda d: d['settings'].update(fps=0))
        mutate_design('upsampling geometry rejected', lambda d: d['settings'].update(width=100))
        for name, rows in [('missing artifact rejected', artifacts['artifacts'][:-1]),
                           ('duplicate artifact rejected', artifacts['artifacts'] + [artifacts['artifacts'][0]]),
                           ('extra artifact rejected', artifacts['artifacts'] + [dict(artifacts['artifacts'][0], run_id='extra')])]:
            reject(name, lambda rows=rows: e.validate_design(design, {'artifacts': rows}))
        broken = copy.deepcopy(artifacts)
        broken['artifacts'][0]['clip_sha256'] = '0'*64
        reject('changed artifact hash rejected', lambda: e.measure(design, broken, root, bootstraps=2))
        for key, value in [('fps', 25), ('num_frames', 5), ('width', 418), ('height', 242)]:
            reject('native ' + key + ' mismatch rejected', lambda key=key, value=value:
                   e.decode_changes(path, dict(settings, **{key: value})))
        reject('unequal feature dimensions rejected', lambda: e.distances([changes, changes], [changes[:2], changes]))

        (root / 'design.json').write_text(json.dumps(design))
        (root / 'artifacts.json').write_text(json.dumps(artifacts))
        for label in ['one', 'two']:
            run = subprocess.run([sys.executable, str(HERE / 'e0_video.py'), str(root / 'design.json'),
                                  str(root / 'artifacts.json'), '--out', str(root / (label + '.json'))],
                                 capture_output=True, text=True)
            check('CLI ' + label + ' succeeds', run.returncode == 0)
        check('CLI replay byte-identical', (root / 'one.json').read_bytes() == (root / 'two.json').read_bytes())
        saved = json.loads((root / 'one.json').read_text())
        check('CLI hashes design and artifact index', saved['design_sha256'] == e.sha256(root / 'design.json')
              and saved['artifact_index_sha256'] == e.sha256(root / 'artifacts.json'))

    result = {'scope': 'Manufactured FFV1 videos only; no Cosmos results or referee clips.',
              'passed_checks': len(checks), 'checks': checks}
    (HERE / 'e0_synthetic_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed_checks': len(checks)}))


if __name__ == '__main__':
    main()
