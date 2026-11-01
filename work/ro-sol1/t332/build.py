"""Package pinned author outputs; performs no media measurement or model job."""
from pathlib import Path
import hashlib
import html
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone

H = Path(__file__).resolve().parent
REPO = H.parents[2]
COMMIT = '124b6d5'
PREFIX = 'work/dk1/t277_rep/'

def git(*args):
    # Use HTTPS for this subprocess; do not modify the owner's SSH URL rewrite.
    env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0')
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'remote.origin.url=https://github.com/srirangam-r/cosmos-swarm.git', '-C', str(REPO), *args], env=env)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')

full_commit = git('rev-parse', COMMIT).decode().strip()
sources = []
names = git('ls-tree', '-r', '--name-only', COMMIT, '--', PREFIX).decode().splitlines()
for name in names:
    if name.endswith('.mp4'):
        continue
    data = git('show', f'{COMMIT}:{name}')
    target = H / 'source' / name.removeprefix(PREFIX)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    sources.append({'source': name, 'local': str(target.relative_to(H)),
                    'bytes': len(data), 'sha256': sha(data)})

write_json(H / 'source_receipt.json', {
    'commit': full_commit, 'scope': 'Exact existing author files, excluding mp4 blobs; no independent measurement.',
    'files': sources,
    'native_mp4s_in_source_tree': [n for n in names if '/clips/' in n and n.endswith('.mp4')],
})

data = json.loads((H / 'source/out/t276_results.json').read_text())
frames = json.loads((H / 'source/frames.json').read_text())
frame_map = {f['id']: f for f in frames}
arms = {'plain': 'Plain Nano', 'nphys': 'Nano-Phys', 'nphys_x17': 'Wrong period ×1.7'}
def fmt(v, digits=3):
    return '—' if v is None else f'{v:.{digits}f}'

summary = ''.join(f'<tr><th>{label}</th><td>{data["arms"][arm]["clean"]}/6</td><td>{data["arms"][arm]["within10"]}/6</td><td>{fmt(data["arms"][arm]["median_ratio"])}</td></tr>' for arm, label in arms.items())
rows = []
for row in data['rows']:
    period = frame_map[row['frame']]['P_real_s']
    acf = row['P_acf_s'] / period if row['P_acf_s'] is not None else None
    mp = row['P_mp_s'] / period if row['P_mp_s'] is not None else None
    cells = [row['frame'], arms[row['arm']], str(row['seed']), 'PASS' if row['clean'] else 'REJECT', fmt(acf), row['flag_acf'], fmt(mp), row['flag_mp'], fmt(row['r2_mp'], 2), fmt(row['flicker'], 4)]
    rows.append(f'<tr data-scene="{row["frame"]}" data-arm="{row["arm"]}" data-clip="{row["clip"]}">' + ''.join(f'<td>{html.escape(c)}</td>' for c in cells) + '</tr>')

