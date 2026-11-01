"""Independent template/crossing readout for task277. UNVALIDATED on video.
python crossing_readout.py --selftest
python crossing_readout.py clip.mp4 --pivot 320 120 --bob 310 260 --out clip.crossing.json
Requires numpy, opencv-python. Freeze coordinates/radius on input frame BEFORE outputs.
No use of proxy period or arm label by the measurement. No reinitialization after loss.
Sampling scale and overlapping interval MAD are descriptive, NOT confidence intervals.
"""
import argparse, json, math
from pathlib import Path
import numpy as np
import cv2

def period(t, angle, min_amp=.01):
    t, angle = np.asarray(t, dtype=float), np.asarray(angle, dtype=float)
    if t.ndim != 1 or angle.shape != t.shape or len(t) < 8 or not np.isfinite(min_amp) or min_amp <= 0:
        raise ValueError("shape/amplitude")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(angle)) or np.any(np.diff(t) <= 0):
        raise ValueError("nonfinite/unordered")
    lo, hi = np.quantile(angle, [.05, .95])
    amp, center = float((hi-lo)/2), float((hi+lo)/2)
    out = dict(amplitude_rad=amp, center_rad=center, crossings=[], intervals_s=[], validated=False)
    if amp < min_amp:
        return dict(out, reason="low_amplitude")
    y, h, state, pending = angle-center, .2*amp, 0, None
    for i, v in enumerate(y):
        if state == 0:
            if v <= -h: state = -1
            elif v >= h: state = 1
            continue
        if i and state == -1 and y[i-1] < 0 <= v:
            pending = float(t[i-1]+(t[i]-t[i-1])*(-y[i-1])/(v-y[i-1]))
        if i and state == 1 and y[i-1] > 0 >= v:
            pending = float(t[i-1]+(t[i]-t[i-1])*y[i-1]/(y[i-1]-v))
        if (state == -1 and v >= h) or (state == 1 and v <= -h):
            if pending is not None: out["crossings"].append(dict(t=pending, direction=-state))
            state, pending = -state, None
        elif (state == -1 and v <= -h) or (state == 1 and v >= h):
            pending = None
    c = out["crossings"]
    out["intervals_s"] = [c[i]["t"]-c[i-2]["t"] for i in range(2,len(c)) if c[i]["direction"] == c[i-2]["direction"]]
    a = out["intervals_s"]
    if not a: return dict(out, reason="insufficient_complete_cycles")
    p = float(np.median(a))
    stats = dict(interval_mad_s=float(np.median(np.abs(np.array(a)-p))),
                 sampling_scale_s=float(2*np.max(np.diff(t))),
                 intervals_overlap=True)
    if (max(a)-min(a))/p > .25:
        return dict(out, **stats, candidate_period_s=p,
                    reason="unstable_intervals")
    return dict(out, **stats, period_s=p, reason="measurable_unvalidated")

def measure(path, pivot, bob, radius=10, search=64, min_corr=.55, min_margin=.03):
    cap = cv2.VideoCapture(str(path))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok: break
        frames.append(frame)
    cap.release()
    if len(frames) < 8 or not math.isfinite(fps) or fps <= 0: raise ValueError("video/fps")
    gray = [cv2.cvtColor(f,cv2.COLOR_BGR2GRAY) for f in frames]
    means = np.array([g.mean() for g in gray])
    flicker = float(means.std()/means.mean()) if means.mean() > 0 else None
    x,y = map(float,bob); x,y = int(round(x)),int(round(y))
    H,W = gray[0].shape
    if not (radius <= x < W-radius and radius <= y < H-radius): raise ValueError("bob patch outside image")
    template = gray[0][y-radius:y+radius+1,x-radius:x+radius+1].copy()
    if template.std() < 3: raise ValueError("unidentifiable template")
    centers, quality = [[float(x),float(y)]], []
    for i,g in enumerate(gray[1:],1):
        cx,cy = centers[-1]
        x0,y0 = max(0,int(round(cx))-search-radius),max(0,int(round(cy))-search-radius)
        x1,y1 = min(W,int(round(cx))+search+radius+1),min(H,int(round(cy))+search+radius+1)
        roi = g[y0:y1,x0:x1]
        if roi.shape[0] < len(template) or roi.shape[1] < template.shape[1]: break
        scores = cv2.matchTemplate(roi,template,cv2.TM_CCOEFF_NORMED)
        scores = np.nan_to_num(scores,nan=-1.,posinf=-1.,neginf=-1.)
        _,best,_,(u,v) = cv2.minMaxLoc(scores)
        competitor = scores.copy()
        yy,xx = np.ogrid[:len(scores),:scores.shape[1]]
        competitor[(xx-u)**2+(yy-v)**2 <= max(2,radius//2)**2] = -1
        margin = float(best-competitor.max())
        quality.append(dict(frame=i,corr=float(best),margin=margin))
        if best < min_corr or margin < min_margin: break
        centers.append([float(x0+u+radius),float(y0+v+radius)])
    out = dict(source=str(path),fps=fps,frames=len(frames),tracked_frames=len(centers),
               pivot=list(pivot),bob=list(bob),radius=radius,search=search,min_corr=min_corr,
               min_margin=min_margin,flicker=flicker,centers=centers,quality=quality,validated=False)
    if len(centers) != len(frames): return dict(out,reason="track_incomplete")
    xy = np.asarray(centers); dx,dy = xy[:,0]-pivot[0],xy[:,1]-pivot[1]
    angle = np.unwrap(np.arctan2(dx,dy)); rr = np.hypot(dx,dy)
    out["radius_p05_p95_over_median"] = float(np.diff(np.quantile(rr,[.05,.95]))[0]/np.median(rr)) if np.median(rr)>0 else None
    out["angle_rad"] = angle.tolist()
    out["crossing"] = period(np.arange(len(xy))/fps,angle)
    return out

def selftest():
    n, worst = 0, 0.
    t = np.arange(93)/24
    for p in [.6,.9,1.186,1.5,2.]:
      for a in [.06,.3]:
       for phase in [0,.2,.7,1.3,2.1,3,4.2,5.5]:
        for off in [-.4,0,.8]:
         for decay in [0,.1]:
          y = off+a*np.exp(-decay*t)*np.sin(2*np.pi*t/p+phase)
          r,m,s = period(t,y),period(t,-y),period(t,y+7)
          assert "period_s" in r and abs(r["period_s"]-p) < .004
          assert abs(r["period_s"]-m["period_s"]) < 1e-12
          assert abs(r["period_s"]-s["period_s"]) < 1e-12
          worst=max(worst,abs(r["period_s"]-p)); n+=1
    for y in [np.ones(93),t,np.full(93,.001)]: assert "period_s" not in period(t,y)
    print(json.dumps(dict(cases=n,max_error_s=worst,video_validated=False)))

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("video",nargs="?")
    ap.add_argument("--pivot",nargs=2,type=float); ap.add_argument("--bob",nargs=2,type=float)
    ap.add_argument("--radius",type=int,default=10); ap.add_argument("--search",type=int,default=64)
    ap.add_argument("--out"); ap.add_argument("--selftest",action="store_true"); ar=ap.parse_args()
    if ar.selftest: selftest()
    else:
        if not ar.video or ar.pivot is None or ar.bob is None or not ar.out: ap.error("video,pivot,bob,out required")
        if ar.radius<2 or ar.search<1: ap.error("radius>=2,search>=1")
        Path(ar.out).write_text(json.dumps(measure(ar.video,ar.pivot,ar.bob,ar.radius,ar.search),indent=2,allow_nan=False)+"\n")


