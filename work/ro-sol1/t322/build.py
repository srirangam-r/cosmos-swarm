#!/usr/bin/env python3
"""Package agy-4's frozen audit; do not rerun any measurements or fits."""
from pathlib import Path
import hashlib
import html
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REV = '27e60e7caad2874a6be3875c4a2d73a2274a15ae'
SOURCE = 'work/agy-4/task316_pendulum_dial_audit/'
receipts = {}
for name in ('audit_results.json', 'README.md', 'audit_pendulum_dial.py'):
    data = subprocess.check_output(['git', 'show', f'{REV}:{SOURCE}{name}'], cwd=ROOT)
    dest = HERE / ('source_' + name)
    dest.write_bytes(data)
    receipts[name] = {'commit': REV, 'path': SOURCE + name, 'sha256': hashlib.sha256(data).hexdigest()}
audit = json.loads((HERE / 'source_audit_results.json').read_text())
review = json.loads((HERE / 'review_6380.json').read_text())
esc = html.escape
fits = []
labels = [('acf_all_20', 'ACF · all clips'), ('mp_selected_17', 'MP · flag=ok only'),
          ('mp_all_20', 'MP · all clips'), ('both_clean_accepted', 'ACF · all gates pass')]
for key, label in labels:
    f = audit['fits'][key]
    fits.append(f'<tr data-fit="{key}"><th scope="row">{label}</th><td>{f["n"]}/20</td>'
                f'<td>{f["slope"]:.4f} ± {f["se_slope"]:.4f}</td>'
                f'<td>[{f["slope_ci_95"][0]:.4f}, {f["slope_ci_95"][1]:.4f}]</td>'
                f'<td>{f["r2"]:.5f}</td><td>{100*f["max_relative_error"]:.2f}%</td></tr>')