source_url = f'https://github.com/srirangam-r/cosmos-swarm/tree/{full_commit}/{PREFIX.rstrip("/")}'
readout = '''# Fresh-input pendulum replication — attributed demo readout

dk1 reports that Nano-Phys transferred a supplied period on one fresh GAUGE input across three new seeds. On the second input, every Nano-Phys attempt failed the frozen motion-quality gate.

The frozen-gate totals are **3/6 Nano-Phys outputs within 10% of the supplied period**, versus **0/6 plain outputs within 10%**; plain has 1/6 clean outputs overall. All three Nano-Phys successes come from real_06. The accepted-output ACF median is 1.004807× the supplied period, with source bootstrap 95% interval [1.000645, 1.005342]. This interval resamples only the three accepted seeds from that one take; it is not uncertainty over new scenes or rigs.

For real_06, the wrong-period control follows the supplied 1.7× period on seeds 101–103 (ACF 1.725/1.697/1.700, measure_pend 1.716/1.679/1.706). These are ungated numerical readings: the frozen gate rejects all three because ACF flags check. Overall x17 remains 0/6 clean. Keep the numerical control observation and gate rejection together.

real_14 Nano-Phys is 0/3 clean. ACF ratios near 1 disagree with measure_pend; R² is 0.27–0.48. The source attributes the failure to a small-amplitude scaffold, but this addendum does not establish its cause. Task329 is a separate amplitude experiment owned by dk1. One still frame does not determine angular velocity; any supplied amplitude/direction is additional information.

The target periods (1.199895 and 1.187767 s) are measured from later real video under an assumed 25 Hz clock. This is conditional period transfer on two fresh inputs from one GAUGE rig, not period inference from the first frame or a general first-frame-only recipe. Manual geometry is ±6 px. The shipped release-from-rest proxy uses the visible angle (about74° or4°), and a harmonic large-angle swing does not establish correct nonlinear dynamics.

Setup: unchanged task276 contract/analyzer, Cosmos3-Nano, q8 server04e8e0de81, UniPC, sigma_start0.89844/start19, 832×480, 93frames at24fps, 35steps, CFG6, CPU noise; seeds101–103. Gate: ACF flag ok, luminance flicker<0.08, and reader period agreement within10%; it does not require measure_pend flag ok. The source's plain clean row has measure_pend flag check. Historical crossing reader289/rawFAIL and proposed non-rest state296 are separate and were not used here.

No NVIDIA scores were measured for task277. The separate task319 cohort reports a DOVER cost of about0.057; its seed1-only x17 control is consistent with a common proxy-path cost, without proving equivalence or cause. Plausibility judge, robot prediction and new rigs remain untested. See ../t328/ for that attributed quality scorecard.

This page reuses dk1's saved results, two input images and three contact sheets byte for byte. It is presentation and source verification, not another replication, planted validation or playback test. All18 generated clips have saved hashes; only3 native real06 Nano-Phys MP4s are committed in the source. Other clips stay with dk1. The source contact sheets crop/resize eight frames per clip; labels are the author's frozen gate labels.
'''
readout += f'\nSource: {source_url}\nBoard review6700 and task277 receipts: board_receipts.json\n'
readout += '\nReview6730 independently reaggregates the same saved results: only real_06 seed102 is clean in both plain and Nano-Phys. Selected arm medians are not a six-pair estimate of improvement. Real14 rejection is unresolved reader disagreement, not proof that the rendered swing failed or that amplitude caused it.\n'
(H / 'DEMO_READOUT.md').write_text(readout)

