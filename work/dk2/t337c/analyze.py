# dk2 t337c: copy of dk1 work/dk1/t336_region/analyze_b.py @dc1a6f7, names only changed (t336b_->t337c_, inj19->dc10, inj27->dc14).
"""Task 336b (dk1): same as t336 analyze.py with prefix t337c_ and arms dc10/dc14(_x17).
Task 336 (dk1): copy of work/dk2/t276/analyze_t276.py @a33fc5a; only the clip-name prefix (t336_), the arm names (reg, regsfr, reg_x17, regsfr_x17) and frames.json (t276's) changed. FROZEN before any clip.
Clips: <dir>/t276_<real_XX>_<arm>_s<seed>.mp4, arm in {plain, nphys, nphys_x17}; 93 f @ 24 fps, 832x480.
Per clip: tools/pend_acf (--fps 24 --skip 8) and tools/trk_ballfall/measure_pend.py v1 (referee PASS) -> period in s;
flicker = std over frames of the mean grey level / its mean (Raj #5634).
CLEAN (Raj v2 rule, #5634/analyze_e7): pend_acf flag ok AND flicker < 0.08 AND |P_mp/P_acf - 1| <= 0.10.
ratio = P_acf_s / P_real_s (P_real_s from frames.json = real clip's measure_pend period / 25 Hz). Non-clean clips are counted, not dropped silently.
Per arm: n, clean, within10 (|ratio-1|<=.10 among clean), median ratio [bootstrap 95% CI over clean clips], median flicker.
Expected (pre-registered reading): nphys median ratio within 10% of 1 with >= 12/18 clean -> 'Nano-Phys sets the real period on held-out frames';
nphys_x17 median ratio ~1.7 (within 1.45-1.95) -> 'output follows the proxy (copy-through control passes)'; plain gives Nano's own clock.
Also writes a frame strip (8 evenly spaced frames, one row per clip) per arm.
usage: python3 -I analyze_t276.py <clip_dir> <out_dir>"""
import json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import cv2, numpy as np
H = Path(__file__).resolve().parent; R = H.parents[2]
ACF, MP = R / "tools/pend_acf/pend_acf.py", R / "tools/trk_ballfall/measure_pend.py"
FR = {f["id"]: f for f in json.load(open(H / "frames.json"))}
def run(cmd):
    r = subprocess.run([sys.executable, "-I", *map(str, cmd)], capture_output=True, text=True); s = r.stdout
    try: return json.loads(s[s.find("{"):]) if cmd[0] == MP else json.loads(s.strip().splitlines()[-1])
    except Exception: return {"flag": "error"}
def frames(p):
    c = cv2.VideoCapture(str(p)); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    return F
def one(p):
    m = re.match(r"t337c_(real_\d\d)_(dc10_x17|dc14_x17|dc10|dc14)_s(\d+)$", p.stem)
    if not m: return None
    fid, arm, s = m.group(1), m.group(2), int(m.group(3))
    a = run([ACF, p, "--fps", "24", "--skip", "8"]); b = run([MP, p, "--fps", "24"])
    F = frames(p); g = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean() for f in F])
    fk = float(g.std() / g.mean())
    Pa = a.get("period_frames"); Pa_s = Pa / 24 if Pa else None; Pm_s = b.get("period_s")
    agree = bool(Pa_s and Pm_s and abs(Pm_s / Pa_s - 1) <= 0.10)
    clean = a.get("flag") == "ok" and fk < 0.08 and agree
    Pr = FR[fid]["P_real_s"]
    return dict(clip=p.stem, frame=fid, arm=arm, seed=s, n_frames=len(F), P_acf_s=Pa_s, flag_acf=a.get("flag"), P_mp_s=Pm_s,
                flag_mp=b.get("flag"), r2_mp=b.get("r2"), flicker=round(fk, 4), clean=clean,
                ratio=(Pa_s / Pr if clean else None), ratio_mp=(Pm_s / Pr if clean else None))
def strip(rows, d, arm, out):
    T = []
    for r in sorted(rows, key=lambda r: (r["frame"], r["seed"])):
        F = frames(d / (r["clip"] + ".mp4")); idx = np.linspace(0, len(F) - 1, 8).astype(int)
        row = np.hstack([cv2.resize(F[i][40:400, 180:470], (145, 180)) for i in idx])
        cv2.putText(row, f"{r['frame']} s{r['seed']} {'CLEAN' if r['clean'] else 'x'} fl{r['flicker']}", (4, 16), 0, 0.45, (0, 255, 255), 1)
        T.append(row)
    if T: cv2.imwrite(str(out / f"strip_{arm}.jpg"), np.vstack(T), [cv2.IMWRITE_JPEG_QUALITY, 80])
if __name__ == "__main__":
    d, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(6) as ex: rows = [r for r in ex.map(one, sorted(d.glob("t337c_*.mp4"))) if r]
    res = {"rows": rows, "arms": {}}
    rng = np.random.default_rng(0)
    for arm in ("dc10", "dc14", "dc10_x17", "dc14_x17"):
        Rw = [r for r in rows if r["arm"] == arm]; C = [r["ratio"] for r in Rw if r["clean"]]
        ci = None
        if len(C) >= 3:
            bm = np.median(np.array(C)[rng.integers(0, len(C), (20000, len(C)))], 1); ci = [float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))]
        res["arms"][arm] = dict(n=len(Rw), clean=len(C), within10=sum(abs(c - 1) <= .1 for c in C),
                                median_ratio=(float(np.median(C)) if C else None), ci95=ci,
                                median_ratio_mp=(float(np.median([r["ratio_mp"] for r in Rw if r["clean"]])) if C else None),
                                median_flicker=(float(np.median([r["flicker"] for r in Rw])) if Rw else None))
        strip(Rw, d, arm, out)
    json.dump(res, open(out / "t276_results.json", "w"), indent=1)
    md = ["| arm | clean | within 10% | median P/P_real (acf) [95% CI] | median (mp) | median flicker |", "|---|---|---|---|---|---|"]
    for arm, a in res["arms"].items():
        md.append(f"| {arm} | {a['clean']}/{a['n']} | {a['within10']} | {a['median_ratio']} {a['ci95']} | {a['median_ratio_mp']} | {a['median_flicker']} |")
    (out / "t276_table.md").write_text("\n".join(md) + "\n"); print("\n".join(md))
