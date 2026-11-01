"""task 221 (rahul): sensitivity of the pendulum amplitude correction (#205/#213) to projection and off-vertical centres.
Input: published turning-point series (amp_results.json t205 + amp_t193.json t213). No new clips."""
import json, numpy as np
from scipy.special import ellipk
B='../../rahul-api-2/'
per={}
for f in ['t205/amp_results.json','t213/amp_t193.json']:
    for k,v in json.load(open(B+f))['per_clip'].items():
        per[k.replace('rpr_','k191_')]=v   # t193 s21-25 duplicate k191; s26-30 only in t193
def F(A):
    A=np.asarray(A,float); A=np.minimum(A,179.0)
    return 2/np.pi*ellipk(np.sin(np.radians(A)/2)**2)
def amp(tt,mode,k=1.0,off=0.0):
    th=np.array(tt,float)
    th=np.degrees(np.arctan(np.tan(np.radians(th))/k))    # projection: tan(img)=k tan(true)
    if mode=='hc':   # half peak-to-peak of consecutive turning points (centre-free)
        a=np.abs(np.diff(th))/2; return np.median(a) if len(a)>=2 else np.nan
    if mode=='side': # |theta| about image vertical shifted by off (pivot/centre offset, deg)
        return np.median(np.abs(th-off))
    if mode=='max':  # largest one-sided excursion
        return np.max(np.abs(th-off))
real=per['real_pend10_f93']
# FIT set: R2>=0.8, pend10, >=2 pairs, unique, exclude first-sample pseudo turning pts (value |th|<15 first)
names=[n for n,v in per.items() if not n.startswith('real') and v.get('kiro_T') and v.get('my_r2',0)>=0.8 and v['input']=='pend10' and np.isfinite(v.get('A_hc',np.nan))]
print(len(names),'clips')
def run(mode_n,mode_r,kn,kr,off=0.0):
    out=[]
    Ar=amp(real['turn_theta'],mode_r,kr,off)
    for n in names:
        v=per[n]; An=amp(v['turn_theta'],mode_n,kn,off)
        R=(v['kiro_T']/F(An))/(real['kiro_T']/F(Ar)); out.append(R)
    out=np.array(out); return np.exp(np.log(out).mean()), out.min(), out.max()
raw=np.array([per[n]['kiro_T']/real['kiro_T'] for n in names]); print('raw geo',np.exp(np.log(raw).mean()), 'n',len(raw))
print('baseline hc k=1 (repro):',run('hc','hc',1,1))
res={}
print('\n[A] same-camera projection k=cos(alpha), applied to BOTH (hc):')
for k in [1,.9,.8,.7,.6,.5]:
    r=run('hc','hc',k,k); print(f' k={k}: geo {r[0]:.3f} range[{r[1]:.2f},{r[2]:.2f}]'); res[f'shared_k{k}']=r
print('[B] projection differs: Nano k_n, real k=1 (generated geometry unvalidated):')
for k in [.9,.8,.7,.6,.5]:
    r=run('hc','hc',k,1); print(f' k_n={k}: geo {r[0]:.3f}'); res[f'nano_only_k{k}']=r
print('[C] off-vertical centre/pivot offset (deg) about vertical, mode side (|theta-off|), both real and Nano:')
for off in [-10,-5,0,5,10,15]:
    r=run('side','side',1,1,off); print(f' off={off}: geo {r[0]:.3f}'); res[f'side_off{off}']=r
print('[D] largest-excursion (max) as amplitude, both:')
for off in [0,5,10]:
    r=run('max','max',1,1,off); print(f' off={off}: geo {r[0]:.3f}'); res[f'max_off{off}']=r
print('[E] Nano uses max-excursion, real uses hc (most generous):')
r=run('max','hc',1,1); print(f' geo {r[0]:.3f} range [{r[1]:.2f},{r[2]:.2f}]'); res['gen_max_vs_hc']=r
print('[F] combined generous: Nano max & k_n=0.7, real hc k=1:')
r=run('max','hc',.7,1); print(f' geo {r[0]:.3f}'); res['gen_max_k.7']=r
# Formal: amplitude needed (period ratio R_raw -> F ratio) per clip
print('\nper-clip: raw ratio, A_n(hc,k=1), F-needed amplitude if real fixed')
for n in names:
    v=per[n]; Rr=v['kiro_T']/real['kiro_T']; Fn_need=Rr*F(amp(real['turn_theta'],'hc'))
    from scipy.optimize import brentq
    try: Aneed=brentq(lambda a:F(a)-Fn_need,1,178.9)
    except Exception: Aneed=np.nan
    print(f' {n:28s} R_raw {Rr:.2f} A_hc {v["A_hc"]:.0f} A_needed {Aneed:.0f}')
json.dump({k:list(map(float,v)) for k,v in res.items()},open('sens_results.json','w'),indent=1)
