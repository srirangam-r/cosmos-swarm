THR=25
import cv2, numpy as np, json, sys
from scipy.optimize import least_squares
def load(p):
    c=cv2.VideoCapture(p); F=[]
    while True:
        ok,f=c.read()
        if not ok: break
        F.append(f.astype(np.float32))
    return np.array(F)
def blobs(F,thr=THR,mode='diff'):
    med=np.median(F,0); out=[]
    if mode=='ball':
        D=(np.abs(F[0]-F[-1]).max(2)>30).astype(np.uint8)
        D=cv2.dilate(cv2.morphologyEx(D,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),np.ones((7,7),np.uint8))
        n,l,st,cen=cv2.connectedComponentsWithStats(D)
        med=F[-1].copy()
        if n>1:
            ids=1+np.argsort(-st[1:,4])[:2]
            i=max(ids,key=lambda j:cen[j][1]); med[l==i]=F[0][l==i]
    for f in F:
        m=(np.abs(f-med).max(2)>(30 if mode=='ball' else thr)).astype(np.uint8)
        m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
        n,l,st,cen=cv2.connectedComponentsWithStats(m)
        if n<2: out.append(None); continue
        i=1+np.argmax(st[1:,4]); mk=(l==i).astype(np.uint8)
        cnt=cv2.findContours(mk,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0][0]
        (cx,cy),(w,h),a=cv2.minAreaRect(cnt)
        out.append((cen[i][0],cen[i][1],st[i,4],max(w,h),min(w,h)))
    return out
def ball(F,fps,D=0.10):
    B=blobs(F,mode='ball'); ok=[i for i,b in enumerate(B) if b]
    y=np.array([B[i][1] for i in ok]); t=np.array(ok)/fps
    A=np.array([B[i][2] for i in ok]); d=np.sqrt(4*np.median(np.sort(A)[-max(3,len(A)//3):])/np.pi)
    d=np.median([B[i][4] for i in ok]); s=D/d; Y=y*s
    # first impact: index of max y
    k=int(np.argmax(Y>=Y.max()-0.006))
    rev=np.where(Y[1:]<Y[:-1]-0.006)[0]
    if len(rev): k=min(k,int(rev[0]))
    n=max(k,6)
    # fit y=y0+0.5 g (t-t0)^2, v0=0, t0 free small
    n=max(k-1,5); c0=np.polyfit(t[:n],Y[:n],2)
    class S: pass
    sol=S(); sol.x=[np.polyval(c0,0),2*c0[0]]
    g=sol.x[1]; e=None
    if k<len(Y)-6:
        j=k+1
        while j<len(Y)-1 and Y[j+1]<Y[j]+0.003: j+=1
        tr=t[k:j+1];yr=Y[k:j+1]
        c=np.polyfit(tr,yr,2)
        if c[0]>0 and len(tr)>=4:
            ap=np.polyval(c,-c[1]/(2*c[0]))
            h0=Y[k]-sol.x[0]; hr=Y[k]-ap
            if h0>0 and hr>0: e=float(np.sqrt(hr/h0))
    return dict(g=float(g),e=e)
def incline(F,fps,L=0.12):
    B=blobs(F); ok=[i for i,b in enumerate(B) if b]
    P=np.array([[B[i][0],B[i][1]] for i in ok]); t=np.array(ok)/fps
    Ls=np.median([B[i][3] for i in ok]); s=L/Ls
    u=P[-1]-P[0]; u/=np.linalg.norm(u); x=(P-P[0])@u*s
    # truncate when stops
    n=len(x)
    for j in range(len(x)-3):
        if abs(x[j+3]-x[j])<0.002 and j>5: n=j+1;break
    r=lambda p: p[0]+0.5*p[1]*(t[:n]-p[2])**2*(t[:n]>p[2])-x[:n]
    sol=least_squares(r,[0,1.0,0.0],bounds=([-0.1,0,-0.2],[0.1,20,1.0]))
    return dict(a=float(abs(sol.x[1])))
def pend(F,fps):
    B=blobs(F); ok=[i for i,b in enumerate(B) if b]
    x=np.array([B[i][0] for i in ok]); t=np.array(ok)/fps
    x=x-x.mean(); best=None
    for T in np.linspace(0.8,3.5,28):
        def r(p): return p[0]*np.exp(-p[3]*t)*np.cos(2*np.pi*t/p[1]+p[2])+p[4]-x
        try: s=least_squares(r,[x.max(),T,0,0.0,0],bounds=([-1e4,0.4,-4,0,-1e3],[1e4,6,4,2,1e3]))
        except Exception: continue
        if best is None or s.cost<best.cost: best=s
    return dict(period_s=float(best.x[1]))
if __name__=='__main__':
    d=json.load(open(sys.argv[1])); est={}
    for c in d['clips']:
        F=load(f"{sys.argv[2]}/{c['clip_id']}.mp4"); p=c['params']
        try:
            if 'period_s' in p: r=pend(F,c['fps'])
            elif 'a' in p: r=incline(F,c['fps'])
            else: r=ball(F,c['fps'])
        except Exception as ex: print(c['clip_id'],'ERR',ex); continue
        est[c['clip_id']]={k:v for k,v in r.items() if k in p and v is not None}
        print(c['clip_id'],est[c['clip_id']])
    json.dump(est,open('est.json','w'))
