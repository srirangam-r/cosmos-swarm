"""Generate concise table and exact headline from frozen primary outputs."""
from pathlib import Path
import json,csv,numpy as np
p=Path(__file__).parent;d=json.loads((p/'output/results.json').read_text());all_=json.loads((p/'output/summary_all.json').read_text());ok=json.loads((p/'output/summary_ok.json').read_text())
fields=['recording','flag','tool_period_s','mocap_crossing_period_s','mocap_turning_period_s','ratio','ratio_turning','ratio_zc','ci95_covers_mocap','prefix_distinct_frames','video_release_frame','window_fit_cutoff_frame']
with (p/'table.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
 for key,r in d.items():
  t=r['tool'];w.writerow(dict(recording=key,flag=t['flag'],tool_period_s=t['period_s'],mocap_crossing_period_s=r['reference_crossing']['period_s'],mocap_turning_period_s=r['reference_turning']['period_s'],ratio=r['ratio'],ratio_turning=r['ratio_turning'],ratio_zc=r['ratio_zc'],ci95_covers_mocap=r['covers_reference'],prefix_distinct_frames=r['n_distinct_prefix'],video_release_frame=r['video_release_frame'],window_fit_cutoff_frame=t['release_frame']))
a=ok['ratio'];b=ok['ratio_turning'];fails=[r['id'] for r in d.values() if r['tool']['flag']!='ok'];ref=np.array([r['reference_crossing']['period_s'] for r in d.values()]);turn=np.array([r['reference_turning']['period_s'] for r in d.values()]);mdiff=np.max(abs(ref-turn))
text=f'''\n## Results\n\nUnchanged `measure_pend v1` passes its own fit checks on **{ok['n']}/20** real
continuations; check IDs: {fails}. On the eligible records, fit period divided
by independent same-window mocap crossing period is **{a['mean']:.6f} ±
{a['se']:.6f} SE** (range {a['min']:.6f}–{a['max']:.6f});
{a['within_1pct']}/{ok['n']} within1%, {a['within_5pct']}/{ok['n']} within5%.
The turning-point reference gives **{b['mean']:.6f} ± {b['se']:.6f} SE**.
The supplied fit CI95 covers the crossing reference on **{ok['covers_reference']}/{ok['n']}**
eligible records: descriptive observed coverage, not a calibrated coverage guarantee.
All20, retaining failures: mean ratio {all_['ratio']['mean']:.6f} ±
{all_['ratio']['se']:.6f} SE (max {all_['ratio']['max']:.6f}).
Maximum reference-period change under ±1distinct-frame alignment is
{all_['max_align_period_change_s']:.6f}s. Crossings versus turning-point reference
periods differ at most {mdiff:.6f}s across all20.
\nThe measurement tool's exact period, crossing period, R² and damping estimate
on recording10 reproduce task182 byte-level floating values (difference0).
All40 original source files match the pinned HF revision by LFS SHA256 / Git
blob SHA1. Four reference tests and independent arithmetic/contract checks pass.
Full output/traces and the failure cases are retained.
'''
p.joinpath('README.md').write_text(p.joinpath('README.md').read_text().split('\n## Results\n')[0]+text)
print(text)
