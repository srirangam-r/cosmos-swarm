#!/usr/bin/env python3
"""Operational gallery check; this does not validate any scientific claim."""
import argparse
import datetime as dt
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.anchors = []
        self.sources = {}
        self.video_id = None
        self.variants = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'video':
            self.video_id = a.get('id', '(anonymous)')
            self.sources[self.video_id] = []
        if tag == 'source' and self.video_id and 'src' in a:
            self.sources[self.video_id].append(a['src'])
        if tag == 'a' and 'href' in a:
            self.anchors.append(a['href'])
        if 'onclick' in a:
            for base in re.findall(r"switchVideo\('[^']+',\s*'([^']+)'", a['onclick']):
                self.variants.update([base + '.mp4', base + '.webm'])
    def handle_endtag(self, tag):
        if tag == 'video':
            self.video_id = None

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr

def check_url(url):
    row = {'url': url, 'utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = r.read(2_000_001)
            row.update(status=r.status, content_type=r.headers.get('Content-Type'), bytes_read=len(data))
    except (OSError, urllib.error.URLError) as e:
        row['error'] = str(e)
    return row

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--gallery', type=Path, default=Path('work/rahul-5-agy/gallery/index.html'))
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--url', action='append', default=[])
    args = ap.parse_args()
    gallery = args.gallery.resolve()
    source = gallery.read_text()
    html = Gallery()
    html.feed(source)
    all_sources = sorted(set(s for paths in html.sources.values() for s in paths) | html.variants)
    media = []
    for src in all_sources:
        p = gallery.parent / src
        row = {'source': src, 'exists': p.is_file()}
        if p.is_file():
            row.update(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            code, stdout, stderr = run(['ffprobe', '-v', 'error', '-count_frames', '-show_entries',
                'stream=index,codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,r_frame_rate,duration,nb_read_frames:format=duration',
                '-of', 'json', str(p)])
            row['probe_exit'] = code
            if code == 0:
                row['probe'] = json.loads(stdout)
            else:
                row['probe_error'] = stderr[-2000:]
            code, _, stderr = run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(p), '-map', '0:v:0', '-f', 'null', '-'])
            row['decode_exit'] = code
            if stderr:
                row['decode_stderr'] = stderr[-2000:]
        media.append(row)
    _, rev, _ = run(['git', 'rev-parse', 'HEAD'])
    result = {
        'scope': 'HTTP reachability, local source/link and full media-decode checks only; no browser execution or physics validation',
        'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'gallery_commit': rev.strip(), 'gallery_path': str(args.gallery),
        'gallery_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'videos': html.sources, 'media': media,
        'broken_local_anchors': [s for s in html.anchors if s.startswith('#') and s[1:] not in html.ids],
        'http': [check_url(url) for url in dict.fromkeys(args.url + [s for s in html.anchors if s.startswith(('http://', 'https://'))])],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'commit': result['gallery_commit'], 'videos': len(html.sources), 'media': len(media),
        'missing': sum(not m['exists'] for m in media),
        'decode_failures': sum(m.get('decode_exit', 1) != 0 for m in media),
        'broken_local_anchors': result['broken_local_anchors'], 'http': result['http']}, indent=2))
    for m in media:
        if m['source'].endswith('.mp4') and 'probe' in m:
            v = next(s for s in m['probe']['streams'] if s['codec_type'] == 'video')
            print(m['source'], v.get('nb_read_frames'), v.get('avg_frame_rate'), m['probe']['format'].get('duration'))

if __name__ == '__main__':
    main()
