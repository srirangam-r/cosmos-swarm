"""Independent scalar E2 SS/contrast/covariance and provenance checks."""
import itertools
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import e0_video as video


def verify(root):
    r=json.loads((root/'results.json').read_text()); checks=[]
    primary=r['primary']; report=primary['cubes'][0]
    assert report['planned_cells']==192 and primary['families'][0]['size']==4
    assert report['counts']['valid']==r['counts']['valid']
    if r['counts']['valid']<192:
        assert not report['complete']
        assert all(t['raw_p'] is None and t['holm_p'] is None for t in primary['tests'])
        assert primary['families'][0]['not_tested_count']==4
    checks.append('all192 cells and primary4-family retained; incomplete primary blocked')
    subset=r['complete_seed_sensitivity']
    if subset:
        cube=subset['cubes'][0]['cube']; n=len(cube); dims=[n,4,3]
        cells=[(s,p,i) for s in range(n) for p in range(4) for i in range(3)]
        values={k:cube[k[0]][k[1]][k[2]] for k in cells}
        grand=sum(values.values())/len(cells)
        ss={}
        for mask in range(1,8):
            axes=[a for a in range(3) if mask & (1<<a)]
            groups={}
            for key,v in values.items():
                group=tuple(key[a] for a in axes)
                groups.setdefault(group,[]).append(v)
            explained=sum(len(g)*(sum(g)/len(g)-grand)**2 for g in groups.values())
            ss[mask]=explained-sum(v for sub,v in ss.items() if sub & mask==sub)
        names={1:'seed',2:'prompt',4:'input',3:'seed:prompt',5:'seed:input',
               6:'prompt:input',7:'seed:prompt:input_or_residual'}
        f=subset['cubes'][0]['factorial']; total=sum((v-grand)**2 for v in values.values())
        assert abs(sum(ss.values())-total)<1e-9
        for mask,v in ss.items():
            assert abs(v-f['ss'][names[mask]])<1e-9
            assert abs(v/total-f['eta2'][names[mask]])<1e-10
        checks.append('independent scalar conditional-means/Mobius all7SS and eta2')
        for k,t in enumerate(subset['tests'][1:],1):
            d=[(sum(row[k])-sum(row[0]))/3 for row in cube]
            observed=sum(d)/n
            assert abs(observed-t['result']['mean_difference'])<1e-12
            hits=sum(abs(sum(a*b for a,b in zip(signs,d))/n)>=abs(observed)-1e-12
                     for signs in itertools.product([-1,1],repeat=n))
            assert hits/2**n==t['independent_exhaustive_scalar_p']
        checks.append('independent scalar recipe contrasts and3 exhaustive sign-flip references')
        for row in r['secondary']['within_input']:
            j=['ball','held','pend'].index(row['input']); k=['F','R','N','QT'].index(row['contrast'].split('-')[0])
            d=[x[k][j]-x[0][j] for x in cube]; mean=sum(d)/n
            assert abs(mean-row['effect']['mean_difference'])<1e-12
            se=(sum((v-mean)**2 for v in d)/(n-1)/n)**.5
            assert abs(se-row['effect']['seed_se'])<1e-12
        checks.append('all9 within-input scalar effect/SE checks')
        flat=[[v for prompt in row for v in prompt] for row in cube]
        means=[sum(row[j] for row in flat)/n for j in range(12)]
        for a in range(12):
            for b in range(12):
                cov=sum((row[a]-means[a])*(row[b]-means[b]) for row in flat)/(n-1)
                assert abs(cov-r['secondary']['covariance'][a][b])<1e-10
        checks.append('all144 scalar covariance entries')
    assert len(r['decode_checks'])==3
    assert all(row['max_trace_error']<3e-15 for row in r['decode_checks'])
    checks.append('three independent full FFmpeg/block-area native trace checks')
    expected=dict(line.split(maxsplit=1)[::-1] for line in (HERE.parent/'SHA256SUMS').read_text().splitlines())
    for name in ['PROTOCOL.md','analysis_core.py','e0_video.py','FACTORIAL_ADAPTER.md','factorial_adapter.py']:
        assert video.sha256(HERE.parent/name)==expected[name]
    checks.append('all5 pre-existing protocol/core/adapter files unchanged')
    ep={(row['seed'],row['prompt'],row['input']):row['endpoint'] for row in r['audits']}
    seeds=r['secondary']['seeds'] if r['secondary'] else []
    pairing={inp:{p:sum(ep[s,p,inp]==ep[s,'F',inp] for s in seeds) for p in ['R','N','QT']}
             for inp in ['ball','held','pend']}
    out=dict(status='pass',checks=checks,complete_seeds=seeds,exact_endpoint_pairing=pairing,
             endpoint_counts=dict(__import__('collections').Counter(row['endpoint'] for row in r['audits'])),
             result_sha256=video.sha256(root/'results.json'),scope='Software/numerical check, not planted validation')
    (root/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    verify(Path(sys.argv[1]) if len(sys.argv)>1 else HERE)
