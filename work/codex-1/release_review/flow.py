import cv2, numpy as np, json, pathlib

base = pathlib.Path('work/agy-1/task9_duration_audit')
results = {}
for name in ['ball1_nf93_s1', 'ball2_nf93_s1']:
    cap = cv2.VideoCapture(str(base / (name+'.mp4')))
    ok, frame = cap.read(); assert ok
    prev = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    groups = {}
    for label, (x0,y0,x1,y1) in {'gripper':(265,55,300,90), 'ball':(270,107,295,131)}.items():
        mask=np.zeros(prev.shape,np.uint8); mask[y0:y1,x0:x1]=255
        p=cv2.goodFeaturesToTrack(prev, maxCorners=30, qualityLevel=.01, minDistance=2, mask=mask, blockSize=3)
        assert p is not None and len(p)>=3
        groups[label]=[p, p.copy(), []]
    for f in range(1,39):
        ok, frame=cap.read(); assert ok
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        for label, (p, initial, rows) in groups.items():
            q, status, err=cv2.calcOpticalFlowPyrLK(prev,gray,p,None,winSize=(21,21),maxLevel=3)
            back, st2, _=cv2.calcOpticalFlowPyrLK(gray,prev,q,None,winSize=(21,21),maxLevel=3)
            good=(status.ravel()==1)&(st2.ravel()==1)&(np.linalg.norm(back-p,axis=2).ravel()<1.0)
            p=q[good].reshape(-1,1,2); initial=initial[good].reshape(-1,1,2)
            assert len(p)>=3, (name,label,f,len(p))
            d=(p-initial).reshape(-1,2)
            rows.append({'frame':f,'n':len(p),'dx':float(np.median(d[:,0])),'dy':float(np.median(d[:,1])),'dy_iqr':float(np.percentile(d[:,1],75)-np.percentile(d[:,1],25))})
            groups[label]=[p,initial,rows]
        prev=gray
    results[name]={label: rows for label, (_,_,rows) in groups.items()}
print(json.dumps(results,indent=2))
