#!/usr/bin/env python3
"""Fetch only completed shared-queue ALG jobs and prepare masked review panels."""
import hashlib, json, random, sys, urllib.request
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

URL = 'http://100.111.167.68:8030'
ROOT = Path(__file__).resolve().parent

def main():
    clips = Path(sys.argv[1]); clips.mkdir(parents=True, exist_ok=True)
    jobs = json.load(urllib.request.urlopen(URL+'/jobs?owner=ro-3'))['jobs']
    selected = [j for j in jobs if 'restalg' in j['name'] and j['status']=='done']
    assert len(selected)==14
    assert len({j['name'] for j in selected})==14
    (ROOT/'source').mkdir(exist_ok=True)
    (ROOT/'source/queue_jobs.json').write_text(json.dumps(
        [j for j in jobs if 'restalg' in j['name']], indent=1)+'\n')
    for j in selected:
        p = clips/(j['name']+'.mp4')
        if not p.exists():
            p.write_bytes(urllib.request.urlopen(URL+'/jobs/'+j['id']+'/mp4',timeout=120).read())
    rng=random.Random(47100891); rng.shuffle(selected)
    key={f'A{i:02}':{'name':j['name'],'queue_id':j['id'],
         'sha256':hashlib.sha256((clips/(j['name']+'.mp4')).read_bytes()).hexdigest()}
         for i,j in enumerate(selected,1)}
    hidden=clips.parent/'key.json'; hidden.write_text(json.dumps(key,indent=1)+'\n')
    (ROOT/'qc').mkdir(exist_ok=True)
    for ident,item in key.items():
        cap=cv2.VideoCapture(str(clips/(item['name']+'.mp4'))); frames=[]
        while True:
            ok,f=cap.read()
            if not ok: break
            frames.append(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
        cap.release(); assert len(frames)==93
        canvas=Image.new('RGB',(6*396,4*344+36),'white'); d=ImageDraw.Draw(canvas)
        d.text((8,8),ident+' native crop x218:614,y30:350; stride 4',fill='black')
        for q,fidx in enumerate(range(0,93,4)):
            x=(q%6)*396; y=36+(q//6)*344
            canvas.paste(Image.fromarray(frames[fidx][30:350,218:614]),(x,y+24))
            d.text((x+5,y+5),str(fidx),fill='black')
        canvas.save(ROOT/'qc'/f'{ident}_crop.jpg',quality=92)
        canvas=Image.new('RGB',(4*416,2*264+36),'white');d=ImageDraw.Draw(canvas)
        d.text((8,8),ident+' full scene',fill='black')
        for q,fidx in enumerate([0,4,12,24,48,72,84,92]):
            x=q%4*416;y=36+q//4*264
            canvas.paste(Image.fromarray(frames[fidx]).resize((416,240)),(x,y+24))
            d.text((x+5,y+5),str(fidx),fill='black')
        canvas.save(ROOT/'qc'/f'{ident}_scene.jpg',quality=92)
    print('Fetched/prepared',len(key),'existing clips; key SHA256',hashlib.sha256(hidden.read_bytes()).hexdigest())

if __name__=='__main__': main()
