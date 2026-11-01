import json, os, re, numpy as np
D='/home/nail/swarm-work/scout-1/cosmos-swarm/work/ro-1/hue_trunc'
R=json.load(open(D+'/res.json'))['results']
by={}
for r in R:
    s=os.path.basename(r['clip'])[:-4]
    v=dict(r['summary']); v.update({f"Q{x['id']}": x['p_yes'] for x in r['rows']})
    by.setdefault(s,[]).append(v)
M={s:{k:float(np.mean([x[k] for x in v])) for k in v[0]} for s,v in by.items()}
rest={('ball1',1):32,('ball1',2):32,('ball1',3):15,('ball1',4):24,('ball1',5):66,('ball2',1):72,('ball2',2):60,('ball2',3):40}
teth={('ball1',2),('ball1',4)}
for w in ('early','late'):
    arms={}
    for s in M:
        m=re.search(rf'^{w}__.*_(F|QT)_(ball\d)_fps24_93f_s(\d)', s)
        if m: arms[(m.group(1),m.group(2),int(m.group(3)))]=s
    print('==',w)
    rows=[]
    for k in sorted(rest):
        f=M[arms[('F',)+k]]; t=M[arms[('QT',)+k]]
        q125=np.mean([t[q]-f[q] for q in ['Q1','Q2','Q5']]); ov=t['overall']-f['overall']
        rows.append((k,rest[k],q125,ov))
        print(k,'rest',rest[k],'tether' if k in teth else '      ','Q125 %+.3f overall %+.3f | Q1 %+.2f Q2 %+.2f Q5 %+.2f'%(q125,ov,t['Q1']-f['Q1'],t['Q2']-f['Q2'],t['Q5']-f['Q5']))
    a=np.array([r[3] for r in rows if r[0] not in teth]); b=np.array([r[3] for r in rows if r[0] in teth])
    print('overall non-tether %+.3f ± %.3f (n=6), tether %s'%(a.mean(),a.std(ddof=1)/np.sqrt(6),np.round(b,3)))
    e=[r[3] for r in rows if r[1]<46 and r[0] not in teth]; l=[r[3] for r in rows if r[1]>=46]
    print('late-window: QT rested before window start (non-tether) overall', np.round(e,3), 'QT still moving into window', np.round(l,3))
