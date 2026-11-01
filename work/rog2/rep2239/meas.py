import cv2, numpy as np, glob, os, json, collections, sys
def load(p):
    cap=cv2.VideoCapture(p); F=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        F.append(cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2RGB),(416,240),interpolation=cv2.INTER_AREA).astype(np.float32))
    return np.stack(F)[:93]
# ROIs in 416x240 coords (frame 832x480 -> /2)
ROIS={'corr':(115,75,180,210),'wide':(80,60,230,240),'full':(0,0,416,240)}  # x0,y0,x1,y1
res={}
for p in sorted(glob.glob('clips/*.mp4')):
    G=load(p); d=np.abs(np.diff(G,axis=0)).mean(axis=3)  # T-1,H,W
    k=os.path.basename(p)[:-4]; r={}
    for n,(x0,y0,x1,y1) in ROIS.items():
        m=d[:,y0:y1,x0:x1].mean(axis=(1,2))
        e=m[4:36].mean(); l=m[56:88].mean(); r[n]=dict(early=float(e),late=float(l),D=float(l/(e+1e-9)))
    res[k]=r
json.dump(res,open('res.json','w'),indent=1)
arms=collections.defaultdict(dict)
for k,v in res.items():
    inp,arm,s=k.split('_'); arms[arm][(inp,s)]=v
for roi in ROIS:
  print('ROI',roi)
  for q in ['D','late','early']:
    for arm in ['base','fast05','tall05','fast2']:
        d=arms[arm]; vals=np.array([d[x][roi][q] for x in sorted(d)])
        s=f'  {q:5s} {arm:7s} {vals.mean():6.2f}±{vals.std(ddof=1)/np.sqrt(len(vals)):.2f}'
        if arm!='base':
            pr=np.array([d[x][roi][q]-arms['base'][x][roi][q] for x in sorted(d)])
            s+=f'  Δ {pr.mean():+.2f}±{pr.std(ddof=1)/np.sqrt(len(pr)):.2f} neg {int((pr<0).sum())}/{len(pr)}'
        print(s)
print({a:len(arms[a]) for a in arms})
# per-clip D for fast05 vs base
for x in sorted(arms['base']): print(x, 'base %.2f fast05 %.2f tall05 %.2f fast2 %.2f'%tuple(arms[a][x]['corr']['D'] for a in ['base','fast05','tall05','fast2']))
