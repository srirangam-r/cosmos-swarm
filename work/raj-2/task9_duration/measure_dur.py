# raj-2 task 9: measure g and fall time on duration-sweep Cosmos clips with two estimators.
#  (a) tools/realball v1.1 (raj-2)   (b) tools/trk_ballfall measure_ball v5 (raj-3) via measure_dir (QC images)
# Usage: python3 -I measure_dur.py <repo> <clip_dir> [<clip_dir> ...]   (ppm 539.8 = 830.5*0.65, letterbox)
import sys, os, glob, json, numpy as np
repo = sys.argv[1]
sys.path.insert(0, repo + '/tools/realball'); sys.path.insert(0, repo + '/tools/trk_ballfall')
import realball, trk, measure_ball as mb, measure_dir as md
PPM = 539.8
out = {}
for d in sys.argv[2:]:
    for p in sorted(glob.glob(f'{d}/*.mp4')):
        if os.path.getsize(p) == 0: continue
        name = p[:-4]; sc = json.load(open(name + '.json')) if os.path.exists(name + '.json') else {}
        fps = float(sc.get('fps', 24)); nf = int(sc.get('num_frames', 0)); F = trk.load(p)
        row = dict(num_frames=nf or len(F), fps=fps, T=len(F) / fps, seed=sc.get('seed'), image=sc.get('image'),
                   neg=bool(sc.get('negative_prompt')))
        try:
            r = realball.measure(F, fps, mpp=1 / PPM, nboot=200)
            row['rb'] = {k: r[k] for k in ('g', 'g_ci95', 'r2', 'rms_m', 't0', 'fit_frames', 'n_fit', 'impact_frame', 'motion_frame', 'g_hinge_v0', 'e', 'dup_period')}
            row['rb']['fall_time'] = r['impact_frame'] / r['fps_true'] - r['t0']
        except Exception as e: row['rb'] = dict(err=repr(e))
        try:
            v = mb.measure(F, fps, mpp=1 / PPM, nboot=300, keep_track=True); md.qc(F, v, name + '_qc.png')
            row['v5'] = {k: v[k] for k in ('g', 'g_ci95', 'r2', 'flag', 'onset_frame', 'impact_frame', 'dAIC_quad_vs_lin') if k in v}
        except Exception as e: row['v5'] = dict(err=repr(e))
        out[os.path.basename(p)] = row
        rb, v5 = row['rb'], row['v5']
        print(os.path.basename(p), f"T={row['T']:.2f}s", 'rb g=%s fall=%s' % (rb.get('g'), rb.get('fall_time')), 'v5 g=%s flag=%s' % (v5.get('g'), v5.get('flag')), flush=True)
json.dump(out, open('dur_results.json', 'w'), indent=1, default=float)
