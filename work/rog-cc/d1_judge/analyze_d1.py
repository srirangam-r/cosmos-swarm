#!/usr/bin/env python3
"""PREREG A3 analysis (work/rog-cc/hue_t24/PREREG.md, commit 9a4f7c0): plausibility judge on the Deliverable-1
mid-fall recipe. Input: hue_judge output for box_ctrl_* (held f0, BASE), box_mid_* (mid-fall, RECIPE),
realball_* (real f0) and realmid_* (real mid-fall). Usage: analyze_d1.py judge.json [--out res.json]

Primary question sets (Q1 and Q5 presuppose a held start, so they are dropped):
  Physical = Q2,Q3,Q4,Q6,Q13 ; Overall = Q2-Q4,Q6-Q13 (11 Qs). All13 is secondary.
Per clip: P(Yes) averaged over offsets, then over the questions in the set.
Delta_nano = mean(mid) - mean(ctrl) over 8 vs 8 clips, Welch SE, one-sided 95% LB.
Delta_real = mean over balls of (realmid_b - realball_b). Net = Delta_nano - Delta_real.
Verdict: non-inferior if LB > -margin (0.03 Overall, 0.04 Physical; HUE margins #1306);
improvement only if LB > 0 and Net > 0.
"""
import argparse, json, math, re, statistics as st
from collections import defaultdict

SETS = {"Physical": [2, 3, 4, 6, 13], "Overall": [2, 3, 4] + list(range(6, 14)), "All13": list(range(1, 14))}
MARGIN = {"Physical": 0.04, "Overall": 0.03, "All13": 0.03}


def t95(df):  # one-sided 95% t quantile
    try:
        from scipy.stats import t
        return float(t.ppf(0.95, df))
    except Exception:
        tab = {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895, 8: 1.860, 9: 1.833, 10: 1.812,
               11: 1.796, 12: 1.782, 13: 1.771, 14: 1.761}
        return tab.get(int(df), 1.753)


def group(clip):
    b = re.search(r"(box_ctrl|box_mid|realball|realmid)_(?:b)?(\d)", clip.split("/")[-1])
    return b.group(1), int(b.group(2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("judge")
    ap.add_argument("--out")
    a = ap.parse_args()
    d = json.load(open(a.judge))
    pq = defaultdict(lambda: defaultdict(list))  # clip -> qid -> [p_yes per offset]
    for r in d["results"]:
        for row in r["rows"]:
            pq[r["clip"]][int(row["id"])].append(row["p_yes"])
    clips = {}
    for c, qs in pq.items():
        g, b = group(c)
        s = {k: st.mean(st.mean(qs[q]) for q in ids if q in qs) for k, ids in SETS.items()}
        s["per_q"] = {q: st.mean(v) for q, v in sorted(qs.items())}
        clips[c.split("/")[-1]] = dict(group=g, ball=b, **s)
    out = {"n_clips": {g: sum(1 for v in clips.values() if v["group"] == g)
                       for g in ("box_ctrl", "box_mid", "realball", "realmid")}, "sets": {}}
    for k in SETS:
        ctrl = [v[k] for v in clips.values() if v["group"] == "box_ctrl"]
        mid = [v[k] for v in clips.values() if v["group"] == "box_mid"]
        dn = st.mean(mid) - st.mean(ctrl)
        va, vb = st.variance(mid) / len(mid), st.variance(ctrl) / len(ctrl)
        se = math.sqrt(va + vb)
        df = (va + vb) ** 2 / (va ** 2 / (len(mid) - 1) + vb ** 2 / (len(ctrl) - 1)) if se > 0 else 1
        lb = dn - t95(df) * se
        per_ball = {}
        for b in (1, 2):
            m = [v[k] for v in clips.values() if v["group"] == "box_mid" and v["ball"] == b]
            c = [v[k] for v in clips.values() if v["group"] == "box_ctrl" and v["ball"] == b]
            per_ball[b] = st.mean(m) - st.mean(c)
        real = {}
        for b in (1, 2):
            rm = [v[k] for v in clips.values() if v["group"] == "realmid" and v["ball"] == b]
            rf = [v[k] for v in clips.values() if v["group"] == "realball" and v["ball"] == b]
            if rm and rf:
                real[b] = rm[0] - rf[0]
        dr = st.mean(real.values()) if real else float("nan")
        out["sets"][k] = dict(base_mean=st.mean(ctrl), recipe_mean=st.mean(mid), delta_nano=dn, welch_se=se, df=df,
                              lb95=lb, per_ball=per_ball, delta_real=dr, real_per_ball=real, net=dn - dr,
                              real_f0=st.mean(v[k] for v in clips.values() if v["group"] == "realball"),
                              real_mid=st.mean(v[k] for v in clips.values() if v["group"] == "realmid"),
                              non_inferior=lb > -MARGIN[k], improvement=(lb > 0 and dn - dr > 0), margin=MARGIN[k])
    # per-question means by group (secondary)
    pqg = {}
    for q in range(1, 14):
        pqg[q] = {g: st.mean(v["per_q"][q] for v in clips.values() if v["group"] == g and q in v["per_q"])
                  for g in ("box_ctrl", "box_mid", "realball", "realmid")}
    out["per_question"] = pqg
    out["clips"] = clips
    s = json.dumps(out, indent=1)
    if a.out:
        open(a.out, "w").write(s)
    print(json.dumps({"n_clips": out["n_clips"], "sets": out["sets"]}, indent=1))
    for q, v in pqg.items():
        print(f"Q{q:2d} ctrl {v['box_ctrl']:.3f} mid {v['box_mid']:.3f} | real f0 {v['realball']:.3f} mid {v['realmid']:.3f}")


if __name__ == "__main__":
    main()
