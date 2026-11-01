"""Retrospective rest-ranking and tie-sensitivity diagnostic; NOT actual E3.

Design fixed in task223 board #4781. Source CSV is never modified.
"""
import csv
from fractions import Fraction as Q
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

SEEDS = list(range(1, 11))
INPUTS = ['b1dd33', 'b2dd35', 'b2dd37']
PROMPTS = ['F', 'QT', 'N']


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def exact_banks(training, heldout):
    """Independent rational enumeration, with no NumPy/core ranking calls."""
    k = 3
    scores = {s: sum(training[s], Q(0)) / len(training[s]) for s in SEEDS}
    order = sorted(SEEDS, key=lambda s: (-scores[s], s))
    chosen = order[:k]
    cutoff = scores[chosen[-1]]
    mandatory = {s for s in SEEDS if scores[s] > cutoff}
    boundary = [s for s in SEEDS if scores[s] == cutoff]
    admissible = [tuple(sorted(mandatory | set(c))) for c in
                  itertools.combinations(boundary, k - len(mandatory))]
    pool = sum(heldout.values(), Q(0)) / 10
    def lift(bank):
        return sum((heldout[s] for s in bank), Q(0)) / k - pool
    null = [lift(bank) for bank in itertools.combinations(SEEDS, k)]
    def pval(value):
        return Q(sum(x >= value for x in null), len(null))
    effects = [lift(bank) for bank in admissible]
    return {'top_seed_ids': chosen, 'training_score_by_seed': {str(s): float(scores[s]) for s in SEEDS},
            'top_test_mean': float(lift(chosen) + pool), 'random_pool_expected_mean': float(pool),
            'top_minus_random_pool': float(lift(chosen)),
            'random_bank_p_one_sided': float(pval(lift(chosen))),
            'random_bank_count': len(null), 'boundary_score': float(cutoff),
            'boundary_seed_ids': boundary, 'mandatory_seed_ids': sorted(mandatory),
            'tie_compatible_bank_count': len(admissible),
            'tie_compatible_lift_range': [float(min(effects)), float(max(effects))],
            'tie_compatible_p_range': [float(min(map(pval, effects))), float(max(map(pval, effects)))],
            'tie_compatible_banks': [{'seeds': list(bank), 'lift': float(lift(bank)),
                                    'p_one_sided': float(pval(lift(bank)))} for bank in admissible]}


