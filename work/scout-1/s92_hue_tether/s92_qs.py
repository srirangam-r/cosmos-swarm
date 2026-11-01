import sys, numpy as np
sys.path.insert(0, '/home/nail/swarm-work/scout-1/cosmos-swarm/work/rog-cc/midq')
from analyze_midq import load, parse, score, SETS
pq = load('/home/nail/swarm-work/scout-1/cosmos-swarm/work/rog-cc/midq/judge.json')
clips={}
for stem,v in pq.items():
    c,a,k=parse(stem); clips[(c,a,k)]=v
for ctl in ['','trunc36']:
    for k in [('ball1',3),('ball1',4),('ball1',5)]:
        F=clips.get((ctl,'F',k)); S=clips.get((ctl,'QS',k)); T=clips.get((ctl,'QT',k))
        if F and S:
            print(ctl or 'full', k, 'QS-F Q125 %+.3f'%(score(S,[1,2,5])-score(F,[1,2,5])), 'Q1 %+.2f Q2 %+.2f Q5 %+.2f'%tuple(S[q]-F[q] for q in [1,2,5]), '| QS Q2 %.2f'%S[2])
# tether vs non-tether split
teth={('ball1',2),('ball1',4)}
for ctl in ['','trunc36']:
    a=[];b=[]
    for k in [('ball1',i) for i in range(1,6)]+[('ball2',i) for i in range(1,4)]:
        d=score(clips[(ctl,'QT',k)],[1,2,5])-score(clips[(ctl,'F',k)],[1,2,5])
        (a if k in teth else b).append(d)
    b=np.array(b)
    print(ctl or 'full','tether pairs',np.round(a,3),'mean %+.3f'%np.mean(a),'| others mean %+.3f ± %.3f (n=%d)'%(b.mean(), b.std(ddof=1)/np.sqrt(len(b)), len(b)))
# overall gauge without tether pairs
for ctl in ['','trunc36']:
    for s in ['gauge_overall','gauge_physical']:
        b=[score(clips[(ctl,'QT',k)],SETS[s])-score(clips[(ctl,'F',k)],SETS[s]) for k in [('ball1',1),('ball1',3),('ball1',5),('ball2',1),('ball2',2),('ball2',3)]]
        b=np.array(b); print(ctl or 'full', s, 'non-tether QT-F %+.3f ± %.3f'%(b.mean(), b.std(ddof=1)/np.sqrt(len(b))))
