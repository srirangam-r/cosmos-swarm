import os
import sys
import json
import numpy as np
import cv2

def generate_set(seed, out_dir, truth_file):
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(seed)
    W, H, FPS, N = 832, 480, 24, 93
    floor = 400
    truth = {}

    def render(path, xs, ys, r, bg, noise, shadow):
        vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W, H))
        for i in range(N):
            f = bg.copy()
            if shadow:
                cv2.ellipse(f, (int(xs[i]), floor + int(r[i]) + 4), (int(r[i] * 1.2), 4), 0, 0, 360, (60, 60, 60), -1)
            cv2.circle(f, (int(round(xs[i])), int(round(ys[i]))), int(round(r[i])), (40, 60, 200), -1, cv2.LINE_AA)
            f = np.clip(f.astype(np.float32) + rng.normal(0, noise, f.shape), 0, 255).astype(np.uint8)
            vw.write(f)
        vw.release()

    for k in range(30):
        e = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.97][k % 8]
        g = 9.81
        mpp = float(rng.uniform(0.0035, 0.0065))
        h0 = float(rng.uniform(1.0, 1.6))
        ga = g / mpp
        hold = int(rng.choice([0, 0, 6]))
        drift = bool((k // 8) % 2 == 1)
        sub = 50
        cur = floor - h0 / mpp
        vv = 0.0
        tt = -hold / FPS
        imp = []
        ys = []
        for i in range(N):
            for s in range(sub):
                tt += 1.0 / (FPS * sub)
                if tt < 0:
                    continue
                vv += ga * (1.0 / (FPS * sub))
                cur += vv * (1.0 / (FPS * sub))
                if cur >= floor and vv > 0:
                    cur = floor - (cur - floor)
                    vv = -vv * e
                    imp.append(float(tt))
                    if abs(vv) < 20:
                        vv = 0.0
            ys.append(float(cur))
        ys = np.array(ys)
        r = np.full(N, 0.05 / mpp)
        if drift:
            r = r * np.linspace(1.0, 1.25, N)
        xs = 300.0 + rng.uniform(-30, 30) + np.linspace(0, rng.uniform(-40, 40), N)
        ys_c = ys - r
        bg = np.full((H, W, 3), rng.integers(150, 210), np.uint8)
        cv2.line(bg, (0, floor + int(r[0]) + 1), (W, floor + int(r[0]) + 1), (90, 90, 90), 2)
        p = os.path.join(out_dir, f'c{k:02d}.mp4')
        render(p, xs, ys_c, r, bg, rng.uniform(1, 4), k % 3 == 0)
        imp = np.array(imp)
        T = np.diff(imp) if len(imp) > 1 else np.array([])
        truth[f'c{k:02d}'] = dict(
            e=e, g=g, mpp=mpp, diam=0.10, hold=hold, drift=drift,
            n_imp=len(imp), T=T.tolist(), imp=imp.tolist()
        )
    with open(truth_file, 'w') as f:
        json.dump(truth, f, indent=1)
    print(f"Generated {len(truth)} clips for seed {seed} into {out_dir}")

if __name__ == '__main__':
    base_dir = '/home/sha/swarm-work/rahul-5-agy/task237_bounce_review'
    generate_set(777, os.path.join(base_dir, 'clips_777'), os.path.join(base_dir, 'truth_777.json'))
    generate_set(888, os.path.join(base_dir, 'clips_888'), os.path.join(base_dir, 'truth_888.json'))
