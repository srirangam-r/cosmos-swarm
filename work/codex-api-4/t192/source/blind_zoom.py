# Zoom on one blind ID: corridor f<a>..f<b> at 1.5x. Usage: python blind_zoom.py ID a b
import json,sys,cv2,numpy as np
inv={v:k for k,v in json.load(open('blind_key.json')).items()}
bid,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
cap=cv2.VideoCapture(f'clips_blur/{inv[bid]}.mp4'); fr=[]
while True:
    ok,f=cap.read()
    if not ok: break
    fr.append(f)
t=[]
for k in range(a,b+1):
    x=fr[k][60:390,207:347].copy(); cv2.line(x,(0,53),(6,53),(0,0,255),1)
    x=cv2.resize(np.clip(x.astype(float)*1.6,0,255).astype(np.uint8),None,fx=1.0,fy=1.0)
    cv2.putText(x,str(k),(2,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1); t.append(x)
cv2.imwrite(f'sheets_blind/zoom_{bid}.jpg',np.hstack(t))
