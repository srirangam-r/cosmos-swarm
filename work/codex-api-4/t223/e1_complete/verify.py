"""Independent scalar checks of the published E1 numerical result."""
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import e0_video as video


def verify(root):
    result = json.loads((root / 'results.json').read_text())
    checks = []
    primary = result['primary']
    assert primary['cubes'][0]['planned_cells'] == 64
    assert primary['families'][0]['size'] == 3
    valid = result['counts']['valid']
    assert primary['cubes'][0]['counts']['valid'] == valid
    if valid < 64:
        assert not primary['cubes'][0]['complete']
        assert all(t['raw_p'] is None and t['holm_p'] is None for t in primary['tests'])
        assert primary['families'][0]['not_tested_count'] == 3
    checks.append('all planned cells and full primary Holm family retained')
    subset = result['complete_seed_sensitivity']
    if subset:
        cube = subset['cubes'][0]['cube']
        rows = [[v[0] for v in row] for row in cube]
        n, m = len(rows), 4
        grand = sum(sum(r) for r in rows) / (n*m)
        seedmeans = [sum(r)/m for r in rows]
        promptmeans = [sum(r[j] for r in rows)/n for j in range(m)]
        ss = {'seed': m*sum((v-grand)**2 for v in seedmeans),
              'prompt': n*sum((v-grand)**2 for v in promptmeans),
              'seed:prompt': sum((rows[i][j]-seedmeans[i]-promptmeans[j]+grand)**2
                                 for i in range(n) for j in range(m))}
        total = sum((v-grand)**2 for row in rows for v in row)
        published = subset['cubes'][0]['factorial']
        assert abs(sum(ss.values())-total) < 1e-10
        for term, value in ss.items():
            assert abs(value-published['ss'][term]) < 1e-10
            assert abs(value/total-published['eta2'][term]) < 1e-11
        checks.append('independent scalar seed/prompt/interaction SS and eta2')
        for test, k in zip(subset['tests'][1:], [1, 3]):
            differences = [r[k]-r[k-1] for r in rows]
            mean = sum(differences)/n
            assert abs(mean-test['result']['mean_difference']) < 1e-12
            if n <= 16:
                exceed = 0
                for signs in itertools.product([-1, 1], repeat=n):
                    null = abs(sum(a*b for a,b in zip(signs, differences))/n)
                    exceed += int(null >= abs(mean)-1e-12)
                exact_p = exceed/2**n
                assert abs(exact_p-test['independent_exhaustive_scalar_p']) < 1e-12
                if test['result']['exact']:
                    assert abs(exact_p-test['raw_p']) < 1e-12
        checks.append('independent scalar paired differences and exhaustive p')
        # Sample covariance, with scalar arithmetic and explicit denominators.
        cov = result['secondary']['covariance']
        for a in range(m):
            for b in range(m):
                expected = sum((r[a]-promptmeans[a])*(r[b]-promptmeans[b]) for r in rows)/(n-1)
                assert abs(cov[a][b]-expected) < 1e-11
        checks.append('all16 scalar covariance entries')
    assert len(result['decode_checks']) == 3
    assert all(r['max_trace_error'] < 3e-15 for r in result['decode_checks'])
    checks.append('three full-video independent ffmpeg/block-area checks')
    endpoints = {(r['seed'], r['prompt']): r['endpoint'] for r in result['audits']}
    seeds = result['secondary']['seeds'] if result['secondary'] else []
    prompt_names = ['red_slow', 'red_fast', 'blue_slow', 'blue_fast']
    endpoint_audit = dict(complete_seeds=len(seeds),
                         all_four_exact_endpoint=sum(len({endpoints[s,p] for p in prompt_names})==1 for s in seeds),
                         red_speed_exact_endpoint=sum(endpoints[s,'red_slow']==endpoints[s,'red_fast'] for s in seeds),
                         blue_speed_exact_endpoint=sum(endpoints[s,'blue_slow']==endpoints[s,'blue_fast'] for s in seeds))
    for filename in ['PROTOCOL.md', 'analysis_core.py', 'e0_video.py',
                     'FACTORIAL_ADAPTER.md', 'factorial_adapter.py']:
        expected = dict(line.split(maxsplit=1)[::-1] for line in
                        (HERE.parent / 'SHA256SUMS').read_text().splitlines())
        # The root checksum file has a larger index; only these files are used.
        key = filename
        assert video.sha256(HERE.parent / filename) == expected[key]
    checks.append('all five pre-existing protocol/core/adapter hashes unchanged')
    output = dict(status='pass', checks=checks,
                  endpoint_matching=endpoint_audit,
                  result_sha256=video.sha256(root/'results.json'),
                  scope='Independent numerical/software verification, not planted validation')
    (root/'verification.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    verify(Path(sys.argv[1]) if len(sys.argv)>1 else HERE)
