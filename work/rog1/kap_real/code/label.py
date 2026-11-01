# rog1 kap: per-frame state labels from tracks.json (video tracker) + GAUGE mocap z (cross-check only).
import json, numpy as np, sys, os
T = json.load(open('tracks.json')); MOC = sys.argv[1]
out = {}
for c, r in T.items():
    trk = r['trk']; n = r['n']
    vis = np.array([t is not None for t in trk]); xy = np.array([t[:2] if t else [np.nan, np.nan] for t in trk])
    # rest-height reference: median y of visible frames in the 2nd half of visible span (ball on plank)
    idx = np.where(vis)[0]
    yref = np.nanmedian(xy[idx[len(idx)//2:], 1])
    onp = vis & (np.abs(xy[:, 1] - yref) <= 12)
    # settle = start of first run of >=15 consecutive on-plank frames
    settle = None; run = 0
    for i in range(n):
        run = run + 1 if onp[i] else 0
        if run >= 15: settle = i - 14; break
    # mocap cross-check: time from first z-min (impact) to last sample with z > rest+5mm
    z = np.array(json.load(open(os.path.join(MOC, f'{c}.json')))['ball']['z']); zr = np.median(z[-8:])
    imp = int(np.argmax((z[1:-1] < z[:-2]) & (z[1:-1] <= z[2:]) & (z[1:-1] < zr + 30)) + 1)
    lastair = int(np.max(np.where(z > zr + 5)[0]))
    first_plank = int(idx[np.argmax(np.abs(xy[idx, 1] - yref) <= 12)]) if len(idx) else None
    lab = []
    for e in range(n):
        w = slice(max(0, e - 29), e + 1); vv = vis[w]
        L = 'AMBIG'
        if settle is not None and first_plank is not None and first_plank <= e <= settle - 10:
            L = 'BOUNCING'
        elif settle is not None and e >= settle + 12 and vv.sum() >= 24:
            p = xy[w][vv]; disp = float(np.hypot(*(p[-3:].mean(0) - p[:3].mean(0))))
            if disp >= 10: L = 'ROLLING'
            elif disp <= 3: L = 'REST'
        elif settle is not None and e > settle and not vis[e] and vis[max(0,e-10):e].sum() == 0 and e > idx.max():
            L = 'GONE'
        lab.append(L)
    out[c] = dict(n=n, yref=float(yref), settle_f=settle, first_plank_f=first_plank,
                  mocap_impact_to_settle_s=round((lastair - imp) / 30, 3),
                  video_firstplank_to_settle_s=None if settle is None else round((settle - first_plank) / 30, 3),
                  labels=lab)
    runs = []; prev = None
    for e, L in enumerate(lab):
        if L != prev: runs.append([L, e, e]); prev = L
        else: runs[-1][2] = e
    out[c]['runs'] = runs
    print(c, 'settle', settle, 'moc', out[c]['mocap_impact_to_settle_s'], 'vid', out[c]['video_firstplank_to_settle_s'],
          ' '.join(f'{L[:4]}{a}-{b}' for L, a, b in runs if L != 'AMBIG' or b - a > 3))
json.dump(out, open('labels.json', 'w'), indent=0)
