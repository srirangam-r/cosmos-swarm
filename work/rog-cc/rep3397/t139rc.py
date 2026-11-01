#!/usr/bin/env python3
"""Independent re-code of raj-opus-1 task 139 (#3397): holder removed vs unedited GAUGE ball frame 0.

Subcommands
  sheets  <clips_dir> <out_dir>   opaque per-clip zoom sheets (<hex>.jpg) + UNBLIND_key.json (do not open before coding)
  depart  <clips_dir> <out_dir>   automated, arm-agnostic departure metric, keyed by the same hex -> depart.json
  unblind <out_dir> <codes.csv>   join codes with key; arm rates (Wilson 95%), seed-level paired sign tests vs O

Arm is visible in every frame (the edit), so coding cannot be blind to arm. The opaque names hide seed/input
pairing and the clip order is shuffled. The coder does not open raj-opus-1's per-clip codes until codes are committed.
"""
import sys, os, json, glob, re, hashlib, random, math, csv
import numpy as np, cv2

BALL = (280, 116); R_BALL = 12
CROP = (190, 60, 370, 420)  # x0,y0,x1,y1 in 832x480 frames
SCALE = 0.75
NAME_RE = re.compile(r"t139_([AOG])_(ball[12])_s(\d+)\.mp4$")


def read_frames(path):
    cap = cv2.VideoCapture(path); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return fr


def clips(d):
    out = []
    for p in sorted(glob.glob(os.path.join(d, "t139_*.mp4"))):
        m = NAME_RE.search(os.path.basename(p))
        if m: out.append((p, m.group(1), m.group(2), int(m.group(3))))
    return out


def key_for(d, out):
    kp = os.path.join(out, "UNBLIND_key.json")
    if os.path.exists(kp):
        return json.load(open(kp))
    salt = os.urandom(8).hex()
    cl = clips(d)
    key = {}
    for p, arm, inp, seed in cl:
        h = hashlib.sha1((salt + os.path.basename(p)).encode()).hexdigest()[:6]
        key[h] = {"file": os.path.basename(p), "arm": arm, "input": inp, "seed": seed}
    json.dump({"salt": salt, "key": key}, open(kp, "w"), indent=1)
    return {"salt": salt, "key": key}


def tile(f, idx):
    x0, y0, x1, y1 = CROP
    t = f[y0:y1, x0:x1]
    t = cv2.resize(t, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_AREA)
    cv2.putText(t, str(idx), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    return t


def sheets(d, out):
    os.makedirs(out, exist_ok=True)
    k = key_for(d, out)["key"]
    hexes = sorted(k); random.Random(139).shuffle(hexes)
    order = []
    for h in hexes:
        fr = read_frames(os.path.join(d, k[h]["file"]))
        n = len(fr)
        rows = [list(range(0, 16)), list(range(16, 32)), list(range(32, min(n, 93), 4))]
        img_rows = []
        for r in rows:
            ts = [tile(fr[i], i) for i in r if i < n]
            while len(ts) < 16: ts.append(np.zeros_like(ts[0]))
            img_rows.append(np.hstack(ts))
        cv2.imwrite(os.path.join(out, h + ".jpg"), np.vstack(img_rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
        order.append(h)
    open(os.path.join(out, "order.txt"), "w").write("\n".join(order) + "\n")
    print("wrote", len(order), "sheets")


def depart(d, out):
    """NCC of the frame-0 ball disk (r=10 mask) at its frame-0 location vs every frame.
    departure frame = first f with NCC < 0.5 for 4 consecutive frames (None if never)."""
    k = key_for(d, out)["key"]
    yy, xx = np.mgrid[-R_BALL:R_BALL + 1, -R_BALL:R_BALL + 1]
    mask = (xx ** 2 + yy ** 2) <= 10 ** 2
    x, y = BALL
    res = {}
    for h in sorted(k):
        fr = read_frames(os.path.join(d, k[h]["file"]))
        g = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in fr]
        def patch(im):
            p = im[y - R_BALL:y + R_BALL + 1, x - R_BALL:x + R_BALL + 1][mask]
            return p - p.mean()
        t0 = patch(g[0]); n0 = np.linalg.norm(t0) + 1e-6
        ncc = [float(np.dot(t0, patch(im)) / (n0 * (np.linalg.norm(patch(im)) + 1e-6))) for im in g]
        dep = None
        for i in range(1, len(ncc) - 3):
            if all(v < 0.5 for v in ncc[i:i + 4]):
                dep = i; break
        res[h] = {"depart_frame": dep, "ncc_f92": ncc[-1], "ncc_min": min(ncc), "n_frames": len(ncc)}
    json.dump(res, open(os.path.join(out, "depart.json"), "w"), indent=1)
    print("depart.json", len(res))


def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; den = 1 + z * z / n; c = p + z * z / (2 * n); r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / den, (c + r) / den)


def sign_p(up, down):
    n = up + down
    if n == 0: return 1.0
    k = min(up, down)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def unblind(out, codes_path):
    k = json.load(open(os.path.join(out, "UNBLIND_key.json")))["key"]
    rows = list(csv.DictReader(open(codes_path)))
    cols = [c for c in rows[0] if c not in ("hex", "note")]
    dep = json.load(open(os.path.join(out, "depart.json"))) if os.path.exists(os.path.join(out, "depart.json")) else {}
    cells = {}
    for r in rows:
        m = k[r["hex"]]
        cells[(m["arm"], m["input"], m["seed"])] = dict(r, **m, depart=dep.get(r["hex"]))
    summ = {"n_coded": len(rows), "rates": {}, "seed_level": {}, "depart": {}}
    for c in cols:
        summ["rates"][c] = {}
        for arm in "OAG":
            v = [x[c] for kk, x in cells.items() if kk[0] == arm]
            y = sum(1 for s in v if s == "Y"); n = sum(1 for s in v if s in ("Y", "N"))
            summ["rates"][c][arm] = {"Y": y, "n": n, "U": len(v) - n, "wilson95": wilson(y, n)}
        for arm in "AG":
            up = down = tie = 0
            seeds = sorted({kk[2] for kk in cells})
            for s in seeds:
                d = 0
                for inp in ("ball1", "ball2"):
                    a = cells.get((arm, inp, s), {}).get(c); o = cells.get(("O", inp, s), {}).get(c)
                    if a in ("Y", "N") and o in ("Y", "N"):
                        d += (a == "Y") - (o == "Y")
                up += d > 0; down += d < 0; tie += d == 0
            summ["seed_level"][f"{c}:{arm}-O"] = {"up": up, "down": down, "tie": tie, "sign_p_two_sided": sign_p(up, down)}
    for arm in "OAG":
        v = [x["depart"]["depart_frame"] for kk, x in cells.items() if kk[0] == arm and x["depart"]]
        summ["depart"][arm] = {"departed": sum(1 for d in v if d is not None), "n": len(v),
                               "median_frame": float(np.median([d for d in v if d is not None])) if any(d is not None for d in v) else None}
    summ["cells"] = {f"{a}_{i}_s{s}": {kk: vv for kk, vv in x.items() if kk not in ("arm", "input", "seed")} for (a, i, s), x in sorted(cells.items())}
    json.dump(summ, open(os.path.join(out, "unblind.json"), "w"), indent=1, default=str)
    print(json.dumps({kk: summ[kk] for kk in ("rates", "seed_level", "depart")}, indent=1, default=str))


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"sheets": lambda: sheets(sys.argv[2], sys.argv[3]), "depart": lambda: depart(sys.argv[2], sys.argv[3]),
     "unblind": lambda: unblind(sys.argv[2], sys.argv[3])}[cmd]()