rows = []
for r in audit['rows']:
    status = 'pass' if r['all_pass'] else 'flagged'
    rows.append(f'<tr data-status="{status}"><th scope="row">{esc(r["clip"].removeprefix("dial_"))}</th>'
                f'<td>{r["target_s"]:.3f}</td><td>{r["acf_s"]:.4f} / {r["acf_flag"]}</td>'
                f'<td>{r["mp_s"]:.4f} / {r["mp_flag"]}</td><td>{100*r["tool_gap"]:.2f}%</td>'
                f'<td>{r["flicker"]:.4f}</td><td>{status}</td></tr>')
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pendulum dial · attributed audit readout</title>
<style>
:root{font-family:system-ui,sans-serif;color:#183039;background:#edf2f2;color-scheme:light}*{box-sizing:border-box}body{margin:0}main{max-width:1180px;margin:auto;padding:36px 24px 64px}h1{font-size:clamp(28px,4.5vw,46px);line-height:1.12;margin:16px 0}h2{font-size:23px;margin-top:32px}p{line-height:1.6;max-width:86ch}.meta{color:#4d6570;text-transform:uppercase;font-size:13px;letter-spacing:.05em}.lead{font-size:21px}.card{background:white;border:1px solid #ccdcde;border-radius:12px;padding:24px;margin:24px 0}.counts{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.count{padding:16px;border-top:4px solid #25816c;background:white}.count strong{display:block;font-size:32px}.count span{font-size:14px;line-height:1.4}.tablewrap{max-width:100%;overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:12px 10px;border-bottom:1px solid #dbe4e6;white-space:nowrap}thead{background:#e3edee}tbody tr[data-status=flagged]{background:#fff0d5}a{color:#075d73;text-underline-offset:3px;overflow-wrap:anywhere}.links{display:flex;flex-wrap:wrap;gap:12px}.links a{background:white;border:1px solid #a7bec4;border-radius:6px;padding:12px}.limit{border-left:4px solid #b57922;padding-left:18px}.note{font-size:14px;color:#415f6b}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 system-ui}summary{cursor:pointer;font-weight:650}details{margin:20px 0}code{overflow-wrap:anywhere}button{padding:10px 14px;background:white;border:1px solid #819fa7;border-radius:5px;color:inherit;cursor:pointer}button[aria-pressed=true]{background:#164c56;color:white}.filter{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:16px 0}#rowcount{font-size:14px}@media(max-width:650px){main{padding:24px 16px}.card{padding:16px}.counts{grid-template-columns:repeat(2,1fr)}.lead{font-size:18px}td,th{padding:10px 8px}}
</style><main>
<p class="meta">Task 322 · presentation of agy-4’s completed audit #6380 / task 316</p>
<h1>Nano follows a supplied pendulum tempo across the published dial</h1>
<p class="lead">The independent numerical audit reproduces ACF’s response over 0.6–2.0 seconds. One clip’s readers disagree; the full table retains that result.</p>
<p>Grid: two scenes (pend10, pend11) × two seeds × five commanded periods = 20 clips. Each clip is 93 frames at 24 fps (3.875 seconds). The commanded period is supplied by a proxy.</p>
<div class="counts" aria-label="Separate audit denominators">
<div class="count"><strong>20/20</strong><span>ACF flags are “ok”</span></div>
<div class="count"><strong>19/20</strong><span>Reader gap ≤ 10%</span></div>
<div class="count"><strong>20/20</strong><span>Flicker below 0.08</span></div>
<div class="count"><strong>17/20</strong><span>Both flags + gap + flicker pass</span></div></div>
<section class="card"><h2>Keep the selections visible</h2>
<div class="tablewrap" tabindex="0" aria-label="Fit table scroll area"><table id="fits"><thead><tr><th>Reader / selection</th><th>Included</th><th>Slope ± SE</th><th>95% bootstrap interval</th><th>R²</th><th>Largest error to command</th></tr></thead><tbody>FIT_ROWS</tbody></table></div>
<p class="note">Values are formatted from agy-4’s frozen JSON. ± denotes the source’s OLS standard error; the bootstrap interval is shown separately. Fits and their intervals describe this grid; they do not establish transfer to new scenes. “All gates pass” uses the ACF value on 17 accepted clips.</p></section>
<h2>The discrepant clip remains in the all-clip result</h2>
<p><code>pend11_P600_s2</code>: command 0.600 s; ACF 0.5986 s; MP 0.2934 s (flag “check”); symmetric reader gap 68.43%. Ag y-4’s audit interprets this as a half-period lock. Codex-1’s bounded visual review supports about 0.60 s; its visual method is unvalidated. The two 2.0 s clips flagged by MP remain within about 1.02% of command but have limited cycle counts.</p>
<div class="links"><a href="../t317/index.html#disagreement">Inspect all 93 frames</a><a href="../t320/index.html">Read codex-1’s visual review</a><a href="source_audit_results.json">Frozen audit JSON</a></div>
<h2>Scope of the demonstration</h2>
<p class="limit">This demonstrates adherence to prescribed proxy tempo. The 1.186 s reference was calibrated to observed video through a 0.35 m length; independent physical prediction from first frame and prompt remains unproved. The requested third scene is absent. Low measured luminance flicker does not certify visual quality or zero flashing. This page supplies no new physical measurement, reader validation or NVIDIA scoreboard pass.</p>
<details id="source-note"><summary>Source inconsistencies and attribution</summary><p>The frozen audit README differs from its JSON and board review #6380: for example, its table says 16/20 both-clean while the JSON records 17/20, and its ACF slope is 1.0053 while the JSON records 1.00501139. This page renders the JSON. The original README is preserved for review. Its attribution of visual adjudication to ro-sol1 is incorrect: codex-1 made review #6330; ro-sol1 published the frame index and attributed review page. The reviewer’s SE and bootstrap intervals are displayed separately here. Source authors’ files remain unchanged.</p><a href="source_README.md">Frozen source README</a> · <a href="source_audit_pendulum_dial.py">Frozen audit code</a> · <a href="source_receipt.json">Hashes and provenance</a></details>
<h2>All 20 source rows</h2><p class="note">Periods in seconds; flicker is the source’s dimensionless luminance-change measure. Horizontal tables can be scrolled on narrow screens.</p>
<div class="filter"><button type="button" id="all" aria-pressed="true">All clips</button><button type="button" id="flagged" aria-pressed="false">Flagged clips</button><span id="rowcount" aria-live="polite">Showing 20 of 20</span></div>
<div class="tablewrap" tabindex="0" aria-label="All clips table scroll area"><table id="clips"><thead><tr><th>Clip</th><th>Command</th><th>ACF / flag</th><th>MP / flag</th><th>Reader gap</th><th>Flicker</th><th>All gates</th></tr></thead><tbody>CLIP_ROWS</tbody></table></div>
<details><summary>Read agy-4’s original board review #6380</summary><pre id="review">REVIEW_BODY</pre><a href="review_6380.json">Original review receipt</a></details>
<p class="note">Prepared by ro-sol1 as an attributed readout. Numerical source: agy-4, commit <a href="https://github.com/srirangam-r/cosmos-swarm/tree/27e60e7caad2874a6be3875c4a2d73a2274a15ae/work/agy-4/task316_pendulum_dial_audit">27e60e7</a>. Native experiment: ro-3, 823a546. Prior-work note #6387: <a href="https://arxiv.org/abs/2607.03732">ProxyUp</a>, <a href="https://arxiv.org/abs/2608.05948">GAUGE</a>, <a href="https://arxiv.org/abs/2501.09038v2">Physics-IQ</a>.</p>
</main><script>for(const id of ['all','flagged'])document.getElementById(id).onclick=()=>{let count=0;for(const row of document.querySelectorAll('#clips tbody tr')){row.hidden=id==='flagged'&&row.dataset.status!=='flagged';if(!row.hidden)count++}for(const key of ['all','flagged'])document.getElementById(key).setAttribute('aria-pressed',String(key===id));document.getElementById('rowcount').textContent=`Showing ${count} of 20`};</script></html>'''
page = page.replace('Ag y-4', 'Agy-4').replace('FIT_ROWS', ''.join(fits)).replace('CLIP_ROWS', ''.join(rows)).replace('REVIEW_BODY', esc(review['body']))
(HERE / 'index.html').write_text(page)
receipts['review_6380.json'] = {'board_message':6380, 'author':'agy-4', 'sha256':hashlib.sha256((HERE/'review_6380.json').read_bytes()).hexdigest()}
(HERE / 'source_receipt.json').write_text(json.dumps(receipts, indent=2)+'\n')
print(json.dumps({'source_commit':REV, 'source_rows':len(audit['rows']), 'page_bytes':len(page.encode()), 'sources':receipts}))
