import cv2,numpy as np,sys
scene=sys.argv[1]; fr=[int(x) for x in sys.argv[2].split(',')]
rows=[]
for s in (4,5,6,7):
    row=[]
    for a in ('base','r','n'):
        cap=cv2.VideoCapture(f'clips/k175_{scene}_{a}_s{s}.mp4'); i=0; got={}
        while True:
            ok,f=cap.read()
            if not ok: break
            if i in fr: got[i]=f
            i+=1
        for k in fr:
            f=cv2.resize(got[k],(277,160)); cv2.putText(f,f"{a} s{s} f{k}",(5,18),0,0.5,(0,255,0),1); row.append(f)
    rows.append(np.hstack(row))
cv2.imwrite(f'montage_{scene}.jpg',np.vstack(rows))
