import cv2,sys,numpy as np,os
p=sys.argv[1];fr_idx=[0,2,4,6,9,12,16,20,26,32,40,60]
cap=cv2.VideoCapture(p);fs=[]
while True:
    ok,f=cap.read()
    if not ok:break
    fs.append(f)
print(p,len(fs),fs[0].shape)
ims=[]
for i in fr_idx:
    c=fs[min(i,len(fs)-1)][0:420,180:480].copy();cv2.putText(c,str(i),(5,20),0,0.7,(0,0,255),2);ims.append(cv2.resize(c,(200,280)))
cv2.imwrite(sys.argv[2],np.vstack([np.hstack(ims[:6]),np.hstack(ims[6:])]))
