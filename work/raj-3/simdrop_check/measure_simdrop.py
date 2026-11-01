"""raj-3: independent g check of rahul-3's sim_drop clips (task 11) with trk_ballfall (referee composite PASS @ 38db9dd).
For every videos/<name>.mp4 + meta/<name>.json in a set dir: measure_ball v5 (free-v0 first-fall g) and measure_bounce v1
(first rebound flight g), both with the generator's px/m (meta px_per_m), fps 24. Writes results.json + QC images.
Also fits the generator's own stored centres (meta centers_px) with the same v5 onset fit, as a no-tracker reference.
Usage: python3 -I measure_simdrop.py <set_dir> <tool_dir> <out_dir>"""
import sys, os, json, glob
import numpy as np
setdir, tooldir, outdir = sys.argv[1:4]
sys.path.insert(0, tooldir)
import trk, measure_ball as mb, measure_bounce as mbo, measure_dir as md
os.makedirs(outdir, exist_ok=True)
out = {}
for mp in sorted(glob.glob(f'{setdir}/meta/*.json')):
    m = json.load(open(mp)); name = m['name']; fps = float(m['fps']); mpp = 1.0 / m['px_per_m']
    F = trk.load(f'{setdir}/videos/{name}.mp4')
    rec = dict(g_true=m['g'], e_true=m['e'], h_m=m['h_m'], r_px=m['r_px'], px_per_m=m['px_per_m'], holder=m['holder'],
               ball=m['ball'], surface=m['surface'], t_fall_start=m['t_fall_start'], first_impact_t=m['first_impact_t'], crf=m['crf'])
    # truth track through the same v5 fit (no tracker): stored per-frame centre = mean over the shutter sub-frames
    cy = np.array([c[1] for c in m['centers_px']]); t = np.arange(len(cy)) / fps
    k_imp = int(np.ceil(m['first_impact_t'] * fps)) - 1      # last frame fully before the first impact
    k0 = int(np.floor(m['t_fall_start'] * fps)) + 2          # onset + 1 skipped frame (as v5)
    if k_imp - k0 >= 3:
        c = np.polyfit(t[k0:k_imp], cy[k0:k_imp], 2); rec['g_truthtrack'] = float(2 * c[0] * mpp)
    try:
        r = mb.measure(F, fps, mpp=mpp, nboot=200, keep_track=True)
        md.qc(F, r, f'{outdir}/{name}_v5_qc.png')
        rec['v5'] = {k: r.get(k) for k in ('g', 'flag', 'tracker', 'n_quad', 'g_ci95', 'r2', 'dAIC_quad_vs_lin', 'onset_frame', 'impact_frame', 'g_by_skip', 'e')}
    except Exception as ex:
        rec['v5'] = dict(err=repr(ex))
    try:
        rb = mbo.measure(F, fps, mpp=mpp, nboot=200)
        if rb.get('g') is not None: mbo.qc(rb, f'{outdir}/{name}_bounce_qc.png')
        rec['bounce'] = {k: rb.get(k) for k in ('g', 'flag', 'g_ci95', 'r2', 'n_frames', 'n_flights', 'g_per_flight', 'flight_frames')}
    except Exception as ex:
        rec['bounce'] = dict(err=repr(ex))
    out[name] = rec
    v, b = rec['v5'], rec['bounce']
    print(name, f"g_true={m['g']:.3f} truth={rec.get('g_truthtrack', float('nan')):.3f} v5={v.get('g')} [{v.get('flag')}] bounce={b.get('g')} [{b.get('flag')}] holder={m['holder']} r={m['r_px']:.1f}", flush=True)
json.dump(out, open(f'{outdir}/results.json', 'w'), indent=1, default=float)
