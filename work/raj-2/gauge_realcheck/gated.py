# raj-2 diagnostic: release-gated free-fall fit on trk_ballfall blob tracks (real GAUGE clips), vs mocap.
import json, sys, numpy as np
FPS, D = 30.0, 0.06
def mocap(i):
    d = json.load(open(f'json/{i}.json')); z = np.array(d['ball']['z'])/1000; t = np.arange(len(z))/d['FPS']
    i0 = int(np.argmax(z)); j = i0+1
    while j < len(z)-1 and not (z[j] <= z[j-1] and z[j] < z[j+1]): j += 1
    g_all = -2*np.polyfit(t[i0:j], z[i0:j], 2)[0]
    g_in = -2*np.polyfit(t[i0+1:j-1], z[i0+1:j-1], 2)[0]   # drop release & pre-contact frames
    return g_all, g_in
rows = []
for i in range(1, 23):
    try: B = json.load(open(f'tracks/{i}.json'))
    except Exception: continue
    cy = np.array([b[1] if b else np.nan for b in B]); sh = np.array([b[4] if b else np.nan for b in B])
    hold = np.nanmedian(cy[:10]); r = int(np.argmax(cy > hold+4))
    k = None
    for j in range(r+2, min(r+30, len(cy)-1)):
        if cy[j+1] < cy[j]-3: k = j; break
    if k is None or k-r < 4: rows.append((i, None)); continue
    idx = np.arange(r, k); ok = ~np.isnan(cy[idx]); idx = idx[ok]
    a_px = 2*np.polyfit(idx/FPS, cy[idx], 2)[0]
    s_rest = D/np.nanmedian(sh[k+20:k+45]); s_fall = D/np.nanmedian(sh[idx])
    s_all = D/np.nanmedian(sh)                                            # trk.py's choice
    gm = mocap(i)
    rows.append((i, dict(n=len(idx), a_px=a_px, g_rest=a_px*s_rest, g_fall=a_px*s_fall, g_trkscale=a_px*s_all,
                         d_rest=D/s_rest, d_all=D/s_all, mocap_g=gm[0], mocap_g_inner=gm[1])))
for i, r in rows: print(i, {k: round(v, 2) for k, v in r.items()} if r else 'no-impact-found')
def st(key):
    v = np.array([r[key] for _, r in rows if r]); return f'{key}: {v.mean():.2f} ± {v.std(ddof=1)/np.sqrt(len(v)):.2f} (sd {v.std(ddof=1):.2f}, n={len(v)})'
for k in ['g_rest', 'g_fall', 'g_trkscale', 'mocap_g', 'mocap_g_inner']: print(st(k))
json.dump(dict(rows), open('gated_results.json', 'w'), indent=1)
