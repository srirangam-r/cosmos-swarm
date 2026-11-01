"""Independent coarse impact timing from foreground episodes; run from repo root."""
import cv2, json, numpy as np
p='work/ro-1/fps_sweep/ballF/ball_F_ball1_fps24_93f_s1.mp4'
c=cv2.VideoCapture(p); fs=[]
while True:
 ok,f=c.read()
 if not ok: break
 fs.append(f)
assert len(fs)==93
bg=np.median(np.array(fs),axis=0).astype('uint8')
# Impact windows selected after visual review, not an automatic detector.
windows=[(5,9),(15,19),(23,27),(31,35),(39,43),(47,51),(54,58),(62,66),(69,73),(76,80),(83,88)]
out={}
for threshold in (15,25,35):
 ys=[]
 for f in fs:
  d=cv2.absdiff(f,bg).max(axis=2); mask=np.zeros(d.shape,np.uint8); mask[170:380,245:345]=(d[170:380,245:345]>threshold).astype(np.uint8)
  n,l,s,cent=cv2.connectedComponentsWithStats(mask); i=1+np.argmax(s[1:,cv2.CC_STAT_AREA]); ys.append(float(cent[i,1]))
 for floor in (325,330,335,340):
  times=[]
  for a,b in windows:
   inds=[i for i in range(a,b+1) if ys[i]>floor]
   assert inds
   times.append((inds[0]+inds[-1])/2)
  T=np.diff(times); x=np.arange(len(T)); slope,intercept=np.polyfit(x,np.log(T),1); residual=np.log(T)-(intercept+slope*x)
  se=(sum(residual**2)/(len(x)-2)/sum((x-x.mean())**2))**.5
  out[f'{threshold}/{floor}']={'times':times,'flight_frames':T.tolist(),'e':float(np.exp(slope)),'conditional_se':float(np.exp(slope)*se)}
print(json.dumps(out,indent=2))
