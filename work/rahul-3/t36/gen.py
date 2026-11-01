# independent synthetic multi-bounce generator (rahul-3, task 36). seed 777.
import numpy as np, cv2, json, sys, os
rng=np.random.default_rng(777); W,H,FPS,N=832,480,24,93
out='clips'; os.makedirs(out,exist_ok=True); truth={}
floor=400
def render(path,xs,ys,r,bg,noise,shadow):
    vw=cv2.VideoWriter(path,cv2.VideoWriter_fourcc(*'mp4v'),FPS,(W,H))
    for i in range(N):
        f=bg.copy()
        if shadow: cv2.ellipse(f,(int(xs[i]),floor+int(r[i])+4),(int(r[i]*1.2),4),0,0,360,(60,60,60),-1)
        cv2.circle(f,(int(round(xs[i]*8)),int(round(ys[i]*8))) if False else (int(round(xs[i])),int(round(ys[i]))),int(round(r[i])),(40,60,200),-1,cv2.LINE_AA)
        f=np.clip(f.astype(np.float32)+rng.normal(0,noise,f.shape),0,255).astype(np.uint8)
        vw.write(f)
    vw.release()
for k in range(30):
    e=[0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.97][k%8]; g=9.81; mpp=rng.uniform(0.0035,0.0065) # m/px
    h0=rng.uniform(1.0,1.6) # drop height m
    ga=g/mpp/FPS**2*0 + g/mpp  # px/s^2
    hold=rng.choice([0,0,6]); drift=(k//8)%2==1
    t=np.arange(N)/FPS-hold/FPS
    # simulate event-based
    y=np.zeros(N); v=0; yy=floor-h0/mpp; vel=0; dt=1/FPS/50; ts=[]; tt=-hold/FPS
    ys=[]
    sub=50; cur=yy; vv=0; imp=[]
    for i in range(N):
        for s in range(sub):
            tt+=1/FPS/sub
            if tt<0: continue
            vv+=ga/1.0*(1/FPS/sub); cur+=vv/1.0*(1/FPS/sub)
            if cur>=floor and vv>0:
                cur=floor-(cur-floor); vv=-vv*e; imp.append(tt)
                if abs(vv)<20: vv=0
        ys.append(cur)
    ys=np.array(ys)
    r=np.full(N,0.05/mpp)
    if drift: r=r*np.linspace(1.0,1.25,N)
    xs=300+rng.uniform(-30,30)+np.linspace(0,rng.uniform(-40,40),N)
    ys_c=ys-r  # floor contact
    bg=np.full((H,W,3),rng.integers(150,210),np.uint8); cv2.line(bg,(0,floor+int(r[0])+1),(W,floor+int(r[0])+1),(90,90,90),2)
    p=f'{out}/c{k:02d}.mp4'
    render(p,xs,ys_c+0,r,bg,rng.uniform(1,4),k%3==0)
    imp=np.array(imp); T=np.diff(imp)
    truth[f'c{k:02d}']=dict(e=e,g=g,mpp=mpp,diam=0.10,hold=int(hold),drift=bool(drift),n_imp=len(imp),T=T.tolist(),imp=imp.tolist())
json.dump(truth,open('truth.json','w'),indent=1)
