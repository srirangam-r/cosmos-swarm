"""rog1 independent time-to-quiet proxy (no ball boxes, no BG ratio).
Per frame: grey, 2x down, Gaussian blur 5; changed px = |f_t - f_{t-1}| > D.
Excluded: nothing (whole frame). Quiet time = start of the first run of frames
with changed px <= N that lasts to the end of the clip ("stays quiet"), in s from f0.
Also reports 'first 0.5 s quiet run' (looser). Censored -> None.
"""
import cv2, numpy as np, json, sys
def frames(p, start=0, n=None):
    c = cv2.VideoCapture(p); fps = c.get(5); F = []; i = 0
    while True:
        r, f = c.read()
        if not r: break
        if i >= start and (n is None or len(F) < n):
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            g = cv2.resize(g, (416, 240), interpolation=cv2.INTER_AREA)
            F.append(cv2.GaussianBlur(g, (5, 5), 0).astype(np.int16))
        i += 1
    return F, fps
def series(F, D):
    return [int((np.abs(F[t] - F[t-1]) > D).sum()) for t in range(1, len(F))]
def quiet(s, N, fps, run):
    q = [x <= N for x in s]
    # stays quiet to end
    stay = None
    for t in range(len(q)):
        if all(q[t:]) and len(q) - t >= run: stay = (t + 1) / fps; break
    first = None
    for t in range(len(q) - run + 1):
        if all(q[t:t+run]): first = (t + 1) / fps; break
    return stay, first
if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1])); out = {}
    for name, (path, start, n) in cfg.items():
        F, fps = frames(path, start, n)
        if 'r60_' in name: fps = 24.0
        res = {'fps': fps, 'nframes': len(F), 'dur_s': (len(F)-1)/fps}
        for D in (10, 15, 25):
            s = series(F, D); res[f'D{D}_series'] = s
            for N in (20, 50, 100):
                res[f'D{D}_N{N}'] = quiet(s, N, fps, int(round(0.5*fps)))
        out[name] = res
    json.dump(out, open(sys.argv[2], 'w'))
