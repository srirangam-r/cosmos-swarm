"""Counterfactual: is the outside-box saturation rise of nphys (vs plain, same seed) a cause of its DOVER cost?
Per clip pair, g = mean_S(plain frames 1..T) / mean_S(nphys frames 1..T), outside dk1's box (whole-frame gain applied).
Writes, losslessly (x264 qp 0, yuv420p, 24 fps):  pp = plain re-encode, nn = nphys re-encode,
nS = nphys with S*g (desaturated to plain's level), pS = plain with S/g (control: plain given nphys' saturation).
Frame 0 is left untouched in all cells. usage: python -I satswap.py <gen> <rev6767_out> <outdir>"""
import sys, os, json, subprocess, numpy as np, cv2
gen, rdir, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
meta = json.load(open(os.path.join(rdir, 'swap_meta.json')))['clips']
def read(p):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return np.stack(fr)
def write(p, v):
    T, H, W, _ = v.shape
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "24",
                           "-i", "-", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", p], stdin=subprocess.PIPE)
    pr.stdin.write(np.ascontiguousarray(v).tobytes()); pr.stdin.close(); assert pr.wait() == 0
def hsv(v): return np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in v]).astype(np.float32)
def from_hsv(h): return np.stack([cv2.cvtColor(np.clip(f, 0, 255).round().astype(np.uint8), cv2.COLOR_HSV2BGR) for f in h])
def sgain(V, g):
    H = hsv(V); H[1:, :, :, 1] *= g; W = from_hsv(H); W[0] = V[0]; return W
info = {}
for key, c in sorted(meta.items()):
    sc, s = key.split('_'); x0, y0, x1, y1 = c['box']
    P = read(os.path.join(gen, f't276_real_{sc}_plain_{s}.mp4')); N = read(os.path.join(gen, f't276_real_{sc}_nphys_{s}.mp4'))
    m = np.ones(P.shape[1:3], bool); m[max(0, y0-8):y1+8, max(0, x0-8):x1+8] = False
    sp = hsv(P)[1:, :, :, 1][:, m].mean(); sn = hsv(N)[1:, :, :, 1][:, m].mean(); g = float(sp / sn)
    nS = sgain(N, g); pS = sgain(P, 1 / g)
    chk = dict(g=g, S_plain=float(sp), S_nphys=float(sn), S_nS=float(hsv(nS)[1:, :, :, 1][:, m].mean()), S_pS=float(hsv(pS)[1:, :, :, 1][:, m].mean()),
               rt_err_nS=float(np.abs(sgain(N, 1.0).astype(np.int16) - N).mean()))
    info[key] = chk; print(key, {k: round(v, 3) for k, v in chk.items()}, flush=True)
    for nm, V in (('pp', P), ('nn', N), ('nS', nS), ('pS', pS)): write(os.path.join(out, f'sat_{sc}_{s}_{nm}.mp4'), V)
json.dump(info, open(os.path.join(out, 'satswap_meta.json'), 'w'), indent=1)
