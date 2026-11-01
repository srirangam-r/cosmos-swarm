import numpy as np, importlib.util, sys
spec=importlib.util.spec_from_file_location('s','scripts/s102_onset_sim.py'); 
src=open('scripts/s102_onset_sim.py').read().split("rng=np.random")[0]; exec(src)
def r2_and_n(y):
    t=f/24.0; k=int(np.argmax(y>=y.max()-1e-9)); n=max(k-1,5)
    y0,g,t0=hinge(t[:n],y[:n]); j0=int(np.searchsorted(t,t0)); j0=min(j0,n-4)
    c=np.polyfit(t[j0:n],y[j0:n],2); res=y[j0:n]-np.polyval(c,t[j0:n]); r2=1-(res**2).sum()/((y[j0:n]-y[j0:n].mean())**2).sum()
    # exponent n = v_imp*T/H with true onset (rel) and finite-diff speed over last 2 pre-impact frames
    v=(y[k-1]-y[k-3])/2.0; T=(k-1)-rel; H=y[k-1]-y[0]
    return r2, v*T/H
for name,y in [('ballistic',ballistic(gpx)),('ballistic g/4',ballistic(gpx/4))]+[('box w=%d'%w,boxsmooth(gpx,w)) for w in (4,8,12,16)]+[('minjerk D=14',minjerk(14))]:
    r2,nn=r2_and_n(y); print('%-14s quad r2=%.4f  n=v*T/H=%.2f'%(name,r2,nn))
