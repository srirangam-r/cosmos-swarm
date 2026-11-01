"""Post hoc diagnostic: evaluate zero crossings at retained container timestamps.
Does not change preregistered25Hz results, eligibility, or fitted periods.
"""
from pathlib import Path
import json,numpy as np
from reference import cross_cycles
p=Path(__file__).parent;d=json.loads((p/'output/results.json').read_text());out={}
for key,r in d.items():
 tr=json.loads((p/f'output/traces/real_{int(key):02}.json').read_text()); track=np.array(tr['tool_track']);keep=np.array(tr['container_keep_indices'])
 time=keep[93+track[:,0].astype(int)]/r['container_fps'];signal=track[:,2]
 corrected=cross_cycles(time,signal,time[0],time[-1]); ref=r['reference_crossing']['period_s']
 out[key]={'nominal_zc_ratio':r['ratio_zc'],'container_timestamp_zc_ratio':corrected['period_s']/ref,'container_timestamp_zc_period_s':corrected['period_s'],'nominal_window_elapsed_s':92/25,'container_window_elapsed_s':float((keep[185]-keep[93])/r['container_fps']),'n_distinct_prefix':r['n_distinct_prefix']}
values=lambda k:np.array([v[k] for v in out.values()]);summary={}
for k in ['nominal_zc_ratio','container_timestamp_zc_ratio','container_window_elapsed_s']:
 a=values(k);summary[k]={'mean':a.mean(),'se':a.std(ddof=1)/np.sqrt(len(a)),'min':a.min(),'max':a.max()}
eligible=[v for key,v in out.items() if d[key]['tool']['flag']=='ok']
summary_ok={}
for k in ['nominal_zc_ratio','container_timestamp_zc_ratio','container_window_elapsed_s']:
 a=np.array([v[k] for v in eligible]);summary_ok[k]={'mean':a.mean(),'se':a.std(ddof=1)/np.sqrt(len(a)),'min':a.min(),'max':a.max()}
summary['flag_ok']=summary_ok
(p/'timebase_sensitivity.json').write_text(json.dumps({'status':'post hoc timebase diagnostic only; primary results unchanged','records':out,'summary':summary},indent=2)+'\n');print(summary)
