"""Reproduce frozen four-clip CPU readout. Does NOT submit to referee.

python3 run_planted.py --clips /tmp/ro-sol1-t289 --out /tmp/recheck289
Requires numpy and opencv-python. Downloads only advertised planted URLs.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import urllib.request
import cv2
import numpy as np
from crossing_readout import measure

ap = argparse.ArgumentParser()
ap.add_argument('--clips', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
args = ap.parse_args()
root = Path(__file__).resolve().parent
args.clips.mkdir(parents=True, exist_ok=True)
args.out.mkdir(parents=True, exist_ok=True)
manifest = json.loads((root/'planted_manifest.json').read_text())
geometry = json.loads((root/'geometry.json').read_text())
summary = []
estimates = {}
for clip in manifest['clips']:
    name = clip['clip_id']
    video = args.clips/(name+'.mp4')
    if not video.exists():
        urllib.request.urlretrieve(clip['url'], video)
    assert hashlib.sha256(video.read_bytes()).hexdigest() == clip['sha256'], name
    result = measure(video, **geometry['clips'][name], **geometry['parameters'])
    (args.out/(name+'.json')).write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    row = {key:result.get(key) for key in ['frames','fps','tracked_frames','reason','crossing']}
    row['clip_id'] = name
    summary.append(row)
    crossing = result.get('crossing', {})
    if crossing.get('reason') == 'measurable_unvalidated':
        estimates[name] = {'period_s':crossing['period_s']}
    cap = cv2.VideoCapture(str(video))
    tiles = []
    for i in np.linspace(0,len(result['centers'])-1,min(8,len(result['centers'])),dtype=int):
        cap.set(cv2.CAP_PROP_POS_FRAMES,int(i))
        ok, frame = cap.read()
        assert ok
        x,y = result['centers'][i]
        cv2.circle(frame,(round(x),round(y)),18,(0,0,255),2)
        cv2.putText(frame,f'{name} f{i}',(10,30),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,0,0),2)
        tiles.append(cv2.resize(frame,(416,240)))
    cap.release()
    while len(tiles)%4:
        tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(str(args.out/(name+'_strip.jpg')),
                cv2.vconcat([cv2.hconcat(tiles[i:i+4]) for i in range(0,len(tiles),4)]))
report = dict(run_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              reader_sha256=hashlib.sha256((root/'crossing_readout.py').read_bytes()).hexdigest(),
              python=platform.python_version(), numpy=np.__version__, opencv=cv2.__version__,
              results=summary, validated=False)
(args.out/'run_summary.json').write_text(json.dumps(report,indent=2)+'\n')
(args.out/'estimates.json').write_text(json.dumps(estimates,indent=2)+'\n')
print(json.dumps({'tracked_all':sum(r['tracked_frames']==r['frames'] for r in summary),
                  'measurable':len(estimates), 'total':len(summary), 'validated':False}))
