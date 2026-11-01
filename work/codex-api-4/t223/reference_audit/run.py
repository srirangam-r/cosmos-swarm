"""Retrospective integration audit of public t141 labels, NOT Program N data.

No new clips, labels, physical validation, or source edits. All artifact hashes
below identify canonical LABEL RECORDS, never generation MP4s or noise tensors.
"""
import copy
import csv
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analysis_core as core
import factorial_adapter as adapter

SOURCE_COMMIT = '028723bdbe6060d161be6849b849e965b4fa5dae'
LEVELS = {'seed': list(range(1, 11)), 'prompt': ['F', 'QT', 'N'],
          'input': ['b1dd33', 'b2dd35', 'b2dd37']}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def fraction_ss(cube):
    """Independent exact scalar inclusion-exclusion of conditional cell means."""
    cells = list(itertools.product(*(range(n) for n in cube.shape)))
    vals = {c: Fraction(int(cube[c])) for c in cells}
    names = ['seed', 'prompt', 'input']
    output = {}
    total = sum((v - sum(vals.values()) / len(cells)) ** 2 for v in vals.values())
    for order in range(1, 4):
        for axes in itertools.combinations(range(3), order):
            ss = Fraction(0)
            for c in cells:
                effect = Fraction(0)
                for size in range(order + 1):
                    for subset in itertools.combinations(axes, size):
                        matched = [vals[d] for d in cells if all(d[a] == c[a] for a in subset)]
                        effect += (-1) ** (order - size) * sum(matched) / len(matched)
                ss += effect ** 2
            key = ':'.join(names[a] for a in axes)
            if order == 3:
                key += '_or_residual'
            output[key] = {'ss': str(ss), 'eta2': float(ss / total)}
    return output


def independent_signflip(cube, a, b):
    d = [sum(Fraction(int(cube[s, a, i]) - int(cube[s, b, i]), 3)
             for i in range(3)) for s in range(10)]
    obs = abs(sum(d))
    hits = sum(abs(sum(sign * value for sign, value in zip(signs, d))) >= obs
               for signs in itertools.product((-1, 1), repeat=10))
    return {'mean': float(sum(d) / 10), 'p': hits / 1024}


