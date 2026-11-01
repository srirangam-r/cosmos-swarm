"""Unchanged planted-PASS tool + independently implemented real mocap references.
python analyze.py <original data dir> <output dir> [ids ...]
"""
from pathlib import Path
import sys,json,hashlib,cv2,numpy as np
from scipy.signal import find_peaks
repo=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(repo/'tools/trk_ballfall'))
import trk, measure_pend as mp
raw,out=map(Path,sys.argv[1:3]); out.mkdir(parents=True,exist_ok=True)
for p in ['qc','clips','traces']: (out/p).mkdir(exist_ok=True)
ids=list(map(int,sys.argv[3:])) or list(range(1,21))
def native(x):
 if isinstance(x,np.generic): return x.item()
 if isinstance(x,np.ndarray): return x.tolist()
 raise TypeError(type(x).__name__)
def dump(p,x): p.write_text(json.dumps(x,indent=2,default=native,allow_nan=False)+'\n')
def read_distinct(path):
 cap=cv2.VideoCapture(str(path)); hz=cap.get(cv2.CAP_PROP_FPS); diffs=[]; frames=[]; prev=None
 for k in range(300):
  ok,frame=cap.read()
  if not ok: break
  if prev is not None: diffs.append(float(np.abs(frame.astype(np.float32)-prev).mean()))
  prev=frame.astype(np.float32)
  lb=np.zeros((480,832,3),np.uint8);lb[6:474]=cv2.resize(frame,(832,468),interpolation=cv2.INTER_AREA);frames.append(lb)
 cap.release(); cut=0.1*np.median(diffs)
 keep=np.r_[0,1+np.flatnonzero(np.array(diffs)>=cut)]
 return np.array(frames)[keep],25.0,keep.tolist(),diffs,float(hz)
from reference import onset, cross_cycles, turning_cycles
res={}
for i in ids:
 F,hz,keep,diff,container_hz=read_distinct(raw/f'{i}.mp4'); assert len(F)>=186
 assert hz==25.0,(i,hz); W=F[93:186].astype(np.float32)
 r=mp.measure(W,hz,keep_track=True)
 mp.qc(W,r,str(out/f'qc/real_{i:02}.png'))
 tooltrack=r.pop('track')
 # Full-prefix centroid track supplies only onset synchronization, not reference period.
 B=trk.blobs(F.astype(np.float32)); good=[j for j,v in enumerate(B) if v]
 xy=np.array([[B[j][0],B[j][1]] for j in good]); dim=int(np.ptp(xy[:,1])>np.ptp(xy[:,0]))
 rel=good[mp.release(xy[:,dim],3.)]
 d=json.loads((raw/f'{i}.json').read_text()); hzmc=d['FPS']; p=np.column_stack([d['ball'][k] for k in ['x','y','z']])/1000
 t=np.arange(len(p))/hzmc; mean=p[:600].mean(0); eigval,eigvec=np.linalg.eigh(np.cov((p[:600]-mean).T)); axis=eigvec[:,np.argmax(eigval)]; x=(p-mean)@axis
 relmc=onset(x,.005); sync=t[relmc]-rel/hz
 lo=sync+(93+r['release_frame'])/hz;hi=sync+185/hz
 ref=cross_cycles(t,x,lo,hi); turn=turning_cycles(t,x,lo,hi,hzmc)
 refs={str(delta):cross_cycles(t,x,lo+delta/hz,hi+delta/hz) for delta in [-1,0,1]}
 full=cross_cycles(t,x,sync+93/hz,sync+185/hz)
 assert ref['period_s'] is not None and turn['period_s'] is not None
 ratio=r['period_s']/ref['period_s'];ratio_turn=r['period_s']/turn['period_s']
 record={'id':i,'tool':r,'reference_crossing':ref,'reference_turning':turn,'full_window_reference':full,'alignment_sensitivity':refs,'video_release_frame':rel,'mocap_release_frame':relmc,'mocap_fps':hzmc,'reference_window_s': [lo,hi],'sync_offset_s':float(sync),'ratio':ratio,'ratio_turning':ratio_turn,'ratio_zc':r['period_zc_s']/ref['period_s'],'covers_reference':r['period_ci95'][0]<=ref['period_s']<=r['period_ci95'][1], 'n_distinct_prefix':len(F),'fps':hz,'container_fps':container_hz}
 dump(out/f'traces/real_{i:02}.json',{'record':record,'tool_track':tooltrack,'prefix_centroids':[[j,B[j][0],B[j][1]] for j in good],'container_keep_indices':keep,'container_pair_mae':diff,'mocap_time_s':t[:600],'mocap_axis_m':x[:600]})
 writer=cv2.VideoWriter(str(out/f'clips/real_{i:02}.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),hz,(832,480))
 for frame in W.astype(np.uint8):writer.write(frame)
 writer.release()
 res[str(i)]=record;dump(out/'results.json',res)
 print(i,r['flag'],round(r['period_s'],6),round(ref['period_s'],6),round(turn['period_s'],6),round(ratio,6),rel,relmc,flush=True)
 del F,W,B
for name,records in [('all',list(res.values())),('ok',[r for r in res.values() if r['tool']['flag']=='ok'])]:
 summary={'n':len(records),'ids':[r['id'] for r in records]}
 for key in ['ratio','ratio_turning','ratio_zc']:
  a=np.array([r[key] for r in records]);summary[key]={'mean':a.mean(),'se':a.std(ddof=1)/np.sqrt(len(a)),'sd':a.std(ddof=1),'min':a.min(),'max':a.max(),'within_1pct':int((np.abs(a-1)<.01).sum()),'within_5pct':int((np.abs(a-1)<.05).sum())}
 summary['covers_reference']=sum(r['covers_reference'] for r in records)
 summary['max_align_period_change_s']=max(abs(r['alignment_sensitivity'][str(q)]['period_s']-r['reference_crossing']['period_s']) for r in records for q in [-1,1])
 dump(out/f'summary_{name}.json',summary);print(name,summary,flush=True)
