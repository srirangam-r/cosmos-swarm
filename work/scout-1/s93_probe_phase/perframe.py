import json,glob,os,sys
import numpy as np
root=sys.argv[1]
files=sorted(set(glob.glob(root+'/work/raj-api-3/t48/out_ctrl/*.json')))
print(f"{'clip':34s} {'meanD':>8s} | pos-aligned D (rev pos i - fwd pos i): L0  L1  L2..L21  L22 L23 | content-aligned (rev 23-i - fwd i): c0 c1 mid c22 c23")
for f in files:
    d=json.load(open(f)); rows=d['rows']
    F={};R={}
    for r in rows:
        k=(r['sigma'],r['seed'])
        if r['variant']=='forward':F[k]=np.array(r['per_frame'])
        if r['variant']=='reverse':R[k]=np.array(r['per_frame'])
    keys=sorted(F)
    pos=np.array([R[k]-F[k] for k in keys])          # 12 x 24
    con=np.array([R[k][::-1]-F[k] for k in keys])    # content aligned approx
    fm=np.array([F[k] for k in keys]).mean(0); rm=np.array([R[k] for k in keys]).mean(0)
    pm=pos.mean(0); cm=con.mean(0)
    n=pm.size
    name=os.path.basename(f).replace('.json','')
    print(f"{name:34s} {pm.mean():+.4f} | {pm[0]:+.3f} {pm[1]:+.3f} {pm[2:n-2].mean():+.4f} {pm[n-2]:+.3f} {pm[n-1]:+.3f} | {cm[0]:+.3f} {cm[1]:+.3f} {cm[2:n-2].mean():+.4f} {cm[n-2]:+.3f} {cm[n-1]:+.3f}  n={n}")
