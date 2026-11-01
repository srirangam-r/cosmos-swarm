import numpy as np, glob, os, json
R=json.load(open('ct_res.json'))
rows={}
for f in sorted(glob.glob('out/*.npz')):
    n=os.path.basename(f)[:-4]; d=np.load(f); y=np.median(d['tracks'],axis=1)[:,1]; vis=d['vis'].mean()
    rest=y>290  # near/on table-plank level
    lifted_late=float((y[56:93]<250).mean())      # ball back up near gripper in late window
    lifted_early=float((y[4:37]<250).mean())
    ymin_late=float(y[56:93].min()); ymin_mid=float(y[36:56].min())
    # frames with |dy|<1.5 over 6-frame windows while y>290 = resting
    rst=0
    for i in range(0,87):
        if (y[i:i+6]>290).all() and np.ptp(y[i:i+6])<6: rst+=1
    rows[n]=dict(vis=float(vis),lifted_late=lifted_late,lifted_early=lifted_early,ymin_late=ymin_late,ymin_mid=ymin_mid,rest_windows=rst,ncontact=len(R[n]['contacts']))
    print('%-18s vis%.2f lift_e %.2f lift_l %.2f ymin_mid %3.0f ymin_late %3.0f rest %2d ncont %d'%(n,vis,lifted_early,lifted_late,ymin_mid,ymin_late,rst,rows[n]['ncontact']))
json.dump(rows,open('summ.json','w'),indent=1)
