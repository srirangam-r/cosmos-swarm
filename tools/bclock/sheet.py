import sys, cv2, numpy as np
cap=cv2.VideoCapture(sys.argv[1]); F=[]
while True:
    ok,f=cap.read()
    if not ok: break
    F.append(f)
idx=np.linspace(0,len(F)-1,12).astype(int)
tiles=[cv2.putText(cv2.resize(F[i],(416,240)),str(i),(5,20),0,0.7,(0,0,255),2) for i in idx]
rows=[np.hstack(tiles[k:k+4]) for k in range(0,12,4)]
cv2.imwrite(sys.argv[2],np.vstack(rows)); print(len(F))
