"""raj-3: run raj-2's firstfall v1 (tools/realball, referee PASS 20/20) on sim_drop clips, seeded at the ball's frame-0 centre
(from meta cx, centers_px[0]), with the generator's px/m. Also runs trk_ballfall measure_bounce v1 on firstfall's seeded track
(first rebound flight; firstfall tracks the whole clip when no --tmax).
Usage: python3 -I ff_simdrop.py <set_dir> <tools_dir> <out_dir>"""
import sys, os, json, glob
import numpy as np
setdir, tools, outdir = sys.argv[1:4]
sys.path.insert(0, f'{tools}/realball'); sys.path.insert(0, f'{tools}/trk_ballfall')
import trk, firstfall as ff, measure_bounce as mbo
os.makedirs(outdir, exist_ok=True)
out = {}
for mp in sorted(glob.glob(f'{setdir}/meta/*.json')):
    m = json.load(open(mp)); name = m['name']; fps = float(m['fps']); ppm = m['px_per_m']
    F = trk.load(f'{setdir}/videos/{name}.mp4')
    pt = [m['cx'], m['centers_px'][0][1]]
    rec = dict(g_true=m['g'], e_true=m['e'], h_m=m['h_m'], r_px=m['r_px'], px_per_m=ppm, holder=m['holder'], ball=m['ball'],
               surface=m['surface'], t_fall_start=m['t_fall_start'], first_impact_t=m['first_impact_t'], crf=m['crf'], seed_pt=pt)
    try:
        r, tr = ff.measure(F, fps, ppm, None, pt, 0, None, no_dedup=True)
        ff.qc_png(f'{outdir}/{name}_ff_qc.png', F, tr, r)
        rec['ff'] = {k: r.get(k) for k in ('g', 'g_ci95', 'flag', 'r2', 'n_fit', 't0', 'fit_frames', 'fall_time_s', 'g_from_h_T', 'e', 'd_growth')}
        rec['ff']['t0_err_s'] = (r['t0'] - m['t_fall_start']) if r.get('t0') is not None else None
        # bounce g on the same seeded track
        try:
            cy = np.asarray(tr[1], float)   # firstfall returns (cx, cy, area), NaN = not tracked
            ok = np.isfinite(cy); fr = np.nonzero(ok)[0]
            rb = mbo.fit_track(fr, cy[ok], fps, 1.0 / ppm, nboot=200)
            rec['bounce'] = {k: rb.get(k) for k in ('g', 'flag', 'g_ci95', 'r2', 'n_frames', 'n_flights', 'g_per_flight', 'flight_frames')}
        except Exception as ex:
            rec['bounce'] = dict(err=repr(ex))
    except Exception as ex:
        rec['ff'] = dict(err=repr(ex))
    out[name] = rec
    f, b = rec['ff'], rec.get('bounce', {})
    print(name, f"g_true={m['g']:.3f} ff={f.get('g')} [{f.get('flag')}] t0err={f.get('t0_err_s')} bounce={b.get('g')} [{b.get('flag')}] holder={m['holder']} r={m['r_px']:.1f} ball={m['ball']}", flush=True)
json.dump(out, open(f'{outdir}/results_ff.json', 'w'), indent=1, default=float)
