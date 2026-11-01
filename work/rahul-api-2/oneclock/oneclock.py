"""oneclock (rahul-api-2, task 162): is the fall from rest on the same clock as the rebound flights, inside ONE clip?

Clock-free, scale-free: with constant g and a fixed camera, every free-flight segment of y(t) (image px, t in frames)
is a parabola with the same curvature a [px/frame^2]. rho1 = a_flight1 / a_fall (physics: 1).

Track: tools/realball/firstfall.track (planted PASS 20/20; seeded colour+change tracker), whole clip.
Segments (PREREG.md): impacts = local maxima of y with prominence >= 8 px.
  fall    = onset (first frame y > y0 + 2 px) .. impact1 - 1
  flight k = impact_k + 2 .. impact_{k+1} - 2
Fit y = c0 + c1 t + (a/2) t^2 per segment (>= 5 frames), residual bootstrap SE of a.
Usage: python3 -I oneclock.py out.json clip1.mp4 [clip2.mp4 ...] [--fps 24] [--ppm 539.8] [--point 280,116]
"""
import sys, os, json, argparse, numpy as np, cv2
from scipy.signal import find_peaks
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', 'tools')
sys.path.insert(0, os.path.join(TOOLS, 'realball')); sys.path.insert(0, os.path.join(TOOLS, 'trk_ballfall'))
import firstfall  # noqa: E402
sys.path.insert(0, HERE)
from track2 import track2  # noqa: E402

VERSION = 'oneclock v1 (firstfall.track; prominence-8 impacts; per-segment free quadratic)'


def read(path):
    cap = cv2.VideoCapture(path); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(f)
    return np.array(F)


def fit_seg(t, y, nboot=300, seed=0):
    if len(t) < 5: return None
    c = np.polyfit(t, y, 2); res = y - np.polyval(c, t)
    rng = np.random.default_rng(seed)
    bs = [2 * np.polyfit(t, np.polyval(c, t) + rng.choice(res, len(t)), 2)[0] for _ in range(nboot)]
    return dict(a=float(2 * c[0]), a_se=float(np.std(bs)), n=int(len(t)), t=[int(t[0]), int(t[-1])],
                rms=float(np.sqrt((res ** 2).mean())), v_end=float(c[1] + 2 * c[0] * t[-1]), v_start=float(c[1] + 2 * c[0] * t[0]))


def analyse(cy, prom=8.0):
    T = len(cy); idx = np.where(np.isfinite(cy))[0]
    if len(idx) < 10: return dict(flag='lost', n_tracked=int(len(idx)))
    yi = np.interp(np.arange(idx[0], idx[-1] + 1), idx, cy[idx])          # gaps interpolated only for peak finding
    off = idx[0]
    y0 = float(np.median(cy[idx[:3]]))
    on = next((int(t) for t in idx if cy[t] > y0 + 2.0), None)
    pk, _ = find_peaks(yi, prominence=prom)
    imp = [int(p + off) for p in pk if on is not None and p + off > on]
    out = dict(flag='ok', y0=y0, onset=on, impacts=imp, n_tracked=int(len(idx)), last_tracked=int(idx[-1]))
    if on is None or not imp:
        out['flag'] = 'no_fall_or_no_impact'; return out
    def seg(a, b):
        tt = np.array([t for t in range(a, b + 1) if 0 <= t < T and np.isfinite(cy[t])])
        return fit_seg(tt.astype(float), cy[tt]) if len(tt) else None
    out['fall'] = seg(on, imp[0] - 1)
    out['flights'] = []
    for k in range(len(imp) - 1):
        out['flights'].append(seg(imp[k] + 2, imp[k + 1] - 2))
    f, fl = out['fall'], out['flights']
    if f and fl and fl[0]:
        out['rho1'] = fl[0]['a'] / f['a'] if f['a'] > 0 else None
        out['rho1_se'] = abs(out['rho1']) * np.hypot(f['a_se'] / f['a'], fl[0]['a_se'] / fl[0]['a']) if out['rho1'] else None
        out['e_v1'] = -fl[0]['v_start'] / f['v_end'] if f['v_end'] > 0 else None
    if f and len(fl) > 1 and fl[1] and f['a'] > 0:
        out['rho2'] = fl[1]['a'] / f['a']
    if fl and len(fl) > 1 and fl[0] and fl[1] and fl[0]['a'] > 0:
        out['fl2_over_fl1'] = fl[1]['a'] / fl[0]['a']
    return out


def run(path, fps, ppm, point, tracker='ff'):
    F = read(path)
    if tracker == 'ff': cx, cy, area, info = firstfall.track(F, point=point, pframe=0)
    else: cx, cy, area = track2(F, point)
    r = analyse(cy)
    r.update(clip=os.path.basename(path), fps=fps, ppm=ppm, method=VERSION, tracker=tracker,
             track_y=[None if not np.isfinite(v) else round(float(v), 2) for v in cy])
    s = fps * fps / ppm                                                    # px/frame^2 -> m/s^2 (context only)
    if r.get('fall'): r['g_eq_fall'] = r['fall']['a'] * s
    if r.get('flights') and r['flights'][0]: r['g_eq_flight1'] = r['flights'][0]['a'] * s
    return r


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('clips', nargs='+')
    ap.add_argument('--fps', type=float, default=24.0); ap.add_argument('--ppm', type=float, default=539.8)
    ap.add_argument('--point', default='280,116'); ap.add_argument('--tracker', default='ff', choices=['ff', 't2'])
    a = ap.parse_args(); pt = tuple(float(v) for v in a.point.split(','))
    res = []
    for c in a.clips:
        try: r = run(c, a.fps, a.ppm, pt, a.tracker)
        except Exception as ex: r = dict(clip=os.path.basename(c), flag='error', err=repr(ex))
        res.append(r)
        print(r['clip'], r.get('flag'), 'onset', r.get('onset'), 'imp', r.get('impacts'),
              'a_fall', None if not r.get('fall') else round(r['fall']['a'], 3),
              'a_fl1', None if not r.get('flights') or not r['flights'][0] else round(r['flights'][0]['a'], 3),
              'rho1', None if r.get('rho1') is None else round(r['rho1'], 3), flush=True)
    json.dump(res, open(a.out, 'w'), indent=1)
