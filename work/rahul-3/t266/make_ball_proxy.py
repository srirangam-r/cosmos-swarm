"""Task 266: 2D sim proxy for GAUGE ball drop/bounce from frame 0 (ro-3 #5315 recipe). Ball crop moves y=y0+g_eff*(t-t0)^2/2,
bounce e on the plank (y_floor), ppm 539.8 px/m (letterbox 832x480). Usage: make_ball_proxy.py out_dir"""
import cv2, numpy as np, sys, json
IMG='../../../assets/gauge_ball1_f0.png'; PPM=539.8; FPS=24; N=189
def build(g, e, out, c=(280,118), r=13, floor=340, hold=0.25):
    im=cv2.imread(IMG); H,W=im.shape[:2]; cx,cy=c
    m=np.zeros((H,W),np.uint8); cv2.circle(m,(cx,cy),r+3,255,-1)
    bg=cv2.inpaint(im,m,5,cv2.INPAINT_TELEA)
    a=np.zeros((H,W),np.uint8); cv2.circle(a,(cx,cy),r,255,-1); a=cv2.GaussianBlur(a,(0,0),1).astype(np.float32)/255
    ys=[]; y=0.; v=0.; t0=hold; dt=1/FPS/20; drop=floor-cy; ypx=0.; vpx=0.
    # integrate in px with g*PPM, sub-stepped
    ga=g*PPM; traj=[]
    t=0.
    for i in range(N*20):
        t=i*dt
        if i%20==0: traj.append(ypx)
        if t>=hold:
            vpx+=ga*dt; ypx+=vpx*dt
            if ypx>=drop and vpx>0: ypx=drop; vpx=-e*vpx
    vw=cv2.VideoWriter(out,cv2.VideoWriter_fourcc(*'mp4v'),FPS,(W,H))
    for k in range(N):
        dy=traj[k]; M=np.float32([[1,0,0],[0,1,dy]])
        sh=cv2.warpAffine(im,M,(W,H)); sa=cv2.warpAffine(a,M,(W,H))[...,None]
        vw.write((bg*(1-sa)+sh*sa).astype(np.uint8))
    vw.release(); return dict(g=g,e=e,drop_px=drop,t_impact=hold+(2*drop/ga)**.5)
if __name__=='__main__':
    o=sys.argv[1]; res={}
    for tag,g in [('g981',9.81),('g490',4.905)]:
        res[tag]=build(g,0.58,f'{o}/ball_{tag}.mp4')
    json.dump(res,open(f'{o}/proxies.json','w'),indent=1); print(res)
