# Run from the GAUGE data dir (video/, json/, tracks/): python3 real_ball.py <repo_root>
# raj-2: real-footage ball-drop fit for GAUGE clips (25 fps content inside a 30 fps container).
# Uses stored trk.blobs(mode='ball') tracks (tracks/<i>.json, from dumptracks.py, trk @5e06ff7) + video frame diffs.
# Steps: (1) drop exact-duplicate frames, re-time distinct frames uniformly (fps_src = fps * n_distinct/n_out);
# (2) hinge fit y0 + g/2 (t-t0)^2 [t>t0] up to first impact (measure_ball.fit_hinge, raj-3 v4), pixel units;
# (3) scale: (a) S_free = median minAreaRect short side over slow free-ball frames after impact;
#             (b) S_cal = mocap-calibrated px/m from hold->rest pixel displacement vs mocap z (decomposition only).
import sys, json, numpy as np, cv2
R = sys.argv[1]; sys.path.insert(0, R + '/tools/trk_ballfall')
import measure_ball as mb
D = 0.06; FPS = 30.0
def dups(path):
    cap = cv2.VideoCapture(path); prev = None; d = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None: d.append(np.abs(g - prev).mean())
        prev = g
    d = np.array(d); return set((np.where(d < 0.1 * np.median(d))[0] + 1).tolist()), len(d) + 1
def mocap(i):
    d = json.load(open(f'json/{i}.json')); z = np.array(d['ball']['z']) / 1000; t = np.arange(len(z)) / d['FPS']
    i0 = int(np.argmax(z)); j = i0 + 1
    while j < len(z) - 1 and not (z[j] <= z[j - 1] and z[j] < z[j + 1]): j += 1
    p = mb.fit_hinge(t[i0:j], (z[i0] - z[i0:j]))          # same hinge estimator on mocap, for a like-for-like reference
    return dict(g_quad=float(-2 * np.polyfit(t[i0:j], z[i0:j], 2)[0]), g_hinge=float(p[1]), z_rel=float(z[i0]), z_rest=float(np.median(z[-10:])))
rows = {}
for i in range(1, 23):
    B = json.load(open(f'tracks/{i}.json')); dup, n = dups(f'video/{i}.mp4')
    keep = [k for k in range(len(B)) if k not in dup]; fsrc = FPS * len(keep) / len(B)
    cy = np.array([B[k][1] if B[k] else np.nan for k in keep]); cx = np.array([B[k][0] if B[k] else np.nan for k in keep])
    sh = np.array([B[k][4] if B[k] else np.nan for k in keep]); t = np.arange(len(keep)) / fsrc
    ok = ~np.isnan(cy)
    hold = np.nanmedian(cy[:8]); r = int(np.argmax(cy > hold + 4))           # first clearly-moving distinct frame
    a = max(r - 6, 0)                                                         # include some hold frames: hinge finds t0
    k = None
    for j in range(r + 1, min(r + 30, len(cy) - 1)):
        if cy[j + 1] < cy[j] - 3: k = j; break                               # first reversal = impact
    if k is None: rows[i] = None; continue
    idx = np.arange(a, k); idx = idx[ok[idx]]                                 # exclude impact frame itself
    U = 1/800.0                                                               # fit in ~metres (fit_hinge bounds g<=200)
    p = mb.fit_hinge(t[idx], cy[idx] * U); g_px = p[1] / U
    # free-ball scale: slow frames after the impact (speed < 2 px/frame), ball not in gripper
    sp = np.hypot(np.gradient(cx), np.gradient(cy)); post = np.arange(k + 3, len(cy))
    slow = post[(sp[post] < 2.0) & ok[post]]; S_free = float(np.median(sh[slow])) if len(slow) >= 5 else np.nan
    m = mocap(i); rest_px = np.nanmedian(cy[slow]) if len(slow) >= 5 else np.nan
    ppm_cal = (rest_px - hold) / (m['z_rel'] - m['z_rest'])
    # same, with naive t = frame/30 and duplicates kept (what the tools do)
    idx30 = [kk for kk in range(len(B)) if B[kk] and keep[a] <= kk < keep[k]]
    p30 = mb.fit_hinge(np.array(idx30) / FPS, np.array([B[kk][1] for kk in idx30]) * U); p30 = p30 / np.array([U, U, 1])
    rows[i] = dict(n_fit=int(len(idx)), fps_src=fsrc, t0=float(p[2]), g_px=float(g_px), g_px_30dup=float(p30[1]),
                   S_free=S_free, n_slow=int(len(slow)), ppm_cal=float(ppm_cal),
                   g_free=float(g_px * D / S_free), g_cal=float(g_px / ppm_cal), g_cal_30dup=float(p30[1] / ppm_cal),
                   S_cal=float(ppm_cal * D), **{'mocap_' + kk: v for kk, v in m.items()})
    print(i, {kk: round(v, 2) for kk, v in rows[i].items()}, flush=True)
json.dump(rows, open('real_ball_results.json', 'w'), indent=1)
def st(key):
    v = np.array([r[key] for r in rows.values() if r and np.isfinite(r[key])]); md = np.median(v)
    return f'{key}: mean {v.mean():.2f} ± {v.std(ddof=1)/np.sqrt(len(v)):.2f} SE (sd {v.std(ddof=1):.2f}, median {md:.2f}, n={len(v)})'
for kk in ['g_free', 'g_cal', 'g_cal_30dup', 'mocap_g_quad', 'mocap_g_hinge', 'S_free', 'S_cal', 'fps_src', 'n_fit']: print(st(kk))
