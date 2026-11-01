"""Present existing task329 outputs. No tracking, inference or scoring is run."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json
import os
import subprocess
import urllib.request

H = Path(__file__).resolve().parent
R = H.parents[2]
C = 'eb5aa13'
PREFIX = 'work/dk1/t329_amp/'

def git(*args):
    env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0')
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c',
        'remote.origin.url=https://github.com/srirangam-r/cosmos-swarm.git', '-C', str(R), *args], env=env)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def save(name, value):
    (H / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

commit = git('rev-parse', C).decode().strip()
names = git('ls-tree', '-r', '--name-only', C, '--', PREFIX).decode().splitlines()
sources = []
def snapshot(rev, name, local):
    data = git('show', f'{rev}:{name}')
    p = H / local
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    sources.append(dict(commit=git('rev-parse', rev).decode().strip(), source=name,
                        local=local, bytes=len(data), sha256=sha(data)))

for name in names:
    if '/proxies/' not in name:
        snapshot(C, name, 'source/' + name.removeprefix(PREFIX))
snapshot(C, 'work/dk2/t276/out/t276_results.json', 'baseline/t276_results.json')
snapshot('124b6d5', 'work/dk1/t277_rep/out/t276_results.json', 'baseline/t277_results.json')
save('source_receipt.json', dict(scope='Byte-exact author files, including three native clips; proxy MP4s omitted. No independent measurement.',
    commit=commit, files=sources, omitted=[n for n in names if '/proxies/' in n]))

d = json.loads((H / 'source/out/t276_results.json').read_text())
frames = {f['id']: f for f in json.loads((H / 'source/frames.json').read_text())}
arms = {'nphys': 'Supplied 18° + P', 'nphys_x17': 'Supplied 18° + 1.7P'}
historical = []
for task in ('t276', 't277'):
    prior = json.loads((H / f'baseline/{task}_results.json').read_text())
    historical.extend(r for r in prior['rows'] if r['frame'] in frames and r['arm'] == 'nphys')

def fmt(v, n=3):
    return '—' if v is None else f'{v:.{n}f}'

rows = []
for row in d['rows']:
    period = frames[row['frame']]['P_real_s']
    cells = [row['frame'], arms[row['arm']], str(row['seed']), 'PASS' if row['clean'] else 'REJECT',
             fmt(row['P_acf_s'] / period), row['flag_acf'], fmt(row['P_mp_s'] / period),
             row['flag_mp'], fmt(row['r2_mp'], 2), fmt(row['flicker'], 4)]
    rows.append('<tr data-scene="{frame}" data-arm="{arm}" data-clip="{clip}">'.format(**row)
                + ''.join('<td>' + html.escape(c) + '</td>' for c in cells) + '</tr>')
summary = ''.join(f'<tr><th>{label}</th><td>{d["arms"][arm]["clean"]}/9</td><td>{d["arms"][arm]["within10"]}/9</td><td>{fmt(d["arms"][arm]["median_ratio"])}</td></tr>' for arm, label in arms.items())
url = f'https://github.com/srirangam-r/cosmos-swarm/tree/{commit}/work/dk1/t329_amp'
readout = f'''# Supplied-amplitude Nano-Phys demo — attributed task 329 result

dk1 reports **7/9 clean outputs within 10% of a supplied pendulum period**, compared with **0/9 clean historical outputs** using the release-from-rest proxy on the same three takes and seeds. This tests the whole supplied non-rest 18° proxy package under the frozen reader/gate. Review #6738/#6753 challenges the claim that amplitude alone is the cause: initial velocity, swing extent, trajectory and reader-visible pixels change together. Improved rendered motion, visibility to the readers, or both can improve this gate.

The per-take clean counts are real_09 2/3, real_14 3/3, real_16 2/3. The two rejected Nano-Phys outputs (real_09 s2, real_16 s3) have ACF periods near the supplied period but disagree with measure_pend (2.9885s/R²0.223 and 0.5880s/R²0.321). Accepted real_09 s3 itself has measure_pend flag check and R²0.265; the frozen gate does not require that flag or a minimum R². Keep this qualification with the 7/9 count.

The wrong-period arm numerically follows ~1.7P on both readers in all 9 attempts. **Only 4/9 pass the frozen gate**; five have ACF check and remain rejected. The 9/9 numerical observation is ungated. No plain arm was newly generated in task 329; its empty summary object is not a measured 0/9 plain result.

The source accepted-only ACF median is 0.994120991×P with bootstrap 95% [0.992122073, 1.001472444]; MP median is 0.998767857×P. The interval resamples seven accepted clip rows from three takes of one rig with shared seed labels. It is conditional on that selection and does not establish uncertainty over independent scenes/rigs. All 9 historical comparisons are retained in baseline/, with source commits in source_receipt.json. This packaging validates saved-file consistency, not new physics.

The input supplies P from later real video under an assumed 25Hz clock, manual pivot/bob geometry, amplitude18° and direction inward. Neither amplitude, direction nor P is inferred from frame0. Frame0 alone does not determine angular velocity. Setup: Cosmos3-Nano q8 server04e8e0de81, UniPC, start19/σ0.89844, CPU noise, 832×480, 93frames/24fps, 35steps, CFG6, unchanged276prompt; seeds1–3 for real_09/16 and101–103 for real_14. Request flow_shift10 does not identify the executed schedule; use the saved server receipts.

Gate: ACF flag ok AND luminance flicker<0.08 AND |P_MP/P_ACF−1|≤0.10. measure_pend v1's planted PASS is attributed to the source; no new validation has been performed. Low measured luminance flicker does not establish shape stability: the author reports some ring-like bob deformation, unscored. This task has no NVIDIA-scoreboard result. Separate task319 reports ~0.057 DOVER cost on another cohort (../t328/); plausibility, robot prediction and general non-regression remain unproved.

The page offers the three native MP4s the author committed (one first available seed per take, all source-clean), not a random or representative selection. All18 outcomes and two unchanged nine-row source contact sheets stay visible. Source-native bytes are not a before/after composite. Local browser checks cover decoding, seeking, advancing playback, layout, values and links; they do not validate physics or shape quality. The other15 generated MP4s remain with dk1; hashes/sidecars for all18 are preserved. No recipe defaults were changed here.

Source: {url}
Finding #6747; design/post-result challenges #6738/#6753: board_receipts.json.
'''
(H / 'DEMO_READOUT.md').write_text(readout)
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supplied-amplitude pendulum | attributed demo</title>
<style>body{margin:0;background:#121923;color:#edf2f9;font:17px/1.55 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px 22px 70px}h1{font-size:clamp(30px,5vw,49px);line-height:1.15}h2{font-size:25px;margin:32px 0 14px}a{color:#a5d6ff;overflow-wrap:anywhere}.tag{color:#a9c6eb;font-size:13px;letter-spacing:.1em}.lead{font-size:22px}.muted,figcaption{color:#bdc8d8}.card{background:#202c3b;padding:20px;border-radius:12px;margin:20px 0}.caution{border-left:4px solid #ffcb77;padding-left:17px;color:#ffe2b3}.scroll{overflow-x:auto}table{border-collapse:collapse;min-width:100%;font-size:15px}th,td{padding:9px;white-space:nowrap;text-align:left;border-bottom:1px solid #425167}th{color:#a5d6ff}select{font:inherit;padding:8px;background:#202c3b;color:#edf2f9;border:1px solid #7990aa;border-radius:5px;max-width:100%}label{display:inline-block;margin:0 16px 12px 0}img,video{width:100%;height:auto;display:block;border-radius:6px}figure{margin:0}figcaption{font-size:14px;margin-top:9px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}nav{display:flex;flex-wrap:wrap;gap:18px;margin-top:25px}li{margin:10px 0}.strip{max-height:1000px;object-fit:contain;object-position:top left}code{overflow-wrap:anywhere}@media(max-width:620px){main{padding:22px 15px 50px}.grid{grid-template-columns:1fr}.card{padding:15px}.lead{font-size:20px}}</style>
<main><div class="tag">TASK 329 • DK1 RESULTS • SOURCE eb5aa13 • PRESENTATION ONLY</div>
<h1>A supplied non-rest proxy raises the clean-gate count to 7/9.</h1>
<p class="lead">Same three takes and seeds: the earlier release-from-rest proxy was 0/9 clean. The 18° proxy changes initial velocity, motion extent and measurement visibility together.</p>
<p class="muted">Attributed provisional result from dk1. Source-file and playback checks here add no independent physics measurement.</p>
<div class="card"><h2 style="margin-top:0">Every attempt stays in the denominator</h2><div class="scroll"><table id="summary"><thead><tr><th>Proxy arm</th><th>Clean</th><th>Clean + within 10% of P</th><th>Accepted ACF median ×P</th></tr></thead><tbody><tr><th>Historical release-from-rest</th><td>0/9</td><td>0/9</td><td>—</td></tr>SUMMARY</tbody></table></div><p class="muted">Three takes × three seeds. Each new arm has 9 clips. No new plain arm was generated. Accepted-only ACF interval [0.992122, 1.001472] resamples seven selected rows; it is not scene-general uncertainty.</p></div>
<p class="caution"><strong>Period, amplitude and direction are supplied.</strong> P comes from later real video; 18° and inward direction are assumptions. This does not demonstrate a first-frame-only recipe. Review #6738/#6753 challenges amplitude-only causation: rendered motion, reader visibility, or both may explain the gate gain.</p>
<section id="playback"><h2>Play the three source-native examples</h2><p>One committed first available seed per take, all source-clean. These examples are selected, not the full experiment. Bob deformation was reported by the author and was not scored.</p><label>Example <select id="example"><option value="real_09">real_09 · seed 1</option><option value="real_14">real_14 · seed 101</option><option value="real_16">real_16 · seed 1</option></select></label><video id="native" controls muted playsinline preload="metadata" src="source/clips/t329a_real_09_nphys_s1.mp4" aria-label="Source-native supplied-amplitude Nano-Phys example"></video><p><a id="native-link" href="source/clips/t329a_real_09_nphys_s1.mp4">Open native MP4</a> · 832×480, 93 frames at 24 fps. No compositing or retiming here.</p></section>
<section><h2>The three source inputs</h2><div class="grid">INPUTS</div></section>
<section><h2>Numerical control and gate acceptance are different</h2><p>The wrong-period ×1.7 arm follows the longer target numerically on both readers in <strong>9/9 attempts</strong>. Only <strong>4/9 pass the frozen gate</strong>; five remain rejected with ACF <em>check</em>. This 9/9 observation is ungated.</p><p>Two main-arm outputs are rejected for reader disagreement: real_09 seed 2 and real_16 seed 3. Another accepted row, real_09 seed 3, has MP flag <em>check</em> and R² 0.265. The frozen gate does not require the MP flag or a minimum R².</p></section>
<section id="rows"><h2>All 18 saved outcomes</h2><p class="muted">Ratios divide each saved reader period by the supplied P, including rejected outputs. They are display calculations, not new tracking.</p><label>Take <select id="scene"><option value="all">All takes</option><option>real_09</option><option>real_14</option><option>real_16</option></select></label><label>Arm <select id="arm"><option value="all">Both arms</option><option value="nphys">Supplied 18° + P</option><option value="nphys_x17">Supplied 18° + 1.7P</option></select></label><p id="count" aria-live="polite">18 saved rows</p><div class="scroll"><table id="clips"><thead><tr><th>Take</th><th>Arm</th><th>Seed</th><th>Frozen gate</th><th>ACF/P</th><th>ACF flag</th><th>MP/P</th><th>MP flag</th><th>MP R²</th><th>Flicker</th></tr></thead><tbody>ROWS</tbody></table></div><details><summary>Frozen rule, uncertainty and calibration</summary><p>ACF flag ok AND luminance flicker&lt;0.08 AND |P_MP/P_ACF−1|≤0.10. No MP-flag or R² gate. Accepted-only bootstrap pools 7 rows from 3 takes of one rig, with shared seed labels. The source attributes planted PASS to measure_pend v1; no new calibration or independent replication was run here.</p></details></section>
<section id="strips"><h2>The author's complete contact sheets</h2><label>Sheet <select id="sheet"><option value="nphys">Supplied 18° + P</option><option value="nphys_x17">Supplied 18° + 1.7P</option></select></label><figure><a id="sheet-link" href="source/out/strip_nphys.jpg"><img class="strip" id="sheet-image" src="source/out/strip_nphys.jpg" alt="Unmodified author contact sheet: nine rows, eight frames per row"></a><figcaption>Unchanged author sheets: real_09, real_14, real_16; three seeds per take and eight cropped/resized frames per row. Author labels retain rejections. Static sheets are not a playback test. Only the three committed native clips above are packaged; hashes and sidecars cover all 18.</figcaption></figure></section>
<section><h2>Keep the claim within this evidence</h2><ul><li>The gate improvement supports the whole supplied non-rest proxy package on these clips. It does not identify amplitude as the sole cause or establish general scene transfer.</li><li>Supplied P uses later-video timing (assumed 25 Hz); amplitude/direction and manual geometry are extra inputs. One still pose does not determine angular velocity.</li><li>No NVIDIA-scoreboard check for these 18 clips. The separate <a href="../t328/index.html">quality scorecard</a> reports ~0.057 DOVER cost on another cohort. Plausibility, robot prediction and non-regression remain unproved.</li><li>Low luminance flicker does not certify stable shape. Some bob deformation is reported and unscored. Default changes belong to recipe owners; none are applied here.</li></ul><details><summary>Generation settings and sampler provenance</summary><p>Cosmos3-Nano, q8 server 04e8e0de81, UniPC, start step 19 at σ 0.89844, CPU noise, 832×480, 93 frames at 24 fps, 35 steps, CFG 6, task 276 prompt. Seeds 1–3 for real_09/16 and 101–103 for real_14. Request flow_shift=10 is not an executed-schedule guarantee; source server sidecars are preserved.</p></details></section>
<nav><a href="DEMO_READOUT.md">Presentation readout</a><a href="source/out/t276_results.json">Saved results</a><a href="source/analyze.py">Frozen analyzer</a><a href="source/build_jobs.py">Original job builder</a><a href="source_receipt.json">Byte receipts</a><a href="board_receipts.json">Finding and challenges</a><a href="baseline/t276_results.json">Historical 276</a><a href="baseline/t277_results.json">Historical 277</a><a href="SOURCE_URL">Pinned original source</a><a href="../t332/index.html">Earlier fresh-input demo</a></nav></main>
<script>const scenes={real_09:1,real_14:101,real_16:1};const q=s=>document.querySelector(s);function filter(){let count=0;document.querySelectorAll('#clips tbody tr').forEach(r=>{r.hidden=!((q('#scene').value==='all'||r.dataset.scene===q('#scene').value)&&(q('#arm').value==='all'||r.dataset.arm===q('#arm').value));if(!r.hidden)count++});q('#count').textContent=count+' saved rows'}q('#scene').addEventListener('change',filter);q('#arm').addEventListener('change',filter);q('#sheet').addEventListener('change',e=>{const src='source/out/strip_'+e.target.value+'.jpg';q('#sheet-image').src=src;q('#sheet-link').href=src});q('#example').addEventListener('change',e=>{q('#native').pause();const src='source/clips/t329a_'+e.target.value+'_nphys_s'+scenes[e.target.value]+'.mp4';q('#native').src=src;q('#native').load();q('#native-link').href=src});</script></html>'''
inputs = ''.join(f'<figure><img src="source/{f["image"]}" alt="Pinned {fid} near-vertical pendulum input"><figcaption>{fid}: supplied P={f["P_real_s"]:.6f}s; new main arm {sum(r["clean"] for r in d["rows"] if r["frame"]==fid and r["arm"]=="nphys")}/3 clean.</figcaption></figure>' for fid, f in sorted(frames.items()))
page = page.replace('SUMMARY', summary).replace('ROWS', ''.join(rows)).replace('INPUTS', inputs).replace('SOURCE_URL', url)
(H / 'index.html').write_text(page)
(H / 'README.md').write_text('''# Task 334: attributed, playable task 329 demo

Open `index.html` locally for three unchanged source-native examples, all 18 saved outcomes, input images, contact sheets and evidence limits. `DEMO_READOUT.md` is the human presentation text. Author result eb5aa13, challenges #6738/#6753, source bytes and provenance are preserved. This is presentation/source consistency and playback QA, not independent physics replication.

From repo root:

```sh
python3 work/ro-sol1/t334/build.py
node work/ro-sol1/t334/render.cjs
```

Build requires git access to pinned commits and checks the two announced gallery HTTP roots. Render uses installed Brave over anonymous CDP pipes, without a listener; `DEMO_BROWSER` overrides the binary. The browser checks native decoding, seek, playback progress, layout, selectors, labels and source values. Those checks do not measure physics, shape stability, or model quality. No GPU/model job, recipe-default change or shared-service deployment occurs.
''')

checks = []
def check(name, condition):
    checks.append(dict(name=name, passed=bool(condition)))
    if not condition:
        raise AssertionError(name)

for s in sources:
    check('exact author bytes: ' + s['source'], sha((H / s['local']).read_bytes()) == s['sha256'])
check('18 unique expected slots', {(r['frame'],r['arm'],r['seed']) for r in d['rows']} == {(fid,a,s) for fid,f in frames.items() for a in arms for s in f['seeds']})
check('18 rows displayed', page.count('data-clip=') == 18)
for arm in arms:
    group = [r for r in d['rows'] if r['arm'] == arm]
    check('saved count: ' + arm, len(group)==9 and sum(r['clean'] for r in group)==d['arms'][arm]['clean'])
check('main 7/9; control 4/9', d['arms']['nphys']['clean']==7 and d['arms']['nphys_x17']['clean']==4)
check('no new plain arm', d['arms']['plain']['n']==0 and not any(r['arm']=='plain' for r in d['rows']))
check('historical nine paired slots', {(r['frame'],r['seed']) for r in historical} == {(r['frame'],r['seed']) for r in d['rows'] if r['arm']=='nphys'} and len(historical)==9)
check('historical zero clean', not any(r['clean'] for r in historical))
check('three native source videos', len(list((H / 'source/clips').glob('*.mp4')))==3)
check('accepted low R2/check row disclosed', any(r['clean'] and r['flag_mp']=='check' and r['r2_mp']<.3 for r in d['rows'] if r['arm']=='nphys'))
for s in sources:
    if s['local'].endswith('.mp4'):
        check('native clip hash: ' + s['local'], s['sha256'] in (H / 'source/out/clips_SHA256SUMS').read_text())
for folder in ('t328','t332'):
    for name in git('ls-tree','-r','--name-only','HEAD','--','work/ro-sol1/'+folder).decode().splitlines():
        check('previous file unchanged: ' + name, sha((R/name).read_bytes())==sha(git('show','HEAD:'+name)))
save('verification.json', dict(scope='Source/display packaging checks only, no new tracking or physics.', checks=checks, passed=all(c['passed'] for c in checks)))
http = dict(utc=datetime.now(timezone.utc).isoformat(), scope='HTTP availability only, no deployed playback or physics check.', urls=[])
for endpoint in ('http://sha-devel:8085','http://board.tail0c526a.ts.net:8031/demos/'):
    try:
        with urllib.request.urlopen(endpoint, timeout=8) as response:
            body = response.read()
            http['urls'].append(dict(url=endpoint,status=response.status,bytes=len(body),sha256=sha(body)))
    except Exception as exc:
        http['urls'].append(dict(url=endpoint,error=str(exc)))
save('gallery_http.json', http)
print(json.dumps(dict(passed=True, checks=len(checks), source_files=len(sources), http=http)))
