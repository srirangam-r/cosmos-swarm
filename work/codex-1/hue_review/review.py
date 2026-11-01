import json, pathlib, statistics, math
src=pathlib.Path('work/rog1/hue_val/val_gauge.json')
items=json.loads(src.read_text())['results']
groups={}
for record in items:
    clip,kind=pathlib.Path(record['clip']).stem.split('__')
    key=(clip,kind,record['offset'])
    assert key not in groups
    rows=record['rows']
    assert len(rows)==13 and len({r['id'] for r in rows})==13
    groups[key]={cat:statistics.mean(r['p_yes'] for r in rows if cat=='overall' or r['category']==cat) for cat in ('overall','Physical Laws','Visual Integrity')}
clips=sorted({k[0] for k in groups})
assert len(clips)==12 and len(groups)==144
out={}
for kind in ('freeze','noise','splice','reverse','shuffle'):
    out[kind]={}
    for cat in ('overall','Physical Laws','Visual Integrity'):
        d=[statistics.mean(groups[c,'orig',o][cat]-groups[c,kind,o][cat] for o in (0.0,0.5)) for c in clips]
        out[kind][cat]={'mean':statistics.mean(d),'se':statistics.stdev(d)/math.sqrt(len(d)),'n':len(d),'positive':sum(v>0 for v in d),'per_clip':dict(zip(clips,d))}
print(json.dumps(out,indent=2))
