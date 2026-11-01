#!/usr/bin/env python3
"""dk2 t337c secondary readout: what happens OUTSIDE the x0_inject box (background fidelity + duplicate motion).

Independent code (not dk-scout's s16/outside.py). Per clip, with the scene's box from dk1 boxes.json @dc1a6f7
(fractions of 832x480), the outside region O = frame minus (box dilated by PAD=16 px, one latent):
  drift_rgb   mean over frames 8..92 of |mean_RGB_O(f) - mean_RGB_O(0)| (L2, grey levels): flat-wall/colour shift
  block_corr  mean over frames 12..92 of the Pearson corr between 16x16 block means of O at f and at f0 (grey):
              ~1 = background structure kept from frame 0, ~0 = replaced (arm A wall: ~-0.05, #6866)
  move_px     # pixels of O with max_t |grey_t - grey_0| > 25 (t331 threshold): motion outside the box
              (duplicate/extra pendulum, or plain's own wide swing; dk-scout #6900 sec.4)
  lap_ratio   Laplacian variance of O, mean over f12..92 divided by its value at f0 (texture kept vs smoothed)
usage: python3 -I outside.py <boxes.json> <out.json> clip.mp4 ...   (scene parsed from 'real_NN' in the file name)
"""
import json, re, sys
import cv2, numpy as np

PAD, THR, B = 16, 25, 16


def read(p):
    cap = cv2.VideoCapture(str(p)); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f[..., ::-1].astype(np.float32))
    return np.stack(fr)


def one(path, box):
    V = read(path); T, H, W, _ = V.shape
    x0, y0, x1, y1 = box
    m = np.ones((H, W), bool)
    m[max(0, int(y0 * H) - PAD):min(H, int(np.ceil(y1 * H)) + PAD), max(0, int(x0 * W) - PAD):min(W, int(np.ceil(x1 * W)) + PAD)] = False
    G = V.mean(-1)
    rgb = np.array([V[t][m].mean(0) for t in range(T)])
    drift = float(np.mean(np.linalg.norm(rgb[8:] - rgb[0], axis=1)))
    hb, wb = H // B, W // B
    mb = m[:hb * B, :wb * B].reshape(hb, B, wb, B).all((1, 3))  # blocks fully outside
    def blocks(g): return g[:hb * B, :wb * B].reshape(hb, B, wb, B).mean((1, 3))[mb]
    b0 = blocks(G[0])
    corr = float(np.mean([np.corrcoef(blocks(G[t]), b0)[0, 1] for t in range(12, T)]))
    move = int(((np.abs(G - G[0]).max(0) > THR) & m).sum())
    def lap(g): return float(cv2.Laplacian(g, cv2.CV_32F)[m].var())
    lr = float(np.mean([lap(G[t]) for t in range(12, T)]) / max(lap(G[0]), 1e-6))
    return dict(drift_rgb=round(drift, 2), block_corr=round(corr, 3), move_px=move, lap_ratio=round(lr, 3),
                outside_px=int(m.sum()), frames=T, rgb_f0=[round(float(v), 1) for v in rgb[0]], rgb_late=[round(float(v), 1) for v in rgb[8:].mean(0)])


def main():
    boxes = json.load(open(sys.argv[1])); out = {}
    for p in sys.argv[3:]:
        sc = re.search(r"real_\d\d", p).group(0)
        if sc not in boxes: continue
        name = p.rsplit("/", 1)[-1][:-4]
        out[name] = one(p, boxes[sc]["box"]); print(name, out[name], flush=True)
    json.dump(out, open(sys.argv[2], "w"), indent=1)


if __name__ == "__main__":
    main()
