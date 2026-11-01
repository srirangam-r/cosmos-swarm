"""E0 native-video temporal-change distance. See E0_ADAPTER.md.

This reads a frozen design and a separate artifact index. It does not infer
execution provenance from client requests or declare CPU-noise equivalence.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import analysis_core as core


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def unique_index(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        if value in result:
            raise ValueError('Duplicate ' + key + ': ' + str(value))
        result[value] = row
    return result


def validate_design(design, artifacts):
    if design.get('experiment') != 'E0' or design.get('schema_version') != 1:
        raise ValueError('Require E0 schema version 1')
    # Settings and identity fields are declarations. Actual request/server
    # records still require a separately published provenance audit.
    for name in ['stratum_id', 'input_sha256', 'prompt_sha256', 'settings',
                 'noise_device', 'reference', 'target']:
        if not design.get(name):
            raise ValueError('Missing design declaration: ' + name)
    for arm in ['reference', 'target']:
        if not all(design[arm].get(key) for key in ['gpu_type', 'stack_id']):
            raise ValueError('Missing declared GPU/stack for ' + arm)
    seeds = design['seeds']
    if len(seeds) < 2 or any(type(s) is not int for s in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError('Require at least two unique integer seeds')
    settings = design['settings']
    if (type(settings.get('num_frames')) is not int or settings['num_frames'] < 2
            or type(settings.get('width')) is not int or settings['width'] < 208
            or type(settings.get('height')) is not int or settings['height'] < 120
            or not np.isfinite(settings.get('fps', float('nan'))) or settings['fps'] <= 0):
        raise ValueError('Require native frames>=2, width>=208, height>=120 and positive fps')
    expected = {(arm, seed) for arm in ['reference', 'target'] for seed in seeds}
    rows = unique_index(design['runs'], 'run_id')
    cells = unique_index([dict(row, cell=(row['arm'], row['seed'])) for row in rows.values()], 'cell')
    if set(cells) != expected:
        raise ValueError('Planned runs must contain every arm x seed exactly once')
    found = unique_index(artifacts['artifacts'], 'run_id')
    if set(found) != set(rows):
        raise ValueError('Artifact join is not one-to-one and complete; missing=' +
                         str(sorted(set(rows) - set(found))) + '; extra=' +
                         str(sorted(set(found) - set(rows))))
    return seeds, cells, found


def decode_changes(path, settings):
    """Float64 BT.601 luma [0,1], INTER_AREA to 208x120, then f1-f0,... ."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError('Cannot decode video: ' + str(path))
    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if not np.isclose(fps, settings['fps'], atol=1e-6, rtol=0):
            raise ValueError('Native fps mismatch')
        previous = None
        changes = []
        count = 0
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            if bgr.shape != (settings['height'], settings['width'], 3):
                raise ValueError('Native geometry mismatch')
            # OpenCV decoding is BGR. Explicit weights avoid uint8 rounding
            # and implicit version-dependent cvtColor integer arithmetic.
            bgr = bgr.astype(np.float64) / 255.0
            gray = .114 * bgr[:, :, 0] + .587 * bgr[:, :, 1] + .299 * bgr[:, :, 2]
            small = cv2.resize(gray, (208, 120), interpolation=cv2.INTER_AREA)
            if previous is not None:
                changes.append(small - previous)
            previous = small
            count += 1
        if count != settings['num_frames']:
            raise ValueError('Decoded frame count mismatch: ' + str(count))
        return np.stack(changes), {'decoded_frames': count, 'fps': fps,
                                   'width': settings['width'], 'height': settings['height']}
    finally:
        cap.release()


def distances(reference, target):
    if len(reference) != len(target) or len(reference) < 2:
        raise ValueError('Need >=2 paired seeds')
    shape = reference[0].shape
    if any(x.shape != shape or not np.isfinite(x).all() for x in reference + target):
        raise ValueError('Incompatible/nonfinite temporal-change arrays')
    return np.asarray([[float(np.mean(np.abs(a - b), dtype=np.float64))
                        for b in target] for a in reference])


def measure(design, artifacts, artifact_root, bootstraps=core.BOOTSTRAPS, perms=core.PERMUTATIONS):
    seeds, cells, found = validate_design(design, artifacts)
    traces = {'reference': [], 'target': []}
    audit = []
    for arm in ['reference', 'target']:
        for seed in seeds:
            run = cells[(arm, seed)]
            artifact = found[run['run_id']]
            path = Path(artifact_root) / artifact['clip_path']
            actual = sha256(path)
            if actual != artifact['clip_sha256']:
                raise ValueError('Clip SHA256 mismatch: ' + run['run_id'])
            changes, contract = decode_changes(path, design['settings'])
            traces[arm].append(changes)
            audit.append(dict(run_id=run['run_id'], seed=seed, arm=arm,
                              clip_sha256=actual, **contract))
    matrix = distances(traces['reference'], traces['target'])
    result = core.correspondence(matrix, bootstraps=bootstraps, perms=perms)
    # Expose row-specific values as required by the frozen protocol. The
    # primary off-diagonal average is unchanged from analysis_core.py v1.
    per_seed = []
    for j, seed in enumerate(seeds):
        other = np.arange(len(seeds)) != j
        per_seed.append({'seed': seed, 'same_seed_distance': float(matrix[j, j]),
                         'different_seed_row_mean': float(matrix[j, other].mean()),
                         'row_difference': float(matrix[j, other].mean() - matrix[j, j])})
    return {'experiment': 'E0', 'stratum_id': design['stratum_id'], 'seed_order': seeds,
            'distance_matrix': matrix.tolist(), 'correspondence': result,
            'per_reference_seed': per_seed, 'artifact_contracts': audit,
            'scope': 'Unvalidated pixel-motion correspondence proxy, not physical motion or equivalence.',
            'provenance_gate': 'pending: GPU, stack, actual request, sampler and executed noise require native-record audit',
            'declared_comparison': {key: design[key] for key in
                                    ['reference', 'target', 'input_sha256', 'prompt_sha256',
                                     'noise_device', 'settings']},
            'versions': {'opencv': cv2.__version__, 'numpy': np.__version__}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('design')
    parser.add_argument('artifacts')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    design = json.loads(Path(args.design).read_text())
    artifacts = json.loads(Path(args.artifacts).read_text())
    result = measure(design, artifacts, Path(args.artifacts).resolve().parent)
    result['design_sha256'] = sha256(args.design)
    result['artifact_index_sha256'] = sha256(args.artifacts)
    result['protocol_version'] = 1
    result['adapter_version'] = 1
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
