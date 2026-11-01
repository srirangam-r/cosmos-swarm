import cv2,sys,numpy as np
for f in sys.argv[1:]:
    cap=cv2.VideoCapture(f); fr=[]
    while len(fr)<93:
        ok,im=cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32))
    fr=np.array(fr)
    hp=np.array([x-cv2.GaussianBlur(x,(0,0),2) for x in fr])
    dh=np.abs(np.diff(hp,axis=0)).mean(axis=(1,2)); b=np.arange(1,len(fr))
    seam=dh[b%4==1].mean(); other=dh[b%4!=1].mean()
    p12=dh[b%12==0].mean(); o12=dh[b%12!=0].mean()
    print(f"{f.split('/')[-1]:36s} HF jump at chunk boundary / other = {seam/other:.2f}   at b%12==0 / other = {p12/o12:.2f}")
