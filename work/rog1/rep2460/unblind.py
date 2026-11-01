#!/usr/bin/env python3
"""Unblind + paired analysis for the rog1 replication of #2460. Run ONLY after eye_codes.csv is written.
Usage: python3 unblind.py blind.json eye_codes.csv KEY.json [nv_scores.json] > summary.json
eye_codes.csv columns: name,settled_by_f92(Y/N),rest_frame(int or -),identity_ok(Y/N),notes"""
import sys, json, csv, math
blind = json.load(open(sys.argv[1]))
eye = {r["name"]: r for r in csv.DictReader(open(sys.argv[2]))}
key = json.load(open(sys.argv[3]))
nv = {}
if len(sys.argv) > 4:
    raw = json.load(open(sys.argv[4]))
    clips = raw.get("clips", raw) if isinstance(raw, dict) else raw
    if isinstance(clips, dict):
        for k, v in clips.items():
            nv[k.split("/")[-1].replace(".mp4", "")] = v
    else:
        for v in clips:
            nv[str(v.get("clip", v.get("name", ""))).split("/")[-1].replace(".mp4", "")] = v

rows = []
for n, k in key.items():
    r = dict(name=n, **k)
    r.update(blind.get(n, {}))
    e = eye.get(n, {})
    r["settled"] = e.get("settled_by_f92", "?")
    r["rest_frame"] = e.get("rest_frame", "?")
    r["identity_ok"] = e.get("identity_ok", "?")
    for m in ("dover_fused", "dover_technical", "dover_aesthetic", "dd_norm", "dd_binary"):
        if n in nv and m in nv[n]:
            r[m] = nv[n][m]
    rows.append(r)

def ms(xs):
    xs = [x for x in xs if x is not None]
    if not xs: return None
    m = sum(xs) / len(xs)
    se = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1) / len(xs)) if len(xs) > 1 else float("nan")
    return {"mean": m, "se": se, "n": len(xs)}

out = {"per_clip": sorted(rows, key=lambda r: (r["image"], r["seed"], r["arm"])), "arms": {}, "paired_QT_minus_F": {}}
metrics = ["moving_frac_last24", "p99diff_last24_mean", "still_since", "dover_fused", "dover_technical", "dover_aesthetic", "dd_norm", "dd_binary"]
for arm in ("F", "QT"):
    a = [r for r in rows if r["arm"] == arm]
    out["arms"][arm] = {m: ms([r.get(m) for r in a]) for m in metrics}
    out["arms"][arm]["settled"] = f'{sum(r["settled"] == "Y" for r in a)}/{len(a)}'
by = {}
for r in rows:
    by.setdefault((r["image"], r["seed"]), {})[r["arm"]] = r
for m in metrics:
    d = [p["QT"][m] - p["F"][m] for p in by.values() if "QT" in p and "F" in p and p["QT"].get(m) is not None and p["F"].get(m) is not None]
    if d:
        s = ms(d); s["n_lower"] = sum(x < 0 for x in d); out["paired_QT_minus_F"][m] = s
print(json.dumps(out, indent=1, default=str))
