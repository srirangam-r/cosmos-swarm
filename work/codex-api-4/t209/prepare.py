#!/usr/bin/env python3
"""Mask shared original clips, validate contracts, and build fixed native panels."""
import argparse,hashlib,json,random,shutil
from pathlib import Path
import cv2
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]

def decode(path):
    cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS);frames=[]
    while True:
        ok,im=cap.read()
        if not ok:break
        frames.append(cv2.cvtColor(im,cv2.COLOR_BGR2RGB))
    cap.release()
    assert len(frames)==93 and frames[0].shape==(480,832,3),(path,len(frames))
    assert abs(fps-24)<1e-8
    return frames

def sheet(frames,ident,indices,path,scene=False):
    w,h=(416,240) if scene else (320,330)
    out=Image.new('RGB',(4*w,30+((len(indices)+3)//4)*(h+20)),'white');d=ImageDraw.Draw(out)
    d.text((5,6),ident+(' scene half scale' if scene else ' native x140:460 y80:410'),fill='black')
    for j,i in enumerate(indices):
        x=j%4*w;y=30+j//4*(h+20);im=Image.fromarray(frames[i])
        im=im.resize((w,h)) if scene else im.crop((140,80,460,410))
        out.paste(im,(x,y+20));d.text((x+4,y+3),str(i),fill='black')
    out.save(path,quality=95)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('hidden');args=ap.parse_args()
    src=Path(args.source);hidden=Path(args.hidden);hidden.mkdir(parents=True,exist_ok=True)
    names=[j['name'] for j in map(json.loads,(ROOT/'source/jobs_v8.jsonl').read_text().splitlines())]
    names += [f'cause5_{a}_ball1_fps24_93f_s{s}' for s in (3,5) for a in ('F','QT')]
    paths={p.stem:p for p in src.rglob('*.mp4')}
    missing=[n for n in names if n not in paths];assert not missing,missing
    random.Random(2094315).shuffle(names);key={};(ROOT/'qc').mkdir(exist_ok=True)
    for i,name in enumerate(names,1):
        ident=f'Q{i:02}';p=paths[name];frames=decode(p)
        key[ident]=dict(name=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_relative=str(p.relative_to(src)))
        sheet(frames,ident,list(range(0,93,3)),ROOT/'qc'/f'{ident}_stride.jpg')
        sheet(frames,ident,list(range(80,93)),ROOT/'qc'/f'{ident}_late.jpg')
        sheet(frames,ident,[0,12,24,48,72,84,92],ROOT/'qc'/f'{ident}_scene.jpg',True)
    # Display derivatives used during the original masked review.
    for start in range(1,15,3):
        ims=[Image.open(ROOT/'qc'/f'Q{i:02}_scene.jpg') for i in range(start,min(start+3,15))]
        out=Image.new('RGB',(1664,550*len(ims)),'white')
        for j,im in enumerate(ims):out.paste(im,(0,j*550))
        out.save(ROOT/'qc'/f'scenes_{start:02}.jpg',quality=95)
    im=Image.open(ROOT/'qc/Q05_stride.jpg')
    for j,(lo,hi) in enumerate([(0,1430),(1430,2830)]):im.crop((0,lo,1280,hi)).save(ROOT/'qc'/f'Q05_part{j}.png')
    Image.open(ROOT/'qc/Q13_late.jpg').save(ROOT/'qc/Q13_late.png')
    (hidden/'key.json').write_text(json.dumps(key,indent=1)+'\n')
    print('14 movies validated and panels prepared; hidden key SHA256',hashlib.sha256((hidden/'key.json').read_bytes()).hexdigest())

if __name__=='__main__':main()
