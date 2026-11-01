"""Join already-frozen visual codes, sidecars and preregistered measurement outputs."""
import pathlib,json,hashlib,csv,re,collections,cv2,numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
EXPECTED_CODES='af474cbcf5967d04cd021b0bfcedf8290c6207819122c8fe87c8f28944e7cf44'
EXPECTED_KEY='55efdbe3783333d2a1d82b70d5b326972c697d72f77ba27cd9175fbdf1ce5257'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert sha(ROOT/'codes.json')==EXPECTED_CODES
    assert sha(ROOT/'blind_key.json')==EXPECTED_KEY
    key=json.loads((ROOT/'blind_key.json').read_text());codes=json.loads((ROOT/'codes.json').read_text());metrics=json.loads((ROOT/'metrics_masked.json').read_text())
    assert len(key)==len(codes)==len(metrics)==48
    rows=[];meta={}
    for code,name in key.items():
        scene,arm,seed=re.fullmatch(r'ms_pend(10|11)_mid([BTW])_s([1-8])',name).groups();seed=int(seed)
        path=ROOT/'clips'/(name+'.mp4');side=json.loads(path.with_suffix('.json').read_text());mp=metrics[code]['mp'];acf=metrics[code]['acf']
        assert (side['width'],side['height'],side['num_frames'],side['fps'],side['steps'],side['guidance'],side['flow_shift'])==(832,480,93,24,35,6.,10.)
        assert side['seed']==seed and side['negative_prompt_text']=='' and side['extra_params']=={}
        assert side['endpoint'].startswith('q8-')
        assert ('1.2 seconds' in side['prompt_text'])==(arm=='T')
        assert ('2.5 seconds' in side['prompt_text'])==(arm=='W')
        cap=cv2.VideoCapture(str(path));nf=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS);w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));cap.release()
        assert (nf,w,h)==(93,832,480) and abs(fps-24)<1e-8
        eligible=codes[code]['rigid']=='Y' and mp.get('flag')=='ok'
        row=dict(code=code,name=name,scene=scene,arm=arm,seed=seed,split='existing1-3' if seed<=3 else 'fresh4-8',rigid=codes[code]['rigid'],eligible=eligible,mp_flag=mp.get('flag'),period_s=mp.get('period_s'),period_ci95=json.dumps(mp.get('period_ci95')),r2=mp.get('r2'),acf_flag=acf.get('flag'),acf_period_s=acf.get('period_frames',0)/24 if acf.get('period_frames') else None,endpoint=side['endpoint'],queue_id=side['queue_id'],sha256=sha(path),bytes=path.stat().st_size,nframes=nf,fps=fps,notes=codes[code]['notes'])
        rows.append(row);meta[name]=side
    rows.sort(key=lambda r:(r['scene'],r['seed'],r['arm']))
    with (ROOT/'table.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    out={'n':48,'distinct_seed_values':8,'inputs':2,'primary_eligible':sum(r['eligible'] for r in rows),'rigidity':dict(collections.Counter(r['rigid'] for r in rows)),'by_arm':{},'paired_contrasts':{},'endpoint_match':{},'notes':'Exact descriptive counts on this fixed sample. Visual codes are unvalidated. No population uncertainty or timing-effect estimate is justified by zero primary eligibility.'}
    for arm in 'BTW':
        rr=[r for r in rows if r['arm']==arm]
        out['by_arm'][arm]={'n':len(rr),'visual':dict(collections.Counter(r['rigid'] for r in rr)),'mp_flags':dict(collections.Counter(r['mp_flag'] for r in rr)),'eligible':sum(r['eligible'] for r in rr)}
    cells={(r['scene'],r['seed'],r['arm']):r for r in rows}
    for a,b in [('T','B'),('W','T')]:
        pairs=[(cells[(s,i,a)],cells[(s,i,b)]) for s in ['10','11'] for i in range(1,9)]
        valid=[(x,y) for x,y in pairs if x['eligible'] and y['eligible']]
        out['paired_contrasts'][a+'-'+b]={'n_planned':16,'n_eligible':len(valid),'effect':None,'SE':None,'sign_test_p':None,'reason':'No eligible paired periods'}
        out['endpoint_match'][a+'-'+b]=sum(x['endpoint']==y['endpoint'] for x,y in pairs)
    (ROOT/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
    (ROOT/'sidecars.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
