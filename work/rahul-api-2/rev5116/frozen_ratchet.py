"""Known-answer check #2: kiro-1 t216 tracker (unchanged) on FROZEN clips of the real task-141 input frames.
Each clip repeats one input frame 189 times (true growth = 1.000, nothing moves). Variant 'noise': + per-frame
Gaussian pixel noise sigma 3 (codec-like). Seeding exactly as analyze_ball_size.py: detect_ball_at_position(f0, w//2, h//3, 200)."""
import sys, types, json
import numpy as np, cv2
sys.modules.setdefault('matplotlib', types.ModuleType('matplotlib')); sys.modules['matplotlib.pyplot'] = types.ModuleType('matplotlib.pyplot')
sys.path.insert(0, sys.argv[1]); import track_ball as tb
rng = np.random.default_rng(1); out = {}
for img in sys.argv[2:]:
    f0 = cv2.imread(img); H, W = f0.shape[:2]
    for var in ('frozen', 'noise'):
        fn = f"{img.split('/')[-1][:-4]}_{var}.mp4"
        vw = cv2.VideoWriter(fn, cv2.VideoWriter_fourcc(*'mp4v'), 24, (W, H))
        for i in range(189):
            fr = f0 if var == 'frozen' else np.clip(f0.astype(np.float32) + rng.normal(0, 3, f0.shape), 0, 255).astype(np.uint8)
            vw.write(fr)
        vw.release()
        cap = cv2.VideoCapture(fn); ok, fr = cap.read(); cap.release()
        cx, cy, d = tb.detect_ball_at_position(fr, W // 2, H // 3, search_radius=200)
        res = tb.track_ball_template(fn, (cx, cy, d))
        dd = np.array([r['diameter'] for r in res])
        out[fn] = dict(seed_xy=[float(cx), float(cy)], true_growth=1.0, d_f0=float(dd[0]), d_end=float(dd[-1]),
                       growth=float(dd[-1] / dd[0]), d_at=[float(dd[k]) for k in (0, 5, 10, 20, 40, 80, 120, 188)],
                       n_decreases=int(np.sum(np.diff(dd) < 0)), n_increases=int(np.sum(np.diff(dd) > 0)))
        print(fn, json.dumps(out[fn]))
json.dump(out, open('frozen_ratchet_result.json', 'w'), indent=1)
