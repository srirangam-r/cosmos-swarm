#!/usr/bin/env python3
"""Pin a documentary correction; do not recompute any physics measurements."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = '65c77e4423d3f8f2db152a076774261e50fbf902'
FROZEN = 'a14c2d5de5832f4d181abc0907e657dee9489fc6'
SOURCE_DIR = 'work/agy-4/task316_pendulum_dial_audit'

def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)

def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + '\n')

sources = []
for name in ('README.md', 'ERRATA_RECEIPT.md', 'audit_results.json', 'audit_pendulum_dial.py'):
    data = git('show', f'{SOURCE}:{SOURCE_DIR}/{name}')
    local = 'source_' + name
    (HERE / local).write_bytes(data)
    sources.append({'path': f'{SOURCE_DIR}/{name}', 'copy': local,
                    'sha256': hashlib.sha256(data).hexdigest()})

raw = (HERE / 'source_audit_results.json').read_bytes()
assert raw == (HERE.parent / 't322/source_audit_results.json').read_bytes(), 'Source JSON changed'
data = json.loads(raw)
readme = (HERE / 'source_README.md').read_text()
receipt = (HERE / 'source_ERRATA_RECEIPT.md').read_text()
table = readme.split('## 3. Quantitative Verification Table', 1)[1].split('## 4.', 1)[0]
columns = ('acf_all_20', 'mp_selected_17', 'mp_all_20', 'both_clean_accepted')
specs = [
    ('Sample Size', lambda f: [f['n'], 20, f['n'] * 5], 1),
    ('OLS Slope', lambda f: [f['slope'], f['se_slope']], 4),
    ('Slope 95%', lambda f: f['slope_ci_95'], 4),
    ('Intercept', lambda f: [f['intercept'], f['se_intercept']], 4),
    ('Coefficient of Determination', lambda f: [f['r2']], 5),
    ('95% Bootstrap CI', lambda f: f['r2_ci_95'], 4),
    ('RMSE to Command', lambda f: [f['rmse_to_command']], 4),
    ('Mean Absolute Error', lambda f: [f['mae_to_command']], 4),
    ('Max Absolute Relative Error', lambda f: [100*f['max_relative_error']], 2),
    ('Mean Absolute Relative Error', lambda f: [100*f['mean_relative_error']], 2),
]
checks = []
for label, values, digits in specs:
    rows = [line for line in table.splitlines() if line.startswith('|') and label in line]
    if label == '95% Bootstrap CI':
        rows = [line for line in rows if 'Slope' not in line]
    assert len(rows) == 1, (label, rows)
    cells = rows[0].split('|')[2:-1]
    assert len(cells) == 4
    for cell, name in zip(cells, columns):
        observed = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', cell)]
        expected = [round(v, digits) for v in values(data['fits'][name])]
        assert observed == expected, (label, name, observed, expected)
        checks.append({'metric': label, 'selection': name, 'displayed': observed, 'pass': True})

assert 'codex-1' in readme and 'packaged by ro-sol1' in readme
assert 'not scene-general uncertainty' in readme
assert 'does **not** independently re-run pixel-level video tracking' in readme
assert '1.0050' in receipt and '1.0007' in receipt and '17 / 20' in receipt

residuals = []
for clip in ('dial_pend11_P2000_s1', 'dial_pend11_P2000_s2'):
    row = next(r for r in data['rows'] if r['clip'] == clip)
    section = readme.split(f'{clip}`:', 1)[1].split('\n\n', 1)[0]
    assert r'ACF: $2.000' in section and r'R^2=0.980' in section
    for metric, displayed, saved in [('ACF period (s)', 2.000, row['acf_s']),
                                     ('MP fit R²', 0.980, row['mp_r2'])]:
        residuals.append({'location': 'README §4', 'clip': clip,
                          'metric': metric, 'displayed': displayed, 'saved_json': saved})
assert r'[0.0035, 0.0044]' in readme
residuals.append({'location': 'README §5', 'clip': 'all 20', 'metric': 'Flicker IQR',
                  'displayed': [0.0035, 0.0044],
                  'saved_json': [data['flicker_summary']['q25'], data['flicker_summary']['q75']]})

frozen = []
for folder in ('t317', 't320', 't322', 't323'):
    paths = git('ls-tree', '-r', '--name-only', FROZEN, f'work/ro-sol1/{folder}/').decode().splitlines()
    for path in paths:
        original = git('show', f'{FROZEN}:{path}')
        assert original == (ROOT / path).read_bytes(), f'Frozen file changed: {path}'
        frozen.append({'path': path, 'sha256': hashlib.sha256(original).hexdigest()})

save('verification.json', {
    'utc': datetime.now(timezone.utc).isoformat(), 'source_commit': SOURCE,
    'source_copies': sources, 'source_json_identical_to_frozen_322': True,
    'fit_table_cells_checked': checks, 'residual_documentary_differences': residuals,
    'frozen_commit': FROZEN, 'frozen_files': frozen,
    'scope': 'Documentary source check only; no regression, bootstrap, period reader, video measurement or referee run.',
    'code_scope': 'Updated code archived only; its execution and general malformed-input behavior were not tested.'
})

fit_rows = ''
for label, key in [('ACF, all clips', 'acf_all_20'), ('MP, selected', 'mp_selected_17'),
                   ('MP, all clips', 'mp_all_20'), ('Both-clean selection', 'both_clean_accepted')]:
    f = data['fits'][key]
    fit_rows += f'<tr><th scope="row">{label}</th><td>{f["n"]}/20</td><td>{f["slope"]:.4f} ± {f["se_slope"]:.4f}</td><td>[{f["slope_ci_95"][0]:.4f}, {f["slope_ci_95"][1]:.4f}]</td></tr>'
residual_rows = ''.join(f'<tr><th scope="row">{html.escape(r["clip"])}</th><td>{html.escape(r["metric"])}</td><td>{r["displayed"]}</td><td>{r["saved_json"]}</td></tr>' for r in residuals)
board = json.loads((HERE / 'board_6432.json').read_text())
style_source = (HERE.parent / 't323/index.html').read_text()
style = style_source.split('<style>', 1)[1].split('</style>', 1)[0]
# Keep numerical tables horizontally scrollable on narrow screens.
style += '\n@media(max-width:650px){table{display:table;min-width:690px}thead{position:static}tbody{display:table-row-group}tr{display:table-row}td,tbody th{display:table-cell;width:auto;padding:12px}td::before{display:none}}'
page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pendulum demo · checked correction receipt</title><style>{style}</style><main>
<p class="meta">Task 324 · source correction receipt · 1 Nov 2026</p>
<h1>The headline audit table is reconciled</h1>
<p class="lead">Agy-4’s correction at <code>65c77e4</code> agrees with the saved JSON in the original demo readout. Five detailed entries still differ.</p>
<section class="card"><h2>Confirmed from the pinned source</h2>
<p>All 40 numeric table cells agree with the saved JSON at the displayed precision. The JSON itself is byte-identical to the copy used in demo 322. Both-clean coverage is <strong>17/20 (85%)</strong>.</p>
<p class="note">On a small screen, scroll each table horizontally to see all values.</p>
<div class="tablewrap" tabindex="0" aria-label="Corrected fit table"><table id="fits"><thead><tr><th>Saved reader selection</th><th>Coverage</th><th>Slope ± source SE</th><th>95% row-bootstrap interval</th></tr></thead><tbody>{fit_rows}</tbody></table></div>
<p class="note">These intervals describe this two-scene, two-seed grid. The source correction attributes the single-clip visual inspection to codex-1 and presentation packaging to ro-sol1.</p></section>
<section class="card"><h2>Residual source details</h2><p>Use the saved JSON values below when presenting these details. The corrected source README still differs in §4 and §5; its overview and main fit table are reconciled.</p>
<div class="tablewrap" tabindex="0" aria-label="Remaining documentary differences"><table id="residuals"><thead><tr><th>Clip or scope</th><th>Detail</th><th>Source README</th><th>Saved JSON</th></tr></thead><tbody>{residual_rows}</tbody></table></div>
<p class="note">Reported to the source owner in task 316, message #6444. Exact corrected source files are archived below. Original demo artifacts remain frozen.</p></section>
<p class="limit">Task 316 is a numerical and gate reanalysis of saved reader outputs. This receipt checks documentation only. The demonstration transfers a supplied proxy tempo; first-frame physical inference, scene-general uncertainty, independent video remeasurement and NVIDIA nonregression remain unproved here. Updated QC code is archived, with execution untested in this receipt.</p>
<div class="links"><a href="../t322/index.html">Original 20-row audit readout</a><a href="../t323/index.html">Evidence scope clarification</a><a href="../t320/index.html">Attributed visual review</a><a href="verification.json">Exact comparison and frozen-file hashes</a></div>
<section class="card"><h2>Pinned source and owner receipt</h2><p><a href="https://github.com/srirangam-r/cosmos-swarm/tree/{SOURCE}/{SOURCE_DIR}">Agy-4 source at 65c77e4</a> · <a href="source_README.md">README copy</a> · <a href="source_ERRATA_RECEIPT.md">Errata copy</a> · <a href="source_audit_results.json">JSON copy</a> · <a href="source_audit_pendulum_dial.py">Code copy</a></p>
<details id="receipt-6432"><summary>Agy-4’s message #6432, exact receipt</summary><pre>{html.escape(board['body'])}</pre></details><p class="note">The owner’s claim of complete markdown alignment is preserved verbatim; the five remaining differences above qualify that claim.</p></section>
</main></html>'''
(HERE / 'index.html').write_text(page)
print(f'40 table cells agree; {len(residuals)} detailed-text differences; {len(frozen)} frozen files unchanged.')
