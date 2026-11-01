"""Independent native E1 decoding and frozen image-change diagnostic."""
import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analysis_core as core
import e0_video as video
import factorial_adapter as adapter

PROMPTS = ['red_slow', 'red_fast', 'blue_slow', 'blue_fast']
METHOD = 'image_change_v1:e0_video@077a68c:all92:graylevels'
SETTINGS = dict(width=832, height=480, num_frames=93, fps=24)


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def make_design(runs):
    tests = [dict(id='omnibus4', kind='omnibus'),
             dict(id='red_fast_slow', kind='contrast', a='red_fast', b='red_slow'),
             dict(id='blue_fast_slow', kind='contrast', a='blue_fast', b='blue_slow')]
    return dict(version=1, experiment='E1',
                provenance=dict(status='unverified native execution; queue request audit only',
                                evidence=['PREREG.md', 'design_only_queue.json']),
                strata=[dict(id='declared_q8', levels=dict(seed=list(range(201, 217)),
                             prompt=PROMPTS, input=['T2V']), runs=runs)],
                outcomes=[dict(id='image_change', definition='255*mean(abs(all92 downsampled luma transitions))',
                               method=METHOD, value_range=[0, 255],
                               validation=dict(status='unvalidated proxy, not physics', evidence=['PREREG.md']))],
                tests=[dict(t, stratum='declared_q8', outcome='image_change', family='E1_M_primary3') for t in tests])


