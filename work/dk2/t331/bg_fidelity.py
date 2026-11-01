"""t331: background fidelity vs the input PNG (outside the per-scene union corridor mask).
Usage: python bg_fidelity.py <inputs_dir> <prox_dir> <gen_dir> <out.json>
Per clip: mean over frames 1..T-1 of background PSNR vs input, Laplacian-variance ratio vs input, luma mean shift, std ratio."""
import sys, json, numpy as np, cv2
sys.path.insert(0, __file__.rsplit("/", 1)[0])
inp, prox, gen, outp = sys.argv[1:5]
THR, DIL = 25, 21
def read(p):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return np.stack(fr)
def motion(v):
    g = v.astype(np.int16).mean(-1); m = (np.abs(g - g[0:1]).max(0) > THR).astype(np.uint8)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
def lap(f):
    return cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32), cv2.CV_32F)
res = {}
for sc in ["09", "12", "16", "17", "18", "19"]:
    I = cv2.imread(f"{inp}/f0_real_{sc}.png"); I = cv2.resize(I, (832, 480), interpolation=cv2.INTER_AREA) if I.shape[:2] != (480, 832) else I
    clips = {"proxy": read(f"{prox}/proxy_real_{sc}_nphys.mp4")}
    for a in ["plain", "nphys"]:
        for s in [1, 2, 3]: clips[f"{a}_s{s}"] = read(f"{gen}/t276_real_{sc}_{a}_s{s}.mp4")
    m = np.maximum.reduce([motion(v) for v in clips.values()])
    bg = cv2.dilate(m, np.ones((DIL, DIL), np.uint8)) == 0
    LI = lap(I)[bg]; gi = cv2.cvtColor(I, cv2.COLOR_BGR2GRAY).astype(np.float32)[bg]
    res[sc] = {"bg_frac": float(bg.mean())}
    for k, v in clips.items():
        ps, lr, sh, sr = [], [], [], []
        for t in range(1, len(v)):
            f = v[t]; d = (f.astype(np.float32) - I.astype(np.float32))[bg]
            ps.append(10 * np.log10(255 ** 2 / max((d ** 2).mean(), 1e-6)))
            lr.append(lap(f)[bg].var() / LI.var())
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)[bg]
            sh.append(g.mean() - gi.mean()); sr.append(g.std() / gi.std())
        res[sc][k] = dict(psnr=float(np.mean(ps)), lapvar_ratio=float(np.mean(lr)), luma_shift=float(np.mean(sh)), std_ratio=float(np.mean(sr)),
                          psnr_f1=float(ps[0]), psnr_last=float(ps[-1]))
json.dump(res, open(outp, "w"), indent=1)
for key in ["psnr", "lapvar_ratio", "luma_shift", "std_ratio", "psnr_last"]:
    row = {"proxy": np.mean([res[s]["proxy"][key] for s in res])}
    for a in ["plain", "nphys"]: row[a] = np.mean([res[s][f"{a}_s{x}"][key] for s in res for x in [1, 2, 3]])
    print(key, {k: round(float(v), 3) for k, v in row.items()})
print("bg_frac", {s: round(res[s]["bg_frac"], 2) for s in res})
