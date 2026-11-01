#!/usr/bin/env python3
"""Task 133 PREREG addendum A2 (EXPLORATORY): blind native-rate spawn / gone codes (reply to rahul-3 #3325).
For every (prompt, seed) with base, R and N present, write TWO sheets per cell, arm order shuffled (seed 2133, new hexes):
  <hex>_early.jpg : rows A/B/C x frames 0..30 step 2 (16 cols)
  <hex>_late.jpg  : rows A/B/C x frames 56..92 step 4 (10 cols)
Key -> <out>/UNBLIND_key.json (do not open before codes are committed).
Codes csv, one line per cell: hex,A_spawn,B_spawn,C_spawn,A_gone,B_gone,C_gone
  spawn = Y if, within f0-30, an object (or debris) not present at f0 pops into view mid-frame or an object pops out
          (not entering smoothly from a frame edge, not a hand/tool the prompt describes); else N
  gone  = Y if the main object the prompt describes as moving has left the frame or vanished by f92
          (in the late sheet it is absent although it was present at f56 or in the early sheet); else N
Usage: spawn_sheets.py make <clips_dir> <out_dir> [--subset physics]
       spawn_sheets.py unblind <out_dir> <codes.csv>"""
import sys, os, re, glob, json, random, hashlib
import numpy as np, cv2

SETS = {"early": list(range(0, 31, 2)), "late": list(range(56, 93, 4))}
TW, TH = 160, 92
pat = re.compile(r"es_(base|R|N)_((?:physics|robot)_\d+)_s(\d+)\.mp4$")


def grab(path, want):
    cap = cv2.VideoCapture(path); out = {}; i = 0
    while True:
        ok, x = cap.read()
        if not ok:
            break
        if i in want:
            out[i] = cv2.resize(x, (TW, TH), interpolation=cv2.INTER_AREA)
        i += 1
    return out


def make(cd, od, subset=None):
    os.makedirs(od, exist_ok=True); C = {}
    for f in glob.glob(os.path.join(cd, "es_*.mp4")):
        m = pat.search(f)
        if m and (subset is None or m.group(2).startswith(subset)):
            C.setdefault((m.group(2), int(m.group(3))), {})[m.group(1)] = f
    rng = random.Random(2133); key = {}
    allf = set(SETS["early"]) | set(SETS["late"])
    for (p, s) in sorted(C):
        d = C[(p, s)]
        if len(d) < 3:
            continue
        arms = ["base", "R", "N"]; rng.shuffle(arms)
        hx = hashlib.sha1(f"{p}|{s}|2133".encode()).hexdigest()[:6]
        G = {a: grab(d[a], allf) for a in arms}
        for nm, FR in SETS.items():
            rows = []
            for lab, a in zip("ABC", arms):
                r = np.concatenate([G[a].get(f, np.zeros((TH, TW, 3), np.uint8)) for f in FR], axis=1)
                band = np.full((TH, 36, 3), 255, np.uint8); cv2.putText(band, lab, (6, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2)
                rows.append(np.concatenate([band, r], axis=1))
            hdr = np.full((20, rows[0].shape[1], 3), 255, np.uint8)
            for j, f in enumerate(FR):
                cv2.putText(hdr, f"f{f}", (36 + j * TW + 60, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
            cv2.imwrite(os.path.join(od, f"{hx}_{nm}.jpg"), np.concatenate([hdr] + rows, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 85])
        key[hx] = {"prompt": p, "seed": s, "rows": dict(zip("ABC", arms))}
    json.dump(key, open(os.path.join(od, "UNBLIND_key.json"), "w"), indent=1)
    print(f"{len(key)} cells -> {od}")


def unblind(od, codes):
    key = json.load(open(os.path.join(od, "UNBLIND_key.json"))); T = {}
    for line in open(codes):
        x = [t.strip().upper() for t in line.strip().split(",")]
        if len(x) < 7 or x[0].lower() not in key:
            continue
        k = key[x[0].lower()]
        for i, lab in enumerate("ABC"):
            T.setdefault(k["rows"][lab], {})[(k["prompt"], k["seed"])] = {"spawn": x[1 + i], "gone": x[4 + i]}
    S = {a: {"n": len(D), "spawn_Y": sum(v["spawn"] == "Y" for v in D.values()), "gone_Y": sum(v["gone"] == "Y" for v in D.values())} for a, D in T.items()}
    def pairs(a, b, c):
        A, B = T.get(a, {}), T.get(b, {}); ks = [k for k in A if k in B]
        return {"n": len(ks), "a_only": sum(A[k][c] == "Y" and B[k][c] != "Y" for k in ks), "b_only": sum(A[k][c] != "Y" and B[k][c] == "Y" for k in ks)}
    S["pairs"] = {f"{c}:{a}_vs_{b}": pairs(a, b, c) for c in ("spawn", "gone") for a, b in (("R", "base"), ("R", "N"), ("N", "base"))}
    json.dump({"summary": S, "codes": {a: [{"prompt": k[0], "seed": k[1], **v} for k, v in D.items()] for a, D in T.items()}},
              open(os.path.join(od, "spawn_eye.json"), "w"), indent=1)
    print(json.dumps(S, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "make":
        make(sys.argv[2], sys.argv[3], sys.argv[sys.argv.index("--subset") + 1] if "--subset" in sys.argv else None)
    elif sys.argv[1] == "unblind":
        unblind(sys.argv[2], sys.argv[3])
