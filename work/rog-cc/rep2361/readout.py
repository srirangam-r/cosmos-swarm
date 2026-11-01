"""rog-cc: independent readout for replicating ro-3 #2361 (pendulum: rest-frame vs mid-swing-frame input).

Per clip (832x480, 93 f), with ROIs chosen from the real input frames (pivot ~ (325,125) px, rod ~130 px):
  - zone_motion: mean |f_t - f_{t-1}| (grey) in the bottom-of-arc zone between the two posts
    (x 290-360, y 180-290). The bob crosses this zone on every swing; at rest it is black curtain.
  - passes: number of entries of the bob into the zone. Presence = mean |f_t - clip_median| in zone > THR.
  - occupancy: fraction of frames with presence.
  - rod_persist: mean |f_t - f_0| in the rest-rod band (x 330-400, y 115-150) over f60-92.
    Small = the rod/bob at the release point never moved (held).
Also writes a blinded contact strip per clip (frames 0,6,...,90; crop x 180-520, y 40-340) for eye coding.
Usage: python3 readout.py CLIPDIR OUTDIR
"""
import sys, os, json, glob, hashlib
import cv2, numpy as np

ZONE = (180, 290, 290, 360)      # y0, y1, x0, x1
ROD = (115, 150, 330, 400)
CROP = (40, 340, 180, 520)
THR = 8.0


def load(p):
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    return np.array(F)


def roi(G, r):
    return G[:, r[0]:r[1], r[2]:r[3]].astype(np.float32)


def measure(p):
    F = load(p); G = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in F])
    z = roi(G, ZONE)
    zone_motion = float(np.abs(np.diff(z, axis=0)).mean())
    dev = np.abs(z - np.median(z, axis=0)).mean(axis=(1, 2))
    pres = dev > THR
    passes = int(pres[0]) + int(np.sum(pres[1:] & ~pres[:-1]))
    r = roi(G, ROD)
    late = slice(60, len(G))
    rod_persist = float(np.abs(r[late] - r[0]).mean())
    return F, dict(n_frames=len(F), zone_motion=zone_motion, passes=passes, occupancy=float(pres.mean()),
                   rod_persist=rod_persist, zone_dev=[round(float(x), 2) for x in dev])


def strip(F, path, tag):
    idx = list(range(0, len(F), 6))[:16]
    tiles = []
    for i in idx:
        t = F[i][CROP[0]:CROP[1], CROP[2]:CROP[3]].copy()
        t = cv2.resize(t, (t.shape[1] // 2, t.shape[0] // 2))
        cv2.putText(t, f"f{i}", (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        tiles.append(t)
    while len(tiles) % 8: tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[k:k + 8]) for k in range(0, len(tiles), 8)]
    im = np.vstack(rows)
    cv2.putText(im, tag, (3, im.shape[0] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.imwrite(path, im)


def main(cd, od):
    os.makedirs(od + "/strips", exist_ok=True)
    res, key = {}, {}
    for p in sorted(glob.glob(cd + "/*.mp4")):
        name = os.path.basename(p)[:-4]
        h = hashlib.sha256(name.encode() + b"rog-cc-2361").hexdigest()[:6]
        F, m = measure(p)
        res[name] = m; key[h] = name
        strip(F, f"{od}/strips/{h}.jpg", h)
        print(name, h, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items() if k != "zone_dev"}, flush=True)
    json.dump(res, open(od + "/readout.json", "w"), indent=1)
    json.dump(key, open(od + "/UNBLIND_key.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
