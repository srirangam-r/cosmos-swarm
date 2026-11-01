"""Fetch only the pre-frozen E2 run IDs, without generating model clips."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
BASE = 'http://100.111.167.68:8030'


def fetch(root, frozen=False):
    rows = json.loads((HERE / 'design_only_queue.json').read_text())['runs']
    root.mkdir(parents=True, exist_ok=True)
    recorded = ({r['id']: r for r in json.loads((HERE/'queue_records.json').read_text())}
                if frozen else None)

    def one(row):
        if frozen:
            actual = recorded[row['id']]
        else:
            with urlopen(BASE + '/jobs/' + row['id'], timeout=30) as stream:
                actual = json.load(stream)
        assert actual['id'] == row['id'] and actual['name'] == row['name']
        assert actual['owner'] == row['owner']
        for key in ('prompt', 'image', 'params', 'endpoints'):
            assert actual.get(key) == row.get(key), (row['name'], key)
        if row['endpoint'] is not None:
            assert actual['endpoint'] == row['endpoint']
        if actual.get('endpoint') is not None:
            assert actual['endpoint'] in row['endpoints']
        (root / (row['name'] + '.queue.json')).write_text(json.dumps(actual, indent=2) + '\n')
        if actual['status'] == 'done':
            path = root / (row['name'] + '.mp4')
            if not path.exists():
                with urlopen(BASE + '/jobs/' + row['id'] + '/mp4', timeout=120) as stream:
                    data = stream.read()
                path.write_bytes(data)
        return actual['status']

    from collections import Counter
    with ThreadPoolExecutor(max_workers=4) as pool:
        counts = Counter(pool.map(one, rows))
    print(dict(counts), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out', type=Path)
    ap.add_argument('--frozen', action='store_true', help='Replay saved queue snapshot, fetching only its finished MP4s')
    args = ap.parse_args()
    fetch(args.out, args.frozen)
