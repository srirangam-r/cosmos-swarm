"""widthtrack (rog1): per-frame width of the largest compact changed blob vs f0 in the table ROI (y>=250)."""
import sys, json, numpy as np, cv2
def track(p):
    cap=cv2.VideoCapture(p); ok,f0=cap.read(); f0=f0.astype(np.float32); out=[]; i=0
    while True:
        ok,f=cap.read(); i+=1
        if not ok: break
        d=(np.abs(f.astype(np.float32)-f0).max(-1)>35).astype(np.uint8); d[:250]=0
        m=cv2.morphologyEx(d,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)); m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
        n,l,st,_=cv2.connectedComponentsWithStats(m,8)
        c=[s for s in st[1:] if s[4]>=40 and s[4]/(s[2]*s[3])>=0.4 and 0.6<=s[2]/s[3]<=1.6]
        if c: s=max(c,key=lambda s:s[4]); out.append([i,int(s[0]),int(s[1]),int(s[2]),int(s[3])])
    return out
for p in sys.argv[1:]: print(json.dumps(dict(clip=p.split('/')[-1],tr=track(p))),flush=True)
