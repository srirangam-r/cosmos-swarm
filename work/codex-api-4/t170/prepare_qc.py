#!/usr/bin/env python3
"""Generate masked native-scale panels, without computing outcome metrics."""
import cv2,hashlib,json,secrets,sys
from pathlib import Path
import numpy as np

clips,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
paths=sorted(clips.glob('t170_*.mp4'));assert len(paths)==24
secrets.SystemRandom().shuffle(paths)
key={}
for k,p in enumerate(paths,1):
    label=f'C{k:02d}';key[label]=p.stem
    cap=cv2.VideoCapture(str(p));frames=[]
    while True:
        ok,f=cap.read()
        if not ok:break
        frames.append(f)
    cap.release();assert len(frames)==93
    for suffix,indices,cols in [('sparse',range(48,93,4),4),('dense',range(72,93),7)]:
        tiles=[]
        for i in indices:
            # Native pixels; corridor plus surrounding context. Labels outside video.
            tile=np.full((350,300,3),255,np.uint8)
            tile[25:,5:295]=frames[i][100:425,190:480]
            cv2.putText(tile,f'{label} f{i}',(5,19),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,0,0),1)
            tiles.append(tile)
        grid=np.concatenate([np.concatenate(tiles[i:i+cols],axis=1) for i in range(0,len(tiles),cols)],axis=0)
        cv2.imwrite(str(out/f'{label}_{suffix}.jpg'),grid,[cv2.IMWRITE_JPEG_QUALITY,92])
(out/'PRIVATE_KEY.json').write_text(json.dumps(key,indent=1)+'\n')
print('key SHA256',hashlib.sha256((out/'PRIVATE_KEY.json').read_bytes()).hexdigest())
print('24 sparse and dense panels prepared; key remains unopened')
