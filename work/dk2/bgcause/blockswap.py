"""Counterfactual 2: is the 8x8 blockiness of nphys (inherited from the mpeg4 0.73 Mb/s proxy) a cause of its DOVER cost?
Cells (lossless x264 qp0, frame 0 untouched): nB = nphys through ffmpeg deblock (filter=strong, block=8);
pB = plain round-tripped through cv2 VideoWriter 'mp4v' (the codec the proxy mp4 has) -> control: plain given proxy-like blocks.
pp/nn come from satswap.py (same encode). Reports outside-box block-edge ratio before/after (bg_features.feats).
usage: python -I blockswap.py <gen> <rev6767_out> <outdir> <bgcause_dir>"""
import sys, os, json, subprocess, tempfile, numpy as np, cv2
gen, rdir, out, bdir = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
argv = sys.argv; sys.argv = ['x', '/nonexistent', rdir, '/dev/null']
ns = {}; exec(open(os.path.join(bdir, 'bg_features.py')).read().split('rows = {}')[0], ns); sys.argv = argv
read, feats = ns['read'], ns['feats']
meta = json.load(open(os.path.join(rdir, 'swap_meta.json')))['clips']
def write(p, v, vf=None):
    T, H, W, _ = v.shape
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "24", "-i", "-"]
    if vf: cmd += ["-vf", vf]
    cmd += ["-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", p]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); pr.stdin.write(np.ascontiguousarray(v).tobytes()); pr.stdin.close(); assert pr.wait() == 0
def mp4v(v):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'x.mp4'); T, H, W, _ = v.shape
        w = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*'mp4v'), 24, (W, H))
        for f in v: w.write(f)
        w.release(); r = read(p)
    r[0] = v[0]; return r
info = {}
for key, c in sorted(meta.items()):
    sc, s = key.split('_')
    P = read(os.path.join(gen, f't276_real_{sc}_plain_{s}.mp4')); N = read(os.path.join(gen, f't276_real_{sc}_nphys_{s}.mp4'))
    with tempfile.TemporaryDirectory() as d:
        t = os.path.join(d, 'nb.mp4'); write(t, N, 'deblock=filter=strong:block=8'); NB = read(t)
    NB[0] = N[0]; PB = mp4v(P)
    write(os.path.join(out, f'blk_{sc}_{s}_nB.mp4'), NB); write(os.path.join(out, f'blk_{sc}_{s}_pB.mp4'), PB)
    info[key] = {nm: {k: feats(V, c['box'])[k] for k in ('blk', 'lap', 'sat')} for nm, V in (('pp', P), ('nn', N), ('nB', NB), ('pB', PB))}
    print(key, {nm: round(v['blk'], 3) for nm, v in info[key].items()}, flush=True)
json.dump(info, open(os.path.join(out, 'blockswap_meta.json'), 'w'), indent=1)
