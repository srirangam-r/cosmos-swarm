"""Planted-case estimates from the oneclock pipeline (track2 + segment fits). Seed = largest |frame0 - median| blob;
scale = 0.10 m / equivalent diameter of that blob; g = a_fall * fps^2 * m/px. e = -v_flight1 / v_fall at the
impact time where the fall and flight-1 parabolas intersect. Also prints rho1 (expected 1 on rendered physics)."""
import sys, os, json, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oneclock
from track2 import track2

def seed(F):
    B = np.median(F[::2], 0).astype(np.float32)
    d = cv2.GaussianBlur(np.abs(F[0].astype(np.float32) - B).max(2), (0, 0), 1.0)
    n, l, st, cen = cv2.connectedComponentsWithStats((d > 25).astype(np.uint8))
    i = 1 + int(np.argmax(st[1:, 4])); return tuple(cen[i]), 2 * np.sqrt(st[i, 4] / np.pi)

def est(path, fps, diam=0.10):
    F = oneclock.read(path); pt, dpx = seed(F)
    cx, cy, area = track2(F, pt)
    r = oneclock.analyse(cy); mpp = diam / dpx; out = dict(seed=[float(pt[0]), float(pt[1])], d_px=float(dpx), flag=r.get('flag'))
    if r.get('fall'):
        out['g'] = r['fall']['a'] * fps * fps * mpp; out['fall'] = r['fall']
    if r.get('rho1') is not None:
        out['rho1'] = r['rho1']
        # parabola coefficients back from fits: refit to get c for intersection
        f, fl = r['fall'], r['flights'][0]
        def coef(seg):
            tt = np.array([t for t in range(seg['t'][0], seg['t'][1] + 1) if np.isfinite(cy[t])], float)
            return np.polyfit(tt, cy[tt.astype(int)], 2)
        cf, cl = coef(f), coef(fl); roots = np.roots(cf - cl); i1 = r['impacts'][0]
        roots = [x.real for x in roots if abs(x.imag) < 1e-9 and i1 - 2 <= x.real <= i1 + 2]
        if roots:
            ts = roots[0]; vf = np.polyval(np.polyder(cf), ts); vl = np.polyval(np.polyder(cl), ts)
            out['e'] = float(-vl / vf); out['t_impact'] = float(ts)
    return out

if __name__ == '__main__':
    pl = json.load(open(sys.argv[1])); d = sys.argv[2]; res = {}
    for c in pl['clips']:
        if 'g' not in c['params']: continue
        o = est(os.path.join(d, c['clip_id'] + '.mp4'), c['fps']); res[c['clip_id']] = o
        print(c['clip_id'], c['params'], 'd_px %.1f' % o['d_px'], 'g', None if 'g' not in o else round(o['g'], 3),
              'e', None if 'e' not in o else round(o['e'], 3), 'rho1', None if 'rho1' not in o else round(o['rho1'], 3), flush=True)
    json.dump(res, open(sys.argv[3], 'w'), indent=1)
