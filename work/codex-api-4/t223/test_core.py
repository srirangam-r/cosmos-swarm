"""Manufactured numerical cases only. These are NOT Cosmos or planted videos."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import numpy as np
import analysis_core as a

HERE=Path(__file__).resolve().parent

def main():
    checks=[]
    def check(name,ok):
        checks.append({'name':name,'passed':bool(ok)})
        assert ok,name
    s=np.arange(8)[:,None,None]-3.5
    p=np.array([-1,1])[None,:,None]
    i=np.array([-1,0,1])[None,None,:]
    shape=(8,2,3)
    for name,values,term in [('pure seed',s,'seed'),('pure prompt',p,'prompt'),
                             ('pure input',i,'input'),('seed prompt interaction',s*p,'seed:prompt'),
                             ('seed input interaction',s*i,'seed:input'),
                             ('prompt input interaction',p*i,'prompt:input'),
                             ('three-way interaction',s*p*i,'seed:prompt:input_or_residual')]:
        got=a.eta_components(np.broadcast_to(values,shape))
        check(name,abs(got['eta2'][term]-1)<1e-12)
    mixed=np.broadcast_to(2*s+3*p+4*i+5*s*p,shape)
    got=a.eta_components(mixed)
    check('orthogonal fractions sum one',abs(sum(got['eta2'].values())-1)<1e-12)
    zeros=a.factorial(np.zeros(shape),bootstraps=40)
    check('constant outcome undefined shares',all(v is None for v in zeros['eta2'].values()))
    check('constant bootstrap explicitly counted',zeros['seed_cluster_bootstrap']['seed']['undefined_draws']==40)
    try:
        a.factorial(np.full(shape,np.nan),bootstraps=10)
        check('missing cube rejected',False)
    except ValueError:
        check('missing cube rejected',True)
    only=a.factorial(np.broadcast_to(s,shape),bootstraps=100)
    check('seed bootstrap retains whole cube',only['seed_cluster_bootstrap']['seed']['ci95']==[1.,1.])
    diagonal=1-np.eye(5)
    e0=a.correspondence(diagonal,bootstraps=100)
    check('E0 exact correspondence advantage',e0['different_minus_same']==1)
    check('E0 exact matching probability',abs(e0['permutation']['p_one_sided']-1/120)<1e-12)
    stat=a.correspondence(np.zeros((5,5)),bootstraps=100)
    check('static background creates no advantage',stat['different_minus_same']==0 and stat['permutation']['p_one_sided']==1)
    check('zero null distance has no ratio',stat['same_divided_by_different'] is None)
    two=a.correspondence(1-np.eye(2),bootstraps=100)
    check('resampled duplicate original seeds excluded',two['seed_cluster_bootstrap']['undefined_draws']>0 and two['seed_cluster_bootstrap']['ci95']==[1.,1.])
    poor=a.correspondence(np.eye(5),bootstraps=100)
    check('inverse correspondence not a win',poor['different_minus_same']==-1 and poor['permutation']['p_one_sided']==1)
    pair=a.paired_prompt(np.ones((4,5)),bootstraps=100)
    check('prompt test uses four seeds not twenty clips',pair['n_seeds']==4 and pair['two_sided_sign_flip_p']==.125)
    check('prompt cluster CI constant paired effect',pair['seed_cluster_bootstrap']['ci95']==[1.,1.])
    perm_input=a.paired_prompt(np.column_stack([np.arange(4),-np.arange(4)]),bootstraps=100)
    check('cancelling prompt effect not significant',perm_input['mean_difference']==0 and perm_input['two_sided_sign_flip_p']==1)
    training=np.array([1,1,0,0,0,0,0,0])[:,None]
    testing=np.broadcast_to(training,(8,6))
    good=a.seedbank(training,testing,list(range(8)),['a','a','b','b','c','c'],bootstraps=100,perms=500)
    check('training-only top bank',good['top_seed_ids']==[0,1])
    check('heldout random-pool expectation',good['random_pool_expected_mean']==.25 and good['top_minus_random_pool']==.75)
    check('top bottom contrast',good['top_minus_bottom']==1)
    check('heldout input clusters not prompt cells',good['n_heldout_inputs']==3)
    check('seed rank transfer correlation',abs(good['train_test_seed_spearman']-1)<1e-12)
    bad=a.seedbank(training,1-testing,list(range(8)),['a','a','b','b','c','c'],bootstraps=100,perms=500)
    check('bad heldout outcome cannot change selected bank',bad['top_seed_ids']==good['top_seed_ids'] and bad['top_minus_random_pool']==-.75)
    tied=a.seedbank(np.zeros((8,1)),testing,list(range(8)),['a','a','b','b','c','c'],bootstraps=100,perms=500)
    check('all-tied training has no ranking signal',not tied['training_has_ranking_signal'])
    check('banks disjoint on ties',not set(tied['top_seed_ids']) & set(tied['bottom_seed_ids']))
    check('Holm retains original order',np.allclose(a.holm([.04,.01,.03]),[.06,.03,.06]))
    # Verify actual default CLI path and deterministic replay on manufactured data.
    with tempfile.TemporaryDirectory(prefix='program-n-core-') as tmp:
        r=Path(tmp)
        fixture={'analysis':'factorial','values':mixed.tolist(),
                 'contrasts':[{'name':'prompt1_minus_prompt0','a':1,'b':0}]}
        (r/'synthetic.json').write_text(json.dumps(fixture))
        for name in ['one','two']:
            run=subprocess.run([sys.executable,str(HERE/'analysis_core.py'),str(r/'synthetic.json'),
                                '--out',str(r/(name+'.json'))],capture_output=True,text=True)
            check('CLI '+name+' exits zero',run.returncode==0)
        check('CLI deterministic replay',(r/'one.json').read_bytes()==(r/'two.json').read_bytes())
    result={'scope':'manufactured arrays only; no Cosmos outcomes or referee clips',
            'passed_checks':len(checks),'checks':checks}
    (HERE/'synthetic_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed_checks':len(checks)}))

if __name__=='__main__':
    main()
