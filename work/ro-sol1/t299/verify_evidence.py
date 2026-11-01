"""Summarize existing acceptance evidence without editing gallery or old results."""
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageChops
import hashlib
import json
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent
digest = lambda data: hashlib.sha256(data).hexdigest()
before = json.loads((HERE.parent / 't293/browser_check.json').read_text())
after = json.loads((HERE / 'browser_check.json').read_text())
delivery = json.loads((HERE / 'delivery_check.json').read_text())
old = {c['name']: c['pass'] for c in before['checks']}
new = {c['name']: c['pass'] for c in after['checks']}
with urllib.request.urlopen(delivery['url'], timeout=15) as response:
    final_status, final_html = response.status, response.read()
gifs = []
for stem in ('pendulum', 'ball'):
    paths = [HERE / f'{stem}_gif_{suffix}.png' for suffix in ('a', 'b')]
    a, b = [Image.open(p).convert('RGB') for p in paths]
    pixels = sum(max(v) > 8 for v in ImageChops.difference(a, b).getdata())
    gifs.append({'stem': stem, 'different_pixels_gt8': pixels,
                 'total_pixels': a.width * a.height,
                 'screenshot_sha256': [digest(p.read_bytes()) for p in paths],
                 'pass': pixels > 100})
suite_same = (HERE / 'browser_check.cjs').read_bytes() == (HERE.parent / 't293/browser_check.cjs').read_bytes()
report = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Live gallery presentation acceptance only; no physical or model validation',
    'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=HERE).decode().strip(),
    'gallery_pin': delivery['pin'], 'url': delivery['url'],
    'suite_byte_identical_to_293': suite_same,
    'suite_sha256': digest((HERE / 'browser_check.cjs').read_bytes()),
    'same_32_check_names': set(old) == set(new) and len(new) == 32,
    'before': {'pass': before['passed'], 'fail': before['failed']},
    'after': {'pass': after['passed'], 'fail': after['failed']},
    'resolved_failures': [name for name in old if not old[name] and new.get(name)],
    'regressions': [name for name in old if old[name] and not new.get(name)],
    'fatal': after.get('fatal'), 'exceptions': after['exceptions'],
    'html_sha256': delivery['html_sha256'],
    'html_equals_commit': delivery['html_equals_pin'],
    'after_browser_http_status': final_status,
    'after_browser_html_unchanged': final_html == (HERE / 'served_gallery.html').read_bytes(),
    'media_count': len(delivery['media']), 'media_pass': delivery['media_pass'],
    'gif_animation': gifs,
}
report['pass'] = all([
    suite_same, report['same_32_check_names'], len(report['resolved_failures']) == 7,
    not report['regressions'], not report['fatal'], not report['exceptions'],
    after['passed'] == 32, after['failed'] == 0, report['html_equals_commit'],
    final_status == 200, report['after_browser_html_unchanged'],
    report['media_count'] == 20, report['media_pass'], all(g['pass'] for g in gifs),
])
(HERE / 'acceptance.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['pass'] else 1)
