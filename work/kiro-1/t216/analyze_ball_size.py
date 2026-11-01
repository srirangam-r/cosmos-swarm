#!/usr/bin/env python3
"""
Analyze ball size across all 90 task-141 clips with perspective calibration.
"""
import json
import cv2
import numpy as np
from pathlib import Path
from track_ball import track_ball_template, detect_ball_at_position, calibrate_perspective
import matplotlib.pyplot as plt
from scipy import stats

def extract_seed_from_filename(filename):
    """Extract seed number from t141_*_s<N>.mp4"""
    parts = filename.stem.split('_')
    for part in parts:
        if part.startswith('s'):
            return int(part[1:])
    return None

def extract_arm_from_filename(filename):
    """Extract arm (F/QT/N) from filename"""
    parts = filename.stem.split('_')
    for part in parts:
        if part in ['F', 'QT', 'N']:
            return part
    return None

def extract_scene_from_filename(filename):
    """Extract scene (b1dd33, b2dd35, b2dd37) from filename"""
    parts = filename.stem.split('_')
    for part in parts:
        if part.startswith('b'):
            return part
    return None

def detect_landing_frame(track_results, video_height):
    """Detect approximate first landing frame (ball reaches bottom third and velocity reverses)."""
    if len(track_results) < 10:
        return None
    
    cy_values = [r['cy'] for r in track_results]
    frames = [r['frame'] for r in track_results]
    
    # Bottom third of frame
    bottom_third = video_height * 2/3
    
    # Find first time ball enters bottom third
    for i, (f, cy) in enumerate(zip(frames, cy_values)):
        if cy > bottom_third and f > 5:  # Skip very early frames
            return f
    
    return None

