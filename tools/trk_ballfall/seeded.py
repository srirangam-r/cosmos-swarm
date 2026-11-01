"""seeded.py (raj-3): ball g for scenes with a moving gripper/hand (Cosmos GAUGE-style clips, sim_drop), where trk.blobs
(largest change blob) tracks the holder instead of the ball (see README warning, work/raj-3/simdrop_check).
Track: raj-2's firstfall v1 seeded single-ball tracker (tools/realball/firstfall.py; colour+change gate, continuity).
Readouts on that one track:
  g_fall   = firstfall's first-fall g (realball v1.1 recipe: hinge onset, free-v0 quadratic from onset+1 to pre-impact)
  g_bounce = measure_bounce v1 fit_track: curvature of the first rebound flight (free v0; independent of release)
  g        = g_bounce if flag ok, else g_fall (the referee composite order of msg 246)
Usage:
  python3 -I seeded.py clip.mp4 --fps 24 --ppm 539.8 --point x,y [--pframe N] [--tmax N] [--qc out.png]
  python3 -I seeded.py --planted planted.json clip_dir out.json      (default seed = trk.blobs centroid, diam 0.10 as firstfall)
Look at the QC: the circle must sit on the ball in every panel."""
import sys, os, json, argparse
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here); sys.path.insert(0, os.path.join(here, '..', 'realball'))
import trk, measure_bounce as mbo, firstfall as ff

VERSION = 'trk_ballfall seeded v1 (firstfall v1 track; g = first-rebound fit_track if ok else firstfall g)'


def measure(F, fps, ppm=None, diam=None, point=None, pframe=0, tmax=None, nboot=200):
    r, tr = ff.measure(F, fps, ppm, diam, point, pframe, tmax, nboot=nboot, no_dedup=True)
    s = r['m_per_px']; cy = np.asarray(tr[1], float); ok = np.isfinite(cy); fr = np.nonzero(ok)[0]
    try:
        rb = mbo.fit_track(fr, cy[ok], r['fps_true'], s, nboot=nboot)
    except Exception as ex:
        rb = dict(g=None, flag='err', err=repr(ex))
    use_b = rb.get('g') is not None and rb.get('flag') == 'ok'
    out = dict(method=VERSION, g=rb['g'] if use_b else r['g'], g_source='bounce' if use_b else 'fall',
               flag=rb['flag'] if use_b else r['flag'], g_fall=r['g'], g_fall_ci95=r['g_ci95'], fall_flag=r['flag'], n_fit=r['n_fit'],
               t0=r['t0'], fit_frames=r['fit_frames'], impact_frame=r['impact_frame'], fall_time_s=r['fall_time_s'], g_from_h_T=r['g_from_h_T'],
               d_growth=r['d_growth'], e=r['e'], g_bounce=rb.get('g'), g_bounce_ci95=rb.get('g_ci95'), bounce_flag=rb.get('flag'),
               bounce_n=rb.get('n_frames'), bounce_flight_frames=rb.get('flight_frames'), g_per_flight=rb.get('g_per_flight'),
               m_per_px=s, fps_true=r['fps_true'], n_tracked=r['n_tracked'])
    return out, tr, r


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--planted':
        d = json.load(open(sys.argv[2])); est = {}
        for c in d['clips']:
            F = trk.load(f"{sys.argv[3]}/{c['clip_id']}.mp4"); p = c['params']
            if 'period_s' in p: r = trk.pend(F, c['fps'])
            elif 'a' in p: r = trk.incline(F, c['fps'])
            else: r = measure(F, c['fps'], diam=0.10, nboot=50)[0]
            est[c['clip_id']] = {k: v for k, v in r.items() if k in p and v is not None}
            print(c['clip_id'], est[c['clip_id']], {k: r.get(k) for k in ('flag', 'g_source', 'g_fall', 'g_bounce', 'bounce_flag')}, flush=True)
        json.dump(est, open(sys.argv[4], 'w'), indent=1); sys.exit()
    a = argparse.ArgumentParser(); a.add_argument('clip'); a.add_argument('--fps', type=float, required=True)
    a.add_argument('--ppm', type=float); a.add_argument('--diam', type=float); a.add_argument('--point'); a.add_argument('--pframe', type=int, default=0)
    a.add_argument('--tmax', type=int); a.add_argument('--qc')
    o = a.parse_args(); assert o.ppm or o.diam
    F = trk.load(o.clip); pt = [float(v) for v in o.point.split(',')] if o.point else None
    out, tr, r = measure(F, o.fps, o.ppm, o.diam, pt, o.pframe, o.tmax)
    if o.qc: ff.qc_png(o.qc, F if not o.tmax else F[:o.tmax], tr, r)
    print(json.dumps(out, indent=1, default=float))
