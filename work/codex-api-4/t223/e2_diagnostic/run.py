"""Independent E2 native decode and frozen image-change cube diagnostic."""
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

PROMPTS = ['F', 'R', 'N', 'QT']
INPUTS = ['ball', 'held', 'pend']
SEEDS = list(range(301, 317))
METHOD = 'image_change_v1:e0_video@077a68c:all92:graylevels'
SETTINGS = dict(width=832, height=480, num_frames=93, fps=24)


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def make_design(runs):
    tests = [dict(id='omnibus4', kind='omnibus')] + [
        dict(id=p+'_minus_F', kind='contrast', a=p, b='F') for p in PROMPTS[1:]]
    return dict(version=1, experiment='E2',
                provenance=dict(status='unverified native execution; queue request audit only',
                                evidence=['PREREG.md', 'design_only_queue.json']),
                strata=[dict(id='declared_q8', levels=dict(seed=SEEDS, prompt=PROMPTS,
                                                         input=INPUTS), runs=runs)],
                outcomes=[dict(id='image_change', definition='255*mean(abs(all92 downsampled luma transitions))',
                               method=METHOD, value_range=[0, 255],
                               validation=dict(status='unvalidated proxy, not physics', evidence=['PREREG.md']))],
                tests=[dict(t, stratum='declared_q8', outcome='image_change', family='E2_M_primary4') for t in tests])


def descriptive(d):
    result = core.paired_prompt(d)
    for key in ('two_sided_sign_flip_p', 'permutations', 'exact'):
        result.pop(key)
    return result