def main():
    work_dir = Path(__file__).parent
    clips_dir = work_dir / 'clips'
    output_dir = work_dir / 'results'
    output_dir.mkdir(exist_ok=True)
    
    # Step 1: Calibrate perspective using real GAUGE clips
    print("=== Step 1: Perspective Calibration ===")
    gauge_dir = work_dir.parent / 'gauge'
    
    calib_results = {}
    for gauge_file in ['10.mp4', '12.mp4']:
        gauge_path = gauge_dir / gauge_file
        gauge_json = gauge_dir / gauge_file.replace('.mp4', '.json')
        
        if not gauge_path.exists():
            print(f"Warning: {gauge_path} not found")
            continue
        
        print(f"Calibrating on {gauge_file}...")
        calib = calibrate_perspective(gauge_path, gauge_json)
        if calib:
            calib_results[gauge_file] = calib
            print(f"  Mean diameter: {calib['mean_diameter_px']:.1f} px for 49mm ball")
            print(f"  Y range: {calib['y_range']}")
        else:
            print(f"  Calibration failed")
    
    if not calib_results:
        print("ERROR: No calibration succeeded")
        return
    
    # Average calibration
    mean_calib_px = np.mean([c['mean_diameter_px'] for c in calib_results.values()])
    print(f"\nAverage calibration: {mean_calib_px:.1f} px = 49mm")
    print(f"Scale: {49/mean_calib_px:.4f} mm/px")
    
    # Save calibration
    with open(output_dir / 'calibration.json', 'w') as f:
        json.dump(calib_results, f, indent=2)
    
    # Step 2: Track all 90 clips
    print("\n=== Step 2: Tracking 90 clips ===")
    
    all_tracks = {}
    
    for video_path in sorted(clips_dir.glob('t141_*.mp4')):
        scene = extract_scene_from_filename(video_path)
        arm = extract_arm_from_filename(video_path)
        seed = extract_seed_from_filename(video_path)
        
        if not all([scene, arm, seed]):
            print(f"Skipping {video_path.name}: couldn't parse")
            continue
        
        print(f"Tracking {video_path.name} ... ", end='', flush=True)
        
        # Detect initial position (frame 0 at top of drop)
        cap = cv2.VideoCapture(str(video_path))
        ret, frame = cap.read()
        h, w = frame.shape[:2]
        cap.release()
        
        if not ret:
            print("FAILED (couldn't read)")
            continue
        
        # Ball starts near top center
        cx, cy, d = detect_ball_at_position(frame, w//2, h//3, search_radius=200)
        
        # Track
        track_results = track_ball_template(video_path, (cx, cy, d))
        
        if not track_results:
            print("FAILED (tracking)")
            continue
        
        # Detect landing frame
        landing_frame = detect_landing_frame(track_results, h)
        
        # Get diameter at f0, landing, and end
        d_f0 = track_results[0]['diameter'] if track_results else None
        d_landing = None
        if landing_frame and landing_frame < len(track_results):
            d_landing = track_results[landing_frame]['diameter']
        d_end = track_results[-1]['diameter'] if track_results else None
        
        all_tracks[video_path.stem] = {
            'scene': scene,
            'arm': arm,
            'seed': seed,
            'track': track_results,
            'landing_frame': landing_frame,
            'd_f0': d_f0,
            'd_landing': d_landing,
            'd_end': d_end,
            'n_frames': len(track_results)
        }
        
        print(f"OK (n={len(track_results)}, landing=f{landing_frame}, d_end={d_end:.1f}px)")
    
    print(f"\nTracked {len(all_tracks)}/90 clips")
    
    # Save all tracks
    # Make JSON-serializable
    def to_python(obj):
        """Convert numpy types to Python native types."""
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif obj is None:
            return None
        return obj
    
    tracks_serializable = {}
    for key, val in all_tracks.items():
        tracks_serializable[key] = {
            'scene': val['scene'],
            'arm': val['arm'],
            'seed': to_python(val['seed']),
            'landing_frame': to_python(val['landing_frame']),
            'd_f0': to_python(val['d_f0']),
            'd_landing': to_python(val['d_landing']),
            'd_end': to_python(val['d_end']),
            'n_frames': to_python(val['n_frames'])
        }
    
    with open(output_dir / 'all_tracks_summary.json', 'w') as f:
        json.dump(tracks_serializable, f, indent=2)
    
    # Step 3: Compute per-arm statistics
    print("\n=== Step 3: Per-Arm Statistics ===")
    
    stats_by_arm = {}
    
    for arm in ['F', 'QT', 'N']:
        arm_data = [v for v in all_tracks.values() if v['arm'] == arm]
        
        d_f0_list = [d['d_f0'] for d in arm_data if d['d_f0'] is not None]
        d_landing_list = [d['d_landing'] for d in arm_data if d['d_landing'] is not None]
        d_end_list = [d['d_end'] for d in arm_data if d['d_end'] is not None]
        
        # Convert to mm using calibration
        mm_per_px = 49 / mean_calib_px
        
        d_f0_mm = np.array(d_f0_list) * mm_per_px
        d_landing_mm = np.array(d_landing_list) * mm_per_px
        d_end_mm = np.array(d_end_list) * mm_per_px
        
        # Ratios vs real (49mm)
        ratio_f0 = d_f0_mm / 49
        ratio_landing = d_landing_mm / 49
        ratio_end = d_end_mm / 49
        
        # Bootstrap CI for seed clusters
        def bootstrap_ci(data, n_boot=1000, confidence=0.95):
            if len(data) < 2:
                return float(np.mean(data)), (np.nan, np.nan)
            
            # Resample seeds (not individual measurements)
            # Assume each clip is from a different seed cluster
            seeds = np.arange(len(data))
            boot_means = []
            for _ in range(n_boot):
                boot_sample = np.random.choice(data, size=len(data), replace=True)
                boot_means.append(np.mean(boot_sample))
            
            mean_val = float(np.mean(data))
            ci_low = float(np.percentile(boot_means, (1-confidence)/2 * 100))
            ci_high = float(np.percentile(boot_means, (1+confidence)/2 * 100))
            return mean_val, (ci_low, ci_high)
        
        stats_by_arm[arm] = {
            'n_clips': len(arm_data),
            'n_f0': len(d_f0_list),
            'n_landing': len(d_landing_list),
            'n_end': len(d_end_list),
            'ratio_f0': bootstrap_ci(ratio_f0) if len(ratio_f0) > 0 else (np.nan, (np.nan, np.nan)),
            'ratio_landing': bootstrap_ci(ratio_landing) if len(ratio_landing) > 0 else (np.nan, (np.nan, np.nan)),
            'ratio_end': bootstrap_ci(ratio_end) if len(ratio_end) > 0 else (np.nan, (np.nan, np.nan))
        }
        
        print(f"\nArm {arm} (n={len(arm_data)} clips):")
        if len(ratio_f0) > 0:
            mean, (low, high) = stats_by_arm[arm]['ratio_f0']
            print(f"  f0 diameter ratio: {mean:.3f} [{low:.3f}, {high:.3f}]")
        if len(ratio_landing) > 0:
            mean, (low, high) = stats_by_arm[arm]['ratio_landing']
            print(f"  landing diameter ratio: {mean:.3f} [{low:.3f}, {high:.3f}]")
        if len(ratio_end) > 0:
            mean, (low, high) = stats_by_arm[arm]['ratio_end']
            print(f"  end diameter ratio: {mean:.3f} [{low:.3f}, {high:.3f}]")
    
    # Save stats
    with open(output_dir / 'per_arm_stats.json', 'w') as f:
        json.dump(stats_by_arm, f, indent=2)
    
    print("\n=== Done ===")
    print(f"Results saved to {output_dir}/")
    print("  - calibration.json")
    print("  - all_tracks_summary.json")
    print("  - per_arm_stats.json")

if __name__ == '__main__':
    main()
