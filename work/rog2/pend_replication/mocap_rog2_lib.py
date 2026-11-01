import numpy as np
def periods(d):
    """Same method as mocap_rog2.py: sphere-fit pivot, swing angle, refined turning points; returns (extremum times, full periods)."""
    fps = d['FPS']; P = np.c_[d['ball']['x'], d['ball']['y'], d['ball']['z']] / 1000.0
    ok = np.isfinite(P).all(1); t = np.arange(len(P)) / fps; P, t = P[ok], t[ok]
    sp = np.linalg.norm(np.diff(P, axis=0), axis=1) * fps; rel = int(np.argmax(sp > 0.05))
    Ps = P[rel:]; A = np.c_[2 * Ps, np.ones(len(Ps))]; c, *_ = np.linalg.lstsq(A, (Ps**2).sum(1), rcond=None)
    v = Ps - c[:3]; _, _, Vt = np.linalg.svd(v - v.mean(0)); n = Vt[2]
    down = v.mean(0) - (v.mean(0) @ n) * n; down /= np.linalg.norm(down); side = np.cross(n, down)
    th = np.arctan2(v @ side, v @ down); ts = t[rel:]; dt = ts[1] - ts[0]
    ex = []
    for i in range(1, len(th) - 1):
        if (th[i] > th[i-1] and th[i] >= th[i+1]) or (th[i] < th[i-1] and th[i] <= th[i+1]):
            y0, y1, y2 = th[i-1], th[i], th[i+1]; den = y0 - 2*y1 + y2; dx = 0.5*(y0-y2)/den if den else 0.0
            if abs(y1) > 0.02: ex.append((ts[i] + dx*dt, y1))
    ex2 = [ex[0]]
    for e in ex[1:]:
        if np.sign(e[1]) != np.sign(ex2[-1][1]): ex2.append(e)
        elif abs(e[1]) > abs(ex2[-1][1]): ex2[-1] = e
    te = np.array([e[0] for e in ex2]); te = np.r_[ts[0], te]  # release counts as first turning point
    return te, te[2:] - te[:-2]
