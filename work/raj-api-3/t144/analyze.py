import json,csv,re,sys
from scipy.stats import binomtest
key=json.load(open('../t144/KEY_DO_NOT_OPEN.json'))
rows=list(csv.DictReader(open('work/raj-api-2/t144/codes.csv')))
d={}
for r in rows:
    m=re.match(r't144_G1_(\w+)_s(\d+)',key[r['hex']]); d[(m[1],int(m[2]))]=r
def y(a,s,strict):
    r=d[(a,s)]; v=r['clean_fall']=='Y'
    if strict and 'AMBIGUOUS' in r['note']: v=False
    return v
arms=['A','VD','VU','VI','VB']
for strict in (0,1):
    print('STRICT' if strict else 'PRIMARY')
    for a in arms: print(a,sum(y(a,s,strict) for s in range(1,11)),'/10')
    ps={}
    for b in ('VU','VI','VB','A'):
        b1=sum(y('VD',s,strict) and not y(b,s,strict) for s in range(1,11))
        c=sum(y(b,s,strict) and not y('VD',s,strict) for s in range(1,11))
        p=binomtest(b1,b1+c,.5,alternative='greater').pvalue if b1+c else 1.0
        ps[b]=p; print(f'VD vs {b}: VD-only {b1}, {b}-only {c}, p1={p:.4f}')
    p=sorted([ps['VU'],ps['VI']]); print('Holm adj:',{k:min(1,v*(2 if v==p[0] else 1)) for k,v in ((k,ps[k]) for k in('VU','VI'))})
for k in ('first_disp','holder_redrawn','clone'):
    print(k)
    for a in arms: 
        from collections import Counter
        print(' ',a,dict(Counter(d[(a,s)][k] for s in range(1,11))))
