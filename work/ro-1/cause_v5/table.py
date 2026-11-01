# ro-1 task22: join late-motion proxy + DOVER/DD per clip; paired QT-F (and QS-F) by input+seed
import json, glob, os, re, numpy as np
R='/home/rohith/swarm-work/ro-1/'
lm=json.load(open(R+'cause_v5/late_motion_v56.json'))
sc={}
for k,v in json.load(open(R+'nv_qt/scores_v4.json')).items(): sc[k[:-4]]=v
for f in glob.glob(R+'nv_qt2/*.score.json'):
    d=json.load(open(f)); 
    for k,v in (d.items() if 'clip' not in d else [(os.path.basename(d['clip']),d)]): sc[os.path.basename(k).replace('.mp4','')]=v
def key2clip(k):
    m=re.match(r'b(\d)_(\w+)_s(\d)',k)
    if not m: return 'real_ball1_dd32_93f'
    b,a,s=m.groups()
    cands=[f'ball_F_ball{b}_fps24_93f_s{s}',f'cause_{a}_ball{b}_fps24_93f_s{s}',f'cause5_{a}_ball{b}_fps24_93f_s{s}',f'cause6_{a}_ball{b}_fps24_93f_s{s}']
    if a!='F': cands=cands[1:]
    for c in cands:
        if c in sc: return c
    return None
rows={}
for k,v in lm.items():
    c=key2clip(k); s=sc.get(c,{}) if c else {}
    rows[k]=dict(last20=v['last20'],late=v['late'],early=v['early'],dover=s.get('dover_fused'),dd=s.get('dd_norm'))
    print(f"{k:10s} early {v['early']:.2f} late {v['late']:.2f} last20 {v['last20']:.2f}  DOVER {s.get('dover_fused',float('nan')):.3f}  DD {s.get('dd_norm',float('nan')):.2f}  [{c}]")
real=rows.get('b1_REAL',{})
out={'rows':rows}
for A in ('QT','QS'):
    for met in ('last20','dover','dd'):
        diffs=[]
        for k,r in rows.items():
            m=re.match(r'b(\d)_F_s(\d)',k)
            if not m: continue
            o=rows.get(f'b{m.group(1)}_{A}_s{m.group(2)}')
            if o and o[met] is not None and r[met] is not None: diffs.append(o[met]-r[met])
        if diffs:
            d=np.array(diffs); se=d.std(ddof=1)/np.sqrt(len(d)) if len(d)>1 else float('nan')
            out[f'{A}-F_{met}']=dict(mean=float(d.mean()),se=float(se),n=len(d),neg=int((d<0).sum()))
            print(f"{A}-F {met}: {d.mean():+.3f} ± {se:.3f} (n={len(d)}, {int((d<0).sum())} negative)")
if real.get('dd') is not None:
    for A in ('F','QT','QS'):
        g=[abs(r['dd']-real['dd']) for k,r in rows.items() if re.match(rf'b1_{A}_s\d',k) and r['dd'] is not None]
        if g: print(f"ball1 |DD-real| {A}: {np.mean(g):.2f} (n={len(g)}; real DD {real['dd']:.2f})")
json.dump(out,open(R+'cause_v5/table.json','w'),indent=1)
