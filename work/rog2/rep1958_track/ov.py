import sys, json, numpy as np, cv2
from track import load
tr=json.load(open('tracks.json'))
names=sys.argv[2:]
rows=[]
for k in names:
    G=load(f'clips/{k}.mp4'); T=np.array(tr[k])
    fr=[]
    for t in range(0,93,6)[:12]:
        im=cv2.cvtColor(G[t],cv2.COLOR_GRAY2BGR)
        if T[t,3]: cv2.circle(im,(int(T[t,0]),int(T[t,1])),14,(0,255,0),1)
        cv2.putText(im,f'{k[:12]} {t}',(3,12),0,0.35,(0,255,255),1)
        fr.append(im)
    rows.append(np.hstack(fr[:6])); rows.append(np.hstack(fr[6:12]))
cv2.imwrite(sys.argv[1],np.vstack(rows))
