"""Source-aware post-freeze Q10 full-frame illustration; no labels changed."""
from pathlib import Path
import cv2
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parent
c=cv2.VideoCapture(str(p/'examples/hrb_b15_s12.mp4'));fs=[]
while True:
 ok,f=c.read()
 if not ok:break
 fs.append(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)))
c.release();assert len(fs)==93
out=Image.new('RGB',(1664,4*504),'#dddddd');d=ImageDraw.Draw(out)
for j,t in enumerate([24,32,40,44,48,52,60,76]):
 x=j%2*832;y=j//2*504
 out.paste(fs[t],(x,y+24));d.text((x+5,y+5),f'Q10 f{t} post-freeze diagnostic full frame',fill='black')
out.save(p/'examples/Q10_postfreeze.png')
