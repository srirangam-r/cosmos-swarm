import sys, numpy as np, cv2
cap = cv2.VideoCapture(sys.argv[1]); F=[]
while True:
    ok,f=cap.read()
    if not ok: break
    F.append(f)
a,b=int(sys.argv[3]),int(sys.argv[4])
tiles=[]
for i in range(a,b):
    c=F[i][40:420,180:420].copy(); cv2.putText(c,str(i),(5,20),0,0.6,(0,0,255),2)
    for y in range(0,380,50): cv2.line(c,(0,y),(8,y),(0,255,255),1); cv2.putText(c,str(y+40),(10,y+4),0,0.3,(0,255,255),1)
    tiles.append(c)
while len(tiles)%8: tiles.append(np.zeros_like(tiles[0]))
rows=[np.hstack(tiles[i:i+8]) for i in range(0,len(tiles),8)]
cv2.imwrite(sys.argv[2],np.vstack(rows))
