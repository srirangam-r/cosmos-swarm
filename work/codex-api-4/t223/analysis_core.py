"""Program N numerical core. Inputs are analysis arrays, not arbitrary clip labels.

Usage: python3 analysis_core.py input.json --out output.json
See PROTOCOL.md. No live data, model, board, or network calls are made here.
"""
import argparse
import itertools
import json
import math
from pathlib import Path
import numpy as np

BOOTSTRAPS=2000
PERMUTATIONS=9999

def array(values, ndim):
    x=np.asarray(values,dtype=float)
    if x.ndim!=ndim or not np.isfinite(x).all() or any(n==0 for n in x.shape):
        raise ValueError('Require finite, nonempty, complete array with ndim='+str(ndim))
    return x

def interval(values):
    vals=[float(v) for v in values if v is not None and np.isfinite(v)]
    return {'ci95':np.percentile(vals,[2.5,97.5]).tolist() if vals else None,
            'defined_draws':len(vals),'undefined_draws':len(values)-len(vals)}

def eta_components(values):
    x=array(values,3)
    ns,nprompt,ni=x.shape
    mu=x.mean()
    s=x.mean(axis=(1,2),keepdims=True)-mu
    p=x.mean(axis=(0,2),keepdims=True)-mu
    i=x.mean(axis=(0,1),keepdims=True)-mu
    sp=x.mean(axis=2,keepdims=True)-mu-s-p
    si=x.mean(axis=1,keepdims=True)-mu-s-i
    pi=x.mean(axis=0,keepdims=True)-mu-p-i
    spi=x-mu-s-p-i-sp-si-pi
    terms={'seed':s,'prompt':p,'input':i,'seed:prompt':sp,'seed:input':si,
           'prompt:input':pi,'seed:prompt:input_or_residual':spi}
    ss={k:float(np.sum(np.broadcast_to(a,x.shape)**2)) for k,a in terms.items()}
    total=float(np.sum((x-mu)**2))
    if not np.isclose(sum(ss.values()),total,atol=1e-10,rtol=1e-10):
        raise AssertionError('Nonorthogonal decomposition')
    return {'n_seeds':ns,'n_prompts':nprompt,'n_inputs':ni,'total_ss':total,
            'ss':ss,'eta2':{k:(v/total if total>0 else None) for k,v in ss.items()}}

def factorial(values,bootstraps=BOOTSTRAPS):
    x=array(values,3)
    if x.shape[0]<2:
        raise ValueError('At least two seed clusters required')
    point=eta_components(x)
    draws={k:[] for k in point['eta2']}
    rng=np.random.default_rng(20261101)
    for _ in range(bootstraps):
        b=eta_components(x[rng.integers(0,x.shape[0],x.shape[0]),:,:])
        for k,v in b['eta2'].items():
            draws[k].append(v)
    point['seed_cluster_bootstrap']={k:interval(v) for k,v in draws.items()}
    point['seed_cell_means']=x.mean(axis=(1,2)).tolist()
    point['prompt_cell_means']=x.mean(axis=(0,2)).tolist()
    point['input_cell_means']=x.mean(axis=(0,1)).tolist()
    point['meaning']='Descriptive variance of this balanced outcome cube; not a universal causal allocation.'
    return point

def paired_prompt(differences,bootstraps=BOOTSTRAPS,perms=PERMUTATIONS):
    """Two-sided paired contrast, all inputs of a seed flipped/resampled together."""
    d=array(differences,2)
    seed_means=d.mean(axis=1)
    n=len(seed_means)
    if n<2:
        raise ValueError('At least two seeds required')
    rng=np.random.default_rng(20261101)
    bs=[float(seed_means[rng.integers(0,n,n)].mean()) for _ in range(bootstraps)]
    exact=2**n<=perms
    rng=np.random.default_rng(20261102)
    signs=(itertools.product([-1,1],repeat=n) if exact else
           (rng.choice([-1,1],size=n) for _ in range(perms)))
    null=[abs(float(np.dot(s,seed_means)/n)) for s in signs]
    obs=float(seed_means.mean())
    hits=sum(v>=abs(obs)-1e-12 for v in null)
    return {'n_seeds':n,'n_inputs':d.shape[1],'mean_difference':obs,
            'seed_means':seed_means.tolist(),'seed_se':float(seed_means.std(ddof=1)/math.sqrt(n)),
            'seed_cluster_bootstrap':interval(bs),
            'two_sided_sign_flip_p':float(hits/len(null) if exact else (hits+1)/(len(null)+1)),
            'exact':exact,'permutations':len(null)}

