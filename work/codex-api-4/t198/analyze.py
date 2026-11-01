"""Independent gate reconstruction and frozen-QC/period join, no fitting.

python analyze.py [output.json]
"""
from pathlib import Path
import csv,json,hashlib,sys,math
import numpy as np
ROOT=Path(__file__).resolve().parent

def summarize(values,reference=1.):
    a=np.asarray(values,dtype=float)
    return {'n':len(a),'mean':float(a.mean()),'seed_se':float(a.std(ddof=1)/math.sqrt(len(a))) if len(a)>1 else None,
            'ratio':float(a.mean()/reference),'ratio_seed_se':float(a.std(ddof=1)/math.sqrt(len(a))/reference) if len(a)>1 else None}

def reconstruct(record,real):
    theta=np.asarray(record['series']['theta']);length=np.asarray(record['series']['L'])
    rt=np.asarray(real['series']['theta']);rl=np.asarray(real['series']['L'])
    grid=list(range(-20,81,5));anchors=[]
    for center in grid:
        points=[l for t,l in zip(rt,rl) if center-5<=t<center+5]
        if points:anchors.append((center,float(np.median(points))))
    mask=(theta>=-20)&(theta<=80)
    prediction=np.interp(theta[mask],*[np.array(x) for x in zip(*anchors)])
    errors=np.abs(length[mask]-prediction)/prediction
    dev=float(np.median(errors)) if len(errors) else 9.
    gates=[record['pivot_resid_px']<3,math.dist(record['pivot'],[326,118])<15,dev<.2,record['valid_frac']>=.6,record.get('r2',0)>=.8]
    return {'Ldev':dev,**{f'G{i}':bool(g) for i,g in enumerate(gates,1)},'PASS':all(gates),
            'g3_frames':int(mask.sum()),'tracked_frames':len(theta),'g3_fraction':float(mask.mean()),
            'within_g3_frames_error_ge20pct':int((errors>=.2).sum()),
            'max_abs_theta_deg':float(np.max(np.abs(theta))),
            'g3_is_median_angle_restricted':True}

def main():
    codes=list(csv.DictReader((ROOT/'codes.csv').open()))
    assert hashlib.sha256((ROOT/'codes.csv').read_bytes()).hexdigest()=='913d14657644cbe2e070bc1b71c8afa964791b6d1a86e18b4890200d22824608'
    assert hashlib.sha256((ROOT/'key.json').read_bytes()).hexdigest()=='1f42b08d274430e20946ceed35437c1d59585c7450af8ce92a95f03918ea3028'
    key=json.loads((ROOT/'key.json').read_text());fresh=json.loads((ROOT/'source/fresh.json').read_text())
    author=json.loads((ROOT/'source/gates_fresh.json').read_text());real=json.loads((ROOT/'source/real.json').read_text())['real_pend10_f93']
    measured=json.loads((ROOT/'measurement/results.json').read_text())
    reference=json.loads((ROOT/'source/real10_calibration_record.json').read_text())
    refperiod=reference['tool']['period_s'];rows=[]
    for c in codes:
        ident=c['id'];name=key[ident]['name'];r=fresh[name];g=reconstruct(r,real)
        for field in ['G1','G2','G3','G4','G5','PASS']:assert g[field]==author[name][field],(name,field)
        assert abs(g['Ldev']-author[name]['Ldev'])<1e-12
        c.update(name=name,seed=int(name.rsplit('s',1)[1]),author_gates=g,author_period_s=r['T'],
                 native_eligible=all(c[k]=='Y' for k in ['scene','single','fixed_pivot','rigid']))
        if ident in measured:c['planted_pass_tool']=measured[ident];c['tool_real_ratio']=measured[ident]['period_s']/refperiod
        rows.append(c)
    passes=[r for r in rows if r['author_gates']['PASS']]
    native=[r for r in passes if r['native_eligible']]
    assert len(rows)==12 and len(passes)==3 and len(native)==2
    oldg=json.loads((ROOT/'source/gates.json').read_text());oldn=json.loads((ROOT/'source/nano.json').read_text())
    oldp=[v['T'] for n,v in oldn.items() if 'p12f101' not in n and oldg[n]['PASS']]
    result={'scope':'same fresh12 movies; independent partially masked native QC and different planted-PASS estimator; no new seeds',
      'native_counts':{k:{v:sum(r[k]==v for r in rows) for v in ['Y','N','U']} for k in ['scene','single','fixed_pivot','rigid','visible_motion']},
      'author_gate_pass_count':len(passes),'native_eligible_count':sum(r['native_eligible'] for r in rows),
      'native_author_intersection':[r['id'] for r in native],
      'author_pass_native_rigid':{v:sum(r['rigid']==v for r in passes) for v in ['Y','N','U']},
      'author_fresh':summarize([r['author_period_s'] for r in passes],real['T']),
      'author_pooled':summarize(oldp+[r['author_period_s'] for r in passes],real['T']),
      'independent_period_all_source_passes':summarize([r['planted_pass_tool']['period_s'] for r in passes],refperiod),
      'independent_period_native_intersection':summarize([r['planted_pass_tool']['period_s'] for r in native],refperiod),
      'reference_tool_s':refperiod,'reference_mocap_s':reference['reference_crossing']['period_s'],
      'all3_independent_tool_ok':all(r['planted_pass_tool']['flag']=='ok' for r in passes),
      'max_abs_method_difference_s':max(abs(r['author_period_s']-r['planted_pass_tool']['period_s']) for r in passes),
      'rows':rows}
    target=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results.json'
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
