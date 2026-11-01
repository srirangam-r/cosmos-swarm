"""Per-side peak angle and zero-crossing period from saved rod-angle traces (pend_angles.json: Nano, 24 fps; pend_real_check.json: real, 25 fps)."""
import json,numpy as np
def an(tr,fps):
    a=np.array([np.nan if x is None else x for x in tr]); t=np.arange(len(a))/fps
    ok=~np.isnan(a); a=np.interp(t,t[ok],a[ok]); s=np.sign(a); i=np.where(s[:-1]!=s[1:])[0]
    tc=t[i]-a[i]*(t[i+1]-t[i])/(a[i+1]-a[i])
    return dict(T=float(2*np.median(np.diff(tc))) if len(tc)>2 else None,n_cross=int(len(tc)),pos_peak=float(a.max()),neg_peak=float(-a.min()))
out=dict(real=an(json.load(open('pend_real_check.json'))['real_tool']['trace'],25.0),
         nano={k:an(v['trace'],24.0) for k,v in sorted(json.load(open('pend_angles.json')).items())})
json.dump(out,open('pend_sides.json','w'),indent=1); print(json.dumps(out,indent=1))
