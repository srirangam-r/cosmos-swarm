#!/usr/bin/env python3
"""
Plot publication-quality 4-panel figure for Task 231 (Review of Finding #4505).
"""
import os, json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

OUT_DIR = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task231_quiet_time_review"
os.makedirs(os.path.join(OUT_DIR, "plots"), exist_ok=True)

with open(os.path.join(OUT_DIR, "replicate_4505_results.json")) as f:
    our_data = json.load(f)

with open(os.path.join(OUT_DIR, "author_quiet2_results.json")) as f:
    auth_data = json.load(f)

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=300)

colors = {
    'Real': '#2ca02c',
    'QT': '#1f77b4',
    'F': '#d62728',
    'N': '#7f7f7f'
}

# Panel (a): Real vs Nano Distributions at TH 2.0
ax1 = axes[0, 0]
real_times = [1.42, 1.44, 1.44, 1.44, 1.44, 1.44] # 6 streams
qt_times = []
f_times = []
n_times = []
for img in ['b1dd33', 'b2dd35', 'b2dd37']:
    qt_times.extend([t if t is not None else 8.5 for t in auth_data[img]['nano']['QT']['2.0']])
    f_times.extend([t if t is not None else 8.5 for t in auth_data[img]['nano']['F']['2.0']])
    n_times.extend([t if t is not None else 8.5 for t in auth_data[img]['nano']['N']['2.0']])

data_groups = [real_times, qt_times, f_times, n_times]
labels = ['Real (n=6)', 'Nano QT (n=30)', 'Nano F (n=30)', 'Nano N (n=30)']
palette = [colors['Real'], colors['QT'], colors['F'], colors['N']]

positions = [1, 2, 3, 4]
bp = ax1.boxplot(data_groups, positions=positions, patch_artist=True, widths=0.5,
                 medianprops=dict(color='black', linewidth=2),
                 boxprops=dict(linewidth=1.5),
                 whiskerprops=dict(linewidth=1.2),
                 capprops=dict(linewidth=1.2))

for patch, col in zip(bp['boxes'], palette):
    patch.set_facecolor(col)
    patch.set_alpha(0.6)

# Overlay individual jittered points
for pos, grp, col in zip(positions, data_groups, palette):
    jitter = np.random.normal(0, 0.05, size=len(grp))
    ax1.scatter(pos + jitter, grp, color=col, edgecolor='black', s=45, alpha=0.8, zorder=3)

ax1.axhline(1.43, color=colors['Real'], linestyle='--', linewidth=1.8, label='Real Reference (~1.43 s)')
ax1.axhline(3.75, color=colors['QT'], linestyle=':', linewidth=2.0, label='Nano QT Median (3.75 s, 2.6x slow)')
ax1.axhline(7.88, color='darkred', linestyle='-.', linewidth=1.2, label='Clip End (7.88 s / Never Settles)')

ax1.set_xticks(positions)
ax1.set_xticklabels(labels, fontsize=11, fontweight='bold')
ax1.set_ylabel('Time to Quiet (seconds at TH = 2.0)', fontsize=12, fontweight='bold')
ax1.set_title('(a) Real vs Nano Settle Timing (TH = 2.0)', fontsize=13, fontweight='bold')
ax1.set_ylim(0.5, 9.2)
ax1.legend(loc='upper left', frameon=True, fontsize=10)

# Panel (b): Threshold Sensitivity Curve
ax2 = axes[0, 1]
th_vals = [1.5, 2.0, 2.5]
real_curve = [1.43, 1.43, 1.35]
qt_auth_curve = [6.25, 3.75, 3.50]
qt_our_curve = [5.50, 4.00, 3.75]
f_curve = [8.5, 8.5, 8.5]
n_curve = [8.5, 8.5, 6.25]

ax2.plot(th_vals, real_curve, marker='s', markersize=8, linewidth=2.5, color=colors['Real'], label='Real Video Ground Truth')
ax2.plot(th_vals, qt_auth_curve, marker='o', markersize=8, linewidth=2.5, color=colors['QT'], label='Nano QT (q8 Karras grid, author)')
ax2.plot(th_vals, qt_our_curve, marker='^', markersize=8, linewidth=2.2, color='#0288d1', linestyle='--', label='Nano QT (Mixed-GPU grid, ours)')
ax2.plot(th_vals, f_curve, marker='x', markersize=8, linewidth=2.0, color=colors['F'], linestyle=':', label='Nano F (No Settle Clause)')
ax2.plot(th_vals, n_curve, marker='d', markersize=7, linewidth=2.0, color=colors['N'], linestyle='-.', label='Nano N (Neutral Control)')

