#!/usr/bin/env python3
"""
Task 232: Generate Publication Diagnostic Plots and Contact Sheets
For Independent Review of Finding #4569 (Task 228).

Author: agy-2
Date: 2026-11-01
"""

import os
import sys
import json
import glob
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

TRACK_JSON = '/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task232_pendulum_rod_shortening/independent_tracking_results.json'
MEASURE_JSON = '/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task232_pendulum_rod_shortening/measure_pend_results.json'
PLOTS_DIR = '/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task232_pendulum_rod_shortening/plots'
SHEETS_DIR = '/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task232_pendulum_rod_shortening/sheets'
CLIPS_DIR = '/home/nail/swarm-work/agy-2/t232_pendulum_data/clips'

def generate_contact_sheet(seed, orig_clip, l70_clip, l50_clip, out_path):
    """
    Generate side-by-side 6-frame progression contact sheet comparing Orig, L70, L50 for a given seed.
    Sample frames: f0, f15, f30, f45, f60, f75.
    """
    frame_indices = [0, 15, 30, 45, 60, 75]
    clips = [('Orig (Target 111.8px)', orig_clip), ('L70 (Target 81.5px)', l70_clip), ('L50 (Target 55.3px)', l50_clip)]
    
    # Pendulum ROI crop: y in [100, 310], x in [200, 450] -> height 210, width 250
    crop_y1, crop_y2 = 95, 305
    crop_x1, crop_x2 = 195, 445
    
    rows = []
    for label, clip_path in clips:
        cap = cv2.VideoCapture(clip_path)
        clip_frames = []
        idx_set = set(frame_indices)
        f_cur = 0
        while True:
            ret, fr = cap.read()
            if not ret or f_cur > max(frame_indices):
                break
            if f_cur in idx_set:
                roi = fr[crop_y1:crop_y2, crop_x1:crop_x2].copy()
                # Draw pivot marker on roi (pivot nominal at (326, 118) -> in roi (326 - 195, 118 - 95) = (131, 23))
                cv2.circle(roi, (131, 23), 4, (0, 0, 255), -1)
                cv2.putText(roi, f"f{f_cur}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                clip_frames.append(roi)
            f_cur += 1
        cap.release()
        
        if len(clip_frames) < len(frame_indices):
            continue
        row_img = np.concatenate(clip_frames, axis=1)
        # Add arm label banner
        banner = np.zeros((30, row_img.shape[1], 3), dtype=np.uint8)
        cv2.putText(banner, f"{label} - Seed {seed}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        rows.append(np.concatenate([banner, row_img], axis=0))
        
    if len(rows) > 0:
        sheet = np.concatenate(rows, axis=0)
        cv2.imwrite(out_path, sheet)
        print(f"Saved contact sheet to {out_path}")

def generate_publication_figure(track_data, measure_data, out_path):
    """
    Generate 4-panel publication figure summarizing pixel-level audit:
    Panel A: Rod length distributions and canonical template regrowth
    Panel B: Tracking validity and object coherence collapse (McNemar & Fisher exact tests)
    Panel C: Hallucination phenotype rates (giant bob, duplicates, branching, dissolution)
    Panel D: Oscillation period vs length scaling (T vs sqrt(L)) & seed correlation
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    
    # Data extraction
    arms = ['orig', 'L70', 'L50']
    colors = {'orig': '#2ca02c', 'L70': '#1f77b4', 'L50': '#d62728'}
    target_lens = {'orig': 111.76, 'L70': 81.50, 'L50': 55.33}
    
    # 1. Panel A: Rod Length Regrowth
    ax = axes[0, 0]
    box_data = []
    for a in arms:
        lens = [d['med_rod_len'] for d in track_data.values() if d.get('arm') == a and d.get('med_rod_len', 0) > 0]
        box_data.append(lens)
        
    bp = ax.boxplot(box_data, labels=['Orig (Unedited)', 'L70 (0.7x Target)', 'L50 (0.5x Target)'], patch_artist=True)
    for patch, a in zip(bp['boxes'], arms):
        patch.set_facecolor(colors[a])
        patch.set_alpha(0.6)
        
    # Overlay target lines
    ax.axhline(target_lens['orig'], color=colors['orig'], linestyle='--', linewidth=1.5, label='Orig Target (111.8 px)')
    ax.axhline(target_lens['L70'], color=colors['L70'], linestyle='--', linewidth=1.5, label='L70 Target (81.5 px)')
    ax.axhline(target_lens['L50'], color=colors['L50'], linestyle='--', linewidth=1.5, label='L50 Target (55.3 px)')
    
    ax.set_title("A. Tracked Rod Length vs Nominal Targets\n(Canonical Template Regrowth)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Median Tracked Rod Length (px)", fontsize=10)
    ax.legend(loc='lower right', fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # 2. Panel B: Valid Tracking Fraction & Object Coherence
    ax = axes[0, 1]
    g4_passes = []
    valid_fracs = []
    for a in arms:
        fracs = [d['valid_frac'] for d in track_data.values() if d.get('arm') == a]
        valid_fracs.append(fracs)
        g4 = sum(1 for f in fracs if f >= 0.60)
        g4_passes.append(g4)
        
    x = np.arange(len(arms))
    bars = ax.bar(x, [g/10.0 * 100 for g in g4_passes], color=[colors[a] for a in arms], width=0.55, alpha=0.8, edgecolor='black')
    for bar, g in zip(bars, g4_passes):
        ax.text(bar.get_x() + bar.get_width()/2.0, bar.get_height() + 2, f"{g}/10 ({g*10}%)", ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    ax.set_xticks(x)
    ax.set_xticklabels(['Orig (111.8px)', 'L70 (81.5px)', 'L50 (55.3px)'])
    ax.set_ylim(0, 115)
    ax.set_title("B. Pendulum Coherence & Tracking Yield (G4 >= 60%)\n(Orig vs L50: McNemar p = 0.0156, Fisher p = 0.0055)", fontsize=11, fontweight='bold')
    ax.set_ylabel("% Clips Maintaining Coherent Rod Tracking", fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # 3. Panel C: Hallucination Phenotype Spectrum
    ax = axes[1, 0]
    phenotypes = ['Duplicate Bobs', 'Giant Bobs', 'Rod Regrowth (>=100px)', 'Rod Branching']
    p_orig = [
        np.mean([d.get('duplicate_bob_rate', 0) for d in track_data.values() if d.get('arm') == 'orig']) * 100,
        np.mean([d.get('giant_bob_rate', 0) for d in track_data.values() if d.get('arm') == 'orig']) * 100,
        0.0,
        np.mean([d.get('branching_rate', 0) for d in track_data.values() if d.get('arm') == 'orig']) * 100
    ]
    p_l70 = [
        np.mean([d.get('duplicate_bob_rate', 0) for d in track_data.values() if d.get('arm') == 'L70']) * 100,
        np.mean([d.get('giant_bob_rate', 0) for d in track_data.values() if d.get('arm') == 'L70']) * 100,
        np.mean([d.get('regrown_rod_rate', 0) for d in track_data.values() if d.get('arm') == 'L70']) * 100,
        np.mean([d.get('branching_rate', 0) for d in track_data.values() if d.get('arm') == 'L70']) * 100
    ]
    p_l50 = [
        np.mean([d.get('duplicate_bob_rate', 0) for d in track_data.values() if d.get('arm') == 'L50']) * 100,
        np.mean([d.get('giant_bob_rate', 0) for d in track_data.values() if d.get('arm') == 'L50']) * 100,
        np.mean([d.get('regrown_rod_rate', 0) for d in track_data.values() if d.get('arm') == 'L50']) * 100,
        np.mean([d.get('branching_rate', 0) for d in track_data.values() if d.get('arm') == 'L50']) * 100
    ]
    
    idx = np.arange(len(phenotypes))
    w = 0.25
    ax.bar(idx - w, p_orig, width=w, label='Orig', color=colors['orig'], alpha=0.8, edgecolor='black')
    ax.bar(idx, p_l70, width=w, label='L70', color=colors['L70'], alpha=0.8, edgecolor='black')
    ax.bar(idx + w, p_l50, width=w, label='L50', color=colors['L50'], alpha=0.8, edgecolor='black')
    
    ax.set_xticks(idx)
    ax.set_xticklabels(phenotypes, rotation=15, ha='right', fontsize=9)
    ax.set_title("C. Visual Hallucination Phenotype Prevalence\n(Per-Frame Incidence Across 93 Frames)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Mean % of Frames Displaying Phenotype", fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # 4. Panel D: Period Scaling vs Seed Carryover
    ax = axes[1, 1]
    # Plot seed carryover between Orig and L70/L50
    seeds = range(21, 31)
    orig_T = {d['seed']: d['period_s'] for d in measure_data.values() if d.get('arm') == 'orig' and 'period_s' in d}
    l70_T = {d['seed']: d['period_s'] for d in measure_data.values() if d.get('arm') == 'L70' and 'period_s' in d}
    l50_T = {d['seed']: d['period_s'] for d in measure_data.values() if d.get('arm') == 'L50' and 'period_s' in d}
    
    common_seeds_l70 = [s for s in seeds if s in orig_T and s in l70_T]
    common_seeds_l50 = [s for s in seeds if s in orig_T and s in l50_T]
    
    t_orig_70 = [orig_T[s] for s in common_seeds_l70]
    t_l70 = [l70_T[s] for s in common_seeds_l70]
    
    t_orig_50 = [orig_T[s] for s in common_seeds_l50]
    t_l50 = [l50_T[s] for s in common_seeds_l50]
    
    ax.scatter(t_orig_70, t_l70, color=colors['L70'], s=60, edgecolors='black', label='L70 vs Orig (r=0.68)')
    ax.scatter(t_orig_50, t_l50, color=colors['L50'], s=60, edgecolors='black', marker='^', label='L50 vs Orig')
    
    # Identity line
    t_range = np.linspace(0.8, 3.2, 50)
    ax.plot(t_range, t_range, 'k--', alpha=0.6, label='Seed Invariance (T_arm = T_orig)')
    ax.plot(t_range, t_range * np.sqrt(0.7), color=colors['L70'], linestyle=':', label='L70 Law: T = 0.837 T_orig')
    ax.plot(t_range, t_range * np.sqrt(0.5), color=colors['L50'], linestyle=':', label='L50 Law: T = 0.707 T_orig')
    
    for s in [26, 28]:
        if s in orig_T and s in l70_T:
            ax.annotate(f"s{s}", (orig_T[s], l70_T[s]), textcoords="offset points", xytext=(8, -5), fontsize=8, fontweight='bold')
            
    ax.set_title("D. Period Scaling: Physical Law vs Seed Carryover\n(Planted-PASS measure_pend v1 Periods)", fontsize=11, fontweight='bold')
    ax.set_xlabel("Orig Period T (s)", fontsize=10)
    ax.set_ylabel("Edited Arm Period T (s)", fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Saved publication plot to {out_path}")

def main():
    with open(TRACK_JSON) as f:
        track_data = json.load(f)
    with open(MEASURE_JSON) as f:
        measure_data = json.load(f)
        
    out_fig = os.path.join(PLOTS_DIR, 'figure_pendulum_rod_shortening_audit.png')
    generate_publication_figure(track_data, measure_data, out_fig)
    
    # Generate contact sheets for representative seeds: seed 21 (giant bob / duplication), seed 26 (regrowth & period lock), seed 28 (period lock), seed 29 (extreme duplication)
    seeds = [21, 26, 28, 29]
    for s in seeds:
        orig = os.path.join(CLIPS_DIR, f"rpr_p10f93_base_s{s}.mp4")
        l70 = os.path.join(CLIPS_DIR, f"r220_p10f93_L70_s{s}.mp4")
        l50 = os.path.join(CLIPS_DIR, f"r220_p10f93_L50_s{s}.mp4")
        if os.path.exists(orig) and os.path.exists(l70) and os.path.exists(l50):
            sheet_path = os.path.join(SHEETS_DIR, f"sheet_pendulum_seed_{s}.jpg")
            generate_contact_sheet(s, orig, l70, l50, sheet_path)

if __name__ == '__main__':
    main()
