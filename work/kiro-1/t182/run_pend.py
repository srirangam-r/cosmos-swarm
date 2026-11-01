"""kiro-1, task 182: measure_pend v1 (raj-3, planted PASS via v5 pendulum estimates) run UNCHANGED on
(a) the 12 t175 pend10_mid_f93 Nano clips (24 fps), and (b) the real GAUGE pendulum-10 continuation,
real frames k93..k93+92 after raj-3's Cosmos input transform (dedup + letterbox 832x480), plus the mocap period
over the same time window (zero crossings of the swing-plane coordinate).
Usage: python3 run_pend.py <repo_root> <t175_clips_dir> <gauge_dir> <outdir>"""
import sys, os, json, glob, numpy as np, cv2
repo, cdir, gd, out = sys.argv[1:5]
sys.path.insert(0, repo + '/tools/trk_ballfall')
import trk, measure_pend as mp, measure_ball as mb
os.makedirs(out + '/qc', exist_ok=True)
res = {}
for p in sorted(glob.glob(cdir + '/k175_pend_mid_*.mp4')):
    name = os.path.basename(p)[:-4]
    F = trk.load(p)
    r = mp.measure(F, 24.0, keep_track=True)
    mp.qc(F, r, f'{out}/qc/{name}.png'); r.pop('track')
    res[name] = r; print(name, r['flag'], round(r['period_s'], 3), [round(x, 3) for x in r['period_ci95']], 'zc', round(r['period_zc_s'], 3), 'R2', round(r['r2'], 3), 'nh', r['n_halfcycles'], 'rel', r['release_frame'])

# real continuation
c = cv2.VideoCapture(f'{gd}/10.mp4'); R = []
while len(R) < 300:
    ok, f = c.read()
    if not ok: break
    R.append(f)
Fd, fac = mb.dedup(np.array(R).astype(np.float32)); fps = 30.0 * fac
LB = []
for f in Fd:
    L = np.zeros((480, 832, 3), np.float32); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); LB.append(L)
ref = cv2.imread(f'{repo}/work/ro-agy1/task140_rule_r_devscenes/inputs/pend10_mid_f93.png').astype(np.float32)
mad = {k: float(np.abs(LB[k] - ref).mean()) for k in range(88, 99)}; k93 = min(mad, key=mad.get)
W = np.array(LB[k93:k93 + 93])
r = mp.measure(W, fps, keep_track=True); mp.qc(W, r, f'{out}/qc/real_pend10_cont.png'); r.pop('track')
r['k93'] = k93; r['mad_k93'] = mad[k93]; r['video_fps_dedup'] = fps
res['real_pend10_cont'] = r
print('real', fps, k93, r['flag'], round(r['period_s'], 3), r['period_ci95'], 'zc', r['period_zc_s'], 'R2', r['r2'])

# mocap over same window: video time of frame k93 relative to video release
d = json.load(open(f'{gd}/10.json')); P = np.array([d['ball'][k] for k in 'xyz']).T / 1000.0; mf = d['FPS']; t = np.arange(len(P)) / mf
mu = P[:600].mean(0); _, _, Vt = np.linalg.svd(P[:600] - mu, full_matrices=False); a = (P - mu) @ Vt[0]
rel = int(np.argmax(np.abs(a - a[:5].mean()) > 0.005)); trel = t[rel]
# video release frame via measure_pend's release detector on the full deduped real video
rv = mp.measure(np.array(LB), fps, nboot=5)
t_rel_vid = rv['release_frame'] / fps
w0 = trel + (k93 / fps - t_rel_vid); w1 = w0 + 92 / fps
m = (t >= w0) & (t <= w1)
Tzc, nh, per = mp.zc_period(t[m], a[m])
res['mocap_pend10_window'] = dict(window_s_after_release=[float(w0 - trel), float(w1 - trel)], period_zc_s=Tzc, n_halfcycles=nh, zc_periods=[float(x) for x in per], video_release_frame=rv['release_frame'])
print('mocap window', w0 - trel, w1 - trel, 'Tzc', Tzc, nh)
json.dump(res, open(f'{out}/pend_periods.json', 'w'), indent=1)
