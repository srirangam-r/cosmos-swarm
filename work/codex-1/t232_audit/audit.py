import json, math, random
from pathlib import Path
src=Path('work/rahul-api-2/t228/results.json')
rows=json.loads(src.read_text())['rows'].values()
d={a:{r['seed']:r for r in rows if r['arm']==a} for a in ('orig','L70','L50')}
assert all(set(v)==set(range(21,31)) for v in d.values())
for a,v in d.items():
 print(a,'G4',sum(r['G4'] for r in v.values()),'PASS',sum(r['PASS'] for r in v.values()),'R2',sum(r['G5'] for r in v.values()))
for a in ('L70','L50'):
 diff=[int(d[a][s]['G4'])-int(d['orig'][s]['G4']) for s in range(21,31)]
 pos=diff.count(1); neg=diff.count(-1); n=pos+neg
 p=min(1,2*sum(math.comb(n,k) for k in range(min(pos,neg)+1))/2**n) if n else 1
 rng=random.Random(232); boots=sorted(sum(rng.choice(diff) for _ in diff)/len(diff) for _ in range(20000))
 print(a,'paired G4 delta',sum(diff)/10,'bootstrap95',boots[499],boots[19499],'gain/loss',pos,neg,'exact p',p)
print('Both PASS orig/L70 seeds:',[s for s in d['orig'] if d['orig'][s]['PASS'] and d['L70'][s]['PASS']])
print('Both PASS orig/L50 seeds:',[s for s in d['orig'] if d['orig'][s]['PASS'] and d['L50'][s]['PASS']])
print('L70 G4-qualified L_med by seed:',[(s,round(r['L_med'],1)) for s,r in d['L70'].items() if r['G4']])
