# ro-1 task 22 v7/v8: late-motion proxy (same metric/crop as cause_v5/analyze.py) + nv_scoreboard merge.
# v7: REC (tools/recipe DEFAULT_PROMPT) vs RECT (REC + timed-settle clause), ball1/ball2 x s1-3, paired by input+seed.
# v8: prompt-switch arms (base F, QT text on the cond pass for steps [a,b)) vs cause5 F/QT at seeds 3, 5.
import av, numpy as np, glob, os, json
from PIL import Image
R = '/home/rohith/swarm-work/ro-1/'


def late(f):
    fr = [x.to_ndarray(format='rgb24') for x in av.open(f).decode(video=0)]
    g = np.stack([np.asarray(Image.fromarray(x).convert('L')).astype(np.float32)[130:360, 220:360] for x in fr])
    d = np.abs(np.diff(g, axis=0)).mean((1, 2))
    return dict(early=round(float(d[1:45].mean()), 3), late=round(float(d[45:].mean()), 3),
                last20=round(float(d[-20:].mean()), 3), n=len(fr))


def nv(b):
    for p in (R + f'nv_v7/{b}.score.json', R + f'nv_qt2/{b}.score.json'):
        if os.path.exists(p):
            d = json.load(open(p)); d = next(iter(d.values())) if 'dover_fused' not in d else d
            return d.get('dover_fused'), d.get('dd_norm')
    return None, None


rows = {}
for f in sorted(glob.glob(R + 'fps_sweep/out_cause7/*.mp4') + glob.glob(R + 'fps_sweep/out_cause8/*.mp4')):
    b = os.path.basename(f)[:-4]
    rows[b] = dict(late(f), dover=nv(b)[0], dd=nv(b)[1])
for s in (3, 5):
    for a in ('F', 'QT'):
        b = f'cause5_{a}_ball1_fps24_93f_s{s}'
        rows[b] = dict(late(R + f'fps_sweep/out_cause5/{b}.mp4'), dover=nv(b)[0], dd=nv(b)[1])
for k, v in rows.items():
    print(f"{k:34s} last20 {v['last20']:.2f}  DOVER {v['dover']}  DD {v['dd']}")


def paired(a, b, key):
    d = [rows[y][key] - rows[x][key] for x, y in zip(a, b) if x in rows and y in rows and rows[x][key] is not None and rows[y][key] is not None]
    if not d: return 'n=0'
    d = np.array(d); se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else float('nan')
    return f'{d.mean():+.3f} ± {se:.3f} (n={len(d)}, {int((d < 0).sum())} negative)'


A = [f'v7_REC_{i}_fps24_93f_s{s}' for i in ('ball1', 'ball2') for s in (1, 2, 3)]
B = [x.replace('REC_', 'RECT_') for x in A]
for key in ('last20', 'dover', 'dd'):
    print('RECT-REC', key, paired(A, B, key))
for arm in ('SWfull', 'SWe3', 'SWe7', 'SWl7', 'SWl17'):
    for s in (3, 5):
        b = f'v8_{arm}_ball1_fps24_93f_s{s}'
        if b in rows:
            print(f'v8 {arm} s{s}: last20 {rows[b]["last20"]:.2f} (F {rows[f"cause5_F_ball1_fps24_93f_s{s}"]["last20"]:.2f}, QT {rows[f"cause5_QT_ball1_fps24_93f_s{s}"]["last20"]:.2f})')
json.dump(rows, open(R + 'cause_v7/late_nv_v78.json', 'w'), indent=1)
