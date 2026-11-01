"""Audit available E0 q8 artifacts; missing cross-GPU tests stay untested."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analysis_core as core
import e0_video as video


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def audit(root, output):
    design = json.loads((Path(__file__).parent / 'q8_design_only.json').read_text())
    records, changes, native_records = [], {}, []
    settings = dict(width=832, height=480, num_frames=93, fps=24)
    assert len(design['runs']) == 12
    expected = {('cpu', s) for s in range(101, 109)} | {('cuda', s) for s in range(101, 105)}
    for row in design['runs']:
        name = row['name']
        actual = json.loads((root / (name + '.queue.json')).read_text())
        assert all(actual[k] == row[k] for k in row)
        assert actual['status'] == 'done'
        side = actual['sidecar']
        params = row['params']
        seed, device = params['seed'], params['extra_params']['noise']['device']
        assert (device, seed) in expected and (device, seed) not in changes
        assert all(params[k] == settings[k] for k in settings)
        assert params['steps'] == 35 and params['guidance'] == 6 and params['flow_shift'] == 10
        assert params['negative_prompt'] is None
        assert all(side[k] == v for k, v in params.items())
        assert side['prompt_text'] == row['prompt'] and side['image'] == row['image']
        assert side['queue_id'] == row['id'] and side['endpoint'] == actual['endpoint']
        path = root / (name + '.mp4')
        trace, contract = video.decode_changes(path, settings)
        changes[device, seed] = trace
        records.append(dict(run_id=row['id'], name=name, device_requested=device,
                            seed=seed, clip_sha256=video.sha256(path),
                            queue_record_sha256=video.sha256(root / (name + '.queue.json')),
                            endpoint=side['endpoint'], server_clip_id=side['server_clip_id'],
                            native_video=contract))
        native_records.append(actual)
    assert set(changes) == expected

    # Independent decoder + scalar block-area implementation, first two changes.
    decode_checks = []
    for device in ['cpu', 'cuda']:
        name = 'N_E0_q8_' + device + '_s101'
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(root / (name + '.mp4')),
                                       '-frames:v', '3', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        rgb = np.frombuffer(raw, dtype=np.uint8).reshape(3, 480, 832, 3).astype(float) / 255
        gray = rgb @ np.array([.299, .587, .114])
        small = gray.reshape(3, 120, 4, 208, 4).mean(axis=(2, 4))
        own = np.diff(small, axis=0)
        error = float(np.max(np.abs(own - changes[device, 101][:2])))
        assert error < 2e-15
        decode_checks.append(dict(name=name, independent_ffmpeg_block_area_max_error=error))

    seeds = list(range(101, 109))
    within_cpu = video.distances([changes['cpu', s] for s in seeds], [changes['cpu', s] for s in seeds])
    assert np.array_equal(np.diag(within_cpu), np.zeros(8))
    # Deliberately NOT a repeat-generation control: each diagonal reuses one file.
    first = list(range(101, 105))
    switched = video.distances([changes['cpu', s] for s in first], [changes['cuda', s] for s in first])
    diagnostic = core.correspondence(switched)
    diagnostic['scope'] = ('Exploratory same-GPU CPU-versus-CUDA device-switch diagnostic; '
                           'not a registered cross-GPU test or an equivalence test. Aggregate #4786 was known.')
    missing = []
    for device, n in [('cpu', 8), ('cuda', 4)]:
        for reference, target in [('q8', 'l40s'), ('q8', 'a6k'), ('l40s', 'a6k')]:
            missing.append(dict(noise_device=device, reference=reference, target=target,
                                planned_seed_count=n, reference_available=n if reference == 'q8' else 0,
                                target_available=0, p_value=None, holm_internal_p=1,
                                status='untested: required target artifacts unavailable'))
    result = dict(
        scope='Partial actual E0 artifact audit, not a cross-GPU replication or physical finding.',
        design_freeze_board=4818, design_sha256=video.sha256(Path(__file__).parent / 'q8_design_only.json'),
        protocol_sha256=video.sha256(Path(__file__).resolve().parents[1] / 'PROTOCOL.md'),
        artifact_count=12, artifacts=records, independent_decode_checks=decode_checks,
        registered_primary_family=missing,
        q8_cpu_seed_order=seeds, q8_cpu_within_gpu_distance_matrix=within_cpu.tolist(),
        q8_cpu_different_seed_mean=float(within_cpu[~np.eye(8, dtype=bool)].mean()),
        within_file_self_distance=0,
        self_control_limit='Same file compared with itself, not independently generated same-host repeats.',
        device_switch_seed_order=first, device_switch_distance_matrix=switched.tolist(),
        device_switch_diagnostic=diagnostic,
        provenance=dict(queue_request_and_video_contract='verified on 12 artifacts',
                        original_input_bytes='unavailable; basename alone does not establish image equality',
                        native_server_sidecars='not provided; queue sidecars contain request parameters',
                        executed_noise_shape_dtype_hash='not provided',
                        actual_sampler_sigmas='not provided; source default Karras, requested flow_shift=10 ignored',
                        checkpoint_and_runtime_revisions='not provided',
                        cross_gpu_execution='unverified'),
        units='Distances are fractions of full grayscale range; multiply by 255 for gray levels.',
        versions=dict(numpy=np.__version__, opencv=video.cv2.__version__))
    output.mkdir(parents=True, exist_ok=True)
    dump(output / 'queue_records.json', native_records)
    dump(output / 'results.json', result)
    print(json.dumps({k: result[k] for k in ['artifact_count', 'q8_cpu_different_seed_mean',
                                           'device_switch_diagnostic', 'independent_decode_checks']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifacts', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    audit(args.artifacts, args.out)
