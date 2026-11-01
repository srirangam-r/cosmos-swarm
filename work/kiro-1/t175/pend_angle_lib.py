"""Same measurement as pend_angle.py (unchanged constants), as importable functions on frame lists."""
import cv2, numpy as np
PX, PY = 318, 120
yy, xx = np.mgrid[0:480, 0:832]; dx = xx - PX; dy = yy - PY; rr = np.hypot(dx, dy)
ann = (rr > 35) & (rr < 95) & (dy > 10)
def angles_frames(frames):
    out = []
    for f in frames:
        h = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        m = ann & (h[..., 0] >= 5) & (h[..., 0] <= 30) & (h[..., 1] > 50) & (h[..., 2] > 90)
        out.append(float(np.degrees(np.arctan2(dx[m].mean(), dy[m].mean()))) if m.sum() >= 15 else None)
    return out
def metrics(a):
    def amp(lo, hi):
        v = [x for x in a[lo:hi] if x is not None]; miss = (hi - lo) - len(v)
        return (float((np.percentile(v, 95) - np.percentile(v, 5)) / 2) if len(v) > 5 else None), miss
    ae, me = amp(1, 31); al, ml = amp(62, 93)
    v = [abs(x) for x in a if x is not None]
    return dict(angle0=a[0], amp_early=ae, amp_late=al, miss_early=me, miss_late=ml, max_abs=max(v) if v else None,
                miss_all=sum(x is None for x in a), trace=[None if x is None else round(x, 1) for x in a])
