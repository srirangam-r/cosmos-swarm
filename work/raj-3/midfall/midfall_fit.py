"""midfall_fit.py (raj-3, task 15): g for clips that START mid-fall (the ball is already falling in frame 0).
Track: the seeded single-ball track of tools/trk_ballfall/seeded.py (firstfall v1, referee PASS msg 264/312).
Readouts:
  g_mid    = free-v0 quadratic y = a + b t + g/2 t^2 over frames 0 .. first_impact-1 (no hinge: the onset is frame 0),
             residual-bootstrap 95% CI. first_impact = start of the first rebound flight (measure_bounce) if found,
             else the first frame where the track reverses (moves up > 2 px) after descending.
  g_bounce = seeded.py's first-rebound curvature (unchanged).
Usage:
  python3 -I midfall_fit.py clip.mp4 --fps 24 --ppm 539.8 --point x,y [--start N] [--qc out.png] [--save-track]
  python3 -I midfall_fit.py --simcheck <sim_drop out dir> <arm> <out.json>   (validation on rahul-3 sim_drop clips cut 2 frames after fall start)
"""
import sys, os, json, argparse, glob, math
import numpy as np
T = '/home/nail/swarm-work/raj-3/cosmos-swarm/tools/trk_ballfall'
sys.path.insert(0, T); sys.path.insert(0, os.path.join(T, '..', 'realball'))
import trk, seeded, firstfall as ff


def quadfit(t, y):
    A = np.vstack([np.ones_like(t), t, 0.5 * t ** 2]).T
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    return c, A


def first_impact(cy, flights):
    """Lowest point (max image y) of the first descent. Fit frames are 0..impact-1, so the impact frame (motion-blurred
    across the contact; finding 109 impact-frame bias) is excluded."""
    if flights:
        k = int(flights[0][0]); seg = cy[:k + 1]
        if np.isfinite(seg).any():
            return int(np.nanargmax(seg))
    ok = np.isfinite(cy)
    best = None
    for i in range(1, len(cy) - 1):
        if not ok[i]:
            continue
        nxt = [cy[j] for j in range(i + 1, min(i + 3, len(cy))) if ok[j]]
        if nxt and cy[i] - min(nxt) > 2.0 and cy[i] > np.nanmin(cy[:i + 1]) + 4:
            best = i
            break
    return best


def g_mid(cy, fps, s, flights, nboot=500, seed=0):
    imp = first_impact(cy, flights)
    if imp is None or imp < 4:
        return dict(g_mid=None, mid_flag='too_few_frames', mid_impact=imp)
    fr = np.arange(imp)
    ok = np.isfinite(cy[:imp])
    fr = fr[ok]; y = cy[:imp][ok] * s
    if len(fr) < 4:
        return dict(g_mid=None, mid_flag='too_few_frames', mid_impact=imp)
    t = fr / fps
    c, A = quadfit(t, y)
    res = y - A @ c
    ss = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (res ** 2).sum() / ss if ss > 0 else float('nan')
    rng = np.random.default_rng(seed)
    gb = []
    for _ in range(nboot):
        yb = A @ c + rng.choice(res, len(res)) * math.sqrt(len(res) / max(len(res) - 3, 1))
        gb.append(np.linalg.lstsq(A, yb, rcond=None)[0][2])
    lo, hi = np.percentile(gb, [2.5, 97.5])
    n = len(fr)
    flag = 'ok' if (n >= 7 and r2 > 0.98 and c[2] > 0) else 'weak'   # n>=7: sim_drop check, n=5-6 gave 1.23-1.28x
    return dict(g_mid=float(c[2]), g_mid_ci95=[float(lo), float(hi)], mid_v0=float(c[1]), mid_r2=float(r2), mid_n=n,
                mid_frames=[int(fr[0]), int(fr[-1])], mid_impact=imp, mid_flag=flag)


def run(F, fps, ppm, point, nboot=200):
    try:
        out, tr, r = seeded.measure(F, fps, ppm, None, point, 0, None, nboot=nboot)
    except Exception as ex:                       # firstfall's fit crashes on very short tracks (ball lost); keep the raw track
        cx, cy, area, info = ff.track(F, point, 0)
        tr, r = (cx, cy, area), None
        out = dict(method=seeded.VERSION + ' [seeded readouts failed]', err=repr(ex), m_per_px=1.0 / ppm, fps_true=fps,
                   n_tracked=int(np.isfinite(cy).sum()), g_bounce=None, bounce_flag='err', bounce_flight_frames=None)
    cy = np.asarray(tr[1], float)
    m = g_mid(cy, out['fps_true'], out['m_per_px'], out.get('bounce_flight_frames'))
    out.update(m)
    return out, tr, r


def simcheck(d, arm, outp):
    rows = []
    for sp in sorted(glob.glob(f'{d}/{arm}/meta/*.json')):
        sc = json.load(open(sp)); fps = sc['fps']
        k0 = int(math.ceil(sc['t_fall_start'] * fps)) + 2           # ~2 frames after the ball starts falling (task-15 inputs)
        kimp = sc['first_impact_t'] * fps
        F = trk.load(f"{d}/{arm}/videos/{sc['name']}.mp4")[k0:]
        pt = sc['centers_px'][k0]
        try:
            o, _, _ = run(F, fps, sc['px_per_m'], pt, nboot=100)
        except Exception as ex:
            o = dict(err=repr(ex))
        row = dict(name=sc['name'], holder=sc['holder'], g_true=sc['g'], start=k0, frames_to_impact=round(kimp - k0, 2),
                   **{k: o.get(k) for k in ('g_mid', 'g_mid_ci95', 'mid_flag', 'mid_n', 'mid_r2', 'mid_impact', 'g_bounce', 'bounce_flag', 'err')})
        row['ratio_mid'] = row['g_mid'] / sc['g'] if row['g_mid'] is not None else None
        row['ratio_bounce'] = row['g_bounce'] / sc['g'] if row['g_bounce'] is not None else None
        print(json.dumps(row, default=float), flush=True)
        rows.append(row)
    json.dump(rows, open(outp, 'w'), indent=1, default=float)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--simcheck':
        simcheck(sys.argv[2], sys.argv[3], sys.argv[4]); sys.exit()
    a = argparse.ArgumentParser(); a.add_argument('clip'); a.add_argument('--fps', type=float, required=True)
    a.add_argument('--ppm', type=float, required=True); a.add_argument('--point', required=True)
    a.add_argument('--start', type=int, default=0); a.add_argument('--qc'); a.add_argument('--save-track', action='store_true')
    o = a.parse_args()
    F = trk.load(o.clip)[o.start:]
    out, tr, r = run(F, o.fps, o.ppm, [float(v) for v in o.point.split(',')])
    if o.save_track:
        out['track_cy'] = [None if not np.isfinite(v) else float(v) for v in np.asarray(tr[1], float)]
        out['track_cx'] = [None if not np.isfinite(v) else float(v) for v in np.asarray(tr[0], float)]
    if o.qc and r is not None:
        ff.qc_png(o.qc, F, tr, r)
    print(json.dumps(out, indent=1, default=float))
