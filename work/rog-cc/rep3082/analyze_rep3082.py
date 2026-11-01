#!/usr/bin/env python3
"""rog-cc replication of #3082: independent readout (see PREREG.md in this folder).
  analyze_rep3082.py metrics <clips_dir> <out_dir>   -> out/metrics.json, out/contrasts.json, blind strips out/blind/<hex>.jpg,
                                                        out/UNBLIND_key.json (do not open before eye-coding)
  analyze_rep3082.py unblind <out_dir> <codes.csv>   -> out/eye.json (codes.csv: hex,rest(Y/N/U),artifact(Y/N))
Primary metric last20: mean over the final 20 frame-pairs of mean |d grey| in corridor x220:360, y130:360 (832x480)."""
import sys, os, re, json, glob, random, math
import numpy as np, cv2
from scipy import stats

NAME = re.compile(r"r3082_(?P<arm>[A-Za-z0-9]+)_(?P<inp>ball[12])_s(?P<seed>\d+)$")
INPUTS = {"ball1": "gauge_ball1_dd33_832x480.png", "ball2": "gauge_ball2_dd35_832x480.png"}
CONTRASTS = [("P1", "S12a4all", "A0"), ("P2", "S12a4all", "R12a4all"), ("QT-A0", "QT", "A0"),
             ("S12a4e-A0", "S12a4e", "A0"), ("R12a4all-A0", "R12a4all", "A0")]


def read_grey(path):
    cap = cv2.VideoCapture(path); fr = []; rgb = []
    while True:
        ok, x = cap.read()
        if not ok:
            break
        fr.append(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY).astype(np.float32)); rgb.append(x)
    return np.stack(fr), rgb


def metrics(clips, out):
    os.makedirs(out, exist_ok=True)
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "raj-opus-1", "steer128")
    ref = {k: cv2.imread(os.path.join(src, v)) for k, v in INPUTS.items()}
    res = {}
    for f in sorted(glob.glob(os.path.join(clips, "r3082_*.mp4"))):
        k = os.path.basename(f)[:-4]; m = NAME.match(k)
        if not m:
            print("UNPARSED", k, file=sys.stderr); continue
        g, rgb = read_grey(f)
        c = g[:, 130:360, 220:360]; d = np.abs(np.diff(c, axis=0)).mean((1, 2))
        r = ref.get(m["inp"]); f0mae = None
        if r is not None and r.shape == rgb[0].shape:
            f0mae = float(np.abs(rgb[0].astype(np.float32) - r.astype(np.float32)).mean())
        res[k] = dict(arm=m["arm"], inp=m["inp"], seed=int(m["seed"]), n=len(g), early=float(d[1:45].mean()),
                      late=float(d[45:].mean()), last20=float(d[-20:].mean()), f0_mae_vs_input=f0mae)
    json.dump(res, open(os.path.join(out, "metrics.json"), "w"), indent=1)
    by = {(v["arm"], v["inp"], v["seed"]): v["last20"] for v in res.values()}
    con = {}
    for lab, a, b in CONTRASTS:
        units = sorted({(i, s) for (x, i, s) in by if x == a} & {(i, s) for (x, i, s) in by if x == b})
        d = np.array([by[(a, i, s)] - by[(b, i, s)] for i, s in units])
        if len(d) < 2:
            con[lab] = dict(n=len(d)); continue
        se = d.std(ddof=1) / math.sqrt(len(d)); t90 = stats.t.ppf(0.90, len(d) - 1)
        con[lab] = dict(a=a, b=b, n=len(d), mean=float(d.mean()), se=float(se), ub90=float(d.mean() + t90 * se),
                        lb90=float(d.mean() - t90 * se), n_lower=int((d < 0).sum()),
                        units=[f"{i}_s{s}" for i, s in units], d=[float(x) for x in d])
    a0 = [v for (x, i, s), v in by.items() if x == "A0"]; qt = [v for (x, i, s), v in by.items() if x == "QT"]
    if a0 and qt:
        con["floor_check"] = dict(qt_median=float(np.median(qt)), frac_A0_below_qt_median=float(np.mean(np.array(a0) < np.median(qt))))
    json.dump(con, open(os.path.join(out, "contrasts.json"), "w"), indent=1)
    for lab, c in con.items():
        if "mean" in c:
            print(f"{lab}: {c['a']}-{c['b']} {c['mean']:+.3f}±{c['se']:.3f} 90%[{c['lb90']:+.3f},{c['ub90']:+.3f}] n={c['n']} lower={c['n_lower']}")
    print("floor", con.get("floor_check"))
    bad = {k: v["f0_mae_vs_input"] for k, v in res.items() if v["f0_mae_vs_input"] is None or v["f0_mae_vs_input"] > 15}
    print("f0 check: flagged", bad if bad else "none")
    # blind strips: every 4th frame f48..f92, ball region, shuffled hex ids
    bd = os.path.join(out, "blind"); os.makedirs(bd, exist_ok=True)
    keys = sorted(res); rnd = random.Random(3082); key = {}
    for k in keys:
        h = "%06x" % rnd.getrandbits(24)
        while h in key:
            h = "%06x" % rnd.getrandbits(24)
        key[h] = k
        _, rgb = read_grey(os.path.join(clips, k + ".mp4"))
        tiles = [cv2.resize(rgb[i][60:420, 120:520], (200, 180)) for i in range(48, min(len(rgb), 93), 4)]
        cv2.imwrite(os.path.join(bd, h + ".jpg"), np.concatenate(tiles, axis=1), [cv2.IMWRITE_JPEG_QUALITY, 80])
    json.dump(key, open(os.path.join(out, "UNBLIND_key.json"), "w"), indent=1)


def unblind(out, codes):
    key = json.load(open(os.path.join(out, "UNBLIND_key.json")))
    rows = [l.strip().split(",") for l in open(codes) if l.strip() and not l.startswith("hex")]
    eye = {}
    for h, rest, art in rows:
        m = NAME.match(key[h]); eye[key[h]] = dict(arm=m["arm"], inp=m["inp"], seed=int(m["seed"]), rest=rest, artifact=art)
    tally = {}
    for v in eye.values():
        t = tally.setdefault(v["arm"], dict(rest_Y=0, rest_N=0, rest_U=0, artifact_Y=0, n=0))
        t["rest_" + v["rest"]] += 1; t["artifact_Y"] += v["artifact"] == "Y"; t["n"] += 1
    by = {(v["arm"], v["inp"], v["seed"]): v["rest"] for v in eye.values()}
    sgn = dict(S_only=0, A0_only=0, tie=0)
    for (a, i, s), r in by.items():
        if a != "S12a4all" or ("A0", i, s) not in by:
            continue
        r0 = by[("A0", i, s)]
        if r == "Y" and r0 != "Y": sgn["S_only"] += 1
        elif r0 == "Y" and r != "Y": sgn["A0_only"] += 1
        else: sgn["tie"] += 1
    nd = sgn["S_only"] + sgn["A0_only"]
    sgn["p_sign_one_sided"] = float(stats.binomtest(sgn["S_only"], nd, 0.5, alternative="greater").pvalue) if nd else None
    json.dump(dict(per_clip=eye, tally=tally, sign_S12a4all_vs_A0=sgn), open(os.path.join(out, "eye.json"), "w"), indent=1)
    print(json.dumps(tally, indent=1)); print(sgn)


if __name__ == "__main__":
    {"metrics": metrics, "unblind": unblind}[sys.argv[1]](*sys.argv[2:])
