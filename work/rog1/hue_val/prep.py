# prep real clips (8 s max-motion window, 832x480 24fps) + corruptions
import cv2,numpy as np,glob,os,json
def read(p):
    cap=cv2.VideoCapture(p);F=[]
    while True:
        ok,f=cap.read()
        if not ok:break
        F.append(cv2.resize(f,(832,480),interpolation=cv2.INTER_AREA))
    return F,cap.get(cv2.CAP_PROP_FPS)
def write(p,F,fps=24):
    w=cv2.VideoWriter(p,cv2.VideoWriter_fourcc(*'mp4v'),fps,(832,480))
    for f in F:w.write(f)
    w.release()
rng=np.random.default_rng(0)
clips=sorted(glob.glob('data/gauge/*.mp4'))
orig={}
for p in clips:
    F,fps=read(p); t=os.path.basename(p)[:-4]
    # resample to 24 fps
    n=int(len(F)/fps*24); F=[F[min(len(F)-1,int(i*fps/24))] for i in range(n)]
    W=189
    if len(F)>W:
        g=np.array([cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)[::8,::8].astype(float) for f in F])
        m=np.abs(np.diff(g,axis=0)).mean((1,2)); c=np.convolve(m,np.ones(W-1),'valid')
        s=int(c.argmax()); F=F[s:s+W]
    orig[t]=F; write(f'data/val/{t}__orig.mp4',F)
names=list(orig)
for t,F in orig.items():
    write(f'data/val/{t}__reverse.mp4',F[::-1])
    write(f'data/val/{t}__shuffle.mp4',[F[i] for i in rng.permutation(len(F))])
    write(f'data/val/{t}__freeze.mp4',[F[len(F)//2]]*len(F))
    write(f'data/val/{t}__noise.mp4',[np.clip(f.astype(float)+rng.normal(0,45,f.shape),0,255).astype(np.uint8) for f in F])
    other=orig[names[(names.index(t)+4)%len(names)]]  # different scene
    h=len(F)//2; write(f'data/val/{t}__splice.mp4',F[:h]+other[h:len(F)])
print(len(names),{k:len(v) for k,v in orig.items()})
