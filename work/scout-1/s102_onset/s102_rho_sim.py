# J (box-smoothed true trajectory) -> what rho1 = a_flight1/a_fall does task 162's segmentation read?
import numpy as np
fps=24.; g=9.19; H=185.; e=0.8; rel=6
def true_traj(n=93, sub=20):
    # y measured downward from start; floor at H; sample finely then average
    tt=np.arange(0,n,1.0/sub); y=np.zeros_like(tt); pos=0.; v=0.; dt=1.0/sub
    for i,t in enumerate(tt):
        if t>=rel:
            v+=g*dt; pos+=v*dt
            if pos>=H: pos=H-(pos-H); v=-e*abs(v)
        y[i]=pos
    return tt,y
def smooth(tt,y,w,sub=20):
    if w<=0: return y
    k=int(w*sub); ker=np.ones(k)/k; yp=np.concatenate([np.full(k,y[0]),y])
    return np.convolve(yp,ker,'full')[k:k+len(y)]  # causal-equivalent shift is irrelevant for curvature
def frames(tt,y,sub=20): return y[::sub][:93]
def seg_fit(Y, lo, hi):
    t=np.arange(lo,hi+1,dtype=float); c=np.polyfit(t,Y[lo:hi+1],2); return 2*c[0], hi-lo+1
def rho1(Y):
    y0=Y[0]; on=int(np.argmax(Y>y0+2))
    # impacts = local maxima of y (lowest points), prominence >= 8 px
    imp=[i for i in range(1,len(Y)-1) if Y[i]>=Y[i-1] and Y[i]>Y[i+1] and Y[i]-min(Y[max(0,i-6):i+7])>=8]
    i1,i2=imp[0],imp[1]
    af,nf=seg_fit(Y,on,i1-1); a1,n1=seg_fit(Y,i1+2,i2-2)
    return af,a1,a1/af,nf,n1,(i1,i2)
tt,y=true_traj()
for w in (0,4,8,12,16):
    Y=frames(tt,smooth(tt,y,w))
    try:
        af,a1,r,nf,n1,ii=rho1(Y); print('w=%2d  a_fall=%.2f a_flight1=%.2f px/f^2  rho1=%.2f  (fall %d f, flight %d f, impacts %s; true a=%.2f)'%(w,af,a1,r,nf,n1,ii,g))
    except Exception as ex: print('w=%d fail %s'%(w,ex))
print('--- trimming test: drop m frames before impact 1 from the fall fit, and m+1 next to each impact in flight 1')
def rho_trim(Y,m):
    y0=Y[0]; on=int(np.argmax(Y>y0+2))
    imp=[i for i in range(1,len(Y)-1) if Y[i]>=Y[i-1] and Y[i]>Y[i+1] and Y[i]-min(Y[max(0,i-6):i+7])>=8]
    i1,i2=imp[0],imp[1]
    if i1-1-m-on<2 or (i2-2-m)-(i1+2+m)<2: return None
    af,_=seg_fit(Y,on,i1-1-m); a1,_=seg_fit(Y,i1+2+m,i2-2-m); return af,a1,a1/af
for w in (0,2,3,4,6):
    Y=frames(tt,smooth(tt,y,w)); out=[]
    for m in (0,1,2):
        r=rho_trim(Y,m); out.append('m=%d: a_fall %.2f a_fl1 %.2f rho1 %.2f'%(m,*r) if r else 'm=%d: too short'%m)
    print('w=%d  '%w+' | '.join(out))
