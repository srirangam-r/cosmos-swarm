"""kiro-1 t185: measure_pend v1 on the real continuation of each input (93 frames from the input frame), plus mocap
zero-crossing period over the same window. Same code path as t182/run_pend.py."""
import sys, json, numpy as np
repo, gd = sys.argv[1:3]
sys.path.insert(0, repo + '/tools/trk_ballfall')
import measure_pend as mp
import cv2, measure_ball as mb
def lbvid(path):
    c = cv2.VideoCapture(path); R = []
    while len(R) < 300:
        ok, f = c.read()
        if not ok: break
        R.append(f)
    Fd, fac = mb.dedup(np.array(R).astype(np.float32)); fps = 30.0 * fac
    LB = []
    for f in Fd:
        L = np.zeros((480, 832, 3), np.float32); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); LB.append(L)
    return np.array(LB), fps
out = {}
for N, k in [(10, 93), (12, 101)]:
    LB, fps = lbvid(f'{gd}/{N}.mp4')
    W = LB[k:k + 93]; r = mp.measure(W, fps, keep_track=True); mp.qc(W, r, f'qc/real_pend{N}_f{k}.png'); r.pop('track')
    rv = mp.measure(LB, fps, nboot=5)
    d = json.load(open(f'{gd}/{N}.json')); P = np.array([d['ball'][c] for c in 'xyz']).T / 1000.0; t = np.arange(len(P)) / d['FPS']
    mu = P[:600].mean(0); _, _, Vt = np.linalg.svd(P[:600] - mu, full_matrices=False); a = (P - mu) @ Vt[0]
    rel = int(np.argmax(np.abs(a - a[:5].mean()) > 0.005)); trel = t[rel]
    w0 = trel + (k - rv['release_frame']) / fps; w1 = w0 + 92 / fps; m = (t >= w0) & (t <= w1)
    Tzc, nh, per = mp.zc_period(t[m], a[m])
    out[f'pend{N}_f{k}'] = dict(video=r, video_fps=fps, video_release_frame=rv['release_frame'], mocap_window_s=[w0 - trel, w1 - trel], mocap_Tzc=Tzc, mocap_nh=nh)
    print(N, k, r['flag'], round(r['period_s'], 4), r['period_ci95'], 'zc', r['period_zc_s'], 'mocap', Tzc, nh, w0 - trel)
json.dump(out, open('real_ref.json', 'w'), indent=1, default=float)
