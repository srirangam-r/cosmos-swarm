import json, numpy as np, cv2
T={json.loads(l)['clip'][5:-4]:json.loads(l)['tr'] for l in open('wt_all.jsonl')}
rows=[]
for s in ('s2','s3','s4','s6','s8','s9'):
  row=[]
  for arm in ('N','F','QT'):
    n=f'b2dd35_{arm}_{s}'; tr=[t for t in T[n] if 24<=t[0]<96 and t[2]>=290]
    tile=np.zeros((140,350,3),np.uint8)
    if tr:
      i,x,y,w,h=tr[len(tr)//2]; cap=cv2.VideoCapture(f'/home/swarm/jobs/poornima-2/task141/clips/t141_{n}.mp4')
      cap.set(cv2.CAP_PROP_POS_FRAMES,i); ok,f=cap.read()
      cv2.rectangle(f,(x,y),(x+w,y+h),(0,0,255),1); tile=f[260:400,150:500].copy()
      cv2.putText(tile,f'{n} f{i} w{w}',(2,12),0,0.4,(255,255,255),1)
    row.append(tile)
  rows.append(np.hstack(row))
cv2.imwrite('spot.jpg',np.vstack(rows))
