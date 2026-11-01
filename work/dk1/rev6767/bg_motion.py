"""Outside-box motion of plain vs nphys and its relation to the per-clip background DOVER effect (dk1 rev6767).
Usage: bg_motion.py <gen_dir> <swap_meta.json> <effects scores_box.json> <out.json>"""
import json, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from swap_box import read
gen, meta, sc, outp = Path(sys.argv[1]), json.load(open(sys.argv[2])), json.load(open(sys.argv[3])), sys.argv[4]
sc = sc if isinstance(sc, list) else sc.get("clips", list(sc.values()))
cell = {re.search(r"bx_(\d\d_s\d)_(\w\w)\.mp4", r["clip"]).groups(): r["dover_fused"] for r in sc}
rows = {}
for key, m in meta["clips"].items():
    x0, y0, x1, y1 = m["box"]; out = np.ones((480, 832), bool); out[y0:y1, x0:x1] = False
    st = {}
    for arm in ("plain", "nphys"):
        g = read(gen / f"t276_real_{key[:2]}_{arm}_{key[3:]}.mp4").astype(np.float32).mean(-1)
        d = np.abs(np.diff(g, axis=0)).mean(0)          # mean frame-to-frame |diff| per pixel
        dev = np.abs(g - np.median(g, 0))
        st[arm] = {"tdiff_out": float(d[out].mean()), "frac_dev20_out": float((dev.max(0) > 20)[out].mean())}
    bg = 0.5 * ((cell[(key, "pn")] - cell[(key, "pp")]) + (cell[(key, "nn")] - cell[(key, "np")]))
    rows[key] = {**{f"{a}_{k}": v for a in st for k, v in st[a].items()}, "bg_effect": bg}
k = sorted(rows); bg = np.array([rows[i]["bg_effect"] for i in k])
dm = np.array([rows[i]["nphys_tdiff_out"] - rows[i]["plain_tdiff_out"] for i in k])
res = {"rows": rows, "mean_plain_tdiff_out": float(np.mean([rows[i]["plain_tdiff_out"] for i in k])),
       "mean_nphys_tdiff_out": float(np.mean([rows[i]["nphys_tdiff_out"] for i in k])),
       "n_nphys_less_motion": int((dm < 0).sum()), "pearson_bg_vs_dmotion": float(np.corrcoef(dm, bg)[0, 1]),
       "spearman_bg_vs_dmotion": float(np.corrcoef(np.argsort(np.argsort(dm)), np.argsort(np.argsort(bg)))[0, 1])}
Path(outp).write_text(json.dumps(res, indent=1))
print({x: res[x] for x in res if x != "rows"})
