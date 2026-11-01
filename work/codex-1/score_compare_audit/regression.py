"""Regression fixtures for compare.py; no model or real scores used."""
import json, pathlib, subprocess, sys, tempfile

compare = pathlib.Path('tools/nv_scoreboard/compare.py').resolve()
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d)
    def scores(name, rows):
        result = {}
        for i, (image, seed, score) in enumerate(rows):
            side = p / f'{name}_side_{i}.json'
            side.write_text(json.dumps(dict(image=image, seed=seed, prompt='p', negative_prompt='', num_frames=61, fps=24, steps=35, guidance=6, flow_shift=10, width=832, height=480)))
            result[str(i)] = dict(clip=f'{name}{i}.mp4', sidecar=str(side), dover_fused=score)
        path = p / f'{name}.json'; path.write_text(json.dumps(result)); return str(path)
    def call(*args):
        return subprocess.run([sys.executable, str(compare), *args], capture_output=True, text=True)
    a = scores('a', [('/one/frame.png', 7, 0), ('/two/frame.png', 7, 10)])
    b = scores('b', [('/two/frame.png', 7, 11), ('/one/frame.png', 7, 1)])
    r = call('paired', a, b); assert r.returncode == 0, r.stderr
    m = json.loads(r.stdout)['metrics']['dover_fused']; assert m['delta'] == 1 and m['n_scenes'] == 2 and m['delta_ci95'] == [1, 1]
    dup = scores('dup', [('/one/frame.png', 7, 0), ('/one/frame.png', 7, 2)])
    assert 'duplicate seed' in call('noise', dup).stderr
    assert 'duplicate pairing key' in call('paired', dup, b).stderr
    one = scores('one', [('/one/frame.png', i, 0) for i in range(10)])
    one2 = scores('one2', [('/one/frame.png', i, 1) for i in range(10)])
    m = json.loads(call('paired', one, one2).stdout)['metrics']['dover_fused']; assert m['n_scenes'] == 1 and m['delta_ci95'] == [None, None]
    assert 'unmatched pairing keys' in call('paired', a, one).stderr
    missing = scores('missing', [(None, 7, 0)])
    assert 'missing pairing key' in call('paired', missing, missing).stderr
    noise = scores('noise', [('/one/frame.png', 7, 0), ('/one/frame.png', 8, 2)])
    n = json.loads(call('noise', noise).stdout); assert abs(n['pooled_seed_sd']['dover_fused']['sd'] - 2**0.5) < 1e-12
print('PASS: distinct paths, duplicate seeds/keys, single-scene CI, unmatched/missing keys, valid seed SD')
