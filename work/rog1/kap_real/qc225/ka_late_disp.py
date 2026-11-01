# rog1: displacement of the tracked ball inside the task-225 late window (last 25 kept frames) of each KA cut.
# strip late tile = 416 px wide from a 1280-px source -> scale 0.325 (cut is 832 wide letterboxed, tile = cut/2).
import json, numpy as np
T = json.load(open('tracks.json')); man = {m['cut_id']: m for m in json.load(open('manifest.json'))}
SEL = ['g04_rest','g12_rest','g17_bouncing','g06_bouncing','g05_bouncing','g09_bouncing','g06_rolling','g09_rolling','g07_rolling','g18_rolling']
S = 416/1280; out = {}
for cid in SEL:
    m = man[cid]; r = T[m['clip']]; dup = r['dup']
    idx = [i for i in range(m['start_f'], m['end_f']+1) if not dup[i]][-25:]
    # strip late tiles sample cut frames 164..188 step 3 -> last-25 offsets 0,3,...,24
    tiles = idx[0::3]
    p = [r['trk'][i] for i in tiles]
    vis = [q is not None for q in p]
    xy = np.array([q[:2] for q in p if q]); area = [q[4] for q in p if q]
    d = np.hypot(*(xy - xy[0]).T) if len(xy) else np.array([np.nan])
    dy = (xy[:,1] - xy[0,1]) if len(xy) else []
    out[cid] = dict(src_frames=[idx[0], idx[-1]], tiles_visible=f'{sum(vis)}/{len(vis)}',
                    max_disp_src_px=round(float(d.max()),1), end_disp_src_px=round(float(d[-1]),1),
                    max_disp_strip_px=round(float(d.max()*S),1), end_disp_strip_px=round(float(d[-1]*S),1),
                    y_range_src=round(float(np.ptp(xy[:,1])),1) if len(xy) else None,
                    area_first_last=[area[0], area[-1]] if area else None)
    print(cid, out[cid])
json.dump(out, open('ka_late_disp.json','w'), indent=1)
