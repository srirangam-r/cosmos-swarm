import cv2, numpy as np, json, sys
from scipy.optimize import least_squares
from scipy.signal import find_peaks
for path in sys.argv[1:]:
 c=cv2.VideoCapture(path); frames=[]
 while True:
  ok,f=c.read()
  if not ok: break
  frames.append(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY).astype(float))
 a=np.array(frames); bg=np.median(a,axis=0); d=np.abs(a-bg); d[d<20]=0
 # Mask stand and use only pixels in the area occupied by bob motion.
 d[:,:170,:]=0; d[:,410:,:]=0; d[:,:,:250]=0; d[:,:,390:440]=0; d[:,:,600:]=0
 x=np.arange(a.shape[2]); signal=((d*(x-415)).sum(axis=(1,2))/(d.sum(axis=(1,2))+1))
 t=np.arange(len(a)); ix=t>=12
 def fit(t,y):
  best=None
  for p in np.linspace(24,125,100):
   def f(z): return z[0]+z[1]*np.cos(2*np.pi*t/z[3])+z[2]*np.sin(2*np.pi*t/z[3])-y
   q=least_squares(f,[0,80,80,p],bounds=([-500,-1000,-1000,20],[500,1000,1000,150]),max_nfev=300)
   err=np.mean(q.fun**2)
   if best is None or err<best[0]: best=(err,q.x)
  return best
 err,z=fit(t[ix],signal[ix]); peaks,_=find_peaks(signal,distance=12,prominence=5); troughs,_=find_peaks(-signal,distance=12,prominence=5)
 print(json.dumps(dict(path=path,period=float(z[3]),rmse=float(err**.5),peaks=peaks.tolist(),troughs=troughs.tolist(),signal=np.round(signal,2).tolist())))
