import sys, av
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]; step=int(sys.argv[3]) if len(sys.argv)>3 else 2
fr=[f.to_image() for f in av.open(src).decode(video=0)]
sel=list(range(0,len(fr),step)); W,H=312,180; cols=8; rows=(len(sel)+cols-1)//cols
sheet=Image.new('RGB',(cols*W,rows*H),'white'); d=ImageDraw.Draw(sheet)
for k,i in enumerate(sel):
    x,y=(k%cols)*W,(k//cols)*H; sheet.paste(fr[i].resize((W,H)),(x,y)); d.rectangle([x,y,x+38,y+14],fill='black'); d.text((x+2,y+1),f"f{i}",fill='yellow')
sheet.save(out,quality=85); print(out,len(fr),sheet.size)
