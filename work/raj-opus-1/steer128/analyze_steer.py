# Task 128 step 2: paired (arm - A0) late-motion deltas, same input+seed
import json, numpy as np, re
lm=json.load(open('lm_steer.json'))
R={}
for k,v in lm.items():
    m=re.match(r't128st_(\w+?)_(ball\d)_s(\d)',k); R[(m[1],m[2],int(m[3]))]=v
arms=json.load(open('steer_arms.json'))
out={}
print('arm        n  last20 mean   d(last20) vs A0 (+-se)  lower  late d  early d  proxy-settled(last20<1.5)')
for a in arms:
    pr=[(R[(a,i,s)],R[('A0',i,s)]) for i in ('ball1','ball2') for s in range(4,10) if (a,i,s) in R and ('A0',i,s) in R]
    if not pr: continue
    d=np.array([x['last20']-y['last20'] for x,y in pr]); dl=np.array([x['late']-y['late'] for x,y in pr]); de=np.array([x['early']-y['early'] for x,y in pr])
    se=d.std(ddof=1)/np.sqrt(len(d)) if len(d)>1 else float('nan')
    st=sum(x['last20']<1.5 for x,_ in pr)
    out[a]=dict(n=len(d),last20=float(np.mean([x['last20'] for x,_ in pr])),d_last20=float(d.mean()),se=float(se),lower=int((d<0).sum()),d_late=float(dl.mean()),d_early=float(de.mean()),settled_proxy=int(st))
    o=out[a]; print(f"{a:10s} {o['n']}  {o['last20']:6.2f}     {o['d_last20']:+6.2f} +- {o['se']:.2f}        {o['lower']}/{o['n']}  {o['d_late']:+6.2f}  {o['d_early']:+6.2f}   {st}/{o['n']}")
json.dump(out,open('steer_summary.json','w'),indent=1)
