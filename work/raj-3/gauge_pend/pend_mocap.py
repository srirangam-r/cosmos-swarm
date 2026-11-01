"""Reference pendulum period from GAUGE mocap (30 Hz, mm).
Per clip: release frame, period from zero-crossings of x (first 8 s after release and whole record),
damped-sinusoid fit over first 8 s, pivot/length from a circle fit in the swing plane,
and the small-angle+finite-amplitude prediction 2*pi*sqrt(L/g)*K(theta0) as a physics check of the clock."""
import json, sys, numpy as np, glob, os
from scipy.optimize import least_squares
from scipy.special import ellipk
G=9.81
def zc_period(t, x, tmin, tmax):
    m=(t>=tmin)&(t<=tmax); tt=t[m]; xx=x[m]-np.median(x[m])
    s=np.sign(xx); i=np.where((s[:-1]<0)&(s[1:]>=0))[0]   # upward crossings
    tc=tt[i]-xx[i]*(tt[i+1]-tt[i])/(xx[i+1]-xx[i])
    if len(tc)<2: return np.nan, 0
    d=np.diff(tc); return float(np.median(d)), len(d)
def damped(t,x):
    best=None
    for T in np.linspace(0.6,2.5,20):
        r=lambda p: p[0]*np.exp(-p[3]*t)*np.cos(2*np.pi*t/p[1]+p[2])+p[4]-x
        s=least_squares(r,[np.ptp(x)/2,T,0,0.01,np.median(x)],bounds=([0,0.3,-7,0,-1e4],[1e4,5,7,3,1e4]))
        if best is None or s.cost<best.cost: best=s
    return best
out={}
for f in sorted(glob.glob(sys.argv[1]+'/*.json'),key=lambda p:int(os.path.basename(p)[:-5])):
    c=os.path.basename(f)[:-5]; d=json.load(open(f)); fps=d['FPS']
    P=np.array([d['ball'][k] for k in 'xyz']).T/1000.0   # m
    n=len(P); t=np.arange(n)/fps
    # swing plane: PCA of positions
    mu=P.mean(0); U,S,Vt=np.linalg.svd(P-mu,full_matrices=False)
    a=(P-mu)@Vt[0]; b=(P-mu)@Vt[1]
    # release: first frame where |a - a[0]| > 5 mm
    a0=a[:5].mean(); rel=int(np.argmax(np.abs(a-a0)>0.005)); trel=t[rel]
    # circle fit in (a,b) over first 8 s after release
    m=(t>=trel)&(t<=trel+8)
    def rc(p): return np.hypot(a[m]-p[0],b[m]-p[1])-p[2]
    # pivot is above the arc: sign of b; try both
    sols=[least_squares(rc,[0,sg*0.3,0.3]) for sg in (1,-1)]
    sc=min(sols,key=lambda s:s.cost); pa,pb,L=sc.x
    th=np.arctan2(a-pa, -(b-pb)*np.sign(np.median(b[m]-pb)) * -1)
    th0=float(np.max(np.abs(np.arcsin(np.clip((a[m]-pa)/L,-1,1)))))
    T_pred=4*np.sqrt(L/G)*ellipk(np.sin(th0/2)**2)
    T8,n8=zc_period(t,a,trel+0.2,trel+8)
    Tall,nall=zc_period(t,a,trel+0.2,t[-1])
    # first 189 frames at 24 fps ~ 7.875 s; also the 1.06 s GAUGE window unknown -> report both
    s=damped(t[m]-trel,a[m]); Tfit=float(s.x[1]); gam=float(s.x[3])
    out[c]=dict(fps=fps,n=n,dur_s=n/fps,release_frame=rel,T_zc_8s=T8,n_cycles_8s=n8,T_zc_all=Tall,
                T_damped_8s=Tfit,gamma=gam,L_m=float(L),theta0_deg=float(np.degrees(th0)),T_pred_L=float(T_pred),
                amp0_m=float(np.ptp(a[m])/2),rms_circle_mm=float(np.sqrt(np.mean(sc.fun**2))*1000))
    print(c,{k:(round(v,4) if isinstance(v,float) else v) for k,v in out[c].items()})
json.dump(out,open(sys.argv[2],'w'),indent=1)
T=np.array([v['T_zc_8s'] for v in out.values()]); R=np.array([v['T_zc_8s']/v['T_pred_L'] for v in out.values()])
print(f"T_zc_8s mean {T.mean():.4f} sd {T.std(ddof=1):.4f} n={len(T)};  T/T_pred(L) {R.mean():.4f} +- {R.std(ddof=1)/np.sqrt(len(R)):.4f}")
