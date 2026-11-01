import pathlib,json,cv2,numpy as np,sys
p=pathlib.Path(__file__).parent;key=json.loads((p/'blind_key.json').read_text());codes=sys.argv[1:];rows=[]
for code in codes:
 cap=cv2.VideoCapture(str(p/'clips'/(key[code]+'.mp4')));fs=[]
 while True:
  ok,f=cap.read()
  if not ok:break
  fs.append(f)
 tiles=[]
 for i in [0,16,32,48,64,80,92]:
  f=fs[i][70:310,230:410].copy();cv2.putText(f,code+' f'+str(i),(4,18),0,.5,(0,255,255),1);tiles.append(f)
 rows.append(np.hstack(tiles))
out=p/('detail_'+'_'.join(codes)+'.jpg');cv2.imwrite(str(out),np.vstack(rows));print(out)
