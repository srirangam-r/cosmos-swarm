"""Known-answer check of kiro-1 t216 track_ball.track_ball_template (used UNCHANGED, imported from the repo).
Synthetic 832x480, 189-frame clips of a CONSTANT-diameter dark ball (true growth = 1.000) on a textured background.
Cases: static ball; falling+bouncing ball; slow horizontal roll. Reports tracker d_end/d_f0 (what #5116 calls growth)."""
import sys, types, json
import numpy as np, cv2
sys.modules.setdefault('matplotlib', types.ModuleType('matplotlib'))
mp = types.ModuleType('matplotlib.pyplot'); sys.modules['matplotlib.pyplot'] = mp
sys.path.insert(0, sys.argv[1])
import track_ball as tb

W, H, N, D = 832, 480, 189, 46
rng = np.random.default_rng(0)
bg = cv2.GaussianBlur(rng.normal(150, 30, (H, W)).astype(np.float32), (0, 0), 3)
bg = np.clip(bg + np.linspace(-20, 20, W)[None, :] + 40 * (np.arange(H)[:, None] > 400), 0, 255).astype(np.uint8)

def path(case, i):
    if case == 'static': return 300, 150
    if case == 'roll': return 200 + 1.5 * i, 380
    # fall from y=100 to floor y=400 with bounces (e=0.6), x drifts slowly
    g = 0.25; y = 100.0; v = 0.0
    for _ in range(i):
        v += g; y += v
        if y > 400: y = 400 - (y - 400); v = -0.6 * v
    return 300 + 0.5 * i, y

out = {}
for case in ('static', 'fall_bounce', 'roll'):
    fn = f'synth_{case}.mp4'
    vw = cv2.VideoWriter(fn, cv2.VideoWriter_fourcc(*'mp4v'), 24, (W, H))
    for i in range(N):
        f = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)
        x, y = path(case, i)
        cv2.circle(f, (int(round(x)), int(round(y))), D // 2, (40, 40, 40), -1, lineType=cv2.LINE_AA)
        vw.write(f)
    vw.release()
    x0, y0 = path(case, 0)
    # seed exactly as kiro-1's main(): f0 position, diameter from detect_ball_at_position
    cap = cv2.VideoCapture(fn); ok, fr = cap.read(); cap.release()
    _, _, d0 = tb.detect_ball_at_position(fr, x0, y0, 50)
    res = tb.track_ball_template(fn, (x0, y0, d0))
    d = np.array([r['diameter'] for r in res])
    nondecr = int(np.sum(np.diff(d) < 0))
    out[case] = dict(true_diameter=D, true_growth=1.0, d_f0=float(d[0]), d_end=float(d[-1]), growth=float(d[-1] / d[0]),
                     d_at=[float(d[k]) for k in (0, 10, 25, 50, 100, 150, 188)], n_frames_diameter_decreased=nondecr)
    print(case, json.dumps(out[case]))
json.dump(out, open('synth_ratchet_result.json', 'w'), indent=1)
