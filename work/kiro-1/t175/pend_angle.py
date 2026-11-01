"""Rod angle from vertical about the axle pivot, from wood-coloured pixels in an annulus (r 35-95 px).
Axle bar band |dy|<10 excluded, so angles beyond ~80 deg read as missing/saturated. Unvalidated."""
import cv2,numpy as np,json,glob,sys
PX,PY=318,120
yy,xx=np.mgrid[0:480,0:832]; dx=xx-PX; dy=yy-PY; rr=np.hypot(dx,dy)
ann=(rr>35)&(rr<95)&(dy>10)
def angles(p):
    cap=cv2.VideoCapture(p); out=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        h=cv2.cvtColor(f,cv2.COLOR_BGR2HSV)
        m=ann&(h[...,0]>=5)&(h[...,0]<=30)&(h[...,1]>50)&(h[...,2]>90)
        n=m.sum()
        out.append(float(np.degrees(np.arctan2(dx[m].mean(),dy[m].mean()))) if n>=15 else None)
    return out
res={}
for p in sorted(glob.glob('clips/k175_pend_mid_*.mp4')):
    a=angles(p); nm=p.split('/')[-1][:-4]
    def amp(lo,hi):
        v=[x for x in a[lo:hi] if x is not None]; miss=(hi-lo)-len(v)
        return (np.percentile(v,95)-np.percentile(v,5))/2 if len(v)>5 else None, miss
    ae,me=amp(1,31); al,ml=amp(62,93)
    v=[abs(x) for x in a if x is not None]
    res[nm]=dict(angle0=a[0],amp_early=ae,amp_late=al,miss_early=me,miss_late=ml,max_abs=max(v),miss_all=sum(x is None for x in a),trace=[None if x is None else round(x,1) for x in a])
    print(nm,f"a0={a[0]} ampE={ae:.1f} ampL={al:.1f} missE={me} missL={ml} max|a|={max(v):.0f} miss={res[nm]['miss_all']}")
json.dump(res,open('pend_angles.json','w'),indent=1)
