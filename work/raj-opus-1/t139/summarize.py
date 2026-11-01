"""Summarize task-139 eye codes (codes.json: {clip_name: {fall,jump,clone,holder_back,reentry,any_fall: 0/1, note}}).
Per arm counts with Wilson 95% CI; Fisher exact (two-sided) A vs O and G vs O; paired-by-(input,seed) table."""
import json, sys, math
from itertools import product
C=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'codes.json'))
FF=json.load(open(sys.argv[2])) if len(sys.argv)>2 else {}
for k in C:  # automatic detector from firstfall (planted PASS tracker): onset <= f10 and fall >= 23 px (1 ball diameter)
    f=FF.get(k) or {}
    C[k]['auto_fall']=int((f.get('motion_frame') is not None) and f['motion_frame']<=10 and (f.get('fall_px') or 0)>=23)
    C[k]['clean_fall']=int(C[k].get('fall',0) and not C[k].get('descent_artifact',0))
    C[k]['fall_or_carried']=int(C[k].get('fall',0) or C[k].get('carried',0))
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),)*2
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return (c-h,c+h)
def fisher(a,b,c,d):  # [[a,b],[c,d]] two-sided
    n=a+b+c+d; r1=a+b; c1=a+c
    def p(x): return math.comb(r1,x)*math.comb(n-r1,c1-x)/math.comb(n,c1)
    p0=p(a); lo=max(0,c1-(n-r1)); hi=min(r1,c1)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=p0*(1+1e-9))
arms={}
for k,v in C.items():
    arm=k.split('_')[1]; arms.setdefault(arm,[]).append(v)
codes=['fall','clean_fall','auto_fall','fall_or_carried','jump','clone','holder_back','reentry','any_fall']
out={}
for arm in sorted(arms):
    V=arms[arm]; n=len(V); out[arm]={'n':n}
    for c in codes:
        kk=sum(int(v.get(c,0)) for v in V); out[arm][c]=[kk,n,[round(x,2) for x in wilson(kk,n)]]
for arm in ('A','G'):
    if arm in out and 'O' in out:
        for c in ('fall','clean_fall','auto_fall','fall_or_carried','any_fall','holder_back'):
            a=out[arm][c][0]; n1=out[arm]['n']; o=out['O'][c][0]; n0=out['O']['n']
            out[f'{arm}_vs_O_{c}']={'diff':round(a/n1-o/n0,3),'fisher_p':round(fisher(a,n1-a,o,n0-o),4)}
print(json.dumps(out,indent=1)); json.dump(out,open('summary.json','w'),indent=1)
# Seed-level analysis (ball1/ball2 are near-identical frames, so outcomes cluster by seed): per seed, mean code over
# inputs per arm; paired arm-O difference across seeds with mean +- SE and an exact sign test on non-zero seeds.
seeds={}
for k,v in C.items():
    _,arm,inp,s=k.split('_'); seeds.setdefault(s,{}).setdefault(arm,[]).append(v)
seed_out={}
for c in ('fall','clean_fall','any_fall','holder_back'):
    for arm in ('A','G'):
        d=[]
        for s,A in sorted(seeds.items()):
            if arm in A and 'O' in A:
                d.append(sum(x[c] for x in A[arm])/len(A[arm])-sum(x[c] for x in A['O'])/len(A['O']))
        if not d: continue
        n=len(d); m=sum(d)/n; se=(sum((x-m)**2 for x in d)/(n-1))**.5/n**.5 if n>1 else float('nan')
        pos=sum(x>0 for x in d); neg=sum(x<0 for x in d); nn=pos+neg
        p=min(1,2*sum(math.comb(nn,i) for i in range(0,min(pos,neg)+1))/2**nn) if nn else 1.0
        seed_out[f'{arm}-O_{c}_seedlevel']={'n_seeds':n,'mean':round(m,3),'se':round(se,3),'pos':pos,'neg':neg,'sign_p':round(p,4)}
print(json.dumps(seed_out,indent=1)); out['seed_level']=seed_out; json.dump(out,open('summary.json','w'),indent=1)
