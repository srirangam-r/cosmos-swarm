# rog1 kap: final labels (conservative mocap+video settle), choose cuts, write manifest.
import json, numpy as np
L = json.load(open('labels.json')); T = json.load(open('tracks.json')); RB = json.load(open('gauge_realball_v11.json'))
MOC = 'src/data/rigid/bouncing ball/json'; M = 8  # ambiguity margin, container frames (~0.27 s)
man = []; per = {}
for c in L:
    trk = T[c]['trk']; n = T[c]['n']; dup = T[c]['dup']; dist = [i for i in range(n) if not dup[i]]
    vis = np.array([t is not None for t in trk]); xy = np.array([t[:2] if t else [np.nan]*2 for t in trk])
    z = np.array(json.load(open(f'{MOC}/{c}.json'))['ball']['z']); zr = np.median(z[-8:])
    imp_m = int(np.argmax(z < zr + 40)); lastair = int(np.max(np.where(z > zr + 5)[0]))
    rbi = RB[c].get('impact_frame'); impv = dist[rbi] if rbi is not None and 30 <= rbi < len(dist) else None
    sv = L[c]['settle_f']; sm = None if impv is None else impv + lastair - imp_m
    s_lo = min(x for x in (sv, sm) if x is not None); s_hi = max(x for x in (sv, sm) if x is not None)
    lab = []
    for e in range(n):
        w = slice(max(0, e - 29), e + 1); vv = vis[w]; Lb = 'AMBIG'
        if impv is not None and impv + 3 <= e <= s_lo - M: Lb = 'BOUNCING'
        elif e >= s_hi + M and vv.sum() >= 24 and vis[e]:
            p = xy[w][vv]; disp = float(np.hypot(*(p[-3:].mean(0) - p[:3].mean(0))))
            Lb = 'ROLLING' if disp >= 10 else ('REST' if disp <= 3 else 'AMBIG')
        lab.append(Lb)
    per[c] = dict(n=n, impact_f=impv, settle_video_f=sv, settle_mocap_f=sm, mocap_impact_to_settle_s=round((lastair-imp_m)/30,3), labels=lab)
    # cuts: start 30 (≈ release; board Nano inputs are dd33/35). one per available label, at the middle of the longest run
    for want in ('BOUNCING', 'ROLLING', 'REST'):
        runs = []; cur = None
        for e, Lb in enumerate(lab):
            if Lb == want: cur = [e, e] if cur is None else [cur[0], e]
            else:
                if cur: runs.append(cur); cur = None
        if cur: runs.append(cur)
        if not runs: continue
        a, b = max(runs, key=lambda r: r[1] - r[0]); e = (a + b) // 2 if want != 'REST' else b
        man.append(dict(cut_id=f'g{int(c):02d}_{want.lower()}', clip=c, start_f=30, end_f=e, label=want, run=[a, b]))
    # ambiguous example: the settle boundary itself
    eb = (s_lo + s_hi) // 2
    man.append(dict(cut_id=f'g{int(c):02d}_ambig_settle', clip=c, start_f=30, end_f=eb, label='AMBIG', run=[s_lo - M, s_hi + M]))
json.dump(per, open('labels_final.json', 'w'))
json.dump(man, open('manifest.json', 'w'), indent=1)
from collections import Counter; print(Counter(m['label'] for m in man), len(man))
for m in man: print(m['cut_id'], m['end_f'], m['run'])
