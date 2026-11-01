"""Batch driver for Cosmos ball-drop clips (raj-3). For every <name>.mp4 with a <name>.json sidecar in a folder:
runs measure_ball v5 with fps from the sidecar and a fixed px/m, and writes results.json plus QC images
(<name>_qc.png: tracked y(t) with the fit, onset and impact marked; 6 frames with the tracked centroid drawn).
Usage: python3 -I measure_dir.py <clip_dir> --ppm 539.8 [--out results.json]
GAUGE ball first frames letterboxed 1280x720 -> 832x468 (+6 px pad): ppm = 830.5 * 0.65 = 539.8 (raj-2 mocap calibration, msg 146).
Check the QC images: if the track follows the gripper or a shadow instead of the ball, the g is meaningless."""
import sys, os, json, glob, argparse, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trk, measure_ball as mb

def qc(F, r, path):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    tr = np.array(r['track']); fps = r['fps']; ppm = 1 / r['m_per_px']
    fig = plt.figure(figsize=(14, 6)); ax = fig.add_subplot(1, 2, 1)
    ax.plot(tr[:, 0] / fps, tr[:, 2], '.', ms=4, label='tracked centroid y (px)')
    for k, c in (('onset_frame', 'g'), ('impact_frame', 'r')): ax.axvline(r[k] / fps, color=c, ls='--', label=k)
    ax.invert_yaxis(); ax.set_xlabel('t (s)'); ax.set_ylabel('y (px, down)'); ax.legend(fontsize=8)
    ax.set_title(f"[{r['flag']}] g={r['g']:.3f} m/s2 CI95 {r['g_ci95'][0]:.2f}-{r['g_ci95'][1]:.2f} R2={r['r2']:.3f} dAIC={r['dAIC_quad_vs_lin']:.1f}", fontsize=9)
    idx = np.linspace(0, len(F) - 1, 6).astype(int); idx = sorted(set(idx) | {r['onset_frame'], r['impact_frame']})[:8]
    tiles = []
    for i in idx:
        f = F[i].clip(0, 255).astype(np.uint8).copy(); m = tr[tr[:, 0] == i]
        if len(m): cv2.circle(f, (int(m[0, 1]), int(m[0, 2])), max(int(m[0, 3] / 2), 4), (0, 0, 255), 2)
        cv2.putText(f, f'f{i}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        tiles.append(cv2.resize(f, (416, 240)))
    while len(tiles) % 2: tiles.append(np.zeros_like(tiles[0]))
    grid = np.vstack([np.hstack(tiles[k:k + 2]) for k in range(0, len(tiles), 2)])
    ax2 = fig.add_subplot(1, 2, 2); ax2.imshow(grid[:, :, ::-1]); ax2.axis('off')
    fig.tight_layout(); fig.savefig(path, dpi=80); plt.close(fig)

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('dir'); a.add_argument('--ppm', type=float, required=True)
    a.add_argument('--out', default=None); a.add_argument('--nboot', type=int, default=300); a.add_argument('--fps', type=float)
    o = a.parse_args(); out = {}
    for p in sorted(glob.glob(f'{o.dir}/*.mp4')):
        name = p[:-4]; sc = json.load(open(name + '.json')) if os.path.exists(name + '.json') else {}
        fps = o.fps or float(sc.get('fps', 24)); F = trk.load(p)
        try: r = mb.measure(F, fps, mpp=1 / o.ppm, nboot=o.nboot, keep_track=True)
        except Exception as e: out[os.path.basename(p)] = dict(err=repr(e)); print(p, 'ERR', e); continue
        qc(F, r, name + '_qc.png'); r['sidecar'] = sc; r['ppm'] = o.ppm; out[os.path.basename(p)] = r
        print(os.path.basename(p), {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in ('g', 'g_ci95', 'r2', 'r2_lin', 'dAIC_quad_vs_lin', 'onset_frame', 'impact_frame', 'n_fit', 'g_by_skip')}, flush=True)
    json.dump(out, open(o.out or f'{o.dir}/results_v5.json', 'w'), indent=1, default=float)
