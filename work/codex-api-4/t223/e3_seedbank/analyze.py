"""Join frozen masked QC with opaque fits only after codes are committed."""
import argparse
from collections import Counter
from fractions import Fraction
import itertools
import json
from pathlib import Path
import sys
import numpy as np
from score import QC_FIELDS,analyze_complete,joint_success,native_success,core
from prepare import sha,write,HERE

def scalar_reference(training,testing,seeds):
    """Independent integer subset calculation for binary two-input outcomes."""
    n=len(seeds);k=(n+3)//4
    order=sorted(range(n),key=lambda j:(-training[j],seeds[j]));top=order[:k]
    held=[sum(row) for row in testing]; observed=sum(held[j] for j in top)
    hits=total=0
    for bank in itertools.combinations(range(n),k):
        hits+=int(sum(held[j] for j in bank)>=observed);total+=1
    cutoff=training[top[-1]];above=sum(v>cutoff for v in training);tied=sum(v==cutoff for v in training)
    import math
    return dict(top_seed_ids=[seeds[j] for j in top],
        lift=float(Fraction(observed,2*k)-Fraction(sum(held),2*n)),
        p_exact=hits/total,exceedances=hits,total_random_banks=total,
        boundary_score=cutoff,seeds_strictly_above_boundary=above,seeds_tied_at_boundary=tied,
        equally_training_ranked_banks=math.comb(tied,k-above))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('root',type=Path)
    ap.add_argument('--qc',type=Path,required=True)
    ap.add_argument('--qc-sha256',required=True,help='Hash published in native-QC freeze before unmasking')
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert sha(a.qc)==a.qc_sha256
    qc=json.loads(a.qc.read_text()); key=json.loads((a.root/'key.json').read_text())
    mask=json.loads((a.root/'masking.json').read_text())
    assert sha(a.root/'key.json')==mask['key_sha256']
    assert set(qc)==set(key) and len(key)==72
    contracts=json.loads((a.root/'contracts.json').read_text());assert set(contracts)==set(key)
    refs=json.loads((HERE/'references.json').read_text())
    declared=json.loads((HERE/'design_only_queue.json').read_text())
    ids={r['id'] for r in declared['runs']};assert ids=={r['run_id'] for r in key.values()}
    cells={}; audit=[]
    for ident,entry in key.items():
        c=contracts[ident];q=qc[ident]
        assert all(q[k] in ['Y','N','U'] for k in QC_FIELDS)
        path=a.root/'fits'/(ident+'.json');record=json.loads(path.read_text()) if path.exists() else None
        fit=None
        if record is not None:
            assert record['clip_sha256']==c['clip_sha256']
            assert record['tool_hashes']==refs['tool_hashes']
            if record['status']=='computed': fit=record['result']
        contract=c['contract']
        if c['executed_endpoint'] is not None and c['executed_endpoint'] not in {'q8-'+str(i) for i in range(8)}:
            contract='invalid stack stratum'
        reference=refs['references'][entry['input']]['crossing']['period_s']
        score=joint_success(contract,q,fit,reference)
        cells[entry['seed'],entry['input']]=score
        audit.append(dict(entry,opaque_id=ident,contract=c,native_qc=q,native_score=native_success(q),
            fit_status=fit.get('flag') if fit else None,period_s=fit.get('period_s') if fit else None,
            reference_s=reference,joint_score=score))
    result=analyze_complete(cells,declared['seeds'])
    if result['status'].startswith('computed'):
        ss=declared['seeds'];train=[cells[s,'pend10']['value'] for s in ss]
        test=[[cells[s,i]['value'] for i in declared['heldout']] for s in ss]
        scalar=scalar_reference(train,test,ss)
        assert scalar['top_seed_ids']==result['result']['top_seed_ids']
        assert abs(scalar['lift']-result['result']['top_minus_random_pool'])<1e-12
        result['independent_exact_subset_reference']=scalar
    summary=dict(scope='Actual E3; provisional native-QC composite, no recipe/NVIDIA claim',
        primary=result,counts=dict(planned=72,joint_states=dict(Counter(r['joint_score']['state'] for r in audit))),
        per_clip=audit,qc_sha256=sha(a.qc),design_sha256=sha(HERE/'design_only_queue.json'),
        references_sha256=sha(HERE/'references.json'),
        limitations=['native QC/composite unvalidated','only two heldout inputs from one apparatus',
            'actual input/noise/sampler/runtime provenance unverified','NVIDIA scoreboard unmeasured'])
    a.out.mkdir(parents=True,exist_ok=True);write(a.out/'results.json',summary)
    print(json.dumps(dict(primary_status=result['status'],counts=summary['counts'])))

if __name__=='__main__': main()
