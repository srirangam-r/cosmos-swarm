"""Fetch only the pre-frozen E1 run IDs, without generating model clips."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
BASE = 'http://100.111.167.68:8030'


def fetch(root):
    rows = json.loads((HERE / 'design_only_queue.json').read_text())['runs']
    root.mkdir(parents=True, exist_ok=True)

    def one(row):
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
    fetch(ap.parse_args().out)
