"""Run task277's predeclared time-series fixtures, not video validation."""
import json
import numpy as np
from crossing_readout import period, selftest

selftest()
t = np.arange(93) / 24
errors = []
for p in [1.186, 2.0162]:
    for a in [.06, .3]:
        for phase in [0, .2, .7, 1.3, 2.1, 3, 4.2, 5.5]:
            for offset in [-.4, 0, .8]:
                for decay in [0, .1]:
                    r = period(t, offset + a*np.exp(-decay*t)*np.sin(2*np.pi*t/p+phase))
                    assert r['reason'] == 'measurable_unvalidated'
                    errors.append(abs(r['period_s']-p))
assert len(errors) == 192 and max(errors) < .004
for phase in [.6*t+.3*t*t, t+.125*t*t]:
    r = period(t, .2*np.sin(2*np.pi*phase))
    assert r['reason'] == 'unstable_intervals'
    assert 'period_s' not in r and 'candidate_period_s' in r
print(json.dumps({'extra_oscillators':len(errors), 'max_error_s':max(errors),
                  'unstable_chirps_rejected':2, 'video_validated':False}))
