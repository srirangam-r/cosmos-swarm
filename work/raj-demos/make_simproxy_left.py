import cv2, numpy as np, sys, math, json
# first-frame-only simulated pendulum proxy: rotate rod+bob patch about axle
cfg={'pend10':dict(img='inputs/pend10_mid_f93.png',piv=(322,122),bot=(311,258)),
     'pend11':dict(img='inputs/pend11_mid_f81.png',piv=(324,122),bot=(327,256))}
g=9.81
def make(name,P,A=18.0,out=None,n=93,fps=24):
    c=cfg[name]; im=cv2.imread(c['img']); H,W=im.shape[:2]
    px,py=c['piv']; bx,by=c['bot']
    th_cur=math.degrees(math.atan2(px-bx,by-py))  # angle from vertical, +=bottom to left? sign convention: +=bottom shifts left
    L=math.hypot(bx-px,by-py)
    # rect region along axis, from 8px below pivot to 8px past bob, half-width 26
    ang=math.atan2(bx-px,by-py)
    ux,uy=math.sin(ang),math.cos(ang); vx,vy=uy,-ux
    pts=[]
    for s,w in [(8,-26),(8,26),(L+10,26),(L+10,-26)]:
        pts.append((px+ux*s+vx*w, py+uy*s+vy*w))
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[np.int32(pts)],255)
    bg=cv2.inpaint(im,cv2.dilate(m,np.ones((5,5),np.uint8)),5,cv2.INPAINT_TELEA)
    malpha=cv2.GaussianBlur(m,(0,0),2).astype(np.float32)[...,None]/255
    # phase: theta(t)=A sin(wt+phi), theta(0)=th_cur, moving toward 0 and beyond (velocity sign + to right => decreasing th)
    phi=math.asin(max(-1,min(1,th_cur/A))); w=2*math.pi/P
    vw=cv2.VideoWriter(out,cv2.VideoWriter_fourcc(*'mp4v'),fps,(W,H))
    for i in range(n):
        t=i/fps; th=A*math.sin(w*t+phi) # increasing: bob moves left first, as in real_10
        d=th-th_cur
        M=cv2.getRotationMatrix2D((px,py),-d,1.0) # positive angle in cv = ccw; bottom moves right for ccw? tune below
        rot=cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        ra=cv2.warpAffine(malpha,M,(W,H))[...,None] if malpha.ndim==2 else cv2.warpAffine(malpha[...,0],M,(W,H))[...,None]
        f=(bg*(1-ra)+rot*ra).astype(np.uint8)
        vw.write(f)
    vw.release()
    return dict(L_px=L,th_cur=th_cur,P=P,A=A)
if __name__=='__main__':
    # physical period: L_m = 0.35 m effective (guess from geometry; real P=1.18 -> 0.346 m)
    Pphys=2*math.pi*math.sqrt(0.35/g)
    res={}
    for n in cfg:
        for tag,P in [('phys',Pphys),('x17',Pphys*1.7)]:
            res[f'{n}_{tag}']=make(n,P,out=f'simproxy/sp_{n}_{tag}.mp4')
    print(Pphys); print(json.dumps(res,indent=1))
