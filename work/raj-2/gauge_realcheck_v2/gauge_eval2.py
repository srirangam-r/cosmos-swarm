# raj-2 shift 11: run measure_ball v4 (raj-3, hinge t0) and rohith_measure v4 UNCHANGED on GAUGE real ball drops vs mocap.
import sys, json, numpy as np, traceback
R = sys.argv[1]                       # cosmos-swarm repo root
G = sys.argv[2]                       # gauge data dir (video/, json/)
sys.path.insert(0, R + '/tools/trk_ballfall'); sys.path.insert(0, R + '/tools/rohith_measure')
import trk, measure_ball
import measure as rm
def mocap_g(js):
    d = json.load(open(js)); fps = d['FPS']; z = np.array(d['ball']['z'])/1000.0
    t = np.arange(len(z))/fps
    i0 = int(np.argmax(z))                 # release ~ highest point
    j = i0+1
    while j < len(z)-1 and not (z[j] <= z[j-1] and z[j] < z[j+1]): j += 1   # first local min = impact
    s = slice(i0, j)                       # airborne frames before impact (exclude contact frame)
    c = np.polyfit(t[s], z[s], 2)          # free v0
    tt = t[s]-t[i0]; A = np.c_[np.ones_like(tt), tt**2]   # v0=0 at release
    c0 = np.linalg.lstsq(A, z[s], rcond=None)[0]
    res = z[s]-np.polyval(c, t[s])
    return dict(g_free=-2*c[0], g_v0=-2*c0[1], n=j-i0, drop_m=z[i0]-z[j], rms_mm=1000*res.std())
D = 0.06
out = {}
for i in range(1, 23):
    r = dict(clip=i)
    r.update({'mocap_' + k: float(v) for k, v in mocap_g(f'{G}/json/{i}.json').items()})
    try:
        F = trk.load(f'{G}/video/{i}.mp4')
        m = measure_ball.measure(F, 30.0, diam=D, nboot=100); del F
        r.update({'mb_' + k: v for k, v in m.items() if k != 'method'})
    except Exception: r['mb_err'] = traceback.format_exc()[-300:]
    try:
        o, P = rm.fit_ball(f'{G}/video/{i}.mp4', D, False)
        r.update({'rm_' + k.lstrip('_'): v for k, v in o.items()})
    except Exception: r['rm_err'] = traceback.format_exc()[-300:]
    out[i] = r; print(json.dumps(r), flush=True)
json.dump(out, open('gauge_eval2_results.json', 'w'), indent=1)
