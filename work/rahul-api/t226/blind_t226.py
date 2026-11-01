#!/usr/bin/env python3
"""t226 blind strips. `make <clip_dir>`: each t226_*.mp4 gets a random 4-letter ID (key -> blind_key.json, gitignored,
its sha256 is committed; do not open before codes are frozen) and strips/<ID>.jpg: frames 0,4,8,16,24,36,48,60,72,84,92
at half size (3 rows), plus a row of 2x object-region crops every 4th frame. Scene is visible (by design), arm is not.
`unblind <codes.json>`: codes keyed by clip name -> codes_unblinded.json."""
import sys, os, json, glob, random, string, hashlib
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
KEY = os.path.join(HERE, 'blind_key.json'); OUT = os.path.join(HERE, 'strips')
FR = [0, 4, 8, 16, 24, 36, 48, 60, 72, 84, 92]
ROI = {'P': (180, 95, 460, 300), 'F': (230, 60, 345, 400), 'H': (230, 60, 345, 400)}


def frames(p):
    c = cv2.VideoCapture(p); out = []
    while True:
        ok, f = c.read()
        if not ok: return out
        out.append(f if f.shape[:2] == (480, 832) else cv2.resize(f, (832, 480)))


def strip(F, scene, bid):
    tiles = []
    for k in FR:
        t = cv2.resize(F[min(k, len(F) - 1)], (416, 240)); cv2.putText(t, f'f{k}', (4, 16), 0, 0.5, (0, 255, 255), 1); tiles.append(t)
    while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
    top = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
    x0, y0, x1, y1 = ROI[scene]; crops = []
    for k in range(0, len(F), 4):
        c = F[k][y0:y1, x0:x1]; s = 150.0 / c.shape[0]
        c = cv2.resize(c, (int(c.shape[1] * s), 150)); cv2.putText(c, str(k), (2, 12), 0, 0.4, (0, 255, 255), 1); crops.append(c)
    W = top.shape[1]; per = max(1, W // crops[0].shape[1]); rows = []
    for i in range(0, len(crops), per):
        r = crops[i:i + per]
        while len(r) < per: r.append(np.zeros_like(crops[0]))
        r = np.hstack(r); rows.append(np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0))))
    hdr = np.zeros((28, W, 3), np.uint8); cv2.putText(hdr, f'ID {bid}   scene {scene}', (6, 20), 0, 0.7, (255, 255, 255), 2)
    return np.vstack([hdr, top] + rows)


def make(clip_dir):
    if os.path.exists(KEY): sys.exit('blind_key.json exists; refusing to re-key')
    os.makedirs(OUT, exist_ok=True); rnd = random.SystemRandom()
    clips = sorted(glob.glob(os.path.join(clip_dir, 't226_*.mp4'))); ids = set(); key = {}
    while len(ids) < len(clips): ids.add(''.join(rnd.choice(string.ascii_uppercase) for _ in range(4)))
    ids = list(ids); rnd.shuffle(ids)
    for p, bid in zip(clips, ids):
        name = os.path.basename(p)[:-4]; scene = name.split('_')[1]; key[bid] = name
        cv2.imwrite(os.path.join(OUT, f'{bid}.jpg'), strip(frames(p), scene, bid), [cv2.IMWRITE_JPEG_QUALITY, 80])
    s = json.dumps(key, sort_keys=True, indent=1); open(KEY, 'w').write(s)
    open(os.path.join(HERE, 'blind_key.sha256'), 'w').write(hashlib.sha256(s.encode()).hexdigest() + '  blind_key.json\n')
    # coder sheet: IDs grouped by scene (scene is visible anyway), alphabetical within scene
    by = {}
    for bid, n in key.items(): by.setdefault(n.split('_')[1], []).append(bid)
    json.dump({sc: sorted(v) for sc, v in sorted(by.items())}, open(os.path.join(HERE, 'strips', 'IDS_by_scene.json'), 'w'), indent=1)
    print(len(key), 'strips')


def unblind(codes):
    key = json.load(open(KEY)); C = json.load(open(codes))
    json.dump({key[b]: v for b, v in C.items()}, open(os.path.join(HERE, 'codes_unblinded.json'), 'w'), indent=1, sort_keys=True)


if __name__ == '__main__':
    make(sys.argv[2]) if sys.argv[1] == 'make' else unblind(sys.argv[2])
