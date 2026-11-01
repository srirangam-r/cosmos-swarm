"""kiro-1 t185: make a mid-swing I2V input from real GAUGE pendulum clip N at the same time-after-release
as pend10_mid_f93 (which sits 1.52 s after release), using the same transform as run_pend.py
(dedup, letterbox 1280x720 -> 832x468 + 6 px)."""
import sys, json, numpy as np, cv2
repo, gd, N, out = sys.argv[1:5]
sys.path.insert(0, repo + '/tools/trk_ballfall')
import measure_pend as mp, measure_ball as mb
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
L10, fps10 = lbvid(f'{gd}/10.mp4'); r10 = mp.measure(L10, fps10, nboot=5)
dt = (93 - r10['release_frame']) / fps10
LN, fpsN = lbvid(f'{gd}/{N}.mp4'); rN = mp.measure(LN, fpsN, nboot=5)
k = int(round(rN['release_frame'] + dt * fpsN))
cv2.imwrite(out, LN[k].clip(0, 255).astype(np.uint8))
json.dump(dict(src=f'GAUGE pendulum {N}', fps_dedup=fpsN, release_frame=rN['release_frame'], k=k, dt_after_release=dt,
               pend10=dict(release_frame=r10['release_frame'], fps=fps10)), open(out + '.json', 'w'), indent=1)
print(fps10, r10['release_frame'], dt, fpsN, rN['release_frame'], k)
