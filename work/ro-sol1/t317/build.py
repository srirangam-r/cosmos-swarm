"""Package frozen task265 frames; no measurement or reader adjudication."""
from pathlib import Path
from fractions import Fraction
import hashlib
import html
import json
import platform
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'work/ro-3/task265'
REV = subprocess.check_output(['git', 'rev-parse', '823a546'], cwd=ROOT, text=True).strip()
NAME = 'dial_pend11_P600_s2'
OUT = HERE / 'dense'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen(path):
    rel = str(path.relative_to(ROOT))
    expected = subprocess.check_output(['git', 'rev-parse', f'{REV}:{rel}'], cwd=ROOT, text=True).strip()
    actual = subprocess.check_output(['git', 'hash-object', str(path)], cwd=ROOT, text=True).strip()
    if actual != expected:
        raise ValueError(f'Source differs from frozen commit: {rel}')
    return {'path': rel, 'git_blob': expected, 'sha256': sha(path), 'bytes': path.stat().st_size}


def main():
    OUT.mkdir(exist_ok=True)
    results_path = SOURCE / 'results_dial.json'
    results = json.loads(results_path.read_text())
    names = sorted(results, key=lambda n: (n.split('_')[1], int(n.split('_')[2][1:]), n))
    sources = [frozen(results_path), frozen(SOURCE / 'measure_dial.py')]
    for name in names:
        sources.extend(frozen(p) for p in [SOURCE / 'qc_dial' / f'sheet_{name}.jpg',
                       SOURCE / 'dial_out' / f'{name}.json', SOURCE / 'dial_out' / f'{name}.qc.json'])
    video = SOURCE / 'dial_out' / f'{NAME}.mp4'
    sources.append(frozen(video))
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height,avg_frame_rate,nb_frames:frame=best_effort_timestamp_time',
        '-of', 'json', str(video)], text=True))
    stream = probe['streams'][0]
    fps = Fraction(stream['avg_frame_rate'])
    cap = cv2.VideoCapture(str(video))
    frames = []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    cap.release()
    assert len(frames) == int(stream['nb_frames']) == len(probe['frames']) == 93
    h, w = frames[0].shape[:2]
    assert (w, h) == (stream['width'], stream['height']) == (832, 480)
    records, sheets = [], []
    # Every source frame is stored at native resolution, once, with labels outside it.
    for start in range(0, len(frames), 12):
        group = frames[start:start + 12]
        rows, cols, label_h = (len(group) + 3) // 4, 4, 32
        canvas = Image.new('RGB', (cols * w, rows * (h + label_h)), '#101820')
        draw = ImageDraw.Draw(canvas)
        positions = []
        for j, frame in enumerate(group):
            i = start + j
            exact_t = Fraction(i, 1) / fps
            pts = Fraction(probe['frames'][i]['best_effort_timestamp_time'])
            assert abs(pts - exact_t) <= Fraction(1, 1000000)
            x, y = (j % cols) * w, (j // cols) * (h + label_h)
            draw.text((x + 8, y + 8), f'Frame {i:02d} | PTS {float(pts):.6f} s | t = {exact_t} s', fill='white')
            canvas.paste(Image.fromarray(frame), (x, y + label_h))
            positions.append((x, y + label_h, x + w, y + label_h + h))
            records.append({'frame': i, 'time_s_rational': str(exact_t), 'pts_s': str(pts),
                            'rgb_sha256': hashlib.sha256(frame.tobytes()).hexdigest(),
                            'sheet': f'dense/frames_{start:02d}_{start + len(group) - 1:02d}.webp',
                            'box_xyxy': positions[-1]})
        dest = HERE / records[-1]['sheet']
        canvas.save(dest, lossless=True, method=6)
        decoded = Image.open(dest).convert('RGB')
        for frame, box in zip(group, positions):
            assert np.array_equal(frame, np.asarray(decoded.crop(box)))
        assert dest.stat().st_size < 20_000_000
        sheets.append({'path': str(dest.relative_to(HERE)), 'sha256': sha(dest),
                       'bytes': dest.stat().st_size, 'first_frame': start,
                       'last_frame': start + len(group) - 1})
    manifest = {'source_commit': REV, 'clip': NAME, 'fps': str(fps),
                'decoded_frames': len(frames), 'native_size': [w, h],
                'pixel_verification': 'All 93 stored frame rectangles exactly equal OpenCV-decoded RGB arrays after lossless WebP readback.',
                'scope': 'Presentation only. Reader disagreement remains unresolved; no new period estimate or physical validation.',
                'environment': {'python': platform.python_version(), 'opencv': cv2.__version__, 'pillow': pillow_version},
                'sources': sources, 'dense_sheets': sheets, 'frames': records}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    cards = []
    base = '../../ro-3/task265'
    github = f'https://github.com/srirangam-r/cosmos-swarm/blob/{REV}/work/ro-3/task265'
    for name in names:
        r = results[name]
        label = 'READER DISAGREEMENT — unresolved' if name == NAME else 'Author reader outputs — not independently adjudicated'
        text = f"MP: {r.get('mp_T')} s ({r.get('mp_flag')}); ACF: {r.get('acf_T')} s ({r.get('acf_flag')})"
        links = ' · '.join(f'<a href="{github}/{sub}">{title}</a>' for title, sub in [
            ('published clip', f'dial_out/{name}.mp4'), ('sidecar', f'dial_out/{name}.json'),
            ('queue QC', f'dial_out/{name}.qc.json'), ('MP plot', f'qc_dial/{name}_mp.png'),
            ('ACF plot', f'qc_dial/{name}_acf.png')])
        cards.append(f'<article id="{name}"><h3>{name}</h3><strong>{label}</strong><p>{html.escape(text)}</p>'
                     f'<img class="author-sheet" loading="lazy" src="{base}/qc_dial/sheet_{name}.jpg" alt="Author sampled sheet for {name}">'
                     f'<p class="links">{links}</p></article>')
    dense = ''.join(f'<figure><figcaption>Frames {s["first_frame"]}–{s["last_frame"]}; every frame, native pixels stored.</figcaption>'
                    f'<a href="{s["path"]}"><img loading="lazy" src="{s["path"]}" alt="Consecutive frames {s["first_frame"]} to {s["last_frame"]}"></a></figure>' for s in sheets)
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pendulum dial — visual evidence index</title><style>
*{box-sizing:border-box}body{margin:0;background:#101820;color:#edf3f8;font:17px/1.55 system-ui,sans-serif}
main{max-width:1300px;margin:auto;padding:28px}h1{font-size:clamp(28px,4vw,44px);line-height:1.15}h2{margin-top:40px}
a{color:#89d8ff}p{max-width:1000px}.notice{background:#302919;border-left:5px solid #f6c75e;padding:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:20px}
article{background:#1b2a37;padding:18px;border:1px solid #394c5d;border-radius:8px;min-width:0}h3{overflow-wrap:anywhere;font-size:18px}
img{display:block;width:100%;height:auto}strong{color:#f6d899}.links{font-size:14px}figure{margin:20px 0}figcaption{margin-bottom:8px}
nav{display:flex;gap:18px;flex-wrap:wrap}.meta{color:#bed0dd;font-size:15px}code{overflow-wrap:anywhere}
</style><main><p class="meta">Task 317 · frozen author publication 823a546 · presentation artifact</p>
<h1>Pendulum dial: inspect the visual evidence</h1>
<div class="notice"><strong>Supplied-motion demonstration. Reader disagreement remains unresolved.</strong>
<p>The author tested 20 outputs from two scenes and two seeds. This index reuses every published sampled sheet; it adds no new experiment or period estimate. The requested third scene is absent. Prescribed period adherence does not establish a recovered physical constant or NVIDIA nonregression.</p></div>
<nav><a href="#disagreement">Every frame of the disputed clip</a><a href="#all20">All 20 author sheets</a><a href="manifest.json">Pixel/source manifest</a></nav>
<section id="disagreement"><h2>Disputed clip: pend11 · prescribed 0.600 s · seed 2</h2>
<p>Author-reported MP 0.293 s and ACF 0.599 s disagree. This page does not select a winner. Each panel below stores consecutive decoded frames at 832×480 with labels outside the image. Open a strip for native resolution. All 93 frames are retained, including frame 0 and frame 92.</p>
<p class="meta">24 fps; frame indices 0–92, t=i/24 s, final timestamp 3.833333 s. Exact rational times and native RGB hashes are in the manifest. Lossless WebP encoding round-trips every stored frame rectangle exactly. Labels and browser scaling are presentation only.</p>
''' + dense + '''</section><section id="all20"><h2>All 20 original author contact sheets</h2>
<p>These JPEGs are the unchanged author artifacts, sampled every 6 frames (0.25 s). They may obscure faster motion; use the dense strips above for the disputed clip. Numbers and flags below are copied from the frozen author JSON, not recomputed or endorsed. Task 316 owns the independent numerical/gate audit.</p>
<div class="grid">''' + ''.join(cards) + '''</div></section>
<p class="meta">No model generation, clip remeasurement, referee submission, physical certification, remote deployment or live media playback was performed for this artifact.</p></main></html>'''
    (HERE / 'index.html').write_text(page)
    print(json.dumps({'frames': len(records), 'lossless_sheets': len(sheets), 'author_sheets': len(cards),
                      'dense_bytes': sum(s['bytes'] for s in sheets), 'source_files_verified': len(sources)}))


if __name__ == '__main__':
    main()
