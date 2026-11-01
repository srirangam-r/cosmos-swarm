"""Independent native-video E0 correspondence using unchanged frozen metric/core."""
import argparse
import itertools
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analysis_core as core
import e0_video as video

HERE = Path(__file__).resolve().parent
PAIRS = [('q8', 'l40s'), ('q8', 'a6k'), ('l40s', 'a6k')]


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def run(q8, targets, output):
    source = []
    for gpu in ['q8', 'l40s', 'a6k']:
        source += [json.loads(line) for line in (HERE / ('owner_E0_' + gpu + '.jsonl')).read_text().splitlines()]
    owner = video.unique_index(source, 'name')
    qdesign = json.loads((HERE.parent / 'e0_partial/q8_design_only.json').read_text())['runs']
    tdesign = json.loads((HERE / 'targets_design_only.json').read_text())['runs']
    assert set(owner) == {r['name'] for r in qdesign + tdesign}
    assert len(owner) == 32
    settings = dict(width=832, height=480, num_frames=93, fps=24)
    traces, audit, queue_records = {}, [], []
    decoder_checks = []
    for row in qdesign + tdesign:
        name = row['name']; parts = name.split('_')
        gpu, device, seed = parts[2], parts[3], int(parts[4][1:])
        root = q8 if gpu == 'q8' else targets
        actual = json.loads((root / (name + '.queue.json')).read_text())
        assert all(actual[k] == row[k] for k in row)
        assert actual['status'] == 'done'
        source_row = owner[name]
        assert source_row['prompt'] == row['prompt']
        assert Path(source_row['image']).name == row['image'] == 'ball1_dd33.png'
        for key, value in row['params'].items():
            assert source_row.get(key) == value, (name, key)
        side = actual['sidecar']; params = row['params']
        assert all(side[k] == v for k, v in params.items())
        assert all(params[k] == settings[k] for k in settings)
        assert params['steps'] == 35 and params['guidance'] == 6 and params['flow_shift'] == 10
        assert params['negative_prompt'] is None
        assert params['seed'] == seed and params['extra_params']['noise']['device'] == device
        assert side['prompt_text'] == row['prompt'] and side['image'] == row['image']
        assert side['queue_id'] == row['id'] and side['endpoint'] == actual['endpoint']
        assert side['endpoint'].startswith(gpu + '-')
        path = root / (name + '.mp4')
        trace, contract = video.decode_changes(path, settings)
        assert (gpu, device, seed) not in traces
        traces[gpu, device, seed] = trace
        audit.append(dict(name=name, run_id=row['id'], gpu_label=gpu, noise_requested=device,
                          seed=seed, endpoint=side['endpoint'], server_clip_id=side['server_clip_id'],
                          clip_sha256=video.sha256(path), native_video=contract))
        queue_records.append(actual)
        if device == 'cpu' and seed == 101:
            raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-frames:v', '3',
                                           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
            rgb = np.frombuffer(raw, dtype=np.uint8).reshape(3,480,832,3).astype(float)/255
            gray = rgb @ np.array([.299,.587,.114])
            small = gray.reshape(3,120,4,208,4).mean(axis=(2,4))
            error = float(np.max(np.abs(np.diff(small,axis=0)-trace[:2])))
            assert error < 2e-15
            decoder_checks.append(dict(name=name, max_error=error))
    results, matrices = [], {}
    for device in ['cpu', 'cuda']:
        seeds = list(range(101, 109 if device == 'cpu' else 105))
        for a,b in PAIRS:
            result = dict(device=device, reference=a, target=b, seed_order=seeds)
            if all((g,device,s) in traces for g in [a,b] for s in seeds):
                d = video.distances([traces[a,device,s] for s in seeds], [traces[b,device,s] for s in seeds])
                matrices[device,a,b] = d
                result.update(status='measured; execution provenance pending',
                              distance_matrix=d.tolist(), statistics=core.correspondence(d),
                              per_seed=[dict(seed=s, same=float(d[j,j]),
                                             different_row_mean=float(np.delete(d[j],j).mean()))
                                        for j,s in enumerate(seeds)])
            else:
                result.update(status='untested: no a6k CUDA arm in owner design', statistics=None)
            results.append(result)
    ps = [r['statistics']['permutation']['p_one_sided'] if r['statistics'] else 1 for r in results]
    for r,p in zip(results,core.holm(ps)):
        r['holm_p_family6'] = p if r['statistics'] else None
        r['internal_family_p'] = r['statistics']['permutation']['p_one_sided'] if r['statistics'] else 1

    # Pre-fixed secondary: same four seeds, paired CPU-minus-CUDA advantage.
    cpu4 = matrices['cpu','q8','l40s'][:4,:4]
    cuda4 = matrices['cuda','q8','l40s']
    def advantage(d, ids):
        block = d[np.ix_(ids,ids)]; off = ids[:,None] != ids[None,:]
        return float(block[off].mean()-np.diag(block).mean()) if off.any() else None
    ids = np.arange(4)
    point = advantage(cpu4,ids)-advantage(cuda4,ids)
    rng = np.random.default_rng(20261101); draws=[]
    for _ in range(core.BOOTSTRAPS):
        ids = rng.integers(0,4,4); ac=advantage(cpu4,ids); ag=advantage(cuda4,ids)
        draws.append(ac-ag if ac is not None else None)
    secondary = dict(seed_order=list(range(101,105)), reference='q8', target='l40s',
                     cpu_advantage=advantage(cpu4,np.arange(4)), cuda_advantage=advantage(cuda4,np.arange(4)),
                     cpu_minus_cuda_advantage=point, paired_seed_bootstrap=core.interval(draws),
                     scope='Pre-fixed secondary; n=4 descriptive, no independent noise-tensor proof.')
    within=[]
    for gpu in ['q8','l40s','a6k']:
        seeds = list(range(101,109))
        d=video.distances([traces[gpu,'cpu',s] for s in seeds], [traces[gpu,'cpu',s] for s in seeds])
        assert np.array_equal(np.diag(d),np.zeros(8))
        within.append(dict(gpu=gpu, seed_order=seeds, different_seed_mean=float(d[~np.eye(8,dtype=bool)].mean()),
                           distance_matrix=d.tolist(), n_seed_clusters=8, n_ordered_pairs=56))
    # Independent exact scalar enumeration verifies CUDA p; CPU uses frozen MC rule.
    observed=advantage(cuda4,np.arange(4)); hits=0
    for perm in itertools.permutations(range(4)):
        remapped=cuda4[:,perm]
        value=sum(remapped[i,j] for i in range(4) for j in range(4) if i!=j)/12-sum(remapped[i,i] for i in range(4))/4
        hits += int(value >= observed-1e-12)
    cuda_result=next(r for r in results if r['device']=='cuda' and r['reference']=='q8' and r['target']=='l40s')
    assert hits/24 == cuda_result['statistics']['permutation']['p_one_sided']
    result=dict(experiment='E0', scope='Independent same-video pixel-motion correspondence; not validated physics or equivalence.',
                metric='Unchanged PROTOCOL.md/e0_video.py/analysis_core.py from077a68c',
                design_mapping_board=4818, target_handoff_board=4840,
                native_artifacts=audit, decoder_checks=decoder_checks, comparisons=results,
                secondary_cpu_vs_cuda=secondary, same_gpu_cpu_controls=within,
                units='fractions of full gray range; multiply by255 for gray levels',
                provenance_gate='pending: input hashes/native execution records/noise tensor hashes/runtime and sampler revisions unavailable',
                limitations=['one real GAUGE frame, one F prompt, eight CPU seeds and four CUDA seeds',
                             'owner aggregate result4786 known before actual clip access; metric frozen before aggregate',
                             'two a6kCUDA comparisons not generated; full6member family retained',
                             'no independent same-host repeat generations; within-file self comparisons are arithmetic controls',
                             'GPU labels and noise devices are request/queue declarations, not native tensor authentication',
                             'no equivalence or unrestricted mixed-stack pairing permission'],
                sources={p.name:video.sha256(p) for p in sorted(HERE.glob('owner_E0_*.jsonl'))},
                independent_cuda_exact_p_check=dict(hits=hits, permutations=24),
                versions=dict(numpy=np.__version__,opencv=video.cv2.__version__))
    output.mkdir(parents=True,exist_ok=True)
    write(output/'results.json',result);write(output/'queue_records.json',queue_records)
    for r in results:
        print(json.dumps({k:v for k,v in r.items() if k not in ['distance_matrix','per_seed']},indent=2))
    print(json.dumps(secondary,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('q8',type=Path);ap.add_argument('targets',type=Path);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();run(args.q8,args.targets,args.out)
