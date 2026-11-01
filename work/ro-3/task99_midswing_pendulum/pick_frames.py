"""ro-3: pick a real mid-swing frame (bob crossing the bottom at max speed) and the rest/extreme frame-0 from letterboxed real GAUGE pendulum clips."""
import sys, json, numpy as np, cv2
sys.path.insert(0, sys.argv[1] + '/tools/trk_ballfall'); import measure_pend as mp
out = {}
for i in sys.argv[3:]:
    p = f'{sys.argv[2]}/pend{i}.mp4'; c = cv2.VideoCapture(p); fps = c.get(5); F = []
    while 1:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    F = np.array(F).astype(np.float32)
    r = mp.measure(F, fps, keep_track=True, nboot=20); tr = np.array(r['track'])
    fr, s = tr[:, 0].astype(int), tr[:, 2]
    zc = [k for k in range(1, len(s)) if np.sign(s[k]) != np.sign(s[k - 1])]
    k = zc[2]  # 3rd bottom crossing after release
    kk = k if abs(s[k]) < abs(s[k - 1]) else k - 1
    fmid = int(fr[kk]); fext = int(r['release_frame'])
    cv2.imwrite(f'midswing/inputs/pend{i}_mid_f{fmid}.png', F[fmid].astype(np.uint8))
    cv2.imwrite(f'midswing/inputs/pend{i}_rest_f{fext}.png', F[fext].astype(np.uint8))
    vel = float((s[kk + 1] - s[kk - 1]) / 2)
    out[i] = dict(fps=fps, period_s=r['period_s'], amp_px=r['amp_px'], release_frame=fext, mid_frame=fmid, s_mid=float(s[kk]), vel_px_per_frame=vel, flag=r['flag'])
    print(i, out[i], flush=True)
json.dump(out, open('midswing/inputs/pick.json', 'w'), indent=1)
