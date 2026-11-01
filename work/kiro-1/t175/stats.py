import json,numpy as np
pc={r['name']:r for r in json.load(open('per_clip.json'))}
pa=json.load(open('pend_angles.json'))
def ms(v): v=np.array(v,float); return f"{v.mean():+.3f} ± {v.std(ddof=1)/np.sqrt(len(v)):.3f} (n={len(v)})"
out={}
for sc in ('slope_wood','slope_plastic','pend_mid'):
    for b in ('base','n'):
        d=[pc[f'k175_{sc}_r_s{s}']['late_tail']-pc[f'k175_{sc}_{b}_s{s}']['late_tail'] for s in (4,5,6,7)]
        print(sc,f'late_tail R-{b}',ms(d)); out[f'{sc}_tail_R-{b}']=d
for b in ('base','n'):
    d=[pa[f'k175_pend_mid_r_s{s}']['amp_late']-pa[f'k175_pend_mid_{b}_s{s}']['amp_late'] for s in (4,5,6,7)]
    print(f'pend amp_late deg R-{b}',ms(d)); out[f'pend_ampL_R-{b}']=d
    d=[np.log(pa[f'k175_pend_mid_r_s{s}']['amp_late']/pa[f'k175_pend_mid_r_s{s}']['amp_early'])-np.log(pa[f'k175_pend_mid_{b}_s{s}']['amp_late']/pa[f'k175_pend_mid_{b}_s{s}']['amp_early']) for s in (4,5,6,7)]
    print(f'pend log(L/E) R-{b}',ms(d)); out[f'pend_logLE_R-{b}']=d
for a in ('base','r','n'):
    v=[pa[f'k175_pend_mid_{a}_s{s}']['amp_late'] for s in (4,5,6,7)]; e=[pa[f'k175_pend_mid_{a}_s{s}']['amp_early'] for s in (4,5,6,7)]
    print(a,'ampE',ms(e),'ampL',ms(v))
json.dump(out,open('contrasts.json','w'),indent=1)