def analyze(root, output):
    expected = [json.loads(line) for line in (HERE / 'owner_E1.jsonl').read_text().splitlines()]
    owner = video.unique_index(expected, 'name')
    planned = json.loads((HERE / 'design_only_queue.json').read_text())['runs']
    assert len(owner) == len(planned) == 64
    assert set(owner) == {r['name'] for r in planned}
    runs, outcomes, audits, records, decode_checks = [], [], [], [], []
    measurements = {}
    for row in planned:
        name = row['name']
        color, speed, seed = name.split('_')[2:]
        seed = int(seed[1:]); prompt = color + '_' + speed
        source = owner[name]
        assert row['image'] is None and 'image' not in source
        assert source['prompt'] == row['prompt']
        params = row['params']
        for k, v in params.items():
            assert source.get(k) == v, (name, k)
        assert all(params[k] == v for k, v in SETTINGS.items())
        assert params['steps'] == 35 and params['guidance'] == 6 and params['flow_shift'] == 10
        assert params['negative_prompt'] is None and params['seed'] == seed
        assert params['extra_params']['noise'] == {'device': 'cpu'}
        actual = json.loads((root / (name + '.queue.json')).read_text())
        assert all(actual[k] == row[k] for k in ('id', 'owner', 'name', 'prompt', 'image', 'params', 'endpoints'))
        if row['endpoint'] is not None:
            assert row['endpoint'] == actual['endpoint']
        endpoint = actual.get('endpoint')
        assert endpoint is None or endpoint in row['endpoints']
        records.append(actual)
        request_hash = video.sha256(root / (name + '.queue.json'))
        run = dict(run_id=row['id'], name=name, seed=seed, prompt=prompt, input='T2V',
                   artifact_sha256=request_hash, artifact_identity_kind='queue_record_hash_pending_clip')
        audit = dict(run_id=row['id'], name=name, seed=seed, prompt=prompt, endpoint=endpoint,
                     queue_status=actual['status'], queue_record_sha256=request_hash,
                     request_contract='pass')
        path = root / (name + '.mp4')
        if actual['status'] == 'done':
            side = actual['sidecar']
            assert all(side[k] == v for k, v in params.items())
            assert side['prompt_text'] == row['prompt']
            assert side['queue_id'] == row['id'] and side['endpoint'] == endpoint
            clip_hash = video.sha256(path)
            run.update(artifact_sha256=clip_hash, artifact_identity_kind='native_mp4_sha256')
            audit.update(clip_sha256=clip_hash)
            try:
                trace, contract = video.decode_changes(path, SETTINGS)
            except ValueError as exc:
                audit.update(native_contract='invalid', reason=str(exc))
                outcomes.append(dict(run_id=row['id'], outcome='image_change', state='invalid', value=None,
                                     reason=str(exc), method=METHOD, evidence=[clip_hash]))
            else:
                value = float(np.abs(trace).mean() * 255)
                audit.update(native_contract='pass', native_video=contract, image_change=value)
                outcomes.append(dict(run_id=row['id'], outcome='image_change', state='valid', value=value,
                                     method=METHOD, evidence=[clip_hash]))
                measurements[seed, prompt] = value
                if len(decode_checks) < 3:
                    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                                                   '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
                    rgb = np.frombuffer(raw, np.uint8).reshape(93, 480, 832, 3).astype(float) / 255
                    gray = rgb @ np.array([.299, .587, .114])
                    small = gray.reshape(93, 120, 4, 208, 4).mean(axis=(2, 4))
                    ff_trace = np.diff(small, axis=0)
                    error = float(np.max(np.abs(ff_trace - trace)))
                    ff_value = float(np.abs(ff_trace).mean() * 255)
                    assert error < 3e-15 and abs(ff_value - value) < 3e-13
                    decode_checks.append(dict(name=name, max_trace_error=error,
                                              scalar_error=abs(ff_value-value)))
                    del rgb, gray, small, ff_trace
                del trace
        else:
            audit.update(native_contract='not available', reason='queue status ' + actual['status'])
        runs.append(run); audits.append(audit)

    design = make_design(runs)
    primary = adapter.analyze(design, outcomes)
    assert len(primary['tests']) == 3
    seeds = [s for s in range(201, 217) if all((s, p) in measurements for p in PROMPTS)]
    excluded = [s for s in range(201, 217) if s not in seeds]
    sensitivity = None
    if len(seeds) >= 2:
        subset = json.loads(json.dumps(design))
        subset['strata'][0]['levels']['seed'] = seeds
        subset['strata'][0]['runs'] = [r for r in runs if r['seed'] in seeds]
        subset['tests'] = [dict(t, family='E1_M_complete_seed_sensitivity3') for t in subset['tests']]
        selected_ids = {r['run_id'] for r in subset['strata'][0]['runs']}
        subset_outcomes = [r for r in outcomes if r['run_id'] in selected_ids]
        sensitivity = adapter.analyze(subset, subset_outcomes)
        sensitivity.update(scope='Pre-fixed complete-seed sensitivity; not the primary16-seed planned estimand',
                           excluded_seeds=excluded)
        x = np.array([[measurements[s, p] for p in PROMPTS] for s in seeds])
        speed = ((x[:, 1] - x[:, 0]) + (x[:, 3] - x[:, 2])) / 2
        color = ((x[:, 2] - x[:, 0]) + (x[:, 3] - x[:, 1])) / 2
        spread = float(x.mean(axis=1).std(ddof=1))
        def contrast(d):
            result = core.paired_prompt(d[:, None])
            # The secondary contrast is descriptive: do not add a posthoc test.
            for key in ('two_sided_sign_flip_p', 'permutations', 'exact'):
                result.pop(key)
            return result
        covariance = np.cov(x, rowvar=False, ddof=1)
        with np.errstate(invalid='ignore', divide='ignore'):
            correlation = np.corrcoef(x, rowvar=False)
        secondary = dict(scope='descriptive, complete seeds only', seeds=seeds, prompt_order=PROMPTS,
                         speed_fast_minus_slow=contrast(speed), blue_minus_red=contrast(color),
                         seed_mean_sample_sd=spread,
                         speed_effect_divided_by_seed_spread=float(speed.mean()/spread) if spread else None,
                         absolute_speed_difference_divided_by_seed_spread=float(np.abs(speed).mean()/spread) if spread else None,
                         covariance=covariance.tolist(),
                         correlation=[[float(v) if np.isfinite(v) else None for v in r] for r in correlation],
                         per_seed=[dict(seed=s, values=x[j].tolist(), speed_difference=float(speed[j]),
                                        colour_difference=float(color[j])) for j, s in enumerate(seeds)])
        # Independent exhaustive scalar sign-flip check on both speed tests.
        for column, test in [(1, sensitivity['tests'][1]), (3, sensitivity['tests'][2])]:
            d = [float(x[j, column] - x[j, column-1]) for j in range(len(seeds))]
            if len(seeds) <= 16:
                hits = 0; observed = abs(sum(d) / len(d))
                for signs in itertools.product([-1, 1], repeat=len(d)):
                    stat = abs(sum(s*v for s, v in zip(signs, d)) / len(d))
                    hits += int(stat >= observed-1e-12)
                exact_p = hits / 2**len(d)
                test['independent_exhaustive_scalar_p'] = exact_p
                if test['result']['exact']:
                    assert test['raw_p'] == exact_p
    else:
        secondary = None
    result = dict(experiment='E1', scope='Unvalidated image-change diagnostic; no physical period/speed/colour or recipe claim',
                  primary=primary, complete_seed_sensitivity=sensitivity, secondary=secondary,
                  counts=dict(planned=64, fetched=sum('clip_sha256' in r for r in audits),
                              valid=len(measurements), complete_seed_clusters=len(seeds),
                              queue_status=dict(Counter(r['queue_status'] for r in audits))),
                  audits=audits, decode_checks=decode_checks,
                  source_hashes={p.name: video.sha256(p) for p in
                                 [HERE/'PREREG.md', HERE/'owner_E1.jsonl', HERE/'design_only_queue.json']},
                  versions=dict(numpy=np.__version__, opencv=video.cv2.__version__),
                  limitations=['T2V appearance and motion both vary; M is not speed or physics',
                               'no authenticated native noise/input/checkpoint/sampler/runtime records',
                               'requested shift10; published Karras default ignores shift; actual sigmas unavailable',
                               'one scene description; no real-photo test or NVIDIA scoreboard result',
                               'pending/running status is not a model failure; missingness may be outcome-related'])
    output.mkdir(parents=True, exist_ok=True)
    for name, value in [('results', result), ('queue_records', records), ('design', design), ('outcomes', outcomes)]:
        write(output/(name+'.json'), value)
    print(json.dumps(result['counts']))
    if sensitivity:
        print(json.dumps(sensitivity['cubes'][0]['factorial'], indent=2))
        print(json.dumps(secondary, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('clips', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    analyze(args.clips, args.out)
