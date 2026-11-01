import cv2,sys,numpy as np
p=sys.argv[1];idx=[int(x) for x in sys.argv[3].split(',')]
cap=cv2.VideoCapture(p);fs=[]
while True:
    ok,f=cap.read()
    if not ok:break
    fs.append(f)
ims=[]
for i in idx:
    c=fs[i][60:460,150:550].copy();cv2.putText(c,str(i),(5,22),0,0.8,(0,0,255),2);ims.append(cv2.resize(c,(240,240)))
cv2.imwrite(sys.argv[2],np.vstack([np.hstack(ims[:6]),np.hstack(ims[6:12])]))
