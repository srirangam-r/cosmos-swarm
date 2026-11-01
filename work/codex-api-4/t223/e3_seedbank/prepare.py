"""CPU-only fetch, masked native panels and opaque period records. No rankings.

Run after the git/board preregistration freeze. Do not open key.json or fits/
until native QC is frozen. Logs disclose operational counts, never fit values.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import sys
from urllib.request import urlopen
import cv2
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
BASE='http://100.111.167.68:8030'
sys.path.insert(0,str(REPO/'tools/trk_ballfall'))
import measure_pend as mp

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,obj): path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def finite(obj):
    if isinstance(obj,dict): return {k:finite(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)): return [finite(v) for v in obj]
    if isinstance(obj,np.ndarray): return finite(obj.tolist())
    if isinstance(obj,np.generic): return finite(obj.item())
    if isinstance(obj,float) and not np.isfinite(obj): return None
    return obj

def decode(path):
    cap=cv2.VideoCapture(str(path)); frames=[]
    fps=cap.get(cv2.CAP_PROP_FPS)
    try:
        if abs(fps-24)>1e-6: raise ValueError('Native fps mismatch')
        while True:
            ok,frame=cap.read()
            if not ok: break
            if frame.shape!=(480,832,3): raise ValueError('Native geometry mismatch')
            frames.append(frame)
        if len(frames)!=93: raise ValueError('Native frame count mismatch')
        return np.asarray(frames,dtype=np.float32),dict(frames=93,fps=float(fps),width=832,height=480)
    finally: cap.release()

def panel(frames,ident,indices,path,scene=False):
    w,h=(416,240) if scene else (550,400)
    out=Image.new('RGB',(4*w,32+((len(indices)+3)//4)*(h+22)),'white')
    draw=ImageDraw.Draw(out)
    draw.text((5,8),ident+(' full scene' if scene else ' native crop x100:650 y0:400'),fill='black')
    for j,k in enumerate(indices):
        x=j%4*w; y=32+j//4*(h+22)
        im=Image.fromarray(cv2.cvtColor(frames[k].astype(np.uint8),cv2.COLOR_BGR2RGB))
        im=im.resize((w,h)) if scene else im.crop((100,0,650,400))
        out.paste(im,(x,y+22));draw.text((x+4,y+4),str(k),fill='black')
    out.save(path,quality=94)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root',type=Path)
    ap.add_argument('--frozen',action='store_true',help='Reuse this operational snapshot without queue refresh')
    args=ap.parse_args(); root=args.root
    for sub in ['clips','panels','fits']: (root/sub).mkdir(parents=True,exist_ok=True)
    rows=json.loads((HERE/'design_only_queue.json').read_text())['runs']
    assert len(rows)==72
    references=json.loads((HERE/'references.json').read_text())
    for p,h in references['tool_hashes'].items(): assert sha(REPO/'tools/trk_ballfall'/p)==h
    saved=({r['id']:r for r in json.loads((root/'queue_records.json').read_text())} if args.frozen else None)
    def fetch(row):
        if saved is None:
            with urlopen(BASE+'/jobs/'+row['id'],timeout=30) as stream: actual=json.load(stream)
        else: actual=saved[row['id']]
        for k in ['id','name','owner','prompt','image','params','endpoints']: assert actual[k]==row[k],(row['name'],k)
        if row['endpoint'] is not None: assert actual['endpoint']==row['endpoint']
        assert actual['endpoint'] is None or actual['endpoint'] in row['endpoints']
        write(root/'clips'/(row['name']+'.queue.json'),actual)
        if actual['status']=='done':
            side=actual['sidecar']
            for k,v in row['params'].items(): assert side[k]==v,(row['name'],k)
            assert side['prompt_text']==row['prompt'] and side['image']==row['image']
            assert side['queue_id']==row['id'] and side['endpoint']==actual['endpoint']
            path=root/'clips'/(row['name']+'.mp4')
            if not path.exists():
                with urlopen(BASE+'/jobs/'+row['id']+'/mp4',timeout=120) as stream: data=stream.read()
                path.write_bytes(data)
        return actual
    with ThreadPoolExecutor(max_workers=4) as pool: actual=list(pool.map(fetch,rows))
    write(root/'queue_records.json',actual)
    print('Operational snapshot',dict(Counter(r['status'] for r in actual)),flush=True)
    items=list(zip(rows,actual));random.Random(22320261101).shuffle(items)
    key={f'Q{j:03}':dict(name=row['name'],run_id=row['id'],seed=row['params']['seed'],
        input=row['name'].split('_')[2]) for j,(row,rec) in enumerate(items,1)}
    write(root/'key.json',key)
    write(root/'masking.json',dict(key_sha256=sha(root/'key.json'),planned_ids=list(key),
        procedure='all72 shuffled, including unavailable; no outcome-based filtering',
        scope='partial masking: source scene may be recognizable; seed key withheld'))
    # Per-ID files support resuming completed records, with no refit if source
    # hashes and clip hash match. A truncated record causes an explicit error.
    by_name={r['name']:r for r in actual}; contracts={}
    for ident,entry in key.items():
        rec=by_name[entry['name']]; path=root/'clips'/(entry['name']+'.mp4')
        item=dict(opaque_id=ident,queue_status=rec['status'],
            queue_record_sha256=sha(root/'clips'/(entry['name']+'.queue.json')),
            executed_endpoint=rec['endpoint'])
        if rec['status']!='done':
            item.update(contract='missing',reason='queue status '+rec['status'])
        else:
            item['clip_sha256']=sha(path)
            try: frames,native=decode(path)
            except ValueError as exc: item.update(contract='invalid',reason=str(exc))
            else:
                item.update(contract='pass',native=native)
                panel(frames,ident,list(range(0,93,4)),root/'panels'/(ident+'_crop.jpg'))
                panel(frames,ident,[0,4,12,24,48,72,84,92],root/'panels'/(ident+'_scene.jpg'),True)
                dest=root/'fits'/(ident+'.json')
                if dest.exists():
                    previous=json.loads(dest.read_text())
                    assert previous['clip_sha256']==item['clip_sha256']
                    assert previous['tool_hashes']==references['tool_hashes']
                else:
                    try:
                        result=mp.measure(frames,24,tol=3.,nboot=200,seed=0,keep_track=True)
                        status='computed'
                    except Exception as exc:
                        result=dict(exception_type=type(exc).__name__,message=str(exc));status='exception'
                    write(dest,dict(opaque_id=ident,status=status,clip_sha256=item['clip_sha256'],
                        tool_hashes=references['tool_hashes'],settings=dict(fps=24,tol=3,nboot=200,seed=0),
                        result=finite(result)))
                del frames
        contracts[ident]=item
        write(root/'contracts.json',contracts)
        print('Prepared',len(contracts),'of72; period values and seed key withheld',flush=True)
    write(root/'prepare_summary.json',dict(planned=72,processed=len(contracts),
        native_contracts=dict(Counter(r['contract'] for r in contracts.values())),
        queue_status=dict(Counter(r['status'] for r in actual)),
        key_sha256=sha(root/'key.json'),design_sha256=sha(HERE/'design_only_queue.json'),
        references_sha256=sha(HERE/'references.json'),
        versions=dict(opencv=cv2.__version__,numpy=np.__version__),
        next='Freeze masked native QC before opening key or opaque fits; no ranking computed'))
    print('Preparation complete; no ranking or fit values disclosed',flush=True)

if __name__=='__main__': main()
