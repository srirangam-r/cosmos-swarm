#!/usr/bin/env python3
"""Compare the announced live gallery with previously decoded source assets."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('gallery_check', HERE.parent / 't279/check_gallery.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
URL = 'http://sha-devel.tail0c526a.ts.net:8085/'
def fetch(path):
    result = {'path':path,'utc':datetime.now(timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(URL + path, timeout=10) as response:
            data = response.read(2_000_001)
            result.update(status=response.status,content_type=response.headers.get('Content-Type'),
                          bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            return result, data
    except OSError as error:
        result['error'] = str(error)
        return result, b''
root, data = fetch('')
html = module.Gallery()
html.feed(data.decode())
sources = sorted(set(s for files in html.sources.values() for s in files) | html.variants)
previous = json.loads((HERE.parent/'t279/smoke_333821f.json').read_text())
previous_hashes = {r['source']:r for r in previous['media']}
def asset(path):
    result, data = fetch(path)
    prior = previous_hashes.get(path,{})
    result['same_as_decoded_t279_asset'] = result.get('sha256') == prior.get('sha256')
    result['t279_full_decode_exit'] = prior.get('decode_exit') if result['same_as_decoded_t279_asset'] else None
    return result
with ThreadPoolExecutor(max_workers=4) as pool:
    assets = list(pool.map(asset, sources))
local = ROOT/'work/rahul-5-agy/gallery/index.html'
result = {'scope':'Live HTTP/hash verification; same-byte assets inherit prior ffmpeg full decode, no browser or scientific validation',
          'root':root,'html_equals_local':data == local.read_bytes(), 'assets':assets,
          'broken_local_anchors':[a for a in html.anchors if a.startswith('#') and a[1:] not in html.ids]}
(HERE/'live_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'root':root,'html_equals_local':result['html_equals_local'],
    'assets':len(assets),'http200':sum(a.get('status')==200 for a in assets),
    'same_as_prior_full_decode':sum(a['same_as_decoded_t279_asset'] and a['t279_full_decode_exit']==0 for a in assets),
    'broken_local_anchors':result['broken_local_anchors']},indent=2))
