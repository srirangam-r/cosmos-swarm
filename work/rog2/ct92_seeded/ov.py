import numpy as np, cv2, sys
def sheet(name,out,frames=range(0,93,6)):
    d=np.load(f'out/{name}.npz'); med=np.median(d['tracks'],axis=1)
    cap=cv2.VideoCapture(f'../ct92/clips/{name}.mp4'); fr=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        fr.append(f)
    tiles=[]
    for i in frames:
        f=fr[i].copy(); x,y=med[i]; cv2.circle(f,(int(x),int(y)),14,(0,255,0),2)
        cv2.putText(f,str(i),(5,30),0,1,(0,0,255),2)
        tiles.append(cv2.resize(f[0:420,100:520],(280,280)))
    while len(tiles)%4: tiles.append(np.zeros_like(tiles[0]))
    rows=[np.hstack(tiles[i:i+4]) for i in range(0,len(tiles),4)]
    cv2.imwrite(out,np.vstack(rows))
for n in sys.argv[1:]: sheet(n,f'ov_{n}.jpg')
