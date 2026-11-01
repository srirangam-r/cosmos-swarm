#!/usr/bin/env python3
"""Known-answer range check of the t226 P period readouts (rec_period v1 primary, TMIN 0.6 s; Amendment-1 sensitivity
TMIN 0.25 s) on rahul-api-2's synthetic pendulum clips (work/rahul-api-2/t226_pend/synth_fast.py: T = 0.33/0.5/1.0/1.8 s,
A = 15/40 deg, drawn on the t226 P input; v2 blurs the real pendulum first, v1 draws over it). A dir without
truth.json (e.g. the t193 Nano base clips, seeds 21-30) is read with T unknown, to check that w025 == v1 on real Nano clips.
Uses measure_t226.period_stats unchanged. Usage: synth_check_t226.py <synth_dir> [<synth_dir> ...] > out.json"""
import sys, os, json, glob
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure_t226 as mt

res = {}
for d in sys.argv[1:]:
    tj = os.path.join(d, 'truth.json')   # no truth.json: unknown-T clips (e.g. t193 Nano) -> T None, check v1 vs w025
    truth = json.load(open(tj)) if os.path.exists(tj) else \
        {os.path.basename(f)[:-4]: dict(T=None, A_deg=None) for f in sorted(glob.glob(os.path.join(d, '*.mp4')))}
    for name, t in sorted(truth.items()):
        F, fps = mt.load_bgr(os.path.join(d, name + '.mp4'))
        G = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in F])
        r = mt.period_stats(G, 24.0)
        row = dict(T_true=t['T'], A_deg=t['A_deg'])
        for k in ('period_v1', 'period_w025'):
            p = r[k]['period_s']
            row[k] = dict(r[k], ratio=None if (p is None or t['T'] is None) else round(p / t['T'], 4))
        res[f'{os.path.basename(os.path.normpath(d))}/{name}'] = row
        print(f"{os.path.basename(os.path.normpath(d))}/{name}: T={t['T']} "
              f"v1 {row['period_v1']['period_s']} ({row['period_v1']['flag']}, x{row['period_v1']['ratio']})  "
              f"w025 {row['period_w025']['period_s']} ({row['period_w025']['flag']}, x{row['period_w025']['ratio']})",
              file=sys.stderr, flush=True)
print(json.dumps(res, indent=1))
