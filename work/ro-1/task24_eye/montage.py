# ro-1: blind eye-coding montages, 12 clips per page, frames 0,12,24,36,48,60,92, content crop x130-540.
import av, numpy as np, glob, os, sys
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
fs = sorted(glob.glob(src + '/*.mp4')); idx = (0, 12, 24, 36, 48, 60, 92)
for p in range(0, len(fs), 12):
    rows = []
    for f in fs[p:p+12]:
        fr = [x.to_ndarray(format='rgb24') for x in av.open(f).decode(video=0)]
        r = np.concatenate([np.array(Image.fromarray(fr[i][:, 155:676]).resize((174, 160))) for i in idx], 1)
        im = Image.fromarray(r); ImageDraw.Draw(im).text((2, 2), os.path.basename(f)[:6], fill=(255, 0, 0))
        rows.append(np.array(im))
    Image.fromarray(np.concatenate(rows, 0)).save(f'{out}/page{p//12}.jpg')
