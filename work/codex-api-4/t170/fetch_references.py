#!/usr/bin/env python3
"""Fetch only already generated r3082 reference jobs from the announced queue."""
import hashlib,json,sys,urllib.request
from pathlib import Path

URL='http://100.111.167.68:8030'
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
source=Path(__file__).resolve().parent/'source/rogcc_metrics.json'
names=set(json.loads(source.read_text()))
jobs=json.load(urllib.request.urlopen(URL+'/jobs?owner=rog-cc'))['jobs']
manifest=[]
for name in sorted(names):
    candidates=[j for j in jobs if j['name']==name and j['status']=='done']
    assert len(candidates)==1,(name,[(j['id'],j['status']) for j in candidates])
    j=candidates[0]; target=out/(name+'.mp4')
    if not target.exists():
        target.write_bytes(urllib.request.urlopen(URL+'/jobs/'+j['id']+'/mp4',timeout=120).read())
    (out/(name+'.json')).write_text(json.dumps(j['sidecar'],indent=1)+'\n')
    manifest.append({'name':name,'queue_id':j['id'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(out/'reference_manifest.json').write_text(json.dumps(manifest,indent=1)+'\n')
print('Fetched',len(manifest),'existing references')
