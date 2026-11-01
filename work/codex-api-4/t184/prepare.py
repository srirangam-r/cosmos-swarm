#!/usr/bin/env python3
"""Fetch exact existing published queue ids and build masked native review panels."""
import hashlib,json,random,sys,urllib.request
from pathlib import Path
import cv2
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
URL='http://100.111.167.68:8030'

def panel(frames,ident,indices,path,scene=False):
    w,h=(416,240) if scene else (390,305)
    cols=4 if scene else 6; rows=(len(indices)+cols-1)//cols
    canvas=Image.new('RGB',(cols*w,rows*(h+24)+32),'white');d=ImageDraw.Draw(canvas)
    d.text((5,8),ident+(' scene' if scene else ' native x130:520,y25:330'),fill='black')
    for i,k in enumerate(indices):
        x=i%cols*w;y=32+i//cols*(h+24)
        f=frames[k]; im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
        im=im.resize((w,h)) if scene else im.crop((130,25,520,330))
        canvas.paste(im,(x,y+24));d.text((x+5,y+5),str(k),fill='black')
    canvas.save(path,quality=94)

def main():
    clips=Path(sys.argv[1]);clips.mkdir(parents=True,exist_ok=True)
    files=sorted((REPO/'work/kiro-1/t175/sidecars').glob('k175_pend_mid_*.json'))
    assert len(files)==12
    items=[]
    (ROOT/'source').mkdir(exist_ok=True);(ROOT/'qc').mkdir(exist_ok=True)
    for p in files:
        s=json.loads(p.read_text()); target=clips/(s['name']+'.mp4')
        if not target.exists():
            target.write_bytes(urllib.request.urlopen(URL+'/jobs/'+s['queue_id']+'/mp4',timeout=120).read())
        (ROOT/'source'/p.name).write_bytes(p.read_bytes())
        items.append({'name':s['name'],'queue_id':s['queue_id'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    random.Random(18411753).shuffle(items)
    key={f'Q{i:02}':v for i,v in enumerate(items,1)}
    hidden=clips.parent/'key.json';hidden.write_text(json.dumps(key,indent=1)+'\n')
    for ident,v in key.items():
        c=cv2.VideoCapture(str(clips/(v['name']+'.mp4')));f=[]
        while True:
            ok,a=c.read()
            if not ok:break
            f.append(a)
        c.release();assert len(f)==93
        panel(f,ident,list(range(0,93,4)),ROOT/'qc'/f'{ident}_crop.jpg')
        panel(f,ident,[0,4,12,24,48,72,84,92],ROOT/'qc'/f'{ident}_scene.jpg',True)
    print('Prepared',len(key),'clips; key SHA256',hashlib.sha256(hidden.read_bytes()).hexdigest())

if __name__=='__main__':main()
