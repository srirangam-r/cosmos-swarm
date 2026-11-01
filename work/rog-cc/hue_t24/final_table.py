"""rog-cc: one table of every task-24 contrast (HUE judge + DOVER/DD), from analyze_t24.py / analyze_nv.py outputs.
Runs both analyzers for each --ref in REFS (skips arms whose .done marker is missing), then prints:
  contrast | HUE overall | HUE Physical | DOVER fused | DOVER tech | DOVER aes | dd_norm
as mean ± se [ci90] (n_pos/n). Margins: HUE 0.03 / 0.04 human-approved (#1306); DOVER 0.02 PROPOSED (not approved).
Usage: python3 final_table.py HUE_T24_DIR [--out table.json]
"""
import sys, os, json, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = ["baseL", "loraC", "loraB"]
CONTRASTS = [  # (arm, ref, label)
    ("baseL", "base", "baseL-base (A/A box null)"),
    ("loraC", "base", "C-base"), ("loraA", "base", "A-base"), ("loraB", "base", "B-base"),
    ("loraC", "baseL", "C-baseL"), ("loraA", "baseL", "A-baseL"), ("loraB", "baseL", "B-baseL"),
    ("loraA", "loraC", "A-C"), ("loraB", "loraC", "B-C"),
    ("loraA", "loraB", "A-B (same box, only g differs)"),
]
HUE = ["overall", "Physical Laws"]; NV = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_norm"]


def run(d):
    out = {}
    for ref in REFS:
        if not os.path.exists(f"{d}/res/{ref}.json.done"): continue
        h, n = f"{d}/summary_hue_ref_{ref}.json", f"{d}/summary_nv_ref_{ref}.json"
        subprocess.run(["python3", f"{HERE}/analyze_t24.py", f"{d}/res", "--ref", ref, "--out", h], check=True, capture_output=True)
        if os.path.exists(f"{d}/res_nv/{ref}.json.done"):
            subprocess.run(["python3", f"{HERE}/analyze_nv.py", f"{d}/res_nv", "--ref", ref, "--out", n], check=True, capture_output=True)
        out[ref] = (h, n)
    return out


def cell(v):
    if not v: return "-"
    return f"{v['mean']:+.4f}±{v['se']:.4f} [{v['ci90'][0]:+.3f},{v['ci90'][1]:+.3f}] ({v['n_pos']}/{v['n_prompts']})"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("d"); ap.add_argument("--out"); a = ap.parse_args()
    files = run(a.d)
    S = {}
    for ref, (h, n) in files.items():
        for f in (h, n):
            if os.path.exists(f):
                for k, blk in json.load(open(f)).items():
                    if k.startswith("paired_vs_"):
                        for arm, cats in blk.items(): S.setdefault((arm, k[10:]), {}).update(cats or {})
    table = []
    print(f"{'contrast':34s} " + " | ".join(HUE + NV))
    for arm, ref, lab in CONTRASTS:
        c = dict(S.get((arm, ref)) or {})
        # never report a partially judged/scored arm (the judge writes its JSON incrementally)
        for sub, keys in (("res", HUE), ("res_nv", NV)):
            if not all(os.path.exists(f"{a.d}/{sub}/{x}.json.done") for x in (arm, ref)):
                for k in keys: c.pop(k, None)
        if not c: continue
        row = {"contrast": lab, **{k: c.get(k) for k in HUE + NV}}
        table.append(row)
        print(f"{lab:34s} " + " | ".join(cell(c.get(k)) for k in HUE + NV))
    if a.out:
        json.dump([{k: ({kk: vv for kk, vv in v.items() if kk != 'per_prompt'} if isinstance(v, dict) else v) for k, v in r.items()} for r in table],
                  open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