def analyze(root, output):
    owner = video.unique_index([json.loads(line) for line in
                               (HERE/'owner_E2.jsonl').read_text().splitlines()], 'name')
    planned = json.loads((HERE/'design_only_queue.json').read_text())['runs']
    assert len(owner) == len(planned) == 192
    assert set(owner) == {r['name'] for r in planned}
    runs, outcomes, audits, records, decode_checks = [], [], [], [], []
    measurements = {}
    for row in planned:
        name = row['name']; _, _, inp, prompt, seed_text = name.split('_')
        seed = int(seed_text[1:]); source = owner[name]; params = row['params']
        assert Path(source['image']).name == row['image']
        assert source['prompt'] == row['prompt']
        for k, v in params.items():
            assert source.get(k) == v, (name, k)
        assert all(params[k] == v for k, v in SETTINGS.items())
        assert params['steps'] == 35 and params['guidance'] == 6 and params['flow_shift'] == 10
        assert params['negative_prompt'] is None and params['seed'] == seed
        assert params['extra_params']['noise'] == {'device': 'cpu'}
        assert params['extra_params']['input'] == inp and params['extra_params']['arm'] == prompt
        actual = json.loads((root/(name+'.queue.json')).read_text())
        assert all(actual[k] == row[k] for k in ('id', 'owner', 'name', 'prompt', 'image', 'params', 'endpoints'))
        if row['endpoint'] is not None:
            assert row['endpoint'] == actual['endpoint']
        endpoint = actual.get('endpoint')
        assert endpoint is None or endpoint in row['endpoints']
        assert set(row['endpoints']) == {'q8-'+str(i) for i in range(8)}
        records.append(actual); request_hash = video.sha256(root/(name+'.queue.json'))
        run = dict(run_id=row['id'], name=name, seed=seed, prompt=prompt, input=inp,
                   artifact_sha256=request_hash, artifact_identity_kind='queue_record_hash_pending_clip')
        audit = dict(run_id=row['id'], name=name, seed=seed, prompt=prompt, input=inp,
                     endpoint=endpoint, queue_status=actual['status'], queue_record_sha256=request_hash,
                     request_contract='pass')
        path = root/(name+'.mp4')
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
                value = float(np.abs(trace).mean()*255)
                audit.update(native_contract='pass', native_video=contract, image_change=value)
                outcomes.append(dict(run_id=row['id'], outcome='image_change', state='valid', value=value,
                                     method=METHOD, evidence=[clip_hash]))
                measurements[seed, prompt, inp] = value
                if len(decode_checks) < 3:
                    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                                                   '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
                    rgb = np.frombuffer(raw, np.uint8).reshape(93,480,832,3).astype(float)/255
                    gray = rgb @ np.array([.299,.587,.114])
                    small = gray.reshape(93,120,4,208,4).mean(axis=(2,4))
                    independent = np.diff(small, axis=0)
                    error = float(np.max(np.abs(independent-trace)))
                    scalar_error = abs(float(np.abs(independent).mean()*255)-value)
                    assert error < 3e-15 and scalar_error < 3e-13
                    decode_checks.append(dict(name=name, max_trace_error=error, scalar_error=scalar_error))
                    del rgb, gray, small, independent
                del trace
        else:
            audit.update(native_contract='not available', reason='queue status '+actual['status'])
        runs.append(run); audits.append(audit)
        if len(runs)%24 == 0:
            print('audited', len(runs), 'valid', len(measurements), flush=True)

    design = make_design(runs); primary = adapter.analyze(design, outcomes)
    seeds = [s for s in SEEDS if all((s,p,i) in measurements for p in PROMPTS for i in INPUTS)]
    excluded = [s for s in SEEDS if s not in seeds]
    sensitivity = secondary = None
    if len(seeds) >= 2:
        subset = json.loads(json.dumps(design))
        subset['strata'][0]['levels']['seed'] = seeds
        subset['strata'][0]['runs'] = [r for r in runs if r['seed'] in seeds]
        subset['tests'] = [dict(t, family='E2_M_complete_seed_sensitivity4') for t in subset['tests']]
        ids = {r['run_id'] for r in subset['strata'][0]['runs']}
        sensitivity = adapter.analyze(subset, [r for r in outcomes if r['run_id'] in ids])
        sensitivity.update(scope='Pre-fixed whole12cell-complete-seed sensitivity, not primary16seed estimand',
                           excluded_seeds=excluded)
        x = np.array([[[measurements[s,p,i] for i in INPUTS] for p in PROMPTS] for s in seeds])
        flat = x.reshape(len(seeds),12)
        with np.errstate(invalid='ignore', divide='ignore'):
            corr = np.corrcoef(flat,rowvar=False)
        secondary = dict(scope='descriptive, complete whole seed clusters only', seeds=seeds,
                         cell_order=[dict(prompt=p,input=i) for p in PROMPTS for i in INPUTS],
                         within_input=[], per_seed=[dict(seed=s,values=x[j].tolist()) for j,s in enumerate(seeds)],
                         covariance=np.cov(flat,rowvar=False,ddof=1).tolist(),
                         correlation=[[float(v) if np.isfinite(v) else None for v in row] for row in corr])
        for j, inp in enumerate(INPUTS):
            spread = float(x[:,:,j].mean(axis=1).std(ddof=1))
            for k,prompt in enumerate(PROMPTS[1:],1):
                d = x[:,k,j]-x[:,0,j]
                secondary['within_input'].append(dict(input=inp, contrast=prompt+'-F',
                    seed_mean_sample_sd=spread, effect=descriptive(d[:,None]),
                    effect_over_seed_spread=float(d.mean()/spread) if spread else None))
        for k,test in enumerate(sensitivity['tests'][1:],1):
            d = [(sum(row[k])-sum(row[0]))/3 for row in x.tolist()]
            hits = 0; observed = abs(sum(d)/len(d))
            for signs in itertools.product([-1,1], repeat=len(d)):
                value = abs(sum(a*b for a,b in zip(signs,d))/len(d))
                hits += int(value >= observed-1e-12)
            test['independent_exhaustive_scalar_p'] = hits/2**len(d)
            if test['result']['exact']:
                assert test['raw_p'] == test['independent_exhaustive_scalar_p']
    result = dict(experiment='E2', scope='Unvalidated whole-frame image-change, not physics or noise-vs-text causation',
        primary=primary, complete_seed_sensitivity=sensitivity, secondary=secondary,
        counts=dict(planned=192, fetched=sum('clip_sha256' in r for r in audits), valid=len(measurements),
                    complete_seed_clusters=len(seeds), queue_status=dict(Counter(r['queue_status'] for r in audits))),
        audits=audits, decode_checks=decode_checks,
        source_hashes={p.name:video.sha256(p) for p in [HERE/'PREREG.md',HERE/'owner_E2.jsonl',HERE/'design_only_queue.json']},
        versions=dict(numpy=np.__version__,opencv=video.cv2.__version__),
        limitations=['Input bundles image+base text; QT recipes differ between ball and pendulum',
                     'M mixes motion, appearance, camera, lighting and codec; no physical speed/rest/identity inference',
                     'No authenticated native noise/input/checkpoint/sampler/runtime records',
                     'Requested shift10; published Karras default ignores shift; actual sigmas unavailable',
                     'Missing queue cells are not model failures; complete-seed selection may be informative',
                     'No NVIDIA scoreboard, improvement or recipe claim'])
    output.mkdir(parents=True,exist_ok=True)
    for name,value in [('results',result),('queue_records',records),('design',design),('outcomes',outcomes)]:
        write(output/(name+'.json'),value)
    print(json.dumps(result['counts']),flush=True)
    if sensitivity:
        print(json.dumps(sensitivity['cubes'][0]['factorial']),flush=True)
        print(json.dumps(secondary['within_input']),flush=True)


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('clips',type=Path); ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(); analyze(args.clips,args.out)
