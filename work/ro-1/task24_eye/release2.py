# ro-1 task24 re-score (blind). Held ball on THIS eval input is at (529,46), D~47 px (NOT 281,119).
# Metrics per clip: keep_t = fraction of f0 ball pixels (gray<60 in box x495-565,y15-80) still dark (<70) at frame t.
# lowest_dark_y_t = lowest row (y) of any dark blob >=300 px in the sky region (y<330, content x160-670) -> ball descent.
import av, numpy as np, glob, os, json, sys
from scipy import ndimage
src, out = sys.argv[1], sys.argv[2]
res = {}
for f in sorted(glob.glob(src + '/*.mp4')):
    c = os.path.basename(f)[:6]
    g = [x.to_ndarray(format='gray').astype(np.float32) for x in av.open(f).decode(video=0)]
    box = np.zeros(g[0].shape, bool); box[15:80, 495:565] = True
    m0 = (g[0] < 60) & box
    keep = [float(((gi < 70) & m0).sum() / max(m0.sum(), 1)) for gi in g]
    # first frame where keep < 0.3 (ball has left its held position)
    left = next((i for i, k in enumerate(keep) if k < 0.3), None)
    back = left is not None and keep[-1] > 0.6
    res[c] = dict(n_mask=int(m0.sum()), keep_f92=round(keep[-1], 2), keep_min=round(min(keep), 2), first_left=left, returned=back,
                  keep_seq=[round(k, 2) for k in keep[::4]])
json.dump(res, open(out, 'w'), indent=1)
for c, r in res.items(): print(c, r['n_mask'], r['keep_min'], r['keep_f92'], r['first_left'], r['returned'])
