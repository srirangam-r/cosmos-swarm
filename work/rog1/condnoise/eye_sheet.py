import sys, cv2, numpy as np
src, out = sys.argv[1], sys.argv[2]
cap=cv2.VideoCapture(src); fr=[]
while True:
    ok,f=cap.read()
    if not ok: break
    fr.append(f)
x0,y0,x1,y1 = 170,60,470,420
def sheet(idx, scale, cols, path):
    tiles=[]
    for i in idx:
        t=cv2.resize(fr[i][y0:y1,x0:x1],None,fx=scale,fy=scale).copy()
        cv2.putText(t,f"f{i}",(4,16),0,0.55,(0,255,255),1); tiles.append(t)
    tiles += [np.zeros_like(tiles[0])]*(-len(tiles)%cols)
    rows=[np.hstack(tiles[r:r+cols]) for r in range(0,len(tiles),cols)]
    cv2.imwrite(path,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,90])
sheet(list(range(0,48,3)),0.8,4,out+"_a.jpg")
sheet(list(range(48,93,4)),0.8,4,out+"_b.jpg")
print(src,len(fr))
