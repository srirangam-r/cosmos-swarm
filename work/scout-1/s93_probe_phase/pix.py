import cv2,sys,numpy as np
for f in sys.argv[1:]:
    cap=cv2.VideoCapture(f); fr=[]
    while True:
        ok,im=cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32))
    fr=np.array(fr); T=len(fr)
    d=np.abs(np.diff(fr,axis=0)).mean(axis=(1,2))           # whole-frame frame diff
    hf=np.array([cv2.Laplacian(x,cv2.CV_32F).var() for x in fr])  # sharpness
    # noise innovation: diff of high-pass residuals
    hp=np.array([x-cv2.GaussianBlur(x,(0,0),2) for x in fr])
    dh=np.abs(np.diff(hp,axis=0)).mean(axis=(1,2))
    name=f.split('/')[-1]
    print(name, T, 'frames; mean diff', d.mean().round(2), 'mean HF-innov', dh.mean().round(2))
    # periodicity: autocorrelation of detrended dh
    for nm,s in [('framediff',d),('hf_innov',dh),('sharp',hf)]:
        x=s-np.convolve(s,np.ones(9)/9,'same'); x=x[5:-5]; x=(x-x.mean())/(x.std()+1e-9)
        ac=[np.mean(x[:-k]*x[k:]) for k in range(1,26)]
        top=np.argsort(ac)[::-1][:3]+1
        print(f"  {nm:9s} ac lags 4,6,8,12,24: {ac[3]:+.2f} {ac[5]:+.2f} {ac[7]:+.2f} {ac[11]:+.2f} {ac[23]:+.2f}  top lags {list(top)}")
    print('  hf_innov frames with z>2:', [i+1 for i in np.where((dh-np.median(dh))/ (1.4826*np.median(np.abs(dh-np.median(dh)))+1e-9) > 3)[0]])
    print('  sharpness first/last 10:', hf[:10].mean().round(1), hf[-10:].mean().round(1))
