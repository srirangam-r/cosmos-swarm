"""Independent arithmetic and contract verification of completed task8 outputs."""
from pathlib import Path
import json,sys,hashlib,subprocess
import numpy as np
p=Path(__file__).resolve().parent; data=json.loads((p/'output/results.json').read_text());assert set(data)==set(map(str,range(1,21)))
for key,r in data.items():
 assert r['id']==int(key) and r['fps']==25
 t=r['tool'];ref=r['reference_crossing'];turn=r['reference_turning']
 assert r['ratio']==t['period_s']/ref['period_s']
 assert r['ratio_turning']==t['period_s']/turn['period_s']
 assert ref['period_s']==float(np.median(ref['cycles_s']))
 assert turn['period_s']==float(np.median(turn['cycles_s']))
 assert t['flag']==('ok' if t['n_halfcycles']>=3 and t['r2']>.8 and abs(t['period_s']-t['period_zc_s'])/t['period_s']<.05 and t['frac_tracked']>=.9 else 'check')
 for side in ['reference_crossing','reference_turning']:
  assert len(r[side]['cycles_s'])>=2
for subset in ['all','ok']:
 rr=[r for r in data.values() if subset=='all' or r['tool']['flag']=='ok']; summary=json.loads((p/f'output/summary_{subset}.json').read_text()); assert summary['n']==len(rr)
 for key in ['ratio','ratio_turning','ratio_zc']:
  x=np.array([r[key] for r in rr]);assert np.isclose(summary[key]['mean'],sum(x)/len(x),atol=1e-15)
  var=sum((v-sum(x)/len(x))**2 for v in x)/(len(x)-1)
  assert np.isclose(summary[key]['se'],(var/len(x))**.5,atol=1e-15)
# Published real10 source used same raw in-memory transform/window.
source=json.loads((p.parents[1]/'kiro-1/t182/pend_periods.json').read_text())['real_pend10_cont']
ours=data['10']['tool'];errs={k:abs(ours[k]-source[k]) for k in ['period_s','period_zc_s','r2','beta']}
assert max(errs.values())<1e-12,errs
for line in (p/'SHA256SUMS').read_text().splitlines():
 sha,rel=line.split('  ',1);assert hashlib.sha256((p/rel).read_bytes()).hexdigest()==sha,rel
print('20 contracts/independent arithmetic/source real10/hash checks PASS',errs)
