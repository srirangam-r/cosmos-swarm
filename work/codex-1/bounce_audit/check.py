import json, math, statistics
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'agy-1/task46_replication/results.json'
x = json.loads(p.read_text())['part_A_midfall_ball_review_698']
def fit(ds):
    y = [math.log(t) for t in ds]
    m, ym = (len(y)-1)/2, statistics.mean(y)
    return math.exp(sum((i-m)*(v-ym) for i,v in enumerate(y))/sum((i-m)**2 for i in range(len(y))))
for name, row in x.items():
    ts = row['indep_corridor_tracker_189f']['impact_t_subframe']
    ds = [b-a for a,b in zip(ts,ts[1:])]
    early = [d for i,d in enumerate(ds) if ts[i+1] <= 97]
    late = [d for i,d in enumerate(ds) if ts[i] >= 96]
    print(name, 'all/early/late',*[round(fit(v),4) for v in (ds,early,late)], 'counts',len(ds),len(early),len(late), 'frames', [round(d,2) for d in ds])
