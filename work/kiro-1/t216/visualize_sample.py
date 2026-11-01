#!/usr/bin/env python3
"""Quick QC visualization of a few sample tracks."""
import cv2
import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

def visualize_track(video_path, output_path):
    """Create a montage showing tracked ball at key frames."""
    # Load tracking results if they exist
    stem = video_path.stem
    
    # Run quick track
    from track_ball import track_ball_template, detect_ball_at_position
    
    cap = cv2.VideoCapture(str(video_path))
    ret, frame = cap.read()
    h, w = frame.shape[:2]
    cap.release()
    
    if not ret:
        return
    
    # Detect at top
    cx, cy, d = detect_ball_at_position(frame, w//2, h//3, search_radius=200)
    print(f"{video_path.name}: f0 detected at ({cx:.0f}, {cy:.0f}), d={d:.0f}px")
    
    # Track
    results = track_ball_template(video_path, (cx, cy, d))
    if not results:
        return
    
    # Select frames to visualize
    n_frames = len(results)
    sample_frames = [0, n_frames//4, n_frames//2, 3*n_frames//4, n_frames-1]
    
    cap = cv2.VideoCapture(str(video_path))
    
    fig, axes = plt.subplots(1, 5, figsize=(20, 4))
    
    for i, (ax, frame_idx) in enumerate(zip(axes, sample_frames)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue
        
        track = results[frame_idx]
        cx, cy, diam = track['cx'], track['cy'], track['diameter']
        
        # Draw circle
        frame_copy = frame.copy()
        cv2.circle(frame_copy, (int(cx), int(cy)), int(diam/2), (0, 255, 0), 2)
        cv2.circle(frame_copy, (int(cx), int(cy)), 3, (0, 0, 255), -1)
        
        # Convert to RGB for matplotlib
        frame_rgb = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
        
        ax.imshow(frame_rgb)
        ax.set_title(f"f{frame_idx}\nd={diam:.0f}px")
        ax.axis('off')
    
    cap.release()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Saved QC image to {output_path}")

def main():
    work_dir = Path(__file__).parent
    clips_dir = work_dir / 'clips'
    qc_dir = work_dir / 'qc'
    qc_dir.mkdir(exist_ok=True)
    
    # Sample a few clips from each arm
    samples = [
        'clips/t141_b1dd33_F_s1.mp4',
        'clips/t141_b1dd33_QT_s1.mp4',
        'clips/t141_b1dd33_N_s1.mp4',
    ]
    
    for sample in samples:
        video_path = work_dir / sample
        if not video_path.exists():
            continue
        
        output_path = qc_dir / f"qc_{video_path.stem}.png"
        visualize_track(video_path, output_path)
    
    # Also visualize GAUGE calibration
    gauge_dir = work_dir.parent / 'gauge'
    for gauge_file in ['10.mp4', '12.mp4']:
        gauge_path = gauge_dir / gauge_file
        if gauge_path.exists():
            output_path = qc_dir / f"qc_gauge_{gauge_path.stem}.png"
            visualize_track(gauge_path, output_path)

if __name__ == '__main__':
    main()
