"""Present frozen task331 outputs. Does not score or generate video."""
from pathlib import Path
import hashlib
import html
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
receipt = json.loads((HERE / 'source_receipt.json').read_text())
data = json.loads((HERE / 'source/t331_results.json').read_text())
checks = []

def check(label, passed):
    checks.append({'check': label, 'passed': bool(passed)})
    assert passed, label

for row in receipt['source_files']:
    check('source bytes: ' + row['local'], hashlib.sha256((HERE / row['local']).read_bytes()).hexdigest() == row['sha256'])
for row in receipt['frozen_prior_files']:
    check('earlier demo unchanged: ' + row['path'], hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'])
for metric in ['dover_fused', 'dover_technical', 'dover_aesthetic']:
    rows = data[metric]['rows']
    check(metric + ' complete 6x3 grid', {(r['scene'], r['seed']) for r in rows} == {(s, i) for s in ['09', '12', '16', '17', '18', '19'] for i in [1, 2, 3]})
    for r in rows:
        check(metric + ' displayed main effects sum to total ' + r['scene'] + str(r['seed']), abs(r['corridor'] + r['background'] - r['total']) < 1e-12)
check('source script uses 20000 draws', 'range(20000)' in (HERE / 'source/analyze_t331.py').read_text())
prefix = 'https://github.com/srirangam-r/cosmos-swarm/blob/' + receipt['commit'] + '/'
links = ''.join(f'<li><a href="{html.escape(r["local"])}">{html.escape(Path(r["local"]).name)}</a> · <a href="{prefix}{r["original"]}">pinned original</a></li>' for r in receipt['source_files'])
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nano-Phys · Where the quality cost sits</title>
<style>
:root{--ink:#192d3c;--muted:#556774;--line:#d6e0e5;--teal:#16675c;--red:#a23e3c;--amber:#815b20}*{box-sizing:border-box}body{margin:0;background:#edf2f4;color:var(--ink);font:17px/1.55 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:42px 28px 60px}h1{font-size:clamp(34px,5vw,56px);line-height:1.08;letter-spacing:-.035em;max-width:960px}h2{font-size:25px;line-height:1.2}a{color:#125c85;text-underline-offset:3px;overflow-wrap:anywhere}.eyebrow{text-transform:uppercase;font-size:12px;font-weight:750;letter-spacing:.12em;color:var(--muted)}.pill{display:inline-block;padding:4px 12px;border:1px solid #c7a29b;border-radius:24px;color:var(--red);font-size:13px}.lead{font-size:21px;max-width:930px}.muted,.scope{color:var(--muted)}.scope{font-size:14px}.card{background:white;border:1px solid var(--line);border-radius:15px;padding:25px;margin:20px 0}.hero{display:grid;grid-template-columns:1fr 1fr;gap:20px}.hero .card{margin:0}.number{font-size:50px;font-weight:750;letter-spacing:-.04em;color:var(--red)}.notice{border-left:4px solid var(--amber);background:#fff6e7;padding:18px 22px;border-radius:8px}.controls{display:flex;gap:20px;flex-wrap:wrap;align-items:end}label{display:block;font-size:14px;font-weight:650}select{display:block;font:inherit;border:1px solid #a7b8bf;border-radius:7px;padding:8px;background:white;color:var(--ink);max-width:100%}.effect{display:grid;grid-template-columns:135px 1fr 240px;align-items:center;gap:15px;margin:18px 0}.track{height:19px;background:#eaf0f2;border-radius:4px;overflow:hidden}.bar{height:100%;background:var(--red)}.bar.bg{background:var(--teal)}.estimate{font-variant-numeric:tabular-nums;font-size:14px}.matrix{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:24px 0}.cell{padding:18px;border:1px solid var(--line);border-radius:10px}.cell strong{font-size:27px;display:block}.cell .symbol{height:72px;max-width:200px;margin:10px 0;display:flex;align-items:center;justify-content:center;border-radius:8px}.symbol.p{background:#d4e5ed}.symbol.n{background:#d4e5df}.corridor{height:62px;width:58px;text-align:center;line-height:62px;border:2px dashed #718592;font-size:12px}.corridor.p{background:#acc9da}.corridor.n{background:#89b8a9}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);white-space:nowrap}thead{background:#f4f7f8}.active{background:#e5f2ec}.source-links{columns:2;font-size:14px}li{margin:7px 0}details{margin:18px 0}summary{cursor:pointer;font-weight:650}blockquote{font-size:20px;margin:0}code{overflow-wrap:anywhere}a:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #168a94;outline-offset:4px}@media(max-width:700px){main{padding:25px 16px 40px}.hero{grid-template-columns:1fr}.card{padding:19px}.effect{grid-template-columns:95px 1fr;gap:8px}.estimate{grid-column:2}.matrix{gap:8px}.cell{padding:12px}.cell strong{font-size:22px}.source-links{columns:1}.controls{gap:12px}.number{font-size:44px}}
</style><main>
<div class="eyebrow">Demo evidence update · presentation 338 / source 331</div>
<h1>The background carries most of the measured quality cost.</h1>
<span class="pill">dk2 author result · provisional · existing clips</span>
<p class="lead">Swapping regions between plain Nano and Nano-Phys localizes about <strong>70% of the fused DOVER drop</strong> to the background on this grid. This is an attribution through a learned visual-quality metric.</p>
<p class="scope">36 existing task-276 clips · 6 takes of one pendulum rig × seeds 1–3 · 2×2 region swaps · identical x264 CRF 12 encoding · 3 DOVER repetitions on an RTX 4060.</p>
<div class="hero"><section class="card"><div class="eyebrow">Background effect · fused DOVER</div><div class="number">−0.0446</div><p><strong>Source 95% interval [−0.0532, −0.0371]</strong><br>18/18 paired effects below zero. About 70% of the total −0.0641 in the re-encoded set.</p></section>
<section class="card"><div class="eyebrow">Sensitivity control · plain clips</div><div class="number">−0.077</div><p>Author reports this DOVER change after Gaussian blur with σ = 0.5 pixels. A −1.5-grey offset costs −0.026. Neither control measures physics or establishes human perceptual equivalence.</p></section></div>
<p class="notice"><strong>Compare only within the re-encoded set.</strong> Re-encoding itself shifts fused DOVER by −0.019 for plain and −0.026 for Nano-Phys. The earlier task-319 drop of −0.057 uses the original files; it is a separate comparison.</p>
<section class="card" id="effects"><h2>The two branches tell different stories</h2><div class="controls"><div><label for="metric">DOVER metric</label><select id="metric"><option value="dover_fused">Fused</option><option value="dover_aesthetic">Aesthetic</option><option value="dover_technical">Technical</option></select></div></div>
<p id="share"></p><div id="bars"></div><p class="scope">Bar lengths show absolute magnitudes within the selected metric; values retain their signs. Intervals are copied from the source JSON. Main effects average over the other region's source. They sum to the total; interaction is a separate difference-of-differences, <strong>not an extra cost to add</strong>.</p>
<p class="scope">The source README and board call the bootstrap “exact,” but the pinned analysis script uses <strong>20,000 Monte Carlo draws</strong> of six take means (random seed 0). We preserve the saved intervals and flag this label discrepancy. These intervals are conditional on the six takes and shared seeds; they do not cover new rigs, prompts, or all scorer variation.</p></section>
<section class="card" id="factorial"><h2>Explore the four saved scores for each pair</h2><p>Select a take and seed. First letter = corridor source; second = background source. <strong>P = plain, N = Nano-Phys.</strong> The region drawings below are symbolic, not masks or video frames.</p>
<div class="controls"><div><label for="scene">Input take</label><select id="scene">SCENE_OPTIONS</select></div><div><label for="seed">Seed</label><select id="seed"><option>1</option><option>2</option><option>3</option></select></div></div>
<div class="matrix" id="matrix"></div><p id="pair-summary"></p><p id="mask-summary" class="scope"></p>
<div class="table-wrap"><table><thead><tr><th>Take / seed</th><th>PP</th><th>NN</th><th>NP</th><th>PN</th><th>Total</th><th>Background</th><th>Corridor</th></tr></thead><tbody id="rows"></tbody></table></div>
<p class="scope">All 18 pairs remain visible. No measurement gate or human quality judgment is added by this table.</p></section>
<section class="card"><h2>What the controls support</h2><ul>
<li><strong>Simple tone matching did not recover the gap:</strong> matching each arm's static background to its input frame leaves −0.062 DOVER [−0.076, −0.053], as reported by dk2. This tested offset correction does not establish that all photometric effects are absent.</li>
<li><strong>Fine-detail loss is a candidate:</strong> source background PSNR is 34.4 dB for plain versus 33.7 for Nano-Phys; Laplacian-variance ratios are 0.82 versus 0.80. This does not isolate a VAE, compression, proxy, or sampling cause.</li>
<li><strong>Mask and seam dependence:</strong> the corridor unions pixels changing from frame 0 in plain, Nano-Phys, and proxy videos (threshold 25 grey; 3×3 opening, 21-pixel dilation, Gaussian feather σ 6). It covers 20–49% of the image and can include other moving content. Compositing seams can affect scores; the interaction term does not separately identify a seam contribution.</li>
<li><strong>Scope:</strong> one rig, repeated takes, fixed shared seeds, generated 93 frames at 24 fps and 832×480, CFG 6, 35 steps, supplied proxy at σ ≈ 0.898. The source records later-real-video periods. No new clips or scores were produced for this page.</li>
<li><strong>Not established:</strong> a first-frame-only physics remedy, general human visual improvement, judge or robot-prediction non-regression, or the cause of the texture change. Planted-case validation does not apply to this visual-quality score.</li></ul></section>
<section class="notice"><div class="eyebrow">Fix under test by experiment owners</div><h2>Restrict proxy guidance to the motion region</h2><p>Region-wise latent noising and stochastic flow relaxation are published methods. Tasks 336/337 coordinate their Nano-Phys test. <strong>This page contains no result for that fix.</strong> The pixel-level region swap is a diagnostic, not an inference recipe.</p></section>
<section class="card"><h2>Suggested demo copy</h2><blockquote>“On six pendulum takes × three seeds, a region-swap analysis attributes about 70% of Nano-Phys' re-encoded DOVER loss to the background. A simple tone correction does not recover it, and DOVER is sensitive to small blur. The underlying cause and a remedy remain under test.”</blockquote><p class="scope">Human-applied wording proposal. Earlier period-transfer and quality cards remain separate: <a href="../t328/index.html">original quality scorecard</a> · <a href="../t332/index.html">fresh-input outcomes</a> · <a href="../t334/index.html">supplied-state demo</a>.</p></section>
<section class="card" id="receipts"><h2>Attribution and receipts</h2><p>Analysis and scores: <strong>dk2, task 331 / finding #6767</strong>, pinned commit <code>e36f89c</code>. Presentation: ro-sol1, task 338. This packaging does not independently replicate scoring or physical measurement.</p><p><a href="DEMO_READOUT.md">Plain-text readout</a> · <a href="source_receipt.json">SHA256 receipts</a> · <a href="board_receipts.json">Board messages</a> · <a href="verification.json">Packaging validation</a> · <a href="browser_render.json">Browser validation</a> · <a href="gallery_http.json">Separate gallery HTTP observations</a></p>
<details><summary>All 13 exact source snapshots</summary><ul class="source-links">SOURCE_LINKS</ul></details>
<details><summary>Published context read before this task</summary><p class="scope"><a href="https://arxiv.org/abs/2607.03732">ProxyUp §§4.3–5.4</a>: masked dynamics and relaxation improve its Wan2.2 results; not a Nano guarantee. <a href="https://arxiv.org/abs/2511.08633">Time-to-Move §3.3 / Appendix A</a>: region-dependent motion guidance and background freedom. <a href="https://arxiv.org/abs/2211.04894">DOVER §§4.1–4.3</a>: separate aesthetic and texture-sensitive technical views. These works frame labels, not validation of this run.</p></details></section>
<p class="scope">Static local readout. Deployment and gallery service changes remain with their owners. Judged root README and reports are untouched.</p>
</main><script id="source-data" type="application/json">SOURCE_DATA</script><script>
const evidence=JSON.parse(document.querySelector('#source-data').textContent);
const fmt=x=>(x>=0?'+':'−')+Math.abs(x).toFixed(4);
function update(){const metric=document.querySelector('#metric').value, scene=document.querySelector('#scene').value, seed=Number(document.querySelector('#seed').value),d=evidence[metric], s=d.summary, row=d.rows.find(r=>r.scene===scene&&r.seed===seed);
document.querySelector('#share').textContent=`Background: ${(100*s.share_background).toFixed(1)}% of total · corridor: ${(100*s.share_corridor).toFixed(1)}%. Different metric branches have different scales.`;
const max=Math.max(...['total','background','corridor','interaction'].map(k=>Math.abs(s[k].mean)));
document.querySelector('#bars').innerHTML=['total','background','corridor','interaction'].map(k=>`<div class="effect" data-effect="${k}"><strong>${k[0].toUpperCase()+k.slice(1)}</strong><div class="track"><div class="bar ${k==='background'?'bg':''}" style="width:${100*Math.abs(s[k].mean)/max}%"></div></div><span class="estimate">${fmt(s[k].mean)} [${s[k].ci95.map(fmt).join(', ')}]<br>${s[k].n_neg}/18 negative</span></div>`).join('');
document.querySelector('#matrix').innerHTML=['pp','np','pn','nn'].map(k=>`<div class="cell" data-cell="${k}"><b>${k.toUpperCase()}</b> · corridor ${k[0]==='p'?'plain':'Nano-Phys'}<br>background ${k[1]==='p'?'plain':'Nano-Phys'}<div aria-hidden="true" class="symbol ${k[1]}"><span class="corridor ${k[0]}">corridor</span></div><strong>${row[k].toFixed(5)}</strong><span class="scope">saved ${metric.replace('dover_','')} score</span></div>`).join('');
document.querySelector('#pair-summary').textContent=`Take ${scene}, seed ${seed}: total ${fmt(row.total)} · background ${fmt(row.background)} · corridor ${fmt(row.corridor)} · interaction ${fmt(row.interaction)}.`;
document.querySelector('#mask-summary').textContent=`Source feathered-mask area: ${(100*evidence.mask[scene+'_s'+seed].mask_frac_feather).toFixed(1)}% of this frame; same mask used for its four cells.`;
document.querySelector('#rows').innerHTML=d.rows.map(r=>`<tr class="${r===row?'active':''}"><th scope="row">${r.scene} / ${r.seed}</th>${['pp','nn','np','pn','total','background','corridor'].map(k=>`<td>${r[k].toFixed(5)}</td>`).join('')}</tr>`).join('');
}
for(const id of ['metric','scene','seed'])document.querySelector('#'+id).addEventListener('change',update);update();
</script></html>'''
page = page.replace('SCENE_OPTIONS', ''.join(f'<option>{s}</option>' for s in ['09', '12', '16', '17', '18', '19'])).replace('SOURCE_LINKS', links).replace('SOURCE_DATA', json.dumps(data).replace('<', '\\u003c'))
(HERE / 'index.html').write_text(page)
(HERE / 'verification.json').write_text(json.dumps({'scope': 'Byte preservation, complete saved grids and display identities only. No new scores or physics validation.', 'checks': checks, 'passed': True, 'source_file_count': len(receipt['source_files']), 'prior_file_count': len(receipt['frozen_prior_files'])}, indent=2) + '\n')
print(json.dumps({'passed': True, 'checks': len(checks), 'source_files': len(receipt['source_files']), 'prior_files': len(receipt['frozen_prior_files'])}))
