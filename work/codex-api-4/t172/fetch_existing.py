#!/usr/bin/env python3
"""Download the 36 existing source clips; creates no jobs or GPU work."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--url',default='http://100.111.167.68:8030');a=ap.parse_args()
root=Path(__file__).resolve().parent;r=json.loads((root/'results.json').read_text());a.out.mkdir(parents=True,exist_ok=True)
for name,c in r['clips'].items():
 side=json.loads((root/'sidecars'/(name+'.json')).read_text());p=a.out/(name+'.mp4')
 if not p.exists():
  with urllib.request.urlopen(a.url+'/jobs/'+side['queue_id']+'/mp4',timeout=120) as u:p.write_bytes(u.read())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==c['video_sha256'],name
 p.with_suffix('.json').write_text((root/'sidecars'/(name+'.json')).read_text())
print('All 36 existing video SHA-256 values verified; no generation.')
