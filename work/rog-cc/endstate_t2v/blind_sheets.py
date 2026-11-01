#!/usr/bin/env python3
"""Task 133 blind eye check (PREREG_ADDENDUM.md). For every (prompt, seed) with base, R and N clips present,
write one sheet <hex>.jpg with three rows A/B/C (arm order shuffled, seeded) x frames 0,24,48,68,76,84,92.
The key goes to <out>/UNBLIND_key.json; do not open it before coding.
Codes file (csv, one line per sheet): hex,A_rest,B_rest,C_rest,A_art,B_art,C_art
  rest = Y if every object that moved earlier is visibly still across frames 68-92, N if something still moves, U unclear/no motion at all
  art  = Y if a gross artifact (object appears/vanishes/merges/teleports) is visible, else N
Usage: blind_sheets.py make <clips_dir> <out_dir> [--subset physics]
       blind_sheets.py unblind <out_dir> <codes.csv>"""
import sys, os, re, glob, json, random, hashlib
import numpy as np, cv2

FR = [0, 24, 48, 68, 76, 84, 92]; TW, TH = 192, 111
pat = re.compile(r"es_(base|R|N)_((?:physics|robot)_\d+)_s(\d+)\.mp4$")


def frames(path):
    cap = cv2.VideoCapture(path); out = {}; i = 0
    while True:
        ok, x = cap.read()
        if not ok:
            break
        if i in FR:
            out[i] = cv2.resize(x, (TW, TH), interpolation=cv2.INTER_AREA)
        i += 1
    return [out.get(f, np.zeros((TH, TW, 3), np.uint8)) for f in FR]


def make(cd, od, subset=None):
    os.makedirs(od, exist_ok=True); C = {}
    for f in glob.glob(os.path.join(cd, "es_*.mp4")):
        m = pat.search(f)
        if m and (subset is None or m.group(2).startswith(subset)):
            C.setdefault((m.group(2), int(m.group(3))), {})[m.group(1)] = f
    rng = random.Random(133); key = {}
    for (p, s) in sorted(C):
        d = C[(p, s)]
        if len(d) < 3:
            continue
        arms = ["base", "R", "N"]; rng.shuffle(arms)
        hx = hashlib.sha1(f"{p}|{s}|133".encode()).hexdigest()[:6]
        rows = []
        for lab, a in zip("ABC", arms):
            r = np.concatenate(frames(d[a]), axis=1)
            band = np.full((TH, 40, 3), 255, np.uint8); cv2.putText(band, lab, (8, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
            rows.append(np.concatenate([band, r], axis=1))
        hdr = np.full((22, rows[0].shape[1], 3), 255, np.uint8)
        for j, f in enumerate(FR):
            cv2.putText(hdr, f"f{f}", (40 + j * TW + 70, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.imwrite(os.path.join(od, hx + ".jpg"), np.concatenate([hdr] + rows, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 85])
        key[hx] = {"prompt": p, "seed": s, "rows": dict(zip("ABC", arms))}
    json.dump(key, open(os.path.join(od, "UNBLIND_key.json"), "w"), indent=1)
    print(f"{len(key)} sheets -> {od}")


def unblind(od, codes):
    key = json.load(open(os.path.join(od, "UNBLIND_key.json"))); T = {}
    for line in open(codes):
        x = [t.strip() for t in line.strip().split(",")]
        if len(x) < 7 or x[0] not in key:
            continue
        k = key[x[0]]
        for i, lab in enumerate("ABC"):
            a = k["rows"][lab]
            T.setdefault(a, []).append({"prompt": k["prompt"], "seed": k["seed"], "rest": x[1 + i].upper(), "art": x[4 + i].upper()})
    S = {a: {"n": len(L), "rest_Y": sum(r["rest"] == "Y" for r in L), "rest_N": sum(r["rest"] == "N" for r in L),
             "rest_U": sum(r["rest"] == "U" for r in L), "art_Y": sum(r["art"] == "Y" for r in L)} for a, L in T.items()}
    # paired (same prompt, seed) R vs base and R vs N on rest Y vs N (U excluded)
    def pairs(a, b):
        A = {(r["prompt"], r["seed"]): r["rest"] for r in T.get(a, [])}; B = {(r["prompt"], r["seed"]): r["rest"] for r in T.get(b, [])}
        ks = [k for k in A if k in B and A[k] in "YN" and B[k] in "YN"]
        return {"n": len(ks), "a_only_rest": sum(A[k] == "Y" and B[k] == "N" for k in ks), "b_only_rest": sum(A[k] == "N" and B[k] == "Y" for k in ks)}
    S["pairs"] = {"R_vs_base": pairs("R", "base"), "R_vs_N": pairs("R", "N"), "N_vs_base": pairs("N", "base")}
    json.dump({"summary": S, "codes": T}, open(os.path.join(od, "eye.json"), "w"), indent=1)
    print(json.dumps(S, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "make":
        make(sys.argv[2], sys.argv[3], sys.argv[sys.argv.index("--subset") + 1] if "--subset" in sys.argv else None)
    else:
        unblind(sys.argv[2], sys.argv[3])
