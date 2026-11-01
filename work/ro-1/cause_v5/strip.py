# ro-1: contact strip of the ball corridor, every 3rd frame, 4 rows
import av, numpy as np, sys
from PIL import Image, ImageDraw
f, out = sys.argv[1], sys.argv[2]
fr = [x.to_ndarray(format='rgb24') for x in av.open(f).decode(video=0)]
idx = list(range(0, len(fr), 3))
tiles = []
for i in idx:
    t = Image.fromarray(fr[i][110:380, 180:400]).resize((110, 135))
    ImageDraw.Draw(t).text((2, 2), str(i), fill=(255, 0, 0))
    tiles.append(t)
cols = 8; rows = (len(tiles) + cols - 1) // cols
S = Image.new('RGB', (cols * 110, rows * 135))
for k, t in enumerate(tiles): S.paste(t, ((k % cols) * 110, (k // cols) * 135))
S.save(out, quality=85)
