import pathlib,json,cv2,numpy as np,sys
p=pathlib.Path(__file__).parent;key=json.loads((p/'blind_key.json').read_text())
for code in sys.argv[1:]:
 cap=cv2.VideoCapture(str(p/'clips'/(key[code]+'.mp4')));fs=[]
 while True:
  ok,f=cap.read()
  if not ok:break
  fs.append(f)
 ids=list(range(0,93,4));tiles=[]
 for i in ids:
  f=fs[i][70:310,230:410].copy();cv2.putText(f,code+' f'+str(i),(4,18),0,.5,(0,255,255),1);tiles.append(f)
 sheet=np.vstack([np.hstack(tiles[i:i+6]) for i in range(0,24,6)])
 cv2.imwrite(str(p/('dense_'+code+'.jpg')),sheet)
