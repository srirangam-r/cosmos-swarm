"""Compare bundled lossless remote frames with the local ffmpeg conversion."""
from pathlib import Path
import subprocess,hashlib,json
import numpy as np,scipy,cv2,PIL
from PIL import Image
root=Path(__file__).resolve().parent;p=root/'decode_check';out=[]
for f in sorted(p.glob('*.png')):
 name,t=f.stem.rsplit('_f',1);t=int(t)
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(root/'examples'/(name+'.mp4')),'-f','rawvideo','-pix_fmt','rgb24','-threads','1','-'])
 local=np.frombuffer(raw,dtype=np.uint8).reshape(93,480,832,3)[t];remote=np.asarray(Image.open(f));diff=np.abs(local.astype(int)-remote.astype(int))
 out.append({'name':name,'frame':t,'remote_png_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'max_abs_rgb_difference':int(diff.max()),'mean_abs_rgb_difference':float(diff.mean()),'nonzero_channel_fraction':float((diff>0).mean())})
result={'local_ffmpeg':subprocess.check_output(['ffmpeg','-version']).decode().splitlines()[0],'remote_ffmpeg':(p/'ffmpeg.txt').read_text().splitlines()[0],'numpy':np.__version__,'scipy':scipy.__version__,'cv2':cv2.__version__,'pillow':PIL.__version__,'samples':out}
print(json.dumps(result,indent=2))
