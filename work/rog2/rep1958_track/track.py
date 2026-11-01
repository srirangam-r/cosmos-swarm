"""Identity-aware dark-ball tracker for #1958 clips (rog2). Static camera.
fg = dark pixels (gray<DARK) that differ from per-clip median background by >THR. Blob nearest to previous centre
(gate GATE px, scaled by size) = ball. Seed = the dark moving blob in frame 0..2 closest to image centre-top (gripper area)
chosen as largest fg blob with area in [AMIN,AMAX]. Output per clip: centre, area, found flag."""
import sys, json, os, glob
import numpy as np, cv2
DARK, THR, AMIN, AMAX, GATE = 70, 28, 80, 9000, 90
def load(p, step=1):
    c = cv2.VideoCapture(p); out=[]
    while True:
        ok, f = c.read()
        if not ok: break
        out.append(cv2.cvtColor(cv2.resize(f,(416,240),interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY))
    return np.array(out)
def blobs(g, bg):
    m = ((g < DARK) & (np.abs(g.astype(np.int16)-bg.astype(np.int16)) > THR)).astype(np.uint8)
    m[:4]=0; m[-4:]=0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    return [(cen[i], st[i,cv2.CC_STAT_AREA]) for i in range(1,n) if AMIN/4 <= st[i,cv2.CC_STAT_AREA] <= AMAX/4]
def track(G):
    bg = np.median(G[::3], axis=0).astype(np.uint8)
    # seed: first frame blob with greatest area in the upper-middle region
    tr=[]; prev=None; parea=None; lost=0
    for t,g in enumerate(G):
        bl = blobs(g,bg)
        if prev is None:
            cand=[b for b in bl if b[0][1]<150]
            if not cand: tr.append((np.nan,np.nan,0,0)); continue
            c,a = max(cand,key=lambda b:b[1]); prev=c; parea=a; tr.append((c[0],c[1],a,1)); continue
        gate = GATE*(1+0.5*lost)/2
        best=None;bd=1e9
        for c,a in bl:
            d=np.hypot(*(c-prev))
            if d<gate and d<bd and 0.3<a/parea<3.5: best=(c,a);bd=d
        if best is None:
            lost+=1; tr.append((np.nan,np.nan,0,0))
            if lost>12: prev=None; lost=0
        else:
            c,a=best; lost=0; prev=c; parea=0.7*parea+0.3*a; tr.append((c[0],c[1],a,1))
    return np.array(tr)
if __name__=='__main__':
    d=sys.argv[1]; out={}
    for p in sorted(glob.glob(d+'/*.mp4')):
        G=load(p)
        if len(G)<90: print("skip",p); continue
        tr=track(G); k=os.path.basename(p)[:-4]
        out[k]=tr.tolist(); print(k, len(G), 'found', int(tr[:,3].sum()))
    json.dump(out,open(sys.argv[2],'w'))
