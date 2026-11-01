#!/usr/bin/env python3
"""
replicate_bounce_decay_ghost.py
Independent replication and review of Finding #4684 (Task 36, rahul-3).

Tests:
1. Baseline unpatched bounce_decay (0 extra iterations of ghost_free_bg) vs patched (+1, +2, +3 extra iterations).
2. Verifies whether iterating ghost_free_bg + track 2 extra times raises e_v coverage from 24/30 to 27/30.
3. Examines the remaining 3 clips lacking e_v, identifying the exact physical / sampling mechanism.
4. Audits flight-time fit e_T_fit across low vs high restitution e, testing rahul-3's hypothesis of sampling limits.
"""

import os
import sys
import json
import hashlib
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import cv2

# Import core functions from tools/bounce_decay/bounce_decay.py
sys.path.insert(0, '/home/nail/swarm-work/agy-2/cosmos-swarm/tools/bounce_decay')
import bounce_decay

def process_single_clip(args):
    clip_id, clip_file, diam, iters = args
    res = run_bounce_decay_custom(clip_file, diam=diam, extra_iters=iters)
    return clip_id, res

def run_bounce_decay_custom(clip_path, diam=0.10, mpp=None, thr=10.0, maxjump=60.0,
                            min_rise=4.0, min_pts=3, hold_px=1.0, tail_frac=0.15,
                            rest_px=2.0, extra_iters=0):
    fr, fps0 = bounce_decay.load(clip_path)
    fps = fps0
    n = len(fr)
    t = np.arange(n) / fps
    bg0 = np.median(fr, 0)
    seed = bounce_decay.auto_seed(fr, bg0, thr)
    
    # Pass 1
    p1, d1 = bounce_decay.track(fr, bg0, seed, thr, maxjump)
    r = np.nanmedian(d1) / 2 if np.isfinite(np.nanmedian(d1)) else 10.0
    
    # Pass 2
    bg = bounce_decay.ghost_free_bg(fr, p1, r)
    pts, diam_arr = bounce_decay.track(fr, bg, seed, thr, maxjump)
    
    # Extra iterations
    for it in range(extra_iters):
        r_cur = np.nanmedian(diam_arr) / 2 if np.isfinite(np.nanmedian(diam_arr)) else r
        bg = bounce_decay.ghost_free_bg(fr, pts, r_cur)
        pts, diam_arr = bounce_decay.track(fr, bg, seed, thr, maxjump)
        
    y = pts[:, 1]
    an = bounce_decay.analyse(t, y, min_rise, min_pts, hold_px)
    
    fp = an['peaks'][0] if an['peaks'] else n
    dd = diam_arr[:max(fp - 2, 1)]
    dpx = float(np.nanmedian(dd)) if np.isfinite(dd).any() else float(np.nanmedian(diam_arr))
    calc_mpp = mpp if mpp else (diam / dpx if diam else None)
    
    out = dict(
        clip=clip_path, fps=fps, n_frames=n, seed=[float(seed[0]), float(seed[1])],
        diam_px=dpx, mpp=calc_mpp, n_tracked=int((~np.isnan(y)).sum()),
        tool='bounce_decay_review.py', extra_iters=extra_iters
    )
    out.update({k: v for k, v in an.items() if k not in ('segs',)})
    
    imps = an['impacts']
    if imps:
        out['e_v'] = [i['e_v'] for i in imps]
        ti = np.array([i['t'] for i in imps])
        T = np.diff(ti)
        out['T'] = T.tolist()
        out['e_T'] = (T[1:] / T[:-1]).tolist() if len(T) > 1 else []
        if len(T) >= 3:
            k_arr = np.arange(len(T))
            X = np.stack([np.ones_like(k_arr), k_arr], 1).astype(float)
            cf, *_ = np.linalg.lstsq(X, np.log(T), rcond=None)
            rs = np.log(T) - X @ cf
            s2 = rs @ rs / (len(T) - 2)
            se = np.sqrt(s2 / ((k_arr - k_arr.mean()) ** 2).sum())
            out['e_T_fit'] = float(np.exp(cf[1]))
            out['e_T_fit_se'] = float(np.exp(cf[1]) * se)
        elif len(T) == 2:
            out['e_T_fit'] = float(T[1] / T[0])
            out['e_T_fit_se'] = None
        else:
            out['e_T_fit'] = None
            out['e_T_fit_se'] = None
            
        h = []
        for k in range(len(imps)):
            if k + 1 < len(an['apex']):
                ap_ = an['apex'][k + 1]
                if imps[k]['t'] < ap_['t'] and (k + 1 >= len(imps) or ap_['t'] < imps[k + 1]['t']):
                    h.append(imps[k]['y'] - ap_['y'])
        out['h_px'] = h
        out['e_h'] = [float(np.sqrt(max(h[k + 1], 0) / h[k])) for k in range(len(h) - 1) if h[k] > 0]
        out['n_impacts'] = len(imps)
        out['last_impact_s'] = float(ti[-1])
    else:
        out['n_impacts'] = 0
        out['e_v'] = []
        out['T'] = []
        out['e_T'] = []
        out['e_T_fit'] = None
        out['e_T_fit_se'] = None
        out['h_px'] = []
        out['e_h'] = []
        
    peaks = an['peaks']
    tail0 = int(n * (1 - tail_frac))
    ok = ~np.isnan(y)
    out['still_bouncing_at_end'] = bool(any(p >= tail0 for p in peaks))
    floor = np.nanmax(y) if ok.any() else np.nan
    near = ok & (np.abs(y - floor) <= rest_px)
    rest = None
    for i in range(n - 1, -1, -1):
        if not near[i] and ok[i]:
            break
        rest = i
    out['rest_s'] = float(t[rest]) if (rest is not None and rest < n - 3) else None
    if calc_mpp:
        out['g_joint'] = float(2 * an['a_px'] * calc_mpp) if 'a_px' in an else None
    else:
        out['g_joint'] = None
        
    out['track_y'] = [None if np.isnan(v) else round(float(v), 2) for v in y]
    return out

