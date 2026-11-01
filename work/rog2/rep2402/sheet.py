import cv2,sys,numpy as np,glob,os
fr_idx=[0,6,12,20,32,48,70,92]
rows=[]
for p in sorted(glob.glob('clips/*.mp4')):
    cap=cv2.VideoCapture(p);fs=[]
    while True:
        ok,f=cap.read()
        if not ok:break
        fs.append(f)
    ims=[cv2.resize(fs[min(i,len(fs)-1)],(312,180)) for i in fr_idx]
    r=np.hstack(ims);cv2.putText(r,os.path.basename(p)[9:-4]+f' n={len(fs)}',(5,15),0,0.5,(0,255,0),1);rows.append(r)
cv2.imwrite('sheet.jpg',np.vstack(rows))
