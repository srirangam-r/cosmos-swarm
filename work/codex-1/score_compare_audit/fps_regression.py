import json, os, pathlib, subprocess, sys, tempfile
root = pathlib.Path.cwd()
score = root / 'tools/nv_scoreboard/score.py'
compare = root / 'tools/nv_scoreboard/compare.py'
source = json.loads((root / 'work/raj-1/gauge_ball/gauge_ball1_noneg_s1.json').read_text())
with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td)
    (p/'torch.py').write_text('def manual_seed(x): pass\n')
    (p/'av.py').write_text('class Stream:\n average_rate=24\n guessed_rate=24\nclass Streams:\n video=[Stream()]\nclass Container:\n streams=Streams()\n def close(self): pass\ndef open(path): return Container()\n')
    (p/'clip.mp4').touch()
    meta = dict(source, fps=12, cond_fps=12, play_fps=24)
    (p/'clip.json').write_text(json.dumps(meta))
    env = dict(os.environ, PYTHONPATH=str(p))
    out = p/'scores.json'
    r = subprocess.run([sys.executable, str(score), str(p/'clip.mp4'), '--out', str(out), '--no_dd', '--no_dover'], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    result = json.loads(out.read_text())['clip.mp4']
    assert result['fps'] == 24 and result['fps_source'] == 'container'
    meta['play_fps'] = 12
    (p/'clip.json').write_text(json.dumps(meta))
    r = subprocess.run([sys.executable, str(score), str(p/'clip.mp4'), '--out', str(out), '--no_dd', '--no_dover'], capture_output=True, text=True, env=env)
    assert r.returncode != 0 and 'does not match container' in r.stderr
    rows = {}
    for seed, cond, play in [(1,12,24),(2,12,24),(1,12,12),(2,12,12),(1,24,24),(2,24,24)]:
        m=dict(source, seed=seed, fps=12, cond_fps=cond, play_fps=play)
        rows[f'{seed}_{cond}_{play}']=dict(clip='ball.mp4', metadata=m, fps=play, fps_source='container', dd_norm=float(seed))
    scores=p/'groups.json'; scores.write_text(json.dumps(rows))
    r=subprocess.run([sys.executable,str(compare),'noise',str(scores)],capture_output=True,text=True)
    assert r.returncode == 0, r.stderr
    groups=json.loads(r.stdout)['groups']
    assert len(groups)==3 and all(x['n']==2 for x in groups), groups
    print('PASS: container 24 fps with conditioning 12, declared playback mismatch rejected, three independent fps groups')
