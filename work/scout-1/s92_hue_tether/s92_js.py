import json, os, re, sys
import numpy as np
sys.path.insert(0, '/home/nail/swarm-work/scout-1/cosmos-swarm/work/rog-cc/midq')
from analyze_midq import load, parse, score, SETS
pq = load('/home/nail/swarm-work/scout-1/cosmos-swarm/work/rog-cc/midq/judge.json')
q = json.load(open('/home/nail/swarm-work/scout-1/cosmos-swarm/work/rog-cc/midq/midq_questions.json'))
print(json.dumps(q)[:3000])
clips = {}
for stem, v in pq.items():
    ctl, arm, key = parse(stem)
    clips[(ctl, arm, key, stem)] = v
# QT rest frames from ro-1 eye codes (midpoints)
rest = {('ball1',1):32,('ball1',2):32,('ball1',3):15,('ball1',4):24,('ball1',5):66,('ball2',1):72,('ball2',2):60,('ball2',3):40}
for ctl in ['', 'trunc36']:
    print('=== ctl', ctl or 'full')
    rows=[]
    for key in sorted(rest):
        F=[v for (c,a,k,s),v in clips.items() if c==ctl and a=='F' and k==key]
        T=[v for (c,a,k,s),v in clips.items() if c==ctl and a=='QT' and k==key]
        if not F or not T: print('missing', key); continue
        F=F[0]; T=T[0]
        d={qid: T[0][qid]-F[0][qid] if False else T[qid]-F[qid] for qid in [1,2,5]}
        d125=np.mean(list(d.values()))
        rows.append((key, rest[key], d125, d[1], d[2], d[5], F[1],T[1],F[2],T[2],F[5],T[5]))
        print(key, 'rest',rest[key], 'dQ125 %+.3f  dQ1 %+.3f dQ2 %+.3f dQ5 %+.3f | F/QT Q1 %.2f/%.2f Q2 %.2f/%.2f Q5 %.2f/%.2f'%(d125,d[1],d[2],d[5],F[1],T[1],F[2],T[2],F[5],T[5]))
    r=np.array([x[1] for x in rows]); dd=np.array([x[2] for x in rows])
    from scipy import stats
    print('spearman rest vs dQ125', stats.spearmanr(r,dd), 'pearson', stats.pearsonr(r,dd))
    early=[x[2] for x in rows if x[1]<36]; late=[x[2] for x in rows if x[1]>=36]
    print('rest<36 n=%d mean %+.3f ; rest>=36 n=%d mean %+.3f'%(len(early),np.mean(early),len(late),np.mean(late)))
# statics and reals
for (c,a,k,s),v in clips.items():
    if a not in ('F','QT','QS'):
        print(s, c, a, ' '.join('Q%d %.2f'%(i,v[i]) for i in [1,2,5] if i in v), 'Q125 %.3f'%score(v,[1,2,5]))
