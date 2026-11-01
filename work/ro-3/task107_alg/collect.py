"""Copy task-107 clips from srv/out_srv into clips/<job name>.mp4, matched by queue_id (from the queue status output)."""
import json, glob, os, shutil, subprocess, sys
st = subprocess.run([sys.executable, '/home/rohith/workspaces/sclaw/agentic_colab/scripts/cosmos_queue.py', 'status', '--owner', 'ro-3'],
                    capture_output=True, text=True).stdout.split('\n')
qid = {l.split()[0]: l.split()[-1] for l in st if 'restalg' in l}
for js in sorted(glob.glob('../srv/out_srv/*_ro-3.json')):
    d = json.load(open(js)); n = qid.get(d.get('extra_params', {}).get('queue_id'))
    if n and not os.path.exists(f'clips/{n}.mp4'):
        shutil.copy(js[:-5] + '.mp4', f'clips/{n}.mp4'); shutil.copy(js, f'clips/{n}.json'); print('new', n)
