#!/usr/bin/env python3
"""
Task 231: Independent Replication & In-Depth Audit of Finding #4505
Author: agy-3 (Shift 42)
Target Finding: Finding #4505 (poornima-3, exploratory extension to Task 217)
Claim: "with QT, Nano's ball goes quiet about 2.6x later than the real GAUGE ball from the same input frame. Without QT (F) it mostly never goes quiet."
"""
import os, sys, glob, json, csv
import numpy as np
import cv2

# Input paths on board
CLIPS_DIR = "/home/swarm/jobs/poornima-2/task141/clips"
REAL_DIR = "/home/swarm/jobs/poornima-3/t141px/real"
CODES_SIZE_CSV = "/home/swarm/jobs/poornima-2/task141/codes_named_size.csv"
AUTHOR_RESULTS_JSON = "/home/swarm/jobs/poornima-3/t141px/quiet2_results.json"
OUT_DIR = "/home/swarm/jobs/agy-3/task231_quiet_time"

os.makedirs(OUT_DIR, exist_ok=True)

# 1. Spatial ROIs (104x60 grid)
def box(x0, x1, y0, y1):
    b = np.zeros((60, 104), bool)
    b[y0:y1+1, x0:x1+1] = True
    return b

BALL = box(22, 45, 14, 33) | box(8, 63, 34, 59)
BG = box(64, 103, 0, 59)
AIR = box(22, 45, 14, 33)
LOW = box(8, 63, 34, 59)
ROBOT = box(22, 45, 0, 13) | box(46, 61, 0, 33)

print("Starting video decoding for 90 native MP4 clips...")

# Load and decode all 90 clips
clips_data = {}
mp4_files = sorted(glob.glob(os.path.join(CLIPS_DIR, "t141_*.mp4")))
print(f"Found {len(mp4_files)} clips in {CLIPS_DIR}")

for idx, fpath in enumerate(mp4_files):
    fname = os.path.basename(fpath)
    # format: t141_<img_id>_<prompt_id>_<seed_id>.mp4
    parts = fname[:-4].split("_")
    img = parts[1]
    prompt = parts[2]
    seed_str = parts[3]
    seed = int(seed_str[1:])
    
    cap = cv2.VideoCapture(fpath)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frames.append(cv2.resize(g, (104, 60), interpolation=cv2.INTER_AREA))
    cap.release()
    
    arr = np.stack(frames).astype(np.float32)
    # compute spatial differences
    diff = np.abs(np.diff(arr, axis=0)) # [T-1, 60, 104]
    
    ball_m = diff[:, BALL].mean(axis=1)
    bg_m = diff[:, BG].mean(axis=1)
    ratio = ball_m / np.maximum(bg_m, 1e-6)
    
    air_m = diff[:, AIR].mean(axis=1)
    low_m = diff[:, LOW].mean(axis=1)
    robot_m = diff[:, ROBOT].mean(axis=1)
    
    clips_data[fname[:-4]] = {
        'img': img,
        'prompt': prompt,
        'seed': seed,
        'frames': len(arr),
        'ratio': ratio,
        'ball_m': ball_m,
        'bg_m': bg_m,
        'air_m': air_m,
        'low_m': low_m,
        'robot_m': robot_m,
        'f0': arr[0]
    }
    if (idx + 1) % 15 == 0:
        print(f"  Decoded {idx+1}/{len(mp4_files)} clips...")

print(f"All {len(clips_data)} clips decoded.")

# 2. Load Real References
def load_real_gray(name):
    p = os.path.join(REAL_DIR, name + ".gray")
    a = np.fromfile(p, dtype=np.uint8)
    return a.reshape(-1, 60, 104).astype(np.float32)

REAL_STREAMS = {
    'b1dd33': [
        ('lb', load_real_gray('b1dd33_lb'), 25.44),
        ('vaert', load_real_gray('b1dd33_vaert'), 25.0)
    ],
    'b2dd35': [
        ('lb', load_real_gray('b2dd35_lb'), 25.03),
        ('vaert', load_real_gray('b2dd35_vaert'), 25.0),
        ('orig93', load_real_gray('b2dd35_orig93'), 25.0)
    ],
    'b2dd37': [
        ('lb', load_real_gray('b2dd37_lb'), 25.03)
    ]
}

real_data = {}
for img, streams in REAL_STREAMS.items():
    real_data[img] = {}
    for tag, arr, fps in streams:
        diff = np.abs(np.diff(arr, axis=0))
        ball_m = diff[:, BALL].mean(axis=1)
        bg_m = diff[:, BG].mean(axis=1)
        ratio = ball_m / np.maximum(bg_m, 1e-6)
        real_data[img][tag] = {
            'fps': fps,
            'frames': len(arr),
            'ratio': ratio,
            'ball_m': ball_m,
            'bg_m': bg_m
        }

