#!/usr/bin/env python3
"""Fetch completed task191 movies and build reproducible masked review panels."""
import concurrent.futures, hashlib, json, random, sys, urllib.request
from pathlib import Path
import cv2
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
URL='http://100.111.167.68:8030'

def decode(path,expected_fps=24):
    cap=cv2.VideoCapture(str(path)); frames=[]
    while True:
        ok,frame=cap.read()
        if not ok: break
        frames.append(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
    fps=cap.get(cv2.CAP_PROP_FPS);cap.release()
    assert len(frames)==93 and frames[0].shape==(480,832,3)
    assert abs(fps-expected_fps)<1e-6
    return frames

def panel(frames,ident,indices,target,scene=False):
    w,h=(416,240) if scene else (550,400)
    cols=4;rows=(len(indices)+cols-1)//cols
    out=Image.new('RGB',(cols*w,32+rows*(h+22)),'white')
    d=ImageDraw.Draw(out);d.text((5,8),ident+(' full scene half-scale' if scene else ' native x100:650 y0:400'),fill='black')
    for i,k in enumerate(indices):
        x=i%cols*w;y=32+i//cols*(h+22)
        im=Image.fromarray(frames[k])
        im=im.resize((w,h)) if scene else im.crop((100,0,650,400))
        out.paste(im,(x,y+22));d.text((x+5,y+4),str(k),fill='black')
    out.save(target,quality=94)

def main():
    clips=Path(sys.argv[1]);clips.mkdir(parents=True,exist_ok=True)
    (ROOT/'qc').mkdir(exist_ok=True);(ROOT/'source').mkdir(exist_ok=True)
    sources=sorted((REPO/'work/kiro-1/t191/sidecars').glob('k191_*.json'));assert len(sources)==12
    def fetch(p):
        s=json.loads(p.read_text());target=clips/(s['name']+'.mp4')
        if not target.exists():
            target.write_bytes(urllib.request.urlopen(URL+'/jobs/'+s['queue_id']+'/mp4',timeout=100).read())
        (ROOT/'source'/p.name).write_bytes(p.read_bytes())
        return dict(name=s['name'],queue_id=s['queue_id'],sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: items=list(ex.map(fetch,sources))
    random.Random(19842413).shuffle(items)
    key={f'Q{i:02}':v for i,v in enumerate(items,1)}
    hidden=clips.parent/'key.json';hidden.write_text(json.dumps(key,indent=1)+'\n')
    for ident,v in key.items():
        frames=decode(clips/(v['name']+'.mp4'))
        panel(frames,ident,list(range(0,93,4)),ROOT/'qc'/f'{ident}_crop.jpg')
        panel(frames,ident,[0,4,12,24,48,72,84,92],ROOT/'qc'/f'{ident}_scene.jpg',True)
    # Followups selected during masked review, before key/gates were opened.
    dense={'Q01':36,'Q02':52,'Q05':24,'Q06':68,'Q07':44,'Q08':8,'Q11':4,'Q12':56}
    for ident,start in dense.items():
        frames=decode(clips/(key[ident]['name']+'.mp4'))
        panel(frames,ident,list(range(start,min(start+20,93))),ROOT/'qc'/f'{ident}_dense.jpg')
    for start in (1,5,9):
        out=Image.new('RGB',(1664,556*4),'white')
        for j,i in enumerate(range(start,start+4)):
            out.paste(Image.open(ROOT/'qc'/f'Q{i:02}_scene.jpg'),(0,556*j))
        out.save(ROOT/'qc'/f'scenes_{start}.jpg',quality=94)
    real=ROOT/'source/real10_review.mp4'
    if real.exists():
        frames=decode(real,25)
        panel(frames,'REAL10 known calibration control',list(range(0,93,4)),ROOT/'qc/real10_crop.jpg')
    print('Prepared12; key SHA256',hashlib.sha256(hidden.read_bytes()).hexdigest())

if __name__=='__main__': main()
