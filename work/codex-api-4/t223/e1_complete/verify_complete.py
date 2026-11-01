"""Verify the additive full64 update against the preserved partial snapshot."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify
import factorial_adapter as adapter


def check(root):
    verify.verify(root)
    old_root = HERE.with_name('e1_diagnostic')
    old = json.loads((old_root / 'results.json').read_text())
    new = json.loads((root / 'results.json').read_text())
    assert old['counts']['valid'] == 58
    assert new['counts'] == dict(planned=64, fetched=64, valid=64,
                                complete_seed_clusters=16, queue_status={'done': 64})
    a = {r['run_id']: r for r in old['audits']}
    b = {r['run_id']: r for r in new['audits']}
    assert a.keys() == b.keys() and len(b) == 64
    added = []
    for run_id, row in a.items():
        current = b[run_id]
        assert current['request_contract'] == current['native_contract'] == 'pass'
        assert current['endpoint'] in ('q8-4', 'q8-5', 'q8-6', 'q8-7')
        if row['native_contract'] == 'pass':
            for key in ('clip_sha256', 'native_video', 'image_change', 'endpoint'):
                assert row[key] == current[key], (run_id, key)
        else:
            added.append(current['name'])
    assert len(added) == 6
    primary = new['primary']
    replay = adapter.analyze(json.loads((root/'design.json').read_text()),
                             json.loads((root/'outcomes.json').read_text()))
    assert replay == primary
    sensitivity = new['complete_seed_sensitivity']
    assert primary['cubes'][0]['complete']
    assert primary['cubes'][0] == sensitivity['cubes'][0]
    assert primary['families'][0]['size'] == 3
    assert primary['families'][0]['not_tested_count'] == 0
    for p, s in zip(primary['tests'], sensitivity['tests']):
        for key in ('raw_p', 'holm_p', 'result'):
            assert p[key] == s[key], key
        assert p['raw_p'] is not None and p['holm_p'] is not None
    # Source copies are exact; no retrospective change to metric, uncertainty,
    # selection, tests or the original preregistration.
    sources = ['run.py', 'fetch.py', 'verify.py', 'PREREG.md',
               'owner_E1.jsonl', 'design_only_queue.json']
    for filename in sources:
        assert (HERE / filename).read_bytes() == (old_root / filename).read_bytes()
    result = dict(status='pass', checks=[
        '64 planned IDs, completed native contracts, original endpoint class',
        'all58 earlier video hashes, metadata, measurements and endpoints unchanged',
        'only six originally unfinished cells added',
        'complete primary cube, all three tests and Holm family retained',
        'byte-equivalent primary numerical replay from saved design/outcomes',
        'complete-seed sensitivity now equals primary; do not count as replication',
        'six source/design/prereg files byte-identical to preserved partial package'],
        added_names=sorted(added),
        copied_source_sha256={p: verify.video.sha256(HERE/p) for p in sources},
        original_result_sha256=verify.video.sha256(old_root/'results.json'),
        result_sha256=verify.video.sha256(root/'results.json'),
        scope='software/numerical checks, not planted validation')
    (root/'completion_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    check(Path(sys.argv[1]) if len(sys.argv)>1 else HERE)
