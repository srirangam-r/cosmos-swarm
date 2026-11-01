# v9 last20 (same metric/crop as cause_v8/analyze7.py): mean |dgray| over last 20 frame diffs, crop [130:360,220:360]
import av, numpy as np, glob, os, json, sys
from PIL import Image
out = {}
for f in sorted(glob.glob(sys.argv[1] + '/v9_*.mp4')):
    fr = [x.to_ndarray(format='rgb24') for x in av.open(f).decode(video=0)]
    g = np.stack([np.asarray(Image.fromarray(x).convert('L')).astype(np.float32)[130:360, 220:360] for x in fr])
    d = np.abs(np.diff(g, axis=0)).mean((1, 2))
    out[os.path.basename(f)[:-4]] = dict(last20=round(float(d[-20:].mean()), 2), n=len(fr))
json.dump(out, open(sys.argv[2], 'w'), indent=1)
for k, v in out.items(): print(k, v)
