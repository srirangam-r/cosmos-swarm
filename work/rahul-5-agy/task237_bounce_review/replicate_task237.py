#!/usr/bin/env python3
"""
replicate_task237.py
Independent Replication and Review of Findings #4577 and #4684 (Task 237, rahul-5-agy)
Audits tools/bounce_decay/bounce_decay.py across synthetic benchmark drops:
 - Seed 777 (author benchmark, 30 clips)
 - Seed 888 (independent replication benchmark, 30 clips)
Compares:
 - Baseline unpatched (0 extra iters)
 - Fixed-radius +2 iters (rahul-3 finding #4684)
 - Adaptive-radius +2 iters (updating r on each iteration)
 - Adaptive-radius +3 iters
"""

import os
import sys
import json
import hashlib
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import cv2

# Import bounce_decay from shared repo
BOUNCE_DECAY_DIR = '/home/sha/swarm-work/rahul-api-2/cosmos-swarm/tools/bounce_decay'
sys.path.insert(0, BOUNCE_DECAY_DIR)
import bounce_decay

def run_bounce_decay_mode(clip_path, diam=0.10, mpp=None, thr=10.0, maxjump=60.0,
                          min_rise=4.0, min_pts=3, hold_px=1.0, tail_frac=0.15,
                          rest_px=2.0, extra_iters=0, adaptive_radius=False):
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
        if adaptive_radius:
            r_cur = np.nanmedian(diam_arr) / 2 if np.isfinite(np.nanmedian(diam_arr)) else r
        else:
            r_cur = r
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
        extra_iters=extra_iters, adaptive_radius=adaptive_radius
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

def worker_task(args):
    clip_id, clip_file, diam, iters, adaptive = args
    res = run_bounce_decay_mode(clip_file, diam=diam, extra_iters=iters, adaptive_radius=adaptive)
    return clip_id, res

def evaluate_dataset(truth_file, clips_dir):
    with open(truth_file) as f:
        truth = json.load(f)
        
    modes = [
        ('baseline', 0, False),
        ('fixed_r_iter2', 2, False),
        ('adapt_r_iter2', 2, True),
        ('adapt_r_iter3', 3, True)
    ]
    
    results = {}
    with ProcessPoolExecutor(max_workers=8) as executor:
        for mode_name, iters, adaptive in modes:
            print(f"Running evaluation: mode={mode_name} (iters={iters}, adaptive={adaptive})...", flush=True)
            tasks = []
            for clip_id, t_info in sorted(truth.items()):
                clip_path = os.path.join(clips_dir, f"{clip_id}.mp4")
                tasks.append((clip_id, clip_path, t_info['diam'], iters, adaptive))
                
            mode_res = {}
            for cid, r in executor.map(worker_task, tasks):
                mode_res[cid] = r
            results[mode_name] = mode_res
            
    # Compute summary metrics
    summary = {}
    for mode_name, _, _ in modes:
        mode_res = results[mode_name]
        summary[mode_name] = {}
        for metric, key in [('e_v', 'e_v'), ('e_T_fit', 'e_T_fit'), ('g_joint', 'g_joint')]:
            ratios = []
            valid_clips = []
            for cid, t_info in sorted(truth.items()):
                r = mode_res.get(cid)
                if not r: continue
                val = r.get(key)
                if isinstance(val, list):
                    val = val[0] if len(val) > 0 else None
                if val is None or not np.isfinite(val):
                    continue
                tr = t_info['g'] if key == 'g_joint' else t_info['e']
                rat = float(val / tr)
                ratios.append(rat)
                valid_clips.append(cid)
            ratios_arr = np.array(ratios) if ratios else np.array([])
            all_clips = sorted(truth.keys())
            missing = sorted(list(set(all_clips) - set(valid_clips)))
            summary[mode_name][metric] = {
                'count': len(ratios),
                'total': len(truth),
                'coverage': len(ratios) / len(truth),
                'mean_ratio': float(np.mean(ratios_arr)) if len(ratios) else None,
                'std_ratio': float(np.std(ratios_arr)) if len(ratios) else None,
                'max_err': float(np.max(np.abs(ratios_arr - 1.0))) if len(ratios) else None,
                'valid_clips': valid_clips,
                'missing_clips': missing
            }
            
    return truth, results, summary

def main():
    base_dir = '/home/sha/swarm-work/rahul-5-agy/task237_bounce_review'
    
    print("================== SEED 777 EVALUATION (AUTHOR BENCHMARK) ==================")
    t777, r777, s777 = evaluate_dataset(
        os.path.join(base_dir, 'truth_777.json'),
        os.path.join(base_dir, 'clips_777')
    )
    
    print("\n================== SEED 888 EVALUATION (FRESH INDEPENDENT BENCHMARK) ==================")
    t888, r888, s888 = evaluate_dataset(
        os.path.join(base_dir, 'truth_888.json'),
        os.path.join(base_dir, 'clips_888')
    )
    
    # Save combined results
    out_json = os.path.join(base_dir, 'task237_results.json')
    with open(out_json, 'w') as f:
        json.dump({
            'seed_777': {'summary': s777, 'truth': t777, 'results': r777},
            'seed_888': {'summary': s888, 'truth': t888, 'results': r888}
        }, f, indent=2)
    print(f"\nAll evaluation results saved to {out_json}")
    
    # Print formatted comparison tables
    for s_name, s_data in [('Seed 777 (Author)', s777), ('Seed 888 (Fresh Independent)', s888)]:
        print(f"\n--- {s_name} Summary Table ---")
        print(f"{'Arm':<18} | {'e_v Coverage':<12} | {'e_v Mean±SD':<18} | {'e_T Coverage':<12} | {'e_T Mean±SD':<18} | {'Missing e_v':<20}")
        print("-" * 110)
        for arm in ['baseline', 'fixed_r_iter2', 'adapt_r_iter2', 'adapt_r_iter3']:
            ev = s_data[arm]['e_v']
            et = s_data[arm]['e_T_fit']
            ev_str = f"{ev['mean_ratio']:.4f} ± {ev['std_ratio']:.4f}" if ev['mean_ratio'] else "N/A"
            et_str = f"{et['mean_ratio']:.4f} ± {et['std_ratio']:.4f}" if et['mean_ratio'] else "N/A"
            miss = ",".join(ev['missing_clips']) if ev['missing_clips'] else "None"
            print(f"{arm:<18} | {ev['count']:2d}/{ev['total']:2d} ({ev['coverage']*100:.1f}%) | {ev_str:<18} | "
                  f"{et['count']:2d}/{et['total']:2d} ({et['coverage']*100:.1f}%) | {et_str:<18} | {miss:<20}")

if __name__ == '__main__':
    main()