# 3. Binning & Quiet Time Algorithms
def compute_discrete_bins(r, bin_size=12):
    return np.array([r[i:i+bin_size].mean() for i in range(0, len(r) - bin_size + 1, bin_size)])

def time_to_quiet_discrete(b, th, fps, bin_size=12):
    for i in range(len(b) - 1):
        if b[i] <= th and b[i+1] <= th:
            return round(i * bin_size / fps, 3)
    return None

def time_to_quiet_rolling(r, th, fps, win=12, persist=24):
    """Continuous rolling window: ratio smoothed over win frames, quiet if <= th for persist frames."""
    roll = np.convolve(r, np.ones(win)/win, mode='valid')
    is_quiet = (roll <= th)
    # find first index where is_quiet is true for persist consecutive frames
    if len(is_quiet) < persist:
        return None
    for i in range(len(is_quiet) - persist + 1):
        if np.all(is_quiet[i:i+persist]):
            return round(i / fps, 3)
    return None

# Load size codes for ball growth interaction
size_codes = {}
if os.path.exists(CODES_SIZE_CSV):
    with open(CODES_SIZE_CSV, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # name format in csv: t141q8_b2dd35_F_s6 -> map to t141_b2dd35_F_s6
            norm_name = row['name'].replace('t141q8_', 't141_')
            size_codes[norm_name] = {
                'end_ratio': float(row['end_ratio']) if row['end_ratio'] else None,
                'growth_end': int(row['growth_end']) if row['growth_end'] else None,
                'settle': int(row['settle']) if row['settle'] else None,
                'clean_settle2': int(row['clean_settle2']) if row['clean_settle2'] else None,
            }

# Compute quiet times across TH and binning
thresholds = [1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0]

# Author replication check (discrete bin_size=12, TH in [1.5, 2.0, 2.5])
eval_results = {}
for name, c in clips_data.items():
    bb = compute_discrete_bins(c['ratio'], bin_size=12)
    c['bins12'] = [round(float(v), 3) for v in bb]
    c['quiet_discrete'] = {}
    c['quiet_rolling'] = {}
    c['quiet_win6'] = {}
    c['quiet_win24'] = {}
    
    for th in thresholds:
        c['quiet_discrete'][str(th)] = time_to_quiet_discrete(bb, th, fps=24.0, bin_size=12)
        c['quiet_rolling'][str(th)] = time_to_quiet_rolling(c['ratio'], th, fps=24.0, win=12, persist=24)
        c['quiet_win6'][str(th)] = time_to_quiet_rolling(c['ratio'], th, fps=24.0, win=6, persist=24)
        c['quiet_win24'][str(th)] = time_to_quiet_rolling(c['ratio'], th, fps=24.0, win=24, persist=24)
    
    # attach size codes
    c['size_info'] = size_codes.get(name, {})

# Compute for real data
for img, streams in real_data.items():
    for tag, r in streams.items():
        bb = compute_discrete_bins(r['ratio'], bin_size=12)
        r['bins12'] = [round(float(v), 3) for v in bb]
        r['quiet_discrete'] = {}
        r['quiet_rolling'] = {}
        for th in thresholds:
            r['quiet_discrete'][str(th)] = time_to_quiet_discrete(bb, th, fps=r['fps'], bin_size=12)
            r['quiet_rolling'][str(th)] = time_to_quiet_rolling(r['ratio'], th, fps=r['fps'], win=12, persist=24)

# 4. Statistical Aggregation
summary = {}

for prompt in ['F', 'QT', 'N']:
    summary[prompt] = {}
    for th in thresholds:
        th_s = str(th)
        times_disc = [clips_data[k]['quiet_discrete'][th_s] for k in clips_data if clips_data[k]['prompt'] == prompt]
        times_roll = [clips_data[k]['quiet_rolling'][th_s] for k in clips_data if clips_data[k]['prompt'] == prompt]
        
        # replace None with 99 for medians / percentiles
        num_disc = [t if t is not None else 99.0 for t in times_disc]
        num_roll = [t if t is not None else 99.0 for t in times_roll]
        
        summary[prompt][th_s] = {
            'discrete': {
                'median': float(np.median(num_disc)),
                'p25': float(np.percentile(num_disc, 25)),
                'p75': float(np.percentile(num_disc, 75)),
                'never_count': sum(t is None for t in times_disc),
                'by_2s_count': sum(t is not None and t <= 2.0 for t in times_disc),
                'total': len(times_disc)
            },
            'rolling': {
                'median': float(np.median(num_roll)),
                'p25': float(np.percentile(num_roll, 25)),
                'p75': float(np.percentile(num_roll, 75)),
                'never_count': sum(t is None for t in times_roll),
                'by_2s_count': sum(t is not None and t <= 2.0 for t in times_roll),
                'total': len(times_roll)
            }
        }

# Real summary
real_summary = {}
for img in real_data:
    real_summary[img] = {}
    for tag in real_data[img]:
        r = real_data[img][tag]
        real_summary[img][tag] = {
            'quiet_discrete': r['quiet_discrete'],
            'quiet_rolling': r['quiet_rolling'],
            'bins12': r['bins12']
        }

# 5. Stratification by Ball Growth on QT clips
qt_growth_strat = {}
for growth_label, filter_fn in [
    ('all_QT', lambda c: True),
    ('no_growth_size', lambda c: c['size_info'].get('growth_end') == 0),
    ('growth_size', lambda c: c['size_info'].get('growth_end') == 1),
    ('clean_settle2', lambda c: c['size_info'].get('clean_settle2') == 1),
]:
    qt_subset = [clips_data[k] for k in clips_data if clips_data[k]['prompt'] == 'QT' and filter_fn(clips_data[k])]
    qt_growth_strat[growth_label] = {
        'n': len(qt_subset)
    }
    for th in [1.5, 2.0, 2.5]:
        th_s = str(th)
        t_d = [c['quiet_discrete'][th_s] for c in qt_subset]
        t_r = [c['quiet_rolling'][th_s] for c in qt_subset]
        num_d = [t if t is not None else 99.0 for t in t_d]
        num_r = [t if t is not None else 99.0 for t in t_r]
        qt_growth_strat[growth_label][th_s] = {
            'discrete_median': float(np.median(num_d)),
            'discrete_never': sum(t is None for t in t_d),
            'discrete_by2s': sum(t is not None and t <= 2.0 for t in t_d),
            'rolling_median': float(np.median(num_r)),
            'rolling_never': sum(t is None for t in t_r),
            'rolling_by2s': sum(t is not None and t <= 2.0 for t in t_r),
        }

# 6. Seed Clustering & Variance Decomposition (ANOVA) on QT clips
# Compute seed medians across the 3 images for QT
seed_qt_data = {}
for s in range(1, 11):
    seed_clips = [clips_data[k] for k in clips_data if clips_data[k]['prompt'] == 'QT' and clips_data[k]['seed'] == s]
    seed_qt_data[s] = {
        'clips': [k for k in clips_data if clips_data[k]['prompt'] == 'QT' and clips_data[k]['seed'] == s],
        'quiet_2.0_discrete': [c['quiet_discrete']['2.0'] for c in seed_clips],
        'quiet_2.0_rolling': [c['quiet_rolling']['2.0'] for c in seed_clips],
        'end_ratios': [c['size_info'].get('end_ratio') for c in seed_clips],
        'growth_end': [c['size_info'].get('growth_end') for c in seed_clips]
    }

# 7. Check Numerical Agreement with Author's quiet2_results.json
author_check = {'matched': 0, 'mismatched': 0, 'details': []}
if os.path.exists(AUTHOR_RESULTS_JSON):
    with open(AUTHOR_RESULTS_JSON, 'r') as f:
        auth = json.load(f)
    for img in auth:
        for p in ['F', 'QT', 'N']:
            for th_s in ['1.5', '2.0', '2.5']:
                auth_vals = auth[img]['nano'][p][th_s]
                # find our clips
                # order in rows: seeds 1..10
                our_clips = [clips_data[f"t141_{img}_{p}_s{s}"] for s in range(1, 11)]
                our_vals = [c['quiet_discrete'][th_s] for c in our_clips]
                for s_idx, (av, ov) in enumerate(zip(auth_vals, our_vals)):
                    if (av is None and ov is None) or (av is not None and ov is not None and abs(av - ov) < 1e-3):
                        author_check['matched'] += 1
                    else:
                        author_check['mismatched'] += 1
                        author_check['details'].append({
                            'img': img, 'prompt': p, 'seed': s_idx+1, 'th': th_s,
                            'author': av, 'ours': ov
                        })

print(f"Author exact replication check: {author_check['matched']} matched, {author_check['mismatched']} mismatched.")

# Save master JSON output
out_payload = {
    'summary': summary,
    'real_summary': real_summary,
    'qt_growth_strat': qt_growth_strat,
    'seed_qt_data': seed_qt_data,
    'author_check': author_check,
    'per_clip_data': {k: {
        'img': v['img'], 'prompt': v['prompt'], 'seed': v['seed'],
        'quiet_discrete': v['quiet_discrete'],
        'quiet_rolling': v['quiet_rolling'],
        'bins12': v['bins12'],
        'size_info': v['size_info']
    } for k, v in clips_data.items()}
}

out_file = os.path.join(OUT_DIR, "replicate_4505_results.json")
with open(out_file, 'w') as f:
    json.dump(out_payload, f, indent=2)

print(f"Results successfully saved to {out_file}")
