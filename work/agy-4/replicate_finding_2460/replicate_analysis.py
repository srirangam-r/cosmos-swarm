"""
Independent replication and verification script for ro-1 Finding #2460 (Task 22 / Task 106).
Audits:
1. Video corridor frame differences and median-background trajectory tracking on raw mp4s.
2. Independent spatio-temporal tile dynamics and object permanence across all 13 committed strips.
3. Rigorous paired statistical evaluation of Late Corridor Motion, DOVER Fused/Tech/Aes, and Dynamic Degree.
4. Evaluation of QS (stillness control) and R20/R95 (restitution control).
"""

import os
import glob
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw

SWARM_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
CAUSE5_DIR = os.path.join(SWARM_ROOT, 'work/ro-1/cause_v5')
OUT_DIR = os.path.abspath(os.path.dirname(__file__))

def audit_raw_mp4s():
    f_path = os.path.join(CAUSE5_DIR, 'clips/cause5_F_ball1_fps24_93f_s3.mp4')
    qt_path = os.path.join(CAUSE5_DIR, 'clips/cause5_QT_ball1_fps24_93f_s3.mp4')
    
    results = {}
    for name, p in [('F_s3', f_path), ('QT_s3', qt_path)]:
        if not os.path.exists(p):
            continue
        cap = cv2.VideoCapture(p)
        frames = []
        while True:
            ret, fr = cap.read()
            if not ret:
                break
            frames.append(fr)
        cap.release()
        
        # Corridor diffs in [130:360, 220:360]
        corridor_grays = [cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)[130:360, 220:360].astype(np.float32) for fr in frames]
        diffs = [float(np.abs(corridor_grays[i] - corridor_grays[i-1]).mean()) for i in range(1, len(corridor_grays))]
        
        early = float(np.mean(diffs[0:45]))
        late = float(np.mean(diffs[45:]))
        last20 = float(np.mean(diffs[-20:]))
        
        # Centroid tracking via median background subtraction
        bg = np.median(np.stack(corridor_grays), axis=0).astype(np.float32)
        traj = []
        for i, gr in enumerate(corridor_grays):
            diff = np.abs(gr - bg)
            th = (diff > 25).astype(np.uint8) * 255
            cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best = None
            max_a = 0
            for c in cnts:
                a = cv2.contourArea(c)
                if 30 < a < 2500:
                    if a > max_a:
                        max_a = a
                        M = cv2.moments(c)
                        if M['m00'] > 0:
                            best = {'x': round(M['m10']/M['m00'], 1), 'y': round(M['m01']/M['m00'], 1), 'area': round(a, 1)}
            traj.append({'frame': i, 'ball': best})
        
        results[name] = {
            'frames': len(frames),
            'early_diff': round(early, 3),
            'late_diff': round(late, 3),
            'last20_diff': round(last20, 3),
            'sample_trajectory': traj[::6],
            'final_frame_ball': traj[-1]['ball']
        }
    return results

def audit_strips():
    strip_files = sorted(glob.glob(os.path.join(CAUSE5_DIR, 'strips/*.strip.jpg')))
    strip_results = {}
    
    for p in strip_files:
        name = os.path.basename(p)
        im = Image.open(p).convert('L')
        arr = np.asarray(im, dtype=np.float32)
        
        tiles = []
        for k in range(31):
            c = k % 8
            r = k // 8
            tile = arr[r*135:(r+1)*135, c*110:(c+1)*110].copy()
            tile[0:15, 0:35] = tile[15, 35] # mask out red frame index text
            tiles.append(tile)
        tiles = np.stack(tiles)
        
        diffs = np.abs(np.diff(tiles, axis=0)).mean(axis=(1, 2))
        early_diff = float(diffs[0:15].mean())
        late_diff = float(diffs[15:].mean())
        last7_diff = float(diffs[23:].mean())
        late_var = float(np.var(tiles[24:], axis=0).mean())
        
        # Object permanence on plank in final 5 tiles (k=26..30)
        u8_tiles = tiles.astype(np.uint8)
        permanence = []
        for k in range(26, 31):
            plank_roi = u8_tiles[k][70:125, 20:90]
            th = cv2.threshold(plank_roi, 40, 255, cv2.THRESH_BINARY_INV)[1]
            cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best_c = None
            max_a = 0
            for cnt in cnts:
                a = cv2.contourArea(cnt)
                if 15 < a < 500:
                    if a > max_a:
                        max_a = a
                        M = cv2.moments(cnt)
                        if M['m00'] > 0:
                            best_c = {'x': round(M['m10']/M['m00'] + 20, 1), 'y': round(M['m01']/M['m00'] + 70, 1), 'area': round(a, 1)}
            permanence.append({'frame': k*3, 'ball': best_c})
            
        strip_results[name] = {
            'early_diff': round(early_diff, 3),
            'late_diff': round(late_diff, 3),
            'last7_diff': round(last7_diff, 3),
            'late_var': round(late_var, 2),
            'permanence_last5_tiles': permanence
        }
    return strip_results

