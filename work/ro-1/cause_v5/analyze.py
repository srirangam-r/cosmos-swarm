# ro-1 task 22 cause v5/v6: late-motion proxy (mean |frame diff| in ball corridor, last 20 f) + eye strips
import av, numpy as np, glob, os, json, sys
from PIL import Image, ImageDraw
R='/home/rohith/swarm-work/ro-1/'
clips = {}
for s in (1,2): clips[f'b1_F_s{s}']=R+f'fps_sweep/out/ball_F_ball1_fps24_93f_s{s}.mp4'; clips[f'b1_QT_s{s}']=R+f'fps_sweep/out_cause/cause_QT_ball1_fps24_93f_s{s}.mp4'
for s in (3,4,5):
    for a in ('F','QT','QS'): clips[f'b1_{a}_s{s}']=R+f'fps_sweep/out_cause5/cause5_{a}_ball1_fps24_93f_s{s}.mp4'
for s in (1,2): clips[f'b2_F_s{s}']=R+f'fps_sweep/out/ball_F_ball2_fps24_93f_s{s}.mp4'
clips['b2_F_s3']=R+'fps_sweep/out_cause6/cause6_F_ball2_fps24_93f_s3.mp4'
for s in (1,2,3): clips[f'b2_QT_s{s}']=R+f'fps_sweep/out_cause6/cause6_QT_ball2_fps24_93f_s{s}.mp4'
clips['b1_REAL']=R+'real_ref/real_ball1_dd32_93f.mp4'
res={}; rows=[]
for k,f in clips.items():
    if not os.path.exists(f): continue
    fr=[x.to_ndarray(format='rgb24') for x in av.open(f).decode(video=0)]
    g=np.stack([np.asarray(Image.fromarray(x).convert('L')).astype(np.float32)[130:360,220:360] for x in fr])
    d=np.abs(np.diff(g,axis=0)).mean((1,2))
    res[k]=dict(early=round(float(d[1:45].mean()),3),late=round(float(d[45:].mean()),3),last20=round(float(d[-20:].mean()),3),n=len(fr))
    ims=[Image.fromarray(fr[i][100:380,180:400]).resize((110,140)) for i in range(0,len(fr),6)]
    row=Image.new('RGB',(110*len(ims)+90,140)); dr=ImageDraw.Draw(row); dr.text((2,60),k,fill=(255,255,0))
    for j,im in enumerate(ims): row.paste(im,(90+110*j,0))
    rows.append(row)
for k,v in res.items(): print(k,v)
json.dump(res,open(R+'cause_v5/late_motion_v56.json','w'),indent=1)
W=max(r.width for r in rows); sheet=Image.new('RGB',(W,140*len(rows)))
for i,r in enumerate(rows): sheet.paste(r,(0,140*i))
sheet.save(R+'cause_v5/strips_all.jpg',quality=80); print('frames every 6: 0,6,...')
