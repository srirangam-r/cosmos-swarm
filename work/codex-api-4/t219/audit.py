"""Independent finite-amplitude model/arithmetic review; no video fitting.

Run from any directory: python3 path/to/audit.py
All inputs are immutable copies under source/. Outputs are deterministic.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import math
import re
import sys
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.ndimage import median_filter
from scipy.optimize import brentq
from scipy.signal import find_peaks
from scipy.stats import spearmanr, t as tdist

HERE = Path(__file__).resolve().parent
SRC = HERE / 'source'

def read(name):
    return json.loads((SRC / name).read_text())

@lru_cache(None)
def factor(angle_deg):
    """T(A)/T(0) by first downward zero crossing of theta''=-sin(theta).

    No elliptic-function implementation or author correction code is used.
    """
    if angle_deg == 0:
        return 1.0
    if not 0 < angle_deg < 180:
        raise ValueError('Oscillation amplitude must be in [0,180) degrees')
    def zero(t, y):
        return y[0]
    zero.direction = -1
    zero.terminal = True
    sol = solve_ivp(lambda t, y: [y[1], -math.sin(y[0])], [0, 40],
                    [math.radians(angle_deg), 0], events=zero,
                    method='DOP853', rtol=2e-11, atol=2e-13, max_step=.1)
    if not sol.success or len(sol.t_events[0]) != 1:
        raise RuntimeError('No downward crossing')
    return float(2 * sol.t_events[0][0] / math.pi)

def required_angle(raw_ratio, real_angle):
    target = raw_ratio * factor(float(real_angle))
    if target < 1:
        return None
    return float(brentq(lambda a: factor(float(a)) - target, 0, 179.9999,
                        xtol=1e-8))

def summary(values):
    x = np.asarray(values, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if not n:
        return {'n': 0}
    d = dict(n=n, mean=float(x.mean()), geo=float(np.exp(np.log(x).mean())))
    if n > 1:
        d['se'] = float(x.std(ddof=1) / math.sqrt(n))
        z = np.log(x)
        h = float(tdist.ppf(.975, n-1) * z.std(ddof=1) / math.sqrt(n))
        d['log_t95'] = np.exp([z.mean()-h, z.mean()+h]).tolist()
    return d

def extrema_amplitude(record, width):
    """Preregistered independent sensitivity on already-published angle tracks."""
    s = record['series']
    tx, yy = np.asarray(s['t']), np.asarray(s['theta'])
    gx = np.arange(round(tx[0]*24), round(tx[-1]*24)+1) / 24
    y = np.interp(gx, tx, yy)
    if width > 1:
        y = median_filter(y, size=width, mode='nearest')
    distance = max(1, int(math.floor(.3 * record['T'] * 24)))
    hi, _ = find_peaks(y, prominence=10, distance=distance)
    lo, _ = find_peaks(-y, prominence=10, distance=distance)
    candidates = sorted([(int(i), 1) for i in hi] + [(int(i), -1) for i in lo])
    turns = []
    for i, sign in candidates:
        if turns and turns[-1][1] == sign:
            j = turns[-1][0]
            if sign*y[i] > sign*y[j]:
                turns[-1] = (i, sign)
        else:
            turns.append((i, sign))
    amps = [float(abs(y[j]-y[i])/2) for (i, a), (j, b) in zip(turns, turns[1:])]
    return dict(width=width, amplitude_deg=float(np.median(amps)) if len(amps)>=2 else None,
                pair_count=len(amps), turning_times_s=[float(gx[i]) for i, _ in turns],
                turning_angles_deg=[float(y[i]) for i, _ in turns],
                max_gap_s=float(np.diff(tx).max()), valid_samples=len(tx))

def main():
    a = read('t205_amp_results.json')
    k = read('t206_results.json')
    raw = {**read('k191_nano.json'), **read('k191_fresh.json')}
    real = read('k191_real.json')['real_pend10_f93']
    gates = {**read('k191_gates.json'), **read('k191_gates_fresh.json')}
    published = a['per_clip']
    ref = published['real_pend10_f93']
    names = sorted(n for n in raw if gates[n]['PASS'] and ('p10' in n or n.startswith('k175_')))
    assert names == sorted(a['summary']['GATE_pend10']['clips'])
    assert len(names) == 6
    assert len({re.search(r'_s(\d+)$', n)[1] for n in names}) == 6
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
        assert ok, name
    # Analytic small-angle expansion is a distinct numerical check, not a planted test.
    check('factor zero exact', factor(0) == 1)
    check('small angle expansion', abs(factor(1.) - (1+math.radians(1)**2/16)) < 1e-9)
    check('monotone grid', all(factor(float(b)) > factor(float(a)) for a,b in zip(range(1,179), range(2,180))))
    # Independent primary arithmetic: author angles, original period (matches #4312).
    rows = []
    for n in names:
        p, r = published[n], raw[n]
        ratio = r['T'] / real['T']
        d = dict(clip=n, seed=int(re.search(r'_s(\d+)$',n)[1]), T_s=r['T'],
                 raw_ratio=ratio, A_hc_deg=p['A_hc'], A_peak_deg=p['A_peak'],
                 raw_track_peak_deg=float(np.max(np.abs(r['series']['theta']))),
                 corrected_primary=ratio*factor(ref['A_hc'])/factor(p['A_hc']),
                 corrected_peak=ratio*factor(ref['A_peak'])/factor(p['A_peak']),
                 # Deliberately removes real's amplitude contribution altogether.
                 corrected_peak_real_zero=ratio/factor(p['A_peak']),
                 # Conditional: orthographic, gravity vertical, planar oscillation,
                 # measured peak envelope complete. No fitted centre redefinition.
                 geometric_conditional_lower=ratio/factor(max(90.,p['A_peak'])),
                 angle_needed_given_real_hc_deg=required_angle(ratio, ref['A_hc']),
                 required_zero_real_amp_deg=required_angle(ratio, 0),
                 raw_amplitudes={})
        check(n+' published T unchanged', r['T'] == p['kiro_T'])
        for width in (1,3,5):
            ar, ar_real = extrema_amplitude(r,width), extrema_amplitude(real,width)
            ar['real_amplitude_deg'] = ar_real['amplitude_deg']
            ar['corrected_ratio'] = (ratio*factor(ar_real['amplitude_deg'])/factor(ar['amplitude_deg'])
                                     if ar['amplitude_deg'] is not None and ar_real['amplitude_deg'] is not None else None)
            d['raw_amplitudes'][str(width)] = ar
        rows.append(d)
    summaries = {key:summary([r[key] for r in rows]) for key in
                 ['raw_ratio','corrected_primary','corrected_peak','corrected_peak_real_zero','geometric_conditional_lower']}
    for own, source in [('raw_ratio','R_raw'), ('corrected_primary','R_corr'),('corrected_peak','R_corr_peak')]:
        check(own+' geo reproduces source', abs(summaries[own]['geo']-a['summary']['GATE_pend10'][source]['geo']) < 2e-9)
        check(own+' CI reproduces source', np.max(np.abs(np.array(summaries[own]['log_t95'])-a['summary']['GATE_pend10'][source]['ci95_logt'])) < 2e-9)
    independent_sensitivity = {}
    for width in (1,3,5):
        independent_sensitivity[str(width)] = summary([r['raw_amplitudes'][str(width)]['corrected_ratio'] for r in rows
                                                       if r['raw_amplitudes'][str(width)]['corrected_ratio'] is not None])
    # Author #4313: independently recompute every correction and seed grouping.
    seed_bins, errors, broader = {}, [], []
    for p in k['clips']:
        corrected = p['T']/k['real']['T']*factor(k['real']['fit_A0'])/factor(p['fit_A0'])
        errors.append(abs(corrected-p['ratio_fit_A0']))
        seed = int(re.search(r'_s(\d+)$',p['clip'])[1])
        seed_bins.setdefault(seed,[]).append(corrected)
        broader.append(corrected)
    check('all17 fit_A0 corrections reproduce', max(errors)<2e-9)
    # Native-QC labels fixed in prior task before any of this amplitude work.
    native = read('t198_results.json')
    indep = read('t198_measurement_results.json')
    native_rows=[]
    for p in native['rows']:
        if not p['native_eligible']:
            continue
        q = next(r for r in rows if r['clip']==p['name'])
        tr = indep[p['id']]['period_s'] / native['reference_tool_s']
        native_rows.append(dict(clip=p['name'], id=p['id'], native_rigid=p['rigid'],
            independent_period_ratio=tr,
            corrected_primary=tr*factor(ref['A_hc'])/factor(q['A_hc_deg']),
            corrected_peak=tr*factor(ref['A_peak'])/factor(q['A_peak_deg']),
            geometric_conditional_lower=tr/factor(max(90.,q['A_peak_deg']))))
    check('native subset unchanged s23/s24', {r['clip'] for r in native_rows} == {'k191_p10f93_base_s23','k191_p10f93_base_s24'})
    # No claim that shared camera cancels nonlinear projection. Concrete counterexample.
    c = .5
    def project(a): return math.degrees(math.atan2(c*math.sin(math.radians(a)), math.cos(math.radians(a))))
    true_r,true_n=70.,50.
    proj_r,proj_n=project(true_r),project(true_n)
    projection_example=dict(true_real_deg=true_r,true_nano_deg=true_n,foreshortening=c,
        observed_real_deg=proj_r,observed_nano_deg=proj_n,
        true_factor_ratio=factor(true_r)/factor(true_n),observed_factor_ratio=factor(proj_r)/factor(proj_n))
    # Recompute G3 angle-restricted bad-length frame counts from original series.
    th=np.asarray(real['series']['theta']); ll=np.asarray(real['series']['L'])
    bins=np.arange(-20,85,5)
    vals=np.asarray([np.median(ll[(th>=b-5)&(th<b+5)]) if ((th>=b-5)&(th<b+5)).any() else np.nan for b in bins])
    length_rows=[]
    for n in names:
        rr=raw[n]['series']; tt=np.asarray(rr['theta']); leng=np.asarray(rr['L']); keep=(tt>=-20)&(tt<=80)
        expected=np.interp(tt[keep],bins[np.isfinite(vals)],vals[np.isfinite(vals)])
        dev=np.abs(leng[keep]-expected)/expected
        length_rows.append(dict(clip=n,n_tracked=len(tt),n_g3=int(keep.sum()),
            n_g3_error_ge20pct=int((dev>=.2).sum()),median_abs_relative_error=float(np.median(dev)),
            p95_abs_relative_error=float(np.percentile(dev,95)),max_abs_relative_error=float(dev.max())))
        check(n+' G3 median reproduces',abs(float(np.median(dev))-gates[n]['Ldev'])<1e-12)
    corr=spearmanr([r['A_hc_deg'] for r in rows],[r['T_s'] for r in rows])
    check('GATE source Spearman reproduces',abs(corr.correlation-a['summary']['GATE_pend10']['spearman_Ahc_vs_Rraw'][0])<1e-12)
    result=dict(scope='Same-data correction/model review. Amplitudes remain unvalidated. No new clips or seeds.',
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__),
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.iterdir()) if p.is_file()},
        primary_reference=dict(T_s=real['T'],A_hc_deg=ref['A_hc'],A_peak_deg=ref['A_peak']),
        gate_rows=rows,gate_summaries=summaries,raw_angle_sensitivity=independent_sensitivity,
        source_gate_spearman=dict(rho=float(corr.correlation),p=float(corr.pvalue)),
        broader_fit_A0=dict(clip_weighted=summary(broader),equal_seed=summary([np.mean(v) for v in seed_bins.values()]),
                            seed_means={str(s):float(np.mean(v)) for s,v in sorted(seed_bins.items())},max_correction_error=max(errors)),
        native_QC_subset=dict(rows=native_rows,summaries={key:summary([r[key] for r in native_rows]) for key in
            ['independent_period_ratio','corrected_primary','corrected_peak','geometric_conditional_lower']}),
        common_camera_counterexample=projection_example,length_gate_audit=length_rows,
        checks=checks,passed_checks=len(checks),planted_amplitude='not checked; numerical ODE checks are not planted validation')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({key:result[key] for key in ['gate_summaries','raw_angle_sensitivity','broader_fit_A0','native_QC_subset','common_camera_counterexample','length_gate_audit','passed_checks']},indent=2))

if __name__=='__main__':
    main()
