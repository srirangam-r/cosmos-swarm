import sys, json, numpy as np
sys.path.insert(0, '/home/nail/swarm-work/raj-3/cosmos-swarm/tools/trk_ballfall')
import measure_ball as mb
root = sys.argv[1]
R = {k: [] for k in ['hinge', 's0', 's1', 's2', 's3', 'argmax']}
for i in range(1, 23):
    d = json.load(open(f'{root}/{i}.json')); fps = d['FPS']; z = np.array(d['ball']['z']) / 1000.0
    t = np.arange(len(z)) / fps
    i0 = int(np.argmax(z)); j = i0 + 1
    while j < len(z) - 1 and not (z[j] <= z[j - 1] and z[j] < z[j + 1]): j += 1
    a = max(i0 - 8, 0)   # include hold frames, as a video tracker would
    tt, Y = t[a:j], z[a] - z[a:j]
    p = mb.fit_hinge(tt, Y); R['hinge'].append(p[1])
    R['argmax'].append(-2 * np.polyfit(t[i0:j], z[i0:j], 2)[0])
    for sk in range(4):
        s = int(np.searchsorted(tt, p[2] + sk / fps - 1e-9)); s = min(s, len(tt) - 5)
        R[f's{sk}'].append(2 * np.polyfit(tt[s:], Y[s:], 2)[0])
for k, v in R.items():
    v = np.array(v); print(k, round(v.mean(), 3), '+-', round(v.std(ddof=1) / np.sqrt(len(v)), 3), 'sd', round(v.std(ddof=1), 3))
