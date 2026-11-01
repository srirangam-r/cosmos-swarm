"""Task 139 input edits v3 (texture copy, no generative model).
A = whole Franka removed (hand, fingers, cables, arm, base, LED glow on the table). G = hand + fingers + strip removed, arm kept.
Curtain: rectangle copied from the clean right curtain (x+290, y), mean/std-matched to the surrounding curtain, feathered.
Base area: per pixel by table geometry: above wood edge yw(x)=266+0.153(x-300) -> curtain (x+290,y);
wood strip [yw,yo], yo(x)=286+0.22(x-300) -> same relative depth t at x+115; below yo (optical table) -> (x+80, y+18).
The ball disk (280,116) r=12 is never touched."""
import cv2, numpy as np, hashlib, json
BALL=(280,116); R=12
yw=lambda x:266+0.153*(x-300); yo=lambda x:286+0.22*(x-300)
def build(im,arm):
    H,W=im.shape[:2]; f=im.astype(np.float32); src=f.copy(); m=np.zeros((H,W),np.uint8)
    if arm=='A':
        cv2.rectangle(m,(226,0),(490,236),255,-1)          # curtain block incl. arm, hand, fingers, cables
        base=np.zeros_like(m); cv2.rectangle(base,(374,236),(490,312),255,-1); cv2.rectangle(base,(414,300),(466,340),255,-1)
        m|=base
    else:
        cv2.rectangle(m,(228,36),(348,106),255,-1); cv2.rectangle(m,(256,90),(330,170),255,-1); cv2.rectangle(m,(278,126),(304,202),255,-1)
    cv2.circle(m,BALL,R,0,-1)
    ys,xs=np.nonzero(m)
    sx=xs+290; sy=ys.copy()
    low=ys>=236
    if low.any():
        x=xs[low].astype(np.float32); y=ys[low].astype(np.float32)
        a_w=yw(x); a_o=yo(x)
        tx=np.where(y<a_w,x+290,np.where(y<=a_o,x+115,x+80))
        t=(y-a_w)/(a_o-a_w)
        ty=np.where(y<a_w,y,np.where(y<=a_o,yw(x+115)+t*(yo(x+115)-yw(x+115)),y+18))
        sx[low]=np.round(tx).astype(int); sy[low]=np.round(ty).astype(int)
    sx=np.clip(sx,0,W-1); sy=np.clip(sy,0,H-1)
    src[ys,xs]=f[sy,sx]
    # brightness match for the curtain part: copied curtain vs a ring of original curtain around the block (dark pixels only)
    cm=np.zeros_like(m); cm[(m>0)]=255; cm[236:,:]=0
    ring=cv2.dilate(cm,np.ones((25,25),np.uint8)); ring[cm>0]=0; ring[236:,:]=0
    g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    rsel=(ring>0)&(g<60); csel=(cm>0)
    for c in range(3):
        mu_r,sd_r=f[...,c][rsel].mean(),f[...,c][rsel].std()+1e-3
        mu_s,sd_s=src[...,c][csel].mean(),src[...,c][csel].std()+1e-3
        src[...,c][csel]=(src[...,c][csel]-mu_s)*min(sd_r/sd_s,1.5)+mu_r
    a=cv2.GaussianBlur((m>0).astype(np.float32),(15,15),0); a[cv2.erode(m,np.ones((7,7),np.uint8))>0]=1
    bd=np.zeros_like(m); cv2.circle(bd,BALL,R,255,-1); a[bd>0]=0
    out=src*a[...,None]+f*(1-a[...,None])
    return np.clip(out,0,255).astype(np.uint8),m
out={}
for name,srcp in [('ball1','../cosmos-swarm/work/raj-1/gauge_ball/gauge_ball1_f0_832x480.png'),('ball2','../cosmos-swarm/work/raj-2/task9_duration/gauge_ball2_f0_832x480.png')]:
    im=cv2.imread(srcp)
    for arm in ('A','G'):
        ed,m=build(im,arm); fn=f'inputs/{name}_{arm}.png'; cv2.imwrite(fn,ed); cv2.imwrite(f'inputs/{name}_{arm}_mask.png',m)
        out[fn]=dict(src=srcp,mask=fn.replace('.png','_mask.png'),masked_px=int((m>0).sum()),sha256=hashlib.sha256(open(fn,'rb').read()).hexdigest())
    fn=f'inputs/{name}_O.png'; cv2.imwrite(fn,im); out[fn]=dict(src=srcp,sha256=hashlib.sha256(open(fn,'rb').read()).hexdigest())
json.dump(out,open('inputs/edits.json','w'),indent=1)
o,a,b=[cv2.imread(f'inputs/ball1_{k}.png') for k in 'OAG']
cv2.imwrite('preview.jpg',np.vstack([np.hstack([o,a]),np.hstack([b,cv2.imread('inputs/ball2_A.png')])]))
z=lambda x:cv2.resize(x[60:180,220:340],None,fx=3,fy=3,interpolation=cv2.INTER_NEAREST)
cv2.imwrite('preview_ball.jpg',np.hstack([z(o),z(a),z(b)]))
