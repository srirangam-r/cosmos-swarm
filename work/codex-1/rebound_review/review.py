import cv2, numpy as np, json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
video = root/'raj-3/midfall/out_gb10/midfall_ball1_dd33_noneg_s1.mp4'
cap = cv2.VideoCapture(str(video)); frames=[]
while len(frames)<60:
    ok, frame=cap.read()
    if not ok: break
    frames.append(frame)
background=np.median(np.stack(frames),axis=0).astype('uint8')
results={}
for threshold in (15,25,35):
    ys=[]
    for f in range(6,15):
        diff=cv2.absdiff(frames[f],background).max(axis=2)
        mask=np.zeros(diff.shape,np.uint8)
        mask[150:335,250:330]=(diff[150:335,250:330]>threshold).astype('uint8')
        n, labels, stats, centers=cv2.connectedComponentsWithStats(mask)
        # The moving ball is the largest foreground region in this constrained ROI.
        k=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]); ys.append(float(centers[k,1]))
    def fit(start,end):
        t=np.arange(start,end+1)/24
        p=np.polyfit(t,np.array(ys)[start-6:end-5],2)
        return float(2*p[0]/539.8)
    t=np.arange(6,13)/24
    y=np.array(ys[:7]); poly=np.polyfit(t,y,2); pred=np.polyval(poly,t)
    residual=y-pred; rng=np.random.default_rng(914)
    boot=[2*np.polyfit(t,pred+rng.choice(residual,size=7,replace=True),2)[0]/539.8 for _ in range(10000)]
    results[str(threshold)]={'centers':ys,'g_frames_6_12':fit(6,12),'residual_bootstrap_ci95':np.percentile(boot,[2.5,97.5]).tolist(),'g_frames_6_14':fit(6,14),'g_frames_7_13':fit(7,13)}
print(json.dumps(results,indent=2))
