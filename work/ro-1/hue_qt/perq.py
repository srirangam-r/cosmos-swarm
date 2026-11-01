#!/usr/bin/env python3
"""Per-question p_yes: F vs QT (paired) vs real ref."""
import json, os
import numpy as np
D = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(D, "pair.json")))
R = json.load(open(os.path.join(D, "res.json")))["results"]
q = {}; txt = {}
for r in R:
    s = os.path.basename(r["clip"])[:-4]
    for x in r["rows"]:
        q.setdefault(s, {}).setdefault(x["id"], []).append(x["p_yes"]); txt[x["id"]] = (x["category"][:4], x["text"][:70])
q = {s: {i: float(np.mean(v)) for i, v in d.items()} for s, d in q.items()}
pairs = P["QT-F"]["pairs"]; out = {}
for i in sorted(txt):
    d = np.array([q[t][i] - q[f][i] for f, t in pairs])
    out[i] = dict(cat=txt[i][0], text=txt[i][1], F=float(np.mean([q[f][i] for f, _ in pairs])), QT=float(np.mean([q[t][i] for _, t in pairs])),
                  diff=float(d.mean()), se=float(d.std(ddof=1)/np.sqrt(len(d))), real=q["real_ball1_dd32_93f"][i],
                  F_b1=float(np.mean([q[f][i] for f, _ in pairs if "ball1" in f])))
    o = out[i]; print(f"Q{i:2d} {o['cat']} F {o['F']:.3f} QT {o['QT']:.3f} d {o['diff']:+.3f}±{o['se']:.3f} | real {o['real']:.3f} (F_b1 {o['F_b1']:.3f}) {o['text']}")
json.dump(out, open(os.path.join(D, "perq.json"), "w"), indent=1)
