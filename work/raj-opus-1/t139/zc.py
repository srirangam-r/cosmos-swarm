import cv2,numpy as np,sys
# usage: zc.py clipname out.jpg f0,f1,... [x0 x1 y0 y1]
n,out,fr=sys.argv[1],sys.argv[2],[int(x) for x in sys.argv[3].split(',')]
x0,x1,y0,y1=(int(v) for v in sys.argv[4:8]) if len(sys.argv)>7 else (190,390,40,440)
c=cv2.VideoCapture(f'/home/nail/swarm-work/raj-opus-1/t139/clips/{n}.mp4');F=[]
while True:
  ok,f=c.read()
  if not ok:break
  F.append(f)
th=[]
for i in fr:
  x=F[i][y0:y1,x0:x1].copy(); x=cv2.convertScaleAbs(x,alpha=1.8,beta=10)
  cv2.putText(x,str(i),(3,16),0,0.55,(0,255,255),1); th.append(x)
rows=[np.hstack(th[k:k+12]+[np.zeros_like(th[0])]*(12-len(th[k:k+12]))) for k in range(0,len(th),12)]
cv2.imwrite(out,np.vstack(rows))
