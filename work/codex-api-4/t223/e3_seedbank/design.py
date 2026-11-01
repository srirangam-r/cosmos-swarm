"""Outcome-blind E3 request registry and real-reference freeze. No generation."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import urlopen

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
BASE='http://100.111.167.68:8030'
SEEDS=list(range(601,625))
INPUTS=['pend10','pend11','pend14']
FIELDS=['id','owner','name','prompt','image','params','endpoints','endpoint']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

def main():
    owner_paths=[REPO/'work/raj-noise/jobs'/f'E3_part{i}.jsonl' for i in [0,1]]
    owner=[json.loads(line) for p in owner_paths for line in p.read_text().splitlines()]
    assert len(owner)==72 and len({r['name'] for r in owner})==72
    expected={f'N_E3_{i}_s{s}' for s in SEEDS for i in INPUTS}
    assert {r['name'] for r in owner}==expected
    assert len({r['prompt'] for r in owner})==1
    for row in owner:
        assert row['extra_params']['noise']=={'device':'cpu'}
        assert row['num_frames']==93 and row['fps']==24
    # The HTTP payload is discarded except explicitly allowed DESIGN fields.
    # Never save/print status, sidecar, finished time, error, output or scores.
    found=[]
    for account in ['raj-noise']+['raj-noise-'+c for c in 'bcdefghi']:
        with urlopen(BASE+'/jobs?owner='+account,timeout=30) as stream:
            response=json.load(stream)
        rows=response['jobs'] if isinstance(response,dict) else response
        found.extend({k:r.get(k) for k in FIELDS} for r in rows if r['name'] in expected)
    assert len(found)==72 and len({r['name'] for r in found})==72
    indexed={r['name']:r for r in found}
    settings=dict(width=832,height=480,num_frames=93,fps=24,steps=35,guidance=6.,flow_shift=10.)
    for source in owner:
        row=indexed[source['name']]
        assert row['prompt']==source['prompt'] and row['image']==Path(source['image']).name
        assert row['params']['negative_prompt'] is None
        for k,v in row['params'].items(): assert source.get(k)==v,(row['name'],k)
        for k,v in settings.items(): assert row['params'][k]==v
        assert set(row['endpoints'])=={'q8-'+str(i) for i in range(8)}
        assert row['endpoint'] is None or row['endpoint'] in row['endpoints']
    sys.path.insert(0,str(REPO/'work/codex-api-4/t8'))
    from reference import cross_cycles, turning_cycles
    import numpy as np
    references={}
    for rec,start in [(10,93),(11,81),(14,81)]:
        path=REPO/f'work/codex-api-4/t8/output/traces/real_{rec:02}.json'
        trace=json.loads(path.read_text()); r=trace['record']
        t=np.asarray(trace['mocap_time_s']); x=np.asarray(trace['mocap_axis_m'])
        lo=r['sync_offset_s']+start/25; hi=r['sync_offset_s']+(start+92)/25
        crossing=cross_cycles(t,x,lo,hi)
        assert crossing['period_s'] is not None and len(crossing['cycles_s'])>=2
        references['pend'+str(rec)]=dict(start_distinct_frame=start,real_fps=25,
            window_s=[lo,hi],crossing=crossing,
            turning=turning_cycles(t,x,lo,hi,r['mocap_fps']),
            alignment_sensitivity={str(d):cross_cycles(t,x,lo+d/25,hi+d/25) for d in [-1,0,1]},
            trace_path=str(path.relative_to(REPO)),trace_sha256=sha(path))
    for p in ['measure_pend.py','trk.py']:
        import subprocess
        expected_bytes=subprocess.check_output(['git','show','2e26463:tools/trk_ballfall/'+p],cwd=REPO)
        assert expected_bytes==(REPO/'tools/trk_ballfall'/p).read_bytes()
    write(HERE/'owner_E3.jsonl.json',owner)
    write(HERE/'design_only_queue.json',dict(selection='Exactly72 design rows; no E3 statuses/outcomes/sidecars inspected',
        source_files={str(p.relative_to(REPO)):sha(p) for p in owner_paths},
        seeds=SEEDS,training=['pend10'],heldout=['pend11','pend14'],bank_size=6,
        runs=sorted(found,key=lambda r:r['name'])))
    write(HERE/'references.json',dict(references=references,
        method='task8 independent mocap crossings over declared frame windows',
        reference_code_sha256=sha(REPO/'work/codex-api-4/t8/reference.py'),
        tool_hashes={p:sha(REPO/'tools/trk_ballfall'/p) for p in ['measure_pend.py','trk.py']},
        validation='Period tracker existing planted-PASS2e26463,20/20,4pendulums<5%; native QC/composite unvalidated'))
    print(json.dumps(dict(design_rows=len(found),owners=dict(Counter(r['owner'] for r in found)),
        assigned_endpoints=dict(Counter(r['endpoint'] for r in found)),
        design_sha256=sha(HERE/'design_only_queue.json'),
        real_reference_period_s={k:v['crossing']['period_s'] for k,v in references.items()})))

if __name__=='__main__': main()
