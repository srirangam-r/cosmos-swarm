"""Task 139 readout helper: fetch clips, run firstfall (planted PASS) seeded on the ball, make eye-coding strips.
Usage: python3 an139.py <workdir>   (clips -> <workdir>/clips, strips -> <workdir>/strips, firstfall json -> <workdir>/ff)"""
import sys, os, glob, json, subprocess, cv2, numpy as np
W=sys.argv[1]; Q='/home/nail/swarm/agentic_colab/scripts/cosmos_queue.py'
REPO=os.path.dirname(os.path.abspath(__file__))+'/../../..'
subprocess.run(['python3',Q,'fetch','--owner','raj-opus-1','--out',f'{W}/clips'],capture_output=True)
def frames(p):
    c=cv2.VideoCapture(p); F=[]
    while True:
        ok,f=c.read()
        if not ok: break
        F.append(f)
    return F
res={}
for p in sorted(glob.glob(f'{W}/clips/t139_*.mp4')):
    n=os.path.basename(p)[:-4]; F=frames(p)
    if len(F)<90: continue
    ffj=f'{W}/ff/{n}.json'
    if not os.path.exists(ffj):
        r=subprocess.run(['python3','-I',f'{REPO}/tools/realball/firstfall.py',p,'--fps','24','--ppm','539.8','--point','280,116','--tmax','92','--qc',f'{W}/ff/{n}_qc.png'],capture_output=True,text=True)
        try: json.loads(r.stdout); open(ffj,'w').write(r.stdout)
        except Exception: open(ffj,'w').write(json.dumps({'error':r.stderr[-500:]}))
    d=json.load(open(ffj)); res[n]={k:d.get(k) for k in ('flag','motion_frame','impact_frame','fall_px','fall_time_s','g','r2','d_growth')}
    # corridor strip: f0-40 every frame, then every 4th
    idx=list(range(0,41))+list(range(44,len(F),4))
    th=[]
    for i in idx:
        c=cv2.resize(F[i][60:420,180:380],(100,180)); cv2.putText(c,str(i),(2,12),0,0.4,(0,255,255),1); th.append(c)
    while len(th)%9: th.append(np.zeros_like(th[0]))
    rows=[np.hstack(th[k:k+9]) for k in range(0,len(th),9)]
    cv2.imwrite(f'{W}/strips/{n}_corr.jpg',np.vstack(rows))
    full=[cv2.resize(F[i],(277,160)) for i in range(0,len(F),8)]
    for i,f in zip(range(0,len(F),8),full): cv2.putText(f,str(i),(3,14),0,0.45,(0,255,255),1)
    while len(full)%4: full.append(np.zeros_like(full[0]))
    cv2.imwrite(f'{W}/strips/{n}_full.jpg',np.vstack([np.hstack(full[k:k+4]) for k in range(0,len(full),4)]))
json.dump(res,open(f'{W}/ff_summary.json','w'),indent=1)
for n,v in res.items(): print(n,v)
