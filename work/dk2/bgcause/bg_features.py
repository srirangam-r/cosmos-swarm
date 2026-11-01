"""Per-clip outside-box image features (nphys vs plain, same seed) vs dk1's per-clip
outside-box DOVER effect (rev6767 bg_motion.json). Question: which measurable change
outside the pendulum box tracks the per-clip DOVER cost? CPU only, no generation.
usage: python -I bg_features.py <gen_dir> <rev6767_out_dir> <out.json>"""
import sys, json, glob, os
import numpy as np, cv2
from scipy import stats

gen, rdir, outp = sys.argv[1:4]
meta = json.load(open(os.path.join(rdir, 'swap_meta.json')))['clips']
bgm = json.load(open(os.path.join(rdir, 'bg_motion.json')))['rows']

def read(p):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return np.stack(fr)

def feats(v, box):
    x0, y0, x1, y1 = box
    T, H, W, _ = v.shape
    m = np.ones((H, W), bool); m[max(0,y0-8):y1+8, max(0,x0-8):x1+8] = False
    g = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in v]).astype(np.float32)
    hsv = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in v]).astype(np.float32)
    lap = np.array([cv2.Laplacian(f, cv2.CV_32F, ksize=3)[m].var() for f in g])
    # fine detail: energy of (img - gaussian blur sigma 1)
    hf = np.array([((f - cv2.GaussianBlur(f, (0, 0), 1.0))[m] ** 2).mean() for f in g])
    # 8x8 block-edge energy ratio (mpeg-style blockiness)
    dx = np.abs(np.diff(g, axis=2))
    cols = np.arange(dx.shape[2]); mb = (cols % 8) == 7
    mm = m[:, :-1]
    blk = (dx[:, :, mb] * mm[:, mb]).sum((1, 2)) / mm[:, mb].sum() / ((dx[:, :, ~mb] * mm[:, ~mb]).sum((1, 2)) / mm[:, ~mb].sum())
    # temporal: frame-to-frame residual after removing a 5-frame temporal mean (grain/flicker)
    k = 5; cs = np.cumsum(np.pad(g, ((k//2, k//2), (0, 0), (0, 0)), mode='edge'), 0)
    cs = np.concatenate([np.zeros((1,) + g.shape[1:], np.float32), cs])
    tm = (cs[k:] - cs[:-k]) / k
    tres = np.abs(g - tm)[:, m].mean()
    d0 = np.abs(g[1:] - g[0])[:, m].mean(1)  # drift from the conditioning frame
    return dict(lap=float(lap[1:].mean() / lap[0]), hf=float(hf[1:].mean() / hf[0]),
                blk=float(blk[1:].mean()), tres=float(tres), drift=float(d0.mean()),
                drift_last=float(d0[-10:].mean()),
                sat=float(hsv[1:, :, :, 1][:, m].mean() - hsv[0, :, :, 1][m].mean()),
                luma=float(g[1:, m].mean() - g[0][m].mean()),
                contrast=float(g[1:, m].std() / g[0][m].std()))

rows = {}
for key, c in sorted(meta.items()):
    sc, s = key.split('_')
    p = os.path.join(gen, f't276_real_{sc}_plain_{s}.mp4'); n = os.path.join(gen, f't276_real_{sc}_nphys_{s}.mp4')
    fp, fn = feats(read(p), c['box']), feats(read(n), c['box'])
    rows[key] = dict(plain=fp, nphys=fn, d={k: fn[k] - fp[k] for k in fp}, bg_effect=bgm[key]['bg_effect'])
    print(key, {k: round(v, 3) for k, v in rows[key]['d'].items()}, round(rows[key]['bg_effect'], 3), flush=True)

keys = sorted(rows); y = np.array([rows[k]['bg_effect'] for k in keys])
scn = np.array([k.split('_')[0] for k in keys])
summ = {}
for f in rows[keys[0]]['d']:
    x = np.array([rows[k]['d'][f] for k in keys])
    # within-scene (demeaned by scene) correlation too, since 6 scenes x 3 seeds
    xw = x - np.array([x[scn == q].mean() for q in scn]); yw = y - np.array([y[scn == q].mean() for q in scn])
    summ[f] = dict(mean_delta=float(x.mean()), n_neg=int((x < 0).sum()),
                   pearson=float(stats.pearsonr(x, y)[0]), spearman=float(stats.spearmanr(x, y)[0]),
                   within_scene_pearson=float(stats.pearsonr(xw, yw)[0]),
                   plain_mean=float(np.mean([rows[k]['plain'][f] for k in keys])),
                   nphys_mean=float(np.mean([rows[k]['nphys'][f] for k in keys])))
for f, v in summ.items(): print(f, {k: round(w, 3) for k, w in v.items()})
json.dump(dict(rows=rows, summary=summ, n=len(keys)), open(outp, 'w'), indent=1)
