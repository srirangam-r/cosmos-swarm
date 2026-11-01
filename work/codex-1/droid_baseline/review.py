import cv2, numpy as np, json, sys, hashlib
p=sys.argv[1]; cap=cv2.VideoCapture(p); frames=[]
while True:
    ok, frame=cap.read()
    if not ok: break
    frames.append(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY).astype(np.float64))
cap.release()
rows=[]
for start in range(0,320,16):
    a=frames[start]; vals=[]
    for b in frames[start+1:start+17]:
        mse=np.mean((a-b)**2); psnr=10*np.log10(255**2/mse)
        mu1=cv2.GaussianBlur(a,(11,11),1.5); mu2=cv2.GaussianBlur(b,(11,11),1.5)
        var1=cv2.GaussianBlur(a*a,(11,11),1.5)-mu1*mu1
        var2=cv2.GaussianBlur(b*b,(11,11),1.5)-mu2*mu2
        cov=cv2.GaussianBlur(a*b,(11,11),1.5)-mu1*mu2
        s=((2*mu1*mu2+6.5025)*(2*cov+58.5225))/((mu1*mu1+mu2*mu2+6.5025)*(var1+var2+58.5225))
        vals.append([psnr,float(np.mean(s[5:-5,5:-5]))])
    rows.append(dict(start=start,psnr=float(np.mean(np.array(vals)[:,0])),ssim=float(np.mean(np.array(vals)[:,1]))))
print(json.dumps(dict(source_sha256=hashlib.sha256(open(p,'rb').read()).hexdigest(),n_frames=len(frames),n=len(rows),psnr_mean=float(np.mean([r['psnr'] for r in rows])),psnr_sd=float(np.std([r['psnr'] for r in rows],ddof=1)),ssim_mean=float(np.mean([r['ssim'] for r in rows])),ssim_sd=float(np.std([r['ssim'] for r in rows],ddof=1)),chunks=rows),indent=2))