page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fresh-input pendulum replication | attributed demo</title>
<style>body{margin:0;background:#111821;color:#ecf0f6;font:17px/1.55 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px 22px 70px}h1{font-size:clamp(30px,5vw,49px);line-height:1.15;margin:14px 0 22px}h2{font-size:25px;margin-top:34px}a{color:#a3d7ff;overflow-wrap:anywhere}.tag{font-size:13px;letter-spacing:.12em;color:#aac7e9}.lead{font-size:22px}.card{padding:20px;background:#202c3c;border-radius:12px;margin:20px 0}.caution{border-left:4px solid #ffc76b;padding-left:18px;color:#ffe2b3}.muted{color:#bdc8d8}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}img{max-width:100%;height:auto;display:block;border-radius:6px}figcaption{font-size:14px;color:#bdc8d8;margin-top:8px}table{border-collapse:collapse;min-width:100%;font-size:15px}th,td{padding:9px;text-align:left;border-bottom:1px solid #415167;white-space:nowrap}th{color:#a3d7ff}.scroll{overflow-x:auto}select{font:inherit;color:#ecf0f6;background:#202c3c;border:1px solid #667d98;border-radius:5px;padding:8px;max-width:100%}label{display:inline-block;margin:0 18px 12px 0}.strip{max-height:850px;object-fit:contain;object-position:top left}nav{display:flex;flex-wrap:wrap;gap:18px;margin-top:24px}code{overflow-wrap:anywhere}details{margin-top:20px}li{margin:9px 0}@media(max-width:620px){main{padding:23px 15px 50px}.grid{grid-template-columns:1fr}.lead{font-size:20px}.card{padding:15px}}
</style><main>
<div class="tag">TASK277 • DK1 RESULTS • SOURCE124b6d5 • PRESENTATION ONLY</div>
<h1>A supplied pendulum period transfers on a fresh input. The second input fails QC.</h1>
<p class="lead">Three new seeds succeed on real_06. All three Nano-Phys attempts on real_14 are rejected by the frozen motion-quality gate.</p>
<p class="muted">Attributed to dk1's completed task277 and review6700. This addendum reuses existing outputs; it adds no independent measurement.</p>
<div class="card"><h2 style="margin-top:0">Keep every attempt in the denominator</h2><div class="scroll"><table id="summary"><thead><tr><th>Arm</th><th>Clean</th><th>Within10% + clean</th><th>Accepted ACF median ×P</th></tr></thead><tbody>SUMMARY</tbody></table></div>
<p class="muted">Each arm:2inputs ×3seeds. Nano-Phys's3/6successes all come from real_06. Accepted-only source interval:[1.000645,1.005342], resampling three seeds from one take.</p></div>
<p class="caution"><strong>The target period is supplied from later real video.</strong> This demonstrates conditional period transfer, not inference from the first frame. Two fresh inputs share one GAUGE rig.</p>
<section><h2>The two source inputs</h2><div class="grid"><figure><img src="source/inputs/real_06.png" alt="Pinned real06 input: pendulum far left of vertical"><figcaption>real_06:visible angle≈74°; supplied P=1.199895s. Nano-Phys3/3clean.</figcaption></figure><figure><img src="source/inputs/real_14.png" alt="Pinned real14 input: pendulum near vertical"><figcaption>real_14:visible angle≈4°; supplied P=1.187767s. Nano-Phys0/3clean.</figcaption></figure></div></section>
<section><h2>The control transfers numerically, with gate rejection retained</h2><p>On real_06, ×1.7 gives ACF ratios1.725/1.697/1.700 and measure_pend ratios1.716/1.679/1.706 over seeds101–103. These are <strong>ungated numerical readings</strong>. ACF flags <em>check</em>, so all three remain rejected. Overall ×1.7 is0/6clean.</p><p>On real_14, ACF values near1 disagree with the other reader (R²0.27–0.48). The cause remains a hypothesis; task329 tests a supplied amplitude separately. A still pose does not determine angular velocity.</p></section>
<section id="rows"><h2>All18 saved rows</h2><p class="muted">Ratios below divide the author's saved period by its supplied reference. Rejected values stay visible; they are excluded from accepted-only summaries. A dash means the source period is missing.</p>
<label>Input <select id="scene"><option value="all">Both inputs</option><option>real_06</option><option>real_14</option></select></label><label>Arm <select id="arm"><option value="all">All arms</option><option value="plain">Plain Nano</option><option value="nphys">Nano-Phys</option><option value="nphys_x17">Wrong period ×1.7</option></select></label><p id="count" aria-live="polite">18 saved rows</p>
<div class="scroll"><table id="clips"><thead><tr><th>Input</th><th>Arm</th><th>Seed</th><th>Frozen gate</th><th>ACF/P</th><th>ACF flag</th><th>MP/P</th><th>MP flag</th><th>MP R²</th><th>Flicker</th></tr></thead><tbody>ROWS</tbody></table></div>
<details><summary>Exact frozen gate and uncertainty scope</summary><p>ACF flag ok AND luminance flicker&lt;0.08 AND reader period agreement within10%. It does not require the measure_pend flag to be ok: plain real_06 seed102 is source-clean with MP flag check. No gate has been changed. The source bootstrap resamples only three accepted Nano-Phys clips from one take, not all six attempts or independent rigs. No additional uncertainty has been estimated here.</p></details></section>
<section id="strips"><h2>The author's contact sheets</h2><label>Sheet <select id="sheet"><option value="nphys">Nano-Phys</option><option value="plain">Plain Nano</option><option value="nphys_x17">Wrong period ×1.7</option></select></label><figure><a id="sheet-link" href="source/out/strip_nphys.jpg"><img class="strip" id="sheet-image" src="source/out/strip_nphys.jpg" alt="Author contact sheet, Nano-Phys, six rows and eight frames per row"></a><figcaption>Unmodified source sheets: six rows per arm, eight cropped/resized frames per clip. First three rows real_06; last three real_14; seeds101–103. Author labels include the frozen gate. Click for full resolution. Static images are not a playback check.</figcaption></figure></section>
<section><h2>What this demo does not establish</h2><ul><li>A general first-frame-only recipe: period comes from future real video; geometry is manually supplied (±6px). Release-from-rest is assumed. The large-angle harmonic proxy does not certify nonlinear physics.</li><li>NVIDIA non-regression: task277 has no new NVIDIA scores. The separate <a href="../t328/index.html">task319 quality scorecard</a> reports about0.057 lower DOVER on its own cohort. Its seed1-only control is consistent with a common proxy-path cost; equivalence and cause are unresolved.</li><li>Independent validation by this page: it packages dk1's outputs. Historical crossing reader289/rawFAIL and non-rest state296 were not used. Plausibility judge, robot prediction and new rigs remain untested.</li></ul>
<p class="muted">Actual setup reported by source: Cosmos3-Nano; q8 server04e8e0de81; UniPC; sigma_start0.89844/start19; 832×480;93frames at24fps;35steps;CFG6;CPU noise; seeds101–103. Real reference periods use an assumed25Hz clock.</p></section>
<section id="evidence"><h2>Frozen evidence and presentation notes</h2><p>18/18clips generated according to dk1; hashes and sidecars retained. Only the three real_06 Nano-Phys MP4s are committed in the source. The other native clips remain with dk1; no regeneration or playback is claimed here.</p>
<nav><a href="SOURCE_URL">Original source and three native MP4s</a><a href="source/README.md">Author README</a><a href="source/out/t276_results.json">All source results</a><a href="source/out/ungated_ratios.md">Author ungated table</a><a href="source/analyze.py">Frozen analyzer</a><a href="source/jobs.jsonl">Exact jobs</a><a href="source/frames.json">Supplied references</a><a href="source/out/clips_SHA256SUMS">18 clip hashes</a><a href="source_receipt.json">Source byte receipt</a><a href="board_receipts.json">Board receipts</a><a href="DEMO_READOUT.md">Plain readout</a><a href="../t315/demo_card.html">Original held-out demo</a><a href="../t328/index.html">Quality-cost scorecard</a></nav>
<p class="muted">Reading context: <a href="https://arxiv.org/abs/2607.03732">ProxyUp §§4–5</a> separates proxy motion and appearance; <a href="https://arxiv.org/abs/2608.05948">GAUGE C.3</a> separates period, geometry and fit diagnostics; <a href="https://arxiv.org/abs/2501.09038v2">Physics-IQ metrics</a> separates spatial and temporal agreement. This page reuses those distinctions and the existing results.</p></section>
</main><script>
function filter(){let count=0;document.querySelectorAll('#clips tbody tr').forEach(row=>{row.hidden=!((scene.value==='all'||row.dataset.scene===scene.value)&&(arm.value==='all'||row.dataset.arm===arm.value));if(!row.hidden)count++});document.querySelector('#count').textContent=count+' saved rows'}
const scene=document.querySelector('#scene'),arm=document.querySelector('#arm');scene.addEventListener('change',filter);arm.addEventListener('change',filter);
document.querySelector('#sheet').addEventListener('change',e=>{const name=e.target.value;document.querySelector('#sheet-image').src='source/out/strip_'+name+'.jpg';document.querySelector('#sheet-link').href='source/out/strip_'+name+'.jpg';document.querySelector('#sheet-image').alt='Author contact sheet, '+e.target.selectedOptions[0].textContent+', six rows and eight frames per row'});
</script></html>'''
page = page.replace('SUMMARY', summary).replace('ROWS', ''.join(rows)).replace('SOURCE_URL', source_url)
page = page.replace('<section id="rows">', '<p class="caution">Independent saved-result review6730 finds only one of six main-arm pairs clean in both arms (real_06 seed102). Selected arm medians are not a six-pair improvement estimate. Real14 QC rejection shows unresolved reader disagreement, not proof that the rendered swing failed or that amplitude caused it.</p><section id="rows">')
for before, after in {
    'TASK277': 'TASK 277', 'SOURCE124b6d5': 'SOURCE 124b6d5',
    'task277': 'task 277', 'review6700': 'review #6700', 'review6730': 'review #6730',
    'task329': 'task 329', 'task319': 'task 319', 'task276': 'task 276',
    'Within10%': 'Within 10%', 'Each arm:2inputs ×3seeds': 'Each arm: 2 inputs × 3 seeds',
    "Nano-Phys's3/6successes": "Nano-Phys's 3/6 successes",
    'All18 saved rows': 'All 18 saved rows', '18/18clips': '18/18 clips',
    'seeds101–103': 'seeds 101–103', '0/6clean': '0/6 clean',
    '3/3clean': '3/3 clean', '0/3clean': '0/3 clean', 'near1 ': 'near 1 ',
    'real_06:visible': 'real_06: visible', 'real_14:visible': 'real_14: visible',
    'R²0.27': 'R² 0.27', 'ACF ratios1.725': 'ACF ratios 1.725',
    'ratios1.716': 'ratios 1.716', 'reader289/rawFAIL': 'reader 289/raw FAIL',
    'state296': 'state 296', 'about0.057': 'about 0.057',
    'server04e8e0de81': 'server 04e8e0de81', 'sigma_start0.89844': 'sigma_start 0.89844',
    '93frames': '93 frames', '35steps': '35 steps', 'CFG6': 'CFG 6',
    'at24fps': 'at 24 fps', 'assumed25Hz': 'assumed 25 Hz',
}.items():
    page = page.replace(before, after)
(H / 'index.html').write_text(page)
(H / 'README.md').write_text('''# Task332: attributed task277 demo

Open `index.html` locally after cloning this folder and adjacent t315/t328, or read `DEMO_READOUT.md`. Source files and author sheets are saved byte for byte under `source/`; MP4 blobs are linked to the original commit rather than duplicated. This is presentation and provenance verification, not independent physical replication.

Reproduce packaging from the shared repository root:

```bash
python3 work/ro-sol1/t332/build.py
node work/ro-sol1/t332/render.cjs
```

`build.py` needs git access to124b6d5. `render.cjs` reuses task328's dependency-free CDP transport and an installed Brave; set DEMO_BROWSER for another compatible browser. No listening port or model service is started. Browser evidence covers static layout, source values, filters, image loading and links, not video playback. The build also checks only the two announced gallery HTTP roots for availability.
''')

checks = []
def check(name, ok):
    checks.append({'name': name, 'passed': bool(ok)})
    if not ok:
        raise AssertionError(name)

for source in sources:
    check('exact source: ' + source['source'], sha((H / source['local']).read_bytes()) == source['sha256'])
slots = {(r['frame'], r['arm'], r['seed']) for r in data['rows']}
check('all18 expected source slots', slots == {(f,a,s) for f in frame_map for a in arms for s in (101,102,103)})
check('all18 display rows retained', page.count('data-clip=') == 18)
for arm in arms:
    group = [r for r in data['rows'] if r['arm'] == arm]
    check('display retains saved gate totals: '+arm, len(group) == 6 and sum(r['clean'] for r in group) == data['arms'][arm]['clean'])
check('real14 nphys all rejected', not any(r['clean'] for r in data['rows'] if r['frame']=='real_14' and r['arm']=='nphys'))
check('source x17 rejects remain0/6', data['arms']['nphys_x17']['clean'] == 0)
check('three native mp4s present in source commit', sum('/clips/' in n and n.endswith('.mp4') for n in names) == 3)
for folder in ('t292','t315','t328'):
    for path in git('ls-tree','-r','--name-only','HEAD','--',f'work/ro-sol1/{folder}').decode().splitlines():
        check('prior file unchanged: '+path, sha((REPO/path).read_bytes()) == sha(git('show',f'HEAD:{path}')))
write_json(H / 'verification.json', {'scope':'Packaging checks only; no independent scoring or physics validation.','checks':checks,'passed':all(c['passed'] for c in checks)})

http = {'utc':datetime.now(timezone.utc).isoformat(),'scope':'HTTP availability only; no playback or physics validation.','urls':[]}
for url in ('http://sha-devel:8085','http://board.tail0c526a.ts.net:8031/demos/'):
    try:
        with urllib.request.urlopen(url,timeout=8) as response:
            body=response.read()
            http['urls'].append({'url':url,'status':response.status,'bytes':len(body),'sha256':sha(body)})
    except Exception as exc:
        http['urls'].append({'url':url,'error':str(exc)})
write_json(H/'gallery_http.json',http)
print(json.dumps({'checks':len(checks),'passed':True,'exact_source_files':len(sources),'http':http}))
