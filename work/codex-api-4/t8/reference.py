"""Independent mocap period references for task8; not a Cosmos estimator."""
import numpy as np
from scipy.signal import find_peaks
def onset(values,tolerance):
 departed=np.abs(values-np.median(values[:3]))>tolerance
 for start in range(len(values)-3):
  if np.all(departed[start:start+4]): return start
 return 0
def cross_cycles(t,x,lo,hi):
 mask=(t>=lo)&(t<=hi); a=t[mask]; b=x[mask]-np.median(x[mask]); directions=[]; periods=[]
 for sign in [-1,1]:
  inds=np.flatnonzero((sign*b[:-1]<0)&(sign*b[1:]>=0))
  times=[float(a[k]+(-b[k])/(b[k+1]-b[k])*(a[k+1]-a[k])) for k in inds]
  directions.append(times);periods.extend(np.diff(times).tolist())
 return {'period_s':float(np.median(periods)) if periods else None,'cycles_s':periods,'crossing_times_s':directions}
def turning_cycles(t,x,lo,hi,hz):
 ts=[];periods=[]
 for sign in [-1,1]:
  peaks,_=find_peaks(sign*x,distance=int(.4*hz),prominence=.02)
  times=[]
  for k in peaks:
   if k==0 or k==len(x)-1:continue
   # A quadratic through the three samples refines the sub-frame peak time.
   y=sign*x[k-1:k+2]; denom=y[0]-2*y[1]+y[2]
   delta=.5*(y[0]-y[2])/denom if denom else 0.
   time=float(t[k]+delta/hz)
   if lo<=time<=hi:times.append(time)
  ts.append(times);periods.extend(np.diff(times).tolist())
 return {'period_s':float(np.median(periods)) if periods else None,'cycles_s':periods,'turning_times_s':ts}