def evaluate_suite(truth_path, clips_dir, extra_iters_list=[0, 1, 2, 3]):
    truth = json.load(open(truth_path))
    results = {}
    
    with ProcessPoolExecutor(max_workers=12) as executor:
        for iters in extra_iters_list:
            print(f"--- Running evaluation with extra_iters = {iters} ---", flush=True)
            tasks = []
            for clip_id, t_info in sorted(truth.items()):
                clip_file = os.path.join(clips_dir, f"{clip_id}.mp4")
                tasks.append((clip_id, clip_file, t_info['diam'], iters))
            
            iter_results = {}
            for clip_id, res in executor.map(process_single_clip, tasks):
                iter_results[clip_id] = res
            results[iters] = iter_results
            print(f"Completed extra_iters = {iters} ({len(iter_results)} clips)", flush=True)
        
    return truth, results

def analyze_results(truth, all_results):
    summary = {}
    
    for iters, iter_res in all_results.items():
        summary[iters] = {}
        for name, key in [('e_v', 'e_v'), ('e_T_fit', 'e_T_fit'), ('g_joint', 'g_joint')]:
            ratios = []
            valid_clips = []
            for k, t_info in sorted(truth.items()):
                r = iter_res.get(k)
                if not r:
                    continue
                v = r.get(key)
                if isinstance(v, list):
                    v = v[0] if len(v) > 0 else None
                if v is None or not np.isfinite(v):
                    continue
                tr = t_info['g'] if key == 'g_joint' else t_info['e']
                rat = float(v / tr)
                ratios.append(rat)
                valid_clips.append(k)
            ratios_arr = np.array(ratios) if ratios else np.array([])
            summary[iters][name] = {
                'count': len(ratios),
                'total': len(truth),
                'coverage': len(ratios) / len(truth),
                'mean_ratio': float(np.mean(ratios_arr)) if len(ratios) else None,
                'std_ratio': float(np.std(ratios_arr)) if len(ratios) else None,
                'max_err': float(np.max(np.abs(ratios_arr - 1.0))) if len(ratios) else None,
                'clips': valid_clips
            }
            
    return summary

def main():
    clips_dir = '/home/nail/swarm-work/agy-2/clips'
    truth_path = '/home/nail/swarm-work/agy-2/truth.json'
    out_dir = '/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/t36_bounce_decay_review'
    os.makedirs(out_dir, exist_ok=True)
    
    truth, all_results = evaluate_suite(truth_path, clips_dir, extra_iters_list=[0, 1, 2, 3])
    summary = analyze_results(truth, all_results)
    
    print("\n================== SUMMARY RESULTS ==================", flush=True)
    for iters, s in summary.items():
        print(f"\nExtra Iterations: {iters}", flush=True)
        for metric, data in s.items():
            print(f"  {metric:10s}: {data['count']:2d}/{data['total']:2d} ({data['coverage']*100:.1f}%) | "
                  f"mean={data['mean_ratio']:.4f} std={data['std_ratio']:.4f} max_err={data['max_err']:.4f}", flush=True)
            
    # Check clip differences between 0 and 2 extra iters
    c0 = set(summary[0]['e_v']['clips'])
    c2 = set(summary[2]['e_v']['clips'])
    gained = sorted(list(c2 - c0))
    lost = sorted(list(c0 - c2))
    all_30 = set(truth.keys())
    missing_c2 = sorted(list(all_30 - c2))
    
    print(f"\nClips gaining e_v with +2 iters: {gained}", flush=True)
    for g in gained:
        t_info = truth[g]
        print(f"  {g}: e={t_info['e']}, hold={t_info['hold']}, drift={t_info['drift']}, mpp={t_info['mpp']:.4f}", flush=True)
        
    print(f"\nClips still missing e_v with +2 iters: {missing_c2}", flush=True)
    for m in missing_c2:
        t_info = truth[m]
        res = all_results[2][m]
        print(f"  {m}: e={t_info['e']}, hold={t_info['hold']}, drift={t_info['drift']}, "
              f"n_impacts={res['n_impacts']}, peaks={res.get('peaks')}, n_tracked={res['n_tracked']}", flush=True)

    # Save detailed JSON output
    out_file = os.path.join(out_dir, "independent_replication_results.json")
    with open(out_file, 'w') as f:
        json.dump({
            'summary': summary,
            'gained_clips': gained,
            'missing_clips': missing_c2,
            'truth': truth,
            'results_iter0': all_results[0],
            'results_iter2': all_results[2]
        }, f, indent=2)
    print(f"\nSaved results to {out_file}", flush=True)

if __name__ == '__main__':
    main()