def permutations(n,count,rng):
    if math.factorial(n)<=count:
        return list(itertools.permutations(range(n))),True
    return (rng.permutation(n) for _ in range(count)),False

def randomization_p(observed,stats,exact):
    ss=list(stats)
    hits=sum(s>=observed-1e-12 for s in ss)
    return {'p_one_sided':float(hits/len(ss) if exact else (hits+1)/(len(ss)+1)),
            'exact':exact,'permutations':len(ss),'exceedances':hits}

def correspondence(distances,bootstraps=BOOTSTRAPS,perms=PERMUTATIONS):
    d=array(distances,2)
    n=d.shape[0]
    if d.shape!=(n,n) or n<2 or (d<0).any():
        raise ValueError('Require nonnegative square distance matrix on >=2 matched seeds')
    same=float(np.diag(d).mean()); different=float(d[~np.eye(n,dtype=bool)].mean())
    advantage=different-same
    rng=np.random.default_rng(20261101); draws=[]
    for _ in range(bootstraps):
        idx=rng.integers(0,n,n)
        off=idx[:,None]!=idx[None,:]
        b=d[np.ix_(idx,idx)]
        draws.append(float(b[off].mean()-np.diag(b).mean()) if off.any() else None)
    perms_it,exact=permutations(n,perms,np.random.default_rng(20261102))
    def stat(p):
        b=d[:,p]
        return float(b[~np.eye(n,dtype=bool)].mean()-np.diag(b).mean())
    return {'n_seeds':n,'same_seed_distance':same,'different_seed_distance':different,
            'different_minus_same':advantage,'same_divided_by_different':same/different if different else None,
            'seed_cluster_bootstrap':interval(draws),
            'permutation':randomization_p(advantage,(stat(p) for p in perms_it),exact)}

def banks(training,seeds):
    score=training.mean(axis=1)
    k=math.ceil(len(seeds)/4)
    ordered=sorted(range(len(seeds)),key=lambda j:(-score[j],seeds[j]))
    top=ordered[:k]
    # Disjoint sets, including training ties. Boundary ties are explicitly reported.
    bottom=ordered[-k:]
    return top,bottom,score

def rankdata(x):
    x=np.asarray(x)
    out=np.zeros(len(x))
    for v in np.unique(x):
        less=int((x<v).sum()); equal=(x==v)
        out[equal]=less+(int(equal.sum())+1)/2
    return out

