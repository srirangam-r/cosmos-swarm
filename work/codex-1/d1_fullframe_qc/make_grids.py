import cv2, glob, random, json, os
files=sorted(glob.glob('task89_originals/*.mp4'))
assert len(files)==16,len(files)
random.Random(891122).shuffle(files)
os.makedirs('task89_review',exist_ok=True)
json.dump(dict(enumerate(files,1)),open('task89_review/key.json','w'),indent=2)
for i,p in enumerate(files,1):
 c=cv2.VideoCapture(p); frames=[]
 while True:
  ok,f=c.read()
  if not ok:break
  n=len(frames); f=cv2.resize(f,(208,120)); cv2.putText(f,str(n),(3,15),cv2.FONT_HERSHEY_SIMPLEX,.42,(0,0,255),1,cv2.LINE_AA); frames.append(f)
 assert len(frames)==189,(p,len(frames))
 import numpy as np
 grid=np.zeros((16*120,12*208,3),np.uint8)
 for n,f in enumerate(frames):grid[(n//12)*120:(n//12+1)*120,(n%12)*208:(n%12+1)*208]=f
 cv2.imwrite(f'task89_review/{i:02}.jpg',grid,[cv2.IMWRITE_JPEG_QUALITY,85])
print('16 frame grids complete')
