"""Read-only deployed gallery delivery check; no model or scientific measurement."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PIN = 'f96be25'
BASE = 'http://sha-devel.tail0c526a.ts.net:8085/'

def fetch(name):
    with urllib.request.urlopen(BASE + name, timeout=15) as r:
        return r.status, r.read()

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []; self.anchors = []; self.sources = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if a.get('href', '').startswith('#'): self.anchors.append(a['href'])
        if tag in ('source', 'img') and a.get('src', '').startswith('clips/'):
            self.sources.add(a['src'])
        for base in re.findall(r"switchVideo\('[^']+',\s*'([^']+)'", a.get('onclick', '')):
            self.sources.update(base + ext for ext in ('.mp4', '.webm'))

status, html = fetch('')
(HERE / 'served_gallery.html').write_bytes(html)
page = Page(); page.feed(html.decode())
committed = subprocess.check_output(['git', 'show', f'{PIN}:work/rahul-5-agy/gallery/index.html'], cwd=ROOT)
report = {'utc': datetime.now(timezone.utc).isoformat(), 'url': BASE, 'pin': PIN,
          'status': status, 'html_sha256': hashlib.sha256(html).hexdigest(),
          'html_equals_pin': html == committed,
          'broken_anchors': sorted(set(a for a in page.anchors if a[1:] not in page.ids)),
          'duplicate_ids': sorted(set(i for i in page.ids if page.ids.count(i) > 1))}

def asset(name):
    result = {'source': name}
    try:
        status, data = fetch(name)
        original = subprocess.check_output(['git', 'show', f'{PIN}:work/rahul-5-agy/gallery/{name}'], cwd=ROOT)
        with tempfile.TemporaryDirectory(prefix='ro-sol1-t293-') as tmp:
            p = Path(tmp) / Path(name).name; p.write_bytes(data)
            probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
                '-show_entries', 'stream=codec_name,pix_fmt,width,height,avg_frame_rate,nb_read_frames:format=duration',
                '-of', 'json', str(p)]))
            decode = subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(p), '-f', 'null', '-'], capture_output=True, text=True)
        result.update(status=status, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                      same_as_pin=data == original, probe=probe, decode_exit=decode.returncode,
                      decode_stderr=decode.stderr)
        if Path(name).name in ('pendulum_physics_start.mp4', 'pendulum_physics_start.gif', 'ball_settle.mp4', 'ball_settle.gif'):
            raj = subprocess.check_output(['git', 'show', f'a597e6f:work/raj-demos/{Path(name).name}'], cwd=ROOT)
            result['same_as_original_raj_demo'] = data == raj
    except Exception as e:
        result['error'] = str(e)
    return result

with ThreadPoolExecutor(max_workers=4) as pool:
    report['media'] = list(pool.map(asset, sorted(page.sources)))
report['media_pass'] = all(a.get('status') == 200 and a.get('same_as_pin') and a.get('decode_exit') == 0 for a in report['media'])
(HERE / 'delivery_check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'media'}, indent=2))
print('media', len(report['media']), 'decoded', sum(a.get('decode_exit') == 0 for a in report['media']))
