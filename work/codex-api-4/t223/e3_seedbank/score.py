"""Frozen E3 composite gate; no native data or network operations."""
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import analysis_core as core

QC_FIELDS=['scene','single','fixed_pivot','rigid','swing']

def native_success(qc):
    if qc is None: return None
    values=[qc[k] for k in QC_FIELDS]
    if any(v not in ['Y','N','U'] for v in values): raise ValueError('Unknown QC code')
    if 'N' in values: return 0
    return 1 if all(v=='Y' for v in values) else None

def joint_success(contract,qc,fit,reference):
    if contract!='pass': return dict(state='missing_or_invalid',value=None)
    native=native_success(qc)
    if native==0: return dict(state='known',value=0,reason='definite native QC failure; not a period')
    if native is None: return dict(state='unknown',value=None,reason='native QC unresolved')
    if fit is None or fit.get('flag')!='ok':
        return dict(state='unknown',value=None,reason='period fit unresolved')
    period=fit.get('period_s')
    if not isinstance(period,(int,float)) or not math.isfinite(period) or period<=0:
        return dict(state='unknown',value=None,reason='period nonfinite/nonpositive')
    if not math.isfinite(reference) or reference<=0: raise ValueError('Invalid real reference')
    ratio=period/reference
    return dict(state='known',value=int(.8<=ratio<=1.2),ratio=ratio,
                reason='native allY and tool ok; provisional composite')

def analyze_complete(cells,seeds,bootstraps=core.BOOTSTRAPS,perms=core.PERMUTATIONS):
    if len(seeds)!=len(set(seeds)) or len(seeds)<4: raise ValueError('Unique candidate seeds required')
    expected={(s,i) for s in seeds for i in ['pend10','pend11','pend14']}
    if set(cells)!=expected: raise ValueError('Require exactly planned cells')
    for cell in cells.values():
        if cell['state']=='known' and cell['value'] not in [0,1]: raise ValueError('Binary known scores required')
        if cell['state']!='known' and cell['value'] is not None: raise ValueError('Missing/unknown cannot have a score')
    missing=[dict(seed=s,input=i,state=cells[s,i]['state']) for s,i in sorted(expected)
             if cells[s,i]['state']!='known']
    if missing: return dict(status='blocked',raw_p=None,holm_p=None,family_size=1,missing=missing)
    train=[[cells[s,'pend10']['value']] for s in seeds]
    test=[[cells[s,i]['value'] for i in ['pend11','pend14']] for s in seeds]
    result=core.seedbank(train,test,seeds,['pend11','pend14'],bootstraps,perms)
    return dict(status='computed; provisional unvalidated composite',raw_p=result['permutation']['p_one_sided'],
                holm_p=result['permutation']['p_one_sided'],family_size=1,result=result,
                uncertainty_scope='descriptive and underpowered: two held-out inputs on one apparatus')
