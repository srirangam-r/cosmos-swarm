# raj-2: validate trk_ballfall ball() on real GAUGE bouncing-ball videos vs mocap ground truth.
import sys, json, numpy as np
sys.path.insert(0, sys.argv[1])            # tools/trk_ballfall
import trk
D = 0.06                                   # GAUGE ball diameter (m)
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
out = {}
for i in range(1, 23):
    r = dict(clip=i)
    try: r.update({'mocap_'+k: float(v) for k, v in mocap_g(f'json/{i}.json').items()})
    except Exception as ex: r['mocap_err'] = str(ex)
    try:
        F = trk.load(f'video/{i}.mp4'); est = trk.ball(F, 30.0, D=D); r.update({'trk_'+k: v for k, v in est.items()})
        del F
    except Exception as ex: r['trk_err'] = repr(ex)
    out[i] = r; print(json.dumps(r), flush=True)
json.dump(out, open('gauge_trk_results.json', 'w'), indent=1)
