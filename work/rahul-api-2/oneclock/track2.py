"""track2 (rahul-api-2): blur-tolerant single-ball tracker for oneclock. Change vs a per-pixel median background
(the ball moves, so it is not in the median unless it rests > half the clip), Gaussian-smoothed max-channel |diff| > thr,
component nearest the constant-velocity prediction, centroid weighted by |diff|. Seeded at a point at frame 0."""
import numpy as np, cv2


def track2(F, point, thr=25.0, jump=110, amin=40, amax=4000):
    """v2: change = min over two half-clip median backgrounds (B1 = first half, B2 = second half), which suppresses
    the 'ghost' a resting (or held) ball leaves in a whole-clip median. Before the first detection the tracker
    waits (no loss limit) for a blob within 30 px of the seed, so a held ball is picked up when it starts to move."""
    T = len(F); h = T // 2
    B1 = np.median(F[:h], 0).astype(np.float32); B2 = np.median(F[h:], 0).astype(np.float32)
    cy = np.full(T, np.nan); cx = np.full(T, np.nan); area = np.zeros(T)
    pos = np.array(point, float); vel = np.zeros(2); lost = 0; found = False
    for t in range(T):
        f = F[t].astype(np.float32)
        d = cv2.GaussianBlur(np.minimum(np.abs(f - B1).max(2), np.abs(f - B2).max(2)), (0, 0), 1.5)
        m = cv2.morphologyEx((d > thr).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, l, st, cen = cv2.connectedComponentsWithStats(m)
        pred = pos + vel; best, bd = None, (40 if not found else jump * (1 + lost))
        for i in range(1, n):
            if not (amin <= st[i, 4] <= amax): continue
            dd = np.hypot(*(cen[i] - pred))
            if dd < bd: best, bd = i, dd
        if best is None:
            if not found: continue
            lost += 1
            if lost > 4: break
            continue
        w = d * (l == best); ys, xs = np.nonzero(w)
        new = np.array([(xs * w[ys, xs]).sum() / w[ys, xs].sum(), (ys * w[ys, xs]).sum() / w[ys, xs].sum()])
        if found: vel = (new - pos) / (1 + lost)
        pos = new; lost = 0; found = True
        cx[t], cy[t], area[t] = pos[0], pos[1], st[best, 4]
    return cx, cy, area
