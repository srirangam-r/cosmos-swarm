"""Synthetic known-rho clips for oneclock: dark ball (d=24 px) over a textured light background, hold H frames,
fall from rest with curvature a_fall [px/frame^2] onto a floor, bounce with restitution e, flights with curvature
rho*a_fall. Sub-frame physics, area-sampled ball, Gaussian pixel noise, mp4v. Writes synth/<name>.mp4 + truth json."""
import numpy as np, cv2, json, os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else 'synth'
os.makedirs(OUT, exist_ok=True)
H, W, R, X0, Y0, FLOOR = 480, 832, 12, 280, 116, 356


def traj(a_f, rho, e, hold, T=93, sub=20):
    ys = []; y = Y0; v = 0.0; a = a_f; dt = 1.0 / sub; t = 0.0
    for f in range(T):
        if f < hold: ys.append(Y0); continue
        acc = []
        for _ in range(sub):
            v += a * dt; y += v * dt
            if y > FLOOR - R and v > 0:
                y = FLOOR - R; v = -e * v; a = rho * a_f
                if abs(v) < 0.3: v = 0.0; a = 0.0
            acc.append(y)
        ys.append(float(np.mean(acc[-4:])))                            # short exposure
    return ys


def render(ys, seed):
    rng = np.random.default_rng(seed)
    bg = cv2.GaussianBlur(rng.uniform(140, 220, (H, W, 3)).astype(np.float32), (0, 0), 4)
    bg[FLOOR:] = (60, 110, 160)
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    fr = []
    for y in ys:
        d = np.sqrt((xx - X0) ** 2 + (yy - y) ** 2); m = np.clip(R + 0.5 - d, 0, 1)[..., None]
        f = bg * (1 - m) + 25 * m + rng.normal(0, 2, (H, W, 3))
        fr.append(np.clip(f, 0, 255).astype(np.uint8))
    return fr


cases = []
for i, (a_f, rho, e, hold) in enumerate([(0.5, 1.0, 0.7, 4), (0.5, 2.0, 0.7, 4), (1.0, 1.0, 0.6, 0), (0.3, 1.0, 0.8, 10),
                                          (0.3, 2.0, 0.9, 0), (1.0, 0.5, 0.8, 2)]):
    name = f'syn{i}_af{a_f}_rho{rho}_e{e}'
    ys = traj(a_f, rho, e, hold); fr = render(ys, i)
    vw = cv2.VideoWriter(f'{OUT}/{name}.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 24, (W, H))
    for f in fr: vw.write(f)
    vw.release(); cases.append(dict(name=name, a_fall=a_f, rho=rho, e=e, hold=hold))
json.dump(cases, open(f'{OUT}/truth.json', 'w'), indent=1)
print(cases)
