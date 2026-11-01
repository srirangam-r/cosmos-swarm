#!/usr/bin/env python3
"""Independent corridor pixel-change reanalysis; NOT a validated physics tool."""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
import cv2,numpy as np
from scipy.stats import t

PAIRS=[('L10','A0'),('L10','RL10'),('L10','S12a4all'),('L20','A0'),('L20','L10'),('RL10','A0'),('S12a4all','A0'),('S12a4e','A0')]
NAME=re.compile(r'(?:t170|r3082)_(\w+)_(ball[12])_s(\d+)$')

def dump(p,x):p.write_text(json.dumps(x,indent=1,sort_keys=True)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
def contrast(vals):
    d=np.array([v for _,_,v in vals]);se=float(d.std(ddof=1)/np.sqrt(len(d)))
    clusters=[np.mean([v for _,s,v in vals if s==k]) for k in sorted({s for _,s,_ in vals})]
    cse=float(np.std(clusters,ddof=1)/np.sqrt(len(clusters)))
    return dict(mean=float(d.mean()),se=se,lb90=float(d.mean()-t.ppf(.9,len(d)-1)*se),ub90=float(d.mean()+t.ppf(.9,len(d)-1)*se),n=len(d),
                seed_cluster_se=cse,n_seeds=len(clusters),seed_means=clusters,seed_lb90=float(d.mean()-t.ppf(.9,len(clusters)-1)*cse),seed_ub90=float(d.mean()+t.ppf(.9,len(clusters)-1)*cse),differences=vals)

def main():
    a=argparse.ArgumentParser();a.add_argument('clips',type=Path);a.add_argument('refs',type=Path);a.add_argument('qc',type=Path);a.add_argument('out',type=Path);args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    repo=Path(__file__).resolve().parents[3]
    source=Path(__file__).parent/'source/rogcc_metrics.json';orig=json.loads(source.read_text())
    prompts=json.loads((repo/'work/raj-opus-1/steer128/prompts.json').read_text())
    vectors={k:np.array([[float(f'{x:.4g}') for x in row] for row in np.load(repo/f'work/raj-opus-1/steer128/{v}')],dtype=np.float64) for k,v in [('v','v_L12_s0s5.npy'),('r','rand_L12.npy')]}
    data={}; audits={};hashes={};f0={}; rounded_source_diffs=[]
    for p in sorted(list(args.clips.glob('t170_*.mp4'))+list(args.refs.glob('r3082_*.mp4'))):
        arm,inp,seed=NAME.fullmatch(p.stem).groups();seed=int(seed)
        side=p.with_suffix('.json');s=json.loads(side.read_text())
        assert [s[k] for k in ['width','height','num_frames','fps','steps','guidance','flow_shift','seed']]==[832,480,93,24,35,6,10,seed]
        assert s['endpoint'] in [f'q8-{i}' for i in range(8)]
        assert s['prompt_text']==prompts['QT' if arm=='QT' else 'F']
        assert not s['negative_prompt_text']
        assert s['image']==f'gauge_{inp}_dd{33 if inp=="ball1" else 35}_832x480.png'
        steer=s.get('extra_params',{}).get('internals',{}).get('steer')
        vector_hash=None
        if arm!='QT':
            assert steer['passes']=='cond' and len(steer['vectors'])==1
            v=steer['vectors'][0];assert v['layer']==12
            val=np.array(v['values'],dtype=np.float64)
            assert np.array_equal(val,vectors['r' if arm.startswith('R') else 'v'])
            assert steer['alpha']==(0 if arm=='A0' else 4)
            expected={'L10':[10,35],'L20':[20,35],'RL10':[10,35],'S12a4e':[0,10]}.get(arm,[0,35])
            assert steer.get('step_range',[0,35])==expected
            vector_hash=sha(val.tobytes())
        cap=cv2.VideoCapture(str(p));fps=cap.get(cv2.CAP_PROP_FPS);traces=[[],[]];prev=[None,None];rgbhash=hashlib.sha256();n=0
        while True:
            ok,bgr=cap.read()
            if not ok:break
            assert bgr.shape==(480,832,3)
            rgbhash.update(bgr[:,:,::-1].tobytes())
            if n==0:f0[p.stem]=bgr.copy()
            c=bgr[130:360,220:360]
            g=[cv2.cvtColor(c,cv2.COLOR_BGR2GRAY).astype(np.float64),c.astype(np.float64)@np.array([.114,.587,.299])]
            for i in range(2):
                if prev[i] is not None:traces[i].append(float(np.abs(g[i]-prev[i]).mean()))
            prev=g;n+=1
        cap.release();assert n==93 and fps==24
        data[p.stem]=dict(arm=arm,inp=inp,seed=seed,rounded_trace=traces[0],continuous_trace=traces[1],rounded_last20=float(np.mean(traces[0][-20:])),continuous_last20=float(np.mean(traces[1][-20:])),count_late_below_point6=int(np.sum(np.array(traces[1][-20:])<.6)))
        if p.stem in orig:rounded_source_diffs.append(abs(data[p.stem]['rounded_last20']-orig[p.stem]['last20']))
        audits[p.stem]=dict(endpoint=s['endpoint'],queue_id=s['queue_id'],input=s['image'],seed=seed,arm=arm,vector_float64_sha256=vector_hash,settings_pass=True,server_hook_summary_available=('internals' in s))
        hashes[p.stem]=dict(mp4=sha(p.read_bytes()),sidecar=sha(side.read_bytes()),decoded_rgb=rgbhash.hexdigest())
    assert len(data)==64 and len(rounded_source_diffs)==40
    results={}
    for metric in ['rounded_last20','continuous_last20']:
        by={(v['arm'],v['inp'],v['seed']):v[metric] for v in data.values()}
        results[metric]={a+'-'+b:contrast([(i,s,by[a,i,s]-by[b,i,s]) for i in ['ball1','ball2'] for s in range(10,14)]) for a,b in PAIRS}
    # Original prereg C1/C3 combine continuous new readout with published rounded references.
    results['original_mixed_implementation']={}
    for b in ['A0','S12a4all']:
        results['original_mixed_implementation']['L10-'+b]=contrast([(i,s,data[f't170_L10_{i}_s{s}']['continuous_last20']-orig[f'r3082_{b}_{i}_s{s}']['last20']) for i in ['ball1','ball2'] for s in range(10,14)])
    key=json.loads((args.qc/'PRIVATE_KEY.json').read_text());codes=list(csv.DictReader((Path(__file__).parent/'qc/codes.csv').open()))
    assert len(key)==len(codes)==24
    eye={key[c['id']]:c for c in codes};tally={}
    for name,c in eye.items():
        arm=data[name]['arm'];q=tally.setdefault(arm,dict(n=0,Y=0,N=0,U=0,artifact_Y=0));q['n']+=1;q[c['rest']]+=1;q['artifact_Y']+=c['artifact']=='Y'
    results['eye_tally']=tally;results['source_rounded_max_abs_difference']=max(rounded_source_diffs)
    results['means']={a:{m:float(np.mean([v[m] for v in data.values() if v['arm']==a])) for m in ['rounded_last20','continuous_last20']} for a in sorted({v['arm'] for v in data.values()})}
    c=results['original_mixed_implementation']['L10-A0'];r=results['continuous_last20']['L10-RL10']
    results['original_prereg_verdict']='H-D' if c['ub90']<0 and r['ub90']<0 and c['mean']<=-.55 else ('H-E' if c['mean']>-.3 and c['lb90']>-.55 else 'partial/inconclusive')
    results['same_seed_f0_max_pixel_delta']={a:max(int(np.max(np.abs(f0[f't170_{a}_{i}_s{s}'].astype(int)-f0[f'r3082_A0_{i}_s{s}'].astype(int)))) for i in ['ball1','ball2'] for s in range(10,14)) for a in ['L10','L20','RL10']}
    dump(args.out/'metrics.json',data);dump(args.out/'results.json',results);dump(args.out/'audit.json',audits);dump(args.out/'hashes.json',hashes);dump(args.out/'eye.json',eye);dump(args.out/'UNBLIND_key.json',key)
    print(json.dumps(results,indent=1))

if __name__=='__main__':main()
