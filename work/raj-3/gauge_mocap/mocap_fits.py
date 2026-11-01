"""raj-3: g from GAUGE real-ball mocap z with different free-fall estimators (review of finding 125, claim c).
Usage: python3 -I mocap_fits.py <json_dir> <out.json>"""
import sys, json, numpy as np
from scipy.optimize import least_squares

def hinge(p, t): return p[0] - 0.5 * p[1] * np.clip(t - p[2], 0, None) ** 2   # z falls

def fit_hinge(t, z):
    best = None
    for t0 in np.linspace(t[0] - 0.1, t[-4], 15):
        s = least_squares(lambda p: hinge(p, t) - z, [z[0], 9.0, t0], bounds=([-np.inf, 0, t[0] - 0.5], [np.inf, 100, t[-1]]))
        if best is None or s.cost < best.cost: best = s
    return best.x, best.fun

out = {}
for i in range(1, 23):
    d = json.load(open(f'{sys.argv[1]}/{i}.json')); fps = d['FPS']; z = np.array(d['ball']['z']) / 1000.0
    t = np.arange(len(z)) / fps
    i0 = int(np.argmax(z)); j = i0 + 1
    while j < len(z) - 1 and not (z[j] <= z[j - 1] and z[j] < z[j + 1]): j += 1   # first local min = impact frame
    s = slice(i0, j)                                     # pre-impact frames (impact frame excluded)
    g_free_all = -2 * np.polyfit(t[s], z[s], 2)[0]       # raj-2 estimator (free v0, from argmax)
    p, res = fit_hinge(t[s], z[s])                       # hinge: v0=0 at free t0
    d2 = np.diff(z[s], 2) * fps ** 2                      # per-frame second differences
    # release = first frame after which every 2nd difference is within 25% of the late median (sustained free fall)
    gm = -np.median(d2[len(d2) // 2:])
    k = next(m for m in range(len(d2)) if np.all(np.abs(-d2[m:] - gm) < 0.25 * gm))
    ss = slice(i0 + k, j)
    c = np.polyfit(t[ss], z[ss], 2); g_free_rel = -2 * c[0]
    rr = z[ss] - np.polyval(c, t[ss])
    out[i] = dict(n_pre=j - i0, g_free_from_argmax=g_free_all, g_hinge=p[1], t0_hinge_frames=(p[2] - t[i0]) * fps,
                  hinge_rms_mm=1000 * res.std(), release_frame=k, n_rel=j - i0 - k, g_free_from_release=g_free_rel,
                  rel_rms_mm=1000 * rr.std(), d2_first4=list(np.round(-d2[:4], 2)), g_median_d2_late=gm, drop_m=z[i0] - z[j])
    print(i, {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in out[i].items()})
summ = {}
for key in ['g_free_from_argmax', 'g_hinge', 'g_free_from_release', 'g_median_d2_late']:
    v = np.array([o[key] for o in out.values()]); summ[key] = dict(mean=v.mean(), se=v.std(ddof=1) / np.sqrt(len(v)), sd=v.std(ddof=1), n=len(v))
    print(key, round(v.mean(), 3), '+-', round(v.std(ddof=1) / np.sqrt(len(v)), 3), 'sd', round(v.std(ddof=1), 3))
json.dump(dict(per_clip=out, summary=summ), open(sys.argv[2], 'w'), indent=1, default=float)
