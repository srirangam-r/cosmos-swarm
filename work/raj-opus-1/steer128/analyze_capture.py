# Task 128 step 1: where does the F-vs-QT cond-pass difference separate beyond seed spread?
import numpy as np, glob, json, itertools, re
A={}
for f in glob.glob('acts/t128cap_*.npz'):
    m=re.match(r'acts/t128cap_(F|QT)_(ball\d)_s(\d)\.npz',f); A[(m[1],m[2],int(m[3]))]=np.load(f)
keys=[k for k in next(iter(A.values())).files if k.endswith('_mean')]
steps=sorted({int(k[1:4]) for k in keys}); layers=sorted({int(k.split('_L')[1][:2]) for k in keys})
inputs=sorted({k[1] for k in A}); seeds=sorted({k[2] for k in A})
def cos(a,b): return float((a*b).sum()/np.linalg.norm(a)/np.linalg.norm(b))
rows=[]
for s in steps:
  for L in layers:
    k=f's{s:03d}_cond_L{L:02d}_mean'
    d=[];sp=[];nrm=[]
    for inp in inputs:
      for sd in seeds:
        if ('F',inp,sd) in A and ('QT',inp,sd) in A:
          F=A[('F',inp,sd)][k][1:]; Q=A[('QT',inp,sd)][k][1:]  # drop cond frame 0
          d.append(Q-F); nrm.append(np.linalg.norm(F,axis=1).mean())
      for a in ('F','QT'):
        for s1,s2 in itertools.combinations(seeds,2):
          if (a,inp,s1) in A and (a,inp,s2) in A: sp.append(A[(a,inp,s1)][k][1:]-A[(a,inp,s2)][k][1:])
    if not d: continue
    d=np.stack(d); sp=np.stack(sp)
    pd=np.linalg.norm(d,axis=2).mean()             # per-frame norm of paired QT-F diff
    ss=np.linalg.norm(sp,axis=2).mean()/np.sqrt(2) # per-frame seed noise per clip
    dm=d.mean(0)                                   # mean diff [T-1,D]
    mean_norm=np.linalg.norm(dm,axis=1).mean()
    # consistency: cos between frame-averaged diffs across pairs
    da=d.mean(1); cs=[cos(da[i],da[j]) for i,j in itertools.combinations(range(len(da)),2)]
    # leave-one-out: does mean of others predict held-out pair direction?
    loo=[cos(da[i],np.delete(da,i,0).mean(0)) for i in range(len(da))]
    # t-like: ||mean diff (frame-avg)|| / (sd across pairs / sqrt n) projected
    rows.append(dict(step=s,layer=L,n=len(d),paired=round(float(pd),3),seednoise=round(float(ss),3),ratio=round(float(pd/ss),3),meandiff=round(float(mean_norm),3),
        act_norm=round(float(np.mean(nrm)),2),cos_pairs=round(float(np.mean(cs)),3),loo_cos=round(float(np.mean(loo)),3),
        late_minus_early=round(float(np.linalg.norm(dm[12:],axis=1).mean()/max(np.linalg.norm(dm[:6],axis=1).mean(),1e-9)),3)))
json.dump(rows,open('capture_sep.json','w'),indent=1)
print('step layer n  paired seednoise ratio  |meandiff| actnorm cos_pairs loo_cos late/early')
for r in rows: print(f"{r['step']:4d} {r['layer']:5d} {r['n']:2d} {r['paired']:8.3f} {r['seednoise']:8.3f} {r['ratio']:6.3f} {r['meandiff']:8.3f} {r['act_norm']:8.2f} {r['cos_pairs']:8.3f} {r['loo_cos']:8.3f} {r['late_minus_early']:6.3f}")
