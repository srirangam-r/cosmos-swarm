import numpy as np, glob, os, json, cv2
res={}
for f in sorted(glob.glob('out/*.npz')):
    n=os.path.basename(f)[:-4]; d=np.load(f); T=d['tracks']; V=d['vis']  # T: frames x 9 x 2
    med=np.median(T,axis=1); spread=np.median(np.linalg.norm(T-med[:,None],axis=2),axis=1)
    vis=V.mean(1)
    x,y=med[:,0],med[:,1]
    # smooth y lightly
    ys=np.convolve(np.pad(y,1,mode='edge'),[1/3]*3,'valid')
    # bounce contacts: local maxima of y (lowest points) with prominence>15px
    from scipy.signal import find_peaks
    pk,_=find_peaks(ys,prominence=15); tr,_=find_peaks(-ys,prominence=15)
    sp=np.linalg.norm(np.diff(med,axis=0),axis=1)
    res[n]=dict(vis=float(vis.mean()),spread_med=float(np.median(spread)),spread_p90=float(np.percentile(spread,90)),
       contacts=pk.tolist(),ycontact=[float(ys[i]) for i in pk],apex=tr.tolist(),yapex=[float(ys[i]) for i in tr],
       x_range=[float(x.min()),float(x.max())],y_range=[float(y.min()),float(y.max())],
       speed_early=float(sp[4:36].mean()),speed_late=float(sp[56:88].mean()),
       yosc_early=float(ys[4:36].max()-ys[4:36].min()),yosc_late=float(ys[56:88].max()-ys[56:88].min()),
       ylast=float(y[-1]))
    r=res[n]; print(n,'vis%.2f sp50 %.1f sp90 %.1f'%(r['vis'],r['spread_med'],r['spread_p90']),'contacts',r['contacts'],'ymax %.0f yrange %.0f-%.0f'%(max(r['ycontact']) if r['ycontact'] else -1,*r['y_range']),'osc e/l %.0f/%.0f'%(r['yosc_early'],r['yosc_late']))
json.dump(res,open('ct_res.json','w'),indent=1)
