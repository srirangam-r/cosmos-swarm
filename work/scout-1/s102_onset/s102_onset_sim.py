# Simulate firstfall's fit pipeline (hinge t0, v0=0; then free-v0 quadratic to impact-1) on
# ballistic vs box-smoothed ("jerk-limited", width w frames) vs min-jerk falls.
# Readout: g_fit/g_from_h_T (ballistic -> ~1) and g_fit/g_true.
import numpy as np
from scipy.optimize import least_squares
def hinge(t, y):
    def r(p): y0, g, t0 = p; return np.where(t < t0, y0, y0 + 0.5*g*(t-t0)**2) - y
    best=None
    for t0 in np.linspace(t[0], t[-1], 25):
        s=least_squares(r,[y[0],2*(y[-1]-y[0])/max((t[-1]-t0)**2,1e-3),t0])
        if best is None or s.cost<best.cost: best=s
    return best.x
def pipeline(f, y, fps=24.0):
    t=f/fps; k=int(np.argmax(y>=y.max()-1e-9))  # impact = first frame at floor
    a0=0; n=max(k-1,a0+5)
    y0,g,t0=hinge(t[a0:n],y[a0:n]); j0=int(np.searchsorted(t,t0))
    if n-j0<4: j0=max(n-4,0)
    c=np.polyfit(t[j0:n],y[j0:n],2); gfit=2*c[0]
    H=y[k]-y[0]; T=t[k]-t0
    return gfit, 2*H/T**2, (k, t0*fps)
fps=24.0; gpx=9.19*fps**2  # px/s^2 at t139 ball1 scale (9.81 m/s^2)
H=185.0; rel=6.0  # release at frame 6
f=np.arange(0,60,dtype=float)
def ballistic(g):
    tt=np.clip(f-rel,0,None)/fps; return np.minimum(0.5*g*tt**2,H)
def boxsmooth(g,w):
    a=np.clip(f-rel,0,None)/fps; b=np.clip(f-rel-w,0,None)/fps
    y=g/(6*w/fps)*(a**3-b**3); return np.minimum(y,H)
def minjerk(D):
    s=np.clip((f-rel)/D,0,1); return H*(10*s**3-15*s**4+6*s**5)
rng=np.random.default_rng(0)
print('case  g_fit/g_hT  g_fit/g_true  impact_f  t0_f')
for name,y,gt in [('ballistic g',ballistic(gpx),gpx),('ballistic g/4',ballistic(gpx/4),gpx/4)]+\
    [('box w=%d'%w,boxsmooth(gpx,w),gpx) for w in (2,4,8,12,16)]+[('minjerk D=%d'%D,minjerk(D),None) for D in (10,14)]:
    out=[]
    for rep in range(30):
        yy=y+rng.normal(0,1.0,len(y)); yy[y>=H]=H
        gf,gh,(k,t0)=pipeline(f,yy); out.append((gf/gh, gf/gt if gt else np.nan, k, t0))
    o=np.array(out); print('%-14s %.2f±%.2f  %.2f  %d  %.1f'%(name,o[:,0].mean(),o[:,0].std(),np.nanmean(o[:,1]),o[0,2],o[:,3].mean()))
