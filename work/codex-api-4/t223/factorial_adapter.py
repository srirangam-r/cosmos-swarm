"""Strict E1/E2 joins and prespecified prompt tests. No network or clip access."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

import numpy as np
import analysis_core as core


def unique(rows, name):
    if not isinstance(rows, list) or not rows or len(set(rows)) != len(rows):
        raise ValueError('Require nonempty unique ' + name)
    return rows


def joint_statistic(values):
    x = core.array(values, 3)
    cells = x.mean(axis=0)
    return float(np.sum((cells - cells.mean(axis=0, keepdims=True)) ** 2))


def joint_prompt(values, perms=core.PERMUTATIONS):
    x = core.array(values, 3)
    ns, nprompt, ni = x.shape
    if ns < 2 or nprompt < 2 or perms < 1:
        raise ValueError('At least two seeds/prompts and positive permutation budget required')
    observed = joint_statistic(x)
    count = math.factorial(nprompt) ** ns
    exact = count <= perms
    rng = np.random.default_rng(20261102)
    if exact:
        sequences = itertools.product(itertools.permutations(range(nprompt)), repeat=ns)
    else:
        sequences = ([rng.permutation(nprompt) for _ in range(ns)] for _ in range(perms))
    def statistics():
        for seq in sequences:
            # One permutation for all inputs within a seed; no clipwise shuffle.
            yield joint_statistic(np.stack([x[s, list(seq[s]), :] for s in range(ns)]))
    return {'statistic': observed, 'n_seeds': ns, 'n_prompts': nprompt,
            'n_inputs': ni, 'randomization': core.randomization_p(observed, statistics(), exact),
            'null': 'Prompt labels exchangeable within each seed, shared over inputs.',
            'scope': 'Consistent prompt differences within inputs; not all seed:prompt effects.'}


def validate_design(design):
    if design.get('version') != 1 or design.get('experiment') not in ('E1', 'E2'):
        raise ValueError('Require version 1, one E1 or E2 experiment')
    if not isinstance(design.get('provenance'), dict):
        raise ValueError('Require explicit provenance declaration')
    strata = unique([s['id'] for s in design['strata']], 'strata')
    outcome_ids = unique([o['id'] for o in design['outcomes']], 'outcomes')
    for out in design['outcomes']:
        if not all(out.get(k) for k in ('definition', 'method', 'validation')):
            raise ValueError('Outcome definition/method/validation declaration required')
        if 'value_range' in out:
            bounds = core.array(out['value_range'], 1)
            if len(bounds) != 2 or bounds[0] > bounds[1]:
                raise ValueError('Invalid value_range')
    all_runs = {}
    for stratum in design['strata']:
        levels = stratum['levels']
        for axis in ('seed', 'prompt', 'input'):
            unique(levels[axis], axis)
        if len(levels['seed']) < 2 or len(levels['prompt']) < 2:
            raise ValueError('Need at least two seeds/prompts per stratum')
        if any(type(v) is not int for v in levels['seed']):
            raise ValueError('Seed IDs must be integers')
        if any(not isinstance(v, str) or not v for a in ('prompt', 'input') for v in levels[a]):
            raise ValueError('Prompt/input IDs must be nonempty strings')
        planned = set(itertools.product(*(levels[a] for a in ('seed', 'prompt', 'input'))))
        observed = set()
        for run in stratum['runs']:
            rid = run['run_id']
            cell = tuple(run[a] for a in ('seed', 'prompt', 'input'))
            if not isinstance(rid, str) or not rid or rid in all_runs or cell in observed or cell not in planned:
                raise ValueError('Duplicate/extra run or cell')
            if not re.fullmatch('[0-9a-f]{64}', run.get('artifact_sha256', '')):
                raise ValueError('Require artifact SHA256 for each planned run')
            all_runs[rid] = (stratum['id'], run)
            observed.add(cell)
        if observed != planned:
            raise ValueError('Incomplete planned factorial grid')
    test_ids = [t['id'] for t in design['tests']]
    if len(set(test_ids)) != len(test_ids):
        raise ValueError('Duplicate test ID')
    stratum_map = {s['id']: s for s in design['strata']}
    for test in design['tests']:
        if test['stratum'] not in strata or test['outcome'] not in outcome_ids or not test.get('family'):
            raise ValueError('Unregistered test target or family')
        if test['kind'] not in ('omnibus', 'contrast'):
            raise ValueError('Unknown test kind')
        if test['kind'] == 'contrast':
            prompts = stratum_map[test['stratum']]['levels']['prompt']
            if test['a'] == test['b'] or any(test[k] not in prompts for k in ('a', 'b')):
                raise ValueError('Contrast requires different registered prompt IDs')
    return all_runs


def analyze(design, outcomes, bootstraps=core.BOOTSTRAPS, perms=core.PERMUTATIONS):
    runs = validate_design(design)
    registry = {o['id']: o for o in design['outcomes']}
    records = {}
    if not isinstance(outcomes, list):
        raise ValueError('Outcomes must be a list')
    for row in outcomes:
        key = (row['run_id'], row['outcome'])
        if key in records or key[0] not in runs or key[1] not in registry:
            raise ValueError('Duplicate/extra outcome key')
        spec = registry[key[1]]
        if row.get('method') != spec['method'] or not row.get('evidence'):
            raise ValueError('Outcome method mismatch or missing evidence')
        state = row.get('state')
        value = row.get('value')
        if state == 'valid':
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('Valid outcomes require finite numeric values')
            if 'value_range' in spec and not spec['value_range'][0] <= value <= spec['value_range'][1]:
                raise ValueError('Outcome outside registered range')
        elif state in ('invalid', 'unknown'):
            if value is not None or not row.get('reason'):
                raise ValueError('Invalid/unknown outcomes require null value and reason')
        else:
            raise ValueError('Unknown outcome state')
        records[key] = row
    cubes = {}
    reports = []
    for stratum in design['strata']:
        levels = stratum['levels']
        indices = {a: {v: j for j, v in enumerate(levels[a])} for a in levels}
        shape = tuple(len(levels[a]) for a in ('seed', 'prompt', 'input'))
        hashes = Counter(r['artifact_sha256'] for r in stratum['runs'])
        for oid, spec in registry.items():
            cube = np.full(shape, np.nan)
            rows = []
            for run in stratum['runs']:
                record = records.get((run['run_id'], oid))
                state = record['state'] if record else 'missing'
                reason = record.get('reason') if record else 'No submitted outcome record'
                rows.append({**{a: run[a] for a in ('run_id', 'seed', 'prompt', 'input')},
                             'state': state, 'reason': reason,
                             'value': record['value'] if record else None,
                             'evidence': record.get('evidence') if record else None})
                if state == 'valid':
                    cube[tuple(indices[a][run[a]] for a in ('seed', 'prompt', 'input'))] = record['value']
            states = ('valid', 'invalid', 'unknown', 'missing')
            def counts(subset):
                return {state: sum(r['state'] == state for r in subset) for state in states}
            complete = bool(np.isfinite(cube).all())
            report = {'stratum': stratum['id'], 'outcome': oid, 'levels': levels,
                      'complete': complete, 'planned_cells': len(rows), 'counts': counts(rows),
                      'by_factor': {a: [{'level': v, **counts([r for r in rows if r[a] == v])}
                                        for v in levels[a]] for a in ('seed', 'prompt', 'input')},
                      'rows': rows, 'method_declaration': spec,
                      'repeated_artifact_hashes': {k: n for k, n in hashes.items() if n > 1},
                      'audit_status': 'Source validation and live provenance not independently cleared by this runner.'}
            if complete:
                cubes[(stratum['id'], oid)] = cube
                report['cube'] = cube.tolist()
                report['factorial'] = core.factorial(cube, bootstraps=bootstraps)
            else:
                report['blocked_reason'] = 'Incomplete valid cube: no primary inference, imputation or silent exclusion.'
            reports.append(report)
    tests = []
    for spec in design['tests']:
        test = {**spec, 'raw_p': None, 'holm_p': None, 'status': 'not_tested_incomplete_cube'}
        cube = cubes.get((spec['stratum'], spec['outcome']))
        if cube is not None:
            if spec['kind'] == 'omnibus':
                result = joint_prompt(cube, perms=perms)
                p = result['randomization']['p_one_sided']
            else:
                levels = next(s['levels'] for s in design['strata'] if s['id'] == spec['stratum'])
                result = core.paired_prompt(cube[:, levels['prompt'].index(spec['a']), :] -
                                            cube[:, levels['prompt'].index(spec['b']), :],
                                            bootstraps=bootstraps, perms=perms)
                p = result['two_sided_sign_flip_p']
            test.update(result=result, raw_p=p, status='diagnostic_pending_validation_and_provenance_audit')
        tests.append(test)
    families = []
    for family in dict.fromkeys(t['family'] for t in tests):
        members = [t for t in tests if t['family'] == family]
        adjusted = core.holm([t['raw_p'] if t['raw_p'] is not None else 1. for t in members])
        for test, p in zip(members, adjusted):
            if test['raw_p'] is not None:
                test['holm_p'] = p
        families.append({'id': family, 'registered_members': [t['id'] for t in members],
                         'size': len(members), 'not_tested_count': sum(t['raw_p'] is None for t in members),
                         'adjustment': 'Holm, untested members retained at p=1; untested null not accepted.'})
    return {'experiment': design['experiment'], 'protocol_version': 1, 'adapter_addendum': 'board4670',
            'execution_provenance_declaration': design['provenance'],
            'method': 'Descriptive outcome-cube analysis; declarations are not independently audited evidence.',
            'cubes': reports, 'tests': tests, 'families': families,
            'software_settings': {'bootstraps': bootstraps, 'permutations': perms}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('design'); parser.add_argument('outcomes'); parser.add_argument('--out', required=True)
    args = parser.parse_args()
    paths = [Path(args.design), Path(args.outcomes)]
    payloads = [json.loads(p.read_text()) for p in paths]
    result = analyze(*payloads)
    result['input_sha256'] = {k: hashlib.sha256(p.read_bytes()).hexdigest()
                              for k, p in zip(('design', 'outcomes'), paths)}
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
