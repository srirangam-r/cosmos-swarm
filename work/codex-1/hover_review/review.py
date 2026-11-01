#!/usr/bin/env python3
"""Independent position-level simulation; no video tracker, no referee data."""
import json
import numpy as np
from scipy.optimize import least_squares

FPS = 24
G = [0.45, 2.0, 9.81]
HOVERS = [0.0, 0.5, 1.0]
N = 200
SCALE = 22 / 0.06
rng = np.random.default_rng(81723)
rows = []
for g in G:
    for hover in HOVERS:
        # Last pre-impact frame, with a fixed 0.30 m fall; no impact frame.
        t = np.arange(int(np.ceil((hover + np.sqrt(0.6/g))*FPS))) / FPS
        ideal = 0.5*g*np.maximum(t-hover, 0)**2
        ratios = []
        for _ in range(N):
            y = ideal + rng.normal(0, 1/SCALE, len(t))
            design = np.column_stack((np.ones(len(t)), .5*t*t))
            anchored = np.linalg.lstsq(design, y, rcond=None)[0][1]
            def residual(p):
                return p[0] + .5*p[1]*np.maximum(t-p[2], 0)**2 - y
            # Independent multistart fits avoid a local minimum at the boundary.
            fits = [least_squares(residual, [y[0], g, start], bounds=([-np.inf, 0, 0], [np.inf, 30, t[-2]])) for start in (0, hover, min(hover+.1, t[-2]))]
            fit = min(fits, key=lambda z: np.sum(z.fun**2))
            ratios.append([anchored/g, fit.x[1]/g, fit.x[2]])
        arr = np.array(ratios)
        rows.append(dict(g=g, hover_s=hover, frames=len(t), anchored_ratio_mean=float(arr[:,0].mean()), anchored_ratio_sd=float(arr[:,0].std(ddof=1)), hinge_ratio_mean=float(arr[:,1].mean()), hinge_ratio_sd=float(arr[:,1].std(ddof=1)), onset_mean_s=float(arr[:,2].mean()), n=N))
print(json.dumps(dict(method='Position-level Gaussian centroid noise, 1 px SD; pre-impact observations; 24 fps; 0.30 m drop; scale 22px/0.06m; seed 81723. SD is across independent noisy trajectories.', rows=rows), indent=2))
