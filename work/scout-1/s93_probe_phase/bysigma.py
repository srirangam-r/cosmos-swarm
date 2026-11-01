import json,glob,os,sys
import numpy as np
root=sys.argv[1]
files=sorted(glob.glob(root+'/work/raj-api-3/t48/out_ctrl/*.json'))
print("clip | middle-latent (L2-21) rel. delta (R-F)/F in % at sigma 0.2 0.4 0.6 0.8 | freeze rel % at 0.2 0.8 | seeds-consistent?")
for f in files:
    d=json.load(open(f)); rows=d['rows']
    name=os.path.basename(f).replace('.json','').replace('r3_probe_','').replace('r3c_','')
    out=[];cons=[]
    for sig in [0.2,0.4,0.6,0.8]:
        ds=[]
        for sd in [3,4,5]:
            F=np.array([r['per_frame'] for r in rows if r['variant']=='forward' and r['sigma']==sig and r['seed']==sd][0])
            R=np.array([r['per_frame'] for r in rows if r['variant']=='reverse' and r['sigma']==sig and r['seed']==sd][0])
            ds.append((R[2:22].mean()-F[2:22].mean())/F[2:22].mean()*100)
        out.append(np.mean(ds)); cons.append(np.std(ds))
    Z=[];
    for sig in [0.2,0.8]:
        F=np.mean([np.mean(r['per_frame'][2:22]) for r in rows if r['variant']=='forward' and r['sigma']==sig])
        Zf=np.mean([np.mean(r['per_frame'][2:22]) for r in rows if r['variant']=='freeze_first' and r['sigma']==sig])
        Z.append((Zf-F)/F*100)
    print(f"{name:26s} " + ' '.join(f"{o:+6.1f}" for o in out) + "   sd " + ' '.join(f"{c:.1f}" for c in cons) + f" | {Z[0]:+5.0f} {Z[1]:+5.0f}")
