import json,glob,os,sys
import numpy as np
root=sys.argv[1]
files=sorted(glob.glob(root+'/work/raj-api-3/t48/out_ctrl/*.json'))
for f in files:
    d=json.load(open(f)); rows=d['rows']
    name=os.path.basename(f).replace('.json','').replace('r3_probe_','').replace('r3c_','')
    for sig in [0.2,0.8]:
        F=np.mean([r['per_frame'] for r in rows if r['variant']=='forward' and r['sigma']==sig],0)
        R=np.mean([r['per_frame'] for r in rows if r['variant']=='reverse' and r['sigma']==sig],0)
        Z=np.mean([r['per_frame'] for r in rows if r['variant']=='freeze_first' and r['sigma']==sig],0)
        t=np.arange(2,22)
        sF=np.polyfit(t,F[2:22],1)[0]; sR=np.polyfit(t,R[2:22],1)[0]
        print(f"{name:26s} s{sig} F:{' '.join(f'{x:.2f}' for x in F[::3])} | R:{' '.join(f'{x:.2f}' for x in R[::3])} | slopeF {sF*1000:+.2f} slopeR {sR*1000:+.2f} e-3/lat  midD {np.mean(R[2:22]-F[2:22]):+.4f}")
