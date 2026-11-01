"""kiro-1, task 175 follow-up: check pend_angle.py against GAUGE mocap on the REAL pend10 continuation,
and compare Nano's pend_mid clips with the real swing over the same window.
1. Real GAUGE pendulum 10 -> dedup + letterbox 832x480 (raj-3's Cosmos input transform, task 8). Frame 93 should equal pend10_mid_f93.png.
2. pend_angle.angles() on real frames 93..185 (= Nano clip frames 0..92).
3. Mocap angle from vertical: swing-plane PCA + circle fit (pivot, L), theta = arcsin((a-pa)/L); aligned to the video by release time.
Usage: python3 pend_real_check.py <gauge_dir with 10.mp4 10.json> <repo_root>"""
import sys, json, numpy as np, cv2
from scipy.optimize import least_squares
gd, repo = sys.argv[1:3]
sys.path.insert(0, repo + '/tools/trk_ballfall'); import measure_ball as mb
sys.argv = [sys.argv[0]]
import importlib.util
spec = importlib.util.spec_from_file_location('pa', __file__.replace('pend_real_check.py', 'pend_angle_lib.py')); pa = importlib.util.module_from_spec(spec); spec.loader.exec_module(pa)

# 1. real video at Cosmos resolution
c = cv2.VideoCapture(f'{gd}/10.mp4'); R = []
while len(R) < 300:
    ok, f = c.read()
    if not ok: break
    R.append(f)
Fd, fac = mb.dedup(np.array(R).astype(np.float32)); fps = 30.0 * fac
LB = []
for f in Fd:
    L = np.zeros((480, 832, 3), np.uint8); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); LB.append(L)
ref = cv2.imread(f'{repo}/work/ro-agy1/task140_rule_r_devscenes/inputs/pend10_mid_f93.png')
mad = {k: float(np.abs(LB[k].astype(float) - ref).mean()) for k in range(88, 99)}
k93 = min(mad, key=mad.get)
print('fps', fps, 'best match to input', k93, 'MAD', round(mad[k93], 2), 'MAD@93', round(mad[93], 2))
win = LB[k93:k93 + 93]
a_real = pa.angles_frames(win)
m_real = pa.metrics(a_real)
print('real video (pend_angle):', {k: v for k, v in m_real.items() if k != 'trace'})

# 3. mocap
d = json.load(open(f'{gd}/10.json')); P = np.array([d['ball'][k] for k in 'xyz']).T / 1000.0; mf = d['FPS']; t = np.arange(len(P)) / mf
mu = P[:600].mean(0); _, _, Vt = np.linalg.svd(P[:600] - mu, full_matrices=False); a = (P - mu) @ Vt[0]; b = (P - mu) @ Vt[1]
rel = int(np.argmax(np.abs(a - a[:5].mean()) > 0.005)); trel = t[rel]
m = (t >= trel) & (t <= trel + 8)
sols = [least_squares(lambda p: np.hypot(a[m] - p[0], b[m] - p[1]) - p[2], [0, sg * 0.3, 0.3]) for sg in (1, -1)]
pa_, pb_, Lm = min(sols, key=lambda s: s.cost).x
th = np.degrees(np.arcsin(np.clip((a - pa_) / Lm, -1, 1)))
# video release frame (pick.json, measure_pend on the same transform): 55
vrel = json.load(open(f'{repo}/work/ro-3/task99_midswing_pendulum/inputs/pick.json'))['10']['release_frame']
t0 = (k93 - vrel) / fps; t1 = t0 + 92 / fps
def mwin(lo, hi):
    mm = (t >= trel + lo) & (t <= trel + hi); return th[mm]
mo_all = mwin(t0, t1)
mo_e = mwin(t0 + 1 / fps, t0 + 31 / fps); mo_l = mwin(t0 + 62 / fps, t1)
amp = lambda v: float((np.percentile(v, 95) - np.percentile(v, 5)) / 2)
m_mocap = dict(L_m=float(Lm), t_window_after_release=[float(t0), float(t1)], amp_early=amp(mo_e), amp_late=amp(mo_l), max_abs=float(np.abs(mo_all).max()),
               amp_early_true=float(np.abs(mo_e).max()), amp_late_true=float(np.abs(mo_l).max()))
print('mocap:', m_mocap)
# tool on mocap angles restricted to what the tool can see (|theta| < ~80 deg saturation): report fraction beyond 80
m_mocap['frac_abs_gt80'] = float((np.abs(mo_all) > 80).mean())

# 4. Nano clips with the same tool (recompute, same code)
nano = {}
import glob
for p in sorted(glob.glob('clips/k175_pend_mid_*.mp4')):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    nano[p.split('/')[-1][:-4]] = {k: v for k, v in pa.metrics(pa.angles_frames(fr)).items() if k != 'trace'}
def agg(key):
    v = np.array([x[key] for x in nano.values() if x[key] is not None]); return float(v.mean()), float(v.std(ddof=1) / np.sqrt(len(v))), len(v)
summ = {k: agg(k) for k in ('amp_early', 'amp_late', 'max_abs')}
print('nano (all 12, mean, SE, n):', summ)
json.dump(dict(fps=fps, match_frame=k93, match_mad=mad[k93], real_tool=m_real, mocap=m_mocap, nano=nano, nano_summary=summ,
               nano_minus_real_tool={k: summ[k][0] - m_real[k] for k in summ}), open('pend_real_check.json', 'w'), indent=1)
