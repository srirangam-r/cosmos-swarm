"""Exercise seed-noise context grouping using fabricated scores."""
import json
import pathlib
import subprocess
import sys
import tempfile

compare = pathlib.Path('tools/nv_scoreboard/compare.py').resolve()
base = dict(image='frame', prompt='p', negative_prompt=None, num_frames=93,
            fps=24, steps=35, guidance=6, flow_shift=10, width=832, height=480)
with tempfile.TemporaryDirectory() as tmp:
    path = pathlib.Path(tmp) / 'scores.json'
    def run(metas):
        path.write_text(json.dumps({str(i): dict(clip=f'{i}.mp4', metadata=dict(base, seed=i, **m), dover_fused=i)
                                    for i, m in enumerate(metas)}))
        return subprocess.run([sys.executable, str(compare), 'noise', str(path)], capture_output=True, text=True)

    # Two seeds in each identical context; baseline and changed template/model must not mix.
    r = run([{'model':'A', 'extra_params':{'use_duration_template':True}},
             {'model':'A', 'use_duration_template':True},
             {'model':'A', 'use_duration_template':False},
             {'model':'A', 'use_duration_template':False},
             {'model':'B', 'use_duration_template':True},
             {'model':'B', 'use_duration_template':True}, {}, {}])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out['n_groups'] == 4 and all(g['n'] == 2 for g in out['groups'])
    assert all('checkpoint' in g['unknown_context'] for g in out['groups'])
    assert any('model' in g['unknown_context'] for g in out['groups'])
    r = run([{'use_duration_template':True, 'extra_params':{'use_duration_template':False}}])
    assert r.returncode != 0 and 'conflicting use_duration_template' in r.stderr
    r = run([{'model':None}, {}])
    assert json.loads(r.stdout)['n_groups'] == 2
print('PASS: recorded model/templates partitioned; unknown and explicit null distinguished; conflict rejected')