def seedbank(training,testing,seeds,test_inputs,bootstraps=BOOTSTRAPS,perms=PERMUTATIONS):
    train=array(training,2); test=array(testing,2)
    if train.shape[0]!=test.shape[0] or len(seeds)!=len(train) or len(set(seeds))!=len(seeds):
        raise ValueError('Matched unique seed IDs required')
    if len(seeds)<4 or len(test_inputs)!=test.shape[1]:
        raise ValueError('At least four seeds and one input ID per test cell required')
    groups=list(dict.fromkeys(test_inputs))
    # One mean per held-out input, retaining its prompts together.
    tm=np.column_stack([test[:,np.asarray(test_inputs)==g].mean(axis=1) for g in groups])
    top,bottom,train_score=banks(train,seeds)
    held=tm.mean(axis=1)
    lift=float(held[top].mean()-held.mean())
    tb=float(held[top].mean()-held[bottom].mean())
    rng=np.random.default_rng(20261101)
    crossed=[]; seed_only=[]; fixed_bank_input=[]
    for _ in range(bootstraps):
        idx=rng.integers(0,len(seeds),len(seeds))
        jj=rng.integers(0,len(groups),len(groups))
        selected,_,_=banks(train[idx], [seeds[j] for j in idx])
        by_seed=tm[idx].mean(axis=1)
        by_both=tm[np.ix_(idx,jj)].mean(axis=1)
        seed_only.append(float(by_seed[selected].mean()-by_seed.mean()))
        crossed.append(float(by_both[selected].mean()-by_both.mean()))
        per_input=tm[:,jj].mean(axis=1)
        fixed_bank_input.append(float(per_input[top].mean()-per_input.mean()))
    ps,exact=permutations(len(seeds),perms,np.random.default_rng(20261102))
    permutation=randomization_p(lift,(float(held[list(p)][top].mean()-held.mean()) for p in ps),exact)
    rho=(float(np.corrcoef(rankdata(train_score),rankdata(held))[0,1])
         if np.ptp(train_score)>0 and np.ptp(held)>0 else None)
    return {'n_seeds':len(seeds),'n_heldout_inputs':len(groups),'bank_size':len(top),
            'top_seed_ids':[seeds[j] for j in top],'bottom_seed_ids':[seeds[j] for j in bottom],
            'training_scores':train_score.tolist(),'training_has_ranking_signal':bool(np.ptp(train_score)>0),
            'training_tied_seed_count':int(len(seeds)-len(np.unique(train_score))),
            'top_test_mean':float(held[top].mean()),'bottom_test_mean':float(held[bottom].mean()),
            'random_pool_expected_mean':float(held.mean()),'top_minus_random_pool':lift,'top_minus_bottom':tb,
            'per_input_top_minus_random':{str(g):float(tm[top,j].mean()-tm[:,j].mean()) for j,g in enumerate(groups)},
            'train_test_seed_spearman':rho,'crossed_seed_input_bootstrap':interval(crossed),
            'seed_cluster_bootstrap':interval(seed_only),'fixed_bank_input_bootstrap':interval(fixed_bank_input),
            'permutation':permutation,
            'meaning':'Training-only ranking; all test candidates required. Higher outcome must mean better by frozen definition.'}

def holm(ps):
    """Adjusted p-values in original order, for a predeclared family."""
    if not ps:
        return []
    order=np.argsort(ps,kind='stable'); result=[0.]*len(ps); previous=0.
    for rank,index in enumerate(order):
        previous=max(previous,(len(ps)-rank)*ps[index])
        result[int(index)]=min(1.,previous)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input');parser.add_argument('--out',required=True)
    args=parser.parse_args()
    payload=json.loads(Path(args.input).read_text())
    kind=payload['analysis']
    if kind=='factorial':
        result=factorial(payload['values'])
        # Only supplied, predeclared contrasts are run. Indices refer to frozen
        # prompt levels, never to a favourable ordering picked after outcome access.
        cube=array(payload['values'],3)
        contrasts=[]
        for spec in payload.get('contrasts',[]):
            a,b=int(spec['a']),int(spec['b'])
            if a==b or not (0<=a<cube.shape[1] and 0<=b<cube.shape[1]):
                raise ValueError('Contrast prompt index outside cube')
            cr=paired_prompt(cube[:,a,:]-cube[:,b,:])
            cr['name']=spec['name'];cr['a']=a;cr['b']=b
            contrasts.append(cr)
        adjusted=holm([r['two_sided_sign_flip_p'] for r in contrasts])
        for row,p in zip(contrasts,adjusted):
            row['holm_p_within_supplied_contrasts']=p
        result['paired_prompt_contrasts']=contrasts
    elif kind=='e0':
        result=correspondence(payload['distances'])
    elif kind=='e3':
        result=seedbank(payload['training'],payload['testing'],payload['seeds'],payload['test_inputs'])
    else:
        raise ValueError('analysis must be factorial, e0, or e3')
    result['input_sha256']=__import__('hashlib').sha256(Path(args.input).read_bytes()).hexdigest()
    result['protocol_version']=1
    Path(args.out).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':
    main()
