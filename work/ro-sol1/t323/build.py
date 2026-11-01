#!/usr/bin/env python3
"""Present attributed evidence-scope clarifications; leave frozen evidence intact."""
from pathlib import Path
import hashlib
import html
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REV = '067d5a18b77a76edfd38b031d8130506c52801d2'
messages = json.loads((HERE / 'reviews_6398_6399.json').read_text())
receipts = []
for m in messages:
    receipts.append(f'<details id="receipt-{m["id"]}"><summary>Codex-1’s original message #{m["id"]}</summary><pre>{html.escape(m["body"])}</pre></details>')
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pendulum dial · evidence scope clarification</title>
<style>
:root{font-family:system-ui,sans-serif;color:#183039;background:#edf2f2;color-scheme:light}*{box-sizing:border-box}body{margin:0}main{max-width:1080px;margin:auto;padding:32px 24px 60px}h1{font-size:clamp(28px,4vw,43px);line-height:1.15}p{line-height:1.6;max-width:85ch}.meta{color:#4d6570;font-size:13px;text-transform:uppercase;letter-spacing:.04em}.lead{font-size:21px}.card{background:white;border:1px solid #ccdcde;border-radius:12px;padding:22px;margin:24px 0}.tablewrap{max-width:100%;overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:16px}td,th{text-align:left;vertical-align:top;padding:14px;border-bottom:1px solid #dbe4e6;line-height:1.6}th{min-width:150px}thead{background:#e3edee}.limit{border-left:4px solid #b57922;padding-left:18px}a{color:#075d73;overflow-wrap:anywhere;text-underline-offset:3px}.links{display:flex;flex-wrap:wrap;gap:12px}.links a{background:white;border:1px solid #a7bec4;border-radius:6px;padding:12px}summary{cursor:pointer;font-weight:650;line-height:1.5}details{margin:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 system-ui}.note{font-size:14px;color:#415f6b}blockquote{margin:0;border-left:4px solid #25816c;padding-left:18px;line-height:1.65;font-size:18px}@media(max-width:650px){main{padding:24px 16px}.card{padding:16px}.lead{font-size:18px}table,tbody,tr,td,tbody th{display:block;width:100%}thead{position:absolute;left:-10000px}tbody th{min-width:0;padding:14px 0 0;border:0}td{padding:10px 0;border:0;font-size:15px}td::before{display:block;font-weight:650;color:#4d6570;font-size:13px}td:nth-child(2)::before{content:"What was checked"}td:nth-child(3)::before{content:"Supported scope"}tr{border-bottom:1px solid #dbe4e6;padding-bottom:12px}}
</style><main>
<p class="meta">Task 323 · attributed clarification of task 316 / demo 322 · 1 Nov 2026</p>
<h1>Pendulum dial: what the numerical audit establishes</h1>
<p class="lead">Task 316 reanalyzes the same saved period-reader outputs. Its results describe the published 20-clip grid.</p>
<section class="card"><div class="tablewrap" tabindex="0" aria-label="Evidence scope table"><table id="scope"><thead><tr><th>Evidence</th><th>What was checked</th><th>Supported scope</th></tr></thead><tbody>
<tr><th scope="row">Period response</th><td>Agy-4 recomputed regressions and gates from ro-3’s saved reader outputs and QC files.</td><td>Numerical reanalysis of the same reader outputs. Independent 20-clip measurement and new-seed replication remain unperformed by this audit.</td></tr>
<tr><th scope="row">Uncertainty</th><td>The source bootstrap resamples individual clip rows in a two-scene, two-seed grid.</td><td>Row-bootstrap summaries conditional on this small grid. Scene-general uncertainty remains unmeasured.</td></tr>
<tr><th scope="row">Flicker gate</th><td>Codex-1 reports that all 20/20 named QC files exist and parse with numeric flicker below 0.08 (median 0.0039; range 0.0029–0.0050).</td><td>Saved-metadata verification. The audit’s missing-file fallback did not affect this grid; independent flicker measurement from video remains unperformed by this check.</td></tr>
<tr><th scope="row">Disputed 0.60 s clip</th><td>Codex-1’s bounded turning-point review supports about 0.60 s in one clip; the raw MP value of 0.2934 s remains in all-clip statistics.</td><td>One unvalidated visual check, with approximate frame-picking bounds.</td></tr>
</tbody></table></div><p class="note">Attribution: codex-1 messages #6398 and #6399, preserved verbatim below. Ro-sol1 packages these statements without rerunning the audit, readers or video measurements.</p></section>
<p class="limit">The demonstration concerns adherence to a supplied proxy tempo. The calibrated 1.186 s reference, absent third scene, reader disagreement and unproved first-frame/prompt physical inference limits still apply. Low saved flicker values alone cannot certify visual quality. NVIDIA nonregression remains unproved here.</p>
<section class="card"><h2>Suggested demo wording</h2><blockquote id="demo-wording">A numerical reanalysis of saved reader outputs reproduces the supplied pendulum tempo response over the published 20-clip grid. Reported bootstrap intervals describe this two-scene, two-seed grid. All 20 saved flicker files were present and numeric; one clip retains a period-reader disagreement. Independent video remeasurement and broader physical generalization remain open.</blockquote></section>
<div class="links"><a href="../t322/index.html">Original audit readout and all 20 rows</a><a href="../t320/index.html">Attributed visual review</a><a href="../t317/index.html#disagreement">All 93 disputed-clip frames</a><a href="reviews_6398_6399.json">Exact clarification receipts</a></div>
<p class="note">Read the original audit readout together with this clarification. Its frozen wording and artifacts are preserved. This addendum changes the evidence label without changing any numerical result.</p>
RECEIPTS
<p class="note">Source audit: agy-4, <a href="https://github.com/srirangam-r/cosmos-swarm/tree/27e60e7caad2874a6be3875c4a2d73a2274a15ae/work/agy-4/task316_pendulum_dial_audit">27e60e7</a>. Native experiment: ro-3, 823a546. Numerical readout: ro-sol1, 067d5a1.</p>
</main></html>'''
(HERE / 'index.html').write_text(page.replace('RECEIPTS', '\n'.join(receipts)))
frozen = []
for folder in ('t317', 't320', 't322'):
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', REV,
                                       f'work/ro-sol1/{folder}/'], cwd=ROOT).decode().splitlines()
    for rel in tracked:
        file = ROOT / rel
        original = subprocess.check_output(['git', 'show', f'{REV}:{rel}'], cwd=ROOT)
        if original != file.read_bytes():
            raise ValueError(f'Frozen artifact changed: {rel}')
        frozen.append({'path': rel, 'sha256': hashlib.sha256(original).hexdigest()})
(HERE / 'frozen_evidence.json').write_text(json.dumps({'commit': REV, 'files': frozen}, indent=2) + '\n')
print(f'Built clarification; {len(frozen)} frozen evidence files unchanged.')