def main():
    checks = []
    def check(name, value):
        checks.append({'name': name, 'passed': bool(value)})
        assert value, name
    source = HERE.parent / 'reference_audit/source/codes_named.csv'
    before = source.read_bytes()
    rows = list(csv.DictReader(before.decode().splitlines()))
    data = {}
    unknown = []
    for row in rows:
        m = re.fullmatch(r't141q8_(b1dd33|b2dd35|b2dd37)_(F|QT|N)_s(\d+)', row['name'])
        assert m, row['name']
        key = (int(m[3]), m[2], m[1])
        assert key not in data
        data[key] = int(row['settle']) if row['settle'] in ('0', '1') else None
        if data[key] is None:
            unknown.append((key, row['name']))
    check('complete_planned_90_label_grid', set(data) == set(itertools.product(SEEDS, PROMPTS, INPUTS)))
    check('single_frozen_unknown', len(unknown) == 1 and unknown[0][1] == 't141q8_b1dd33_F_s1')
    results = []
    for completion in (0, 1):
        complete = dict(data)
        complete[unknown[0][0]] = completion
        for prompt, excluded in itertools.product(PROMPTS, INPUTS):
            train_inputs = [i for i in INPUTS if i != excluded]
            train = {s: [Q(complete[s, prompt, i]) for i in train_inputs] for s in SEEDS}
            held = {s: Q(complete[s, prompt, excluded]) for s in SEEDS}
            scalar = exact_banks(train, held)
            numeric = core.seedbank([[float(v) for v in train[s]] for s in SEEDS],
                                    [[float(held[s])] for s in SEEDS], SEEDS, [excluded])
            name = f'unknown{completion}/{prompt}/heldout{excluded}'
            check(name + '/scalar_core_point_match', all(
                np.isclose(scalar[k], numeric[k]) for k in
                ['top_test_mean', 'random_pool_expected_mean', 'top_minus_random_pool']))
            check(name + '/training_only_bank_match', scalar['top_seed_ids'] == numeric['top_seed_ids'])
            # Deliberately reverse every held-out label. Selection must be unchanged.
            changed_top, _, _ = core.banks(np.asarray([[float(v) for v in train[s]] for s in SEEDS]), SEEDS)
            reverse = exact_banks(train, {s: 1 - held[s] for s in SEEDS})
            check(name + '/heldout_label_reversal_never_changes_selection',
                  scalar['top_seed_ids'] == reverse['top_seed_ids'] == [SEEDS[j] for j in changed_top])
            check(name + '/all_selected_banks_respect_training_cutoff', all(
                len(b['seeds']) == 3 and len(set(b['seeds'])) == 3 and
                set(scalar['mandatory_seed_ids']).issubset(b['seeds']) and
                all(s in scalar['mandatory_seed_ids'] + scalar['boundary_seed_ids'] for s in b['seeds'])
                for b in scalar['tie_compatible_banks']))
            results.append({'scope': 'hypothetical_unknown_completion; rest-only historical diagnostic',
                            'unknown_completion': completion, 'prompt': prompt,
                            'training_inputs': train_inputs, 'heldout_input': excluded,
                            'independent_exact': scalar, 'frozen_core': numeric,
                            'interval_status': 'descriptive_underpowered: only one held-out input'})
    check('source_bytes_unchanged_and_original_unknown_retained', source.read_bytes() == before and
          data[unknown[0][0]] is None)
    # Named fault controls: a test-only winner does not enter a tied training bank;
    # training-constant and test-constant outcomes have no inferential ranking signal.
    tied = {s: [Q(0), Q(0)] for s in SEEDS}
    fault = exact_banks(tied, {s: Q(s == 10) for s in SEEDS})
    check('heldout_only_winner_is_not_selected', fault['top_seed_ids'] == [1, 2, 3] and fault['top_minus_random_pool'] == -0.1)
    flat = exact_banks(tied, {s: Q(1) for s in SEEDS})
    check('constant_outcome_null', flat['tie_compatible_lift_range'] == [0.0, 0.0] and flat['random_bank_p_one_sided'] == 1)
    check('all_tied_training_enumerates_all120_banks', flat['tie_compatible_bank_count'] == 120)
    report = {'scope': 'Retrospective t141 E3 reference diagnostic; NOT actual raj-noise E3',
              'design_board_id': 4781, 'source_sha256': hashlib.sha256(before).hexdigest(),
              'source_commit': '028723bdbe6060d161be6849b849e965b4fa5dae',
              'primary_original_status': 'blocked_unknown_label; only hypothetical completions evaluated',
              'measurement_status': 'unvalidated eye-coded rest; no release/identity/quality safeguard',
              'multiple_testing': '18 retrospective unadjusted p-values; no confirmatory hypothesis claim',
              'randomization': 'exact120 random subsets, equivalent to full seed-map permutation for fixed top3',
              'results': results}
    write('results.json', report)
    write('verification.json', {'checks': checks, 'passed': len(checks), 'software_checks_only': True})
    for result in results:
        r = result['independent_exact']
        print(result['unknown_completion'], result['prompt'], result['heldout_input'],
              'top', r['top_seed_ids'], 'lift', round(r['top_minus_random_pool'], 6),
              'p', round(r['random_bank_p_one_sided'], 6),
              'tie_banks', r['tie_compatible_bank_count'], 'range', r['tie_compatible_lift_range'])
    print('Checks passed:', len(checks))


if __name__ == '__main__':
    main()
