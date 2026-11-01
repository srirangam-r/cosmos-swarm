#!/usr/bin/env python3
"""Exercise the exact published hook AST with sentinel forward arguments (no model)."""
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
SRC=ROOT/'source/server_prompt_switch.py'
JOBS=ROOT/'source/jobs_v8.jsonl'

def main():
    source=SRC.read_text();tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('_fwd','_Cap')]
    nodes += [n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_STATIC' for t in n.targets)]
    ns={'SW':dict(mode=None,cap=None,rng=(0,0),n=0,used=0),'_orig_fwd':lambda *a,**kw:kw}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SRC),'exec'),ns)
    checks=[]
    cap={k:'QT-'+k for k in ns['_STATIC']}
    ns['SW'].update(mode='capture');args=dict(cap,noisy_latents='live',timestep=123)
    try:ns['_fwd'](**args)
    except ns['_Cap']:checks.append('capture aborts before underlying forward')
    assert ns['SW']['cap']==cap;checks.append('capture contains static fields only')
    records=[]
    for line in JOBS.read_text().splitlines():
        job=json.loads(line);ps=job['extra_params']['prompt_switch'];lo,hi=ps['from'],ps['to'];
        sw=ns['SW'];sw.update(mode='switch',n=0,used=0,rng=(lo,hi),cap=cap)
        changed=[];allpass=[]
        for call_i in range(70):
            kw={k:'F-'+k for k in ns['_STATIC']};kw.update(noisy_latents=object(),timestep=object(),extra_dynamic=object())
            got=ns['_fwd'](**kw)
            expected=(call_i%2==0 and lo<=call_i//2<hi)
            assert all(got[k]==(cap[k] if expected else kw[k]) for k in cap)
            assert all(got[k] is kw[k] for k in ('noisy_latents','timestep','extra_dynamic'))
            assert kw['input_ids']=='F-input_ids'
            if expected:changed.append(call_i//2)
            allpass.append(call_i)
        assert changed==list(range(lo,hi)) and sw['used']==hi-lo
        records.append(dict(name=job['name'],declared_range=[lo,hi],switched_conditional_steps=changed,observed_stub_forward_calls=sw['n'],used=sw['used']))
        checks.append(job['name']+' paired-call window+dynamic invariance')
    # Default mode passes through unchanged.
    ns['SW']['mode']=None;kw={'input_ids':object()};assert ns['_fwd'](**kw)['input_ids'] is kw['input_ids']
    checks.append('disabled hook is passthrough')
    out=dict(source_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),jobs_sha256=hashlib.sha256(JOBS.read_bytes()).hexdigest(),checks=checks,records=records,scope='Exact published AST with fake underlying forward; assumes conditional then unconditional each step. Does not prove live deployment, pipeline order, tensor alignment, token positions, scheduler, or GPU execution.')
    (ROOT/'hook_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print(len(checks),'checks pass; exact published AST, fake forward only')

if __name__=='__main__':main()