def main():
    checks = []
    def check(name, yes):
        checks.append({'name': name, 'passed': bool(yes)})
        assert yes, name
    source = HERE / 'source/codes_named.csv'
    rows = list(csv.DictReader(source.open(newline='')))
    runs, outcomes = [], []
    for row in rows:
        m = re.fullmatch(r't141q8_(b1dd33|b2dd35|b2dd37)_(F|QT|N)_s(\d+)', row['name'])
        assert m, row['name']
        image, prompt, seed = m.group(1), m.group(2), int(m.group(3))
        runs.append({'run_id': row['name'], 'seed': seed, 'prompt': prompt, 'input': image,
                     'artifact_sha256': digest(json.dumps(row, sort_keys=True).encode()),
                     'artifact_kind': 'canonical source CSV label record; NOT video/noise'})
        present = row['settle'] in ('0', '1')
        outcome = {'run_id': row['name'], 'outcome': 'rest_eye_code',
                   'state': 'valid' if present else 'unknown',
                   'value': int(row['settle']) if present else None,
                   'method': 't141_frozen_csv@' + digest(source.read_bytes()),
                   'evidence': 'source/codes_named.csv: id=' + row['id']}
        if not present:
            outcome['reason'] = 'Frozen end_state=' + row['end_state'] + '; source settle blank'
        outcomes.append(outcome)
    tests = [{'id': 'joint', 'kind': 'omnibus'}]
    tests += [{'id': a + '_minus_' + b, 'kind': 'contrast', 'a': a, 'b': b}
              for a, b in [('QT', 'F'), ('QT', 'N'), ('N', 'F')]]
    tests = [dict(t, stratum='historical_q8_label_grid', outcome='rest_eye_code',
                  family='retrospective_reference_only') for t in tests]
    design = {'version': 1, 'experiment': 'E2',
              'scope': 'HISTORICAL t141 adapter integration; E2 is schema routing only. NOT raj-noise E2.',
              'provenance': {'status': 'No native execution/noise/video audit; label-record hashes only',
                             'evidence': [SOURCE_COMMIT, 'board4720']},
              'strata': [{'id': 'historical_q8_label_grid', 'levels': LEVELS, 'runs': runs}],
              'outcomes': [{'id': 'rest_eye_code', 'definition': 'Frozen t141 settle column, unchanged',
                            'method': outcomes[0]['method'], 'value_range': [0, 1],
                            'validation': {'status': 'unvalidated eye codes; NOT planted-pass physics',
                                           'evidence': ['source/codes_named.csv']}}], 'tests': tests}
    write(HERE / 'historical_design.json', design)
    write(HERE / 'historical_outcomes.json', outcomes)
    blocked = adapter.analyze(design, outcomes)
    write(HERE / 'blocked_original.json', blocked)
    check('90 unique label records form exact declared grid', len(runs) == len({r['run_id'] for r in runs}) == 90)
    check('89 observed plus one unknown, not missing or zero',
          blocked['cubes'][0]['counts'] == {'valid': 89, 'unknown': 1, 'invalid': 0, 'missing': 0})
    check('full cube primary inference blocked', not blocked['cubes'][0]['complete'] and
          'factorial' not in blocked['cubes'][0] and all(t['raw_p'] is None for t in blocked['tests']))
    check('full four-test registry retained despite block', blocked['families'][0]['size'] == 4 and
          blocked['families'][0]['not_tested_count'] == 4)
    unknown = [j for j, o in enumerate(outcomes) if o['state'] == 'unknown']
    check('exactly one unknown at the published cell', len(unknown) == 1 and
          outcomes[unknown[0]]['run_id'] == 't141q8_b1dd33_F_s1')
    completions = []
    for value in (0, 1):
        hypothetical = copy.deepcopy(outcomes)
        hypothetical[unknown[0]].update(state='valid', value=value,
            reason='HYPOTHETICAL binary completion only; source label remains unknown')
        result = adapter.analyze(design, hypothetical)
        result['scope'] = 'EXPLORATORY exhaustive binary-label sensitivity; NOT measured replacement data'
        write(HERE / f'hypothetical_unknown_{value}.json', result)
        cube = np.asarray(result['cubes'][0]['cube'])
        exact = fraction_ss(cube)
        point = result['cubes'][0]['factorial']
        check(f'completion{value} exact Fraction SS agrees on all seven terms',
              all(abs(point['eta2'][k] - x['eta2']) < 1e-12 for k, x in exact.items()))
        check(f'completion{value} seven shares sum to one', abs(sum(point['eta2'].values()) - 1) < 1e-12)
        for test in result['tests'][1:]:
            independent = independent_signflip(cube, LEVELS['prompt'].index(test['a']),
                                               LEVELS['prompt'].index(test['b']))
            check(f'completion{value} independent exact {test["id"]}',
                  abs(test['raw_p'] - independent['p']) < 1e-12 and
                  abs(test['result']['mean_difference'] - independent['mean']) < 1e-12)
        completions.append({'unknown_value': value, 'eta2': point['eta2'],
            'seed_cluster_bootstrap': point['seed_cluster_bootstrap'], 'tests': result['tests'],
            'exact_fraction_ss': exact})
    source_result = json.loads((HERE / 'source/res_q8_settle.json').read_text())
    summary = {'scope': 'Retrospective same-label software/robustness audit, not a new model finding',
        'source_commit': SOURCE_COMMIT, 'source_labels_sha256': digest(source.read_bytes()),
        'missing_cell': outcomes[unknown[0]]['run_id'],
        'source_imputation': 'source/analyze_grid.py: additive seed+image/prompt-cell fit, 50 iterations',
        'published_imputed_shares': source_result['shares'],
        'original_primary_status': 'blocked:89 valid+1 unknown, all4 tests untested',
        'hypothetical_completions': completions,
        'point_identification_ranges': {k: [min(c['eta2'][k] for c in completions),
                                               max(c['eta2'][k] for c in completions)]
                                       for k in completions[0]['eta2']},
        'warnings': ['No actual raj-noise outputs accessed.',
                     'Ranges enumerate labels only; conditional bootstrap intervals are not a joint coverage guarantee.',
                     'Reference prompt vocabulary and one GAUGE camera setup cannot establish general causality.',
                     'Artifact hashes identify CSV records, not clips, noise tensors or execution provenance.']}
    write(HERE / 'summary.json', summary)
    write(HERE / 'verification.json', {'checks': checks, 'all_passed': all(c['passed'] for c in checks)})
    print(json.dumps({'checks': len(checks), 'ranges': summary['point_identification_ranges'],
        'QT_F': [{k: c['tests'][1][k] for k in ('raw_p', 'holm_p', 'result')} for c in completions]}, indent=2))


if __name__ == '__main__':
    main()
