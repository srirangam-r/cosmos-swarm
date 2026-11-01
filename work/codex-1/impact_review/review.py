#!/usr/bin/env python3
"""Independent point-trajectory check; no image tracker or planted data."""
import json
import numpy as np

rng = np.random.default_rng(10673)
n = 10000
fps = 24.0
bias_with, bias_without = [], []
for _ in range(n):
    g = rng.uniform(3, 13)
    h = rng.uniform(0.8, 1.6)
    # Clip starts at release; first floor-clamped sample is retained in one fit.
    j = int(np.ceil(np.sqrt(2*h/g)*fps))
    t = np.arange(j + 1) / fps
    y = np.minimum(0.5*g*t*t, h)
    def fit(tt, yy):
        # Intercept and curvature are both estimated, initial velocity fixed at zero.
        return 2 * np.linalg.lstsq(np.column_stack((np.ones(len(tt)), tt*tt)), yy, rcond=None)[0][1]
    bias_with.append((fit(t, y)/g - 1)*100)
    bias_without.append((fit(t[:-1], y[:-1])/g - 1)*100)

def summary(x):
    a=np.asarray(x)
    return {'mean_percent':float(a.mean()),'sd_percent':float(a.std(ddof=1)),
            'se_percent':float(a.std(ddof=1)/np.sqrt(len(a))),
            'p05_percent':float(np.quantile(a,.05)),'p95_percent':float(np.quantile(a,.95))}
print(json.dumps({'seed':10673,'n':n,'fps':fps,'g_range_m_s2':[3,13],
                  'height_range_m':[0.8,1.6],
                  'impact_included':summary(bias_with),
                  'impact_excluded':summary(bias_without)},indent=2))
