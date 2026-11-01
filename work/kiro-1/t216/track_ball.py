#!/usr/bin/env python3
"""
Independent ball tracker for task 216.
Seed at known f0 position, follow frame-by-frame with template matching + circle fit.
Record diameter vs frame and vs y-position for perspective calibration.
"""
import cv2
import numpy as np
import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt

def load_first_frame_position(json_path):
    """Extract f0 ball position from GAUGE JSON or sidecar."""
    with open(json_path) as f:
        data = json.load(f)
    
    # For GAUGE JSON format
    if 'annotations' in data:
        # Find the ball annotation at frame 0
        for ann in data['annotations']:
            if ann.get('frame') == 0 and ann.get('object_type') == 'ball':
                center = ann.get('center')
                if center:
                    return (float(center['x']), float(center['y']))
        # Fallback: get bbox from first annotation
        if data['annotations']:
            bbox = data['annotations'][0].get('bbox', {})
            x = bbox.get('x', 0)
            y = bbox.get('y', 0)
            w = bbox.get('width', 50)
            h = bbox.get('height', 50)
            return (x + w/2, y + h/2)
    
    # For cosmos sidecars, we'll need to detect manually
    return None

def detect_ball_at_position(frame, cx, cy, search_radius=50):
    """Detect ball at approximate position using circle detection."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # Crop region around expected position
    x1 = max(0, int(cx - search_radius))
    y1 = max(0, int(cy - search_radius))
    x2 = min(w, int(cx + search_radius))
    y2 = min(h, int(cy + search_radius))
    
    roi = gray[y1:y2, x1:x2]
    
    # Try Hough circle detection
    circles = cv2.HoughCircles(
        roi,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=50,
        param2=30,
        minRadius=10,
        maxRadius=50
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        # Find closest circle to center
        best_circle = None
        best_dist = float('inf')
        for circle in circles[0]:
            c_x, c_y, r = circle
            dist = np.hypot(c_x - search_radius, c_y - search_radius)
            if dist < best_dist:
                best_dist = dist
                best_circle = circle
        
        if best_circle is not None:
            c_x, c_y, r = best_circle
            return (x1 + c_x, y1 + c_y, 2*r)
    
    # Fallback: use darkest region
    blurred = cv2.GaussianBlur(roi, (11, 11), 0)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred)
    
    # Estimate radius from dark region
    _, thresh = cv2.threshold(blurred, min_val + (max_val - min_val) * 0.3, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest = max(contours, key=cv2.contourArea)
        (c_x, c_y), radius = cv2.minEnclosingCircle(largest)
        return (x1 + c_x, y1 + c_y, 2*radius)
    
    # Ultimate fallback
    return (cx, cy, 30.0)

def track_ball_template(video_path, initial_pos, template_size=40):
    """Track ball using template matching + circle refinement."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    
    results = []
    frame_idx = 0
    prev_cx, prev_cy, prev_d = initial_pos
    template = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if frame_idx == 0:
            # Initialize template from first frame
            x1 = max(0, int(prev_cx - template_size//2))
            y1 = max(0, int(prev_cy - template_size//2))
            x2 = min(w, int(prev_cx + template_size//2))
            y2 = min(h, int(prev_cy + template_size//2))
            template = gray[y1:y2, x1:x2].copy()
            
            results.append({
                'frame': frame_idx,
                'cx': prev_cx,
                'cy': prev_cy,
                'diameter': prev_d,
                'method': 'init'
            })
        else:
            # Template matching in search region
            search_radius = max(100, int(prev_d * 3))
            x1 = max(0, int(prev_cx - search_radius))
            y1 = max(0, int(prev_cy - search_radius))
            x2 = min(w, int(prev_cx + search_radius))
            y2 = min(h, int(prev_cy + search_radius))
            
            search_roi = gray[y1:y2, x1:x2]
            
            if template.shape[0] > 0 and template.shape[1] > 0 and \
               search_roi.shape[0] >= template.shape[0] and \
               search_roi.shape[1] >= template.shape[1]:
                
                # Template match
                res = cv2.matchTemplate(search_roi, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                
                # Convert to full frame coordinates
                match_cx = x1 + max_loc[0] + template.shape[1] // 2
                match_cy = y1 + max_loc[1] + template.shape[0] // 2
                
                # Refine with circle detection around match
                refine_size = int(prev_d * 1.5)
                rx1 = max(0, int(match_cx - refine_size))
                ry1 = max(0, int(match_cy - refine_size))
                rx2 = min(w, int(match_cx + refine_size))
                ry2 = min(h, int(match_cy + refine_size))
                
                refine_roi = gray[ry1:ry2, rx1:rx2]
                
                # Circle fit
                blurred = cv2.GaussianBlur(refine_roi, (9, 9), 0)
                circles = cv2.HoughCircles(
                    blurred,
                    cv2.HOUGH_GRADIENT,
                    dp=1,
                    minDist=20,
                    param1=50,
                    param2=20,
                    minRadius=int(prev_d * 0.5),
                    maxRadius=int(prev_d * 2)
                )
                
                if circles is not None:
                    circles = np.uint16(np.around(circles))
                    # Use first/best circle
                    c_x, c_y, r = circles[0][0]
                    cx = rx1 + c_x
                    cy = ry1 + c_y
                    diameter = 2 * r
                else:
                    cx = match_cx
                    cy = match_cy
                    diameter = prev_d
                
                # Update template periodically
                if frame_idx % 10 == 0:
                    tx1 = max(0, int(cx - template_size//2))
                    ty1 = max(0, int(cy - template_size//2))
                    tx2 = min(w, int(cx + template_size//2))
                    ty2 = min(h, int(cy + template_size//2))
                    if tx2 > tx1 and ty2 > ty1:
                        template = gray[ty1:ty2, tx1:tx2].copy()
                
                results.append({
                    'frame': frame_idx,
                    'cx': float(cx),
                    'cy': float(cy),
                    'diameter': float(diameter),
                    'method': 'track',
                    'match_score': float(max_val)
                })
                
                prev_cx, prev_cy, prev_d = cx, cy, diameter
            else:
                # Can't track, use previous
                results.append({
                    'frame': frame_idx,
                    'cx': prev_cx,
                    'cy': prev_cy,
                    'diameter': prev_d,
                    'method': 'lost'
                })
        
        frame_idx += 1
    
    cap.release()
    return results

def calibrate_perspective(real_video_path, real_json_path, known_diameter_m=0.049):
    """Calibrate perspective using real GAUGE video with known ball size."""
    # GAUGE ball diameter is 49mm = 0.049m
    initial_pos_tuple = load_first_frame_position(real_json_path)
    
    if initial_pos_tuple is None:
        # Manually detect
        cap = cv2.VideoCapture(str(real_video_path))
        ret, frame = cap.read()
        cap.release()
        if ret:
            cx, cy, d = detect_ball_at_position(frame, frame.shape[1]//2, frame.shape[0]//2, 200)
            initial_pos_tuple = (cx, cy, d)
        else:
            return None
    else:
        # Need to estimate diameter
        cap = cv2.VideoCapture(str(real_video_path))
        ret, frame = cap.read()
        cap.release()
        if ret:
            cx, cy = initial_pos_tuple
            _, _, d = detect_ball_at_position(frame, cx, cy, 50)
            initial_pos_tuple = (cx, cy, d)
    
    results = track_ball_template(real_video_path, initial_pos_tuple)
    if not results:
        return None
    
    # Fit diameter vs y position
    valid_tracks = [r for r in results if r.get('method') in ['init', 'track']]
    if len(valid_tracks) < 10:
        return None
    
    y_positions = np.array([r['cy'] for r in valid_tracks])
    diameters_px = np.array([r['diameter'] for r in valid_tracks])
    
    # Linear fit: diameter_px = a + b * y
    # This gives us px_per_m as a function of y
    coeffs = np.polyfit(y_positions, diameters_px, 1)
    
    return {
        'poly_coeffs': coeffs.tolist(),  # [b, a] for d = a + b*y
        'known_diameter_m': known_diameter_m,
        'y_range': [float(y_positions.min()), float(y_positions.max())],
        'diameter_px_range': [float(diameters_px.min()), float(diameters_px.max())],
        'mean_diameter_px': float(diameters_px.mean())
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python track_ball.py <video.mp4> [f0_x] [f0_y] [f0_diameter]")
        sys.exit(1)
    
    video_path = Path(sys.argv[1])
    
    if len(sys.argv) >= 5:
        initial_pos = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
    else:
        # Try to load from sidecar
        json_path = video_path.with_suffix('.json')
        if json_path.exists():
            pos = load_first_frame_position(json_path)
            if pos:
                # Detect diameter
                cap = cv2.VideoCapture(str(video_path))
                ret, frame = cap.read()
                cap.release()
                if ret:
                    cx, cy = pos
                    _, _, d = detect_ball_at_position(frame, cx, cy, 50)
                    initial_pos = (cx, cy, d)
                else:
                    print("Failed to read video")
                    sys.exit(1)
            else:
                print("Could not extract position from JSON")
                sys.exit(1)
        else:
            print("Need initial position or sidecar JSON")
            sys.exit(1)
    
    results = track_ball_template(video_path, initial_pos)
    
    if results:
        output_path = video_path.parent / f"{video_path.stem}_track.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Tracked {len(results)} frames -> {output_path}")
    else:
        print("Tracking failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
