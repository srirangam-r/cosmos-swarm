import json,glob,numpy as np
T=json.load(open('truth.json'));rows=[]
for k,t in T.items():
    try:r=json.load(open(f'res/{k}.json'))
    except: print(k,'NO RESULT');continue
    rows.append((k,t,r))
import collections
for name,key in [('e_T_fit','e_T_fit'),('e_v','e_v'),('g_joint','g_joint')]:
    rat=[];
    for k,t,r in rows:
        v=r.get(key)
        if isinstance(v,dict):v=v.get('e',v.get('value'))
        if isinstance(v,list): v=v[0] if v else None
        if v is None: continue
        tr=t['g'] if key=='g_joint' else t['e']
        rat.append(v/tr)
    rat=np.array(rat);print(name,len(rat),'/',len(rows),'mean %.3f sd %.3f max|err| %.3f'%(rat.mean(),rat.std(),abs(rat-1).max()) if len(rat) else '')
