"""Read only shared originals. Make masked panels without reading author labels."""
import argparse, hashlib, json, random, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source',type=Path); ap.add_argument('out',type=Path)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    movies=sorted(a.source.glob('hrb_*.mp4')); assert len(movies)==24,len(movies)
    random.Random(19201101).shuffle(movies)
    key=[]
    for i,p in enumerate(movies,1):
        q=f'Q{i:02}'
        meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',str(p)]))['streams'][0]
        n,d=map(int,meta['r_frame_rate'].split('/'));fps=n/d
        assert (meta['width'],meta['height'])==(832,480) and abs(fps-24)<1e-6
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','rawvideo','-pix_fmt','rgb24','-threads','1','-'])
        framebytes=832*480*3; assert len(raw)==93*framebytes,(p,len(raw))
        fs=[Image.frombytes('RGB',(832,480),raw[t*framebytes:(t+1)*framebytes]) for t in range(93)]
        panel=Image.new('RGB',(6*320,4*384),'#dddddd'); draw=ImageDraw.Draw(panel)
        for k,t in enumerate(range(0,93,4)):
            x=(k%6)*320;y=(k//6)*384
            panel.paste(fs[t].crop((150,30,470,390)),(x,y+24))
            draw.text((x+5,y+5),f'{q} f{t}',fill='black')
        panel.save(a.out/f'{q}.jpg',quality=94,subsampling=0)
        ov=Image.new('RGB',(4*416,2*264),'#dddddd'); d=ImageDraw.Draw(ov)
        for k,t in enumerate([0,12,24,36,48,60,76,92]):
            x=k%4*416;y=k//4*264
            ov.paste(fs[t].resize((416,240)),(x,y+24));d.text((x+5,y+5),f'{q} full f{t}',fill='black')
        ov.save(a.out/f'{q}_full.jpg',quality=94,subsampling=0)
        key.append({'id':q,'name':p.stem,'sha256':sha(p),'rgb_sha256':hashlib.sha256(raw).hexdigest(),'size':p.stat().st_size,'frames':len(fs),'fps':fps,'shape':[480,832,3]})
    kp=a.out/'key.json';kp.write_text(json.dumps(key,indent=2)+'\n')
    print(json.dumps({'clips':len(key),'key_sha256':sha(kp)}))

if __name__=='__main__':main()
