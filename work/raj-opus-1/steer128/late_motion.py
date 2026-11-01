# ro-1's late-motion proxy (cause_v5/analyze.py): mean |grey frame diff| in ball corridor x220:360,y130:360; plus strips
import cv2, numpy as np, glob, json, sys, os
from PIL import Image, ImageDraw
pat=sys.argv[1]; outj=sys.argv[2]
res={}; rows=[]
for f in sorted(glob.glob(pat)):
    k=os.path.basename(f)[:-4]
    cap=cv2.VideoCapture(f); fr=[]
    while True:
        ok,x=cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(x,cv2.COLOR_BGR2RGB))
    g=np.stack([np.asarray(Image.fromarray(x).convert('L')).astype(np.float32)[130:360,220:360] for x in fr])
    d=np.abs(np.diff(g,axis=0)).mean((1,2))
    res[k]=dict(early=round(float(d[1:45].mean()),3),late=round(float(d[45:].mean()),3),last20=round(float(d[-20:].mean()),3),n=len(fr))
    ims=[Image.fromarray(fr[i][100:380,180:400]).resize((88,112)) for i in range(0,len(fr),6)]
    row=Image.new('RGB',(88*len(ims)+200,112)); dr=ImageDraw.Draw(row); dr.text((2,50),k[-28:],fill=(255,255,0))
    for j,im in enumerate(ims): row.paste(im,(200+88*j,0))
    rows.append(row)
json.dump(res,open(outj,'w'),indent=1)
for k,v in res.items(): print(k,v)
if rows:
    W=max(r.width for r in rows); sheet=Image.new('RGB',(W,112*len(rows)))
    for i,r in enumerate(rows): sheet.paste(r,(0,112*i))
    sheet.save(outj.replace('.json','_strips.jpg'),quality=75)
