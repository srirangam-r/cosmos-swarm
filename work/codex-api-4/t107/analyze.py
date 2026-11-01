#!/usr/bin/env python3
"""Independent post-freeze audit of the 14 existing ALG clips. Pixel change only."""
import argparse, csv, hashlib, json, re
from collections import Counter
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parent
CODE_SHA='b18a7dcc51a2f5b7674377ff957bea50e362b37c49e36649d4d73d99e7c66b34'

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(x):
    x=np.asarray(x,dtype=float)
    return {'n':len(x),'mean':float(x.mean()),'sample_SE':float(x.std(ddof=1)/np.sqrt(len(x))) if len(x)>1 else None}
def measure(frames,roi):
    x0,x1,y0,y1=roi
    gray=frames[:,y0:y1,x0:x1].mean(axis=-1)
    trace=np.abs(np.diff(gray,axis=0)).mean(axis=(1,2))
    return {'motion_early':float(trace[:24].mean()),'motion_late':float(trace[-24:].mean()),
            'motion_all':float(trace.mean()),'trace':trace.tolist()}
def decode(path):
    c=cv2.VideoCapture(str(path));fps=c.get(cv2.CAP_PROP_FPS); frames=[]
    while True:
        ok,f=c.read()
        if not ok:break
        frames.append(f)
    c.release(); return np.stack(frames),fps

def main():
    ap=argparse.ArgumentParser();ap.add_argument('clips',type=Path);a=ap.parse_args()
    assert digest(ROOT/'frozen_codes.json')==CODE_SHA
    key=json.loads((ROOT/'key.json').read_text())
    codes={x['id']:x for x in json.loads((ROOT/'frozen_codes.json').read_text())['codes']}
    queue=json.loads((ROOT/'source/queue_jobs.json').read_text())
    jobs={x['name']:x for x in queue if x['status']=='done'}
    orig=json.loads((ROOT/'source/roi_motion_alg.json').read_text())
    requests=[json.loads(x) for x in (ROOT/'source/jobs_alg.jsonl').read_text().splitlines()]
    reqs={x['name']:x for x in requests};assert len(reqs)==18
    rows=[];source_error=[];first={};f0_diffs={}
    (ROOT/'sidecars').mkdir(exist_ok=True)
    for ident,k in sorted(key.items()):
        name=k['name'];j=jobs[name];p=j['params'];s=j['sidecar']; req=reqs[name]
        path=a.clips/(name+'.mp4');assert digest(path)==k['sha256']
        m=re.fullmatch(r'ms_(pend\d+)_rest(alg(?:0|4|8f4))_s(\d+)',name);assert m
        scene,arm,seed=m[1],m[2],int(m[3])
        assert j['endpoint']=='puget13' and j['endpoints']==['puget13']
        for field in ['width','height','num_frames','fps','steps','guidance','flow_shift','seed','negative_prompt','extra_params']:
            assert p[field]==req[field]==s[field],(name,field)
        assert j['prompt']==req['prompt']==s['prompt_text']
        assert j['image']==Path(req['image']).name==s['image']
        fr,fps=decode(path);assert fr.shape==(93,480,832,3) and fps==24
        if scene not in first:first[scene]=fr[0]
        f0_diffs[name]=int(np.abs(fr[0].astype(int)-first[scene].astype(int)).max())
        r={'id':ident,'name':name,'scene':scene,'arm':arm,'seed':seed,**k,
           'endpoint':j['endpoint'],'video_fps':fps,'video_shape':list(fr.shape),
           'roi':measure(fr,(240,420,90,300)),
           'content_roi':measure(fr,(218,614,0,480)),
           'codes':codes[ident]}
        if name in orig:
            source_error.extend(abs(r['roi'][f]-orig[name][f]) for f in ['motion_early','motion_late','motion_all'])
        rows.append(r)
        (ROOT/'sidecars'/f'{name}.json').write_text(json.dumps(s,indent=1)+'\n')
    assert len(rows)==14 and len(source_error)==12
    arms={}
    fields=['motion_early','motion_late','motion_all']
    for arm in ['alg0','alg4','alg8f4']:
        rr=[r for r in rows if r['arm']==arm]
        arms[arm]={'n_clips':len(rr),'seeds':sorted({r['seed'] for r in rr}),
            'codes':{f:dict(Counter(r['codes'][f] for r in rr)) for f in ['scene_preserved','rigid_swing','visible_motion','geometry_failure']},
            'clip_descriptive':{roi:{f:stats([r[roi][f] for r in rr]) for f in fields} for roi in ['roi','content_roi']},
            'seed_clustered':{roi:{f:stats([np.mean([r[roi][f] for r in rr if r['seed']==seed]) for seed in sorted({r['seed'] for r in rr})]) for f in fields} for roi in ['roi','content_roi']}}
    contrasts={}
    for arm,ref in [('alg4','alg0'),('alg8f4','alg0'),('alg8f4','alg4')]:
        aa={(r['scene'],r['seed']):r for r in rows if r['arm']==arm}
        bb={(r['scene'],r['seed']):r for r in rows if r['arm']==ref}
        common=sorted(aa.keys()&bb.keys()); seeds=sorted({s for _,s in common})
        contrasts[arm+'-'+ref]={'n_pairs':len(common),'seeds':seeds,
            'roi':{roi:{f:{'per_pair':[float(aa[k][roi][f]-bb[k][roi][f]) for k in common],
                'seed_clustered':stats([np.mean([aa[k][roi][f]-bb[k][roi][f] for k in common if k[1]==s]) for s in seeds])} for f in fields} for roi in ['roi','content_roi']}}
    out={'scope':'unvalidated image-change and one-coder qualitative diagnostic; no physical-rate or cause claim',
         'source_max_abs_error':max(source_error),'source_values_checked':len(source_error),
         'first_frame_max_pixel_difference_by_input':f0_diffs,
         'status_counts':dict(Counter(j['status'] for j in queue)),
         'arms':arms,'contrasts':contrasts,'rows':rows}
    (ROOT/'results.json').write_text(json.dumps(out,indent=1)+'\n')
    with (ROOT/'table.csv').open('w',newline='') as f:
        fields=['id','name','scene','arm','seed','motion_early','motion_late','motion_all','scene_preserved','rigid_swing','visible_motion','geometry_failure','queue_id','sha256']
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for r in rows:w.writerow({**{k:r[k] for k in ['id','name','scene','arm','seed','queue_id','sha256']},**{k:r['roi'][k] for k in ['motion_early','motion_late','motion_all']},**{k:r['codes'][k] for k in ['scene_preserved','rigid_swing','visible_motion','geometry_failure']}})
    print(json.dumps({'source_max_abs_error':out['source_max_abs_error'],'statuses':out['status_counts'],
        'codes':{a:v['codes'] for a,v in arms.items()},'seed_clustered_motion':{a:v['seed_clustered']['roi'] for a,v in arms.items()},
        's1_matched_contrasts':{c:v['roi']['roi']['motion_all'] for c,v in contrasts.items() if c.endswith('alg0')}},indent=1))

if __name__=='__main__':main()
