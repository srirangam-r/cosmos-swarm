"""Build an attributed presentation from frozen outputs; no media scoring."""
from pathlib import Path
import hashlib
import html
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
receipt = json.loads((HERE / 'source_receipt.json').read_text())
source = json.loads((HERE / 'source/t319_results.json').read_text())
fused = source['metrics']['dover_fused']
checks = []

def check(label, passed):
    checks.append({'check': label, 'passed': bool(passed)})
    assert passed, label

for entry in receipt['source_files']:
    check('source bytes: ' + entry['local'], hashlib.sha256((HERE / entry['local']).read_bytes()).hexdigest() == entry['sha256'])
for entry in receipt['frozen_prior_files']:
    check('prior immutable: ' + entry['path'], hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256'])
check('42 generated plus 6 real rows', len(source['per_clip']) == 48)
for arm, seeds in [('plain', [1, 2, 3]), ('nphys', [1, 2, 3]), ('nphys_x17', [1])]:
    check('complete source slots: ' + arm, all(f'{scene}_{arm}_s{seed}' in source['per_clip'] for scene in source['scenes'] for seed in seeds))
check('fused headline agrees with source means', abs(fused['nphys_mean'] - fused['plain_mean'] - fused['delta_scene_mean']) < 1e-12)
check('source interval below proposed margin', fused['delta_boot95_exact'][1] < -0.030)
mf = {a: json.loads((HERE / f'source/mf_{a}.json').read_text()) for a in ['plain', 'nphys']}
check('MF uses disclosed convention', all(m['ddof'] == 0 and m['zero_denominator_policy'] == 'zero' for m in mf.values()))
check('six zero-denominator nphys groups', sum(p['zero_denominator'] for p in mf['nphys']['bands'][0]['prompts']) == 6)

prefix = 'https://github.com/srirangam-r/cosmos-swarm/blob/' + receipt['commit'] + '/work/dk2/t319/'
links = ''.join(f'<li><a href="{html.escape(e["local"])}">{html.escape(Path(e["local"]).name)}</a> · <a href="{prefix}{html.escape(Path(e["local"]).name)}">pinned original</a></li>' for e in receipt['source_files'])
scene_rows = ''.join(f'<tr><th scope="row">{s}</th><td>{d:+.5f}</td></tr>' for s, d in zip(source['scenes'], fused['delta_per_scene']))
page = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nano-Phys · quality cost on the held-out pendulum benchmark</title>
<style>
:root{color-scheme:light;--ink:#15283a;--muted:#506274;--line:#d9e2e8;--paper:#fff;--red:#9e332e;--teal:#17645d}*{box-sizing:border-box}body{margin:0;background:#edf2f4;color:var(--ink);font:17px/1.55 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:42px 28px 64px}a{color:#135c82;text-underline-offset:3px;overflow-wrap:anywhere}h1{max-width:850px;font-size:clamp(32px,5vw,54px);line-height:1.08;letter-spacing:-.035em;margin:18px 0}h2{font-size:24px;line-height:1.2}p{max-width:900px}small,.muted{color:var(--muted)}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:750;color:var(--muted)}.pill{display:inline-block;border:1px solid #cba7a4;color:var(--red);border-radius:30px;padding:4px 11px;font-size:13px}.lead{font-size:20px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:24px;margin:20px 0}.grid .card{margin:0}.number{font-size:46px;font-weight:750;color:var(--red);letter-spacing:-.04em}.warning{border-left:4px solid var(--red);padding-left:18px}.notice{background:#fff6e8;border:1px solid #d3b687;border-radius:10px;padding:18px}.metric{border-top:1px solid var(--line);margin-top:22px;padding-top:20px}.metric-head{display:flex;gap:20px;align-items:center;justify-content:space-between}select{font:inherit;border:1px solid #9eafb9;border-radius:7px;padding:8px;max-width:100%;background:white;color:var(--ink)}.valuegrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:20px 0}.valuegrid strong{font-size:30px;display:block}.valuegrid span{font-size:13px;color:var(--muted)}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}td,th{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line)}th{font-weight:650}blockquote{margin:0;font-size:20px}details{border-top:1px solid var(--line);padding-top:15px;margin-top:20px}summary{cursor:pointer;font-weight:650}li{margin:7px 0}.sources{font-size:14px;columns:2}.footer{font-size:14px}.scope{font-size:15px}.nowrap{white-space:nowrap}button:focus-visible,a:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #168d99;outline-offset:4px}@media(max-width:680px){main{padding:25px 16px 40px}.grid{grid-template-columns:1fr}.card{padding:19px}.metric-head{display:block}.metric-head select{margin-top:8px}.valuegrid strong{font-size:25px}.sources{columns:1}td,th{padding:8px 5px;font-size:14px}}
</style>
<main>
<div class="eyebrow">Demo evidence update · task 328 / source task 319</div>
<h1>Nano-Phys has a visual-quality cost on this benchmark.</h1>
<span class="pill">Author-reported · provisional</span>
<p class="lead">dk2 scored the existing held-out pendulum clips. Compared with plain Nano, Nano-Phys lost <strong>0.057 DOVER</strong> on the matched grid. The motion-fidelity score needs a prominent qualification.</p>
<p class="muted scope">18 plain + 18 Nano-Phys clips · 6 held-out input images × seeds 1–3 · 6 wrong-period clips at seed 1 · 6 real references from one pendulum rig.</p>
<div class="grid">
 <section class="card"><div class="eyebrow">DOVER fused · Nano-Phys minus plain</div><div class="number">−0.0572</div><p><strong>Source JSON 95% interval: [−0.0675, −0.0488]</strong><br>All 6 take means and all 18 matched pairs are negative.</p><p class="scope">The author enumerates all 6⁶ resamples of take means after averaging 3 seeds per arm. This interval is conditional on these six takes and the fixed shared seeds; it does not cover new rigs or prompts.</p></section>
 <section class="card"><div class="eyebrow">Threshold and seed baseline</div><h2>Below the proposed −0.030 margin</h2><p>The whole interval is below that threshold. The source explicitly says this margin was proposed by agy-3 and <strong>never approved</strong>.</p><p class="scope">Author's plain seed SD: <strong>0.0444</strong> per clip; estimated SD of a 3-seed mean: <strong>0.0257</strong>. These are seed baselines, separate from the bootstrap interval and repeated DOVER crops.</p></section>
</div>
<section class="card" id="scores"><h2>Read each score in its own units</h2><p>Values below are copied from the frozen source JSON. Selecting a metric changes the displayed means and paired summary.</p>
<div class="metric-head"><label for="metric">Metric</label><select id="metric"><option value="dover_fused">DOVER fused</option><option value="dover_technical">DOVER technical</option><option value="dover_aesthetic">DOVER aesthetic</option><option value="dd_binary">Binary dynamic degree</option><option value="dd_norm">Continuous flow proxy (dd_norm)</option></select></div>
<div class="valuegrid"><div><span>Plain · 18 clips</span><strong id="plain"></strong></div><div><span>Nano-Phys · 18 clips</span><strong id="nphys"></strong></div><div><span>Real · 6 references</span><strong id="real"></strong></div></div>
<p id="metric-summary"></p><p id="metric-note" class="scope"></p>
<details><summary>Six take-level DOVER differences</summary><table><thead><tr><th>Input take</th><th>Nano-Phys − plain</th></tr></thead><tbody>SCENE_ROWS</tbody></table><p class="scope">Each difference averages seeds 1–3 within each arm. The source names these “scenes”; the real references are repeated takes of one physical rig.</p></details>
</section>
<section class="card"><h2>A motion-fidelity score of 1.000 is degenerate here</h2><p>Source MF: <strong>plain 0.238 → Nano-Phys 1.000</strong>. Every real reference and every Nano-Phys clip has binary DD = 0; plain has 7/18 clips flagged dynamic. Under <code>ddof=0</code> and the disclosed <code>0/0 → 0</code> MC convention, even a static output earns MF = 1 against this zero-DD reference.</p>
<p class="warning"><strong>This score cannot certify correct pendulum motion.</strong> MF implements the published Cosmos 3 formula using an approximate DD scorer. It is not an NVIDIA-identical evaluation.</p>
<p class="scope">Continuous flow proxy: real <strong>1.94</strong>, plain <strong>4.83</strong>, Nano-Phys <strong>0.44</strong>. Nano-Phys undershoots real flow. The proxy does not identify whether bob motion, camera motion or background motion was lost.</p></section>
<section class="card"><h2>What this evidence covers</h2>
<ul><li><strong>Existing clips, new scores:</strong> the author re-scored 42 task-276 clips on an RTX 4060 using the unchanged shared scorer, with 3 DOVER repetitions. Their source records MP4 hashes and reports 42/42 sidecars identical to task 276.</li>
<li><strong>Supplied dynamics:</strong> Nano-Phys used a simulated proxy, sigma 0.90, and a period derived from later real-video frames. The earlier <a href="../t315/DEMO_READOUT.md">12/18 period-transfer demo</a> remains conditional on that supplied period; it is not a first-frame-only physics solution.</li>
<li><strong>Small, shared-rig reference:</strong> six 93-frame real windows have nominal 25 fps metadata versus generated 24 fps. For MF, the author re-encoded the real references at 24 fps, reporting unchanged frame sequence. Retiming changes playback time; it does not establish the original camera clock or an independently matched physical duration.</li>
<li><strong>Implementation scope:</strong> shared DD uses torchvision RAFT/PyAV and differs from original VBench. Nvidia's original report used 5-second clips and roughly 100 real references per FPS band. This grid is shorter and narrower.</li>
<li><strong>Wrong-period comparison:</strong> x17 minus Nano-Phys is −0.00090 DOVER when restricted to their six matched seed-1 pairs. This is a descriptive comparison, not equivalence or identification of the cause of the quality drop.</li>
<li><strong>Still untested:</strong> plausibility judge, robot prediction, new prompts/rigs, and the cause of the DOVER drop.</li></ul>
</section>
<section class="notice" id="demo-copy"><div class="eyebrow">Suggested wording for a human to apply</div><blockquote>“Nano-Phys transfers a supplied pendulum period, with a visual-quality cost. On six held-out input images × three seeds, the author reports a 0.057 DOVER drop versus plain Nano. The higher motion-fidelity score is degenerate on these zero-DD references; a general first-frame-only recipe and full scoreboard non-regression remain unproved.”</blockquote></section>
<section class="card" id="receipts"><h2>Attribution and frozen receipts</h2><p>Measurements and analysis: <strong>dk2, task 319, finding #6690</strong>, source commit <code>9e92945</code>. Presentation: ro-sol1, task 328. No new video measurement or independent physics validation is claimed by this page.</p>
<p class="scope">The source JSON gives [−0.0674511, −0.0488436]; the author's board message/README quotes [−0.068, −0.049]. This page uses the JSON values. Near-equal real/plain means do not establish equivalence. The author's causal wording about the proxy path is retained in the source receipt, with cause left unresolved in this readout.</p>
<p><a href="board_receipts.json">Exact board messages</a> · <a href="source_receipt.json">SHA256 / immutable-file receipt</a> · <a href="DEMO_READOUT.md">Plain-text readout</a> · <a href="verification.json">Packaging checks</a></p>
<details><summary>All 13 pinned source files</summary><ul class="sources">SOURCE_LINKS</ul></details>
<details><summary>Prior work used to frame the labels</summary><p class="scope"><a href="https://arxiv.org/abs/2607.03732">ProxyUp §§4.2–5.2</a>: supplied proxy dynamics and appearance quality are separate measures. <a href="https://arxiv.org/abs/2311.17982">VBench G.1</a>: flow-based dynamic presence and the static-video tradeoff. <a href="https://arxiv.org/abs/2606.02800">Cosmos 3 E.2</a>: three-seed MF and FPS-band reference design. These sources frame reporting; they do not validate this Nano-Phys run.</p></details>
</section><p class="footer">Append-only addendum. Earlier demo artifacts are preserved. The judged root README and reports are untouched. This local static page is not a deployment to the shared gallery.</p>
</main><script id="score-data" type="application/json">SOURCE_DATA</script><script>
const evidence=JSON.parse(document.getElementById('score-data').textContent);
function update(){const k=document.getElementById('metric').value,r=evidence.metrics[k];for(const [id,key] of [['plain','plain_mean'],['nphys','nphys_mean'],['real','real_mean']])document.getElementById(id).textContent=r[key].toFixed(4);document.getElementById('metric-summary').textContent=`Nano-Phys − plain: ${r.delta_scene_mean.toFixed(4)} · source 95% bootstrap interval [${r.delta_boot95_exact.map(v=>v.toFixed(4)).join(', ')}]`;document.getElementById('metric-note').textContent=k==='dd_norm'?'dd_norm is a continuous optical-flow proxy in normalized pixels, not NVIDIA binary dynamic degree. Less flow alone is not a physics improvement.':k==='dd_binary'?'Binary DD is dynamic presence, not a period or trajectory measurement. Zero DD does not imply a motionless bob; small motion may miss this scorer.':'Higher is better within this shared DOVER implementation. These source scores are not calibrated to the scale of NVIDIA’s published table.';}
document.getElementById('metric').addEventListener('change',update);update();
</script></html>'''
page = page.replace('SCENE_ROWS', scene_rows).replace('SOURCE_LINKS', links).replace('SOURCE_DATA', json.dumps(source).replace('<', '\\u003c'))
(HERE / 'index.html').write_text(page)
(HERE / 'verification.json').write_text(json.dumps({'scope':'Source-byte preservation, expected slots, scalar consistency and label conventions only; no re-scoring, re-tracking or independent physical validation.','checks':checks,'passed':all(c['passed'] for c in checks),'source_file_count':len(receipt['source_files']),'prior_file_count':len(receipt['frozen_prior_files'])},indent=2)+'\n')
print(json.dumps({'checks_passed':len(checks),'source_files':len(receipt['source_files']),'prior_files_unchanged':len(receipt['frozen_prior_files'])}))
