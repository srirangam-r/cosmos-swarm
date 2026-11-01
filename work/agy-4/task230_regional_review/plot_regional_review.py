#!/usr/bin/env python3
"""
Generate publication figure for Task 230: Independent Review of Finding #4460 (Task 217).
Plots:
Panel A: Late-frame pixel motion maps (F, QT, N) showing localized suppression.
Panel B: Forest plot of regional QT/F late-motion ratios with 95% bootstrap CIs.
Panel C: Spatial breakdown of absolute motion drop (% share of total reduction).
Panel D: Gripper vs Background motion across arms compared to real video ground truth.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def main():
    # Load data
    with open('independent_review_results.json') as f:
        res = json.load(f)
    
    mm = np.load('motionmaps.npz')
    F_map = mm['F']
    QT_map = mm['QT']
    N_map = mm['N']
    
    fig = plt.figure(figsize=(16, 12), dpi=150)
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)
    
    # -------------------------------------------------------------
    # Panel A: Spatial Late Motion Heatmaps
    # -------------------------------------------------------------
    ax_a = fig.add_subplot(gs[0, 0])
    
    # Create combined display: stack F, QT, N side by side
    vmax = np.percentile(F_map, 99.5)
    combined = np.hstack([F_map, QT_map, N_map])
    
    im = ax_a.imshow(combined, cmap='inferno', vmin=0, vmax=vmax, aspect='auto')
    
    # Add separator lines between the three arms
    ax_a.axvline(104, color='cyan', linestyle='--', linewidth=1.5)
    ax_a.axvline(208, color='cyan', linestyle='--', linewidth=1.5)
    
    # Label the three arms
    ax_a.text(52, -4, 'Base F (Undamped)', color='black', fontsize=11, fontweight='bold', ha='center')
    ax_a.text(156, -4, 'Prompt QT (Timed Settle)', color='darkgreen', fontsize=11, fontweight='bold', ha='center')
    ax_a.text(260, -4, 'Control N (Neutral)', color='navy', fontsize=11, fontweight='bold', ha='center')
    
    # Draw region boxes on the Base F panel
    # LOW: x 8-63, y 34-59
    rect_low = patches.Rectangle((8, 34), 56, 26, linewidth=1.5, edgecolor='#00ff00', facecolor='none')
    # AIR: x 22-45, y 14-33
    rect_air = patches.Rectangle((22, 14), 24, 20, linewidth=1.5, edgecolor='#ff00ff', facecolor='none')
    # GRIP: x 22-45, y 0-13
    rect_grip = patches.Rectangle((22, 0), 24, 14, linewidth=1.5, edgecolor='#ff3333', facecolor='none')
    # ARM: x 46-61, y 0-33
    rect_arm = patches.Rectangle((46, 0), 16, 34, linewidth=1.5, edgecolor='#ff9900', facecolor='none')
    # BG: x 64-103, y 0-59
    rect_bg = patches.Rectangle((64, 0), 40, 60, linewidth=1.5, edgecolor='#33ccff', facecolor='none')
    
    ax_a.add_patch(rect_low)
    ax_a.add_patch(rect_air)
    ax_a.add_patch(rect_grip)
    ax_a.add_patch(rect_arm)
    ax_a.add_patch(rect_bg)
    
    ax_a.text(10, 48, 'LOW (Plank)', color='#00ff00', fontsize=8, fontweight='bold')
    ax_a.text(24, 25, 'AIR', color='#ff00ff', fontsize=8, fontweight='bold')
    ax_a.text(24, 9, 'GRIP', color='#ff3333', fontsize=8, fontweight='bold')
    ax_a.text(48, 18, 'ARM', color='#ff9900', fontsize=8, fontweight='bold')
    ax_a.text(72, 30, 'BG (Null Control)', color='#33ccff', fontsize=8, fontweight='bold')
    
    ax_a.set_title('A: Late-Frame Mean Absolute Motion |d| (f164–188)', fontsize=12, fontweight='bold')
    ax_a.set_xticks([])
    ax_a.set_yticks([])
    
    cbar = plt.colorbar(im, ax=ax_a, orientation='horizontal', pad=0.08, shrink=0.8)
    cbar.set_label('Mean |gray(t) - gray(t-1)| (Intensity levels / frame)', fontsize=9)
    
    # -------------------------------------------------------------
    # Panel B: Forest Plot of Regional QT/F Late Motion Ratios
    # -------------------------------------------------------------
    ax_b = fig.add_subplot(gs[0, 1])
    
    regions_order = ['BG', 'ARM_posthoc', 'LOW', 'ROBOT', 'GRIP_posthoc', 'AIR', 'WHOLE']
    labels = [
        'BG (Background Null)',
        'ARM (Robot White Arm)',
        'LOW (Table + Plank)',
        'ROBOT (Grip + Arm)',
        'GRIP (Gripper Box)',
        'AIR (Ball Corridor)',
        'WHOLE Frame'
    ]
    
    y_pos = np.arange(len(regions_order))
    ratios = []
    ci_lowers = []
    ci_uppers = []
    colors = []
    
    for r in regions_order:
        c_data = res['independent_contrasts'][r]['QT-F']
        ratios.append(c_data['ratio'])
        ci_lowers.append(c_data['ratio'] - c_data['ci95_ratio'][0])
        ci_uppers.append(c_data['ci95_ratio'][1] - c_data['ratio'])
        if r == 'BG':
            colors.append('#337ab7')
        elif r in ['AIR', 'LOW', 'GRIP_posthoc', 'ROBOT']:
            colors.append('#d9534f')
        else:
            colors.append('#f0ad4e')
            
    ax_b.axvline(1.0, color='gray', linestyle='--', linewidth=1.5, label='Null Effect (Ratio = 1.0)')
    for i in range(len(y_pos)):
        ax_b.errorbar([ratios[i]], [y_pos[i]], xerr=[[ci_lowers[i]], [ci_uppers[i]]], fmt='o', color=colors[i],
                     ecolor=colors[i], elinewidth=2.5, capsize=5, capthick=2, markersize=8)
    
    for i, r in enumerate(regions_order):
        c_data = res['independent_contrasts'][r]['QT-F']
        txt = f"{c_data['ratio']:.3f} [{c_data['ci95_ratio'][0]:.3f}, {c_data['ci95_ratio'][1]:.3f}]"
        ax_b.text(c_data['ci95_ratio'][1] + 0.03, y_pos[i], txt, va='center', fontsize=9, fontweight='semibold')
    
    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels(labels, fontsize=10)
    ax_b.set_xlabel('Paired Motion Ratio QT / F (exp(mean log Δ))', fontsize=11)
    ax_b.set_title('B: Regional QT / F Motion Contrast (10 Seeds × 3 Images)', fontsize=12, fontweight='bold')
    ax_b.set_xlim(0.0, 1.35)
    ax_b.grid(True, linestyle=':', alpha=0.5)
    ax_b.invert_yaxis()
    
    # -------------------------------------------------------------
    # Panel C: Spatial Breakdown of Absolute Motion Drop (% Share)
    # -------------------------------------------------------------
    ax_c = fig.add_subplot(gs[1, 0])
    
    shares = res['spatial_shares']
    sub_names = ['GRIP', 'LOW', 'AIR', 'ARM', 'BG', 'REST']
    drop_pcts = [shares[k]['drop_share_pct'] for k in sub_names]
    area_pcts = [shares[k]['area_pct'] for k in sub_names]
    bar_colors = ['#d9534f', '#5cb85c', '#f0ad4e', '#f89406', '#5bc0de', '#aaaaaa']
    
    x = np.arange(len(sub_names))
    width = 0.38
    
    rects1 = ax_c.bar(x - width/2, drop_pcts, width, label='% of Motion Drop (F - QT)', color='#d9534f', alpha=0.85)
    rects2 = ax_c.bar(x + width/2, area_pcts, width, label='% of Total Image Area', color='#337ab7', alpha=0.85)
    
    for rect in rects1:
        h = rect.get_height()
        ax_c.annotate(f'{h:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
                    
    for rect in rects2:
        h = rect.get_height()
        ax_c.annotate(f'{h:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)
    
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(['Gripper (GRIP)', 'Plank (LOW)', 'Corridor (AIR)', 'Arm (ARM)', 'Background (BG)', 'Rest of Frame'], fontsize=9)
    ax_c.set_ylabel('Percentage (%)', fontsize=11)
    ax_c.set_title('C: Spatial Concentration: 93.4% of Drop is in Ball/Gripper Corridor', fontsize=12, fontweight='bold')
    ax_c.set_ylim(0, 50)
    ax_c.legend(loc='upper right', fontsize=10)
    ax_c.grid(True, linestyle=':', alpha=0.5, axis='y')
    
    # -------------------------------------------------------------
    # Panel D: Gripper vs Background Motion Across Arms & Real Reference
    # -------------------------------------------------------------
    ax_d = fig.add_subplot(gs[1, 1])
    
    # Load real reference numbers
    with open('realref_results.json') as f:
        real_data = json.load(f)
    
    real_f164 = real_data['real_f68_92']
    nano_f164 = real_data['nano_f164_188']
    
    arms = ['Real Video', 'Prompt QT', 'Neutral N', 'Base F']
    grip_means = [
        real_f164['GRIP'],
        nano_f164['QT']['GRIP'][0],
        nano_f164['N']['GRIP'][0],
        nano_f164['F']['GRIP'][0]
    ]
    bg_means = [
        real_f164['BG'],
        nano_f164['QT']['BG'][0],
        nano_f164['N']['BG'][0],
        nano_f164['F']['BG'][0]
    ]
    
    x_d = np.arange(len(arms))
    width_d = 0.35
    
    ax_d.bar(x_d - width_d/2, grip_means, width_d, label='Gripper (GRIP) Motion', color='#d9534f', alpha=0.85)
    ax_d.bar(x_d + width_d/2, bg_means, width_d, label='Background (BG) Floor', color='#5bc0de', alpha=0.85)
    
    for i in range(len(arms)):
        ax_d.text(x_d[i] - width_d/2, grip_means[i] + 0.1, f"{grip_means[i]:.2f}", ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax_d.text(x_d[i] + width_d/2, bg_means[i] + 0.1, f"{bg_means[i]:.2f}", ha='center', va='bottom', fontsize=9)
        
    ax_d.set_xticks(x_d)
    ax_d.set_xticklabels(arms, fontsize=10, fontweight='semibold')
    ax_d.set_ylabel('Late Motion |Δgray| (f164–188)', fontsize=11)
    ax_d.set_title('D: Gripper Motion vs Background Noise Floor & Real Reference', fontsize=12, fontweight='bold')
    ax_d.set_ylim(0, 5.0)
    ax_d.legend(loc='upper left', fontsize=10)
    ax_d.grid(True, linestyle=':', alpha=0.5, axis='y')
    
    plt.tight_layout()
    plt.savefig('plots/figure_regional_motion_audit.png', dpi=300)
    print("Plot generated successfully at plots/figure_regional_motion_audit.png")

if __name__ == '__main__':
    main()
