"""Independent replication of poornima-1 #1958 (V2V5/V2V9 vs I2V continuation of real GAUGE bounce).

My own metrics (deliberately different ROIs from poornima-1's table/curtain ROIs):
  LM  = late motion: mean over k in [K0, K1) of mean |G[cut+k+1] - G[cut+k]| (grayscale 0-255, full
        active frame, letterbox rows excluded), i.e. frame-to-frame change 2.0-3.3 s after the last real frame.
  DR  = scene drift: mean |G[cut+K1] - G[cut]| on the upper 40% of the active frame (background: curtain,
        robot base; the ball path is mostly lower), plus DRfull on the whole active frame.
Alignment: every clip is indexed from its last real context frame (sidecar last_real_frame_index_in_output;
0 for I2V). Real reference: the same GAUGE video, deduplicated (drop exact-duplicate frames of the 25-in-30
container), letterboxed 1280x720 -> 832x468 + 6 px pad, continued from the same dedup cut frame.
Usage: python3 rep1958.py CLIPDIR CTXDIR REALDIR OUT.json
"""
import json, sys, glob, os
import numpy as np, cv2

K0, K1 = 48, 80
TOP, BOT = 3, 237  # active rows at 416x240 (all frames area-downscaled to 416x240)


def read_gray(path):
    cap = cv2.VideoCapture(path); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if g.shape[1] == 832: g = cv2.resize(g, (416, 240), interpolation=cv2.INTER_AREA)
        fr.append(g)
    return fr


def letterbox(g):
    r = cv2.resize(g, (832, 468), interpolation=cv2.INTER_AREA)
    out = np.zeros((480, 832), np.float32); out[6:474] = r
    return cv2.resize(out, (416, 240), interpolation=cv2.INTER_AREA)


def metrics(fr, cut):
    a = fr[cut:]
    if len(a) <= K1: return None
    lm = np.mean([np.abs(a[k + 1][TOP:BOT] - a[k][TOP:BOT]).mean() for k in range(K0, K1)])
    up = TOP + int(0.4 * (BOT - TOP))
    dr = np.abs(a[K1][TOP:up] - a[0][TOP:up]).mean()
    drf = np.abs(a[K1][TOP:BOT] - a[0][TOP:BOT]).mean()
    return dict(LM=float(lm), DR=float(dr), DRfull=float(drf))


def real_dedup(path):
    cap = cv2.VideoCapture(path); raw = []
    while True:
        ok, f = cap.read()
        if not ok: break
        raw.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32))
    keep = [0]
    for i in range(1, len(raw)):
        if np.abs(raw[i] - raw[keep[-1]]).mean() > 0.05: keep.append(i)
    return raw, keep


def main(clipdir, ctxdir, realdir, out):
    meta = json.load(open(os.path.join(ctxdir, 'meta.json')))
    res = {'clips': {}, 'real': {}, 'K0': K0, 'K1': K1}
    for cut, m in meta.items():
        vid = m['video'].split('/')[-1].replace('.mp4', '')
        raw, keep = real_dedup(os.path.join(realdir, f'ball{vid}.mp4'))
        d_last = m['dedup_frames'][-1]; r_last = m['raw_frames'][-1]
        # my dedup index vs the sidecar's; and pixel check vs the context PNG
        my_raw = keep[d_last] if d_last < len(keep) else None
        # align on the sidecar's RAW index of the last context frame (my dedup can drop static early frames)
        d_last = min(range(len(keep)), key=lambda j: abs(keep[j] - r_last))
        lb = [letterbox(raw[i]) for i in keep]
        png = cv2.resize(cv2.imread(os.path.join(ctxdir, f'{cut}_8.png'), cv2.IMREAD_GRAYSCALE).astype(np.float32), (416, 240), interpolation=cv2.INTER_AREA)
        pix = float(np.abs(lb[d_last] - png)[TOP:BOT].mean())
        mr = metrics(lb, d_last)
        res['real'][cut] = dict(my_raw_for_dedup=my_raw, sidecar_raw=r_last, ctx_png_mad=pix,
                                n_after_cut=len(lb) - d_last, **(mr or {}))
    for p in sorted(glob.glob(os.path.join(clipdir, '*.mp4'))):
        sc = json.load(open(p[:-4] + '.json'))
        cut = sc.get('last_real_frame_index_in_output', 0) or 0
        fr = read_gray(p)
        mm = metrics(fr, cut)
        res['clips'][os.path.basename(p)[:-4]] = dict(cut=sc['cut'], mode=sc['mode'], seed=sc['seed'],
                                                      cut_idx=cut, nf=len(fr), **(mm or {}))
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:5])
