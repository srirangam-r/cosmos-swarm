"""Manufactured records/arrays only; no Cosmos outcomes or referee clips."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import analysis_core as core
import factorial_adapter as adapter

HERE = Path(__file__).resolve().parent


def fixture():
    levels = {'seed': [11, 12, 13, 14], 'prompt': ['base', 'alt', 'neutral'], 'input': ['a', 'b']}
    runs, outcomes = [], []
    for s, p, i in itertools.product(*levels.values()):
        rid = f'{s}-{p}-{i}'
        runs.append({'run_id': rid, 'seed': s, 'prompt': p, 'input': i,
                     'artifact_sha256': hashlib.sha256(rid.encode()).hexdigest()})
        # Pure input-specific prompt effect, reversing across input a/b.
        value = (levels['prompt'].index(p) - 1) * (1 if i == 'a' else -1) + (s - 11)
        outcomes.append({'run_id': rid, 'outcome': 'motion', 'state': 'valid', 'value': value,
                         'method': 'manufactured@1', 'evidence': 'manufactured array cell'})
    design = {'version': 1, 'experiment': 'E1', 'provenance': {'status': 'unverified', 'evidence': []},
              'strata': [{'id': 'gpuA', 'levels': levels, 'runs': runs}],
              'outcomes': [{'id': 'motion', 'definition': 'Manufactured diagnostic', 'method': 'manufactured@1',
                            'validation': {'status': 'unvalidated', 'evidence': []}}],
              'tests': [{'id': 'joint', 'stratum': 'gpuA', 'outcome': 'motion', 'kind': 'omnibus', 'family': 'E1'},
                        {'id': 'pair', 'stratum': 'gpuA', 'outcome': 'motion', 'kind': 'contrast',
                         'a': 'alt', 'b': 'base', 'family': 'E1'}]}
    return design, outcomes


def main():
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        assert condition, name
    def rejects(name, d, o):
        try:
            adapter.analyze(d, o, bootstraps=12, perms=31)
        except (ValueError, KeyError, TypeError):
            check(name, True)
        else:
            check(name, False)
    d, o = fixture()
    result = adapter.analyze(d, o, bootstraps=80, perms=2000)
    cube = np.asarray(result['cubes'][0]['cube'])
    check('strict ordered cube join', cube.shape == (4, 3, 2) and cube[0, 0, 0] == -1)
    check('all planned cells retained', result['cubes'][0]['counts'] == {'valid': 24, 'invalid': 0, 'unknown': 0, 'missing': 0})
    check('input-specific effect cancels in pooled prompt means', np.ptp(cube.mean(axis=(0, 2))) == 0)
    check('joint test detects input-specific prompt effect', result['tests'][0]['raw_p'] < .01)
    check('pooled paired contrast cancellation is reported', result['tests'][1]['raw_p'] == 1)
    check('omnibus statistic equals frozen SS formula', np.isclose(adapter.joint_statistic(cube),
          (core.eta_components(cube)['ss']['prompt'] + core.eta_components(cube)['ss']['prompt:input']) / 4))
    # Independent scalar enumeration, deliberately no adapter permutation helpers.
    tiny = np.array([[[0., 1.], [2., 4.], [1., 0.]], [[2., 2.], [4., 5.], [1., 1.]]])
    def slow_stat(x):
        means = [[sum(x[s, p, i] for s in range(2)) / 2 for i in range(2)] for p in range(3)]
        return sum((means[p][i] - sum(means[q][i] for q in range(3)) / 3) ** 2
                   for p in range(3) for i in range(2))
    observed = slow_stat(tiny)
    null = [slow_stat(np.array([tiny[0, list(a)], tiny[1, list(b)]]))
            for a in itertools.permutations(range(3)) for b in itertools.permutations(range(3))]
    independent_p = sum(v >= observed - 1e-12 for v in null) / 36
    exact = adapter.joint_prompt(tiny)
    check('independent scalar omnibus statistic', np.isclose(exact['statistic'], observed))
    check('independent whole-seed permutation enumeration', exact['randomization']['exact'] and
          exact['randomization']['permutations'] == 36 and np.isclose(exact['randomization']['p_one_sided'], independent_p))
    check('input ordering invariant', adapter.joint_prompt(tiny[:, :, ::-1])['randomization'] == exact['randomization'])
    check('seed ordering invariant exact null', adapter.joint_prompt(tiny[::-1])['randomization'] == exact['randomization'])
    check('constant cube no omnibus significance', adapter.joint_prompt(np.ones((4, 3, 2)), perms=50)['randomization']['p_one_sided'] == 1)
    pure_seed = np.broadcast_to(np.arange(4)[:, None, None], (4, 3, 2))
    check('pure seed cube no prompt significance', adapter.joint_prompt(pure_seed, perms=50)['statistic'] == 0)
    pair = np.stack([np.zeros((4, 2)), np.ones((4, 2))], axis=1)
    check('two-prompt omnibus matches whole-seed signflip',
          adapter.joint_prompt(pair)['randomization']['p_one_sided'] == core.paired_prompt(np.ones((4, 2)), bootstraps=20)['two_sided_sign_flip_p'])
    mc = adapter.joint_prompt(cube, perms=17)['randomization']
    check('Monte Carlo plus-one correction', not mc['exact'] and mc['permutations'] == 17 and
          mc['p_one_sided'] == (mc['exceedances'] + 1) / 18)
    check('Monte Carlo deterministic', adapter.joint_prompt(cube, perms=17)['randomization'] == mc)
    # Explicit state/missingness handling and family retention.
    dm = copy.deepcopy(d)
    dm['outcomes'].append({**copy.deepcopy(d['outcomes'][0]), 'id': 'rest'})
    dm['tests'].append({**copy.deepcopy(d['tests'][0]), 'id': 'rest_joint', 'outcome': 'rest'})
    om = copy.deepcopy(o)
    om += [{**copy.deepcopy(r), 'outcome': 'rest'} for r in o]
    om[-1].update(state='unknown', value=None, reason='ambiguous identity')
    om[-2].update(state='invalid', value=None, reason='cannot track')
    om.pop(-3)
    missing = adapter.analyze(dm, om, bootstraps=20, perms=100)
    rest = missing['cubes'][1]
    check('unknown invalid missing stay distinct', rest['counts'] == {'valid': 21, 'invalid': 1, 'unknown': 1, 'missing': 1})
    check('incomplete cube blocks primary decomposition', not rest['complete'] and 'factorial' not in rest and 'cube' not in rest)
    check('incomplete cube blocks registered test', missing['tests'][2]['raw_p'] is None and missing['tests'][2]['holm_p'] is None)
    check('all registered tests count for Holm', missing['families'][0]['size'] == 3 and missing['families'][0]['not_tested_count'] == 1)
    expected = core.holm([missing['tests'][0]['raw_p'], missing['tests'][1]['raw_p'], 1])
    check('Holm retains missing member at p one', missing['tests'][0]['holm_p'] == expected[0])
    check('missingness factor tables retain counts', all(sum(sum(v[k] for k in ('valid', 'invalid', 'unknown', 'missing'))
          for v in rest['by_factor'][a]) == 24 for a in ('seed', 'prompt', 'input')))
    check('every planned row reported', len(rest['rows']) == 24)
    check('declarations not promoted to runtime proof', result['execution_provenance_declaration']['status'] == 'unverified' and
          all(t['status'] == 'diagnostic_pending_validation_and_provenance_audit' for t in result['tests']))
    reversed_outcomes = adapter.analyze(d, o[::-1], bootstraps=80, perms=2000)
    check('outcome row ordering cannot alter joins or inference', reversed_outcomes == result)
    # Two GPU/stack strata stay separate even with identical numeric seed IDs.
    ds, os = copy.deepcopy(d), copy.deepcopy(o)
    other = copy.deepcopy(ds['strata'][0]); other['id'] = 'gpuB'
    for row in other['runs']: row['run_id'] = 'B-' + row['run_id']
    ds['strata'].append(other)
    os += [{**copy.deepcopy(row), 'run_id': 'B-' + row['run_id'], 'value': 0} for row in o]
    ds['tests'].append({**copy.deepcopy(d['tests'][0]), 'id': 'jointB', 'stratum': 'gpuB', 'family': 'E1_other'})
    separate = adapter.analyze(ds, os, bootstraps=20, perms=100)
    check('GPU strata never pooled', len(separate['cubes']) == 2 and
          all(c['factorial']['n_seeds'] == 4 for c in separate['cubes']))
    check('second GPU has own null and cube', separate['tests'][2]['raw_p'] == 1 and
          np.max(np.abs(separate['cubes'][1]['cube'])) == 0)
    check('registered families adjusted separately', [f['size'] for f in separate['families']] == [2, 1])
    for name, change in [
        ('duplicate planned run rejected', lambda x: x['strata'][0]['runs'].append(copy.deepcopy(x['strata'][0]['runs'][0]))),
        ('missing planned cell rejected', lambda x: x['strata'][0]['runs'].pop()),
        ('extra planned cell rejected', lambda x: x['strata'][0]['runs'][0].update(prompt='extra')),
        ('bad artifact hash rejected', lambda x: x['strata'][0]['runs'][0].update(artifact_sha256='bad')),
        ('duplicate levels rejected', lambda x: x['strata'][0]['levels']['input'].append('a')),
        ('bad contrast rejected', lambda x: x['tests'][1].update(a='not_registered')),
        ('duplicate test ID rejected', lambda x: x['tests'].append(copy.deepcopy(x['tests'][0]))),
        ('mixed experiment rejected', lambda x: x.update(experiment='E1/E2')),
        ('missing method declaration rejected', lambda x: x['outcomes'][0].pop('method')),
    ]:
        changed = copy.deepcopy(d); change(changed); rejects(name, changed, o)
    for name, change in [
        ('duplicate outcome rejected', lambda x: x.append(copy.deepcopy(x[0]))),
        ('extra run outcome rejected', lambda x: x[0].update(run_id='extra')),
        ('extra metric rejected', lambda x: x[0].update(outcome='extra')),
        ('method drift rejected', lambda x: x[0].update(method='different')),
        ('missing evidence rejected', lambda x: x[0].pop('evidence')),
        ('NaN rejected', lambda x: x[0].update(value=float('nan'))),
        ('bool not numeric measurement', lambda x: x[0].update(value=True)),
        ('unknown cannot carry zero value', lambda x: x[0].update(state='unknown', value=0, reason='unknown')),
        ('invalid needs reason', lambda x: x[0].update(state='invalid', value=None)),
    ]:
        changed = copy.deepcopy(o); change(changed); rejects(name, d, changed)
    ranged = copy.deepcopy(d); ranged['outcomes'][0]['value_range'] = [0, 1]
    rejects('registered measurement bounds enforced', ranged, o)
    constants = copy.deepcopy(o)
    for row in constants: row['value'] = 0
    const = adapter.analyze(d, constants, bootstraps=12, perms=20)
    check('constant variance shares stay undefined', all(v is None for v in const['cubes'][0]['factorial']['eta2'].values()))
    dr = copy.deepcopy(d)
    dr['strata'][0]['runs'][1]['artifact_sha256'] = dr['strata'][0]['runs'][0]['artifact_sha256']
    rep = adapter.analyze(dr, o, bootstraps=12, perms=20)
    check('duplicate artifacts are audited not new replication', list(rep['cubes'][0]['repeated_artifact_hashes'].values()) == [2])
    # Real CLI runs at frozen default budgets, using manufactured records only.
    with tempfile.TemporaryDirectory(prefix='t223-factorial-') as td:
        temp = Path(td)
        for name, payload in [('design', d), ('outcomes', o)]:
            (temp / (name + '.json')).write_text(json.dumps(payload))
        for name in ('one', 'two'):
            run = subprocess.run([sys.executable, str(HERE / 'factorial_adapter.py'), str(temp / 'design.json'),
                                  str(temp / 'outcomes.json'), '--out', str(temp / (name + '.json'))],
                                 capture_output=True, text=True)
            check('CLI ' + name + ' exits zero', run.returncode == 0)
        check('CLI byte-identical replay', (temp / 'one.json').read_bytes() == (temp / 'two.json').read_bytes())
        report = json.loads((temp / 'one.json').read_text())
        check('CLI hashes both input files', report['input_sha256'] == {k: hashlib.sha256((temp / (k + '.json')).read_bytes()).hexdigest()
              for k in ('design', 'outcomes')})
    report = {'scope': 'Manufactured arrays and records only; no Cosmos or referee data.',
              'passed_checks': len(checks), 'checks': checks}
    (HERE / 'factorial_synthetic_verification.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'passed_checks': len(checks)}))


if __name__ == '__main__':
    main()
