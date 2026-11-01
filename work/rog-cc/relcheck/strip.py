import sys, av, numpy as np
from PIL import Image, ImageDraw
def frames(p, idx):
    c = av.open(p); out = {}
    for i, f in enumerate(c.decode(video=0)):
        if i in idx: out[i] = f.to_ndarray(format='rgb24')
        if i > max(idx): break
    return out
clips = sys.argv[2:]; idx = list(range(0, 27, 2))
rows = []
for p in clips:
    fr = frames(p, set(idx)); tiles = []
    for i in idx:
        im = Image.fromarray(fr[i][20:420, 130:450]).resize((160, 200))
        ImageDraw.Draw(im).text((3, 3), str(i), fill=(255, 255, 0)); tiles.append(np.asarray(im))
    rows.append(np.concatenate(tiles, 1))
Image.fromarray(np.concatenate(rows, 0)).save(sys.argv[1], quality=85)
