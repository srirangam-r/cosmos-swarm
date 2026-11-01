#!/usr/bin/env python3
import argparse, hashlib, json, math, random
from pathlib import Path
import cv2
import numpy as np


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(x):
    a=np.asarray(x,float)
    return {'n':len(a),'mean':float(a.mean()),'sample_sd':float(a.std(ddof=1)), 'se':float(a.std(ddof=1)/math.sqrt(len(a))), 'values':a.tolist()}
def read(p):
    c=cv2.VideoCapture(str(p)); fps=c.get(cv2.CAP_PROP_FPS); fs=[]
    while True:
        ok,f=c.read()
        if not ok: break
        fs.append(f)
    c.release(); return np.asarray(fs),fps

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--clips',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    kin=json.loads((a.source/'kinematics_results.json').read_text())
    out={'source_hashes':{f:sha(a.source/f) for f in ['kinematics_results.json','analyze_clips.py','summary_contrasts.json','jobs.jsonl']}, 'groups':{},'paired':{},'clips':{}}
    for scene in ['pend_mid','pend_rest','slope_wood','slope_plastic']:
        out['groups'][scene]={}
        field='decay_ratio' if scene=='pend_mid' else ('max_diff_f0' if scene=='pend_rest' else 'v_peak_mps')
        for arm in ['base','r','n']:
            vs=[kin[f't140_{scene}_{arm}_s{s}'][field] for s in [1,2,3]]
            out['groups'][scene][arm]={'field':field,**stats(vs)}
        out['paired'][scene]={arm:stats([kin[f't140_{scene}_r_s{s}'][field]-kin[f't140_{scene}_{arm}_s{s}'][field] for s in [1,2,3]]) for arm in ['base','n']}
    names=sorted(kin)
    for name in names:
        p=a.clips/(name+'.mp4'); side=json.loads(p.with_suffix('.json').read_text())
        sc,arm,seed=kin[name]['scene'],kin[name]['arm'],kin[name]['seed']
        frames,fps=read(p)
        z={'video_sha256':sha(p),'sidecar_sha256':sha(p.with_suffix('.json')), 'scene':sc,'arm':arm,'seed':seed, 'endpoint':side['endpoint'], 'decoded_frames':len(frames),'decoded_fps':fps,'decoded_shape':list(frames.shape[1:]),'settings':{k:side.get(k) for k in ['width','height','num_frames','fps','steps','guidance','flow_shift','negative_prompt']},'prompt':side['prompt_text']}
        if sc.startswith('pend'):
            gray=np.asarray([cv2.cvtColor(f,cv2.COLOR_BGR2GRAY) for f in frames],np.float64)
            diff=np.mean(np.abs(np.diff(gray,axis=0)),axis=(1,2))
            d0=np.mean(np.abs(gray-gray[0]),axis=(1,2))
            z.update(early=float(diff[:24].mean()),late=float(diff[60:92].mean()),ratio=float(diff[60:92].mean()/diff[:24].mean()),max_diff0=float(d0.max()),frame_mae=diff.tolist())
            z['saved_rounded_match']=(round(z['early'],2)==kin[name]['early_motion_energy'] and round(z['late'],2)==kin[name]['late_motion_energy'])
            if sc=='pend_rest': z['max_diff0_saved_rounded_match']=round(z['max_diff0'],2)==kin[name]['max_diff_f0']
        out['clips'][name]=z
    # Reproducible opaque IDs; saved key opened only after codes freeze.
    rest=[n for n in names if kin[n]['scene']=='pend_rest'];random.Random(172041).shuffle(rest)
    panels=a.out/'blind';panels.mkdir(exist_ok=True)
    key={}
    for j,name in enumerate(rest):
        ident=f'P{j+1:02}';key[ident]=name
        fs,_=read(a.clips/(name+'.mp4'))
        ids=list(range(0,89,8))+[92]
        rows=[]
        for start in range(0,len(ids),5):
            cells=[]
            for idx in ids[start:start+5]:
                crop=fs[idx,20:340,340:565].copy()
                cv2.putText(crop,f'{ident} f{idx}',(5,18),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,0,255),1)
                cells.append(crop)
            while len(cells)<5:cells.append(np.zeros_like(cells[0]))
            rows.append(np.hstack(cells))
        cv2.imwrite(str(panels/(ident+'.jpg')),np.vstack(rows))
    (a.out/'key.json').write_text(json.dumps(key,indent=2)+'\n')
    (a.out/'results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'n':len(out['clips']),'key_sha256':sha(a.out/'key.json'),'results_sha256':sha(a.out/'results.json'),'groups':out['groups'],'paired':out['paired']},indent=2))
if __name__=='__main__':main()
