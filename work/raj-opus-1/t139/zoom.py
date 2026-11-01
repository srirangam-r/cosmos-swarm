import cv2,numpy as np,sys
c=cv2.VideoCapture(f'clips/{sys.argv[1]}.mp4'); F=[]
while True:
  ok,f=c.read()
  if not ok: break
  F.append(f)
th=[]
for i in [0,4,8,12,16,20,24,32,40,52,64,76,88,92]:
  x=cv2.resize(F[i][80:160,240:320],(120,120),interpolation=cv2.INTER_NEAREST); x=cv2.convertScaleAbs(x,alpha=2,beta=10); cv2.putText(x,str(i),(2,14),0,0.5,(0,255,255),1); th.append(x)
cv2.imwrite(sys.argv[2],np.hstack(th))
