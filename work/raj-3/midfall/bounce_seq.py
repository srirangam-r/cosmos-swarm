"""bounce_seq.py (raj-3, task 15): bounce-sequence readouts from a saved single-ball track.
Unvalidated supplementary readouts (the planted-PASS number is seeded.py's first-rebound g; these describe the
sequence after it):
  impacts  = local maxima of image y (lowest ball positions) that are >= MIN_RISE px below both neighbouring apexes
  apexes   = local minima of image y between consecutive impacts
  rise_px  = y(impact_k) - y(apex_k) for flight k (impact_k -> impact_{k+1}); uses the next impact's y too (mean)
  T_k      = (impact_{k+1} - impact_k) / fps   (frame-resolution, +-1 frame)
  e_h      = sqrt(rise_{k+1} / rise_k)     (height-based restitution, scale-free)
  e_T      = T_{k+1} / T_k                 (time-based restitution, scale-free)
  g_hT     = 8 rise / T^2 (m/s^2, uses --ppm)
Usage:
  python3 -I bounce_seq.py track.json --fps 24 --ppm 539.8 [--last N]   (track.json from midfall_fit.py --save-track)
  python3 -I bounce_seq.py --real bounce_real22.json                     (real GAUGE reference from measure_bounce v1)
"""
import sys, json, argparse
import numpy as np

MIN_RISE = 25.0


def interp_track(cy):
    y = np.array([np.nan if v is None else v for v in cy], float)
    ok = np.isfinite(y)
    return y, ok


def sequence(cy, fps, ppm, last=None):
    y, ok = interp_track(cy)
    n = len(y) if last is None else min(len(y), last + 1)
    idx = [i for i in range(n) if ok[i]]
    # candidate extrema on the valid samples
    imps, apx = [], []
    for j in range(1, len(idx) - 1):
        a, b, c = y[idx[j - 1]], y[idx[j]], y[idx[j + 1]]
        if b >= a and b >= c:
            imps.append(idx[j])
        if b <= a and b <= c:
            apx.append(idx[j])
    # alternate impact/apex with a minimum rise, greedy
    ext = sorted([(i, 'I') for i in imps] + [(i, 'A') for i in apx])
    seq = []
    for i, k in ext:
        if seq and seq[-1][1] == k:
            # keep the more extreme of two same-type extrema
            if (k == 'I' and y[i] > y[seq[-1][0]]) or (k == 'A' and y[i] < y[seq[-1][0]]):
                seq[-1] = (i, k)
            continue
        if seq and abs(y[i] - y[seq[-1][0]]) < MIN_RISE:
            continue
        seq.append((i, k))
    I = [i for i, k in seq if k == 'I']
    flights = []
    for a, b in zip(I[:-1], I[1:]):
        ap = [i for i, k in seq if k == 'A' and a < i < b]
        if not ap:
            continue
        p = ap[0]
        rise = 0.5 * (y[a] + y[b]) - y[p]
        T = (b - a) / fps
        flights.append(dict(impact0=a, apex=p, impact1=b, rise_px=float(rise), T_s=float(T),
                            g_hT=float(8 * rise / ppm / T ** 2)))
    for k in range(len(flights) - 1):
        f0, f1 = flights[k], flights[k + 1]
        f0['e_h_next'] = float(np.sqrt(max(f1['rise_px'], 0) / f0['rise_px']))
        f0['e_T_next'] = float(f1['T_s'] / f0['T_s'])
    return dict(impacts=I, flights=flights)


def summarize(flights):
    eh = [f['e_h_next'] for f in flights if 'e_h_next' in f]
    eT = [f['e_T_next'] for f in flights if 'e_T_next' in f]
    g = [f['g_hT'] for f in flights]
    out = dict(n_flights=len(flights), rise_px=[round(f['rise_px'], 1) for f in flights],
               T_frames=[f['impact1'] - f['impact0'] for f in flights])
    for name, v in (('e_h', eh), ('e_T', eT), ('g_hT', g)):
        if v:
            v = np.array(v)
            out[name + '_mean'] = float(v.mean())
            out[name + '_se'] = float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else None
            out[name + '_all'] = [round(float(x), 3) for x in v]
    return out


def real_reference(path):
    d = json.load(open(path))
    rows = []
    for k, r in d.items():
        rise = r.get('flight_rise_px') or []
        imp = r.get('impact_frames') or []
        fps = r.get('fps')
        if len(rise) >= 2 and rise[0] > 0:
            T = [(b - a) for a, b in zip(imp[:-1], imp[1:])]
            rows.append(dict(clip=k, flag=r.get('flag'), e_h1=float(np.sqrt(max(rise[1], 0) / rise[0])),
                             e_T1=float(T[1] / T[0]) if len(T) >= 2 and T[0] > 0 else None,
                             rise0=rise[0], rise1=rise[1], T0=T[0] if T else None, T1=T[1] if len(T) > 1 else None,
                             fps=fps))
    ok = [r for r in rows if r['flag'] == 'ok']
    eh = np.array([r['e_h1'] for r in ok]); eT = np.array([r['e_T1'] for r in ok if r['e_T1'] is not None])
    return dict(n=len(ok), e_h1_mean=float(eh.mean()), e_h1_se=float(eh.std(ddof=1) / np.sqrt(len(eh))),
                e_h1_median=float(np.median(eh)), e_T1_mean=float(eT.mean()),
                e_T1_se=float(eT.std(ddof=1) / np.sqrt(len(eT))), e_T1_median=float(np.median(eT)), rows=rows)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('track', nargs='?'); a.add_argument('--fps', type=float); a.add_argument('--ppm', type=float)
    a.add_argument('--last', type=int); a.add_argument('--real')
    o = a.parse_args()
    if o.real:
        print(json.dumps(real_reference(o.real), indent=1))
        sys.exit()
    d = json.load(open(o.track))
    s = sequence(d['track_cy'], o.fps, o.ppm, o.last)
    s['summary'] = summarize(s['flights'])
    print(json.dumps(s, indent=1))