ax2.fill_between(th_vals, [3.0, 3.0, 2.5], [6.0, 6.0, 5.0], color=colors['QT'], alpha=0.15, label='QT 95% Bootstrap CI')
ax2.set_xlabel('Quiet Ratio Threshold (TH)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Median Time to Quiet (seconds)', fontsize=12, fontweight='bold')
ax2.set_title('(b) Settle Time vs Ratio Threshold (TH 1.5 - 2.5)', fontsize=13, fontweight='bold')
ax2.set_xticks(th_vals)
ax2.set_xticklabels(['1.5 (Strict)', '2.0 (Nominal)', '2.5 (Loose)'], fontsize=11)
ax2.set_ylim(0.8, 9.2)
ax2.legend(loc='upper right', frameon=True, fontsize=9.5)

# Panel (c): Seed-Level Pacing (QT Condition)
ax3 = axes[1, 0]
seed_ids = list(range(1, 11))
img_markers = {'b1dd33': ('o', '#1f77b4'), 'b2dd35': ('s', '#ff7f0e'), 'b2dd37': ('^', '#2ca02c')}

for img, (m, c) in img_markers.items():
    times = []
    for s in seed_ids:
        clip_id = f"t141_{img}_QT_s{s}"
        t = our_data['per_clip_data'][clip_id]['quiet_discrete']['2.0']
        times.append(t if t is not None else 8.5)
    ax3.plot(seed_ids, times, marker=m, markersize=8, linewidth=1.5, color=c, alpha=0.8, label=f'Image {img}')

ax3.axhline(1.43, color=colors['Real'], linestyle='--', linewidth=1.5, label='Real Reference (~1.43 s)')
ax3.axhline(8.5, color='gray', linestyle=':', label='Non-Settling Ceiling')

ax3.set_xlabel('Noise Seed (1 to 10)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Time to Quiet (s at TH = 2.0)', fontsize=12, fontweight='bold')
ax3.set_title('(c) Seed-Locking of Settle Time (QT condition, $\eta^2_{seed} = 0.491$)', fontsize=13, fontweight='bold')
ax3.set_xticks(seed_ids)
ax3.set_ylim(0.8, 9.2)
ax3.legend(loc='upper left', frameon=True, fontsize=9.5)

# Panel (d): Ball Growth vs Settle Time
ax4 = axes[1, 1]
growth_labels = ['All QT (n=30)', 'Normal Size (n=26)\n(<1.6x)', 'Giant Growth (n=4)\n(>=1.6x)', 'Clean Rest (n=21)\n(clean_settle2)']
d_meds = [4.0, 4.5, 3.5, 4.0]
r_meds = [4.40, 5.50, 3.44, 3.96]

x_pos = np.arange(len(growth_labels))
width = 0.35

rects1 = ax4.bar(x_pos - width/2, d_meds, width, label='Discrete 12f Bins (0.5s)', color='#1f77b4', alpha=0.8)
rects2 = ax4.bar(x_pos + width/2, r_meds, width, label='Continuous Rolling Win (12f)', color='#aec7e8', edgecolor='navy')

ax4.axhline(1.43, color=colors['Real'], linestyle='--', linewidth=1.8, label='Real Reference (1.43 s)')

for rect in rects1:
    h = rect.get_height()
    ax4.annotate(f'{h:.1f}s', xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=10, fontweight='bold')

for rect in rects2:
    h = rect.get_height()
    ax4.annotate(f'{h:.2f}s', xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=10, fontweight='bold')

ax4.set_xticks(x_pos)
ax4.set_xticklabels(growth_labels, fontsize=10, fontweight='bold')
ax4.set_ylabel('Median Time to Quiet (seconds at TH = 2.0)', fontsize=12, fontweight='bold')
ax4.set_title('(d) Ball Growth Stratification & Rolling-Window Check', fontsize=13, fontweight='bold')
ax4.set_ylim(0, 6.5)
ax4.legend(loc='upper right', frameon=True, fontsize=9.5)

plt.tight_layout()
out_png = os.path.join(OUT_DIR, "plots", "figure_quiet_time_replication.png")
plt.savefig(out_png, dpi=300)
print(f"Figure saved to {out_png}")