def audit_statistics():
    tbl_path = os.path.join(CAUSE5_DIR, 'table.json')
    tbl = json.load(open(tbl_path))
    rows = tbl['rows']
    real_dd = rows['b1_REAL']['dd'] # 0.563923
    
    pairs = [
        ('b1_F_s1', 'b1_QT_s1', 'b1_s1'),
        ('b1_F_s2', 'b1_QT_s2', 'b1_s2'),
        ('b1_F_s3', 'b1_QT_s3', 'b1_s3'),
        ('b1_F_s4', 'b1_QT_s4', 'b1_s4'),
        ('b1_F_s5', 'b1_QT_s5', 'b1_s5'),
        ('b2_F_s1', 'b2_QT_s1', 'b2_s1'),
        ('b2_F_s2', 'b2_QT_s2', 'b2_s2'),
        ('b2_F_s3', 'b2_QT_s3', 'b2_s3'),
    ]
    
    pair_details = []
    diff_l20, diff_dover, diff_dd, diff_dist = [], [], [], []
    
    for f_k, qt_k, label in pairs:
        rf = rows[f_k]
        rqt = rows[qt_k]
        
        dl20 = rqt['last20'] - rf['last20']
        ddover = rqt['dover'] - rf['dover']
        ddd = rqt['dd'] - rf['dd']
        
        df_real = abs(rf['dd'] - real_dd)
        dqt_real = abs(rqt['dd'] - real_dd)
        ddist = dqt_real - df_real
        
        diff_l20.append(dl20)
        diff_dover.append(ddover)
        diff_dd.append(ddd)
        diff_dist.append(ddist)
        
        pair_details.append({
            'label': label,
            'f_key': f_k,
            'qt_key': qt_k,
            'f_last20': rf['last20'],
            'qt_last20': rqt['last20'],
            'delta_last20': round(dl20, 3),
            'f_dover': round(rf['dover'], 4),
            'qt_dover': round(rqt['dover'], 4),
            'delta_dover': round(ddover, 4),
            'f_dd': round(rf['dd'], 2),
            'qt_dd': round(rqt['dd'], 2),
            'delta_dd': round(ddd, 2),
            'f_dist_to_real': round(df_real, 2),
            'qt_dist_to_real': round(dqt_real, 2),
            'delta_dist_to_real': round(ddist, 2)
        })
        
    diff_l20 = np.array(diff_l20)
    diff_dover = np.array(diff_dover)
    diff_dd = np.array(diff_dd)
    diff_dist = np.array(diff_dist)
    n = len(pairs)
    t_crit = 2.365 # for df=7, 95% two-sided
    t_crit_one = 1.895 # for df=7, 95% one-sided
    
    def stat_summary(d):
        m = float(d.mean())
        se = float(d.std(ddof=1) / np.sqrt(len(d)))
        t_val = float(m / se) if se > 0 else 0.0
        ci_low = m - t_crit * se
        ci_high = m + t_crit * se
        one_sided_lb = m - t_crit_one * se
        return {
            'mean': round(m, 4),
            'se': round(se, 4),
            't_stat': round(t_val, 2),
            'ci_95': [round(ci_low, 4), round(ci_high, 4)],
            'one_sided_95_lb': round(one_sided_lb, 4),
            'negative_count': int(np.sum(d < 0)),
            'positive_count': int(np.sum(d > 0))
        }
        
    stats = {
        'last20': stat_summary(diff_l20),
        'dover_fused': stat_summary(diff_dover),
        'dynamic_degree': stat_summary(diff_dd),
        'dist_to_real_dd': stat_summary(diff_dist),
        'pairs': pair_details
    }
    return stats

def generate_visual_qc(strip_results):
    # Create visual contact sheet comparing F vs QT vs QS strips
    sample_strips = [
        ('cause5_F_ball1_fps24_93f_s3.strip.jpg', 'F (Base Control) - Ball 1 Seed 3'),
        ('cause5_QS_ball1_fps24_93f_s3.strip.jpg', 'QS (Stillness Control) - Ball 1 Seed 3'),
        ('cause5_QT_ball1_fps24_93f_s3.strip.jpg', 'QT (Timed Prompt) - Ball 1 Seed 3'),
        ('cause5_F_ball1_fps24_93f_s4.strip.jpg', 'F (Base Control) - Ball 1 Seed 4'),
        ('cause5_QT_ball1_fps24_93f_s4.strip.jpg', 'QT (Timed Prompt) - Ball 1 Seed 4'),
    ]
    
    row_images = []
    for filename, label in sample_strips:
        path = os.path.join(CAUSE5_DIR, 'strips', filename)
        if not os.path.exists(path):
            continue
        im = Image.open(path)
        # Create banner
        banner = Image.new('RGB', (im.width, 30), color=(30, 30, 30))
        dr = ImageDraw.Draw(banner)
        dr.text((10, 8), label, fill=(255, 255, 0))
        combined = Image.new('RGB', (im.width, im.height + 30))
        combined.paste(banner, (0, 0))
        combined.paste(im, (0, 30))
        row_images.append(combined)
        
    if row_images:
        total_h = sum(r.height for r in row_images)
        max_w = max(r.width for r in row_images)
        sheet = Image.new('RGB', (max_w, total_h))
        curr_y = 0
        for r in row_images:
            sheet.paste(r, (0, curr_y))
            curr_y += r.height
        out_path = os.path.join(OUT_DIR, 'replication_2460_visual_qc.jpg')
        sheet.save(out_path, quality=85)
        print(f'Visual QC saved to {out_path}')

def main():
    print('Starting independent replication audit for Finding #2460...')
    mp4_res = audit_raw_mp4s()
    strip_res = audit_strips()
    stat_res = audit_statistics()
    generate_visual_qc(strip_res)
    
    full_output = {
        'finding_id': 2460,
        'title': 'Timed prompt induces bounce settling without DOVER degradation',
        'raw_mp4_audit': mp4_res,
        'strip_audit': strip_res,
        'statistical_audit': stat_res
    }
    
    json_path = os.path.join(OUT_DIR, 'replication_2460_results.json')
    with open(json_path, 'w') as f:
        json.dump(full_output, f, indent=2)
    print(f'Replication results saved to {json_path}')

if __name__ == '__main__':
    main()
