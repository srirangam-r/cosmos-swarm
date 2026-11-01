#!/usr/bin/env python3
"""Join frozen QC, audit metadata, recompute author proxy, verify exact controls."""
import argparse,csv,hashlib,json,math,re,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
sys.path.insert(0,str(ROOT));from prepare import decode

def main():
 ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('--key',default=str(ROOT/'key.json'));a=ap.parse_args()
 src=Path(a.source);key=json.loads(Path(a.key).read_text());codes={r['id']:r for r in csv.DictReader((ROOT/'codes_frozen.csv').open())}
 paths={p.stem:p for p in src.rglob('*.mp4')}
 jobs={j['name']:j for j in map(json.loads,(ROOT/'source/jobs_v8.jsonl').read_text().splitlines())}
 author={r['clip']:r for r in csv.DictReader((ROOT/'source/author_codes_v5.csv').open())}
 author.update({r['clip']:r for r in csv.DictReader((ROOT/'source/author_codes_v8.csv').open())})
 checks=[];rows=[];cache={};f0hashes=[]
 for ident,item in key.items():
  name=item['name'];p=paths[name];rawhash=hashlib.sha256(p.read_bytes()).hexdigest();assert rawhash==item['sha256'];checks.append(ident+' original hash')
  frames=np.stack(decode(p));cache[name]=frames
  f0hashes.append(hashlib.sha256(frames[0].tobytes()).hexdigest())
  gray=np.stack([np.asarray(Image.fromarray(f).convert('L'),dtype=np.float32)[130:360,220:360] for f in frames]);delta=np.abs(np.diff(gray,axis=0)).mean((1,2))
  sidepath=(ROOT/'source/sidecars')/(name+'.json');side=json.loads(sidepath.read_text())
  assert side['name']==name and side['num_frames']==93 and side['width']==832 and side['height']==480 and side['fps']==24
  assert side['steps']==35 and side['guidance']==6.0 and side['flow_shift']==10.0 and side['negative_prompt'] is None
  checks.append(ident+' declared request/movie contract')
  seed=side['seed'];arm=side['arm'];last20=float(delta[-20:].mean())
  author_rest=author[name].get('settled_by_f92',author[name].get('settles_by_f92')) if name in author else None
  author_value=float(author[name]['last20']) if name in author and 'last20' in author[name] else None
  if name in jobs:
   job=jobs[name]
   for field in ('seed','prompt','negative_prompt','fps','steps','guidance','flow_shift','width','height','num_frames'):
    assert side[field]==job[field],(name,field)
   assert side['extra_params']['prompt_switch']==job['extra_params']['prompt_switch']
   checks.append(ident+' requested window contract')
   assert abs(last20-author_value)<.011,(name,last20,author_value)
   checks.append(ident+' author proxy to published0.01 precision')
  row=dict(codes[ident],name=name,seed=seed,arm=arm,author_rest=author_rest,last20=last20,author_last20=author_value,sha256=rawhash,decoded_rgb_sha256=hashlib.sha256(frames.tobytes()).hexdigest(),frame0_sha256=f0hashes[-1],sidecar_sha256=hashlib.sha256(sidepath.read_bytes()).hexdigest())
  rows.append(row)
 assert len(set(f0hashes))==1;checks.append('all14 decoded first frames identical')
 identity=[]
 for seed in (3,5):
  n1=f'v8_SWfull_ball1_fps24_93f_s{seed}';n2=f'cause5_QT_ball1_fps24_93f_s{seed}'
  assert np.array_equal(cache[n1],cache[n2]);assert paths[n1].read_bytes()==paths[n2].read_bytes()
  identity.append(dict(seed=seed,decoded_maxabs=0,original_mp4_byte_identity=True));checks.append(f'seed{seed} full/QT byte+decoded identity')
 counts={}
 for arm in ['F','QT','SWfull','SWe3','SWe7','SWl7','SWl17']:
  rr=[r for r in rows if r['arm']==arm];counts[arm]={k:sum(r['late_rest']==k for r in rr) for k in 'YNU'};counts[arm]['n']=len(rr)
  counts[arm]['source_rest_Y']=sum(r['author_rest']=='Y' for r in rr)
 paired=[]
 for arm in ['SWfull','SWe3','SWe7','SWl7','SWl17','QT']:
  ds=[]
  for seed in (3,5):
   rr=next(r for r in rows if r['arm']==arm and r['seed']==seed);base=next(r for r in rows if r['arm']=='F' and r['seed']==seed);ds.append(rr['last20']-base['last20'])
  paired.append(dict(arm=arm,delta_last20_vs_F_by_seed=ds,mean=float(np.mean(ds)),seed_se=float(np.std(ds,ddof=1)/np.sqrt(2))))
 out=dict(rows=rows,counts=counts,identity=identity,paired_pixel_proxy=paired,checks=checks,n_checks=len(checks),versions=dict(python=sys.version.split()[0],opencv=cv2.__version__,numpy=np.__version__),scope='Unvalidated pixel proxy and partially masked visual QC; repeated identities are controls, not extra independent seeds. No physical parameter, cause timing or NVIDIA-scoreboard validation.')
 (ROOT/'results.json').write_text(json.dumps(out,indent=2)+'\n')
 with (ROOT/'table.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 print(json.dumps(dict(counts=counts,identity=identity,checks=len(checks),max_proxy_error=max(abs(r['last20']-r['author_last20']) for r in rows if r['author_last20'] is not None)),indent=2))

if __name__=='__main__':main()
