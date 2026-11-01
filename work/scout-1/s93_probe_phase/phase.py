import cv2,sys,numpy as np
def frames(f):
    cap=cv2.VideoCapture(f); fr=[]
    while True:
        ok,im=cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32))
    return np.array(fr)
for f in sys.argv[1:]:
    fr=frames(f)
    hp=np.array([x-cv2.GaussianBlur(x,(0,0),2) for x in fr])
    d=np.abs(np.diff(fr,axis=0)).mean(axis=(1,2)); dh=np.abs(np.diff(hp,axis=0)).mean(axis=(1,2))
    b=np.arange(1,len(fr))   # jump into frame b
    name=f.split('/')[-1]
    # phase of b mod 4 (encoder chunk k = frames 4k-3..4k; b%4==1 => chunk boundary)
    print(name)
    print('  frame-diff by (b mod 4) [1=chunk boundary]:', ' '.join(f"{m}:{d[b%4==m].mean():.3f}" for m in [1,2,3,0]), '| HF:', ' '.join(f"{m}:{dh[b%4==m].mean():.3f}" for m in [1,2,3,0]))
    p12=(b%12==0); print(f'  b%12==0 (n={p12.sum()}): framediff {d[p12].mean():.3f} vs other {d[~p12].mean():.3f}; HF {dh[p12].mean():.3f} vs {dh[~p12].mean():.3f}')
