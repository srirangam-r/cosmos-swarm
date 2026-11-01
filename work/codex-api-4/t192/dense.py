"""Extra opaque-ID consecutive-frame sheets, fixed before key inspection."""
import argparse,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('panels',type=Path)
    a=ap.parse_args();key=json.loads((a.panels/'key.json').read_text())
    selected={'Q02','Q04','Q05','Q08','Q10','Q11','Q14','Q15','Q17','Q18','Q20'}
    for k in key:
        q=k['id']
        if q not in selected:continue
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(a.source/(k['name']+'.mp4')),'-f','rawvideo','-pix_fmt','rgb24','-threads','1','-'])
        fb=832*480*3
        chunks=range(4) if q=='Q15' else range(1)
        for ch in chunks:
            im=Image.new('RGB',(1920,1536),'#dddddd');d=ImageDraw.Draw(im)
            for j,t in enumerate(range(ch*24,min((ch+1)*24,93))):
                f=Image.frombytes('RGB',(832,480),raw[t*fb:(t+1)*fb])
                x=j%6*320;y=j//6*384
                im.paste(f.crop((150,30,470,390)),(x,y+24));d.text((x+5,y+5),f'{q} f{t}',fill='black')
            im.save(a.panels/f'{q}_dense{ch}.jpg',quality=94,subsampling=0)

if __name__=='__main__':main()
