"""raj-3: release-aware g from GAUGE real ball-drop VIDEO (dedup -> 25 fps, free-v0 fit from sustained onset).
Usage: python3 -I video_fits.py <gauge_real_dir> <out.json>
Scale A: ball horizontal width (px) in free flight -> D=0.06 m. Scale B: pixel drop / mocap drop (timing-only check, uses mocap)."""
import sys, json, numpy as np, cv2

root = sys.argv[1]

def load(p):
    cap = cv2.VideoCapture(p); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(f)
    return F

def track(F):
    G = np.stack([cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (5, 5), 0) for f in F]).astype(np.int16)
    bg = np.median(G, axis=0).astype(np.int16)
    out = []
    for g in G:
        m = (np.abs(g - bg) > 22).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        out.append([(st[k, 4], cen[k, 0], cen[k, 1], st[k, 2], st[k, 3], st[k, 1], st[k, 1] + st[k, 3]) for k in range(1, n) if st[k, 4] > 80])
    return out

res = {}
for i in range(1, 23):
    F = load(f'{root}/video/{i}.mp4')
    keep = [0] + [k for k in range(1, len(F)) if np.abs(F[k].astype(np.int16) - F[k - 1]).mean() > 0.5]
    F = [F[k] for k in keep]
    B = track(F)
    # held-ball position: largest blob in the upper half over the first 10 frames -> x column of the fall
    up = [b for bb in B[:10] for b in bb if b[2] < 360]
    if not up: res[i] = dict(err='no held blob'); continue
    x0 = float(np.median([b[1] for b in sorted(up)[-5:]])); y0 = float(np.median([b[2] for b in sorted(up)[-5:]]))
    # per frame: blob in column |x-x0|<60 with smallest top (y_top) >= y0-30 -> follow the falling ball top edge and centroid
    ys, tops, ws, fr = [], [], [], []
    for k, bb in enumerate(B):
        c = [b for b in bb if abs(b[1] - x0) < 70 and b[5] > y0 - 40]
        if not c: continue
        b = max(c, key=lambda b: b[0])
        ys.append(b[2]); tops.append(b[5]); ws.append(b[3]); fr.append(k)
    ys, tops, ws, fr = map(np.array, (ys, tops, ws, fr))
    # release: first frame where the top edge has moved > 6 px below its held median and keeps going down
    held = np.median(tops[:10])
    rel = next((m for m in range(len(tops) - 3) if tops[m] > held + 6 and tops[m + 1] > tops[m] and tops[m + 2] > tops[m + 1]), None)
    if rel is None: res[i] = dict(err='no release'); continue
    # impact: first frame where the top edge stops descending
    imp = rel
    while imp + 1 < len(tops) and tops[imp + 1] > tops[imp] + 2 and fr[imp + 1] - fr[imp] == 1: imp += 1
    s = slice(max(rel - 1, 0), imp + 1)
    t = fr[s] / 25.0; yt = tops[s].astype(float)  # top edge: immune to downward blur streak growth
    if len(t) < 4: res[i] = dict(err=f'only {len(t)} frames', rel=int(rel), imp=int(imp)); continue
    c = np.polyfit(t, yt, 2); gpx = 2 * c[0]
    t30 = fr[s] * 1.2 / 30.0  # alternative timing: keep original 30fps index of each unique frame
    c30 = np.polyfit(np.array([keep[k] for k in fr[s]]) / 30.0, yt, 2)
    wfree = float(np.median(ws[s]))
    d = json.load(open(f'{root}/json/{i}.json'))['ball']; z = np.array(d['z'])
    zi = int(np.argmax(z)); j = zi + 1
    while j < len(z) - 1 and not (z[j] <= z[j - 1] and z[j] < z[j + 1]): j += 1
    drop_m = (z[zi] - z[j]) / 1000; drop_px = float(yt[-1] - held)
    res[i] = dict(n_fit=len(t), rel_frame=int(fr[rel]), imp_frame=int(fr[imp]), g_px=gpx, g_px_30idx=2 * c30[0], w_free_px=wfree,
                  g_scaleA_width=gpx * 0.06 / wfree, drop_px=drop_px, drop_mocap_m=drop_m, g_scaleB_mocapdrop=gpx * drop_m / drop_px,
                  g_scaleB_30idx=2 * c30[0] * drop_m / drop_px, rms_px=float(np.std(yt - np.polyval(c, t))))
    print(i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res[i].items()}, flush=True)
ok = [r for r in res.values() if 'err' not in r]
summ = {}
for key in ['g_scaleA_width', 'g_scaleB_mocapdrop', 'g_scaleB_30idx']:
    v = np.array([r[key] for r in ok]); summ[key] = dict(mean=v.mean(), median=float(np.median(v)), se=v.std(ddof=1) / np.sqrt(len(v)), sd=v.std(ddof=1), n=len(v))
    print(key, summ[key])
print('failed:', {k: r for k, r in res.items() if 'err' in r})
json.dump(dict(per_clip=res, summary=summ), open(sys.argv[2], 'w'), indent=1, default=float)
