#!/usr/bin/env python3
"""Arithmetic + independent decoder checks, not planted physics validation."""
import json,subprocess,sys
from pathlib import Path
import numpy as np
from scipy.stats import t
from analyze import contrast

v=contrast([(i,s,2.) for i in ['ball1','ball2'] for s in range(4)])
assert v['mean']==2 and v['se']==v['seed_cluster_se']==0
v=contrast([('a',i,float(i)) for i in range(4)])
assert abs(v['mean']-1.5)<1e-12
assert abs(v['se']-np.sqrt(5/12))<1e-12
assert abs(t.ppf(.9,7)-1.4149239276488585)<1e-10
root=Path(sys.argv[1]);data=json.loads((Path(__file__).parent/'res/metrics.json').read_text())
for name in ['t170_L10_ball2_s11','t170_RL10_ball2_s11']:
    raw=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(root/(name+'.mp4')),'-f','rawvideo','-pix_fmt','rgb24','-threads','1','pipe:1'])
    a=np.frombuffer(raw,np.uint8).reshape(93,480,832,3)[:,130:360,220:360].astype(np.float64)
    g=a@np.array([.299,.587,.114]);d=np.abs(np.diff(g,axis=0)).mean(axis=(1,2))
    assert np.max(np.abs(d-data[name]['continuous_trace']))<1e-12
    assert abs(d[-20:].mean()-data[name]['continuous_last20'])<1e-12
print('PASS: constant contrast, known SE/t quantile, and two independent ffmpeg decodes (all 92 trace values each)')
