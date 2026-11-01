import json, os, pathlib, subprocess, sys, tempfile
root = pathlib.Path.cwd()
compare = root / 'tools/nv_scoreboard/compare.py'
score = root / 'tools/nv_scoreboard/score.py'
source = json.loads((root / 'work/raj-1/gauge_ball/gauge_ball1_noneg_s1.json').read_text())
def call(args, env=None):
    return subprocess.run([sys.executable, *map(str,args)], capture_output=True, text=True, env=env)
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d)
    rows = {}
    for seed in (1, 2):
        meta = dict(source, seed=seed)
        rows[str(seed)] = dict(clip=f'ball_{seed}.mp4', sidecar='/unavailable.json', metadata=meta, dover_fused=float(seed))
    scores = p/'scores.json'; scores.write_text(json.dumps(rows))
    result = call([compare,'noise',scores,'--real',root/'work/raj-4/nv_scoreboard_real/gauge_real_matched.json'])
    assert result.returncode == 0, result.stderr
    rep = json.loads(result.stdout)
    assert rep['n_groups'] == 1 and rep['groups'][0]['n'] == 2 and len(rep['real_reference']) == 3
    rows['2']['metadata']['negative_prompt_text'] = ''
    scores.write_text(json.dumps(rows))
    rep = json.loads(call([compare,'noise',scores]).stdout)
    assert rep['n_groups'] == 2
    for item in rows.values():
        item['metadata'].pop('negative_prompt_text'); item['metadata'].pop('negative_prompt')
    scores.write_text(json.dumps(rows))
    assert 'missing image' in call([compare,'noise',scores]).stderr
    # Fake torch only: no actual scoring is performed in this I/O integration test.
    (p/'torch.py').write_text('def manual_seed(x): pass\n')
    (p/'av.py').write_text('class Stream:\n average_rate=24\n guessed_rate=24\nclass Streams:\n video=[Stream()]\nclass Container:\n streams=Streams()\n def close(self): pass\ndef open(path): return Container()\n')
    env=dict(os.environ, PYTHONPATH=str(p))
    for folder in ('a','b'):
        (p/folder).mkdir(); (p/folder/'same.mp4').touch()
        (p/folder/'same.json').write_text(json.dumps(source))
    out=p/'out.json'
    r=call([score,p/'a/same.mp4',p/'b/same.mp4','--out',out,'--no_dd','--no_dover'],env)
    assert r.returncode != 0 and 'duplicate clip basename' in r.stderr and not out.exists(), r.stderr
    r=call([score,p/'a/same.mp4','--out',out,'--no_dd','--no_dover'],env)
    assert r.returncode == 0, r.stderr
    saved=json.loads(out.read_text()); assert saved['same.mp4']['metadata'] == source
    r=call([score,p/'b/same.mp4','--out',out,'--no_dd','--no_dover'],env)
    assert r.returncode != 0 and 'duplicate clip basename' in r.stderr
    print('PASS: real sidecar null, embedded portability, null vs empty/missing, real reference, batch and existing-output collisions')
