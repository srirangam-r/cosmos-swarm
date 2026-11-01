"""Sensitivity of one existing seeded track to fit window; not an independent tracker."""
import json, sys
import numpy as np
sys.path.insert(0, 'tools/realball')
import firstfall
clip='work/raj-2/task9_duration/first_clip/raj2_dur_ball1_nf61_s1.mp4'
f=firstfall.trk.load(clip)
r,(_, y, _)=firstfall.measure(f, 24, ppm=539.8, point=(282,117), tmax=16)
windows=[(2,10),(3,10),(4,10),(5,10),(2,9),(3,9),(2,11)]
out={'original_result':{k:r[k] for k in ['g','g_ci95','fit_frames','flag','d_growth']},'fps':24,'pixels_per_metre':539.8,'tracked_y_px':[float(x) for x in y[:13]],'g_by_inclusive_frame_window_m_s2':{f'{a}-{b}':float(2*np.polyfit(np.arange(a,b+1)/24, y[a:b+1]/539.8,2)[0]) for a,b in windows}}
print(json.dumps(out,indent=2))
