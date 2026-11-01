# fetch queue clips, then download capture artifacts from the endpoint that ran each job
import json, glob, os, subprocess, sys, urllib.request
Q='/home/nail/swarm/agentic_colab/scripts/cosmos_queue.py'
out=sys.argv[1] if len(sys.argv)>1 else 'clips'
subprocess.run(['python3',Q,'fetch','--owner','raj-opus-1','--out',out])
st=subprocess.run(['python3',Q,'status'],capture_output=True,text=True).stdout
EP={l.split()[1]:l.split()[-1] for l in st.splitlines() if l.startswith('endpoint')}
os.makedirs('acts',exist_ok=True)
for sc in sorted(glob.glob(f'{out}/t128cap_*.json')):
    j=json.load(open(sc)); n=os.path.basename(sc)[:-5]
    dst=f'acts/{n}.npz'
    if os.path.exists(dst): continue
    ids=j.get('artifact_ids') or []
    ep=j.get('endpoint') or j.get('queue',{}).get('endpoint')
    url=EP.get(ep, ep)
    if not ids or not url: print('missing',n,ids,ep); continue
    urllib.request.urlretrieve(f'{url}/v1/artifacts/{ids[0]}',dst); print('got',n,ep,ids[0])
