import json, math, statistics
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'raj-4/nv_scoreboard_real/gauge_real_matched.json'
data=json.loads(p.read_text())
for task in ('ball','pend','slopewood'):
    rows=[]
    for name,r in data.items():
        if not name.startswith(task+'_'): continue
        assert r['fps']==24 and r['dd_interval']==3 and len(r['dd_maxrad'])>=30
        v=r['dd_maxrad'][:30]
        short=sum(v)/len(v)/(480/256)
        rows.append({'clip':name,'full':r['dd_norm'],'first_93_approx':short,'delta':short-r['dd_norm']})
    delta=[r['delta'] for r in rows]
    print(json.dumps({'task':task,'n':len(rows),'full_mean':statistics.mean(r['full'] for r in rows),'short_mean':statistics.mean(r['first_93_approx'] for r in rows),'delta_mean':statistics.mean(delta),'delta_se':statistics.stdev(delta)/math.sqrt(len(delta)),'rows':rows}))
