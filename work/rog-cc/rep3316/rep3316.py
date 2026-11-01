#!/usr/bin/env python3
"""rep3316 readout tools (PREREG.md, commit 69895b2). Written before any clip arrived.
  sheets <clips_dir> <out_dir>   one sheet per (ball, seed): rows A/B/C = F/R/N shuffled (rng seed 3316); each row =
                                 full frames 0,30,60,92 (small) + corridor crop every 2nd frame f60-92. Key -> UNBLIND_key.json.
  unblind <out_dir> <codes.csv>  codes csv: hex,A_rest,B_rest,C_rest,A_art,B_art,C_art (Y/N/U). Prints per-arm counts and paired
                                 R-F, R-N, N-F discordant pairs with exact two-sided sign-test p.
  motion <clips_dir> --out x.json  mean |d grey| over pairs 60..92, whole frame and the corridor band; paired d vs F (mean, SE, n_neg)."""
import sys, os, re, glob, json, random, math
import numpy as np, cv2

pat = re.compile(r"rep3316_(F|R|N)_(ball\d)_s(\d+)\.mp4$")
CROP = (180, 100, 420, 430)   # x0,y0,x1,y1 ball corridor (fixed from the dd33 input frame before any clip)
BAND = (150, 250, 420, 430)   # plank band for the motion metric
FULL = [0, 30, 60, 92]; STRIP = list(range(60, 93, 2))


def read(path):
    cap = cv2.VideoCapture(path); F = []
    while True:
        ok, x = cap.read()
        if not ok:
            break
        F.append(x)
    return F


def collect(cd):
    C = {}
    for f in glob.glob(os.path.join(cd, "rep3316_*.mp4")):
        m = pat.search(f)
        if m:
            C.setdefault((m.group(2), int(m.group(3))), {})[m.group(1)] = f
    return C


def row(F):
    blank = np.zeros((480, 832, 3), np.uint8)
    get = lambda i: F[i] if i < len(F) else blank
    full = [cv2.resize(get(i), (208, 120)) for i in FULL]
    x0, y0, x1, y1 = CROP
    crops = [cv2.resize(get(i)[y0:y1, x0:x1], (96, 132)) for i in STRIP]
    for c, i in zip(crops, STRIP):
        cv2.putText(c, str(i), (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    top = np.hstack(full); bot = np.hstack(crops)
    W = max(top.shape[1], bot.shape[1])
    pad = lambda a: np.hstack([a, np.zeros((a.shape[0], W - a.shape[1], 3), np.uint8)]) if a.shape[1] < W else a
    return np.vstack([pad(top), pad(bot)])


def sheets(cd, od):
    os.makedirs(od, exist_ok=True); C = collect(cd); rng = random.Random(3316); key = {}
    for k in sorted(C):
        d = C[k]
        if len(d) < 3:
            print("incomplete", k, sorted(d)); continue
        arms = ["F", "R", "N"]; rng.shuffle(arms); hx = "%06x" % rng.getrandbits(24)
        rows = []
        for lab, a in zip("ABC", arms):
            r = row(read(d[a])); cv2.putText(r, lab, (4, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2); rows.append(r)
            rows.append(np.full((6, r.shape[1], 3), 255, np.uint8))
        cv2.imwrite(os.path.join(od, hx + ".jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
        key[hx] = {"ball": k[0], "seed": k[1], "rows": dict(zip("ABC", arms))}
    json.dump(key, open(os.path.join(od, "UNBLIND_key.json"), "w"), indent=1)
    print(len(key), "sheets ->", od, "(key written; do not open before coding)")


def sign_p(up, dn):
    n = up + dn
    if n == 0:
        return 1.0
    k = min(up, dn); return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def unblind(od, codes):
    key = json.load(open(os.path.join(od, "UNBLIND_key.json"))); cell = {}
    for line in open(codes):
        p = [x.strip() for x in line.strip().split(",")]
        if len(p) < 7 or p[0] == "hex":
            continue
        k = key[p[0]]
        for i, lab in enumerate("ABC"):
            cell.setdefault((k["ball"], k["seed"]), {})[k["rows"][lab]] = {"rest": p[1 + i], "art": p[4 + i]}
    out = {"cells": {f"{b}_s{s}": v for (b, s), v in sorted(cell.items())}, "arms": {}, "paired": {}}
    for a in "FRN":
        out["arms"][a] = {c: sum(v[a][c] == "Y" for v in cell.values()) for c in ("rest", "art")} | {"n": len(cell)}
    for a, b in (("R", "F"), ("R", "N"), ("N", "F")):
        up = sum(v[a]["rest"] == "Y" and v[b]["rest"] != "Y" for v in cell.values())
        dn = sum(v[b]["rest"] == "Y" and v[a]["rest"] != "Y" for v in cell.values())
        out["paired"][f"{a}-{b}"] = {"rest_up": up, "rest_down": dn, "sign_p_two_sided": sign_p(up, dn)}
    print(json.dumps(out, indent=1)); return out


def motion(cd, outp):
    C = collect(cd); per = {}
    for k, d in sorted(C.items()):
        for a, f in d.items():
            F = [cv2.cvtColor(x, cv2.COLOR_BGR2GRAY).astype(np.float32) for x in read(f)]
            if len(F) < 93:
                continue
            x0, y0, x1, y1 = BAND
            dw = [np.abs(F[i + 1] - F[i]).mean() for i in range(60, 92)]
            db = [np.abs(F[i + 1][y0:y1, x0:x1] - F[i][y0:y1, x0:x1]).mean() for i in range(60, 92)]
            per.setdefault(f"{k[0]}_s{k[1]}", {})[a] = {"late_whole": float(np.mean(dw)), "late_band": float(np.mean(db))}
    res = {"per_cell": per, "paired": {}}
    for a, b in (("R", "F"), ("N", "F"), ("R", "N")):
        for m in ("late_whole", "late_band"):
            d = np.array([v[a][m] - v[b][m] for v in per.values() if a in v and b in v])
            if len(d):
                res["paired"][f"{a}-{b}:{m}"] = {"mean": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None,
                                                 "n": int(len(d)), "n_neg": int((d < 0).sum())}
    json.dump(res, open(outp, "w"), indent=1); print(json.dumps(res["paired"], indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "sheets":
        sheets(sys.argv[2], sys.argv[3])
    elif c == "unblind":
        unblind(sys.argv[2], sys.argv[3])
    elif c == "motion":
        motion(sys.argv[2], sys.argv[sys.argv.index("--out") + 1])
