import cv2,numpy as np,sys
ims=[]
for n in sys.argv[2:]:
    a=cv2.imread(f'/home/nail/swarm-work/raj-opus-1/t139/strips/{n}_corr.jpg'); a=cv2.convertScaleAbs(a,alpha=1.6,beta=8)
    ims.append(cv2.resize(a,(a.shape[1]*2//3,a.shape[0]*2//3)))
cv2.imwrite(sys.argv[1],np.hstack(ims))
