"""Task 266 driver (direct endpoints; the queue cannot upload latent.ref). E=http://host:port,... python3 run_t266.py
Arms: plain, proxy g=9.81 and g=4.905 (wrong-g control) x start_step 8/12/16 x seeds 1-3. 832x480, 189 f, noise.device=cpu."""
import json, os, subprocess, threading, queue as Q
from pathlib import Path
R=Path(__file__).parent; OUT=R/'out'; OUT.mkdir(exist_ok=True)
PROMPT=json.loads(open(R/'../../../tools/cosmos_local/example_jobs_gauge_ball.jsonl').readline())['prompt']
IMG=R/'../../../assets/gauge_ball1_f0.png'
E=[u for u in os.environ['E'].split(',') if u]
jobs=[]
for s in (1,2,3):
    jobs.append((f'plain_s{s}',s,None,0))
    for tag in ('g981','g490'):
        for k in (8,12,16): jobs.append((f'{tag}_k{k}_s{s}',s,tag,k))
def post(url,name,seed,tag,k):
    mp4=OUT/f'{name}.mp4'
    if mp4.exists() and mp4.stat().st_size>1000: return
    ex={'noise':{'device':'cpu'}}; cmd=['curl','-s','-o',str(mp4),'-w','%{http_code}','--max-time','3000','-X','POST',f'{url}/v1/videos/sync',
      '-F',f'prompt={PROMPT}','-F','num_frames=189','-F','fps=24','-F','num_inference_steps=35','-F','guidance_scale=6','-F','flow_shift=10','-F',f'seed={seed}','-F',f'input_reference=@{IMG}']
    if tag:
        ex['latent']={'ref':f'ball_{tag}.mp4','start_step':k,'init':'noised'}
        cmd+=['-F',f'internals_files=@{R}/proxies/ball_{tag}.mp4']
    cmd+=['-F',f'extra_params={json.dumps(ex)}']
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    if c!='200': mp4.unlink(missing_ok=True); print('FAIL',name,c)
    else: (OUT/f'{name}.json').write_text(json.dumps(dict(name=name,seed=seed,proxy=tag,start_step=k,endpoint=url,extra=ex)))
q=Q.Queue(); [q.put(j) for j in jobs]
def w(u):
    while True:
        try: n,s,t,k=q.get_nowait()
        except Q.Empty: return
        post(u,n,s,t,k)
ts=[threading.Thread(target=w,args=(u,)) for u in E]; [t.start() for t in ts]; [t.join() for t in ts]
